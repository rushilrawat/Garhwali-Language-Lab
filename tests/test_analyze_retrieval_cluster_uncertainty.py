import importlib
import json
import tempfile
import unittest
from pathlib import Path


try:
    analysis = importlib.import_module('analyze_retrieval_cluster_uncertainty')
except ModuleNotFoundError as error:
    if error.name != 'analyze_retrieval_cluster_uncertainty':
        raise
    analysis = None


class RetrievalClusterUncertaintyTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(
            analysis, 'analyze_retrieval_cluster_uncertainty module is missing')
        return analysis

    def test_bootstrap_resamples_complete_page_families_and_is_reproducible(self):
        rows = [
            {'record_id': 'a1', 'source_page_family_sha256': 'page-a', 'rank': 1},
            {'record_id': 'a2', 'source_page_family_sha256': 'page-a', 'rank': 1},
            {'record_id': 'b1', 'source_page_family_sha256': 'page-b', 'rank': None},
        ]

        first = self.module().cluster_bootstrap_metric(
            rows, metric='recall_at_1', replicates=200, seed=17)
        second = self.module().cluster_bootstrap_metric(
            rows, metric='recall_at_1', replicates=200, seed=17)

        self.assertEqual(first, second)
        self.assertEqual(first['point_estimate'], 2 / 3)
        # Sampling two page families with replacement yields only these values;
        # row-level resampling would also create partial-family outcomes.
        self.assertEqual(set(first['bootstrap_values']), {0.0, 2 / 3, 1.0})

    def test_run_checks_lineage_and_writes_text_free_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            benchmark = root / 'benchmark.jsonl'
            predictions = root / 'predictions.jsonl'
            parent_report = root / 'retrieval-report.json'
            output_dir = root / 'output'
            benchmark_rows = [
                {
                    'record_id': 'q1', 'split': 'dev',
                    'source_example': {'title': 'title:Page A_parentSection:One'},
                    'question': 'must not appear in report',
                },
                {
                    'record_id': 'q2', 'split': 'dev',
                    'source_example': {'title': 'title:Page A_parentSection:Two'},
                    'question': 'must not appear in report',
                },
                {
                    'record_id': 'q3', 'split': 'dev',
                    'source_example': {'title': 'title:Page B_parentSection:One'},
                    'question': 'must not appear in report',
                },
                {
                    'record_id': 'q4', 'split': 'test',
                    'source_example': {'title': 'title:Held out_parentSection:One'},
                    'question': 'test question must not be scored',
                },
            ]
            benchmark.write_text(
                ''.join(json.dumps(row) + '\n' for row in benchmark_rows),
                encoding='utf-8')
            prediction_rows = [
                {
                    'record_id': record_id, 'split': 'dev',
                    'garhwali_word_bm25': {'rank': word_rank},
                    'garhwali_character_bm25': {'rank': char_rank},
                    'oracle_english_word_bm25': {'rank': oracle_rank},
                }
                for record_id, word_rank, char_rank, oracle_rank in [
                    ('q1', 1, 2, 1), ('q2', None, 1, 10), ('q3', 20, None, None)]
            ]
            predictions.write_text(
                ''.join(json.dumps(row) + '\n' for row in prediction_rows),
                encoding='utf-8')
            parent_report.write_text(json.dumps({
                'input_manifest_sha256': self.module().sha256_file(benchmark),
                'passage_corpus_sha256': 'c' * 64,
                'corpus_documents': 9,
                'evaluation_queries': 3,
                'test_scored': False,
                'baselines': {
                    'garhwali_word_bm25': {'dev': {
                        'recall_at_1': 1 / 3, 'recall_at_5': 1 / 3,
                        'recall_at_10': 1 / 3, 'mrr_at_10': 1 / 3,
                    }},
                    'garhwali_character_bm25': {'dev': {
                        'recall_at_1': 1 / 3, 'recall_at_5': 2 / 3,
                        'recall_at_10': 2 / 3, 'mrr_at_10': 0.5,
                    }},
                    'oracle_english_word_bm25': {'dev': {
                        'recall_at_1': 1 / 3, 'recall_at_5': 1 / 3,
                        'recall_at_10': 2 / 3, 'mrr_at_10': 1.1 / 3,
                    }},
                },
            }), encoding='utf-8')

            report = self.module().run(
                benchmark_path=benchmark,
                predictions_path=predictions,
                retrieval_report_path=parent_report,
                output_dir=output_dir,
                replicates=50,
                seed=5,
            )

            saved = json.loads((output_dir / 'report.json').read_text(encoding='utf-8'))
            self.assertEqual(saved, report)
            self.assertEqual(report['evaluation_record_count'], 3)
            self.assertEqual(report['source_page_family_count'], 2)
            self.assertEqual(report['multiquery_family_count'], 1)
            self.assertEqual(report['paired_deltas']['recall_at_1']['point_estimate'], 0.0)
            self.assertNotIn('must not appear', (output_dir / 'report.json').read_text())
            self.assertNotIn('Page A', (output_dir / 'report.md').read_text())
            self.assertEqual(report['lineage']['test_rows_scored'], 0)

    def test_rejects_prediction_id_mismatch_and_unparsed_source_page(self):
        rows = [
            {
                'record_id': 'q1', 'split': 'dev',
                'source_example': {'title': 'title:Page A_parentSection:One'},
            },
        ]
        with self.assertRaisesRegex(ValueError, 'prediction IDs must exactly match'):
            self.module().validate_inputs(
                rows,
                [{'record_id': 'other', 'split': 'dev'}],
                {'evaluation_queries': 1},
            )
        with self.assertRaisesRegex(ValueError, 'source-page title'):
            self.module().validate_inputs(
                [{'record_id': 'q1', 'split': 'dev', 'source_example': {}}],
                [{'record_id': 'q1', 'split': 'dev'}],
                {'evaluation_queries': 1},
            )

    def test_rejects_missing_rank_in_saved_prediction(self):
        benchmark_row = {
            'record_id': 'q1', 'split': 'dev',
            'source_example': {'title': 'title:Page A_parentSection:One'},
        }
        prediction_row = {
            'record_id': 'q1', 'split': 'dev',
            'garhwali_word_bm25': {},
            'garhwali_character_bm25': {'rank': None},
            'oracle_english_word_bm25': {'rank': 1},
        }
        with self.assertRaisesRegex(ValueError, 'missing rank'):
            self.module().validate_inputs(
                [benchmark_row], [prediction_row], {'evaluation_queries': 1})


if __name__ == '__main__':
    unittest.main()
