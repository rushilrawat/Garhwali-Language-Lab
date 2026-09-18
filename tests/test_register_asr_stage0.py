import unittest

import register_asr_stage0 as m


class RegisterAsrStage0Tests(unittest.TestCase):
    def test_training_equivalence_requires_same_hashes_and_targets(self):
        strict = [
            {'audio_sha256': 'a', 'asr_target_clean': 'एक'},
            {'audio_sha256': 'b', 'asr_target_clean': 'दुई'},
        ]
        curriculum = [
            {'audio_sha256': 'b', 'target_text': 'दुई', 'introduced_stage': 0},
            {'audio_sha256': 'a', 'target_text': 'एक', 'introduced_stage': 0},
            {'audio_sha256': 'c', 'target_text': 'तीन', 'introduced_stage': 1},
        ]
        result = m.verify_training_equivalence(strict, curriculum)
        self.assertEqual(result['records'], 2)
        self.assertTrue(result['same_audio_hashes'])
        self.assertTrue(result['same_targets'])

        curriculum[0]['target_text'] = 'अलग'
        with self.assertRaisesRegex(ValueError, 'does not match'):
            m.verify_training_equivalence(strict, curriculum)

    def test_prediction_summary_uses_only_requested_audio(self):
        rows = [
            {
                'audio_sha256': 'a',
                'word_errors': 1,
                'reference_words': 4,
                'character_errors': 2,
                'reference_characters': 10,
            },
            {
                'audio_sha256': 'b',
                'word_errors': 9,
                'reference_words': 9,
                'character_errors': 9,
                'reference_characters': 9,
            },
        ]
        result = m.summarize_predictions(rows, {'a'})
        self.assertEqual(result['records'], 1)
        self.assertEqual(result['wer'], 0.25)
        self.assertEqual(result['cer'], 0.2)

    def test_prediction_references_must_match_validation_manifest(self):
        rows = [{'audio_sha256': 'a', 'reference': 'अलग'}]
        with self.assertRaisesRegex(ValueError, 'references'):
            m.verify_prediction_references(rows, {'a': 'सही'})


if __name__ == '__main__':
    unittest.main()
