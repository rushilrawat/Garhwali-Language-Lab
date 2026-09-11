#!/usr/bin/env python3
"""Run dependency-free passage-retrieval baselines on Garhwali XORQA."""

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
INPUT = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/retrieval'
TEST_PILOT_RECORDS = 128


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text)).casefold()).strip()


def word_tokens(text):
    return re.findall(r'[^\W_]+', normalize(text), flags=re.UNICODE)


def character_ngrams(text, orders=(3, 4, 5)):
    value = f'  {normalize(text)}  '
    return [
        value[index:index + order]
        for order in orders
        for index in range(len(value) - order + 1)
    ]


def context_id(context):
    return hashlib.sha256(normalize(context).encode('utf-8')).hexdigest()


def build_documents(rows):
    contexts = {}
    relevant_ids = []
    for row in rows:
        context = row['source_example']['context']
        document_id = context_id(context)
        contexts.setdefault(document_id, context)
        relevant_ids.append(document_id)
    documents = [
        {'document_id': document_id, 'text': contexts[document_id]}
        for document_id in sorted(contexts)
    ]
    return documents, relevant_ids


class BM25Index:
    def __init__(self, documents, analyzer, k1=1.5, b=0.75):
        self.documents = sorted(documents, key=lambda row: row['document_id'])
        self.k1 = k1
        self.b = b
        self.postings = defaultdict(list)
        self.lengths = {}
        document_frequency = Counter()
        for document in self.documents:
            counts = Counter(analyzer(document['text']))
            document_id = document['document_id']
            self.lengths[document_id] = sum(counts.values())
            for token, frequency in counts.items():
                document_frequency[token] += 1
                self.postings[token].append((document_id, frequency))
        self.average_length = sum(self.lengths.values()) / max(1, len(self.documents))
        total = len(self.documents)
        self.idf = {
            token: math.log(1 + (total - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }
        self.analyzer = analyzer

    def rank(self, query, top_k=10):
        scores = defaultdict(float)
        for token in set(self.analyzer(query)):
            for document_id, frequency in self.postings.get(token, ()):
                length_ratio = self.lengths[document_id] / max(self.average_length, 1)
                denominator = frequency + self.k1 * (1 - self.b + self.b * length_ratio)
                scores[document_id] += self.idf[token] * frequency * (self.k1 + 1) / denominator
        ranked = sorted(
            (
                {'document_id': document['document_id'], 'score': round(scores[document['document_id']], 8)}
                for document in self.documents
            ),
            key=lambda row: (-row['score'], row['document_id']),
        )
        return ranked[:top_k]


def metric_summary(results):
    ranks = [row['rank'] for row in results]
    return {
        'queries': len(results),
        'recall_at_1': round(sum(rank <= 1 for rank in ranks) / max(1, len(ranks)), 8),
        'recall_at_5': round(sum(rank <= 5 for rank in ranks) / max(1, len(ranks)), 8),
        'recall_at_10': round(sum(rank <= 10 for rank in ranks) / max(1, len(ranks)), 8),
        'mrr_at_10': round(
            sum(1 / rank for rank in ranks if rank <= 10) / max(1, len(ranks)),
            8,
        ),
        'mean_rank': round(sum(ranks) / max(1, len(ranks)), 6),
        'median_rank': round(statistics.median(ranks), 6) if ranks else None,
        'zero_relevant_score_queries': sum(row['relevant_score'] == 0 for row in results),
    }


def evaluate(rows, relevant_ids, index, query_field):
    results = []
    requested = 0
    for row, relevant_id in zip(rows, relevant_ids):
        if row.get('split') not in {'dev', 'test'}:
            continue
        requested += 1
        query = row['source_example'].get(query_field, '').strip()
        if not query:
            continue
        ranked = index.rank(query, top_k=len(index.documents))
        rank = next(position for position, item in enumerate(ranked, 1)
                    if item['document_id'] == relevant_id)
        relevant_score = ranked[rank - 1]['score']
        results.append({
            'record_id': row.get('record_id'),
            'split': row['split'],
            'rank': rank,
            'relevant_score': relevant_score,
            'top_10': ranked[:10],
        })
    return {
        'query_coverage': {
            'requested': requested,
            'available': len(results),
            'missing': requested - len(results),
        },
        'overall': metric_summary(results),
        'dev': metric_summary([row for row in results if row['split'] == 'dev']),
        'test': metric_summary([row for row in results if row['split'] == 'test']),
    }, results


def run(input_path=INPUT, output_dir=OUTPUT):
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    documents, relevant_ids = build_documents(rows)
    word_index = BM25Index(documents, word_tokens)
    character_index = BM25Index(documents, character_ngrams)
    configurations = {
        'garhwali_word_bm25': (word_index, 'question'),
        'garhwali_character_bm25': (character_index, 'question'),
        'oracle_english_word_bm25': (word_index, 'oracle_question'),
    }
    baselines = {}
    predictions = {}
    test_pilot_ids = {
        row.get('record_id')
        for row in sorted(
            (row for row in rows if row.get('split') == 'test'),
            key=lambda row: row.get('record_id', ''),
        )[:TEST_PILOT_RECORDS]
    }
    for name, (index, query_field) in configurations.items():
        metrics, results = evaluate(rows, relevant_ids, index, query_field)
        metrics['test_pilot'] = metric_summary([
            row for row in results if row['record_id'] in test_pilot_ids
        ])
        baselines[name] = metrics
        for result in results:
            predictions.setdefault(result['record_id'], {
                'record_id': result['record_id'],
                'split': result['split'],
            })[name] = {
                'rank': result['rank'],
                'relevant_score': result['relevant_score'],
                'top_10': result['top_10'],
            }
    evaluated = [row for row in rows if row.get('split') in {'dev', 'test'}]
    report = {
        'run_id': 'garhwali-xorqa-retrieval-baselines-v0.1',
        'benchmark': 'IndicGenBench XORQA Garhwali',
        'corpus_documents': len(documents),
        'source_rows': len(rows),
        'evaluation_queries': len(evaluated),
        'test_pilot_records': len(test_pilot_ids),
        'splits': Counter(row['split'] for row in evaluated),
        'answer_text_present_queries': sum(
            any(normalize(answer.get('text', '')) in normalize(row['source_example']['context'])
                for answer in row['source_example'].get('answers', []))
            for row in evaluated
        ),
        'retrieval_scope': 'all_unique_xorqa_contexts',
        'training_use': 'none; train-labelled queries are indexed as passages but not evaluated',
        'baselines': baselines,
        'metric_note': 'Recall and reciprocal rank treat the row-associated deduplicated context as relevant.',
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                for row in predictions.values()),
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
