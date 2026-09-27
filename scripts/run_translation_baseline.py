#!/usr/bin/env python3
"""Run dependency-free Garhwali-to-English translation baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from evaluation_run_manifest import utc_now, write_run_artifacts


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
    if len(references) != len(hypotheses) or not references:
        raise ValueError('BLEU requires a non-empty set of paired references and hypotheses')
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
    if not reference_length or not hypothesis_length:
        return 0.0
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
    if len(references) != len(hypotheses) or not references:
        raise ValueError('chrF requires a non-empty set of paired references and hypotheses')
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


def translation_memory_predict(development, sources, exclude_exact_source=False):
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
            if exclude_exact_source and normalize(development[index]['source']) == normalize(source):
                continue
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
    if len(references) != len(hypotheses) or not references:
        raise ValueError('metrics require a non-empty set of paired references and hypotheses')
    return {
        'records': len(references),
        'corpus_bleu_smoothed': corpus_bleu(references, hypotheses),
        'corpus_chrf2': corpus_chrf(references, hypotheses),
        'exact_match': round(
            sum(normalize(reference) == normalize(hypothesis)
                for reference, hypothesis in zip(references, hypotheses)) / max(1, len(references)),
            8,
        ),
        'empty_reference_records': sum(not normalize(reference) for reference in references),
        'empty_hypothesis_records': sum(not normalize(hypothesis) for hypothesis in hypotheses),
    }


def selected_rows_sha256(rows):
    payload = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in rows
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def exact_source_duplicate_summary(examples):
    counts = Counter(normalize(row['source']) for row in examples)
    duplicate_counts = [count for count in counts.values() if count > 1]
    return {
        'duplicate_groups': len(duplicate_counts),
        'rows_in_duplicate_groups': sum(duplicate_counts),
    }


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def select_split(rows, split):
    if split not in {'dev', 'test'}:
        raise ValueError("split must be 'dev' or 'test'")
    selected = sorted(
        (row for row in rows if row.get('split') == split),
        key=lambda row: row.get('record_id', ''),
    )
    if not selected:
        raise ValueError(f'no records found for split: {split}')
    if any(
        not isinstance(row.get('source_example'), dict)
        or row['source_example'].get('translation_direction') != 'xxen'
        for row in selected
    ):
        raise ValueError('expected only Garhwali-to-English FLORES rows')
    return selected


def run(
    input_path=INPUT,
    output_dir=None,
    split='dev',
    max_records=None,
    allow_historical_test=False,
):
    if split not in {'dev', 'test'}:
        raise ValueError("split must be 'dev' or 'test'")
    if split == 'test' and not allow_historical_test:
        raise ValueError('test scoring requires allow_historical_test=True')
    started_at_utc = utc_now()
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    development_rows = select_split(rows, 'dev')
    evaluation_rows = select_split(rows, split)
    if max_records is not None:
        if max_records < 0:
            raise ValueError('max_records must be zero or greater')
        evaluation_rows = evaluation_rows[:max_records] if max_records else evaluation_rows
    development = [row['source_example'] for row in development_rows]
    sources = [row['source_example']['source'] for row in evaluation_rows]
    references = [row['source_example']['target'] for row in evaluation_rows]
    memory = translation_memory_predict(
        development,
        sources,
        exclude_exact_source=(split == 'dev'),
    )
    memory_hypotheses = [row['hypothesis'] for row in memory]
    copy_hypotheses = sources

    predictions = []
    for row, reference, copy, memory_row in zip(evaluation_rows, references, copy_hypotheses, memory):
        memory_index = memory_row['memory_index']
        predictions.append({
            'record_id': row.get('record_id'),
            'source': row['source_example']['source'],
            'reference': reference,
            'copy_hypothesis': copy,
            'translation_memory_hypothesis': memory_row['hypothesis'],
            'translation_memory_similarity': memory_row['similarity'],
            'translation_memory_record_id': (
                development_rows[memory_index].get('record_id')
                if memory_index is not None else None
            ),
        })
    report = {
        'run_id': f'garhwali-english-translation-baselines-{split}-v0.2',
        'translation_direction': 'gbm_to_en',
        'evaluation_split': split,
        'evaluation_status': 'historical_already_scored' if split == 'test' else 'development_only',
        'input_name': Path(input_path).name,
        'script_sha256': file_sha256(__file__),
        'python_version': sys.version.split()[0],
        'max_records': max_records,
        'development_records': len(development),
        'evaluation_records': len(evaluation_rows),
        'selected_record_ids': [row.get('record_id') for row in evaluation_rows],
        'input_sha256': file_sha256(input_path),
        'selected_rows_sha256': selected_rows_sha256(evaluation_rows),
        'exact_normalized_source_duplicates': exact_source_duplicate_summary(
            [row['source_example'] for row in evaluation_rows]
        ),
        'translation_memory_protocol': (
            'dev_leave_exact_normalized_source_out'
            if split == 'dev' else 'dev_memory_to_historical_test'
        ),
        'metric_config': {
            'bleu': 'corpus orders 1-4, add-one smoothing',
            'chrf': 'character orders 1-6, beta=2',
            'normalizer': 'NFC, case-fold, collapse whitespace, trim',
        },
        'baselines': {
            'copy_source': metric_summary(references, copy_hypotheses),
            'development_translation_memory': metric_summary(references, memory_hypotheses),
        },
        'retrieval': {
            'mean_similarity': round(sum(row['similarity'] for row in memory) / max(1, len(memory)), 8),
            'zero_similarity_records': sum(row['similarity'] == 0 for row in memory),
        },
        'metric_note': (
            'BLEU uses add-one smoothing; chrF uses character orders 1-6 and beta=2. '
            'Text is NFC-normalized, case-folded, and whitespace-collapsed.'
        ),
    }
    output_dir = Path(output_dir) if output_dir is not None else OUTPUT / f'accuracy_{split}'
    write_run_artifacts(
        output_dir,
        predictions,
        report,
        config={
            'split': split,
            'max_records': max_records,
            'allow_historical_test': allow_historical_test,
            'translation_memory_protocol': report['translation_memory_protocol'],
            'metric_config': report['metric_config'],
        },
        model={
            'kind': 'deterministic_baselines',
            'components': ['copy_source', 'character_trigram_translation_memory'],
        },
        runtime={'python': sys.version.split()[0]},
        device='cpu',
        code_paths=(__file__, Path(__file__).with_name('evaluation_run_manifest.py')),
        git_root=ROOT,
        started_at_utc=started_at_utc,
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--split', choices=('dev', 'test'), default='dev')
    parser.add_argument('--allow-historical-test', action='store_true')
    parser.add_argument('--max-records', type=int)
    args = parser.parse_args()
    print(json.dumps(
        run(
            args.input,
            args.output,
            split=args.split,
            max_records=args.max_records,
            allow_historical_test=args.allow_historical_test,
        ),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
