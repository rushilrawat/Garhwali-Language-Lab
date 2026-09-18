import unittest

import build_sravaani_recovery_adjudication as m


class SraVaaniRecoveryAdjudicationTests(unittest.TestCase):
    def test_structurally_clean_candidate_wins(self):
        chosen = m.choose_candidate([
            {'model': 'ARTPARK-IISc/SraVaani-1.0', 'transcript': '', 'flags': ['empty_transcript']},
            {'model': 'whisper-tiny-garhwali-v0.2', 'transcript': 'साफ पाठ', 'flags': []},
            {'model': 'whisper-tiny-garhwali-v0.1', 'transcript': 'साफ पाठ', 'flags': []},
        ])
        self.assertEqual(chosen['model'], 'whisper-tiny-garhwali-v0.2')

    def test_model_rank_breaks_equal_severity_tie(self):
        chosen = m.choose_candidate([
            {'model': 'ARTPARK-IISc/SraVaani-1.0', 'transcript': 'मूल', 'flags': []},
            {'model': 'whisper-tiny-garhwali-v0.2', 'transcript': 'दूसर', 'flags': []},
        ])
        self.assertEqual(chosen['model'], 'ARTPARK-IISc/SraVaani-1.0')

    def test_clean_consensus_remains_review_only(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2,
            'machine_transcript': '',
            'machine_transcript_quality': {'flags': ['empty_transcript']},
            'recovery_confidence': {
                'whisper_candidate': 'गढ़वळि पाठ',
                'whisper_candidate_flags': [],
            },
        }
        v01 = {
            'machine_transcript': 'गढ़वळि पाठ',
            'token_confidence_uncalibrated': 0.8,
        }
        result = m.build_review_row(row, v01)
        self.assertEqual(result['evidence_status'], 'related_checkpoint_consensus_clean')
        self.assertFalse(result['automatic_correction'])
        self.assertFalse(result['supervised_training_eligible'])
        self.assertFalse(result['recommended_for_machine_label_training'])
        self.assertTrue(result['original_transcript_preserved'])

    def test_flagged_best_proposal_stays_unresolved(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2,
            'machine_transcript': 'एक एक एक एक',
            'machine_transcript_quality': {'flags': ['repeated_token_loop']},
            'recovery_confidence': {
                'whisper_candidate': 'दो दो दो दो',
                'whisper_candidate_flags': ['repeated_token_loop'],
            },
        }
        v01 = {'machine_transcript': 'तीन तीन तीन तीन', 'token_confidence_uncalibrated': 0.5}
        result = m.build_review_row(row, v01)
        self.assertEqual(result['evidence_status'], 'unresolved_structural_risk')
        self.assertTrue(result['proposed_machine_transcript_flags'])


if __name__ == '__main__':
    unittest.main()
