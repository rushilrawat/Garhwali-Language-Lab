#!/usr/bin/env python3
"""Build a local-only, draft GarhwaliBench v0.2 adapter export."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

from audit_benchmark_overlap_candidates import normalize_text as normalize_overlap_text
from audit_xorqa_source_page_families import source_page_hashes


SCHEMA_VERSION = 'garhwali-bench-record-v0.2-draft'
BENCHMARK_ID = 'garhwali-bench-v0.2-draft'
OUTPUT_DIR = Path('data/processed/evaluation/garhwali_bench/v0.2-draft')
EXTERNAL_TASKS = {
    'external/flores': 'translation',
    'external/crosssum': 'summarization',
    'external/xorqa': 'question_answering',
}
METRICS = {
    'translation': {
        'status': 'draft_not_release_frozen',
        'scores_computed': False,
        'metrics': [
            {
                'id': 'garhwali-custom-add1-bleu-v1',
                'signature': (
                    'NFC+casefold+whitespace-collapse; corpus word n-grams orders 1-4; '
                    'add-one precision smoothing per order; corpus brevity penalty; '
                    'scripts/run_translation_baseline.py:corpus_bleu'
                ),
                'implementation_status': 'existing_nonstandard_custom_scorer',
            },
            {
                'id': 'garhwali-custom-chrf2-v1',
                'signature': (
                    'NFC+casefold+whitespace-collapse; character n-grams orders 1-6; '
                    'beta=2; per-order corpus precision/recall F-beta macro-average; '
                    'scripts/run_translation_baseline.py:corpus_chrf'
                ),
                'implementation_status': 'existing_custom_scorer_not_sacrebleu',
            },
        ],
        'limitations': 'Direction, references, normalization, and implementation must be frozen per run; do not call custom BLEU SacreBLEU.',
    },
    'summarization': {
        'status': 'draft_not_release_frozen',
        'scores_computed': False,
        'metrics': [
            {
                'id': 'garhwali-custom-chrf2-v1',
                'signature': 'character n-gram orders 1-6; beta=2; exact implementation and normalizer hash required',
                'implementation_status': 'reuse_candidate_not_yet_bound_to_crosssum',
            },
            {
                'id': 'garhwali-rouge-l-f1-v1',
                'signature': (
                    'NFC+casefold; Unicode punctuation and symbols become spaces; '
                    'collapsed whitespace tokens; token LCS F1; macro mean of '
                    'per-record maximum across non-empty references; empty hypotheses '
                    'score zero and remain in the denominator; '
                    'scripts/benchmark_metrics.py:score_rouge_l'
                ),
                'implementation_status': 'implemented_dependency_free; runner reports missing-reference exclusions',
            },
        ],
        'limitations': 'No CrossSum model scores are computed here; source-family uncertainty is not aggregated by the scorer.',
    },
    'question_answering': {
        'status': 'draft_not_release_frozen',
        'scores_computed': False,
        'metrics': [
            {
                'id': 'garhwali-qa-em-token-f1-v1',
                'signature': (
                    'NFC+casefold; Unicode punctuation and symbols become spaces; '
                    'collapsed whitespace tokens; exact match and multiset token F1; '
                    'maximum per-record score across non-empty references; macro mean; '
                    'empty hypotheses score zero and remain in the denominator; '
                    'records without a non-empty reference are rejected; '
                    'scripts/benchmark_metrics.py:score_qa_answers'
                ),
                'implementation_status': 'implemented_dependency_free; runner reports missing-reference exclusions',
            },
        ],
        'limitations': 'No XORQA model scores are computed here. Explicit no-answer scoring is unsupported; rows without a target-language reference are excluded and reported. The current usage overlay marks 138 records with exact context, source-page, question, or oracle-question overlap as open-diagnostic-only for independent source-generalization claims.',
    },
    'language_modeling': {
        'status': 'draft_not_release_frozen',
        'scores_computed': False,
        'metrics': [
            {
                'id': 'character-ngram-cross-entropy-v1-draft',
                'signature': 'NFC+whitespace-collapse; character n-gram order and add-one smoothing recorded per run; include boundary symbols and report evaluated character denominator',
                'implementation_status': 'existing_experimental_baseline; order is run-configured',
            },
        ],
        'limitations': 'Perplexity is tokenizer/model specific and is not directly comparable across different tokenizers.',
    },
    'asr': {
        'status': 'draft_not_release_frozen',
        'scores_computed': False,
        'metrics': [
            {
                'id': 'garhwali-asr-corpus-wer-v1',
                'signature': (
                    'NFC+casefold+punctuation/symbol-to-space+whitespace-collapse; '
                    'whitespace-word edit distance; micro aggregate from summed '
                    'errors/reference words; empty hypotheses count as deletions; '
                    'empty references are excluded and listed; '
                    'scripts/asr_metrics.py:score_corpus'
                ),
                'implementation_status': 'implemented_tested_integrated_in_shared_benchmark_scorer',
            },
            {
                'id': 'garhwali-asr-corpus-cer-v1',
                'signature': (
                    'same normalization; code-point edit distance over normalized '
                    'characters with spaces removed; micro aggregate from summed '
                    'errors/reference characters; empty hypotheses count as deletions; '
                    'empty references are excluded and listed; '
                    'scripts/asr_metrics.py:score_corpus'
                ),
                'implementation_status': 'implemented_tested_integrated_in_shared_benchmark_scorer',
            },
        ],
        'limitations': 'The shared scorer emits corpus and per-record WER/CER with explicit empty-reference policy; existing local ASR comparisons remain historical and are not native-validated or independent.',
    },
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode('utf-8'))


def _script_name(char: str) -> str:
    name = unicodedata.name(char, '')
    for prefix, script in (
        ('DEVANAGARI', 'Deva'), ('LATIN', 'Latn'), ('ARABIC', 'Arab'),
        ('BENGALI', 'Beng'), ('GURMUKHI', 'Guru'), ('TAMIL', 'Taml'),
        ('TELUGU', 'Telu'), ('GUJARATI', 'Gujr'), ('ORIYA', 'Orya'),
    ):
        if name.startswith(prefix):
            return script
    return 'Other'


def observed_script_profile(text: str | None) -> list[str]:
    if not isinstance(text, str):
        return []
    return sorted({
        _script_name(char)
        for char in text
        if unicodedata.category(char).startswith('L')
    })


def _score_normalize(text: str, normalizer_id: str) -> str:
    if normalizer_id == 'asr-nfc-casefold-punctuation-symbol-space-v1':
        value = unicodedata.normalize('NFC', text).casefold()
        value = ''.join(
            ' ' if unicodedata.category(char).startswith(('P', 'S')) else char
            for char in value
        )
        return re.sub(r'\s+', ' ', value).strip()
    return unicodedata.normalize('NFC', text).strip()


def _is_external(view_name: str) -> bool:
    return view_name in EXTERNAL_TASKS


def _task_for_view(view_name: str) -> str:
    if view_name in EXTERNAL_TASKS:
        return EXTERNAL_TASKS[view_name]
    if view_name == 'internal/text' or view_name.startswith('text_recommended/'):
        return 'language_modeling'
    if view_name == 'internal/asr':
        return 'asr'
    raise ValueError(f'unsupported benchmark view: {view_name}')


def _text_fields(view_name: str, row: dict) -> dict:
    if _is_external(view_name):
        raw = row.get('text_original')
        source = row.get('text_original')
        scoring = row.get('text_normalized')
        normalizer_id = 'unicode-nfc-trim-v1'
        raw_status = 'source_text_original_field'
        raw_available = isinstance(raw, str)
    elif view_name == 'internal/asr':
        raw = row.get('transcript')
        source = row.get('asr_target')
        normalizer_id = 'asr-nfc-casefold-punctuation-symbol-space-v1'
        scoring = _score_normalize(source, normalizer_id) if isinstance(source, str) else None
        raw_status = 'upstream_transcript_field' if isinstance(raw, str) and raw else 'not_available'
        raw_available = isinstance(raw, str) and bool(raw)
    else:
        source = row.get('text')
        normalizer_id = 'unicode-nfc-trim-v1'
        scoring = _score_normalize(source, normalizer_id) if isinstance(source, str) else None
        raw = None
        raw_status = 'not_available_in_v01_view'
        raw_available = False

    return {
        'text_raw': raw,
        'text_source': source,
        'text_scoring': scoring,
        'normalizer_id': normalizer_id,
        'raw_text_available': raw_available,
        'raw_text_status': raw_status,
        'text_raw_sha256': sha256_text(raw) if isinstance(raw, str) else None,
        'text_source_sha256': sha256_text(source) if isinstance(source, str) else None,
        'text_scoring_sha256': sha256_text(scoring) if isinstance(scoring, str) else None,
    }


def _base_usage(view_name: str, row: dict) -> dict:
    split = str(row.get('split') or '')
    if view_name.startswith('text_recommended/'):
        label = {
            'train': 'train_candidate' if row.get('recommended_for_training') else 'not_training_eligible',
            'validation': 'dev_select',
            'test': 'open_test_historical',
        }.get(split, 'unknown')
    elif split == 'dev':
        label = 'dev_select'
    elif split == 'test':
        label = 'open_test_historical'
    elif split == 'train':
        label = 'source_split_train_evaluation_only' if _is_external(view_name) else 'train_candidate'
    else:
        label = 'unknown'
    return {
        'usage_label': label,
        'source_usage': row.get('usage'),
        'training_eligibility_as_recorded': row.get(
            'training_eligible', row.get('recommended_for_training', row.get('experimental_training_eligible')),
        ),
        'open_diagnostic_eligible': split in {'dev', 'test'},
        'independent_source_generalization_eligible': None,
        'independent_claim_status': 'not_established_by_adapter',
        'record_retained': True,
    }


def adapt_record(view_name: str, row: dict, overlay: dict | None = None) -> dict:
    """Wrap one source record without dropping or rewriting its legacy payload."""
    task = _task_for_view(view_name)
    text_fields = _text_fields(view_name, row)
    if _is_external(view_name):
        example_id = str(row.get('record_id') or '')
        language = row.get('iso_639_3')
        declared_script = row.get('script')
        split = row.get('split')
        provenance = {
            key: row.get(key)
            for key in ('source_id', 'attribution', 'provenance', 'extractor_version', 'modifications')
        }
        rights = {
            'rights_status': row.get('rights_status'),
            'declared_license_id': row.get('license_id'),
            'declared_license_url': row.get('license_url'),
            'component_rights_status': 'not_assessed_by_v02_export',
            'redistribution_status': 'not_cleared_by_v02_export',
            'public_release_cleared': False,
        }
        quality = {
            'native_reviewed': row.get('native_reviewed'),
            'quality_status': row.get('quality_status'),
            'quality_flags': row.get('quality_flags', []),
        }
        payload = {'source_example': row.get('source_example')}
        source_text = row.get('text_original')
        audio_private = False
    elif view_name == 'internal/text':
        example_id = f"internal_text:{row.get('segment_sha256', '')}"
        language = 'gbm'
        declared_script = None
        split = row.get('split')
        provenance = {'parents': row.get('parents'), 'parent_count': row.get('parent_count')}
        rights = {
            'component_rights': [
                {
                    'source_id': p.get('source_id'),
                    'record_id': p.get('record_id'),
                    'rights_status': p.get('rights_status'),
                    'license_id': p.get('license_id'),
                    'license_url': p.get('license_url'),
                }
                for parent in row.get('parents', [])
                for p in parent.get('provenance', [])
            ],
            'redistribution_status': 'not_cleared_by_v02_export',
            'public_release_cleared': False,
        }
        quality = {
            'review_status': row.get('review_status'),
            'quality_flags': row.get('quality_flags', []),
            'native_reviewed': False,
        }
        payload = {'text': row.get('text'), 'parents': row.get('parents')}
        source_text = row.get('text')
        audio_private = False
    elif view_name == 'internal/asr':
        example_id = f"sravaani_asr:{row.get('audio_sha256', '')}"
        language = row.get('language')
        declared_script = None
        split = row.get('split')
        provenance = {
            'source': row.get('source'), 'config': row.get('config'),
            'revision': row.get('revision'), 'transcription_split': row.get('transcription_split'),
        }
        rights = {
            'license_declaration': row.get('license'),
            'rights_status': row.get('rights_status', 'not_assessed_by_v02_export'),
            'redistribution_status': 'not_cleared_by_v02_export',
            'public_release_cleared': False,
        }
        quality = {
            'review_status': row.get('review_status'),
            'quality_flags': row.get('quality_flags', []),
            'audio_quality': row.get('audio_quality'),
            'language_quality': row.get('language_quality'),
            'dialect_quality': row.get('dialect_quality'),
        }
        payload = {
            'audio_sha256': row.get('audio_sha256'),
            'audio_path': row.get('audio_path'),
            'local_audio_path': row.get('local_audio_path'),
            'duration_seconds': row.get('duration_seconds'),
            'speaker_id': row.get('speaker_id'),
            'transcript': row.get('transcript'),
            'canonical_transcript': row.get('canonical_transcript'),
            'selected_transcript': row.get('selected_transcript'),
            'reference_text': row.get('asr_target'),
        }
        source_text = row.get('asr_target')
        audio_private = True
    else:
        example_id = str(row.get('id') or '')
        language = row.get('language')
        declared_script = row.get('script')
        split = row.get('split')
        provenance = {'provenance': row.get('provenance')}
        rights = {
            'public_rights_basis_as_recorded': row.get('public_rights_basis'),
            'redistribution_status': 'not_cleared_by_v02_export',
            'public_release_cleared': False,
        }
        quality = {'quality_flags': row.get('quality_flags', []), 'quality_tiers': row.get('quality_tiers')}
        payload = {'text': row.get('text'), 'language_buckets': row.get('language_buckets')}
        source_text = row.get('text')
        audio_private = False

    usage = _base_usage(view_name, row)
    overlay = overlay or None
    if overlay:
        usage.update({
            'usage_label': overlay.get('usage_label'),
            'open_diagnostic_eligible': overlay.get('open_diagnostic_eligible'),
            'independent_source_generalization_eligible': overlay.get('independent_source_generalization_eligible'),
            'independent_claim_status': overlay.get('reason_code'),
            'record_retained': overlay.get('record_retained', True),
            'overlay_evidence_types': overlay.get('evidence_types', []),
        })

    source_example = row.get('source_example') if _is_external(view_name) else {}
    context = source_example.get('context') if isinstance(source_example, dict) else None
    normalized_context = normalize_overlap_text(context) if isinstance(context, str) else ''
    context_hash = sha256_text(normalized_context) if normalized_context else None
    context_family_hash = (
        sha256_text(f'source_content_sha256:{context_hash}') if context_hash else None
    )
    page_hashes = source_page_hashes(row) if view_name == 'external/xorqa' else None
    lineage = {
        'exact_text_group_sha256': text_fields['text_scoring_sha256'],
        'source_context_group_sha256': context_family_hash,
        'normalized_source_context_sha256': context_hash,
        'overlay_source_family_sha256': overlay.get('source_family_sha256') if overlay else None,
        'overlay_normalized_context_sha256': overlay.get('normalized_context_sha256') if overlay else None,
        'source_page_family_sha256': page_hashes[1] if page_hashes else None,
        'normalized_source_page_title_sha256': page_hashes[0] if page_hashes else None,
        'overlay_source_page_family_sha256': overlay.get('source_page_family_sha256') if overlay else None,
        'duplicate_component_id': row.get('duplicate_component_id'),
        'segment_sha256': row.get('segment_sha256'),
        'audio_sha256': row.get('audio_sha256'),
        'speaker_id': row.get('speaker_id'),
    }
    if overlay and not usage['record_retained']:
        raise ValueError(f'{example_id}: overlay says record is not retained; adapter cannot drop source rows')
    return {
        'schema_version': SCHEMA_VERSION,
        'benchmark_id': BENCHMARK_ID,
        'example_id': example_id,
        'view': view_name,
        'task': task,
        'split': split,
        'source_split': row.get('original_split', row.get('transcription_split', split)),
        'language': language,
        'declared_script': declared_script,
        'observed_script_profile': observed_script_profile(source_text),
        'text': text_fields,
        'payload': payload,
        'provenance': provenance,
        'rights': rights,
        'quality': quality,
        'usage': usage,
        'lineage': lineage,
        'privacy': {
            'export_scope': 'local_only',
            'contains_local_identifiers': audio_private,
            'contains_local_audio_locator': audio_private,
            'public_upload_allowed': False,
        },
        'legacy_record': row,
    }


def metric_contracts() -> dict:
    return json.loads(json.dumps(METRICS))


def _jsonl_bytes(rows: list[dict]) -> bytes:
    return ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in rows
    ).encode('utf-8')


def validate_usage_overlay(xorqa_rows: list[dict], overlay: dict) -> list[str]:
    """Check every overlay label against its actual XORQA source row."""
    errors = []
    rows_by_id = {str(row.get('record_id') or ''): row for row in xorqa_rows}
    labels = overlay.get('labels', [])
    if len(labels) != len({str(label.get('record_id') or '') for label in labels}):
        errors.append('usage overlay contains duplicate record IDs')
    for label in labels:
        record_id = str(label.get('record_id') or '')
        row = rows_by_id.get(record_id)
        if row is None:
            errors.append(f'{record_id}: overlay record is absent from XORQA input')
            continue
        if label.get('original_split') != row.get('split'):
            errors.append(f'{record_id}: overlay split differs from XORQA row')
        if label.get('record_retained') is not True:
            errors.append(f'{record_id}: overlay marks source row as not retained')
        evidence = set(label.get('evidence_types') or [])
        if 'exact_source_context' in evidence:
            context = row.get('source_example', {}).get('context')
            normalized = normalize_overlap_text(context)
            context_hash = sha256_text(normalized)
            family_hash = sha256_text(f'source_content_sha256:{context_hash}')
            if label.get('normalized_context_sha256') != context_hash:
                errors.append(f'{record_id}: overlay context hash does not match source row')
            if label.get('source_family_sha256') != family_hash:
                errors.append(f'{record_id}: overlay source-family hash does not match source row')
        if 'exact_normalized_question' in evidence:
            question = normalize_overlap_text(row.get('text_normalized') or row.get('text_original') or '')
            if label.get('normalized_question_sha256') != sha256_text(question):
                errors.append(f'{record_id}: overlay question hash does not match source row')
        if 'exact_nested_oracle_question' in evidence:
            oracle_question = row.get('source_example', {}).get('oracle_question')
            normalized_oracle_question = normalize_overlap_text(oracle_question)
            if label.get('normalized_oracle_question_sha256') != sha256_text(normalized_oracle_question):
                errors.append(f'{record_id}: overlay oracle-question hash does not match source row')
        if 'exact_source_page_title' in evidence:
            page_hashes = source_page_hashes(row)
            if page_hashes is None or label.get('normalized_source_page_title_sha256') != page_hashes[0]:
                errors.append(f'{record_id}: overlay source-page title hash does not match source row')
            elif label.get('source_page_family_sha256') != page_hashes[1]:
                errors.append(f'{record_id}: overlay source-page hash does not match source row')
    counts = overlay.get('counts') or {}
    if counts.get('affected_records') != len(labels):
        errors.append('usage overlay affected-record count does not match label rows')
    return errors


def build_export_from_views(
    views: dict[str, list[dict]],
    usage_labels: dict[str, dict],
    input_hashes: dict[str, str],
    source_manifest_sha256: str,
    usage_overlay_sha256: str,
    output_dir: Path,
) -> dict:
    """Write deterministic JSONL views and a local-only draft manifest."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        'schema_version': 'garhwali-bench-export-v0.2-draft',
        'benchmark_id': BENCHMARK_ID,
        'status': 'draft_local_only_not_release_ready',
        'local_only': True,
        'public_upload_allowed': False,
        'all_source_rows_retained': True,
        'source_release_id': None,
        'source_manifest_sha256': source_manifest_sha256,
        'usage_overlay_sha256': usage_overlay_sha256,
        'input_hashes': dict(sorted(input_hashes.items())),
        'views': {},
        'total_records': 0,
        'metric_contracts': metric_contracts(),
        'migration_gaps': [
            'Some legacy views do not contain original raw text; the adapter records that absence rather than relabeling normalized view text as raw.',
            'Metric signatures are draft definitions, not release-frozen protocols; no scores are computed by this export.',
            'No row has been rights-cleared by this schema adapter; release eligibility remains an independent gate.',
            'Model exposure and semantic/cross-language contamination remain unresolved unless row-level evidence is available.',
        ],
    }
    total = 0
    for view_name, source_rows in sorted(views.items()):
        output_rows = [
            adapt_record(
                view_name,
                row,
                usage_labels.get(str(row.get('record_id') or '')) if view_name == 'external/xorqa' else None,
            )
            for row in source_rows
        ]
        filename = view_name.replace('/', '__') + '.jsonl'
        data = _jsonl_bytes(output_rows)
        (output_dir / filename).write_bytes(data)
        manifest['views'][view_name] = {
            'path': filename,
            'records': len(output_rows),
            'split_counts': dict(sorted(Counter(str(row.get('split') or '') for row in output_rows).items())),
            'input_sha256': input_hashes[view_name],
            'output_sha256': sha256_bytes(data),
            'task': _task_for_view(view_name),
        }
        total += len(output_rows)
    manifest['total_records'] = total
    manifest['source_release_id'] = 'garhwali-bench-v0.1-experimental'
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    (output_dir / 'manifest.json').write_bytes(manifest_bytes)
    return manifest


