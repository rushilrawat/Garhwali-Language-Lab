import unittest

import analyze_sravaani_drafts as m


class SraVaaniDraftQualityTests(unittest.TestCase):
    def test_empty_draft_is_flagged_but_remains_active(self):
        row = {'machine_transcript': '', 'duration_seconds': 2.0}
        result = m.analyze_row(row, hypothesis_frequency=1)
        self.assertIn('empty_transcript', result['machine_transcript_quality']['flags'])
        self.assertTrue(result['experimental_training_eligible'])
        self.assertEqual(result['machine_transcript_quality']['usage'], 'active_experimental')

    def test_bengali_output_is_identified(self):
        row = {'machine_transcript': 'আমি ভালো আছি', 'duration_seconds': 2.0}
        result = m.analyze_row(row, hypothesis_frequency=1)
        flags = result['machine_transcript_quality']['flags']
        self.assertIn('bengali_script', flags)
        self.assertIn('no_devanagari_letters', flags)

    def test_repeated_token_loop_is_flagged(self):
        row = {'machine_transcript': 'हा हा हा हा हा', 'duration_seconds': 2.0}
        result = m.analyze_row(row, hypothesis_frequency=1)
        self.assertIn('repeated_token_loop', result['machine_transcript_quality']['flags'])

    def test_frequent_identical_hypothesis_is_flagged(self):
        row = {'machine_transcript': 'नमस्कार', 'duration_seconds': 1.0}
        result = m.analyze_row(row, hypothesis_frequency=12)
        quality = result['machine_transcript_quality']
        self.assertIn('frequent_identical_hypothesis', quality['flags'])
        self.assertEqual(quality['identical_hypothesis_frequency'], 12)


if __name__ == '__main__':
    unittest.main()
