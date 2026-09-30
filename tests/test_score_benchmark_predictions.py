import importlib
import json
import tempfile
import unittest
from pathlib import Path


try:
    scorer = importlib.import_module('score_benchmark_predictions')
except ModuleNotFoundError as error:
    if error.name != 'score_benchmark_predictions':
        raise
    scorer = None


class ScoreBenchmarkPredictionTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(scorer, 'score_benchmark_predictions module is missing')
        return scorer

    def test_crosssum_uses_target_language_summary_on_dev_only(self):
        report, predictions = self.module().evaluate_rows(
            task='summarization',
            benchmark_rows=[
                {'record_id': 'dev-1', 'split': 'dev', 'source_example': {'summary': 'गढ़वाली सार'}},
                {'record_id': 'test-1', 'split': 'test', 'source_example': {'summary': 'अलग सार'}},
            ],
            prediction_rows=[{'record_id': 'dev-1', 'hypothesis': 'गढ़वाली सार'}],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['task'], 'summarization')
        self.assertEqual(report['evaluation_split'], 'dev')
        self.assertEqual(report['evaluation_records'], 1)
        self.assertEqual(report['metrics']['rouge_l_f1'], 1.0)
        self.assertEqual([row['record_id'] for row in predictions], ['dev-1'])

    def test_xorqa_scores_target_language_answers_not_english_answers(self):
        report, _ = self.module().evaluate_rows(
            task='question_answering',
            benchmark_rows=[{
                'record_id': 'dev-1',
                'split': 'dev',
                'source_example': {
                    'answers': [{'text': 'English answer'}],
                    'translated_answers': [{'text': 'गढ़वाली उत्तर'}],
                },
            }],
            prediction_rows=[{'record_id': 'dev-1', 'hypothesis': 'गढ़वाली उत्तर'}],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['metrics']['exact_match'], 1.0)
        self.assertEqual(report['metrics']['token_f1'], 1.0)

    def test_flores_scores_garhwali_to_english_with_versioned_custom_metrics(self):
        report, _ = self.module().evaluate_rows(
            task='translation',
            benchmark_rows=[{
                'record_id': 'dev-1', 'split': 'dev',
                'source_example': {
                    'translation_direction': 'xxen',
                    'source': 'गढ़वाली वाक्य',
                    'target': 'English reference.',
                },
            }],
            prediction_rows=[{'record_id': 'dev-1', 'hypothesis': 'English reference.'}],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['task'], 'translation')
        self.assertEqual(report['evaluation_split'], 'dev')
        self.assertEqual(report['metrics']['exact_match'], 1.0)
        self.assertEqual(report['metrics']['corpus_bleu_smoothed'], 1.0)
        self.assertEqual(report['metrics']['corpus_chrf2'], 1.0)
        self.assertEqual(
            report['metrics']['metric_ids'],
            ['garhwali-custom-add1-bleu-v1', 'garhwali-custom-chrf2-v1'],
        )

    def test_asr_uses_corpus_wer_cer_and_explicitly_excludes_empty_references(self):
        report, predictions = self.module().evaluate_rows(
            task='asr',
            benchmark_rows=[
                {'record_id': 'dev-1', 'split': 'dev', 'text': {'text_scoring': 'अ ब'}},
                {'record_id': 'dev-2', 'split': 'dev', 'text': {'text_scoring': ''}},
            ],
            prediction_rows=[
                {'record_id': 'dev-1', 'hypothesis': 'अ'},
                {'record_id': 'dev-2', 'hypothesis': 'noise'},
            ],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['metrics']['wer'], 0.5)
        self.assertEqual(report['metrics']['cer'], 0.5)
        self.assertEqual(report['metrics']['scored_records'], 1)
        self.assertEqual(report['coverage']['excluded_missing_reference_records'], 1)
        self.assertEqual(report['excluded_record_ids'], ['dev-2'])
        self.assertEqual(
            report['metrics']['metric_ids'],
            ['garhwali-asr-corpus-wer-v1', 'garhwali-asr-corpus-cer-v1'],
        )
        self.assertFalse(predictions[1]['metric_included'])

    def test_asr_run_writes_aggregate_metric_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark = root / 'benchmark.jsonl'
            predictions = root / 'predictions.jsonl'
            benchmark.write_text(json.dumps({
                'record_id': 'dev-1', 'split': 'dev',
                'text': {'text_scoring': 'गढ़वाली'},
            }, ensure_ascii=False) + '\n', encoding='utf-8')
            predictions.write_text(json.dumps({
                'record_id': 'dev-1', 'hypothesis': 'गढ़वाली',
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            report = self.module().run(
                task='asr', benchmark_path=benchmark,
                predictions_path=predictions, output_dir=root / 'run',
                prediction_field='hypothesis', model={'id': 'test-asr', 'revision': 'abc'},
                git_root=None,
            )

            manifest = json.loads((root / 'run/run_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(report['metrics']['wer'], 0.0)
            self.assertEqual(
                manifest['config']['metric_ids'],
                ['garhwali-asr-corpus-wer-v1', 'garhwali-asr-corpus-cer-v1'],
            )
            self.assertIn('asr_metrics.py', manifest['code']['files_sha256'])

    def test_generation_scores_validation_rows_with_acceptable_variants(self):
        first_hash = 'a' * 64
        missing_reference_hash = 'b' * 64
        report, predictions = self.module().evaluate_rows(
            task='generation',
            benchmark_rows=[
                {
                    'instruction_sha256': first_hash,
                    'split': 'validation',
                    'task': 'english_to_garhwali_lexicon',
                    'instruction': 'Translate this term',
                    'response': 'उत्तर',
                    'acceptable_responses': ['उत्तर', 'जवाब'],
                },
                {
                    'instruction_sha256': missing_reference_hash,
                    'split': 'validation',
                    'task': 'garhwali_to_english_lexicon',
                    'instruction': 'Translate another term',
                    'response': '',
                    'acceptable_responses': [],
                },
            ],
            prediction_rows=[
                {'record_id': f'instruction:{first_hash}', 'hypothesis': 'जवाब'},
                {'record_id': f'instruction:{missing_reference_hash}', 'hypothesis': 'noise'},
            ],
            prediction_field='hypothesis',
            split='validation',
        )

        self.assertEqual(report['evaluation_split'], 'validation')
        self.assertEqual(report['claim_limit'], 'development_metrics_not_final_accuracy')
        self.assertEqual(report['selected_record_ids'], [
            f'instruction:{first_hash}', f'instruction:{missing_reference_hash}',
        ])
        self.assertEqual(report['coverage']['metric_scored_records'], 1)
        self.assertEqual(report['excluded_record_ids'], [f'instruction:{missing_reference_hash}'])
        self.assertEqual(report['source_split_counts'], {})
        self.assertEqual(report['metrics']['overall']['exact_match'], 1.0)
        self.assertEqual(report['metrics']['overall']['corpus_chrf2'], 1.0)
        self.assertFalse(predictions[1]['metric_included'])
        self.assertEqual(
            predictions[0]['generation_diagnostics']['acceptable_responses'],
            ['उत्तर', 'जवाब'],
        )

    def test_generation_run_hashes_its_generation_metric_implementation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark = root / 'validation.jsonl'
            predictions = root / 'predictions.jsonl'
            digest = 'c' * 64
            benchmark.write_text(json.dumps({
                'instruction_sha256': digest,
                'split': 'validation',
                'task': 'english_to_garhwali_lexicon',
                'instruction': 'Translate this term',
                'response': 'उत्तर',
                'acceptable_responses': ['उत्तर'],
            }, ensure_ascii=False) + '\n', encoding='utf-8')
            predictions.write_text(json.dumps({
                'record_id': f'instruction:{digest}', 'hypothesis': 'उत्तर',
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            report = self.module().run(
                task='generation', benchmark_path=benchmark,
                predictions_path=predictions, output_dir=root / 'run',
                prediction_field='hypothesis', model={'id': 'test-generation', 'revision': 'abc'},
                split='validation', git_root=None,
            )

            manifest = json.loads((root / 'run/run_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(report['metrics']['overall']['exact_match'], 1.0)
            self.assertEqual(
                manifest['config']['metric_ids'],
                ['garhwali-generation-em-multi-ref-v1', 'garhwali-generation-chrf2-multi-ref-v1'],
            )
            self.assertIn('run_mt5_instruction_tuning.py', manifest['code']['files_sha256'])

    def test_crosssum_includes_rouge_and_existing_custom_chrf(self):
        report, _ = self.module().evaluate_rows(
            task='summarization',
            benchmark_rows=[{
                'record_id': 'dev-1', 'split': 'dev',
                'source_example': {'summary': 'गढ़वाली सार'},
            }],
            prediction_rows=[{'record_id': 'dev-1', 'hypothesis': 'गढ़वाली सार'}],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['metrics']['rouge_l_f1'], 1.0)
        self.assertEqual(report['metrics']['corpus_chrf2'], 1.0)
        self.assertIn('garhwali-custom-chrf2-v1', report['metrics']['metric_ids'])

    def test_xorqa_missing_target_reference_is_explicitly_excluded_but_retained(self):
        report, predictions = self.module().evaluate_rows(
            task='question_answering',
            benchmark_rows=[
                {
                    'record_id': 'dev-1', 'split': 'dev',
                    'source_example': {'translated_answers': [{'text': 'गढ़वाली उत्तर'}]},
                },
                {
                    'record_id': 'dev-2', 'split': 'dev',
                    'source_example': {
                        'answers': [{'text': 'English answer'}],
                        'translated_answers': [{'text': ''}],
                    },
                },
            ],
            prediction_rows=[
                {'record_id': 'dev-1', 'hypothesis': 'गढ़वाली उत्तर'},
                {'record_id': 'dev-2', 'hypothesis': 'उत्तर'},
            ],
            prediction_field='hypothesis',
        )

        self.assertEqual(report['evaluation_records'], 2)
        self.assertEqual(report['metrics']['scored_records'], 1)
        self.assertEqual(report['coverage']['excluded_missing_reference_records'], 1)
        self.assertEqual(report['excluded_record_ids'], ['dev-2'])
        self.assertEqual([row['record_id'] for row in predictions], ['dev-1', 'dev-2'])
        self.assertEqual(predictions[1]['metric_included'], False)

    def test_test_split_requires_historical_test_opt_in(self):
        with self.assertRaisesRegex(ValueError, 'allow-historical-test'):
            self.module().evaluate_rows(
                task='question_answering',
                benchmark_rows=[{
                    'record_id': 'test-1', 'split': 'test',
                    'source_example': {'translated_answers': [{'text': 'उत्तर'}]},
                }],
                prediction_rows=[{'record_id': 'test-1', 'hypothesis': 'उत्तर'}],
                prediction_field='hypothesis',
                split='test',
            )

    def test_predictions_must_match_selected_ids_exactly(self):
        kwargs = {
            'task': 'summarization',
            'benchmark_rows': [{
                'record_id': 'dev-1', 'split': 'dev',
                'source_example': {'summary': 'सार'},
            }],
            'prediction_field': 'hypothesis',
        }
        with self.assertRaisesRegex(ValueError, 'missing prediction IDs'):
            self.module().evaluate_rows(
                **kwargs,
                prediction_rows=[{'record_id': 'other', 'hypothesis': 'सार'}],
            )

    def test_run_writes_shared_hash_linked_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmark = root / 'benchmark.jsonl'
            predictions = root / 'predictions.jsonl'
            output = root / 'run'
            benchmark.write_text(json.dumps({
                'record_id': 'dev-1', 'split': 'dev',
                'source_example': {'summary': 'गढ़वाली सार'},
            }, ensure_ascii=False) + '\n', encoding='utf-8')
            predictions.write_text(json.dumps({
                'record_id': 'dev-1', 'hypothesis': 'गढ़वाली सार',
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            report = self.module().run(
                task='summarization', benchmark_path=benchmark,
                predictions_path=predictions, output_dir=output,
                prediction_field='hypothesis', model={'id': 'test-model', 'revision': 'abc'},
                git_root=None,
            )

            self.assertEqual(report['metrics']['rouge_l_f1'], 1.0)
            manifest = json.loads((output / 'run_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['evaluation_split'], 'dev')
            self.assertEqual(manifest['selected_record_ids'], ['dev-1'])
            self.assertIn('report.json', manifest['outputs'])


if __name__ == '__main__':
    unittest.main()
