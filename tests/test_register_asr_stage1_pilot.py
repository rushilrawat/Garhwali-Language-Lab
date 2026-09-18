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

    def test_paired_outcomes_count_better_worse_ties_and_exact_predictions(self):
        baseline = [
            {
                'audio_sha256': 'a', 'reference': 'एक', 'hypothesis': 'एक',
                'wer': 0.0, 'cer': 0.0,
            },
            {
                'audio_sha256': 'b', 'reference': 'दुई', 'hypothesis': 'एक',
                'wer': 1.0, 'cer': 1.0,
            },
            {
                'audio_sha256': 'c', 'reference': 'तीन', 'hypothesis': 'तीन',
                'wer': 0.5, 'cer': 0.5,
            },
        ]
        pilot = [
            {
                'audio_sha256': 'a', 'reference': 'एक', 'prediction': 'एक',
                'wer': 0.0, 'cer': 0.0,
            },
            {
                'audio_sha256': 'b', 'reference': 'दुई', 'prediction': 'दुई',
                'wer': 0.0, 'cer': 0.0,
            },
            {
                'audio_sha256': 'c', 'reference': 'तीन', 'prediction': 'चार',
                'wer': 1.0, 'cer': 1.0,
            },
        ]
        result = m.paired_outcomes(baseline, pilot, {'a', 'b', 'c'})
        self.assertEqual(result['wer'], {'better': 1, 'worse': 1, 'tie': 1})
        self.assertEqual(result['cer'], {'better': 1, 'worse': 1, 'tie': 1})
        self.assertEqual(result['exact_same_predictions'], 1)

    def test_paired_outcomes_require_matching_rows_and_references(self):
        baseline = [{
            'audio_sha256': 'a', 'reference': 'एक', 'hypothesis': 'एक',
            'wer': 0.0, 'cer': 0.0,
        }]
        with self.assertRaisesRegex(ValueError, 'paired'):
            m.paired_outcomes(baseline, [], {'a'})


if __name__ == '__main__':
    unittest.main()
