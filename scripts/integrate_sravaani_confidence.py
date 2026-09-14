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


def merge_row(base, confidence):
    merged = dict(base)
    merged['training_eligible'] = False
    merged['experimental_training_eligible'] = True
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
        output_path=OUTPUT, report_path=REPORT):
    base_path = Path(base_path)
    confidence_path = Path(confidence_path)
    output_path = Path(output_path)
    report_path = Path(report_path)
    confidence_rows = read_jsonl(confidence_path)
    confidence_by_hash = {row['audio_sha256']: row for row in confidence_rows}
    if len(confidence_by_hash) != len(confidence_rows):
        raise ValueError('Recovery confidence audio hashes are not unique')

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
            merged = merge_row(base, confidence)
            output.write(json.dumps(merged, ensure_ascii=False, sort_keys=True) + '\n')
            counts['records'] += 1
            if confidence is not None:
                matched_hashes.add(audio_hash)
                counts['recovery_attached_rows'] += 1
                counts[f"confidence:{confidence['confidence_band']}"] += 1
            else:
                counts['not_targeted_rows'] += 1
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
        'all_records_active_experimentally': True,
        'all_supervised_training_eligible': False,
        'inputs': {
            'base': {'path': str(base_path), 'sha256': sha256_file(base_path)},
            'confidence': {
                'path': str(confidence_path),
                'sha256': sha256_file(confidence_path),
            },
        },
        'output': {'path': str(output_path), 'sha256': sha256_file(output_path)},
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
    args = parser.parse_args()
    print(json.dumps(
        run(args.base, args.confidence, args.output, args.report),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
