#!/usr/bin/env python3
"""Audit the tracked release index against the upload-ready dataset package."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from datetime import date
from pathlib import Path

from build_huggingface_dataset import (
    is_publishable_provenance,
    recommended_text_training_row,
)
from validate_release_index import validate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'release/v0.1.1-manifest.json'
DEFAULT_DATASET = ROOT / 'data/huggingface/garhwali-language-lab'
DEFAULT_OUTPUT = ROOT / 'release/v0.1.1/final-audit.json'
REQUIRED_CONFIGS = {
    'text/train', 'text/validation', 'text/test',
    'asr/train', 'asr/validation', 'asr/test',
    'sravaani_drafts/train', 'lexicon/train',
    'instructions/train', 'instructions/validation', 'instructions/test',
    'catalog/train',
    'geography/train', 'historical_terms/train', 'literary_people/train',
    'literary_works/train', 'popular_songs/train', 'university_research/train',
}
KNOWLEDGE_GROUPS = {
    'geography', 'historical_terms', 'literary_people',
    'literary_works', 'popular_songs', 'university_research',
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def overlap_error(label, split_values):
    errors = []
    names = ('train', 'validation', 'test')
    for position, left in enumerate(names):
        for right in names[position + 1:]:
            if split_values.get(left, set()) & split_values.get(right, set()):
                errors.append(f'{label} overlap across {left} and {right}')
    return errors


def normalized_text_key(text):
    normalized = unicodedata.normalize('NFKC', str(text or '')).casefold()
    return ''.join(char for char in normalized if char.isalnum())


def public_rights_basis(row):
    if 'public_rights_basis' in row:
        return row.get('public_rights_basis') or []
    return [
        item for item in row.get('provenance') or []
        if is_publishable_provenance(item)
    ]


def benchmark_artifact(root, artifact, label, errors):
    relative = Path(str(artifact.get('path') or ''))
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        errors.append(f'{label} artifact path escapes project root')
        return []
    if not relative.parts or not path.is_file():
        errors.append(f'{label} artifact is missing: {relative}')
        return []
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if artifact.get('sha256') != digest:
        errors.append(f'{label} artifact hash does not match benchmark manifest')
    try:
        rows = list(read_jsonl(path))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f'{label} artifact is not valid JSONL: {exc}')
        return []
    if len(rows) != artifact.get('records'):
        errors.append(f'{label} artifact row count does not match benchmark manifest')
    return rows


def audit_benchmark(project_root):
    """Recompute benchmark artifact hashes, counts, and internal split leakage."""
    root = Path(project_root).resolve()
    manifest_path = root / 'data/processed/evaluation/garhwali_bench/manifest.json'
    errors = []
    artifacts_checked = 0
    if not manifest_path.is_file():
        return {
            'status': 'failed', 'errors': ['GarhwaliBench manifest is missing'],
            'artifact_failures': 1, 'artifacts_checked': 0,
            'leakage': {},
        }
    try:
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {
            'status': 'failed', 'errors': [f'GarhwaliBench manifest is invalid: {exc}'],
            'artifact_failures': 1, 'artifacts_checked': 0,
            'leakage': {},
        }

    internal = manifest.get('internal_evaluation') or {}
    records = manifest.get('records') or {}
    internal_text_manifest = dict(internal.get('text') or {})
    internal_asr_manifest = dict(internal.get('asr') or {})
    internal_text_manifest.setdefault('records', records.get('text_evaluation'))
    internal_asr_manifest.setdefault('records', records.get('asr_evaluation'))
    text_rows = benchmark_artifact(
        root, internal_text_manifest, 'GarhwaliBench internal text', errors
    )
    asr_rows = benchmark_artifact(
        root, internal_asr_manifest, 'GarhwaliBench internal ASR', errors
    )
    artifacts_checked += 2
    if len(text_rows) != records.get('text_evaluation'):
        errors.append('GarhwaliBench internal text count disagrees with top-level manifest')
    if len(asr_rows) != records.get('asr_evaluation'):
        errors.append('GarhwaliBench internal ASR count disagrees with top-level manifest')

    tasks = manifest.get('tasks') or {}
    for name in ('crosssum', 'flores', 'xorqa'):
        artifact = tasks.get(name)
        if not isinstance(artifact, dict):
            errors.append(f'GarhwaliBench task {name} is missing from manifest')
            continue
        benchmark_artifact(root, artifact, f'GarhwaliBench {name}', errors)
        artifacts_checked += 1
        if artifact.get('usage') != 'evaluation_only':
            errors.append(f'GarhwaliBench task {name} is not marked evaluation-only')
        if artifact.get('schema_errors') != 0:
            errors.append(f'GarhwaliBench task {name} declares schema errors')

    text_train_path = root / 'data/processed/model_ready/splits/text/train.jsonl'
    asr_train_path = root / 'data/processed/model_ready/splits/asr/train.jsonl'
    asr_validation_path = root / 'data/processed/model_ready/splits/asr/validation.jsonl'
    try:
        text_train = list(read_jsonl(text_train_path))
        asr_train = list(read_jsonl(asr_train_path))
        asr_validation = list(read_jsonl(asr_validation_path))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f'cannot load training splits for benchmark leakage audit: {exc}')
        text_train, asr_train, asr_validation = [], [], []

    trained_text = {
        normalized_text_key(row.get('text')) for row in text_train
        if normalized_text_key(row.get('text'))
    }
    heldout_text = {
        normalized_text_key(row.get('text')) for row in text_rows
        if normalized_text_key(row.get('text'))
    }
    text_overlap = len(trained_text & heldout_text)
    train_audio = {
        row.get('audio_sha256') for row in asr_train + asr_validation
        if row.get('audio_sha256')
    }
    train_speakers = {
        row.get('speaker_id') for row in asr_train + asr_validation
        if row.get('speaker_id') not in (None, '', 'NA')
    }
    heldout_audio = {row.get('audio_sha256') for row in asr_rows if row.get('audio_sha256')}
    heldout_speakers = {
        row.get('speaker_id') for row in asr_rows
        if row.get('speaker_id') not in (None, '', 'NA')
    }
    audio_overlap = len(train_audio & heldout_audio)
    speaker_overlap = len(train_speakers & heldout_speakers)
    if text_overlap:
        errors.append(f'GarhwaliBench internal text overlaps text train by {text_overlap} normalized values')
    if audio_overlap:
        errors.append(f'GarhwaliBench ASR overlaps train/validation by {audio_overlap} audio hashes')
    if speaker_overlap:
        errors.append(f'GarhwaliBench ASR overlaps train/validation by {speaker_overlap} speakers')

    computed_leakage = {
        'internal_text_exact_train_text': text_overlap,
        'asr_audio_train_or_validation_overlap': audio_overlap,
        'asr_speaker_train_or_validation_overlap': speaker_overlap,
    }
    declared = manifest.get('leakage') or {}
    for key, actual in (
        ('internal_text_exact_train_text', text_overlap),
        ('asr_speaker_overlap', speaker_overlap),
    ):
        if key in declared and declared[key] != actual:
            errors.append(f'GarhwaliBench declared leakage {key} disagrees with recomputed value')
    return {
        'status': 'passed' if not errors else 'failed',
        'errors': errors,
        'artifacts_checked': artifacts_checked,
        'artifact_failures': sum('artifact' in error or 'manifest' in error for error in errors),
        'record_counts': {
            'internal_text': len(text_rows), 'internal_asr': len(asr_rows),
            'text_train': len(text_train), 'asr_train': len(asr_train),
            'asr_validation': len(asr_validation),
        },
        'leakage': computed_leakage,
    }


def audit(index, dataset_root, benchmark_root=None):
    dataset_root = Path(dataset_root)
    errors = list(validate(index))
    warnings = []
    manifest_path = dataset_root / 'manifest.json'
    if not manifest_path.exists():
        return {'status': 'failed', 'errors': errors + ['Hugging Face manifest is missing'], 'warnings': warnings}

    if benchmark_root is None and dataset_root.resolve() == DEFAULT_DATASET.resolve():
        benchmark_root = ROOT
    benchmark_report = None
    if benchmark_root is not None:
        benchmark_report = audit_benchmark(benchmark_root)
        errors.extend(
            f'benchmark audit: {error}' for error in benchmark_report['errors']
        )

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('release_id') != index.get('release_id'):
        errors.append('Hugging Face release ID does not match release index')
    available_configs = set(manifest.get('configs', {}))
    required_configs = REQUIRED_CONFIGS
    if manifest.get('profile') == 'public':
        required_configs = REQUIRED_CONFIGS - {
            f'{family}/train' for family in KNOWLEDGE_GROUPS
        }
    missing_configs = sorted(required_configs - available_configs)
    if missing_configs:
        errors.append(f'missing configs: {", ".join(missing_configs)}')
    unexpected_configs = sorted(available_configs - REQUIRED_CONFIGS)
    if unexpected_configs:
        errors.append(f'unexpected configs: {", ".join(unexpected_configs)}')

    actual_counts = {}
    text_ids = {}
    text_normalized = {}
    text_components = {}
    instruction_prompts = {}
    asr_hashes = {}
    asr_speakers = {}
    provenance_missing = 0
    rights_failures = 0
    language_scope_failures = 0
    text_admission_metadata_missing = 0
    invalid_text_training_recommendations = 0
    instruction_reference_metadata_missing = 0
    instruction_attribution_missing = 0
    content_hash_failures = 0
    text_id_hash_failures = 0
    asr_metadata_missing = 0
    expected_audio = set()
    draft_hashes = set()
    draft_rows = 0
    empty_drafts = 0
    draft_quality_missing = 0
    supervised_drafts = 0
    source_conflict_drafts = 0
    invalid_source_conflict_drafts = 0
    recovery_adjudications = 0
    invalid_recovery_adjudications = 0
    third_checkpoint_records = 0
    invalid_third_checkpoint_records = 0
    audio_grounded_review_records = 0
    invalid_audio_grounded_review_records = 0
    catalog_ids = set()
    catalog_redacted = 0
    catalog_missing_evidence = 0
    knowledge_records = 0
    knowledge_provenance_missing = 0
    knowledge_source_untraceable = 0
    knowledge_quality_missing = 0
    knowledge_rights_failures = 0
    knowledge_rights_unassessed = 0
    shard_hash_failures = 0

    for key, config in sorted(manifest.get('configs', {}).items()):
        group, split = key.split('/', 1)
        rows = []
        declared_hashes = config.get('file_sha256') or {}
        filenames = config.get('files', [])
        if set(declared_hashes) != set(filenames):
            errors.append(f'{key} shard hash manifest does not match its file list')
            shard_hash_failures += 1
        for filename in filenames:
            path = dataset_root / 'data' / group / filename
            if not path.exists():
                errors.append(f'{key} shard is missing: {filename}')
                continue
            if declared_hashes.get(filename) != hashlib.sha256(path.read_bytes()).hexdigest():
                errors.append(f'{key} shard hash mismatch: {filename}')
                shard_hash_failures += 1
            rows.extend(read_jsonl(path))
        actual_counts[key] = len(rows)
        if len(rows) != config.get('records'):
            errors.append(f'{key} has {len(rows)} rows, manifest declares {config.get("records")}')
        if len(config.get('files', [])) != config.get('shards'):
            errors.append(f'{key} shard count does not match its manifest')

        if group == 'text':
            id_hash_failures = sum(
                not row.get('text')
                or row.get('id') != hashlib.sha256(
                    str(row.get('text') or '').encode('utf-8')
                ).hexdigest()
                for row in rows
            )
            text_id_hash_failures += id_hash_failures
            text_ids[split] = {row.get('id') for row in rows}
            text_normalized[split] = {
                normalized_text_key(row.get('text')) for row in rows
                if normalized_text_key(row.get('text'))
            }
            text_components[split] = {
                row.get('duplicate_component_id') for row in rows
                if row.get('duplicate_component_id')
            }
            missing = sum(not row.get('provenance') for row in rows)
            rights = sum(
                not public_rights_basis(row)
                or not all(
                    is_publishable_provenance(item)
                    for item in public_rights_basis(row)
                )
                for row in rows
            )
            language_scope = sum(
                row.get('language') != 'gbm' or any(
                    item.get('iso_639_3') != 'gbm'
                    for item in public_rights_basis(row)
                )
                for row in rows
            )
            admission_missing = sum(
                'language_buckets' not in row
                or 'quality_tiers' not in row
                or 'recommended_for_training' not in row
                for row in rows
            )
            invalid_recommendations = sum(
                row.get('recommended_for_training')
                is not recommended_text_training_row(row)
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows without provenance')
            if rights:
                errors.append(f'{key} has {rights} rows without compatible public rights')
            if language_scope:
                errors.append(f'{key} has {language_scope} rows outside explicit Garhwali scope')
            if admission_missing:
                errors.append(
                    f'{key} has {admission_missing} rows without language/quality '
                    'admission metadata'
                )
            if invalid_recommendations:
                errors.append(
                    f'{key} has {invalid_recommendations} training recommendation flags '
                    'that disagree with Garhwali, quality, and public-rights evidence'
                )
            if id_hash_failures:
                errors.append(
                    f'{key} has {id_hash_failures} text IDs that do not match SHA-256 of exported text'
                )
            provenance_missing += missing
            rights_failures += rights
            language_scope_failures += language_scope
            text_admission_metadata_missing += admission_missing
            invalid_text_training_recommendations += invalid_recommendations
        elif group == 'asr':
            expected_audio.update(row.get('audio') for row in rows if row.get('audio'))
            asr_hashes[split] = {row.get('audio_sha256') for row in rows}
            asr_speakers[split] = {
                row.get('speaker_id') for row in rows
                if row.get('speaker_id') not in (None, '', 'NA')
            }
            missing = sum(
                not row.get('source') or not row.get('license') or not row.get('transcript')
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows missing transcript/source/license metadata')
            asr_metadata_missing += missing
        elif group in ('lexicon', 'instructions'):
            missing = sum(not row.get('provenance') for row in rows)
            rights = sum(
                not public_rights_basis(row)
                or not all(
                    is_publishable_provenance(item)
                    for item in public_rights_basis(row)
                )
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows without provenance')
            if rights:
                errors.append(f'{key} has {rights} rows without compatible public rights')
            provenance_missing += missing
            rights_failures += rights
            if group == 'instructions':
                instruction_prompts[split] = {
                    ' '.join(str(row.get('instruction') or '').casefold().split())
                    for row in rows
                }
                reference_missing = sum(
                    not row.get('acceptable_responses') for row in rows
                )
                if reference_missing:
                    errors.append(
                        f'{key} has {reference_missing} rows without acceptable '
                        'response metadata'
                    )
                instruction_reference_metadata_missing += reference_missing
                attribution_missing = sum(
                    any(
                        not item.get('attribution')
                        or not (item.get('license_id') or item.get('license_url'))
                        for item in public_rights_basis(row)
                    )
                    for row in rows
                )
                if attribution_missing:
                    errors.append(
                        f'{key} has {attribution_missing} rows with incomplete '
                        'public attribution or license metadata'
                    )
                instruction_attribution_missing += attribution_missing
            else:
                for row in rows:
                    expected = hashlib.sha256(
                        str(row.get('form') or '').encode('utf-8')
                    ).hexdigest()
                    if row.get('form_sha256') != expected:
                        content_hash_failures += 1
        elif group == 'sravaani_drafts':
            expected_audio.update(row.get('audio') for row in rows if row.get('audio'))
            draft_rows += len(rows)
            for row in rows:
                digest = row.get('audio_sha256')
                if digest in draft_hashes:
                    errors.append(f'sravaani_drafts contains duplicate audio hash {digest}')
                draft_hashes.add(digest)
                empty_drafts += not bool(row.get('transcript'))
                draft_quality_missing += not bool(row.get('machine_transcript_quality'))
                supervised_drafts += row.get('training_eligible') is True
                if row.get('language_scope_status') == 'source_label_conflict':
                    source_conflict_drafts += 1
                    invalid_source_conflict_drafts += bool(
                        row.get('training_eligible')
                        or row.get('experimental_training_eligible')
                        or not row.get('active_for_source_error_analysis')
                    )
                adjudication = row.get('recovery_adjudication')
                if adjudication:
                    recovery_adjudications += 1
                    invalid_recovery_adjudications += bool(
                        adjudication.get('automatic_correction')
                        or adjudication.get('human_reference_available')
                        or adjudication.get('supervised_training_eligible')
                        or adjudication.get('recommended_for_machine_label_training')
                        or not adjudication.get('original_transcript_preserved')
                    )
                third_checkpoint = row.get('recovery_third_checkpoint')
                if third_checkpoint:
                    third_checkpoint_records += 1
                    invalid_third_checkpoint_records += bool(
                        third_checkpoint.get('confidence_is_calibrated')
                        or third_checkpoint.get('human_reference_available')
                    )
                audio_review = row.get('audio_grounded_review')
                if audio_review:
                    audio_grounded_review_records += 1
                    invalid_audio_grounded_review_records += bool(
                        not audio_review.get('machine_audio_review_complete')
                        or not audio_review.get('human_listening_review_required')
                        or audio_review.get('automatic_correction')
                        or audio_review.get('human_reference_available')
                        or audio_review.get('supervised_training_eligible')
                        or audio_review.get('recommended_for_machine_label_training')
                        or not audio_review.get('original_transcript_preserved')
                    )
        elif group == 'catalog':
            for row in rows:
                identity = row.get('id')
                if not identity or identity in catalog_ids:
                    errors.append('catalog contains a missing or duplicate stable ID')
                catalog_ids.add(identity)
                if identity != row.get('text_sha256'):
                    content_hash_failures += 1
                if row.get('text') is None:
                    catalog_redacted += 1
                    if not row.get('redaction_reason') or not row.get('sources'):
                        catalog_missing_evidence += 1
                else:
                    expected = hashlib.sha256(row['text'].encode('utf-8')).hexdigest()
                    if row.get('release_text_sha256') != expected:
                        content_hash_failures += 1
        elif group in KNOWLEDGE_GROUPS:
            ids = [row.get('id') for row in rows]
            if not all(ids) or len(ids) != len(set(ids)):
                errors.append(f'{group} contains a missing or duplicate stable ID')
            if any(row.get('knowledge_family') != group for row in rows):
                errors.append(f'{group} contains a mismatched knowledge family')
            provenance_missing = sum(
                not row.get('provenance')
                or any(
                    not (item.get('source_id') or item.get('source_url'))
                    for item in row.get('provenance') or []
                )
                for row in rows
            )
            source_untraceable = sum(
                not row.get('provenance')
                or any(
                    not (
                        item.get('source_url')
                        or item.get('source_snapshot_sha256')
                        or item.get('source_capture_path')
                    )
                    for item in row.get('provenance') or []
                )
                for row in rows
            )
            quality_missing = sum(
                not isinstance(row.get('quality_metadata'), dict)
                or not row['quality_metadata'].get('review_status')
                for row in rows
            )
            rights_unassessed = sum(
                not row.get('rights_status')
                or row.get('rights_status') == 'not_assessed'
                for row in rows
            )
            knowledge_rights_missing = sum(
                not row.get('public_rights_basis')
                or not all(
                    is_publishable_provenance(item)
                    and item.get('attribution')
                    and (item.get('source_url') or item.get('source_snapshot_sha256'))
                    for item in row.get('public_rights_basis') or []
                )
                for row in rows
            )
            if provenance_missing:
                errors.append(
                    f'{group}/{split} has {provenance_missing} rows without '
                    'standardized source provenance'
                )
            if source_untraceable:
                errors.append(
                    f'{group}/{split} has {source_untraceable} rows with '
                    'source IDs but no source URL or captured-source locator'
                )
            if quality_missing:
                errors.append(
                    f'{group}/{split} has {quality_missing} rows without quality metadata'
                )
            if rights_unassessed:
                errors.append(
                    f'{group}/{split} has {rights_unassessed} rows without an '
                    'assessed rights status'
                )
            if manifest.get('profile') == 'public' and knowledge_rights_missing:
                errors.append(
                    f'{group}/{split} has {knowledge_rights_missing} rows without compatible public rights'
                )
            knowledge_provenance_missing += provenance_missing
            knowledge_source_untraceable += source_untraceable
            knowledge_quality_missing += quality_missing
            knowledge_rights_failures += knowledge_rights_missing
            knowledge_rights_unassessed += rights_unassessed
            knowledge_records += len(rows)

    errors.extend(overlap_error('text IDs', text_ids))
    errors.extend(overlap_error('normalized text', text_normalized))
    errors.extend(overlap_error('text duplicate components', text_components))
    errors.extend(overlap_error('ASR audio hashes', asr_hashes))
    errors.extend(overlap_error('ASR speakers', asr_speakers))
    errors.extend(overlap_error('instruction prompts', instruction_prompts))
    if draft_quality_missing:
        errors.append(f'{draft_quality_missing} SraVaani drafts lack quality metadata')
    if supervised_drafts:
        errors.append(f'{supervised_drafts} machine drafts are marked supervised-training eligible')
    if invalid_source_conflict_drafts:
        errors.append(
            f'{invalid_source_conflict_drafts} source-label conflict drafts are '
            'marked as Garhwali training data'
        )
    if invalid_recovery_adjudications:
        errors.append(
            f'{invalid_recovery_adjudications} recovery adjudications make an '
            'unsupported training or accuracy claim'
        )
    if invalid_third_checkpoint_records:
        errors.append(
            f'{invalid_third_checkpoint_records} third-checkpoint records make '
            'an unsupported confidence or reference claim'
        )
    if invalid_audio_grounded_review_records:
        errors.append(
            f'{invalid_audio_grounded_review_records} audio-grounded reviews make '
            'an unsupported completion, training, or accuracy claim'
        )
    expected_catalog_records = index.get('text', {}).get(
        'unique_parent_documents', index.get('text', {}).get('total')
    )
    if len(catalog_ids) != expected_catalog_records:
        errors.append('catalog does not account for every exact-unique text record')
    if catalog_missing_evidence:
        errors.append(f'{catalog_missing_evidence} redacted catalog rows lack public evidence')
    if content_hash_failures:
        errors.append(f'{content_hash_failures} exported values have invalid release hashes')

    asr_total = sum(actual_counts.get(f'asr/{split}', 0) for split in ('train', 'validation', 'test'))
    if asr_total != index.get('speech', {}).get('strict_comparison_rows'):
        errors.append('ASR export total does not match release strict comparison rows')
    comparison = index.get('speech_baseline_comparison', {})
    checks = {
        'draft_queue_records': manifest.get('draft_queue_records'),
        'draft_records': manifest.get('draft_records'),
        'draft_unique_audio': manifest.get('draft_unique_audio'),
        'draft_inherited_duplicate_rows': manifest.get('draft_inherited_duplicate_rows'),
    }
    expected = {
        'draft_records': comparison.get('sravaani_draft_rows'),
        'draft_unique_audio': comparison.get('sravaani_draft_unique_audio'),
        'draft_inherited_duplicate_rows': comparison.get('sravaani_draft_inherited_duplicate_rows'),
    }
    for name, value in expected.items():
        if checks[name] != value:
            errors.append(f'{name} does not match release index')
    if draft_rows != manifest.get('draft_unique_audio'):
        errors.append('exported draft rows do not match unique-audio count')
    if source_conflict_drafts != manifest.get('draft_source_label_conflicts'):
        errors.append('source-label conflict count does not match manifest')
    if recovery_adjudications != manifest.get('draft_three_checkpoint_review_records'):
        errors.append('recovery adjudication count does not match manifest')
    if third_checkpoint_records != manifest.get('draft_third_checkpoint_records'):
        errors.append('third-checkpoint recovery count does not match manifest')
    if audio_grounded_review_records != manifest.get('draft_audio_grounded_review_records'):
        errors.append('audio-grounded review count does not match manifest')
    if not manifest.get('drafts_complete'):
        errors.append('SraVaani draft coverage is incomplete')
    audio_files = set()
    if (dataset_root / 'audio').exists():
        audio_files = {
            path.relative_to(dataset_root).as_posix()
            for path in (dataset_root / 'audio').rglob('*.wav')
        }
    missing_audio = expected_audio - audio_files
    unexpected_audio = audio_files - expected_audio
    if manifest.get('include_audio'):
        if missing_audio:
            errors.append(f'{len(missing_audio)} referenced audio files are missing')
        if unexpected_audio:
            errors.append(f'{len(unexpected_audio)} unexpected audio files are present')
        if manifest.get('linked_audio_files') != len(expected_audio):
            errors.append('linked audio count does not match referenced unique audio')
    else:
        warnings.append('audio_not_included')
    if manifest.get('draft_inherited_duplicate_rows'):
        warnings.append('inherited_source_audio_duplicates_collapsed')
    if empty_drafts:
        warnings.append('empty_machine_drafts_retained_with_quality_flags')

    return {
        'audit_id': 'garhwali-final-release-audit-v0.1',
        'generated': date.today().isoformat(),
        'release_id': index.get('release_id'),
        'status': 'passed' if not errors else 'failed',
        'errors': errors,
        'warnings': warnings,
        'configs': actual_counts,
        'exported_rows': sum(actual_counts.values()),
        'audio': {
            'included': bool(manifest.get('include_audio')),
            'referenced_unique_files': len(expected_audio),
            'present_files': len(audio_files),
            'missing_files': len(missing_audio),
            'unexpected_files': len(unexpected_audio),
        },
        'provenance': {
            'missing_rows': provenance_missing,
            'public_rights_failures': rights_failures,
            'text_language_scope_failures': language_scope_failures,
            'text_admission_metadata_missing': text_admission_metadata_missing,
            'invalid_text_training_recommendations': invalid_text_training_recommendations,
            'instruction_reference_metadata_missing': instruction_reference_metadata_missing,
            'instruction_attribution_or_license_missing': instruction_attribution_missing,
            'asr_missing_transcript_source_or_license': asr_metadata_missing,
            'knowledge_missing_standardized_rows': knowledge_provenance_missing,
            'knowledge_source_untraceable_rows': knowledge_source_untraceable,
            'knowledge_quality_metadata_missing': knowledge_quality_missing,
            'knowledge_public_rights_failures': knowledge_rights_failures,
            'knowledge_rights_unassessed': knowledge_rights_unassessed,
        },
        'leakage': {
            'text_id_cross_split': 0 if not overlap_error('text', text_ids) else 1,
            'normalized_text_cross_split': (
                0 if not overlap_error('normalized text', text_normalized) else 1
            ),
            'semantic_component_cross_split': (
                0 if not overlap_error('component', text_components) else 1
            ),
            'asr_audio_cross_split': 0 if not overlap_error('asr', asr_hashes) else 1,
            'asr_speaker_cross_split': 0 if not overlap_error('speaker', asr_speakers) else 1,
            'instruction_prompt_cross_split': (
                0 if not overlap_error('instruction', instruction_prompts) else 1
            ),
        },
        'drafts': {
            **checks,
            'exported_unique_audio': len(draft_hashes),
            'empty_transcripts': empty_drafts,
            'quality_metadata_missing': draft_quality_missing,
            'supervised_training_eligible': supervised_drafts,
            'source_label_conflicts': source_conflict_drafts,
            'invalid_source_label_conflicts': invalid_source_conflict_drafts,
            'recovery_adjudications': recovery_adjudications,
            'invalid_recovery_adjudications': invalid_recovery_adjudications,
            'third_checkpoint_records': third_checkpoint_records,
            'invalid_third_checkpoint_records': invalid_third_checkpoint_records,
            'audio_grounded_review_records': audio_grounded_review_records,
            'invalid_audio_grounded_review_records': invalid_audio_grounded_review_records,
            'complete': bool(manifest.get('drafts_complete')),
        },
        'catalog': {
            'records': len(catalog_ids),
            'redacted_text_records': catalog_redacted,
            'missing_evidence': catalog_missing_evidence,
            'invalid_release_hashes': content_hash_failures,
        },
        'text_id_hash_failures': text_id_hash_failures,
        'shard_hash_failures': shard_hash_failures,
        'structured_knowledge': {
            'records': knowledge_records,
            'configs': sorted(
                KNOWLEDGE_GROUPS & {key.split('/', 1)[0] for key in actual_counts}
            ),
            'provenance_missing': knowledge_provenance_missing,
            'source_untraceable': knowledge_source_untraceable,
            'quality_metadata_missing': knowledge_quality_missing,
            'public_rights_failures': knowledge_rights_failures,
            'rights_unassessed': knowledge_rights_unassessed,
        },
        'benchmark': benchmark_report,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding='utf-8'))
    report = audit(index, args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
