import math
import unittest

import run_indicbert_adaptation as m


class IndicBertAdaptationTests(unittest.TestCase):
    def test_defaults_use_recommended_training_and_validation_views(self):
        self.assertEqual(m.TRAIN.parts[-3:], ('splits', 'text_recommended', 'train.jsonl'))
        self.assertEqual(m.VALIDATION.parts[-3:], ('splits', 'text_recommended', 'validation.jsonl'))
        self.assertIn('recommended', m.OUTPUT.name)

    def test_training_selection_is_deterministic(self):
        rows = [{'segment_sha256': str(index), 'text': str(index)} for index in range(20)]
        first = m.select_rows(rows, 5, 17)
        second = m.select_rows(rows, 5, 17)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 5)
        self.assertNotEqual(first, m.select_rows(rows, 5, 29))

    def test_summary_reports_mean_delta_and_seed_variance(self):
        baseline = {'cross_entropy': 5.0, 'accuracy': 0.1}
        runs = [
            {'seed': 17, 'validation': {'cross_entropy': 4.0, 'accuracy': 0.2}},
            {'seed': 29, 'validation': {'cross_entropy': 4.5, 'accuracy': 0.15}},
        ]
        summary = m.summarize_runs(baseline, runs)
        self.assertEqual(summary['mean_cross_entropy'], 4.25)
        self.assertEqual(summary['mean_cross_entropy_delta'], -0.75)
        self.assertTrue(math.isclose(summary['std_cross_entropy'], 0.25))
        self.assertEqual(summary['promotion_status'], 'advance_to_encoder_adaptation')

    def test_no_improvement_is_not_advanced(self):
        baseline = {'cross_entropy': 5.0, 'accuracy': 0.1}
        runs = [{'seed': 17, 'validation': {'cross_entropy': 5.2, 'accuracy': 0.1}}]
        self.assertEqual(m.summarize_runs(baseline, runs)['promotion_status'], 'not_advanced')


if __name__ == '__main__':
    unittest.main()
