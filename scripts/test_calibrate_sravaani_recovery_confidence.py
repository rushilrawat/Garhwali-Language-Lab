import unittest

import calibrate_sravaani_recovery_confidence as m


class SraVaaniRecoveryConfidenceTests(unittest.TestCase):
    def test_character_agreement_is_bounded_and_exact(self):
        self.assertEqual(m.character_agreement('गढ़वाली भाषा', 'गढ़वाली भाषा'), 1.0)
        self.assertEqual(m.character_agreement('', ''), 1.0)
        self.assertGreaterEqual(m.character_agreement('गढ़वाली', 'हिंदी'), 0.0)
        self.assertLessEqual(m.character_agreement('गढ़वाली', 'हिंदी'), 1.0)

    def test_join_calibration_requires_matching_references(self):
        sra = [{'audio_sha256': 'a', 'reference': 'गढ़वाली', 'hypothesis': 'गढ़वाली'}]
        whisper = [{'audio_sha256': 'a', 'reference': 'दूसरा', 'prediction': 'गढ़वाली'}]
        with self.assertRaises(ValueError):
            m.join_calibration(sra, whisper)

    def test_calibration_records_model_errors_and_agreement(self):
        sra = [{'audio_sha256': 'a', 'reference': 'गढ़वाली भाषा',
                'hypothesis': 'गढ़वाली भाषा'}]
        whisper = [{'audio_sha256': 'a', 'reference': 'गढ़वाली भाषा',
                    'prediction': 'गढ़वाली भासा'}]
        row = m.join_calibration(sra, whisper)[0]
        self.assertEqual(row['sra_metrics']['cer'], 0)
        self.assertGreater(row['whisper_metrics']['cer'], 0)
        self.assertGreater(row['character_agreement'], 0)

    def test_recovery_score_is_not_claimed_as_human_validation(self):
        row = {
            'audio_sha256': 'a',
            'original_machine_transcript': 'गढ़वाली भाषा',
            'whisper_candidate': 'गढ़वाली भासा',
            'structural_preference': 'sravaani_original',
            'quality_flags': [],
            'whisper_candidate_flags': [],
            'supervised_training_eligible': False,
        }
        calibration = {
            'strong': {
                'records': 20,
                'sravaani': {'cer': 0.2},
                'whisper': {'cer': 0.4},
            }
        }
        scored = m.score_recovery_row(row, calibration, direct_reference=False)
        self.assertFalse(scored['direct_human_reference_available'])
        self.assertFalse(scored['confidence_is_accuracy_probability'])
        self.assertFalse(scored['automatic_promotion'])
        self.assertFalse(scored['supervised_training_eligible'])
        self.assertIn(scored['confidence_band'], {'medium', 'low', 'very_low'})
        self.assertTrue(scored['calibration_in_matching_band_support'])

    def test_flagged_selection_receives_very_low_confidence(self):
        row = {
            'audio_sha256': 'a',
            'original_machine_transcript': 'गढ़वाली भाषा',
            'whisper_candidate': 'गढ़वाली �',
            'structural_preference': 'whisper_candidate',
            'quality_flags': [],
            'whisper_candidate_flags': ['decoding_replacement_character'],
            'supervised_training_eligible': False,
        }
        calibration = {
            'moderate': {
                'records': 20,
                'sravaani': {'cer': 0.2},
                'whisper': {'cer': 0.4},
            }
        }
        scored = m.score_recovery_row(row, calibration, direct_reference=False)
        self.assertEqual(scored['confidence_band'], 'very_low')

    def test_unseen_agreement_band_is_out_of_support(self):
        row = {
            'audio_sha256': 'a',
            'original_machine_transcript': 'बिल्कुल अलग वाक्य',
            'whisper_candidate': 'कोई दूसरा पाठ',
            'structural_preference': 'whisper_candidate',
            'quality_flags': [],
            'whisper_candidate_flags': [],
            'supervised_training_eligible': False,
        }
        calibration = {
            'all': {
                'records': 112,
                'sravaani': {'cer': 0.2},
                'whisper': {'cer': 0.4},
            }
        }
        scored = m.score_recovery_row(row, calibration, direct_reference=False)
        self.assertFalse(scored['calibration_in_matching_band_support'])
        self.assertEqual(scored['confidence_band'], 'very_low')


if __name__ == '__main__':
    unittest.main()
