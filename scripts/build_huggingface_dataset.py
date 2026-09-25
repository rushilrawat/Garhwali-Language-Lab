#!/usr/bin/env python3
"""Build deterministic Hugging Face upload folders from prepared Garhwali views."""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab'
ALL_DATA_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-all-data'
RELEASE_ID = 'garhwali-language-lab-v0.1.1'
KNOWLEDGE_CONFIGS = {
    'geography': ROOT / 'data/extracted/geography/records.jsonl',
    'historical_terms': ROOT / 'data/extracted/historical_terms/records.jsonl',
    'literary_people': ROOT / 'data/extracted/literary_people/records.jsonl',
    'literary_works': ROOT / 'data/extracted/literary_works/records.jsonl',
    'popular_songs': ROOT / 'data/extracted/popular_songs/records.jsonl',
    'university_research': ROOT / 'data/extracted/university_research/records.jsonl',
}
KNOWLEDGE_SOURCE_CATALOGS = {
    'geography': ROOT / 'research/garhwali-geography-catalog.json',
    'historical_terms': ROOT / 'research/garhwali-historical-terms.json',
    'literary_people': ROOT / 'research/garhwali-literary-people-catalog.json',
    'literary_works': ROOT / 'research/garhwali-literary-works-catalog.json',
}
OPEN_LICENSE_MARKERS = (
    'cc0', 'creativecommons.org/publicdomain', 'cc-by-', 'cc_by_',
    '/licenses/by/', '/licenses/by-sa/', 'apache-2.0',
)
BLOCKING_FLAGS = {
    'component_rights_review_required', 'source_lineage_missing', 'unlicensed',
    'publisher_license_not_stated', 'underlying_web_copyrights_not_cleared',
}
BLOCKING_RIGHTS_MARKERS = (
    'not_sublicensed', 'review_pending', 'review_required',
    'no_open_license', 'copyrights_not_cleared', 'license_link_missing',
    'license_not_stated', 'author_death_evidence_pending',
    'component_review', 'no_license',
)


def profile_includes_all_data(profile):
    return profile == 'all-data'


def prepare_package_output(output):
    output = Path(output)
    resolved = output.resolve()
    managed = {DEFAULT_OUTPUT.resolve(), ALL_DATA_OUTPUT.resolve()}
    if output.exists() and resolved not in managed:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def asr_split_directory(profile):
    return 'asr_experimental' if profile_includes_all_data(profile) else 'asr'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def is_publishable_provenance(item):
    flags = set(item.get('quality_flags') or [])
    if flags & BLOCKING_FLAGS:
        return False
    rights = re.sub(
        r'[^a-z0-9]+', '_', str(item.get('rights_status') or '').casefold()
    ).strip('_')
    if any(marker in rights for marker in BLOCKING_RIGHTS_MARKERS):
        return False
    license_text = ' '.join(str(item.get(key) or '') for key in (
        'license', 'license_id', 'license_url',
    )).casefold()
    compact_license = re.sub(r'[^a-z0-9]+', '', license_text)
    if any(marker in compact_license for marker in (
        'ccbync', 'ccbynd', 'licensesbync', 'licensesbynd',
    )):
        return False
    if re.search(r'(?<![a-z0-9])mit(?![a-z0-9])', license_text):
        return True
    return any(marker in license_text for marker in OPEN_LICENSE_MARKERS)


def provenance_items(row):
    direct = row.get('provenance') or []
    nested = [
        item
        for parent in row.get('parents') or []
        for item in parent.get('provenance') or []
    ]
    return direct + nested


def publishable_provenance_items(row):
    return [item for item in provenance_items(row) if is_publishable_provenance(item)]


def is_public_text_row(row):
    return bool(publishable_provenance_items(row))


def is_public_garhwali_text_row(row):
    items = publishable_provenance_items(row)
    return bool(items) and all(
        item.get('iso_639_3') == 'gbm' for item in items
    )


