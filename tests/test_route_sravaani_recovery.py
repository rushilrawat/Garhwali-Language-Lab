import unittest

import route_sravaani_recovery as m


class SraVaaniRecoveryRoutingTests(unittest.TestCase):
    def test_empty_and_script_mismatch_get_specific_redecode_actions(self):
        empty = m.route_row({
            'audio_sha256': 'a',
            'machine_transcript': '',
            'machine_transcript_quality': {
                'level': 'high_risk', 'flags': ['empty_transcript'],
            },
        })
        bengali = m.route_row({
            'audio_sha256': 'b',
            'machine_transcript': 'আমি ভালো',
            'machine_transcript_quality': {
                'level': 'high_risk',
                'flags': ['bengali_script', 'no_devanagari_letters'],
            },
        })
        self.assertIn('redecode_empty', empty['recovery_actions'])
        self.assertIn('redecode_with_devanagari_constraint', bengali['recovery_actions'])
        self.assertTrue(empty['active_for_experiment'])
        self.assertFalse(empty['supervised_training_eligible'])

    def test_repetition_candidate_is_reversible_and_bounded(self):
        row = m.route_row({
            'audio_sha256': 'a',
            'machine_transcript': 'अलग अलग अलग अलग प्रकार',
            'machine_transcript_quality': {
                'level': 'high_risk', 'flags': ['repeated_token_loop'],
            },
        })
        self.assertEqual(row['original_machine_transcript'], 'अलग अलग अलग अलग प्रकार')
        self.assertEqual(row['mechanical_candidate'], 'अलग अलग प्रकार')
        self.assertIn('compare_repetition_compaction', row['recovery_actions'])


if __name__ == '__main__':
    unittest.main()
