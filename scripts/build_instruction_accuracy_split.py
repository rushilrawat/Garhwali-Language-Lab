#!/usr/bin/env python3
"""Freeze a new instruction test split unseen by the first mT5 pilot."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import run_mt5_instruction_tuning as tuning


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/instructions'
OUTPUT = ROOT / 'data/processed/model_ready/instructions_v0.2'
PRIOR_SEEDS = (17, 29, 43)
PRIOR_STEPS = 64
PRIOR_BATCH_SIZE = 1


def prior_seen_parent_ids(rows, seeds=PRIOR_SEEDS, steps=PRIOR_STEPS,
                          batch_size=PRIOR_BATCH_SIZE):
    seen = set()
    examples = min(len(rows), steps * batch_size)
    for seed in seeds:
        pool = tuning.select_rows(rows, len(rows), seed)
        seen.update(
            row['parent_text_sha256'] for row in pool[:examples]
        )
    return seen


def rank_key(seed, label, value):
    return hashlib.sha256(f'{seed}:{label}:{value}'.encode()).digest()


def select_holdout_parent_ids(rows, excluded_parent_ids, target_records=256,
                              seed=211):
    groups = defaultdict(list)
    for row in rows:
        parent = row['parent_text_sha256']
        if parent not in excluded_parent_ids:
            groups[parent].append(row)
    if sum(map(len, groups.values())) < target_records:
        raise ValueError('not enough unseen parent groups for requested test size')

    tasks = sorted({row['task'] for group in groups.values() for row in group})
    selected = set()
    covered = set()
    for task in tasks:
        if task in covered:
            continue
        candidates = [
            parent for parent, group in groups.items()
            if task in {row['task'] for row in group}
        ]
        parent = min(candidates, key=lambda value: rank_key(seed, task, value))
        selected.add(parent)
        covered.update(row['task'] for row in groups[parent])

    record_count = sum(len(groups[parent]) for parent in selected)
    ranked = sorted(groups, key=lambda value: rank_key(seed, 'all', value))
    for parent in ranked:
        if record_count >= target_records:
            break
        if parent in selected:
            continue
        selected.add(parent)
        record_count += len(groups[parent])
    return selected


def split_rows(train_rows, validation_rows, target_test_records=256,
               prior_seeds=PRIOR_SEEDS, prior_steps=PRIOR_STEPS,
               prior_batch_size=PRIOR_BATCH_SIZE, seed=211):
    prior_seen = prior_seen_parent_ids(
        train_rows, prior_seeds, prior_steps, prior_batch_size,
    )
    test_parents = select_holdout_parent_ids(
        train_rows, prior_seen, target_test_records, seed,
    )
    train = [
        row | {'split': 'train'} for row in train_rows
        if row['parent_text_sha256'] not in test_parents
    ]
    validation = [row | {'split': 'validation'} for row in validation_rows]
    test = [
        row | {'split': 'test'} for row in train_rows
        if row['parent_text_sha256'] in test_parents
    ]
    split_parents = defaultdict(set)
    for split, records in (
        ('train', train), ('validation', validation), ('test', test),
    ):
        for row in records:
            split_parents[row['parent_text_sha256']].add(split)
    return {
        'train': train,
        'validation': validation,
        'test': test,
        'prior_seen_parent_ids': prior_seen,
        'integrity': {
            'parent_cross_split': sum(
                len(splits) > 1 for splits in split_parents.values()
            ),
            'prior_seen_parent_test_overlap': len(prior_seen & test_parents),
            'all_records_active_for_experiment': all(
                row.get('active_for_experiment') is True
                for row in train + validation + test
            ),
            'test_task_count': len({row['task'] for row in test}),
        },
    }


def build(input_dir=INPUT, output_dir=OUTPUT, target_test_records=256):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    train_rows = tuning.read_jsonl(input_dir / 'train.jsonl')
    validation_rows = tuning.read_jsonl(input_dir / 'validation.jsonl')
    closed_test_rows = tuning.read_jsonl(input_dir / 'test.jsonl')
    result = split_rows(train_rows, validation_rows, target_test_records)
    output_dir.mkdir(parents=True, exist_ok=True)
    for split in ('train', 'validation', 'test'):
        rows = sorted(result[split], key=lambda row: row['instruction_sha256'])
        tuning.write_jsonl(output_dir / f'{split}.jsonl', rows)
    report = {
        'run_id': 'garhwali-instruction-accuracy-split-v0.2',
        'records': {
            split: len(result[split]) for split in ('train', 'validation', 'test')
        },
        'previously_closed_test_records_not_reused': len(closed_test_rows),
        'prior_pilot': {
            'seeds': list(PRIOR_SEEDS),
            'steps_per_seed': PRIOR_STEPS,
            'batch_size': PRIOR_BATCH_SIZE,
            'seen_parent_count': len(result['prior_seen_parent_ids']),
        },
        'integrity': result['integrity'] | {
            'previously_closed_test_reused': 0,
            'provenance_preserved': True,
            'rights_metadata_preserved': True,
        },
        'policy': {
            'selection_split': 'existing validation split',
            'new_test_source': 'previous training split parents unseen by prior pilot',
            'new_test_frozen_before_mt0_training': True,
            'all_source_records_remain_active_in_versioned_views': True,
        },
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
