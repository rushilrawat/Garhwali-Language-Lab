#!/usr/bin/env python3
"""Run dependency-free passage-retrieval baselines on Garhwali XORQA."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from evaluation_run_manifest import write_run_artifacts


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/retrieval'
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
    source_ids = defaultdict(set)
    for row_index, row in enumerate(rows):
        context = row['source_example']['context']
        document_id = context_id(context)
        contexts.setdefault(document_id, context)
        relevant_ids.append(document_id)
        source_ids[document_id].add(row.get('record_id') or f'source_row:{row_index:08d}')
    documents = [
        {'document_id': document_id, 'text': contexts[document_id]}
        for document_id in sorted(contexts)
    ]
    return documents, relevant_ids, {
        document_id: sorted(record_ids)
        for document_id, record_ids in sorted(source_ids.items())
    }


def provenance(input_path, documents, source_ids, evaluated_rows):
    canonical_corpus = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in documents
    ).encode('utf-8')
    duplicate_groups = {
        document_id: record_ids
        for document_id, record_ids in source_ids.items()
        if len(record_ids) > 1
    }
    return {
        'input_manifest_sha256': hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
        'passage_corpus_sha256': hashlib.sha256(canonical_corpus).hexdigest(),
        'evaluated_record_ids': sorted(
            row.get('record_id') or f'evaluation_row:{index:08d}'
            for index, row in enumerate(evaluated_rows)
        ),
        'passage_source_record_ids': source_ids,
        'duplicate_passage_groups': duplicate_groups,
    }


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
    ranks = [row['rank'] for row in results if row['rank'] is not None]
    query_count = len(results)
    return {
        'queries': query_count,
        'retrieved_queries': len(ranks),
        'not_retrieved_queries': query_count - len(ranks),
        'recall_at_1': round(sum(rank <= 1 for rank in ranks) / max(1, query_count), 8),
        'recall_at_5': round(sum(rank <= 5 for rank in ranks) / max(1, query_count), 8),
        'recall_at_10': round(sum(rank <= 10 for rank in ranks) / max(1, query_count), 8),
        'mrr_at_10': round(
            sum(1 / rank for rank in ranks if rank <= 10) / max(1, query_count),
            8,
        ),
        'mean_rank': round(sum(ranks) / len(ranks), 6) if ranks else None,
        'median_rank': round(statistics.median(ranks), 6) if ranks else None,
        'zero_relevant_score_queries': sum(row['relevant_score'] == 0 for row in results),
    }


def evaluate(rows, relevant_ids, index, query_field, selection_split='dev'):
    if selection_split != 'dev':
        raise ValueError('retrieval selection supports only dev; test rows are not eligible')
    results = []
    requested = 0
    for row, relevant_id in zip(rows, relevant_ids):
        if row.get('split') != selection_split:
            continue
        requested += 1
        query = row['source_example'].get(query_field, '').strip()
        if not query:
            continue
        ranked = index.rank(query, top_k=len(index.documents))
        relevant = next(
            (
                (position, item)
                for position, item in enumerate(ranked, 1)
                if item['document_id'] == relevant_id and item['score'] > 0
            ),
            None,
        )
        rank = relevant[0] if relevant else None
        relevant_score = relevant[1]['score'] if relevant else 0.0
        results.append({
            'record_id': row.get('record_id'),
            'split': row['split'],
            'rank': rank,
            'relevant_score': relevant_score,
            'top_10': [item for item in ranked if item['score'] > 0][:10],
        })
    return {
        'query_coverage': {
            'requested': requested,
            'available': len(results),
            'missing': requested - len(results),
        },
        'overall': metric_summary(results),
        'dev': metric_summary(results),
        'test': None,
    }, results


def run(input_path=INPUT, output_dir=OUTPUT, selection_split='dev'):
    if selection_split != 'dev':
        raise ValueError('retrieval selection supports only dev; test rows are not eligible')
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    documents, relevant_ids, source_ids = build_documents(rows)
    word_index = BM25Index(documents, word_tokens)
    character_index = BM25Index(documents, character_ngrams)
    configurations = {
        'garhwali_word_bm25': (word_index, 'question'),
        'garhwali_character_bm25': (character_index, 'question'),
        'oracle_english_word_bm25': (word_index, 'oracle_question'),
    }
    baselines = {}
    evaluated_rows = [row for row in rows if row.get('split') == selection_split]
    predictions = {
        str(row.get('record_id') or f'evaluation_row:{index:08d}'): {
            'record_id': str(row.get('record_id') or f'evaluation_row:{index:08d}'),
            'split': row['split'],
        }
        for index, row in enumerate(evaluated_rows)
    }
    for name, (index, query_field) in configurations.items():
        metrics, results = evaluate(
            rows, relevant_ids, index, query_field, selection_split=selection_split
        )
        metrics['test_pilot'] = None
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
    evaluated = evaluated_rows
    report = {
        'run_id': 'garhwali-xorqa-retrieval-baselines-v0.1',
        'benchmark': 'IndicGenBench XORQA Garhwali',
        'corpus_documents': len(documents),
        'source_rows': len(rows),
        'evaluation_queries': len(evaluated),
        'selection_split': selection_split,
        'evaluation_status': 'development_selection_only',
        'test_scored': False,
        'test_pilot_records': 0,
        'splits': Counter(row['split'] for row in evaluated),
        'answer_text_present_queries': sum(
            any(normalize(answer.get('text', '')) in normalize(row['source_example']['context'])
                for answer in row['source_example'].get('answers', []))
            for row in evaluated
        ),
        'retrieval_scope': 'all_unique_xorqa_contexts',
        'training_use': 'none; train-labelled queries are indexed as passages but not evaluated',
        'baselines': baselines,
        'metric_note': (
            'Recall and reciprocal rank use the row-associated deduplicated context as relevant. '
            'A zero-score BM25 positive has null rank and is not retrieved; mean and median rank '
            'summarize retrieved positives only.'
        ),
        **provenance(input_path, documents, source_ids, evaluated),
    }
    selected_record_ids = [
        str(row.get('record_id') or f'evaluation_row:{index:08d}')
        for index, row in enumerate(evaluated_rows)
    ]
    selected_bytes = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in evaluated_rows
    ).encode('utf-8')
    report.update({
        'evaluation_records': len(evaluated_rows),
        'evaluation_split': selection_split,
        'selected_record_ids': selected_record_ids,
        'input_sha256': report['input_manifest_sha256'],
        'selected_rows_sha256': hashlib.sha256(selected_bytes).hexdigest(),
    })
    config = {
        'task': 'retrieval',
        'split': selection_split,
        'candidate_corpus_sha256': report['passage_corpus_sha256'],
        'bm25': {
            'k1': 1.5,
            'b': 0.75,
            'word_analyzer': 'unicode_words_casefold_nfc_v1',
            'character_analyzer': 'boundary_padded_3_4_5_grams_v1',
        },
        'retrievers': {
            'garhwali_word_bm25': 'question',
            'garhwali_character_bm25': 'question',
            'oracle_english_word_bm25': 'oracle_question',
        },
    }
    write_run_artifacts(
        output_dir,
        list(predictions.values()),
        report,
        config=config,
        model={'id': 'local-bm25-retrieval', 'revision': 'garhwali-xorqa-bm25-v0.1'},
        runtime={
            'python': platform.python_version(),
            'implementation': platform.python_implementation(),
            'platform': platform.platform(),
        },
        device='cpu',
        code_paths=(__file__, Path(__file__).with_name('evaluation_run_manifest.py')),
        git_root=ROOT,
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--selection-split', choices=('dev',), default='dev')
    args = parser.parse_args()
    print(json.dumps(
        run(args.input, args.output, selection_split=args.selection_split),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
