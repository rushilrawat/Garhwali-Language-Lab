import hashlib
import importlib
import json
import re
import tempfile
import unicodedata
import unittest
from pathlib import Path


try:
    analysis = importlib.import_module('analyze_retrieval_misses')
except ModuleNotFoundError as error:
    if error.name != 'analyze_retrieval_misses':
        raise
    analysis = None


def normalize(value):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(value)).casefold()).strip()


def context_id(value):
    return hashlib.sha256(normalize(value).encode('utf-8')).hexdigest()


class RetrievalMissAnalysisTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(analysis, 'analyze_retrieval_misses module is missing')
        return analysis

    def fixture(self, root):
        benchmark_rows = [
            {
                'record_id': 'xorqa:dev:1', 'split': 'dev',
                'source_example': {
                    'title': 'title:Shared Page_parentSection:First',
                    'context': 'alpha evidence passage',
                    'question': 'alpha', 'oracle_question': 'alpha',
                },
            },
            {
                'record_id': 'xorqa:dev:2', 'split': 'dev',
                'source_example': {
                    'title': 'title:Shared Page_parentSection:Second',
                    'context': 'gamma special phrase',
                    'question': 'alpha', 'oracle_question': 'gamma',
                },
            },
            {
                'record_id': 'xorqa:test:3', 'split': 'test',
                'source_example': {
                    'title': 'title:Other Page_parentSection:First',
                    'context': 'beta heldout context',
                    'question': 'beta', 'oracle_question': 'beta',
                },
            },
            {
                'record_id': 'xorqa:train:4', 'split': 'train',
                'source_example': {
                    'title': 'title:Shared Page_parentSection:First',
                    'context': 'alpha evidence passage',
                    'question': 'alpha', 'oracle_question': 'alpha',
                },
            },
            {
                'record_id': 'xorqa:train:5', 'split': 'train',
                'source_example': {
                    'title': 'title:Other Page_parentSection:First',
                    'context': 'beta heldout context',
                    'question': 'beta', 'oracle_question': 'beta',
                },
            },
        ]
        benchmark = root / 'benchmark.jsonl'
        benchmark.write_text(
            ''.join(json.dumps(row) + '\n' for row in benchmark_rows), encoding='utf-8')
        docs = [
            {'document_id': context_id(row['source_example']['context']),
             'text': row['source_example']['context']}
            for row in benchmark_rows
        ]
        passage_sources_by_context = {}
        for row in benchmark_rows:
            passage_sources_by_context.setdefault(
                context_id(row['source_example']['context']), []).append(row['record_id'])
        passage_sources = {
            document_id: sorted(record_ids)
            for document_id, record_ids in sorted(passage_sources_by_context.items())
        }
        corpus_payload = ''.join(
            json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
            for row in sorted({row['document_id']: row for row in docs}.values(),
                              key=lambda row: row['document_id'])
        ).encode('utf-8')
        corpus_hash = hashlib.sha256(corpus_payload).hexdigest()
        predictions_rows = [
            {
                'record_id': 'xorqa:dev:1', 'split': 'dev',
                'garhwali_word_bm25': {
                    'rank': 1, 'relevant_score': 1.0,
                    'top_10': [{'document_id': context_id('alpha evidence passage'), 'score': 1.0}],
                },
                'garhwali_character_bm25': {
                    'rank': 2, 'relevant_score': 0.8,
                    'top_10': [
                        {'document_id': context_id('gamma special phrase'), 'score': 1.0},
                        {'document_id': context_id('alpha evidence passage'), 'score': 0.8},
                    ],
                },
                'oracle_english_word_bm25': {
                    'rank': 1, 'relevant_score': 1.0,
                    'top_10': [{'document_id': context_id('alpha evidence passage'), 'score': 1.0}],
                },
            },
            {
                'record_id': 'xorqa:dev:2', 'split': 'dev',
                'garhwali_word_bm25': {
                    'rank': None, 'relevant_score': 0.0,
                    'top_10': [{'document_id': context_id('alpha evidence passage'), 'score': 1.0}],
                },
                'garhwali_character_bm25': {
                    'rank': None, 'relevant_score': 0.0,
                    'top_10': [{'document_id': context_id('alpha evidence passage'), 'score': 1.0}],
                },
                'oracle_english_word_bm25': {
                    'rank': 1, 'relevant_score': 1.0,
                    'top_10': [{'document_id': context_id('gamma special phrase'), 'score': 1.0}],
                },
            },
        ]
        predictions = root / 'predictions.jsonl'
        predictions.write_text(
            ''.join(json.dumps(row) + '\n' for row in predictions_rows), encoding='utf-8')
        parent_report = root / 'retrieval-report.json'
        parent_report.write_text(json.dumps({
            'input_manifest_sha256': hashlib.sha256(benchmark.read_bytes()).hexdigest(),
            'passage_corpus_sha256': corpus_hash,
            'passage_source_record_ids': passage_sources,
            'corpus_documents': 3,
            'evaluation_queries': 2,
            'retrieval_scope': 'all_unique_xorqa_contexts',
            'evaluated_record_ids': ['xorqa:dev:1', 'xorqa:dev:2'],
            'test_scored': False,
            'baselines': {
                'garhwali_word_bm25': {'dev': {
                    'recall_at_1': 0.5, 'recall_at_5': 0.5,
                    'recall_at_10': 0.5, 'mrr_at_10': 0.5,
                }},
                'garhwali_character_bm25': {'dev': {
                    'recall_at_1': 0.0, 'recall_at_5': 0.5,
                    'recall_at_10': 0.5, 'mrr_at_10': 0.25,
                }},
                'oracle_english_word_bm25': {'dev': {
                    'recall_at_1': 1.0, 'recall_at_5': 1.0,
                    'recall_at_10': 1.0, 'mrr_at_10': 1.0,
                }},
            },
        }), encoding='utf-8')
        return benchmark, predictions, parent_report

    def test_run_reports_passage_coverage_and_miss_types_without_source_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark, predictions, parent_report = self.fixture(root)
            report = self.module().run(
                benchmark_path=benchmark,
                predictions_path=predictions,
                retrieval_report_path=parent_report,
                output_dir=root / 'output',
            )

            self.assertEqual(report['evaluation_record_count'], 2)
            self.assertEqual(report['candidate_coverage']['available_gold_records'], 2)
            self.assertEqual(report['candidate_coverage']['missing_gold_records'], 0)
            self.assertEqual(
                report['candidate_coverage']['candidate_corpus_duplicate_context_groups'], 2)
            self.assertEqual(
                report['candidate_coverage']['unique_gold_contexts_with_duplicate_source_rows'], 1)
            self.assertEqual(
                report['candidate_coverage']['unique_gold_contexts_with_sources_in_multiple_splits'], 1)
            self.assertEqual(report['retrievers']['garhwali_word_bm25']['status_counts'], {
                'rank_1': 1, 'rank_2_5': 0, 'rank_6_10': 0,
                'rank_11_plus': 0, 'zero_score': 1,
            })
            second_query = next(
                row for row in report['per_query'] if row['record_id'] == 'xorqa:dev:2')
            self.assertTrue(
                second_query['retrievers']['garhwali_word_bm25']
                ['same_page_non_gold_passage_in_top_10'])
            saved = (root / 'output/report.json').read_text(encoding='utf-8')
            self.assertNotIn('alpha evidence passage', saved)
            self.assertNotIn('gamma special phrase', saved)
            self.assertEqual(report['lineage']['test_rows_scored'], 0)

    def test_rejects_candidate_corpus_drift_and_test_predictions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark, predictions, parent_report = self.fixture(root)
            bad_report = json.loads(parent_report.read_text(encoding='utf-8'))
            bad_report['passage_corpus_sha256'] = 'f' * 64
            parent_report.write_text(json.dumps(bad_report), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'candidate corpus hash'):
                self.module().run(
                    benchmark_path=benchmark,
                    predictions_path=predictions,
                    retrieval_report_path=parent_report,
                    output_dir=root / 'bad-corpus',
                )

            _, predictions, parent_report = self.fixture(root)
            rows = [json.loads(line) for line in predictions.read_text().splitlines()]
            rows.append({'record_id': 'xorqa:test:3', 'split': 'test'})
            predictions.write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'only dev predictions'):
                self.module().run(
                    benchmark_path=benchmark,
                    predictions_path=predictions,
                    retrieval_report_path=parent_report,
                    output_dir=root / 'bad-split',
                )

    def test_rejects_rank_list_and_parent_metric_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark, predictions, parent_report = self.fixture(root)
            rows = [json.loads(line) for line in predictions.read_text().splitlines()]
            rows[0]['garhwali_word_bm25']['rank'] = 2
            predictions.write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'rank does not point to gold passage'):
                self.module().run(
                    benchmark_path=benchmark,
                    predictions_path=predictions,
                    retrieval_report_path=parent_report,
                    output_dir=root / 'bad-rank',
                )

            benchmark, predictions, parent_report = self.fixture(root)
            report = json.loads(parent_report.read_text(encoding='utf-8'))
            report['baselines']['garhwali_word_bm25']['dev']['recall_at_10'] = 0.99
            parent_report.write_text(json.dumps(report), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'does not reproduce saved dev report'):
                self.module().run(
                    benchmark_path=benchmark,
                    predictions_path=predictions,
                    retrieval_report_path=parent_report,
                    output_dir=root / 'bad-metric',
                )


if __name__ == '__main__':
    unittest.main()
