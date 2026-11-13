"""Row builders for the Hugging Face package configs.

Turns prepared corpus records into the exported row shapes for text, catalog,
ASR, lexicon, knowledge, PahariLI, and the expansion views.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from functools import lru_cache

from hf_rights import (
    META_OMNILINGUAL_TRAINING_DECISION,
    catalog_noncommercial_basis,
    catalog_policy_basis,
    individual_word_fact_basis,
    is_publishable_provenance,
    noncommercial_catalog_provenance,
    open_bible_stories_provenance,
    panos_reproduction_policy_provenance,
    pib_policy_catalog_provenance,
    provenance_items,
    publishable_provenance_items,
    signed_off_public_domain_provenance,
)
from hf_source_registry import SOURCE_URLS, source_record_locator

from garhwali_lab.paths import ROOT
from garhwali_lab.text import content_key as normalized_text_key

SOURCE_ATTRIBUTION_OVERLAY_PATH = ROOT / 'research/source-attribution-overlays-2026-10-05.json'
UPSTREAM_SPLIT_OVERLAP_PATH = ROOT / 'research/huggingface-upstream-split-overlap-2026-10-05.json'
PAHARILI_GBM_ROWS_PATH = ROOT / 'experimental/paharili_gbm.jsonl'
PAHARILI_LICENSE_PATH = ROOT / 'sources/online/paharili/c71d239df91726fc-LICENSE'
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


def content_audio_path(audio_sha256):
    return f'audio/{audio_sha256[:2]}/{audio_sha256}.wav'


def public_speaker_id(row):
    speaker = row.get('speaker_id')
    if speaker in (None, '', 'NA'):
        return None
    value = f"{row.get('source', '')}|{speaker}".encode()
    return f'speaker_{hashlib.sha256(value).hexdigest()[:16]}'


def audio_row(row, transcript_field, include_audio_reference=True,
              serialize_evidence=False):
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
    if serialize_evidence:
        # Draft evidence is sparse and nested. JSON strings keep one stable
        # Arrow schema across shards while preserving every nested value.
        json_fields = (
            'machine_transcript_quality', 'recovery_confidence',
            'source_conflict_evidence', 'recovery_adjudication',
            'recovery_third_checkpoint', 'audio_grounded_review',
        )
        for key in json_fields:
            value = row.get(key)
            exported[key] = (
                json.dumps(value, ensure_ascii=False, sort_keys=True,
                           separators=(',', ':'))
                if value is not None else ''
            )
        for key in ('quality_flags', 'training_quality_flags'):
            exported[key] = json.dumps(
                row.get(key) or [], ensure_ascii=False, separators=(',', ':')
            )
        exported['active_for_source_error_analysis'] = bool(
            row.get('active_for_source_error_analysis', False)
        )
        exported['language_scope_status'] = row.get('language_scope_status') or ''
    if include_audio_reference:
        exported['audio'] = content_audio_path(row['audio_sha256'])
    # Stable string typing prevents Dataset Viewer/Parquet inference from
    # treating early null-only rows as a Null feature before later IDs appear.
    exported['speaker_id'] = public_speaker_id(row) or ''
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


def source_record_ids(row):
    """Return record-level source IDs from corpus or benchmark provenance."""
    values = []
    for field in ('provenance', 'sources'):
        source_rows = row.get(field) or []
        if isinstance(source_rows, dict):
            source_rows = source_rows.get('provenance') or []
        if isinstance(source_rows, list):
            values.extend(source_rows)
    return {
        item.get('record_id') for item in values
        if isinstance(item, dict) and item.get('record_id')
    }


def build_paharili_gbm_rows(source_rows, existing_text_rows):
    """Build a traceable Garhwali-only PahariLI view without duplicate text rows."""
    source_rows = list(source_rows)
    groups = {}
    garhwali_rows = []
    seen_record_ids = set()
    for row in source_rows:
        if row.get('iso_639_3') != 'gbm' or row.get('upstream_label') != 'gbm':
            continue
        record_id = str(row.get('record_id') or '')
        if record_id in seen_record_ids:
            raise ValueError(f'Duplicate PahariLI record ID: {record_id}')
        seen_record_ids.add(record_id)
        if not record_id.startswith('paharili_gbm:'):
            raise ValueError(f'Invalid PahariLI record ID: {record_id!r}')
        text = str(row.get('text_original') or row.get('text_normalized') or '')
        key = normalized_text_key(text)
        if not key:
            raise ValueError(f'Empty Garhwali PahariLI record: {record_id}')
        origin = row.get('provenance') or {}
        if not origin.get('url') or not re.fullmatch(
            r'[0-9a-f]{64}', str(origin.get('sha256') or '')
        ):
            raise ValueError(f'Missing raw-file provenance for {record_id}')
        if row.get('split') not in {'train', 'test'}:
            raise ValueError(
                f'Unexpected upstream PahariLI split for {record_id}: {row.get("split")!r}'
            )
        groups.setdefault(key, {})[record_id] = row
        garhwali_rows.append(row)

    existing_by_key = {}
    for row in existing_text_rows:
        for field in (
            'text', 'release_text', 'text_normalized', 'text_original',
            'transcript', 'asr_target_clean', 'machine_transcript', 'form',
        ):
            value = row.get(field)
            key = normalized_text_key(value) if isinstance(value, str) else ''
            if key:
                existing_by_key.setdefault(key, []).append(row)

    output = []
    already_present = 0
    already_present_source_ids = 0
    source_overlap_groups = 0
    split_records = Counter()
    for key, group in sorted(groups.items()):
        group_rows = list(group.values())
        record_ids = sorted(group)
        source_splits = sorted({str(row['split']) for row in group_rows})
        if key in existing_by_key:
            represented_ids = set().union(*(
                source_record_ids(existing)
                for existing in existing_by_key[key]
            ))
            missing_ids = set(record_ids) - represented_ids
            if missing_ids:
                raise ValueError(
                    'PahariLI text already exists in another release config but '
                    f'its source IDs are not preserved: {sorted(missing_ids)[:5]}'
                )
            already_present += 1
            already_present_source_ids += len(record_ids)
            continue

        split = 'source_overlap' if len(source_splits) > 1 else source_splits[0]
        source_overlap_groups += split == 'source_overlap'
        split_records[split] += 1
        source_texts = sorted({
            str(row.get('text_original') or row.get('text_normalized') or '')
            for row in group_rows
        })
        provenance = []
        for record_id in record_ids:
            row = group[record_id]
            origin = row['provenance']
            split_name = str(row['split'])
            try:
                source_record_index = int(record_id.rsplit(':', 1)[1])
            except (IndexError, ValueError) as exc:
                raise ValueError(f'Invalid PahariLI source index: {record_id}') from exc
            provenance.append({
                'source_id': 'paharili_gbm',
                'source_ref_id': 'PahariLI',
                'record_id': record_id,
                'source_url': str(row.get('source_url') or ''),
                'source_file_url': str(origin['url']),
                'source_file_sha256': str(origin['sha256']),
                'source_split': split_name,
                'source_record_index': source_record_index,
                'source_line_number': source_record_index + 1,
                'iso_639_3': 'gbm',
                'upstream_label': 'gbm',
                'license_id': str(row.get('license_id') or ''),
                'license_url': str(row.get('license_url') or ''),
                'rights_status': str(row.get('rights_status') or ''),
                'attribution': str(row.get('attribution') or ''),
            })

        first = group_rows[0]
        license_id = str(first.get('license_id') or '')
        rights_status = str(first.get('rights_status') or 'not_assessed')
        flags = sorted({
            str(flag)
            for row in group_rows
            for flag in row.get('quality_flags') or []
            if flag
        })
        text = source_texts[0]
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        output.append({
            'id': f'paharili-gbm-{digest}',
            'text': text,
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
            'normalized_text_key_sha256': digest,
            'source_text_variants': source_texts,
            'source_record_ids': record_ids,
            'upstream_splits': source_splits,
            'split': split,
            'split_assignment': (
                'upstream_paharili_train_test; '
                'cross-split text grouped in source_overlap'
            ),
            'language': 'gbm',
            'iso_639_3': 'gbm',
            'language_name': 'Garhwali',
            'language_label_source': (
                'PahariLI upstream label; not independently reviewed'
            ),
            'script': str(first.get('script') or 'Deva'),
            'genre': 'mixed_web_and_scripture',
            'upstream_task': 'text language identification',
            'provenance': provenance,
            'attribution': 'Rachana Gusain, PahariLI repository',
            'license_id': license_id,
            'license_url': str(first.get('license_url') or ''),
            'rights_status': rights_status,
            'reuse_scope': (
                'The PahariLI repository declares Apache-2.0; sentence-level '
                'origins and redistribution rights are not independently established.'
            ),
            'license_labels': [license_id] if license_id else [],
            'quality_status': 'unreviewed; no native-language review',
            'quality_flags': flags,
            'record_quality_flags': flags,
            'native_reviewed': False,
            'training_eligible': False,
            'experimental_training_eligible': split == 'train',
            'recommended_for_general_language_model_training': False,
        })

    metrics = {
        'input_records': len(source_rows),
        'garhwali_source_records': len(garhwali_rows),
        'excluded_non_garhwali_records': len(source_rows) - len(garhwali_rows),
        'normalized_unique_source_texts': len(groups),
        'collapsed_duplicate_source_records': len(garhwali_rows) - len(groups),
        'already_present_in_existing_configs': already_present,
        'source_record_ids_already_in_existing_configs': already_present_source_ids,
        'new_records': len(output),
        'new_source_record_ids': sum(len(row['source_record_ids']) for row in output),
        'all_source_record_ids_preserved': (
            already_present_source_ids
            + sum(len(row['source_record_ids']) for row in output)
            == len(garhwali_rows)
        ),
        'source_split_overlap_groups': source_overlap_groups,
        'split_records': dict(sorted(split_records.items())),
    }
    return output, metrics


@lru_cache(maxsize=1)
def upstream_split_overlap_ids():
    """Return audited source IDs whose upstream component split is held out."""
    if not UPSTREAM_SPLIT_OVERLAP_PATH.is_file():
        raise FileNotFoundError(
            f'Missing upstream split audit: {UPSTREAM_SPLIT_OVERLAP_PATH}'
        )
    payload = json.loads(
        UPSTREAM_SPLIT_OVERLAP_PATH.read_text(encoding='utf-8')
    )
    if payload.get('schema_version') != 'garhwali-upstream-split-overlap-v1':
        raise ValueError('Unsupported upstream split overlap audit schema')
    direct_ids = payload.get('meta_upstream_eval_record_ids')
    aggregate_rows = payload.get('community_rows_with_eval_split_text_matches')
    if not isinstance(direct_ids, list) or not isinstance(aggregate_rows, list):
        raise ValueError('Upstream split overlap audit has incomplete ID lists')
    aggregate_ids = {
        str(row['record_id'])
        for row in aggregate_rows
        if isinstance(row, dict) and row.get('record_id')
    }
    return set(map(str, direct_ids)), aggregate_ids


def route_upstream_split_overlap(row, direct_eval_ids, aggregate_eval_ids):
    """Keep a row public but move a train row with upstream eval lineage aside."""
    result = dict(row)
    record_ids = source_record_ids(result)
    direct_matches = sorted(record_ids & direct_eval_ids)
    aggregate_matches = sorted(record_ids & aggregate_eval_ids)
    vaani_test_matches = sorted({
        str(item.get('record_id'))
        for item in provenance_items(result)
        if isinstance(item, dict)
        and (
            item.get('source_id') in {
                'vaani-official-test-remainder',
                'vaani-transcription-part',
            }
            or item.get('canonical_transcript_source')
            == 'ARTPARK-IISc/Vaani-transcription-part'
        )
        and item.get('transcription_split') == 'test'
        and item.get('record_id')
    })
    if direct_matches and aggregate_matches:
        status = 'upstream_record_and_transcript_match'
    elif direct_matches:
        status = 'upstream_eval_record_id_match'
    elif aggregate_matches:
        status = 'upstream_eval_transcript_match'
    elif vaani_test_matches:
        status = 'upstream_vaani_test_source_record_match'
    else:
        status = 'no_upstream_eval_match_detected'
    result['source_split_overlap_status'] = status
    result['source_split_overlap_source_ids'] = sorted(
        set(direct_matches + aggregate_matches + vaani_test_matches)
    )
    if result.get('split') == 'train' and status != 'no_upstream_eval_match_detected':
        result['original_split'] = result.get('original_split') or 'train'
        result['split'] = 'source_overlap'
        assignment = str(result.get('split_assignment') or '').strip()
        reason = (
            'upstream dev/test source overlap; text retained and routed to '
            'source_overlap instead of default train'
        )
        result['split_assignment'] = f'{assignment}; {reason}'.strip('; ')
        result['recommended_for_training'] = False
    return result


@lru_cache(maxsize=1)
def source_attribution_overlays():
    """Load audited, content-free creator and revision metadata once per build."""
    if not SOURCE_ATTRIBUTION_OVERLAY_PATH.is_file():
        return {}
    payload = json.loads(SOURCE_ATTRIBUTION_OVERLAY_PATH.read_text(encoding='utf-8'))
    if payload.get('schema_version') != 'garhwali-source-attribution-overlay-v1':
        raise ValueError('Unsupported source attribution overlay schema')
    records = payload.get('records')
    if not isinstance(records, dict):
        raise ValueError('Source attribution overlay has no record map')
    return records


def enrich_source_attribution(item, overlays=None):
    """Overlay audited attribution metadata without replacing source content."""
    item = dict(item)
    record_id = item.get('record_id')
    overlay = (source_attribution_overlays() if overlays is None else overlays).get(record_id)
    if not overlay:
        return item
    if overlay.get('source_id') != item.get('source_id'):
        raise ValueError(f'Source ID mismatch in attribution overlay for {record_id}')
    return {**item, **overlay}


def comparable_text_rows(rows, field):
    """Expose selected text-bearing fields to the shared exact-text deduper."""
    for row in rows:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            yield {**row, 'text': value}


def build_catalog_text_expansion(catalog_rows, existing_text_rows, benchmark_eval_rows=()):
    """Promote strict, rights-cleared catalog text that is net-new to text views.

    This is a separate train-only expansion view. It excludes exact normalized
    text already in existing text-bearing views, source record IDs used by
    validation/test or frozen benchmark validation/test, and internal duplicates.
    Source-page-family isolation is not claimed.
    """
    existing_text_rows = list(existing_text_rows)
    existing_ids = {row.get('id') for row in existing_text_rows}
    existing_text_keys = {
        normalized_text_key(row.get('text')) for row in existing_text_rows
        if normalized_text_key(row.get('text'))
    }
    evaluation_rows = [
        row for row in existing_text_rows
        if row.get('split') in {'validation', 'test'}
    ] + list(benchmark_eval_rows)
    evaluation_record_ids = set().union(
        *(source_record_ids(row) for row in evaluation_rows)
    ) if evaluation_rows else set()

    candidates = []
    counters = Counter()
    for row in catalog_rows:
        if not row.get('text'):
            continue
        if row.get('redistribution_status') != 'rights_cleared':
            continue
        if row.get('language_bucket') != 'garhwali_candidate':
            continue
        if (row.get('quality_v2') or {}).get('tier') != 'strict_gold_candidate':
            continue
        rights_basis = row.get('public_rights_basis') or []
        if not rights_basis or not all(
            is_publishable_provenance(item) for item in rights_basis
        ):
            continue
        sources = row.get('sources') or []
        languages = {
            item.get('iso_639_3') for item in sources
            if isinstance(item, dict) and item.get('iso_639_3')
        }
        if languages != {'gbm'}:
            continue
        counters['strict_rights_language_candidates'] += 1
        if row.get('id') in existing_ids:
            counters['excluded_exact_existing_identity'] += 1
            continue
        if source_record_ids({'sources': sources}) & evaluation_record_ids:
            counters['excluded_evaluation_source_record'] += 1
            continue
        text_key = normalized_text_key(row.get('text'))
        if not text_key or text_key in existing_text_keys:
            counters['excluded_normalized_existing_text'] += 1
            continue
        candidates.append((text_key, row))

    selected = {}
    for text_key, row in sorted(candidates, key=lambda item: item[1].get('id') or ''):
        if text_key in selected:
            counters['excluded_normalized_internal_duplicate'] += 1
            continue
        selected[text_key] = row

    output = []
    for row in selected.values():
        enriched = dict(row)
        sources = row.get('sources') or []
        quality_flags = list(row.get('record_quality_flags') or [])
        enriched.update({
            'language': 'gbm',
            'source_languages': ['gbm'],
            'language_buckets': ['garhwali_candidate'],
            'quality_tiers': ['strict_gold_candidate'],
            'recommended_for_training': False,
            'script': (row.get('language_quality') or {}).get('script_profile', {}).get('script', 'Other'),
            'split': 'train',
            'duplicate_component_id': None,
            'original_split': 'catalog/train',
            'split_assignment': 'strict rights-cleared catalog addition; normalized-text and project evaluation-source overlaps excluded; known upstream dev/test overlaps route to source_overlap; source-page-family isolation not assessed',
            'quality_flags': quality_flags,
            'provenance': list(row.get('public_rights_basis') or []),
        })
        enriched['recommended_for_training'] = recommended_text_training_row(enriched)
        output.append(enriched)
    counters['records'] = len(output)
    counters['recommended_for_training'] = sum(
        row['recommended_for_training'] for row in output
    )
    return output, dict(counters)


def build_catalog_text_resources(catalog_rows, existing_text_rows, benchmark_eval_rows=()):
    """Expose additional rights-cleared catalog text as a non-evaluation resource.

    This intentionally has higher recall than text_expansion: records do not
    need to meet the strict training tier, but must be Garhwali-only, have a
    recorded redistribution basis, be new after normalized cross-config
    deduplication, and have no source-record match to held-out evaluation data.
    Every row remains explicitly ineligible for benchmark/evaluation use.
    """
    existing_text_rows = list(existing_text_rows)
    existing_ids = {row.get('id') for row in existing_text_rows}
    existing_text_keys = {
        normalized_text_key(row.get('text')) for row in existing_text_rows
        if normalized_text_key(row.get('text'))
    }
    evaluation_rows = [
        row for row in existing_text_rows
        if row.get('split') in {'validation', 'test'}
    ] + list(benchmark_eval_rows)
    evaluation_record_ids = set().union(
        *(source_record_ids(row) for row in evaluation_rows)
    ) if evaluation_rows else set()

    candidates = []
    counters = Counter()
    for row in catalog_rows:
        if not row.get('text'):
            continue
        rights_status = row.get('redistribution_status')
        if rights_status == 'rights_cleared':
            rights_basis = row.get('public_rights_basis') or []
        elif rights_status == 'rights_cleared_noncommercial_sharealike':
            rights_basis = row.get('noncommercial_rights_basis') or []
        else:
            continue
        if not rights_basis or not all(
            is_publishable_provenance(item)
            or (
                item.get('license_id') == 'CC-BY-NC-SA-4.0'
                and item.get('commercial_use_status') == 'noncommercial_only'
                and bool(item.get('attribution'))
                and bool(item.get('source_url'))
            )
            for item in rights_basis
        ):
            continue
        if row.get('language_bucket') != 'garhwali_candidate':
            continue
        sources = row.get('sources') or []
        languages = {
            item.get('iso_639_3') for item in sources
            if isinstance(item, dict) and item.get('iso_639_3')
        }
        if languages != {'gbm'}:
            continue
        counters['rights_and_language_candidates'] += 1
        if row.get('id') in existing_ids:
            counters['excluded_existing_identity'] += 1
            continue
        if source_record_ids({'sources': sources}) & evaluation_record_ids:
            counters['excluded_evaluation_source_record'] += 1
            continue
        text_key = normalized_text_key(row.get('text'))
        if not text_key or text_key in existing_text_keys:
            counters['excluded_normalized_existing_text'] += 1
            continue
        candidates.append((text_key, row))

    selected = {}
    for text_key, row in sorted(candidates, key=lambda item: item[1].get('id') or ''):
        if text_key in selected:
            counters['excluded_normalized_internal_duplicate'] += 1
            continue
        selected[text_key] = row

    output = []
    for row in selected.values():
        rights_basis = (
            row.get('noncommercial_rights_basis') or []
            if row.get('redistribution_status') == 'rights_cleared_noncommercial_sharealike'
            else row.get('public_rights_basis') or []
        )
        enriched = dict(row)
        enriched.update({
            'language': 'gbm',
            'source_languages': ['gbm'],
            'split': 'train',
            'split_assignment': (
                'supplementary redistributable resource; normalized duplicates and '
                'project held-out evaluation source-record overlaps excluded; '
                'upstream dev/test overlaps route to source_overlap; not an '
                'evaluation split'
            ),
            'intended_use': ['language_resource_lookup', 'research'],
            'recommended_for_training': False,
            'recommended_for_evaluation': False,
            'provenance': list(rights_basis),
            'quality_flags': list(row.get('record_quality_flags') or []),
        })
        output.append(enriched)
    counters['records'] = len(output)
    counters['characters'] = sum(len(row['text']) for row in output)
    counters['whitespace_words'] = sum(len(row['text'].split()) for row in output)
    counters['recommended_for_training'] = sum(
        bool(row.get('recommended_for_training')) for row in output
    )
    return output, dict(counters)


def recommended_text_training_row(row):
    if row.get('split') not in (None, 'train'):
        return False
    rights_basis = row.get('public_rights_basis') or []
    provenance = row.get('provenance') or row.get('sources') or []
    source_rows = [
        item for item in [*provenance, *rights_basis]
        if isinstance(item, dict)
    ]
    source_training_flags = [
        item['training_eligible'] for item in source_rows
        if isinstance(item.get('training_eligible'), bool)
    ]
    source_quality_flags = {
        flag
        for item in source_rows
        for flag in item.get('quality_flags') or []
        if isinstance(flag, str) and flag
    }
    if (
        (source_training_flags and not any(source_training_flags))
        or source_quality_flags
        or row.get('record_quality_flags')
    ):
        return False
    return bool(
        row.get('language') == 'gbm'
        and set(row.get('source_languages') or []) == {'gbm'}
        and row.get('language_buckets') == ['garhwali_candidate']
        and 'strict_gold_candidate' in (row.get('quality_tiers') or [])
        and not row.get('quality_flags')
        and rights_basis
        and all(is_publishable_provenance(item) for item in rights_basis)
    )


def apply_meta_training_rights_decision(row):
    """Apply the exact Meta CC BY-4.0 decision to a derived row, not its source."""
    result = dict(row)
    for field in ('provenance', 'public_rights_basis'):
        items = result.get(field)
        if not isinstance(items, list):
            continue
        decided = []
        for item in items:
            if not isinstance(item, dict):
                decided.append(item)
                continue
            matches = all(
                item.get(key) == META_OMNILINGUAL_TRAINING_DECISION[key]
                for key in (
                    'source_id', 'source_url', 'rights_status', 'license_id',
                    'license_url', 'rights_evidence',
                )
            )
            if not matches:
                decided.append(item)
                continue
            updated = dict(item)
            updated['training_eligible_before_project_decision'] = item.get(
                'training_eligible'
            )
            updated['training_eligible'] = True
            updated['training_eligibility_decision_id'] = (
                META_OMNILINGUAL_TRAINING_DECISION['decision_id']
            )
            updated['training_eligibility_evidence'] = list(
                META_OMNILINGUAL_TRAINING_DECISION['evidence_urls']
            )
            updated['training_eligibility_checked_at'] = (
                META_OMNILINGUAL_TRAINING_DECISION['checked_at']
            )
            decided.append(updated)
        result[field] = decided
    return result


def build_quality_screened_meta_text(rows_by_config):
    """Select non-empty, strict, train-only Meta text without editing source rows."""
    selected = []
    seen_ids = set()
    seen_text = {}
    metrics = {
        'candidate_rows_evaluated': 0,
        'blank_excluded': 0,
        'eligibility_excluded': 0,
        'normalized_duplicate_excluded': 0,
        'duplicate_exclusions': [],
        'selected_rows': 0,
        'whitespace_words': 0,
        'characters': 0,
    }
    for config in ('text', 'text_expansion'):
        for row in rows_by_config.get(config, []):
            metrics['candidate_rows_evaluated'] += 1
            text = row.get('text')
            if not isinstance(text, str) or not text.strip():
                metrics['blank_excluded'] += 1
                continue
            decided = apply_meta_training_rights_decision(row)
            if not recommended_text_training_row(decided):
                metrics['eligibility_excluded'] += 1
                continue
            record_id = str(decided.get('id') or '')
            text_key = normalized_text_key(text)
            if not record_id:
                raise ValueError('Quality-screened text row is missing a stable ID')
            if record_id in seen_ids:
                raise ValueError(f'Duplicate quality-screened record ID: {record_id}')
            if not text_key:
                metrics['blank_excluded'] += 1
                continue
            if text_key in seen_text:
                metrics['normalized_duplicate_excluded'] += 1
                metrics['duplicate_exclusions'].append({
                    'excluded_id': record_id,
                    'retained_id': seen_text[text_key],
                    'normalized_text_key_sha256': hashlib.sha256(
                        text_key.encode('utf-8')
                    ).hexdigest(),
                })
                continue
            seen_ids.add(record_id)
            seen_text[text_key] = record_id
            decided.update({
                'source_config': config,
                'training_profile': 'strict_auto_screened_meta_gbm_v1',
                'training_eligibility_decision_id': (
                    META_OMNILINGUAL_TRAINING_DECISION['decision_id']
                ),
                'upstream_recommended_for_training': bool(
                    row.get('recommended_for_training', False)
                ),
                'recommended_for_training': True,
                'project_recommendation_status': 'experimental_training_candidate',
                'native_reviewed': False,
            })
            selected.append(decided)
            metrics['whitespace_words'] += len(text.split())
            metrics['characters'] += len(text)
    metrics['selected_rows'] = len(selected)
    return selected, metrics


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
        'original_split': row.get('original_split') or '',
        'split_assignment': row.get('split_assignment') or '',
        'quality_flags': row.get('quality_flags') or [],
        'provenance': [
            enrich_source_attribution(item) for item in provenance_items(row)
        ],
        'public_rights_basis': [
            catalog_provenance(item) for item in publishable_provenance_items(row)
        ],
    }
    exported['recommended_for_training'] = recommended_text_training_row(exported)
    return exported


def with_public_rights_basis(row):
    enriched = dict(row)
    enriched['provenance'] = [
        enrich_source_attribution(item) for item in provenance_items(row)
    ]
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
    item = enrich_source_attribution(item)
    item = (
        signed_off_public_domain_provenance(item)
        or open_bible_stories_provenance(item)
        or noncommercial_catalog_provenance(item)
        or pib_policy_catalog_provenance(item)
        or panos_reproduction_policy_provenance(item)
        or item
    )
    keep = (
        'source_id', 'source_url', 'source_title', 'source_kind',
        'source_snapshot_sha256', 'source_capture_id', 'source_capture_path',
        'source_notes', 'source_capture_bytes', 'record_id', 'source_revision',
        'source_history_url', 'source_title', 'item_url', 'iso_639_3', 'genre', 'script',
        'transcription_split', 'main_split', 'canonical_transcript_source',
        'license', 'license_id', 'license_url', 'rights_status', 'quality_flags',
        'training_eligible', 'experimental_training_eligible',
        'rights_evidence', 'attribution', 'attribution_name', 'contributor',
        'contributor_profile_url', 'contributor_added_date', 'attribution_status',
        'attribution_evidence_url', 'attribution_evidence_sha256',
        'attribution_evidence_retrieved_at', 'source_api_url', 'api_retrieved_at',
        'upstream_owner', 'upstream_orphaned', 'upstream_unapproved',
        'commercial_use_status', 'model_training_status',
        'third_party_material_included', 'sharealike_required',
        'permitted_audiences',
        'source_pdf', 'source_pdf_sha256', 'pdf_page', 'title', 'author',
        'publication_year', 'extraction_method', 'modifications',
        'rights_decision_ledger',
    )
    result = {key: item.get(key) for key in keep if item.get(key) not in (None, '', [])}
    for key, value in source_record_locator(item).items():
        result.setdefault(key, value)
    if not result.get('source_url') and result.get('source_id') in SOURCE_URLS:
        result['source_url'] = SOURCE_URLS[result['source_id']]
    return result


def catalog_row(row, include_all_text=False, refinement=None):
    items = provenance_items(row)
    rights_basis = publishable_provenance_items(row)
    noncommercial_basis = catalog_noncommercial_basis(row)
    policy_basis = catalog_policy_basis(row)
    text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    factual_basis = individual_word_fact_basis(row, text)
    distributable = bool(
        rights_basis or noncommercial_basis or policy_basis or factual_basis
    )
    text_is_public = distributable
    if rights_basis:
        redistribution_status = 'rights_cleared'
        commercial_use_status = 'permitted_under_row_level_license'
    elif noncommercial_basis:
        redistribution_status = 'rights_cleared_noncommercial_sharealike'
        commercial_use_status = 'noncommercial_only'
    elif policy_basis:
        redistribution_status = 'reproduced_under_source_policy'
        commercial_use_status = (
            'not_authorized_by_source_policy'
            if any(item.get('commercial_use_status') == 'not_authorized_by_source_policy'
                   for item in policy_basis)
            else 'not_explicitly_addressed_by_source_policy'
        )
    elif factual_basis:
        redistribution_status = 'individual_word_fact'
        commercial_use_status = 'no_source_license_claimed_for_single_word'
    else:
        redistribution_status = 'rights_pending'
        commercial_use_status = 'not_cleared'
    sharealike_required = any(
        item.get('license_id') in {'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0'}
        for item in rights_basis + noncommercial_basis
    )
    exported = {
        'id': row['text_sha256'],
        'split': row.get('split'),
        'text': text if distributable or include_all_text else None,
        'text_sha256': row['text_sha256'],
        'source_text_sha256': row['text_sha256'],
        'release_text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'text_character_count': len(text),
        'content_included': distributable or include_all_text,
        'active_for_quality_work': True,
        'text_publicly_available': text_is_public,
        'redistribution_status': redistribution_status,
        'commercial_use_status': commercial_use_status,
        'sharealike_required': sharealike_required,
        'redaction_reason': None if text_is_public or include_all_text else 'source_rights_do_not_permit_public_text_redistribution',
        'language_bucket': row.get('language_bucket'),
        'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'),
        'genre_quality': row.get('genre_quality'),
        'surface_quality': row.get('quality'),
        'quality_v2': row.get('quality_v2'),
        'sources': [
            {key: value for key, value in catalog_provenance(item).items()
             if not factual_basis or key != 'record_id'}
            for item in items
        ],
        'public_rights_basis': [catalog_provenance(item) for item in rights_basis + policy_basis],
        'noncommercial_rights_basis': [
            catalog_provenance(item) for item in noncommercial_basis
        ],
        'factual_publication_basis': factual_basis,
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


PUBLIC_FACT_FIELDS = {
    'geography': (
        'name', 'name_local', 'division', 'districts', 'coordinates',
        'coordinates_status', 'place_type', 'wikipedia_title', 'wikipedia_url',
        'osm_query', 'osm_search_url', 'evidence',
    ),
    'historical_terms': (
        'term', 'term_local', 'name_variants', 'period', 'term_type', 'source_refs',
    ),
    'literary_people': (
        'canonical_name', 'aliases', 'associated_works', 'roles', 'source_ids',
        'verification_status',
    ),
    'literary_works': (
        'title', 'title_variants', 'creators', 'date_or_period', 'language_scope',
        'work_type', 'source_ids', 'ingestion_status',
    ),
    'popular_songs': (
        'title', 'artists', 'genre', 'language', 'caption_status', 'youtube_url',
        'youtube_video_id', 'lyrics_sources', 'translation_sources',
    ),
    'university_research': (
        'title', 'creators', 'institution', 'year', 'resource_type', 'language_scope',
        'topics', 'source_authority', 'source_url', 'visibility', 'access_level',
        'already_covered_by', 'ingestion_status',
    ),
}

PUBLIC_FACT_METADATA_FIELDS = {
    'id', 'knowledge_family', 'record_scope', 'rights_status',
    'expressive_source_content_included', 'omitted_content_fields',
    'provenance', 'public_metadata_note', 'quality_metadata',
    'reuse_scope', 'license_labels', 'quality_status', 'record_quality_flags',
}


def is_public_factual_metadata_row(row, family):
    """Validate the narrow metadata-only projection without asserting a license."""
    if family not in PUBLIC_FACT_FIELDS:
        return False
    return (
        row.get('knowledge_family') == family
        and row.get('record_scope') == 'factual_bibliographic_metadata_only'
        and row.get('rights_status') == 'metadata_only; no license asserted for underlying work'
        and row.get('expressive_source_content_included') is False
        and set(row).issubset(set(PUBLIC_FACT_FIELDS[family]) | PUBLIC_FACT_METADATA_FIELDS)
    )


def public_factual_metadata_row(row, family):
    """Release citation-level facts while omitting unlicensed source prose/content."""
    if family not in PUBLIC_FACT_FIELDS:
        raise ValueError(f'No factual-metadata projection for {family}')
    exported = {
        key: row[key] for key in PUBLIC_FACT_FIELDS[family]
        if key in row and row[key] not in (None, '', [])
    }
    exported.update({
        'id': row['id'],
        'knowledge_family': family,
        'record_scope': 'factual_bibliographic_metadata_only',
        'rights_status': 'metadata_only; no license asserted for underlying work',
        'expressive_source_content_included': False,
        'omitted_content_fields': [
            'extended_notes', 'source_passages', 'abstracts_or_summaries',
            'song_lyrics', 'translations', 'full_work_text',
        ],
        'provenance': [
            {
                key: item[key] for key in (
                    'source_id', 'source_url', 'source_title', 'source_kind',
                    'source_snapshot_sha256', 'source_capture_path', 'record_id',
                ) if item.get(key) not in (None, '', [])
            }
            for item in row.get('provenance') or []
            if isinstance(item, dict)
        ],
        'public_metadata_note': (
            'Only names, titles, dates, categories, identifiers, and source citations '
            'are included. This row does not license the underlying book, article, '
            'song, recording, or source-page prose.'
        ),
        'quality_metadata': {
            key: value for key, value in (row.get('quality_metadata') or {}).items()
            if key in {
                'review_status', 'source_verification_status',
                'native_reviewed', 'evidence_fields',
            }
        },
    })
    return exported