def validate_export_artifacts(output_dir: Path, manifest: dict | None = None) -> dict:
    """Verify that every written view matches its recorded hash and row count."""
    output_dir = Path(output_dir)
    manifest = manifest or json.loads((output_dir / 'manifest.json').read_text(encoding='utf-8'))
    errors = []
    observed_total = 0
    for view_name, entry in sorted(manifest.get('views', {}).items()):
        path = output_dir / entry.get('path', '')
        if not path.is_file():
            errors.append(f'{view_name}: output file is missing')
            continue
        data = path.read_bytes()
        if sha256_bytes(data) != entry.get('output_sha256'):
            errors.append(f'{view_name}: output SHA-256 differs from manifest')
            continue
        try:
            rows = _read_jsonl(path)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f'{view_name}: output JSONL is invalid: {exc}')
            continue
        if len(rows) != entry.get('records'):
            errors.append(f'{view_name}: output record count differs from manifest')
        for index, row in enumerate(rows):
            if row.get('schema_version') != SCHEMA_VERSION or row.get('view') != view_name:
                errors.append(f'{view_name}[{index}]: schema or view identifier mismatch')
                break
            if not row.get('example_id') or not isinstance(row.get('legacy_record'), dict):
                errors.append(f'{view_name}[{index}]: stable ID or preserved legacy row is missing')
                break
            if row.get('usage', {}).get('record_retained') is not True:
                errors.append(f'{view_name}[{index}]: source row is not marked retained')
                break
        observed_total += len(rows)
    if observed_total != manifest.get('total_records'):
        errors.append('total output row count differs from manifest')
    disk_manifest_path = output_dir / 'manifest.json'
    if disk_manifest_path.is_file():
        try:
            disk_manifest = json.loads(disk_manifest_path.read_text(encoding='utf-8'))
            if manifest != disk_manifest:
                errors.append('in-memory manifest differs from written manifest')
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            errors.append(f'manifest JSON is invalid: {exc}')
    else:
        errors.append('manifest.json is missing')
    return {
        'status': 'pass' if not errors else 'fail',
        'views': len(manifest.get('views', {})),
        'records': observed_total,
        'errors': errors,
    }


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def build_export(project_root: Path, output_dir: Path | None = None) -> dict:
    root = Path(project_root).resolve()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from validate_benchmark_v02 import validate_project

    validation = validate_project(root)
    if validation['status'] != 'pass':
        raise ValueError(f"current v0.1 benchmark contract fails: {validation['errors'][:5]}")
    benchmark_dir = root / 'data/processed/evaluation/garhwali_bench'
    source_manifest_path = benchmark_dir / 'manifest.json'
    source_manifest = json.loads(source_manifest_path.read_text(encoding='utf-8'))
    overlay_path = benchmark_dir / 'benchmark_usage_labels.json'
    overlay_data = json.loads(overlay_path.read_text(encoding='utf-8'))
    xorqa_path = root / source_manifest['tasks']['xorqa']['path']
    xorqa_hash = sha256_bytes(xorqa_path.read_bytes())
    if overlay_data.get('input_hashes', {}).get('xorqa_benchmark_sha256') != xorqa_hash:
        raise ValueError('XORQA usage overlay is stale against the source benchmark')
    overlay_errors = validate_usage_overlay(_read_jsonl(xorqa_path), overlay_data)
    if overlay_errors:
        raise ValueError(f'XORQA usage overlay validation failed: {overlay_errors[:5]}')
    usage_labels = {str(item['record_id']): item for item in overlay_data.get('labels', [])}

    view_paths = {}
    for task, entry in source_manifest['tasks'].items():
        view_paths[f'external/{task}'] = root / entry['path']
    for task, entry in source_manifest['internal_evaluation'].items():
        view_paths[f'internal/{task}'] = root / entry['path']
    for split in ('train', 'validation', 'test'):
        if split == 'train':
            relative = source_manifest['training']['text']['path']
        else:
            relative = f'data/processed/model_ready/splits/text_recommended/{split}.jsonl'
        view_paths[f'text_recommended/{split}'] = root / relative

    views = {}
    input_hashes = {}
    for view_name, path in sorted(view_paths.items()):
        relative = path.relative_to(root).as_posix()
        expected = validation['assets'][view_name]['sha256']
        actual = sha256_bytes(path.read_bytes())
        if actual != expected:
            raise ValueError(f'{view_name} changed after validation')
        views[view_name] = _read_jsonl(path)
        input_hashes[view_name] = actual

    destination = Path(output_dir) if output_dir else root / OUTPUT_DIR
    if not destination.is_absolute():
        destination = root / destination
    manifest = build_export_from_views(
        views=views,
        usage_labels=usage_labels,
        input_hashes=input_hashes,
        source_manifest_sha256=sha256_bytes(source_manifest_path.read_bytes()),
        usage_overlay_sha256=sha256_bytes(overlay_path.read_bytes()),
        output_dir=destination,
    )
    manifest['source_release_id'] = source_manifest.get('release_id')
    manifest['source_validation_status'] = validation['status']
    manifest['source_validation_errors'] = len(validation['errors'])
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')
    (destination / 'manifest.json').write_bytes(manifest_bytes)
    output_validation = validate_export_artifacts(destination, manifest)
    if output_validation['status'] != 'pass':
        raise ValueError(f"generated v0.2 draft export failed self-validation: {output_validation['errors'][:5]}")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output_dir = Path(args.output_dir) if args.output_dir else project_root / OUTPUT_DIR
    if not output_dir.is_absolute():
        output_dir = project_root / output_dir
    result = build_export(project_root, output_dir)
    print(json.dumps({
        'status': result['status'],
        'views': len(result['views']),
        'records': result['total_records'],
        'output_dir': str(output_dir),
        'manifest_sha256': sha256_bytes((output_dir / 'manifest.json').read_bytes()),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
