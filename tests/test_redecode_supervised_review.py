import unittest

import redecode_supervised_review as m


class SupervisedReviewRedecodeTests(unittest.TestCase):
    def test_selects_only_non_bengali_flagged_rows(self):
        rows = [
            {
                'audio_sha256': 'a',
                'asr_target_clean': 'गढ़वाली पाठ',
                'transcript_review_flags': ['manual-transcript-review'],
            },
            {
                'audio_sha256': 'b',
                'asr_target_clean': 'বাংলা পাঠ',
                'transcript_review_flags': ['bengali_script'],
            },
            {
                'audio_sha256': 'c',
                'asr_target_clean': 'साफ पाठ',
                'transcript_review_flags': [],
            },
        ]
        self.assertEqual(
            [row['audio_sha256'] for row in m.select_review_rows(rows)],
            ['a'],
        )

    def test_model_agreement_never_replaces_human_reference(self):
        row = {
            'audio_sha256': 'a',
            'asr_target': 'मूल पाठ',
            'asr_target_clean': 'मूल पाठ',
            'transcript_review_flags': ['manual-transcript-review'],
        }
        result = m.build_review_record(row, {
            'whisper-v0.1': 'दूसर पाठ',
            'whisper-v0.2': 'दूसर पाठ',
        })
        self.assertEqual(result['reference_text'], 'मूल पाठ')
        self.assertEqual(result['recommended_text'], 'मूल पाठ')
        self.assertFalse(result['reference_changed'])
        self.assertTrue(result['model_evidence']['models_agree'])
        self.assertFalse(result['model_evidence']['all_models_match_reference'])
        self.assertEqual(result['review_status'], 'listening_review_required')

    def test_exact_model_support_is_recorded_without_claiming_accuracy(self):
        row = {
            'audio_sha256': 'a',
            'asr_target_clean': 'मूल  पाठ',
            'transcript_review_flags': ['manual-transcript-review'],
        }
        result = m.build_review_record(row, {
            'whisper-v0.1': 'मूल पाठ',
            'whisper-v0.2': 'मूल पाठ',
        })
        self.assertTrue(result['model_evidence']['all_models_match_reference'])
        self.assertEqual(result['review_status'], 'model_supported_listening_review_pending')
        self.assertFalse(result['model_evidence']['agreement_is_accuracy_proof'])

    def test_removes_only_unmatched_open_parenthesis_from_release_text(self):
        row = {
            'audio_sha256': 'a',
            'asr_target_clean': 'एक हरी और एक नीली ( साड़ी',
            'transcript_review_flags': ['manual-transcript-review'],
        }
        result = m.build_review_record(row, {'whisper-v0.2': 'एक हरी और एक नीली साड़ी'})
        self.assertEqual(result['reference_text'], 'एक हरी और एक नीली ( साड़ी')
        self.assertEqual(result['release_text'], 'एक हरी और एक नीली साड़ी')
        self.assertEqual(result['recommended_text'], result['release_text'])
        self.assertIn('unmatched_open_parenthesis_removed', result['automatic_changes'])

    def test_preserves_balanced_parenthetical_for_listening_review(self):
        row = {
            'audio_sha256': 'a',
            'asr_target_clean': 'टीचरों (teachers) दगड़',
            'transcript_review_flags': ['manual-transcript-review'],
        }
        result = m.build_review_record(row, {'whisper-v0.2': 'टीचरों दगड़'})
        self.assertEqual(result['release_text'], row['asr_target_clean'])
        self.assertIn('parenthetical_content_alignment_review', result['review_signals'])


if __name__ == '__main__':
    unittest.main()
