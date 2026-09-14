#!/usr/bin/env python3
"""Build a confidence-weighted ASR curriculum without changing source records."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HUMAN_SPLITS = ROOT / 'data/processed/model_ready/splits/asr'
MACHINE = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl'
CONFIDENCE_REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json'
OUTPUT = ROOT / 'data/processed/model_ready/asr_curriculum'
STAGES = {
    'human_reference': 0,
    'standard_sravaani': 1,
    'recovery_medium': 2,
    'recovery_low': 3,
    'recovery_very_low': 4,
}


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


def human_row(row, split):
    return {
        'audio_sha256': row['audio_sha256'],
        'local_audio_path': row['local_audio_path'],
        'duration_seconds': row.get('duration_seconds'),
        'target_text': row['asr_target_clean'],
        'target_type': 'human_reference',
        'target_model': None,
        'target_selection': 'human_reference',
        'curriculum_tier': 'human_reference',
        'introduced_stage': 0,
        'sample_weight': 1.0,
        'split': split,
        'speaker_id': row.get('speaker_id'),
        'district': row.get('district'),
        'gender': row.get('gender'),
        'source': row.get('source'),
        'license': row.get('license'),
        'quality_flags': row.get('training_quality_flags', []),
        'supervised_training_eligible': True,
        'active_for_experiment': True,
    }


def recovery_target(row):
    recovery = row['recovery_confidence']
    if recovery['structural_preference'] == 'whisper_candidate':
        return recovery['whisper_candidate'], recovery.get(
            'whisper_candidate_model', 'whisper-tiny-garhwali-v0.2'
        )
    return row['machine_transcript'], row.get(
        'machine_transcript_model', 'ARTPARK-IISc/SraVaani-1.0'
    )


def machine_raw_score(row, standard_score):
    if row.get('recovery_status') != 'confidence_scored_alternative_available':
        return standard_score
    return max(0.001, float(row['recovery_confidence']['confidence_score']))


def machine_weight_scale(raw_scores, human_records, ratio=1.0):
    total = sum(raw_scores)
    if total <= 0:
        raise ValueError('Machine confidence scores must have positive mass')
    return human_records * ratio / total


def machine_row(row, standard_score, weight_scale):
    recovery = row.get('recovery_confidence')
    if recovery is None:
        tier = 'standard_sravaani'
        target_text = row['machine_transcript']
        target_model = row.get(
            'machine_transcript_model', 'ARTPARK-IISc/SraVaani-1.0'
        )
        confidence_score = standard_score
        confidence_band = 'standard_unflagged_sravaani'
        confidence_scope = 'expanded_381_reference_model_calibration'
        target_selection = 'standard_sravaani'
        quality_flags = row.get('machine_transcript_quality', {}).get('flags', [])
    else:
        confidence_band = recovery['confidence_band']
        tier = f'recovery_{confidence_band}'
        target_text, target_model = recovery_target(row)
        confidence_score = machine_raw_score(row, standard_score)
        confidence_scope = recovery.get(
            'confidence_scope', 'cross_model_review_priority'
        )
        target_selection = 'structural_preference'
        quality_flags = recovery.get('selected_candidate_flags', [])
        if not target_text.strip():
            alternative = recovery.get('whisper_candidate', '')
            if recovery['structural_preference'] == 'whisper_candidate':
                alternative = row['machine_transcript']
                target_model = row.get(
                    'machine_transcript_model', 'ARTPARK-IISc/SraVaani-1.0'
                )
                quality_flags = row.get('machine_transcript_quality', {}).get('flags', [])
            else:
                target_model = recovery.get(
                    'whisper_candidate_model', 'whisper-tiny-garhwali-v0.2'
                )
                quality_flags = recovery.get('whisper_candidate_flags', [])
            if not alternative.strip():
                raise ValueError(f"No non-empty transcript candidate for {row['audio_sha256']}")
            target_text = alternative
            target_selection = 'nonempty_candidate_fallback'
    raw_score = machine_raw_score(row, standard_score)
    return {
        'audio_sha256': row['audio_sha256'],
        'local_audio_path': row['local_audio_path'],
        'duration_seconds': row.get('duration_seconds'),
        'target_text': target_text,
        'target_type': 'machine_pseudo_label',
        'target_model': target_model,
        'target_selection': target_selection,
        'original_machine_transcript': row['machine_transcript'],
        'curriculum_tier': tier,
        'introduced_stage': STAGES[tier],
        'sample_weight': round(raw_score * weight_scale, 10),
        'raw_confidence_score': confidence_score,
        'confidence_band': confidence_band,
        'confidence_scope': confidence_scope,
        'confidence_is_accuracy_probability': False,
        'split': 'train',
        'speaker_id': row.get('speaker_id'),
        'district': row.get('district'),
        'gender': row.get('gender'),
        'source': row.get('source'),
        'license': row.get('license'),
        'quality_flags': quality_flags,
        'source_audio_records': row.get('source_audio_records', 1),
        'supervised_training_eligible': False,
        'active_for_experiment': True,
    }


def deduplicate_machine_rows(rows):
    groups = {}
    for row in rows:
        audio_hash = row['audio_sha256']
        if audio_hash not in groups:
            groups[audio_hash] = dict(row)
            groups[audio_hash]['source_audio_records'] = 1
            continue
        current = groups[audio_hash]
        if current.get('machine_transcript') != row.get('machine_transcript'):
            raise ValueError(f'Conflicting machine transcripts for {audio_hash}')
        if current.get('recovery_confidence') != row.get('recovery_confidence'):
            raise ValueError(f'Conflicting recovery evidence for {audio_hash}')
        current['source_audio_records'] += 1
    return [groups[key] for key in sorted(groups)]


def summarize_rows(rows):
    tiers = Counter(row['curriculum_tier'] for row in rows)
    weight_mass = Counter()
    hours = Counter()
    for row in rows:
        tier = row['curriculum_tier']
        weight_mass[tier] += row['sample_weight']
        hours[tier] += float(row.get('duration_seconds') or 0) / 3600
    return {
        'records': dict(sorted(tiers.items())),
        'effective_weight_mass': {
            key: round(value, 6) for key, value in sorted(weight_mass.items())
        },
        'hours': {key: round(value, 6) for key, value in sorted(hours.items())},
    }


def run(human_splits=HUMAN_SPLITS, machine_path=MACHINE,
        confidence_report_path=CONFIDENCE_REPORT, output_dir=OUTPUT,
        machine_weight_ratio=1.0):
    human_splits = Path(human_splits)
    machine_path = Path(machine_path)
    confidence_report_path = Path(confidence_report_path)
    output_dir = Path(output_dir)
    human = {
        split: read_jsonl(human_splits / f'{split}.jsonl')
        for split in ('train', 'validation', 'test')
    }
    confidence_report = json.loads(confidence_report_path.read_text())
    standard_score = 1.0 - confidence_report['calibration']['all']['sravaani']['cer']
    machine_source_rows = read_jsonl(machine_path)
    machine_unique = deduplicate_machine_rows(machine_source_rows)

    human_hashes = {
        split: {row['audio_sha256'] for row in rows}
        for split, rows in human.items()
    }
    if any(human_hashes[left] & human_hashes[right] for left, right in (
        ('train', 'validation'), ('train', 'test'), ('validation', 'test')
    )):
        raise ValueError('Human ASR splits overlap by audio hash')
    machine_hashes = {row['audio_sha256'] for row in machine_unique}
    all_human_hashes = set().union(*human_hashes.values())
    if machine_hashes & all_human_hashes:
        raise ValueError('Machine curriculum audio overlaps human ASR splits')

    raw_scores = [machine_raw_score(row, standard_score) for row in machine_unique]
    scale = machine_weight_scale(
        raw_scores, human_records=len(human['train']), ratio=machine_weight_ratio
    )
    train = [human_row(row, 'train') for row in human['train']]
    train.extend(machine_row(row, standard_score, scale) for row in machine_unique)
    train.sort(key=lambda row: (row['introduced_stage'], row['audio_sha256']))
    validation = [human_row(row, 'validation') for row in human['validation']]
    test = [human_row(row, 'test') for row in human['test']]
    empty_training_targets = sum(not row['target_text'].strip() for row in train)
    if empty_training_targets:
        raise ValueError(f'Curriculum contains {empty_training_targets} empty training targets')
    write_jsonl(output_dir / 'train.jsonl', train)
    write_jsonl(output_dir / 'validation.jsonl', validation)
    write_jsonl(output_dir / 'test.jsonl', test)

    stage_plan = {
        'stage_0': {'tiers': ['human_reference']},
        'stage_1': {'tiers': ['human_reference', 'standard_sravaani']},
        'stage_2': {'tiers': ['human_reference', 'standard_sravaani', 'recovery_medium']},
        'stage_3': {'tiers': ['human_reference', 'standard_sravaani', 'recovery_medium', 'recovery_low']},
        'stage_4': {'tiers': list(STAGES)},
        'selection': 'introduced_stage <= active stage',
        'loss_weight': 'sample_weight',
        'evaluation': 'human-only validation and test',
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'stage_plan.json').write_text(
        json.dumps(stage_plan, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    summary = summarize_rows(train)
    machine_mass = sum(
        row['sample_weight'] for row in train if row['target_type'] == 'machine_pseudo_label'
    )
    report = {
        'run_id': 'garhwali-asr-confidence-curriculum-v0.1',
        'train_records': len(train),
        'validation_records': len(validation),
        'test_records': len(test),
        'human_train_records': len(human['train']),
        'machine_source_records': len(machine_source_rows),
        'machine_unique_audio_records': len(machine_unique),
        'inherited_machine_duplicate_rows': len(machine_source_rows) - len(machine_unique),
        'machine_weight_ratio': machine_weight_ratio,
        'machine_weight_scale': scale,
        'human_effective_weight_mass': float(len(human['train'])),
        'machine_effective_weight_mass': round(machine_mass, 6),
        'standard_sravaani_raw_score': standard_score,
        'curriculum': summary,
        'audio_hash_leakage': {
            'machine_to_human': 0,
            'human_cross_split': 0,
        },
        'empty_training_targets': empty_training_targets,
        'nonempty_candidate_fallbacks': sum(
            row['target_selection'] == 'nonempty_candidate_fallback' for row in train
        ),
        'records_removed_or_quarantined': 0,
        'all_unique_machine_audio_active': len(machine_unique),
        'validation_and_test_human_only': True,
        'inputs': {
            'machine': {'path': str(machine_path), 'sha256': sha256_file(machine_path)},
            'confidence_report': {
                'path': str(confidence_report_path),
                'sha256': sha256_file(confidence_report_path),
            },
        },
        'outputs': {
            name: {
                'path': str(output_dir / name),
                'sha256': sha256_file(output_dir / name),
            }
            for name in ('train.jsonl', 'validation.jsonl', 'test.jsonl', 'stage_plan.json')
        },
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--human-splits', type=Path, default=HUMAN_SPLITS)
    parser.add_argument('--machine', type=Path, default=MACHINE)
    parser.add_argument('--confidence-report', type=Path, default=CONFIDENCE_REPORT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--machine-weight-ratio', type=float, default=1.0)
    args = parser.parse_args()
    print(json.dumps(run(
        args.human_splits,
        args.machine,
        args.confidence_report,
        args.output,
        args.machine_weight_ratio,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
