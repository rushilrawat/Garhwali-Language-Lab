#!/usr/bin/env python3
"""Verify and register the normalized weighted-batch ASR stage-1 pilot."""

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
from register_asr_stage1_pilot import (
    compare_metrics,
    paired_outcomes,
    verify_report_metrics,
)


ROOT = Path(__file__).resolve().parents[1]
STAGE0_REPORT = ROOT / 'data/processed/evaluation/asr/curriculum_stage_0/report.json'
ORIGINAL_PILOT_REPORT = (
    ROOT / 'data/processed/evaluation/asr/curriculum_stage_1_pilot/report.json'
)
VALIDATION = ROOT / 'data/processed/model_ready/splits/asr/validation.jsonl'
BASELINE_PREDICTIONS = (
    ROOT / 'data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/predictions.jsonl'
)
PILOT = (
    ROOT
    / 'models/whisper-tiny-garhwali-curriculum-stage-1-pilot-h32-m2048-weighted-batches'
)
OUTPUT = (
    ROOT / 'data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/report.json'
)
BATCHING_STRATEGY = 'stratified_normalized_weighted_gradient_accumulation'


def validate_training_report(report):
    expected = {
        'curriculum_stage': 1,
        'training_complete': False,
        'batching_strategy': BATCHING_STRATEGY,
        'pilot_human_records': 32,
        'pilot_machine_records': 2048,
        'training_examples': 2080,
        'training_steps': 32,
        'records_per_batch': {'minimum': 65, 'maximum': 65},
    }
    if any(report.get(key) != value for key, value in expected.items()):
        raise ValueError('Report is not the expected bounded weighted-batch pilot')
    return True


def run():
    stage0 = json.loads(STAGE0_REPORT.read_text(encoding='utf-8'))
    selected_name = stage0['selected_checkpoint']
    baseline = stage0['human_checkpoint_candidates'][selected_name]['validation']
    original = json.loads(ORIGINAL_PILOT_REPORT.read_text(encoding='utf-8'))['pilot']
    pilot_report_path = PILOT / 'report.json'
    predictions_path = PILOT / 'evaluation_predictions.jsonl'
    pilot_report = json.loads(pilot_report_path.read_text(encoding='utf-8'))
    validate_training_report(pilot_report)

    validation_targets = {
        row['audio_sha256']: row['asr_target_clean']
        for row in read_jsonl(VALIDATION)
    }
    validation_hashes = set(validation_targets)
    baseline_predictions = read_jsonl(BASELINE_PREDICTIONS)
    pilot_predictions = read_jsonl(predictions_path)
    verify_prediction_references(baseline_predictions, validation_targets)
    verify_prediction_references(pilot_predictions, validation_targets)
    pilot = summarize_predictions(pilot_predictions, validation_hashes)
    verify_report_metrics(pilot_report, pilot)
    comparison = compare_metrics(baseline, pilot)

    report = {
        'run_id': 'garhwali-whisper-stage-1-weighted-batch-pilot-h32-m2048-v0.1',
        'status': 'completed',
        'curriculum_stage': 1,
        'training_complete': False,
        'stage_2_unlocked': False,
        'baseline_checkpoint': selected_name,
        'baseline': baseline,
        'original_stage_1_pilot': original,
        'weighted_batch_pilot': pilot,
        'comparison_to_stage_0': comparison,
        'comparison_to_original_stage_1_pilot': {
            'wer_delta': pilot['wer'] - original['wer'],
            'cer_delta': pilot['cer'] - original['cer'],
            'word_error_delta': pilot['word_errors'] - original['word_errors'],
            'character_error_delta': (
                pilot['character_errors'] - original['character_errors']
            ),
        },
        'paired_validation_against_stage_0': paired_outcomes(
            baseline_predictions, pilot_predictions, validation_hashes
        ),
        'training': {
            'batching_strategy': pilot_report['batching_strategy'],
            'human_records': pilot_report['pilot_human_records'],
            'machine_records': pilot_report['pilot_machine_records'],
            'total_records': pilot_report['train_records'],
            'training_examples': pilot_report['training_examples'],
            'optimizer_steps': pilot_report['training_steps'],
            'records_per_batch': pilot_report['records_per_batch'],
            'effective_weight_mass': pilot_report['effective_weight_mass'],
            'epochs': pilot_report['epochs'],
            'mean_raw_loss': pilot_report['mean_raw_training_loss'],
            'mean_objective_loss': pilot_report['mean_training_loss'],
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
        'decision': comparison['decision'],
        'next_action': 'retain_stage_0_and_stop_this_machine_label_curriculum_recipe',
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
