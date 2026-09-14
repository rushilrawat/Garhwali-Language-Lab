import unittest

import integrate_sravaani_confidence as m


class SraVaaniConfidenceIntegrationTests(unittest.TestCase):
    def test_recovery_metadata_is_attached_without_replacing_original(self):
        base = {
            'audio_sha256': 'a',
            'machine_transcript': 'मूल पाठ',
            'training_eligible': False,
            'experimental_training_eligible': True,
        }
        confidence = {
            'audio_sha256': 'a',
            'original_machine_transcript': 'मूल पाठ',
            'whisper_candidate': 'दूसरा पाठ',
            'confidence_score': 0.2,
            'confidence_band': 'very_low',
            'structural_preference': 'whisper_candidate',
            'automatic_promotion': False,
        }
        merged = m.merge_row(base, confidence)
        self.assertEqual(merged['machine_transcript'], 'मूल पाठ')
        self.assertEqual(
            merged['recovery_confidence']['whisper_candidate'], 'दूसरा पाठ'
        )
        self.assertFalse(merged['training_eligible'])
        self.assertTrue(merged['experimental_training_eligible'])

    def test_transcript_mismatch_is_rejected(self):
        base = {'audio_sha256': 'a', 'machine_transcript': 'मूल पाठ'}
        confidence = {
            'audio_sha256': 'a',
            'original_machine_transcript': 'अलग पाठ',
        }
        with self.assertRaises(ValueError):
            m.merge_row(base, confidence)

    def test_unflagged_row_remains_active_without_fabricated_confidence(self):
        base = {
            'audio_sha256': 'a',
            'machine_transcript': 'मूल पाठ',
            'training_eligible': False,
            'experimental_training_eligible': True,
        }
        merged = m.merge_row(base, None)
        self.assertEqual(merged['recovery_status'], 'not_targeted_for_redecode')
        self.assertNotIn('recovery_confidence', merged)
        self.assertFalse(merged['training_eligible'])
        self.assertTrue(merged['experimental_training_eligible'])


if __name__ == '__main__':
    unittest.main()