def is_public_knowledge_row(row):
    rights_basis = row.get('public_rights_basis') or []
    rights_status = re.sub(
        r'[^a-z0-9]+', '_', str(row.get('rights_status') or '').casefold()
    ).strip('_')
    return bool(rights_basis) and rights_status not in {
        'not_assessed', 'review_pending', 'rights_pending', 'unknown',
    } and all(
        is_publishable_provenance(item)
        and item.get('attribution')
        and (item.get('source_url') or item.get('source_snapshot_sha256'))
        for item in rights_basis
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
        'audio_grounded_review',
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


def attach_audio_grounded_review(rows, review_rows):
    by_hash = {row['audio_sha256']: row for row in review_rows}
    if len(by_hash) != len(review_rows):
        raise ValueError('Audio-grounded review hashes are not unique')
    safe_fields = (
        'audio_grounded_evidence', 'audio_review_category',
        'audio_review_priority', 'machine_audio_review_complete',
        'human_listening_review_required', 'automatic_correction',
        'human_reference_available', 'supervised_training_eligible',
        'recommended_for_machine_label_training',
        'original_transcript_preserved',
    )
    result = []
    for row in rows:
        enriched = dict(row)
        evidence = by_hash.get(row['audio_sha256'])
        if evidence:
            enriched['audio_grounded_review'] = {
                field: evidence[field] for field in safe_fields if field in evidence
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


def source_languages(row):
    """Return source-declared ISO codes without guessing from shared scripts."""
    return sorted({
        item.get('iso_639_3')
        for item in provenance_items(row)
        if item.get('iso_639_3')
    })


def recommended_text_training_row(row):
    rights_basis = row.get('public_rights_basis') or []
    return bool(
        row.get('language') == 'gbm'
        and set(row.get('source_languages') or []) == {'gbm'}
        and row.get('language_buckets') == ['garhwali_candidate']
        and 'strict_gold_candidate' in (row.get('quality_tiers') or [])
        and not row.get('quality_flags')
        and rights_basis
        and all(is_publishable_provenance(item) for item in rights_basis)
    )


def text_row(row, parent_quality=None):
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
    parent_quality = parent_quality or {}
    parent_records = [
        parent_quality[parent['text_sha256']]
        for parent in row.get('parents') or []
        if parent.get('text_sha256') in parent_quality
    ]
    language_buckets = sorted({
        parent.get('language_bucket') for parent in parent_records
        if parent.get('language_bucket')
    })
    quality_tiers = sorted({
        (parent.get('quality_v2') or {}).get('tier') for parent in parent_records
        if (parent.get('quality_v2') or {}).get('tier')
    })
    languages = source_languages(row)
    if language_buckets == ['garhwali_candidate']:
        language = 'gbm'
    elif 'mixed_language' in language_buckets:
        language = 'mul'
    elif 'review' in language_buckets:
        language = 'und'
    elif len(languages) == 1:
        language = languages[0]
    elif languages:
        language = 'mul'
    else:
        language = 'und'
    exported = {
        'id': row['segment_sha256'],
        'text': row['text'],
        'language': language,
        'source_languages': languages,
        'language_buckets': language_buckets,
        'quality_tiers': quality_tiers,
        'recommended_for_training': False,
        'script': script,
        'split': row['split'],
        'duplicate_component_id': row.get('duplicate_component_id'),
        'original_split': row.get('original_split'),
        'split_assignment': row.get('split_assignment'),
        'quality_flags': row.get('quality_flags') or [],
        'provenance': provenance_items(row),
        'public_rights_basis': [
            catalog_provenance(item) for item in publishable_provenance_items(row)
        ],
    }
    exported['recommended_for_training'] = recommended_text_training_row(exported)
    return exported


def with_public_rights_basis(row):
    enriched = dict(row)
    enriched['public_rights_basis'] = [
        catalog_provenance(item) for item in publishable_provenance_items(row)
    ]
    return enriched


def lexicon_row(row):
    enriched = with_public_rights_basis(row)
    enriched['source_text_sha256'] = row.get('text_sha256')
    enriched['form_sha256'] = hashlib.sha256(
        str(row.get('form') or '').encode('utf-8')
    ).hexdigest()
    return enriched


def refresh_acceptable_responses(rows):
    groups = {}
    for row in rows:
        key = (
            row.get('task'),
            ' '.join(str(row.get('instruction') or '').casefold().split()),
        )
        groups.setdefault(key, set()).add(row.get('response'))
    for row in rows:
        key = (
            row.get('task'),
            ' '.join(str(row.get('instruction') or '').casefold().split()),
        )
        row['acceptable_responses'] = sorted(groups[key])
    return rows


def catalog_provenance(item):
    keep = (
        'source_id', 'source_url', 'source_title', 'source_kind',
        'source_snapshot_sha256', 'source_capture_id', 'source_capture_path',
        'source_notes', 'source_capture_bytes', 'record_id', 'iso_639_3', 'genre', 'script',
        'license', 'license_id', 'license_url', 'rights_status', 'quality_flags',
        'rights_evidence', 'attribution',
        'source_pdf', 'source_pdf_sha256', 'pdf_page', 'title', 'author',
        'publication_year', 'extraction_method', 'modifications',
    )
    return {key: item.get(key) for key in keep if item.get(key) not in (None, '', [])}


def catalog_row(row, include_all_text=False, refinement=None):
    items = provenance_items(row)
    rights_basis = publishable_provenance_items(row)
    text_is_public = bool(rights_basis)
    text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    exported = {
        'id': row['text_sha256'],
        'split': row.get('split'),
        'text': text if text_is_public or include_all_text else None,
        'text_sha256': row['text_sha256'],
        'source_text_sha256': row['text_sha256'],
        'release_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'text_character_count': len(text),
        'content_included': text_is_public or include_all_text,
        'active_for_quality_work': True,
        'text_publicly_available': text_is_public,
        'redistribution_status': 'rights_cleared' if text_is_public else 'rights_pending',
        'redaction_reason': None if text_is_public or include_all_text else 'source_rights_do_not_permit_public_text_redistribution',
        'language_bucket': row.get('language_bucket'),
        'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'),
        'genre_quality': row.get('genre_quality'),
        'surface_quality': row.get('quality'),
        'quality_v2': row.get('quality_v2'),
        'sources': [catalog_provenance(item) for item in items],
        'public_rights_basis': [catalog_provenance(item) for item in rights_basis],
    }
    if refinement:
        exported['text_refinement'] = {
            key: refinement.get(key) for key in (
                'automatic_changes', 'review_signals', 'manual_review_required',
                'language_decision', 'quality_refinement_status',
                'release_text_sha256', 'quality_dimensions', 'review_priority',
            )
        }
        if text_is_public or include_all_text:
            exported['text_refinement']['release_text'] = refinement.get('release_text')
    return exported


def source_catalog_for_family(family):
    path = KNOWLEDGE_SOURCE_CATALOGS.get(family)
    if path is None or not path.exists():
        return {}
    catalog = json.loads(path.read_text(encoding='utf-8'))
    sources = {
        item['source_id']: item
        for item in catalog.get('sources', [])
        if item.get('source_id')
    }
    # Some catalog families share captures but keep their source registries
    # separately. Merge matching IDs so exported references retain the best
    # available URL or capture fingerprint.
    for other_path in KNOWLEDGE_SOURCE_CATALOGS.values():
        if not other_path.exists():
            continue
        for item in json.loads(other_path.read_text(encoding='utf-8')).get('sources', []):
            if item.get('source_id'):
                sources.setdefault(item['source_id'], item)
                if item['source_id'] in sources:
                    sources[item['source_id']] = {
                        **item, **sources[item['source_id']],
                        **{key: value for key, value in item.items()
                           if value and not sources[item['source_id']].get(key)},
                    }
    if family == 'geography':
        aliases = {
            'division_district_list': 'Garhwal Mandal official introduction',
            'division_headquarters': 'Garhwal Mandal official introduction',
            'district_portal': 'Government of Uttarakhand district portal',
            'district_page': 'Government of Uttarakhand district portal',
            'tehsil_list': 'Wikipedia list of tehsils of Uttarakhand',
            'map_lookup': 'OpenStreetMap search',
            'wikipedia_place': 'Wikipedia Garhwal division',
            'wikipedia_geography': 'Wikipedia Garhwal division',
            'division_geography': 'Wikipedia Garhwal division',
            'historic_capital': 'Wikipedia Garhwal division',
            'river_confluence': 'Wikipedia Garhwal division',
            'river_source': 'Wikipedia Garhwal division',
            'mountain_geography': 'Wikipedia Garhwal division',
            'protected_area': 'Wikipedia Garhwal division',
            'government_water_source': 'Garhwal Mandal official introduction',
            'pilgrimage_geography': 'Wikipedia Garhwal division',
        }
        by_name = {item.get('name'): item for item in catalog.get('sources', [])}
        for source_id, name in aliases.items():
            if name in by_name:
                sources[source_id] = by_name[name]
                sources[source_id]['source_id'] = source_id
    return sources


def source_provenance(source_id, source_catalog):
    source = source_catalog.get(source_id) or {}
    result = {'source_id': source_id}
    mapped = {
        'source_url': source.get('url') or source.get('canonical_url') or source.get('source_url'),
        'source_title': source.get('title') or source.get('name'),
        'source_kind': source.get('source_kind'),
        'source_snapshot_sha256': source.get('sha256'),
        'source_capture_id': source.get('capture_id'),
        'source_capture_path': source.get('local_capture'),
        'source_notes': source.get('notes'),
        'source_capture_bytes': source.get('captured_text_bytes'),
    }
    result.update({key: value for key, value in mapped.items() if value not in (None, '', [])})
    return result


def knowledge_row(row, family, source_catalog=None):
    """Add stable IDs and explicit provenance, quality, and rights fields."""
    identity = next(
        (row.get(key) for key in ('id', 'record_id', 'person_id', 'term_id') if row.get(key)),
        None,
    )
    if not identity:
        raise ValueError(f'{family} knowledge record has no stable ID')
    source_catalog = source_catalog or {}
    exported = {**row, 'id': identity, 'knowledge_family': family}
    if not exported.get('provenance'):
        provenance = []
        for field in ('source_ids', 'source_refs', 'evidence'):
            values = exported.get(field) or []
            if isinstance(values, str):
                values = [values]
            provenance.extend(
                source_provenance(value, source_catalog)
                for value in values if isinstance(value, str) and value.strip()
            )
        for field in (
            'source_url', 'wikipedia_url', 'osm_search_url', 'youtube_url',
            'lyrics_sources', 'translation_sources',
        ):
            values = exported.get(field) or []
            if isinstance(values, str):
                values = [values]
            provenance.extend(
                {'source_url': value}
                for value in values if isinstance(value, str) and value.strip()
            )
        exported['provenance'] = provenance
    else:
        exported['provenance'] = [
            {
                **(
                    source_provenance(item.get('source_id'), source_catalog)
                    if item.get('source_id') else {}
                ),
                **item,
            }
            for item in exported['provenance']
            if isinstance(item, dict)
        ]
    exported.setdefault('quality_metadata', {
        'review_status': 'not_reviewed',
        'source_verification_status': (
            exported.get('verification_status')
            or exported.get('ingestion_status')
            or 'not_assessed'
        ),
        'native_reviewed': False,
        'evidence_fields': [
            field for field in (
                'evidence', 'source_refs', 'source_ids', 'source_url',
                'wikipedia_url', 'lyrics_sources', 'translation_sources',
            ) if exported.get(field)
        ],
    })
    exported.setdefault('rights_status', 'not_assessed')
    exported.setdefault('public_rights_basis', [])
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
    files = [str(path.name) for path in paths]
    return {
        'records': count,
        'shards': len(paths),
        'files': files,
        'file_sha256': {path.name: sha256_file(path) for path in paths},
    }


def link_audio(rows, output):
    linked = 0
    seen = set()
    for row in rows:
        digest = row['audio_sha256']
        if digest in seen:
            continue
        seen.add(digest)
        source = (ROOT / row['local_audio_path']).resolve()
        audio_root = (ROOT / 'data/vaani/audio').resolve()
        if source.is_symlink() or not source.is_file() or not source.is_relative_to(audio_root):
            raise ValueError(f'unsafe audio source path: {row["local_audio_path"]}')
        if sha256_file(source) != digest:
            raise ValueError(f'audio SHA-256 mismatch: {row["local_audio_path"]}')
        target = output / content_audio_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            try:
                os.link(source, target)
            except OSError as error:
                if error.errno != errno.EXDEV:
                    raise
                shutil.copy2(source, target)
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
    nonempty_configs = {
        key: value for key, value in report['configs'].items()
        if value.get('records', 0) > 0
    }
    config_names = sorted({key.split('/', 1)[0] for key in nonempty_configs})
    config_count = len(config_names)
    config_blocks = []
    for name in config_names:
        files = []
        for key, value in sorted(nonempty_configs.items()):
            config, split = key.split('/', 1)
            if config != name:
                continue
            files.extend(
                f'  - split: {split}\n    path: data/{name}/{filename}'
                for filename in value.get('files') or [f'{split}-*.jsonl']
            )
        config_blocks.append(
            f'- config_name: {name}\n  data_files:\n' + '\n'.join(files)
        )
    configs_yaml = '\n'.join(config_blocks)
    speech_companion = ''
    if profile_includes_all_data(report['profile']):
        language_header = '- gbm\n- hi\n- en'
        package_summary = (
            f'This complete all-data package contains **{exported_rows:,} records** '
            f'across {config_count} configurations'
        )
        catalog_summary = f'''The `catalog` configuration contains all
**{report['catalog_records']:,} exact-unique collected text records with their full
text values. No catalog text values are redacted. Source, license, rights status,
quality tier, language evidence, and review state remain attached to every row so
research use and any later redistribution decision can be audited.'''
        access_notice = '''> **Access warning:** this all-data profile contains
restricted and rights-pending source content. Keep it local or access-controlled;
do not publish it as an open dataset until every included component is cleared.
It retains all structured records with row-level source, quality, and rights
metadata attached.'''
    else:
        speech_companion = '''\n\n## Linked speech dataset\n\nThe companion [Garhwali Speech dataset](https://huggingface.co/datasets/rushilrawat/garhwali-speech) contains VAANI audio with provider transcripts and separately labeled SraVaani drafts.'''
        language_header = '- gbm'
        package_summary = (
            f'This public-profile package contains **{exported_rows:,} records** '
            f'across {config_count} configurations'
        )
        catalog_summary = f'''The `catalog` configuration publicly accounts for all
**{report['catalog_records']:,} exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
only the protected text value is redacted. Nothing is silently omitted.'''
        excluded = sum(report.get('structured_knowledge_excluded_for_rights', {}).values())
        access_notice = f'''This public profile omits **{excluded:,} structured-knowledge records**
whose provenance does not include an explicit compatible public-rights basis.
They remain intact in the complete all-data package. No source license is
inferred from a URL. The text catalog records each collected text identity and
redacts values without compatible redistribution evidence. Native-speaker
review and dialect annotation are deferred; benchmark and model scores are
automated research results, not native-validated claims.'''
    return f'''---
language:
{language_header}
license: other
task_categories:
- automatic-speech-recognition
- text-generation
- translation
configs:
{configs_yaml}
---

# Garhwali Language Lab

Release: **{report['release_id']}**

{access_notice}

Versioned Garhwali (`gbm`) text, speech, lexicon, instruction, geographic,
historical, literary, music, and university-research resources built by the
Garhwali Language Lab. Available source and review metadata vary by configuration.

{package_summary}, including transcripts for **{report['draft_unique_audio']:,}
unique SraVaani recordings**. {audio_summary}

{catalog_summary}

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
The remaining **{report['draft_audio_grounded_review_records']:,}** structural
outliers also include deterministic re-decoding, waveform activity, and
human-reference calibration evidence. They still require listening review.

The draft layer also preserves **{report['draft_source_label_conflicts']:,}
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).{speech_companion}
'''


def _build_at(output, profile='public', include_audio=False,
              allow_partial_drafts=False, shard_rows=10_000):
    output = prepare_package_output(output)
    report = {
        'release_id': RELEASE_ID,
        'profile': profile,
        'include_audio': include_audio,
        'configs': {},
        'structured_knowledge_excluded_for_rights': {},
    }

    quality_catalog = list(read_jsonl(
        ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
    ))
    parent_quality = {row['text_sha256']: row for row in quality_catalog}
    text_dir = ROOT / 'data/processed/model_ready/splits/text'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(text_dir / f'{split}.jsonl')
        exported_rows = (text_row(row, parent_quality) for row in rows)
        if profile == 'public':
            exported_rows = (
                exported
                for exported in exported_rows
                if exported['language'] == 'gbm'
                and is_public_garhwali_text_row(exported)
            )
        report['configs'][f'text/{split}'] = write_shards(
            exported_rows,
            output / 'data/text', split, shard_rows
        )

    refinement_path = ROOT / 'data/processed/model_ready/text_quality_v2/priority_text.jsonl'
    refinements = {
        row['text_sha256']: row for row in read_jsonl(refinement_path)
    } if refinement_path.exists() else {}
    catalog_rows = [
        catalog_row(
            row,
            include_all_text=profile_includes_all_data(profile),
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
    report['all_collected_text_values_included'] = (
        report['catalog_redacted_text_records'] == 0
    )
    if profile_includes_all_data(profile) and not report['all_collected_text_values_included']:
        raise RuntimeError('All-data profile omitted one or more collected text values')
    report['configs']['catalog/train'] = write_shards(
        catalog_rows, output / 'data/catalog', 'train', shard_rows
    )

    for family, path in KNOWLEDGE_CONFIGS.items():
        if not path.exists():
            raise FileNotFoundError(f'Missing structured knowledge catalog: {path}')
        source_catalog = source_catalog_for_family(family)
        rows = [
            knowledge_row(row, family, source_catalog)
            for row in read_jsonl(path)
        ]
        ids = [row['id'] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate stable IDs in {family}')
        if profile == 'public':
            publishable_rows = [row for row in rows if is_public_knowledge_row(row)]
            report['structured_knowledge_excluded_for_rights'][family] = (
                len(rows) - len(publishable_rows)
            )
            rows = publishable_rows
            if not rows:
                continue
        report['configs'][f'{family}/train'] = write_shards(
            rows, output / f'data/{family}', 'train', shard_rows
        )

    audio_sources = []
    asr_dir = ROOT / 'data/processed/model_ready/splits' / asr_split_directory(profile)
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(asr_dir / f'{split}.jsonl'))
        audio_sources.extend(rows)
        report['configs'][f'asr/{split}'] = write_shards(
            (audio_row(row, 'asr_target_clean', include_audio) for row in rows),
            output / 'data/asr', split, shard_rows,
        )

    queue_path = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
    confidence_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
    verified_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_verified.jsonl'
    quality_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
    raw_drafts_path = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'
    drafts_path = next(
        path for path in (
            verified_drafts_path, confidence_drafts_path,
            quality_drafts_path, raw_drafts_path
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
    audio_review_path = (
        ROOT / 'data/processed/model_ready/transcripts/'
        'sravaani_recovery_audio_grounded_review.jsonl'
    )
    audio_review_rows = list(read_jsonl(audio_review_path)) \
        if audio_review_path.exists() else []
    unique_drafts = attach_audio_grounded_review(unique_drafts, audio_review_rows)
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
    report['draft_audio_grounded_review_records'] = sum(
        bool(row.get('audio_grounded_review')) for row in unique_drafts
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
        (lexicon_row(row) for row in lexicon),
        output / 'data/lexicon', 'train', shard_rows,
    )

    instructions_dir = ROOT / 'data/processed/model_ready/instructions_v0.2'
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(instructions_dir / f'{split}.jsonl'))
        if profile == 'public':
            rows = [row for row in rows if is_public_text_row(row)]
        rows = refresh_acceptable_responses(rows)
        report['configs'][f'instructions/{split}'] = write_shards(
            (with_public_rights_basis(row) for row in rows),
            output / 'data/instructions', split, shard_rows,
        )

    removed_audio_files = 0 if include_audio else remove_packaged_audio(output)
    link_report = link_audio(audio_sources, output) if include_audio else {'new': 0, 'total': 0}
    report['linked_audio_files'] = link_report['total']
    report['newly_linked_audio_files'] = link_report['new']
    report['removed_audio_files'] = removed_audio_files
    output.mkdir(parents=True, exist_ok=True)
    (output / 'README.md').write_text(dataset_card(report), encoding='utf-8')
    for name in ('LICENSE_POLICY.md', 'ATTRIBUTION.md', 'REMOVAL_POLICY.md'):
        shutil.copy2(ROOT / name, output / name)
    (output / 'manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    report['manifest_sha256'] = sha256_file(output / 'manifest.json')
    return report


def build(output, profile='public', include_audio=False, allow_partial_drafts=False,
          shard_rows=10_000):
    """Build in a sibling staging directory, then replace the managed package."""
    output = Path(output)
    managed = {DEFAULT_OUTPUT.resolve(), ALL_DATA_OUTPUT.resolve()}
    if output.exists() and output.resolve() not in managed:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.building-'
    ))
    staging.rmdir()
    backup = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.previous-'
    ))
    backup.rmdir()
    try:
        report = _build_at(
            staging, profile=profile, include_audio=include_audio,
            allow_partial_drafts=allow_partial_drafts, shard_rows=shard_rows,
        )
        if output.exists():
            output.rename(backup)
        staging.rename(output)
        if backup.exists():
            shutil.rmtree(backup)
        return report
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and not output.exists():
            backup.rename(output)
        elif backup.exists():
            shutil.rmtree(backup)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument(
        '--profile', choices=('public', 'all-data'),
        default='public',
    )
    parser.add_argument('--include-audio', action='store_true')
    parser.add_argument('--allow-partial-drafts', action='store_true')
    parser.add_argument('--shard-rows', type=int, default=10_000)
    args = parser.parse_args()
    output = args.output or (
        ALL_DATA_OUTPUT if profile_includes_all_data(args.profile) else DEFAULT_OUTPUT
    )
    print(json.dumps(build(
        output,
        profile=args.profile,
        include_audio=args.include_audio,
        allow_partial_drafts=args.allow_partial_drafts,
        shard_rows=args.shard_rows,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
