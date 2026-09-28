import importlib
import unittest


try:
    benchmark_metrics = importlib.import_module('benchmark_metrics')
except ModuleNotFoundError as error:
    if error.name != 'benchmark_metrics':
        raise
    benchmark_metrics = None


class BenchmarkMetricTests(unittest.TestCase):
    def metrics(self):
        self.assertIsNotNone(benchmark_metrics, 'benchmark_metrics module is missing')
        return benchmark_metrics

    def test_qa_scores_unicode_normalized_multiple_references_and_empty_output(self):
        metrics = self.metrics()
        result = metrics.score_qa_answers(
            predictions=[' उत्तर! ', ''],
            references=[['उत्तर', 'जवाब'], ['लिखित उत्तर']],
        )

        self.assertEqual(result['metric_id'], 'garhwali-qa-em-token-f1-v1')
        self.assertEqual(result['scored_records'], 2)
        self.assertEqual(result['empty_prediction_records'], 1)
        self.assertEqual(result['exact_match'], 0.5)
        self.assertEqual(result['token_f1'], 0.5)

    def test_normalizer_preserves_digits_and_devanagari_marks(self):
        metrics = self.metrics()

        self.assertEqual(metrics.normalize_metric_text(0), '0')
        self.assertEqual(metrics.normalize_metric_text('कि।'), 'कि')

    def test_qa_rejects_unanswerable_or_missing_reference_lists(self):
        metrics = self.metrics()
        with self.assertRaisesRegex(ValueError, 'non-empty reference'):
            metrics.score_qa_answers(['उत्तर'], [[]])
        with self.assertRaisesRegex(ValueError, 'same number of records'):
            metrics.score_qa_answers(['उत्तर'], [['उत्तर'], ['जवाब']])

    def test_rouge_l_uses_whitespace_tokens_and_scores_empty_hypothesis_as_zero(self):
        metrics = self.metrics()
        result = metrics.score_rouge_l(
            predictions=['गढ़वाली भाषा', ''],
            references=[['गढ़वाली भाषा का पाठ'], ['अर्को पाठ']],
        )

        self.assertEqual(result['metric_id'], 'garhwali-rouge-l-f1-v1')
        self.assertEqual(result['scored_records'], 2)
        self.assertEqual(result['empty_prediction_records'], 1)
        self.assertAlmostEqual(result['rouge_l_f1'], 1 / 3)

    def test_metric_inputs_require_one_nonempty_reference_per_record(self):
        metrics = self.metrics()
        with self.assertRaisesRegex(ValueError, 'non-empty reference'):
            metrics.score_rouge_l([''], [['']])


if __name__ == '__main__':
    unittest.main()
