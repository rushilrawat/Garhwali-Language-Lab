#!/usr/bin/env python3
"""Register the best existing human-only Whisper checkpoint as curriculum stage 0."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STRICT_TRAIN = ROOT / 'data/processed/model_ready/splits/asr/train.jsonl'
CURRICULUM_TRAIN = ROOT / 'data/processed/model_ready/asr_curriculum/train.jsonl'
VALIDATION = ROOT / 'data/processed/model_ready/splits/asr/validation.jsonl'
V01_CHECKPOINT = ROOT / 'models/whisper-tiny-garhwali-v0.1'
V02_CHECKPOINT = ROOT / 'models/whisper-tiny-garhwali-v0.2'
V01_PREDICTIONS = (
    ROOT / 'data/processed/evaluation/asr/curriculum_stage_0_validation/predictions.jsonl'
)
V02_PREDICTIONS = (
    ROOT / 'data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/predictions.jsonl'
)
SRAVAANI_PREDICTIONS = (
    ROOT / 'data/processed/evaluation/asr/confidence_calibration/sravaani/predictions.jsonl'
)
OUTPUT = ROOT / 'data/processed/evaluation/asr/curriculum_stage_0/report.json'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path):
    return str(Path(path).relative_to(ROOT))


def verify_training_equivalence(strict_rows, curriculum_rows):
    strict = {row['audio_sha256']: row['asr_target_clean'] for row in strict_rows}
    stage_rows = [row for row in curriculum_rows if row['introduced_stage'] == 0]
    stage = {row['audio_sha256']: row['target_text'] for row in stage_rows}
    same_hashes = strict.keys() == stage.keys()
    same_targets = strict == stage
    no_duplicates = len(strict) == len(strict_rows) and len(stage) == len(stage_rows)
    if not (same_hashes and same_targets and no_duplicates):
        raise ValueError('Curriculum stage 0 does not match the strict human training split')
    return {
        'records': len(strict),
        'same_audio_hashes': same_hashes,
        'same_targets': same_targets,
        'duplicate_audio_hashes': 0,
    }


def summarize_predictions(rows, allowed_hashes):
    selected = [row for row in rows if row['audio_sha256'] in allowed_hashes]
    totals = {
        key: sum(row[key] for row in selected)
        for key in (
            'word_errors', 'reference_words',
            'character_errors', 'reference_characters',
        )
    }
    return {
        'records': len(selected),
        **totals,
        'wer': totals['word_errors'] / max(1, totals['reference_words']),
        'cer': totals['character_errors'] / max(1, totals['reference_characters']),
    }


def verify_prediction_references(rows, references):
    filtered = [row for row in rows if row['audio_sha256'] in references]
    selected = {
        row['audio_sha256']: row['reference']
        for row in filtered
    }
    if len(filtered) != len(references) or selected != references:
        raise ValueError('Prediction references do not match the validation manifest')
    return True


def checkpoint_entry(path, metrics):
    training_report = path / 'report.json'
    return {
        'path': relative(path),
        'model_sha256': sha256_file(path / 'model.safetensors'),
        'training_report': relative(training_report),
        'training_report_sha256': sha256_file(training_report),
        'validation': metrics,
    }


def run():
    strict_rows = read_jsonl(STRICT_TRAIN)
    curriculum_rows = read_jsonl(CURRICULUM_TRAIN)
    equivalence = verify_training_equivalence(strict_rows, curriculum_rows)
    validation_targets = {
        row['audio_sha256']: row['asr_target_clean']
        for row in read_jsonl(VALIDATION)
    }
    validation_hashes = set(validation_targets)
    v01_predictions = read_jsonl(V01_PREDICTIONS)
    v02_predictions = read_jsonl(V02_PREDICTIONS)
    sravaani_predictions = read_jsonl(SRAVAANI_PREDICTIONS)
    for predictions in (v01_predictions, v02_predictions, sravaani_predictions):
        verify_prediction_references(predictions, validation_targets)
    candidates = {
        'whisper_tiny_v0.1': checkpoint_entry(
            V01_CHECKPOINT,
            summarize_predictions(v01_predictions, validation_hashes),
        ),
        'whisper_tiny_v0.2': checkpoint_entry(
            V02_CHECKPOINT,
            summarize_predictions(v02_predictions, validation_hashes),
        ),
    }
    comparator = summarize_predictions(
        sravaani_predictions, validation_hashes
    )
    expected = len(validation_hashes)
    if any(candidate['validation']['records'] != expected for candidate in candidates.values()):
        raise ValueError('A human-only checkpoint is missing validation predictions')
    if comparator['records'] != expected:
        raise ValueError('SraVaani is missing validation predictions')
    selected_name = min(candidates, key=lambda name: candidates[name]['validation']['cer'])
    selected = candidates[selected_name]
    report = {
        'run_id': 'garhwali-whisper-curriculum-stage-0-selection-v0.1',
        'curriculum_stage': 0,
        'training_scope': 'human_reference_only',
        'training_equivalence': {
            **equivalence,
            'strict_manifest': relative(STRICT_TRAIN),
            'strict_manifest_sha256': sha256_file(STRICT_TRAIN),
            'curriculum_manifest': relative(CURRICULUM_TRAIN),
            'curriculum_manifest_sha256': sha256_file(CURRICULUM_TRAIN),
        },
        'validation_manifest': relative(VALIDATION),
        'validation_manifest_sha256': sha256_file(VALIDATION),
        'validation_records': expected,
        'human_checkpoint_candidates': candidates,
        'sravaani_comparator': comparator,
        'selection_criterion': 'lowest_validation_cer_among_human_only_checkpoints',
        'selected_checkpoint': selected_name,
        'selected_checkpoint_path': selected['path'],
        'checkpoint_weights_copied': False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    sidecar = {
        'run_id': 'garhwali-whisper-curriculum-stage-0-v0.1',
        'curriculum_stage': 0,
        'training_complete': True,
        'training_scope': 'human_reference_only',
        'training_records': equivalence['records'],
        'training_equivalence_verified': True,
        'selection_report': relative(OUTPUT),
        'selection_report_sha256': sha256_file(OUTPUT),
        'validation': selected['validation'],
        'checkpoint_weights_copied': False,
    }
    selected_path = ROOT / selected['path']
    (selected_path / 'curriculum_stage_report.json').write_text(
        json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
