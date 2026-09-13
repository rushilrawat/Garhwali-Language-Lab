#!/usr/bin/env python3
"""Build deterministic Hugging Face upload folders from prepared Garhwali views."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab'
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


def content_audio_path(audio_sha256):
    return f'audio/{audio_sha256[:2]}/{audio_sha256}.wav'


def audio_row(row, transcript_field):
    keep = (
        'audio_sha256', 'duration_seconds', 'language', 'district', 'state',
        'gender', 'speaker_id', 'languages_known', 'source', 'license',
        'main_split', 'transcription_split', 'quality_flags',
        'training_quality_flags', 'review_status',
        'machine_transcript_model', 'machine_transcript_model_revision',
        'machine_transcript_quality',
        'experimental_training_eligible', 'training_eligible',
    )
    exported = {key: row.get(key) for key in keep if key in row}
    exported['audio'] = content_audio_path(row['audio_sha256'])
    exported['transcript'] = row.get(transcript_field, '')
    if row.get('duplicate_source_audio_paths'):
        exported['duplicate_source_audio_paths'] = row['duplicate_source_audio_paths']
    return exported


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
    return {
        'id': row['segment_sha256'],
        'text': row['text'],
        'language': 'gbm',
        'script': 'Deva',
        'split': row['split'],
        'quality_flags': row.get('quality_flags') or [],
        'provenance': provenance_items(row),
    }


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
    return linked


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def dataset_card(report):
    draft_status = 'complete' if report['drafts_complete'] else 'partial'
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
---

# Garhwali Language Lab

Versioned Garhwali (`gbm`) text, speech, lexicon, and instruction resources built
by the Garhwali Language Lab. Every row retains source and license evidence.

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Draft export status: **{draft_status}**.

This package uses multiple upstream licenses. Inspect each row's provenance and
the repository's full dataset card before redistribution or model release.
'''


def build(output, profile='public', include_audio=False, allow_partial_drafts=False,
          shard_rows=10_000):
    output = Path(output)
    report = {'profile': profile, 'include_audio': include_audio, 'configs': {}}

    text_dir = ROOT / 'data/processed/model_ready/splits/text'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(text_dir / f'{split}.jsonl')
        if profile == 'public':
            rows = (row for row in rows if is_public_text_row(row))
        report['configs'][f'text/{split}'] = write_shards(
            (text_row(row) for row in rows), output / 'data/text', split, shard_rows
        )

    audio_sources = []
    asr_dir = ROOT / 'data/processed/model_ready/splits/asr'
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(asr_dir / f'{split}.jsonl'))
        audio_sources.extend(rows)
        report['configs'][f'asr/{split}'] = write_shards(
            (audio_row(row, 'asr_target_clean') for row in rows),
            output / 'data/asr', split, shard_rows,
        )

    queue_path = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
    quality_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
    drafts_path = quality_drafts_path if quality_drafts_path.exists() else (
        ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'
    )
    queue = list(read_jsonl(queue_path))
    queue_count = len(queue)
    drafts = list(read_jsonl(drafts_path))
    unique_drafts = list(deduplicate_audio_rows(drafts, 'machine_transcript'))
    report['draft_queue_records'] = queue_count
    report['draft_records'] = len(drafts)
    report['draft_unique_audio'] = len(unique_drafts)
    report['draft_inherited_duplicate_rows'] = len(drafts) - len(unique_drafts)
    report['drafts_complete'] = drafts_cover_queue(queue, drafts)
    if not report['drafts_complete'] and not allow_partial_drafts:
        raise RuntimeError(
            f'SraVaani drafts incomplete: {len(drafts)}/{queue_count}; '
            'use --allow-partial-drafts only for a preview'
        )
    audio_sources.extend(unique_drafts)
    report['configs']['sravaani_drafts/train'] = write_shards(
        (audio_row(row, 'machine_transcript') for row in unique_drafts),
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

    report['linked_audio_files'] = link_audio(audio_sources, output) if include_audio else 0
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
