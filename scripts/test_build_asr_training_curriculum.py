import unittest

import build_asr_training_curriculum as m


class AsrTrainingCurriculumTests(unittest.TestCase):
    def test_human_row_is_full_weight_anchor(self):
        row = {
            'audio_sha256': 'a',
            'local_audio_path': 'audio.wav',
            'asr_target_clean': 'गढ़वाली भाषा',
        }
        result = m.human_row(row, 'train')
        self.assertEqual(result['target_text'], 'गढ़वाली भाषा')
        self.assertEqual(result['sample_weight'], 1.0)
        self.assertEqual(result['introduced_stage'], 0)
        self.assertTrue(result['supervised_training_eligible'])

    def test_unflagged_machine_row_uses_sravaani_target(self):
        row = {
            'audio_sha256': 'a',
            'local_audio_path': 'audio.wav',
            'machine_transcript': 'गढ़वाली भाषा',
            'recovery_status': 'not_targeted_for_redecode',
        }
        result = m.machine_row(row, standard_score=0.8, weight_scale=0.1)
        self.assertEqual(result['target_text'], 'गढ़वाली भाषा')
        self.assertEqual(result['curriculum_tier'], 'standard_sravaani')
        self.assertEqual(result['introduced_stage'], 1)
        self.assertAlmostEqual(result['sample_weight'], 0.08)

    def test_recovery_row_uses_structural_candidate_and_band_stage(self):
        row = {
            'audio_sha256': 'a',
            'local_audio_path': 'audio.wav',
            'machine_transcript': 'मूल',
            'recovery_status': 'confidence_scored_alternative_available',
            'recovery_confidence': {
                'whisper_candidate': 'विकल्प',
                'structural_preference': 'whisper_candidate',
                'confidence_score': 0.3,
                'confidence_band': 'low',
                'confidence_is_accuracy_probability': False,
            },
        }
        result = m.machine_row(row, standard_score=0.8, weight_scale=0.1)
        self.assertEqual(result['target_text'], 'विकल्प')
        self.assertEqual(result['curriculum_tier'], 'recovery_low')
        self.assertEqual(result['introduced_stage'], 3)
        self.assertAlmostEqual(result['sample_weight'], 0.03)
        self.assertFalse(result['supervised_training_eligible'])

    def test_empty_preferred_recovery_target_falls_back_to_nonempty_candidate(self):
        row = {
            'audio_sha256': 'a',
            'local_audio_path': 'audio.wav',
            'machine_transcript': '',
            'recovery_status': 'confidence_scored_alternative_available',
            'recovery_confidence': {
                'whisper_candidate': 'विकल्प',
                'whisper_candidate_flags': ['noisy'],
                'structural_preference': 'sravaani_original',
                'selected_candidate_flags': ['empty_transcript'],
                'confidence_score': 0.1,
                'confidence_band': 'very_low',
            },
        }
        result = m.machine_row(row, standard_score=0.8, weight_scale=0.1)
        self.assertEqual(result['target_text'], 'विकल्प')
        self.assertEqual(result['target_model'], 'whisper-tiny-garhwali-v0.2')
        self.assertEqual(result['target_selection'], 'nonempty_candidate_fallback')
        self.assertEqual(result['quality_flags'], ['noisy'])

    def test_machine_weights_match_requested_effective_budget(self):
        raw_scores = [0.8, 0.2]
        scale = m.machine_weight_scale(raw_scores, human_records=1, ratio=1.0)
        self.assertAlmostEqual(sum(score * scale for score in raw_scores), 1.0)

    def test_duplicate_machine_audio_requires_matching_transcript(self):
        rows = [
            {'audio_sha256': 'a', 'machine_transcript': 'एक'},
            {'audio_sha256': 'a', 'machine_transcript': 'दुई'},
        ]
        with self.assertRaises(ValueError):
            m.deduplicate_machine_rows(rows)


if __name__ == '__main__':
    unittest.main()
