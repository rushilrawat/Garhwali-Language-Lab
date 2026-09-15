#!/usr/bin/env python3
"""Build deterministic Hugging Face upload folders from prepared Garhwali views."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab'
RELEASE_ID = 'garhwali-language-lab-v0.1.0'
OPEN_LICENSE_MARKERS = (
    'cc0', 'creativecommons.org/publicdomain', 'cc-by-', 'cc_by_',
    '/licenses/by/', '/licenses/by-sa/', 'mit', 'apache-2.0',
)
BLOCKING_FLAGS = {
    'component_rights_review_required', 'source_lineage_missing', 'unlicensed',
    'publisher_license_not_stated', 'underlying_web_copyrights_not_cleared',
}
BLOCKING_RIGHTS_MARKERS = (
    'not_sublicensed', 'review_pending', 'review_required',
    'no_open_license', 'copyrights_not_cleared', 'license_link_missing',
    'license_not_stated', 'author_death_evidence_pending',
)


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def is_publishable_provenance(item):
    flags = set(item.get('quality_flags') or [])
    if flags & BLOCKING_FLAGS:
        return False
    rights = str(item.get('rights_status') or '').casefold()
    if any(marker in rights for marker in BLOCKING_RIGHTS_MARKERS):
        return False
    license_text = ' '.join(str(item.get(key) or '') for key in (
        'license', 'license_id', 'license_url',
    )).casefold()
    return any(marker in license_text for marker in OPEN_LICENSE_MARKERS)


def provenance_items(row):
    direct = row.get('provenance') or []
    nested = [
        item
        for parent in row.get('parents') or []
        for item in parent.get('provenance') or []
    ]
    return direct + nested


def is_public_text_row(row):
    items = provenance_items(row)
    return bool(items) and all(is_publishable_provenance(item) for item in items)


def is_public_garhwali_text_row(row):
    items = provenance_items(row)
    return is_public_text_row(row) and all(
        item.get('iso_639_3') == 'gbm' for item in items
    )


def content_audio_path(audio_sha256):
    return f'audio/{audio_sha256[:2]}/{audio_sha256}.wav'


def public_speaker_id(row):
    speaker = row.get('speaker_id')
    if speaker in (None, '', 'NA'):
        return None
    value = f"{row.get('source', '')}|{speaker}".encode()
    return f'speaker_{hashlib.sha256(value).hexdigest()[:16]}'


def audio_row(row, transcript_field, include_audio_reference=True):
    keep = (
        'audio_sha256', 'duration_seconds', 'language', 'district', 'state',
        'gender', 'languages_known', 'source', 'license',
        'main_split', 'transcription_split', 'quality_flags',
        'training_quality_flags', 'review_status',
        'machine_transcript_model', 'machine_transcript_model_revision',
        'machine_transcript_quality',
        'recovery_status', 'recovery_confidence',
        'experimental_training_eligible', 'training_eligible',
        'language_scope_status', 'source_conflict_evidence',
        'active_for_source_error_analysis',
        'recovery_adjudication',
        'recovery_third_checkpoint',
    )
    exported = {key: row.get(key) for key in keep if key in row}
    if include_audio_reference:
        exported['audio'] = content_audio_path(row['audio_sha256'])
    exported['speaker_id'] = public_speaker_id(row)
    exported['transcript'] = row.get(transcript_field, '')
    exported['source_audio_records'] = max(
        1, len(row.get('duplicate_source_audio_paths') or [])
    )
    return exported


def attach_recovery_adjudication(rows, adjudication_rows):
    by_hash = {row['audio_sha256']: row for row in adjudication_rows}
    if len(by_hash) != len(adjudication_rows):
        raise ValueError('Recovery adjudication audio hashes are not unique')
    safe_fields = (
        'candidates', 'pairwise_character_agreement',
        'whisper_v0.1_token_confidence_uncalibrated',
        'proposed_machine_transcript', 'proposed_machine_transcript_model',
        'proposed_machine_transcript_flags', 'proposal_basis',
        'evidence_status', 'review_priority', 'human_review_status',
        'automatic_correction', 'human_reference_available',
        'supervised_training_eligible',
        'recommended_for_machine_label_training',
        'original_transcript_preserved',
    )
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['recovery_adjudication'] = {
                field: evidence[field] for field in safe_fields if field in evidence
            }
        result.append(enriched)
    return result


def attach_recovery_third_checkpoint(rows, checkpoint_rows):
    by_hash = {row['audio_sha256']: row for row in checkpoint_rows}
    if len(by_hash) != len(checkpoint_rows):
        raise ValueError('Third-checkpoint recovery audio hashes are not unique')
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['recovery_third_checkpoint'] = {
                'transcript': evidence.get('machine_transcript', ''),
                'model': 'whisper-tiny-garhwali-v0.1',
                'mean_token_log_probability': evidence.get('mean_token_log_probability'),
                'token_confidence_uncalibrated': evidence.get('token_confidence_uncalibrated'),
                'confidence_is_calibrated': False,
                'human_reference_available': False,
            }
        result.append(enriched)
    return result


def draft_identity(row):
    return row['audio_sha256'], row.get('audio_path') or row.get('local_audio_path')


def drafts_cover_queue(queue, drafts):
    return Counter(map(draft_identity, queue)) == Counter(map(draft_identity, drafts))


def deduplicate_audio_rows(rows, transcript_field):
    groups = {}
    for row in rows:
        digest = row['audio_sha256']
        if digest not in groups:
            groups[digest] = dict(row)
            groups[digest]['duplicate_source_audio_paths'] = []
        current = groups[digest]
        if current.get(transcript_field, '') != row.get(transcript_field, ''):
            raise ValueError(f'conflicting transcripts for audio_sha256={digest}')
        source_path = row.get('audio_path') or row.get('local_audio_path')
        if source_path not in current['duplicate_source_audio_paths']:
            current['duplicate_source_audio_paths'].append(source_path)
    yield from groups.values()


def text_row(row):
    scripts = set()
    for character in row['text']:
        codepoint = ord(character)
        if 0x0900 <= codepoint <= 0x097F:
            scripts.add('Deva')
        elif 0x0980 <= codepoint <= 0x09FF:
            scripts.add('Beng')
        elif character.isascii() and character.isalpha():
            scripts.add('Latn')
    script = next(iter(scripts)) if len(scripts) == 1 else ('Mixed' if scripts else 'Other')
    return {
        'id': row['segment_sha256'],
        'text': row['text'],
        'language': 'gbm',
        'script': script,
        'split': row['split'],
        'quality_flags': row.get('quality_flags') or [],
        'provenance': provenance_items(row),
    }


def catalog_provenance(item):
    keep = (
        'source_id', 'source_url', 'record_id', 'iso_639_3', 'genre', 'script',
        'license', 'license_id', 'license_url', 'rights_status', 'quality_flags',
    )
    return {key: item.get(key) for key in keep if item.get(key) not in (None, '', [])}


def catalog_row(row, include_restricted_text=False, refinement=None):
    items = provenance_items(row)
    text_is_public = bool(items) and all(is_publishable_provenance(item) for item in items)
    text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    exported = {
        'id': row['text_sha256'],
        'split': row.get('split'),
        'text': text if text_is_public or include_restricted_text else None,
        'text_sha256': row['text_sha256'],
        'text_character_count': len(text),
        'text_publicly_available': text_is_public,
        'redaction_reason': None if text_is_public or include_restricted_text else 'source_rights_do_not_permit_public_text_redistribution',
        'language_bucket': row.get('language_bucket'),
        'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'),
        'genre_quality': row.get('genre_quality'),
        'surface_quality': row.get('quality'),
        'quality_v2': row.get('quality_v2'),
        'sources': [catalog_provenance(item) for item in items],
    }
    if refinement:
        exported['text_refinement'] = {
            key: refinement.get(key) for key in (
                'automatic_changes', 'review_signals', 'manual_review_required',
                'language_decision', 'quality_refinement_status',
                'release_text_sha256', 'quality_dimensions', 'review_priority',
            )
        }
        if text_is_public or include_restricted_text:
            exported['text_refinement']['release_text'] = refinement.get('release_text')
    return exported


def write_shards(rows, directory, split, shard_rows=10_000):
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.glob(f'{split}-*.jsonl'):
        old.unlink()
    count = 0
    shard = -1
    handle = None
    paths = []
    try:
        for row in rows:
            if count % shard_rows == 0:
                if handle:
                    handle.close()
                shard += 1
                path = directory / f'{split}-{shard:05d}.jsonl'
                paths.append(path)
                handle = path.open('w', encoding='utf-8')
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    finally:
        if handle:
            handle.close()
    return {'records': count, 'shards': len(paths), 'files': [str(p.name) for p in paths]}


def link_audio(rows, output):
    linked = 0
    seen = set()
    for row in rows:
        digest = row['audio_sha256']
        if digest in seen:
            continue
        seen.add(digest)
        source = ROOT / row['local_audio_path']
        target = output / content_audio_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            os.link(source, target)
            linked += 1
    return {'new': linked, 'total': len(seen)}


def remove_packaged_audio(output):
    directory = Path(output) / 'audio'
    count = sum(1 for _ in directory.rglob('*.wav')) if directory.exists() else 0
    if directory.exists():
        shutil.rmtree(directory)
    return count


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_card(report):
    draft_status = 'complete' if report['drafts_complete'] else 'partial'
    exported_rows = sum(item['records'] for item in report['configs'].values())
    audio_summary = (
        f"The package includes **{report['linked_audio_files']:,} content-addressed audio files**."
        if report['include_audio'] else
        'This transcript-only package does not include audio files or source filenames.'
    )
    return f'''---
language:
- gbm
license: other
task_categories:
- automatic-speech-recognition
- text-generation
- translation
configs:
- config_name: text
  data_files:
  - split: train
    path: data/text/train-*.jsonl
  - split: validation
    path: data/text/validation-*.jsonl
  - split: test
    path: data/text/test-*.jsonl
- config_name: asr
  data_files:
  - split: train
    path: data/asr/train-*.jsonl
  - split: validation
    path: data/asr/validation-*.jsonl
  - split: test
    path: data/asr/test-*.jsonl
- config_name: sravaani_drafts
  data_files:
  - split: train
    path: data/sravaani_drafts/train-*.jsonl
- config_name: lexicon
  data_files:
  - split: train
    path: data/lexicon/train-*.jsonl
- config_name: instructions
  data_files:
  - split: train
    path: data/instructions/train-*.jsonl
  - split: validation
    path: data/instructions/validation-*.jsonl
  - split: test
    path: data/instructions/test-*.jsonl
- config_name: catalog
  data_files:
  - split: train
    path: data/catalog/train-*.jsonl
---

# Garhwali Language Lab

Release: **{report['release_id']}**

Versioned Garhwali (`gbm`) text, speech, lexicon, and instruction resources built
by the Garhwali Language Lab. Every row retains source and license evidence.

This rights-filtered package contains **{exported_rows:,} records** across six
configurations, including transcripts for **{report['draft_unique_audio']:,}
unique SraVaani recordings**. {audio_summary}

The `catalog` configuration publicly accounts for all
**{report['catalog_records']:,} exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
only the protected text value is redacted. Nothing is silently omitted.

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Targeted rows also retain their local Whisper alternative,
cross-model agreement, and bounded review-confidence evidence. Draft export
status: **{draft_status}**.

All **{report['draft_third_checkpoint_records']:,}** targeted recordings retain
the third-checkpoint hypothesis. For the **{report['draft_three_checkpoint_review_records']:,}**
Garhwali review records, the package also carries a structurally ranked machine
proposal and its evidence limits. These proposals are pending audio review and
are never represented as automatic corrections or human references.

The draft layer also preserves **{report['draft_source_label_conflicts']:,}
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).
'''


def build(output, profile='public', include_audio=False, allow_partial_drafts=False,
          shard_rows=10_000):
    output = Path(output)
    report = {
        'release_id': RELEASE_ID,
        'profile': profile,
        'include_audio': include_audio,
        'configs': {},
    }

    text_dir = ROOT / 'data/processed/model_ready/splits/text'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(text_dir / f'{split}.jsonl')
        if profile == 'public':
            rows = (row for row in rows if is_public_garhwali_text_row(row))
        report['configs'][f'text/{split}'] = write_shards(
            (text_row(row) for row in rows), output / 'data/text', split, shard_rows
        )

    quality_catalog = read_jsonl(
        ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
    )
    refinement_path = ROOT / 'data/processed/model_ready/text_quality_v2/priority_text.jsonl'
    refinements = {
        row['text_sha256']: row for row in read_jsonl(refinement_path)
    } if refinement_path.exists() else {}
    catalog_rows = [
        catalog_row(
            row,
            include_restricted_text=profile == 'experimental-local',
            refinement=refinements.get(row['text_sha256']),
        )
        for row in quality_catalog
    ]
    report['catalog_refined_text_records'] = sum(
        'text_refinement' in row for row in catalog_rows
    )
    report['catalog_records'] = len(catalog_rows)
    report['catalog_redacted_text_records'] = sum(
        row['text'] is None for row in catalog_rows
    )
    report['configs']['catalog/train'] = write_shards(
        catalog_rows, output / 'data/catalog', 'train', shard_rows
    )

    audio_sources = []
    asr_dir = ROOT / 'data/processed/model_ready/splits/asr'
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(asr_dir / f'{split}.jsonl'))
        audio_sources.extend(rows)
        report['configs'][f'asr/{split}'] = write_shards(
            (audio_row(row, 'asr_target_clean', include_audio) for row in rows),
            output / 'data/asr', split, shard_rows,
        )

    queue_path = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
    confidence_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
    quality_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
    raw_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'
    drafts_path = next(
        path for path in (
            confidence_drafts_path, quality_drafts_path, raw_drafts_path
        ) if path.exists()
    )
    queue = list(read_jsonl(queue_path))
    queue_count = len(queue)
    drafts = list(read_jsonl(drafts_path))
    unique_drafts = list(deduplicate_audio_rows(drafts, 'machine_transcript'))
    third_checkpoint_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_whisper_v0.1.jsonl'
    )
    third_checkpoint_rows = list(read_jsonl(third_checkpoint_path)) \
        if third_checkpoint_path.exists() else []
    unique_drafts = attach_recovery_third_checkpoint(
        unique_drafts, third_checkpoint_rows
    )
    adjudication_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_adjudication.jsonl'
    )
    adjudication_rows = list(read_jsonl(adjudication_path)) \
        if adjudication_path.exists() else []
    unique_drafts = attach_recovery_adjudication(unique_drafts, adjudication_rows)
    report['draft_queue_records'] = queue_count
    report['draft_source'] = str(drafts_path.relative_to(ROOT))
    report['draft_records'] = len(drafts)
    report['draft_unique_audio'] = len(unique_drafts)
    report['draft_source_label_conflicts'] = sum(
        row.get('language_scope_status') == 'source_label_conflict'
        for row in unique_drafts
    )
    report['draft_three_checkpoint_review_records'] = sum(
        bool(row.get('recovery_adjudication')) for row in unique_drafts
    )
    report['draft_third_checkpoint_records'] = sum(
        bool(row.get('recovery_third_checkpoint')) for row in unique_drafts
    )
    report['draft_inherited_duplicate_rows'] = len(drafts) - len(unique_drafts)
    report['drafts_complete'] = drafts_cover_queue(queue, drafts)
    if not report['drafts_complete'] and not allow_partial_drafts:
        raise RuntimeError(
            f'SraVaani drafts incomplete: {len(drafts)}/{queue_count}; '
            'use --allow-partial-drafts only for a preview'
        )
    audio_sources.extend(unique_drafts)
    report['configs']['sravaani_drafts/train'] = write_shards(
        (audio_row(row, 'machine_transcript', include_audio) for row in unique_drafts),
        output / 'data/sravaani_drafts', 'train', shard_rows,
    )

    lexicon = read_jsonl(
        ROOT / 'data/processed/model_ready/language_resources/pronunciation/lexicon.jsonl'
    )
    if profile == 'public':
        lexicon = (row for row in lexicon if is_public_text_row(row))
    report['configs']['lexicon/train'] = write_shards(
        lexicon, output / 'data/lexicon', 'train', shard_rows,
    )

    instructions_dir = ROOT / 'data/processed/model_ready/instructions_v0.2'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(instructions_dir / f'{split}.jsonl')
        if profile == 'public':
            rows = (row for row in rows if is_public_text_row(row))
        report['configs'][f'instructions/{split}'] = write_shards(
            rows, output / 'data/instructions', split, shard_rows,
        )

    removed_audio_files = 0 if include_audio else remove_packaged_audio(output)
    link_report = link_audio(audio_sources, output) if include_audio else {'new': 0, 'total': 0}
    report['linked_audio_files'] = link_report['total']
    report['newly_linked_audio_files'] = link_report['new']
    report['removed_audio_files'] = removed_audio_files
    output.mkdir(parents=True, exist_ok=True)
    (output / 'README.md').write_text(dataset_card(report), encoding='utf-8')
    (output / 'manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    report['manifest_sha256'] = sha256_file(output / 'manifest.json')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--profile', choices=('public', 'experimental-local'), default='public')
    parser.add_argument('--include-audio', action='store_true')
    parser.add_argument('--allow-partial-drafts', action='store_true')
    parser.add_argument('--shard-rows', type=int, default=10_000)
    args = parser.parse_args()
    print(json.dumps(build(
        args.output,
        profile=args.profile,
        include_audio=args.include_audio,
        allow_partial_drafts=args.allow_partial_drafts,
        shard_rows=args.shard_rows,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
