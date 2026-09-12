import unittest

import run_indicbert_lora_adaptation as m


class IndicBertLoraAdaptationTests(unittest.TestCase):
    def test_summary_advances_only_when_mean_loss_improves(self):
        baseline = {'cross_entropy': 6.0, 'accuracy': 0.2}
        improved = [
            {'seed': 17, 'validation': {'cross_entropy': 5.8, 'accuracy': 0.21}},
            {'seed': 29, 'validation': {'cross_entropy': 5.9, 'accuracy': 0.20}},
        ]
        result = m.summarize_lora(baseline, improved)
        self.assertEqual(result['mean_cross_entropy'], 5.85)
        self.assertEqual(result['improved_seed_count'], 2)
        self.assertEqual(result['promotion_status'], 'advance_to_longer_continued_pretraining')

        worse = [{'seed': 17, 'validation': {'cross_entropy': 6.1, 'accuracy': 0.2}}]
        self.assertEqual(m.summarize_lora(baseline, worse)['promotion_status'], 'not_advanced')

    def test_target_modules_are_narrow_and_explicit(self):
        self.assertEqual(m.LORA_TARGET_MODULES, ('query', 'value'))


if __name__ == '__main__':
    unittest.main()
