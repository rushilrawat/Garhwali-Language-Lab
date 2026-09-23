#!/usr/bin/env python3
"""Run multi-seed character-model data-scaling controls for Garhwali text."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / 'data/processed/model_ready/splits/text_recommended/train.jsonl'
VALIDATION = ROOT / 'data/processed/model_ready/splits/text_recommended/validation.jsonl'
TEST = ROOT / 'data/processed/evaluation/garhwali_bench/internal_text.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/controlled_modeling/text_scaling_recommended.json'
DEFAULT_FRACTIONS = (0.01, 0.05, 0.10, 0.25, 0.50, 1.0)
DEFAULT_SEEDS = (17, 29, 43)
DEFAULT_ORDERS = (2, 3)
UNKNOWN = '\ufffd'
BOUNDARY = '\0'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def row_key(row):
    return str(row.get('segment_sha256') or row.get('text_sha256') or row.get('text') or '')


def hash_sample(rows, fraction, seed):
    if not 0 < fraction <= 1:
        raise ValueError('fraction must be in (0, 1]')
    count = max(1, math.ceil(len(rows) * fraction))
    ranked = sorted(
        rows,
        key=lambda row: hashlib.sha256(f'{seed}:{row_key(row)}'.encode()).digest(),
    )
    return ranked[:count]


def character_ngram_score(train_texts, evaluation_texts, order=2):
    if order < 2:
        raise ValueError('order must be at least 2')
    normalized_train = [normalize(text) for text in train_texts]
    vocabulary = {character for text in normalized_train for character in text}
    vocabulary.update({BOUNDARY, UNKNOWN})
    ngrams = Counter()
    contexts = Counter()
    padding = BOUNDARY * (order - 1)
    for text in normalized_train:
        sequence = padding + text + BOUNDARY
        for index in range(order - 1, len(sequence)):
            context = sequence[index - order + 1:index]
            token = sequence[index]
            ngrams[context, token] += 1
            contexts[context] += 1

    negative_log_likelihood = 0.0
    evaluated_tokens = 0
    unknown_tokens = 0
    for text in evaluation_texts:
        normalized = normalize(text)
        mapped = ''.join(character if character in vocabulary else UNKNOWN for character in normalized)
        unknown_tokens += sum(character not in vocabulary for character in normalized)
        sequence = padding + mapped + BOUNDARY
        for index in range(order - 1, len(sequence)):
            context = sequence[index - order + 1:index]
            token = sequence[index]
            probability = (ngrams[context, token] + 1) / (
                contexts[context] + len(vocabulary)
            )
            negative_log_likelihood -= math.log(probability)
            evaluated_tokens += 1
    cross_entropy = negative_log_likelihood / max(1, evaluated_tokens)
    return {
        'order': order,
        'cross_entropy': round(cross_entropy, 8),
        'perplexity': round(math.exp(cross_entropy), 8),
        'train_character_vocabulary': len(vocabulary),
        'train_distinct_ngrams': len(ngrams),
        'evaluated_characters_with_boundaries': evaluated_tokens,
        'evaluation_character_oov_rate': round(
            unknown_tokens / max(1, sum(len(normalize(text)) for text in evaluation_texts)), 8,
        ),
    }


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path):
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def evaluate_run(train_rows, evaluation_texts, fraction, seed, order, split):
    sample = hash_sample(train_rows, fraction, seed)
    result = {
        'fraction': fraction,
        'seed': seed,
        'evaluation_split': split,
        'training_records': len(sample),
        'training_characters': sum(len(normalize(row.get('text', ''))) for row in sample),
    }
    result.update(character_ngram_score(
        [row.get('text', '') for row in sample], evaluation_texts, order,
    ))
    return result


def aggregate_runs(runs):
    groups = defaultdict(list)
    for item in runs:
        groups[item['order'], item['fraction']].append(item)
    aggregate = []
    for (order, fraction), items in sorted(groups.items()):
        losses = [item['cross_entropy'] for item in items]
        perplexities = [item['perplexity'] for item in items]
        aggregate.append({
            'order': order,
            'fraction': fraction,
            'seeds': [item['seed'] for item in items],
            'mean_training_records': round(statistics.mean(
                item['training_records'] for item in items), 3),
            'mean_training_characters': round(statistics.mean(
                item['training_characters'] for item in items), 3),
            'mean_validation_cross_entropy': round(statistics.mean(losses), 8),
            'std_validation_cross_entropy': round(statistics.pstdev(losses), 8),
            'mean_validation_perplexity': round(statistics.mean(perplexities), 8),
            'std_validation_perplexity': round(statistics.pstdev(perplexities), 8),
        })
    return aggregate


def exact_overlap(left_rows, right_rows):
    left = {normalize(row.get('text', '')) for row in left_rows}
    return sum(normalize(row.get('text', '')) in left for row in right_rows)


def run(train_path=TRAIN, validation_path=VALIDATION, test_path=TEST, output_path=OUTPUT,
        fractions=DEFAULT_FRACTIONS, seeds=DEFAULT_SEEDS, orders=DEFAULT_ORDERS):
    train_rows = read_jsonl(train_path)
    validation_rows = read_jsonl(validation_path)
    test_rows = read_jsonl(test_path)
    validation_texts = [row.get('text', '') for row in validation_rows]
    test_texts = [row.get('text', '') for row in test_rows]
    validation_runs = [
        evaluate_run(train_rows, validation_texts, fraction, seed, order, 'validation')
        for order in orders for fraction in fractions for seed in seeds
    ]
    aggregates = aggregate_runs(validation_runs)
    selected = min(
        aggregates,
        key=lambda item: (
            item['mean_validation_cross_entropy'], -item['fraction'], item['order'],
        ),
    )
    configuration = {'order': selected['order'], 'fraction': selected['fraction']}
    frozen_test_runs = [
        evaluate_run(
            train_rows, test_texts, selected['fraction'], seed, selected['order'], 'test',
        )
        for seed in seeds
    ]
    test_losses = [item['cross_entropy'] for item in frozen_test_runs]
    test_perplexities = [item['perplexity'] for item in frozen_test_runs]
    report = {
        'run_id': 'garhwali-controlled-text-scaling-v0.1',
        'model_family': 'add-one-smoothed_character_ngram',
        'data': {
            'train_path': display_path(train_path),
            'validation_path': display_path(validation_path),
            'frozen_test_path': display_path(test_path),
            'train_records': len(train_rows),
            'validation_records': len(validation_rows),
            'frozen_test_records': len(test_rows),
            'train_sha256': sha256_file(train_path),
            'validation_sha256': sha256_file(validation_path),
            'frozen_test_sha256': sha256_file(test_path),
        },
        'design': {
            'fractions': list(fractions),
            'seeds': list(seeds),
            'orders': list(orders),
            'nested_samples_within_seed': True,
            'selection_split': 'validation',
            'final_evaluation_split': 'frozen_test',
        },
        'validation_runs': validation_runs,
        'validation_aggregates': aggregates,
        'selection': {
            'metric': 'mean_validation_cross_entropy',
            'configuration': configuration,
            'mean_validation_cross_entropy': selected['mean_validation_cross_entropy'],
            'mean_validation_perplexity': selected['mean_validation_perplexity'],
        },
        'frozen_test_runs': frozen_test_runs,
        'frozen_test_summary': {
            'mean_cross_entropy': round(statistics.mean(test_losses), 8),
            'std_cross_entropy': round(statistics.pstdev(test_losses), 8),
            'mean_perplexity': round(statistics.mean(test_perplexities), 8),
            'std_perplexity': round(statistics.pstdev(test_perplexities), 8),
        },
        'integrity': {
            'train_validation_exact_text_overlap': exact_overlap(train_rows, validation_rows),
            'train_test_exact_text_overlap': exact_overlap(train_rows, test_rows),
            'test_records_used_during_selection': 0,
        },
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def parse_csv_numbers(value, cast):
    return tuple(cast(item.strip()) for item in value.split(',') if item.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=Path, default=TRAIN)
    parser.add_argument('--validation', type=Path, default=VALIDATION)
    parser.add_argument('--test', type=Path, default=TEST)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--fractions', default=','.join(map(str, DEFAULT_FRACTIONS)))
    parser.add_argument('--seeds', default=','.join(map(str, DEFAULT_SEEDS)))
    parser.add_argument('--orders', default=','.join(map(str, DEFAULT_ORDERS)))
    args = parser.parse_args()
    print(json.dumps(run(
        args.train, args.validation, args.test, args.output,
        parse_csv_numbers(args.fractions, float),
        parse_csv_numbers(args.seeds, int),
        parse_csv_numbers(args.orders, int),
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
