import unittest

import run_indicbert_lora_adaptation as m


class IndicBertLoraAdaptationTests(unittest.TestCase):
    def test_defaults_use_recommended_data_and_distinct_output(self):
        self.assertEqual(m.TRAIN, m.head.TRAIN)
        self.assertEqual(m.VALIDATION, m.head.VALIDATION)
        self.assertIn('recommended', m.OUTPUT.name)

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

    def test_auto_device_prefers_cuda_then_mps(self):
        class Available:
            @staticmethod
            def is_available():
                return True

        class Unavailable:
            @staticmethod
            def is_available():
                return False

        cuda = type('Torch', (), {
            'cuda': Available(), 'backends': type('Backends', (), {'mps': Available()})(),
        })()
        mps = type('Torch', (), {
            'cuda': Unavailable(), 'backends': type('Backends', (), {'mps': Available()})(),
        })()
        self.assertEqual(m.resolve_device('auto', cuda), 'cuda')
        self.assertEqual(m.resolve_device('auto', mps), 'mps')
        self.assertEqual(m.resolve_device('cpu', cuda), 'cpu')


if __name__ == '__main__':
    unittest.main()
