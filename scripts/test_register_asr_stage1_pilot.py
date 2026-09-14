import unittest

import register_asr_stage1_pilot as m


class RegisterAsrStage1PilotTests(unittest.TestCase):
    def test_comparison_rejects_pilot_unless_both_error_rates_improve(self):
        baseline = {
            'records': 2,
            'word_errors': 10,
            'reference_words': 20,
            'character_errors': 20,
            'reference_characters': 100,
            'wer': 0.5,
            'cer': 0.2,
        }
        worse_cer = {
            **baseline,
            'word_errors': 9,
            'character_errors': 21,
            'wer': 0.45,
            'cer': 0.21,
        }
        result = m.compare_metrics(baseline, worse_cer)
        self.assertEqual(result['decision'], 'rejected')
        self.assertEqual(result['word_error_delta'], -1)
        self.assertEqual(result['character_error_delta'], 1)

        better = {
            **baseline,
            'word_errors': 9,
            'character_errors': 19,
            'wer': 0.45,
            'cer': 0.19,
        }
        self.assertEqual(m.compare_metrics(baseline, better)['decision'], 'promoted')

    def test_comparison_requires_identical_validation_denominators(self):
        baseline = {
            'records': 2,
            'word_errors': 10,
            'reference_words': 20,
            'character_errors': 20,
            'reference_characters': 100,
            'wer': 0.5,
            'cer': 0.2,
        }
        pilot = {**baseline, 'records': 1}
        with self.assertRaisesRegex(ValueError, 'same validation set'):
            m.compare_metrics(baseline, pilot)


if __name__ == '__main__':
    unittest.main()
