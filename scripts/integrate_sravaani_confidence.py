#!/usr/bin/env python3
"""Attach calibrated recovery evidence to the complete SraVaani draft layer."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from asr_metrics import normalize


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
CONFIDENCE = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_confidence.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json'


def display_path(path):
    path = Path(path)
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)
SOURCE_CONFLICTS = ROOT / 'data/processed/model_ready/language_quality/vaani_source_conflicts.jsonl'
RECOVERY_FIELDS = (
    'whisper_candidate',
    'whisper_candidate_model',
    'whisper_candidate_flags',
    'whisper_candidate_frequency',
    'structural_preference',
    'cross_model_character_agreement',
    'cross_model_agreement_band',
    'confidence_score',
    'confidence_band',
    'confidence_scope',
    'confidence_is_accuracy_probability',
    'confidence_ceiling',
    'direct_human_reference_available',
    'calibration_domain',
    'calibration_band_used',
    'calibration_in_matching_band_support',
    'calibration_bin_records',
    'calibration_selected_model_cer',
    'selected_candidate_flags',
    'review_priority',
    'automatic_promotion',
)


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def merge_row(base, confidence, source_conflict=None):
    merged = dict(base)
    merged['training_eligible'] = False
    merged['experimental_training_eligible'] = True
    if source_conflict is not None:
        merged['language_scope_status'] = source_conflict['language_scope_status']
        merged['source_conflict_evidence'] = source_conflict['source_conflict_evidence']
        merged['experimental_training_eligible'] = False
        merged['active_for_source_error_analysis'] = True
    if confidence is None:
        merged['recovery_status'] = 'not_targeted_for_redecode'
        merged.pop('recovery_confidence', None)
        return merged
    if normalize(base.get('machine_transcript', '')) != normalize(
        confidence.get('original_machine_transcript', '')
    ):
        raise ValueError(
            f"Recovery original differs for audio_sha256={base.get('audio_sha256')}"
        )
    merged['recovery_status'] = 'confidence_scored_alternative_available'
    merged['recovery_confidence'] = {
        field: confidence[field]
        for field in RECOVERY_FIELDS
        if field in confidence
    }
    merged['recovery_confidence']['original_transcript_preserved'] = True
    return merged


def run(base_path=BASE, confidence_path=CONFIDENCE,
        source_conflict_path=SOURCE_CONFLICTS,
        output_path=OUTPUT, report_path=REPORT):
    base_path = Path(base_path)
    confidence_path = Path(confidence_path)
    output_path = Path(output_path)
    report_path = Path(report_path)
    source_conflict_path = Path(source_conflict_path)
    confidence_rows = read_jsonl(confidence_path)
    confidence_by_hash = {row['audio_sha256']: row for row in confidence_rows}
    if len(confidence_by_hash) != len(confidence_rows):
        raise ValueError('Recovery confidence audio hashes are not unique')
    conflict_rows = read_jsonl(source_conflict_path) if source_conflict_path.exists() else []
    conflicts_by_hash = {row['audio_sha256']: row for row in conflict_rows}

    base_hashes = Counter()
    matched_hashes = set()
    counts = Counter()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + '.tmp')
    with base_path.open(encoding='utf-8') as source, temporary.open(
        'w', encoding='utf-8'
    ) as output:
        for line in source:
            if not line.strip():
                continue
            base = json.loads(line)
            audio_hash = base['audio_sha256']
            base_hashes[audio_hash] += 1
            confidence = confidence_by_hash.get(audio_hash)
            conflict = conflicts_by_hash.get(audio_hash)
            merged = merge_row(base, confidence, conflict)
            output.write(json.dumps(merged, ensure_ascii=False, sort_keys=True) + '\n')
            counts['records'] += 1
            if confidence is not None:
                matched_hashes.add(audio_hash)
                counts['recovery_attached_rows'] += 1
                counts[f"confidence:{confidence['confidence_band']}"] += 1
            else:
                counts['not_targeted_rows'] += 1
            if conflict is not None:
                counts['source_conflict_rows'] += 1
    missing = set(confidence_by_hash) - matched_hashes
    if missing:
        temporary.unlink(missing_ok=True)
        raise ValueError(f'Recovery confidence hashes missing from base: {len(missing)}')
    temporary.replace(output_path)

    report = {
        'run_id': 'sravaani-confidence-aware-integration-v0.1',
        'data_grain': 'one row per original SraVaani source recording row',
        'base_records': counts['records'],
        'base_unique_audio_hashes': len(base_hashes),
        'inherited_duplicate_audio_rows': counts['records'] - len(base_hashes),
        'confidence_records': len(confidence_rows),
        'confidence_unique_audio_hashes': len(confidence_by_hash),
        'recovery_attached_rows': counts['recovery_attached_rows'],
        'not_targeted_rows': counts['not_targeted_rows'],
        'confidence_bands': {
            band: counts[f'confidence:{band}']
            for band in ('medium', 'low', 'very_low')
        },
        'missing_confidence_hashes': len(missing),
        'machine_transcripts_replaced': 0,
        'records_removed_or_quarantined': 0,
        'automatic_promotions': 0,
        'source_conflict_registry_records': len(conflict_rows),
        'source_conflicts_attached_to_machine_rows': counts['source_conflict_rows'],
        'all_records_active_experimentally': counts['source_conflict_rows'] == 0,
        'all_non_conflict_records_active_experimentally': True,
        'all_records_preserved': True,
        'all_supervised_training_eligible': False,
        'inputs': {
            'base': {'path': display_path(base_path), 'sha256': sha256_file(base_path)},
            'confidence': {
                'path': display_path(confidence_path),
                'sha256': sha256_file(confidence_path),
            },
            'source_conflicts': {
                'path': display_path(source_conflict_path),
                'sha256': sha256_file(source_conflict_path),
            },
        },
        'output': {'path': display_path(output_path), 'sha256': sha256_file(output_path)},
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--confidence', type=Path, default=CONFIDENCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    parser.add_argument('--source-conflicts', type=Path, default=SOURCE_CONFLICTS)
    args = parser.parse_args()
    print(json.dumps(
        run(
            args.base, args.confidence, args.source_conflicts,
            args.output, args.report,
        ),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
