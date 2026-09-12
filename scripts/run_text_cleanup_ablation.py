#!/usr/bin/env python3
"""Measure cleanup proposals on fixed document-level train/test partitions."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/text_cleanup/proposals.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/text_cleanup_ablation/report.json'
DEVANAGARI_TOKEN = re.compile(r'[\u0900-\u097F]+')


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def apply_spelling_candidates(text, candidates):
    replacements = {item['observed']: item['candidate'] for item in candidates}
    return DEVANAGARI_TOKEN.sub(lambda match: replacements.get(match.group(), match.group()), text)


def variant_text(row, variant):
    current = row.get('text_current') or ''
    if variant == 'baseline':
        return current
    mechanical = row.get('proposed_text') or current
    if variant == 'mechanical':
        return mechanical
    if variant == 'spelling':
        return apply_spelling_candidates(mechanical, row.get('spelling_candidates', []))
    raise ValueError(f'unknown variant: {variant}')


def char_bigram_score(train_texts, test_texts):
    vocabulary = {character for text in train_texts for character in normalize(text)}
    pairs = Counter()
    contexts = Counter()
    for text in train_texts:
        sequence = '\0' + normalize(text) + '\0'
        for left, right in zip(sequence, sequence[1:]):
            pairs[left, right] += 1
            contexts[left] += 1
    vocabulary_size = max(1, len(vocabulary) + 2)
    negative_log_likelihood = 0.0
    evaluated = 0
    for text in test_texts:
        sequence = '\0' + normalize(text) + '\0'
        for left, right in zip(sequence, sequence[1:]):
            probability = (pairs[left, right] + 1) / (contexts[left] + vocabulary_size)
            negative_log_likelihood -= math.log(probability)
            evaluated += 1
    loss = negative_log_likelihood / max(1, evaluated)
    return {
        'character_bigram_cross_entropy': round(loss, 8),
        'character_bigram_perplexity': round(math.exp(loss), 8),
        'evaluated_characters_with_boundaries': evaluated,
        'train_character_vocabulary': len(vocabulary),
    }


def lexical_metrics(train_texts, test_texts):
    train_counts = Counter(token for text in train_texts for token in DEVANAGARI_TOKEN.findall(text))
    test_tokens = [token for text in test_texts for token in DEVANAGARI_TOKEN.findall(text)]
    return {
        'train_devanagari_types': len(train_counts),
        'train_singleton_types': sum(frequency == 1 for frequency in train_counts.values()),
        'test_devanagari_tokens': len(test_tokens),
        'test_token_oov_rate': round(
            sum(token not in train_counts for token in test_tokens) / max(1, len(test_tokens)), 8,
        ),
    }


def evaluate(rows, variant):
    train_texts = [variant_text(row, variant) for row in rows if row.get('split') == 'train']
    test_texts = [variant_text(row, variant) for row in rows if row.get('split') == 'test']
    changed = sum(variant_text(row, variant) != variant_text(row, 'baseline') for row in rows)
    result = {
        'train_records': len(train_texts),
        'test_records': len(test_texts),
        'changed_records': changed,
    }
    result.update(char_bigram_score(train_texts, test_texts))
    result.update(lexical_metrics(train_texts, test_texts))
    return result


def delta(candidate, baseline, field):
    return round(candidate[field] - baseline[field], 8)


def run(input_path=INPUT, output_path=OUTPUT):
    rows = read_jsonl(input_path)
    variants = {name: evaluate(rows, name) for name in ('baseline', 'mechanical', 'spelling')}
    baseline = variants['baseline']
    for name in ('mechanical', 'spelling'):
        variants[name]['delta_vs_baseline'] = {
            'character_bigram_perplexity': delta(
                variants[name], baseline, 'character_bigram_perplexity'),
            'test_token_oov_rate': delta(variants[name], baseline, 'test_token_oov_rate'),
            'train_singleton_types': variants[name]['train_singleton_types']
            - baseline['train_singleton_types'],
        }
    mechanical_improves = (
        variants['mechanical']['character_bigram_perplexity']
        <= baseline['character_bigram_perplexity']
        and variants['mechanical']['test_token_oov_rate'] <= baseline['test_token_oov_rate']
    )
    report = {
        'run_id': 'garhwali-text-cleanup-ablation-v0.1',
        'records': {
            'total': len(rows),
            'active_for_experiment': sum(bool(row.get('active_for_experiment')) for row in rows),
            'excluded': sum(not bool(row.get('active_for_experiment')) for row in rows),
        },
        'partitions': {
            'train': sum(row.get('split') == 'train' for row in rows),
            'validation': sum(row.get('split') == 'validation' for row in rows),
            'test': sum(row.get('split') == 'test' for row in rows),
        },
        'variants': variants,
        'promotion': {
            'mechanical': {
                'status': 'eligible_for_versioned_cleaned_view' if mechanical_improves else 'not_promoted',
                'reason': 'Only reversible Unicode, invisible-character, whitespace, and repeated-punctuation changes were tested.',
            },
            'spelling': {
                'status': 'not_promoted',
                'reason': 'Corpus-neighbor substitutions can erase valid dialect and spelling forms even when aggregate metrics improve.',
            },
        },
        'method': {
            'split': 'existing fixed document-level train/test assignments',
            'candidate_lexicon': 'train-only medium/high-confidence Garhwali candidates',
            'primary_metric': 'add-one-smoothed character-bigram perplexity',
            'secondary_metrics': ['test token OOV rate', 'train singleton types'],
            'source_text_mutated': False,
        },
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
