#!/usr/bin/env python3
"""Verify and register the bounded ASR curriculum stage-1 pilot."""

from __future__ import annotations

import json
from pathlib import Path

from register_asr_stage0 import (
    read_jsonl,
    relative,
    sha256_file,
    summarize_predictions,
    verify_prediction_references,
)


ROOT = Path(__file__).resolve().parents[1]
STAGE0_REPORT = ROOT / 'data/processed/evaluation/asr/curriculum_stage_0/report.json'
VALIDATION = ROOT / 'data/processed/model_ready/splits/asr/validation.jsonl'
PILOT = ROOT / 'models/whisper-tiny-garhwali-curriculum-stage-1-pilot-h32-m2048'
OUTPUT = ROOT / 'data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json'


def compare_metrics(baseline, pilot):
    denominator_keys = ('records', 'reference_words', 'reference_characters')
    if any(baseline[key] != pilot[key] for key in denominator_keys):
        raise ValueError('Pilot and baseline must use the same validation set')
    promoted = pilot['wer'] < baseline['wer'] and pilot['cer'] < baseline['cer']
    return {
        'decision': 'promoted' if promoted else 'rejected',
        'promotion_rule': 'pilot_wer_and_cer_must_both_be_lower_than_stage_0',
        'wer_delta': pilot['wer'] - baseline['wer'],
        'cer_delta': pilot['cer'] - baseline['cer'],
        'word_error_delta': pilot['word_errors'] - baseline['word_errors'],
        'character_error_delta': (
            pilot['character_errors'] - baseline['character_errors']
        ),
        'relative_wer_change': (
            (pilot['wer'] - baseline['wer']) / baseline['wer']
        ),
        'relative_cer_change': (
            (pilot['cer'] - baseline['cer']) / baseline['cer']
        ),
    }


def verify_report_metrics(report, metrics):
    mapping = {
        'evaluation_records': 'records',
        'word_errors': 'word_errors',
        'reference_words': 'reference_words',
        'character_errors': 'character_errors',
        'reference_characters': 'reference_characters',
        'wer': 'wer',
        'cer': 'cer',
    }
    if any(report[report_key] != metrics[metric_key] for report_key, metric_key in mapping.items()):
        raise ValueError('Pilot report metrics do not match its saved predictions')


def paired_outcomes(baseline_rows, pilot_rows, allowed_hashes):
    baseline = {
        row['audio_sha256']: row
        for row in baseline_rows
        if row['audio_sha256'] in allowed_hashes
    }
    pilot = {
        row['audio_sha256']: row
        for row in pilot_rows
        if row['audio_sha256'] in allowed_hashes
    }
    if baseline.keys() != pilot.keys() or baseline.keys() != allowed_hashes:
        raise ValueError('Prediction rows cannot form a complete paired comparison')
    if any(baseline[key]['reference'] != pilot[key]['reference'] for key in allowed_hashes):
        raise ValueError('Prediction references differ in paired comparison')

    result = {}
    for metric in ('wer', 'cer'):
        result[metric] = {
            'better': sum(pilot[key][metric] < baseline[key][metric] for key in allowed_hashes),
            'worse': sum(pilot[key][metric] > baseline[key][metric] for key in allowed_hashes),
            'tie': sum(pilot[key][metric] == baseline[key][metric] for key in allowed_hashes),
        }
    result['exact_same_predictions'] = sum(
        pilot[key].get('prediction', pilot[key].get('hypothesis'))
        == baseline[key].get('prediction', baseline[key].get('hypothesis'))
        for key in allowed_hashes
    )
    return result


def run():
    stage0 = json.loads(STAGE0_REPORT.read_text(encoding='utf-8'))
    selected_name = stage0['selected_checkpoint']
    baseline = stage0['human_checkpoint_candidates'][selected_name]['validation']
    pilot_report_path = PILOT / 'report.json'
    predictions_path = PILOT / 'evaluation_predictions.jsonl'
    pilot_report = json.loads(pilot_report_path.read_text(encoding='utf-8'))
    if pilot_report['curriculum_stage'] != 1 or pilot_report['training_complete']:
        raise ValueError('Expected an incomplete bounded curriculum stage-1 pilot')

    validation_targets = {
        row['audio_sha256']: row['asr_target_clean']
        for row in read_jsonl(VALIDATION)
    }
    predictions = read_jsonl(predictions_path)
    verify_prediction_references(predictions, validation_targets)
    pilot = summarize_predictions(predictions, set(validation_targets))
    verify_report_metrics(pilot_report, pilot)
    comparison = compare_metrics(baseline, pilot)

    report = {
        'run_id': 'garhwali-whisper-curriculum-stage-1-pilot-h32-m2048-v0.1',
        'status': 'completed',
        'curriculum_stage': 1,
        'training_complete': False,
        'stage_2_unlocked': False,
        'baseline_checkpoint': selected_name,
        'baseline': baseline,
        'pilot': pilot,
        'comparison': comparison,
        'training': {
            'human_records': pilot_report['pilot_human_records'],
            'machine_records': pilot_report['pilot_machine_records'],
            'total_records': pilot_report['train_records'],
            'full_stage_records': pilot_report['full_stage_train_records'],
            'effective_weight_mass': pilot_report['effective_weight_mass'],
            'epochs': pilot_report['epochs'],
            'steps': pilot_report['training_steps'],
            'mean_raw_loss': pilot_report['mean_raw_training_loss'],
            'mean_weighted_loss': pilot_report['mean_training_loss'],
        },
        'artifacts': {
            'pilot_checkpoint': relative(PILOT),
            'model_sha256': sha256_file(PILOT / 'model.safetensors'),
            'training_report': relative(pilot_report_path),
            'training_report_sha256': sha256_file(pilot_report_path),
            'predictions': relative(predictions_path),
            'predictions_sha256': sha256_file(predictions_path),
            'validation_manifest': relative(VALIDATION),
            'validation_manifest_sha256': sha256_file(VALIDATION),
        },
        'next_action': (
            'retain_stage_0_and_do_not_run_full_stage_1_with_this_configuration'
            if comparison['decision'] == 'rejected'
            else 'replicate_pilot_before_any_full_stage_1_run'
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
