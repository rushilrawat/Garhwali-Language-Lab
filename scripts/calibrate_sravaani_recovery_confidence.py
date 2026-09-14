#!/usr/bin/env python3
"""Calibrate review confidence for SraVaani recovery alternatives."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from asr_metrics import edit_distance, normalize, score


ROOT = Path(__file__).resolve().parents[1]
RECOVERY = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2.jsonl'
SUPERVISED = ROOT / 'data/processed/vaani/supervised.jsonl'
TRAINING_MANIFEST = ROOT / 'data/processed/model_ready/splits/asr/train.jsonl'
CALIBRATION_DIR = ROOT / 'data/processed/evaluation/asr/confidence_calibration'
SRA_BENCHMARK = CALIBRATION_DIR / 'sravaani/predictions.jsonl'
WHISPER_BENCHMARK = CALIBRATION_DIR / 'whisper_v0.2/predictions.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_confidence.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json'


def resolve_project_path(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prediction_text(row):
    return row.get('hypothesis', row.get('prediction', ''))


def character_agreement(left, right):
    left = normalize(left).replace(' ', '')
    right = normalize(right).replace(' ', '')
    if not left and not right:
        return 1.0
    distance = edit_distance(list(left), list(right))
    return max(0.0, 1.0 - distance / max(1, len(left), len(right)))


def agreement_band(value):
    if value >= 0.75:
        return 'strong'
    if value >= 0.50:
        return 'moderate'
    if value >= 0.25:
        return 'weak'
    return 'minimal'


def join_calibration(sravaani_rows, whisper_rows):
    sravaani = {row['audio_sha256']: row for row in sravaani_rows}
    whisper = {row['audio_sha256']: row for row in whisper_rows}
    if set(sravaani) != set(whisper):
        raise ValueError('Benchmark prediction audio hashes do not match')
    joined = []
    for audio_sha256 in sorted(sravaani):
        sra_row = sravaani[audio_sha256]
        whisper_row = whisper[audio_sha256]
        if normalize(sra_row['reference']) != normalize(whisper_row['reference']):
            raise ValueError(f'Benchmark references disagree for {audio_sha256}')
        reference = sra_row['reference']
        sra_text = prediction_text(sra_row)
        whisper_text = prediction_text(whisper_row)
        sra_metrics = score(reference, sra_text)
        whisper_metrics = score(reference, whisper_text)
        agreement = character_agreement(sra_text, whisper_text)
        if sra_metrics['cer'] < whisper_metrics['cer']:
            winner = 'sravaani'
        elif whisper_metrics['cer'] < sra_metrics['cer']:
            winner = 'whisper'
        else:
            winner = 'tie'
        joined.append({
            'audio_sha256': audio_sha256,
            'reference': reference,
            'sravaani_hypothesis': sra_text,
            'whisper_hypothesis': whisper_text,
            'sra_metrics': sra_metrics,
            'whisper_metrics': whisper_metrics,
            'character_agreement': agreement,
            'agreement_band': agreement_band(agreement),
            'lower_cer_model': winner,
        })
    return joined


def micro_metrics(rows, key):
    word_errors = sum(row[key]['word_errors'] for row in rows)
    reference_words = sum(row[key]['reference_words'] for row in rows)
    character_errors = sum(row[key]['character_errors'] for row in rows)
    reference_characters = sum(row[key]['reference_characters'] for row in rows)
    return {
        'wer': word_errors / max(1, reference_words),
        'cer': character_errors / max(1, reference_characters),
        'word_errors': word_errors,
        'reference_words': reference_words,
        'character_errors': character_errors,
        'reference_characters': reference_characters,
    }


def pearson(values):
    if len(values) < 2:
        return None
    left_mean = sum(left for left, _ in values) / len(values)
    right_mean = sum(right for _, right in values) / len(values)
    numerator = sum((left - left_mean) * (right - right_mean) for left, right in values)
    left_scale = math.sqrt(sum((left - left_mean) ** 2 for left, _ in values))
    right_scale = math.sqrt(sum((right - right_mean) ** 2 for _, right in values))
    if not left_scale or not right_scale:
        return None
    return numerator / (left_scale * right_scale)


def summarize_calibration(rows):
    result = {}
    for band in ('strong', 'moderate', 'weak', 'minimal'):
        selected = [row for row in rows if row['agreement_band'] == band]
        if not selected:
            continue
        result[band] = {
            'records': len(selected),
            'sravaani': micro_metrics(selected, 'sra_metrics'),
            'whisper': micro_metrics(selected, 'whisper_metrics'),
            'lower_cer_model_counts': dict(sorted(Counter(
                row['lower_cer_model'] for row in selected
            ).items())),
        }
    result['all'] = {
        'records': len(rows),
        'sravaani': micro_metrics(rows, 'sra_metrics'),
        'whisper': micro_metrics(rows, 'whisper_metrics'),
        'lower_cer_model_counts': dict(sorted(Counter(
            row['lower_cer_model'] for row in rows
        ).items())),
        'agreement_to_sravaani_cer_pearson': pearson([
            (row['character_agreement'], row['sra_metrics']['cer']) for row in rows
        ]),
        'agreement_to_whisper_cer_pearson': pearson([
            (row['character_agreement'], row['whisper_metrics']['cer']) for row in rows
        ]),
    }
    return result


def calibration_for_band(calibration, band):
    if band in calibration:
        return band, calibration[band], True
    if 'all' in calibration:
        return 'all_fallback_no_matching_bin', calibration['all'], False
    name, values = next(iter(calibration.items()))
    return f'{name}_fallback_no_matching_bin', values, False


def score_recovery_row(row, calibration, direct_reference=False):
    original = row['original_machine_transcript']
    alternative = row['whisper_candidate']
    agreement = character_agreement(original, alternative)
    band = agreement_band(agreement)
    preference = row['structural_preference']
    model_key = 'sravaani' if preference == 'sravaani_original' else 'whisper'
    selected_flags = (
        row.get('quality_flags', []) if model_key == 'sravaani'
        else row.get('whisper_candidate_flags', [])
    )
    calibration_name, calibration_bin, in_bin_support = calibration_for_band(
        calibration, band
    )
    benchmark_cer = calibration_bin[model_key]['cer']
    benchmark_character_accuracy = max(0.0, 1.0 - min(1.0, benchmark_cer))
    flag_penalty = 0.25 if selected_flags else 1.0
    support_penalty = 1.0 if in_bin_support else 0.5
    evidence_score = (
        benchmark_character_accuracy * (0.5 + 0.5 * agreement)
        * flag_penalty * support_penalty
    )
    if selected_flags or not in_bin_support:
        confidence = 'very_low'
    elif band == 'strong' and benchmark_character_accuracy >= 0.70 \
            and calibration_bin['records'] >= 10:
        confidence = 'medium'
    elif agreement >= 0.35 and benchmark_character_accuracy >= 0.45:
        confidence = 'low'
    else:
        confidence = 'very_low'
    return {
        **row,
        'cross_model_character_agreement': round(agreement, 6),
        'cross_model_agreement_band': band,
        'confidence_score': round(evidence_score, 6),
        'confidence_band': confidence,
        'confidence_scope': 'cross_model_review_priority',
        'confidence_is_accuracy_probability': False,
        'confidence_ceiling': 'medium_without_same_record_human_reference',
        'direct_human_reference_available': direct_reference,
        'calibration_domain': 'separate_112_record_supervised_vaani_test',
        'calibration_band_used': calibration_name,
        'calibration_in_matching_band_support': in_bin_support,
        'calibration_bin_records': calibration_bin['records'],
        'calibration_selected_model_cer': benchmark_cer,
        'selected_candidate_flags': selected_flags,
        'review_priority': round(100 * (1.0 - evidence_score), 3),
        'automatic_promotion': False,
        'supervised_training_eligible': False,
        'original_preserved': True,
    }


def run(recovery_path=RECOVERY, supervised_path=SUPERVISED,
        training_manifest_path=TRAINING_MANIFEST,
        sravaani_benchmark_path=SRA_BENCHMARK,
        whisper_benchmark_path=WHISPER_BENCHMARK,
        output_path=OUTPUT, report_path=REPORT):
    recovery_path = resolve_project_path(recovery_path)
    supervised_path = resolve_project_path(supervised_path)
    training_manifest_path = resolve_project_path(training_manifest_path)
    sravaani_benchmark_path = resolve_project_path(sravaani_benchmark_path)
    whisper_benchmark_path = resolve_project_path(whisper_benchmark_path)
    output_path = resolve_project_path(output_path)
    report_path = resolve_project_path(report_path)
    recovery = read_jsonl(recovery_path)
    supervised = read_jsonl(supervised_path)
    calibration_rows = join_calibration(
        read_jsonl(sravaani_benchmark_path), read_jsonl(whisper_benchmark_path)
    )
    calibration = summarize_calibration(calibration_rows)
    calibration_hashes = {row['audio_sha256'] for row in calibration_rows}
    training_hashes = {
        row['audio_sha256'] for row in read_jsonl(training_manifest_path)
    }
    training_overlap = calibration_hashes & training_hashes
    if training_overlap:
        raise ValueError('Confidence calibration overlaps Whisper training audio')
    recovery_hashes = {row['audio_sha256'] for row in recovery}
    supervised_hashes = {row['audio_sha256'] for row in supervised}
    direct_hashes = recovery_hashes & supervised_hashes
    scored = [
        score_recovery_row(
            row, calibration, direct_reference=row['audio_sha256'] in direct_hashes
        )
        for row in recovery
    ]
    scored.sort(key=lambda row: (-row['review_priority'], row['audio_sha256']))
    write_jsonl(output_path, scored)
    output_hashes = {row['audio_sha256'] for row in scored}
    report = {
        'run_id': 'sravaani-recovery-confidence-v0.2',
        'data_grain': 'one row per recovery audio SHA-256',
        'inputs': {
            'recovery': {
                'path': str(Path(recovery_path).relative_to(ROOT)),
                'sha256': sha256_file(recovery_path),
            },
            'supervised_vaani': {
                'path': str(Path(supervised_path).relative_to(ROOT)),
                'sha256': sha256_file(supervised_path),
            },
            'whisper_training_manifest': {
                'path': str(Path(training_manifest_path).relative_to(ROOT)),
                'sha256': sha256_file(training_manifest_path),
            },
            'sravaani_benchmark_predictions': {
                'path': str(Path(sravaani_benchmark_path).relative_to(ROOT)),
                'sha256': sha256_file(sravaani_benchmark_path),
            },
            'whisper_benchmark_predictions': {
                'path': str(Path(whisper_benchmark_path).relative_to(ROOT)),
                'sha256': sha256_file(whisper_benchmark_path),
            },
        },
        'output': str(Path(output_path).relative_to(ROOT)),
        'records': len(scored),
        'unique_audio_hashes': len(output_hashes),
        'coverage': {
            'expected_unique_audio_hashes': len(recovery_hashes),
            'missing_audio_hashes': len(recovery_hashes - output_hashes),
            'unexpected_audio_hashes': len(output_hashes - recovery_hashes),
        },
        'human_reference_audit': {
            'supervised_vaani_records': len(supervised),
            'supervised_unique_audio_hashes': len(supervised_hashes),
            'same_record_reference_matches': len(direct_hashes),
            'calibration_records': len(calibration_rows),
            'calibration_unique_audio_hashes': len(calibration_hashes),
            'calibration_whisper_training_overlap': len(training_overlap),
        },
        'confidence_bands': dict(sorted(Counter(
            row['confidence_band'] for row in scored
        ).items())),
        'agreement_bands': dict(sorted(Counter(
            row['cross_model_agreement_band'] for row in scored
        ).items())),
        'structural_preferences': dict(sorted(Counter(
            row['structural_preference'] for row in scored
        ).items())),
        'selected_candidate_flagged_records': sum(
            bool(row['selected_candidate_flags']) for row in scored
        ),
        'out_of_matching_calibration_band_records': sum(
            not row['calibration_in_matching_band_support'] for row in scored
        ),
        'automatic_promotions': sum(row['automatic_promotion'] for row in scored),
        'supervised_training_eligible': sum(
            row['supervised_training_eligible'] for row in scored
        ),
        'originals_preserved': all(row['original_preserved'] for row in scored),
        'calibration': calibration,
        'confidence_definition': {
            'scope': 'review priority, not transcript correctness probability',
            'score': '(1 - benchmark-bin CER) * (0.5 + 0.5 * cross-model agreement) * structural-flag penalty * calibration-support penalty',
            'structural_flag_penalty': 0.25,
            'out_of_matching_calibration_band_penalty': 0.5,
            'maximum_band_without_same_record_reference': 'medium',
        },
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--recovery', type=Path, default=RECOVERY)
    parser.add_argument('--supervised', type=Path, default=SUPERVISED)
    parser.add_argument('--training-manifest', type=Path, default=TRAINING_MANIFEST)
    parser.add_argument('--sravaani-benchmark', type=Path, default=SRA_BENCHMARK)
    parser.add_argument('--whisper-benchmark', type=Path, default=WHISPER_BENCHMARK)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(run(
        args.recovery,
        args.supervised,
        args.training_manifest,
        args.sravaani_benchmark,
        args.whisper_benchmark,
        args.output,
        args.report,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
