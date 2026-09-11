#!/usr/bin/env python3
"""Run dependency-free Garhwali-to-English translation baselines."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'benchmarks/indicgenbench_flores.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/translation'


def normalize(text):
    value = unicodedata.normalize('NFC', str(text)).casefold()
    return re.sub(r'\s+', ' ', value).strip()


def word_ngrams(text, size):
    words = normalize(text).split()
    return Counter(tuple(words[index:index + size]) for index in range(len(words) - size + 1))


def corpus_bleu(references, hypotheses, max_order=4):
    matched = [0] * max_order
    possible = [0] * max_order
    reference_length = 0
    hypothesis_length = 0
    for reference, hypothesis in zip(references, hypotheses):
        reference_words = normalize(reference).split()
        hypothesis_words = normalize(hypothesis).split()
        reference_length += len(reference_words)
        hypothesis_length += len(hypothesis_words)
        for order in range(1, max_order + 1):
            reference_counts = word_ngrams(reference, order)
            hypothesis_counts = word_ngrams(hypothesis, order)
            matched[order - 1] += sum(
                min(count, reference_counts[gram]) for gram, count in hypothesis_counts.items()
            )
            possible[order - 1] += sum(hypothesis_counts.values())
    precisions = [
        (matches + 1) / (total + 1) for matches, total in zip(matched, possible)
    ]
    geometric_mean = math.exp(sum(math.log(value) for value in precisions) / max_order)
    brevity = 1.0 if hypothesis_length > reference_length else math.exp(
        1 - reference_length / max(1, hypothesis_length)
    )
    return round(brevity * geometric_mean, 8)


def character_ngrams(text, size):
    characters = ''.join(normalize(text).split())
    return Counter(characters[index:index + size] for index in range(len(characters) - size + 1))


def corpus_chrf(references, hypotheses, max_order=6, beta=2.0):
    scores = []
    for order in range(1, max_order + 1):
        matches = reference_total = hypothesis_total = 0
        for reference, hypothesis in zip(references, hypotheses):
            reference_counts = character_ngrams(reference, order)
            hypothesis_counts = character_ngrams(hypothesis, order)
            matches += sum(
                min(count, reference_counts[gram]) for gram, count in hypothesis_counts.items()
            )
            reference_total += sum(reference_counts.values())
            hypothesis_total += sum(hypothesis_counts.values())
        precision = matches / max(1, hypothesis_total)
        recall = matches / max(1, reference_total)
        denominator = beta**2 * precision + recall
        scores.append((1 + beta**2) * precision * recall / denominator if denominator else 0.0)
    return round(sum(scores) / max_order, 8)


def trigram_set(text):
    value = f'  {normalize(text)}  '
    return {value[index:index + 3] for index in range(len(value) - 2)}


def translation_memory_predict(development, sources):
    document_grams = [trigram_set(row['source']) for row in development]
    postings = defaultdict(set)
    for index, grams in enumerate(document_grams):
        for gram in grams:
            postings[gram].add(index)
    predictions = []
    for source in sources:
        query = trigram_set(source)
        candidates = set().union(*(postings.get(gram, set()) for gram in query))
        best_index = None
        best_score = 0.0
        for index in candidates:
            score = len(query & document_grams[index]) / max(1, len(query | document_grams[index]))
            if score > best_score or (score == best_score and (best_index is None or index < best_index)):
                best_index = index
                best_score = score
        predictions.append({
            'hypothesis': development[best_index]['target'] if best_index is not None else '',
            'similarity': round(best_score, 8),
            'memory_index': best_index,
        })
    return predictions


def metric_summary(references, hypotheses):
    return {
        'corpus_bleu_smoothed': corpus_bleu(references, hypotheses),
        'corpus_chrf2': corpus_chrf(references, hypotheses),
        'exact_match': round(
            sum(normalize(reference) == normalize(hypothesis)
                for reference, hypothesis in zip(references, hypotheses)) / max(1, len(references)),
            8,
        ),
    }


def run(input_path=INPUT, output_dir=OUTPUT):
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    if any(row.get('source_example', {}).get('translation_direction') != 'xxen' for row in rows):
        raise ValueError('expected only Garhwali-to-English FLORES rows')
    development = [row['source_example'] for row in rows if row.get('split') == 'dev']
    test_rows = [row for row in rows if row.get('split') == 'test']
    sources = [row['source_example']['source'] for row in test_rows]
    references = [row['source_example']['target'] for row in test_rows]
    memory = translation_memory_predict(development, sources)
    memory_hypotheses = [row['hypothesis'] for row in memory]
    copy_hypotheses = sources

    predictions = []
    for row, reference, copy, memory_row in zip(test_rows, references, copy_hypotheses, memory):
        predictions.append({
            'record_id': row.get('record_id'),
            'source': row['source_example']['source'],
            'reference': reference,
            'copy_hypothesis': copy,
            'translation_memory_hypothesis': memory_row['hypothesis'],
            'translation_memory_similarity': memory_row['similarity'],
            'translation_memory_index': memory_row['memory_index'],
        })
    report = {
        'run_id': 'garhwali-english-translation-baselines-v0.1',
        'translation_direction': 'gbm_to_en',
        'development_records': len(development),
        'test_records': len(test_rows),
        'baselines': {
            'copy_source': metric_summary(references, copy_hypotheses),
            'development_translation_memory': metric_summary(references, memory_hypotheses),
        },
        'retrieval': {
            'mean_similarity': round(sum(row['similarity'] for row in memory) / max(1, len(memory)), 8),
            'zero_similarity_records': sum(row['similarity'] == 0 for row in memory),
        },
        'metric_note': 'BLEU uses add-one smoothing; chrF uses character orders 1-6 and beta=2.',
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in predictions),
        encoding='utf-8',
    )
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
