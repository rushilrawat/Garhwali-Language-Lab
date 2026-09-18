import unittest

import build_vaani_source_conflicts as m


class VaaniSourceConflictTests(unittest.TestCase):
    def test_requires_repeated_human_and_machine_bengali_evidence(self):
        human = [
            {'speaker_id': 'speaker-a', 'canonical_transcript': 'বাংলা পাঠ'}
            for _ in range(3)
        ]
        machine = [
            {
                'speaker_id': 'speaker-a',
                'machine_transcript_quality': {'flags': ['bengali_script']},
            }
            for _ in range(10)
        ]
        profiles = m.conflict_profiles(human, machine)
        self.assertIn('speaker-a', profiles)
        self.assertEqual(profiles['speaker-a']['human_bengali_transcripts'], 3)
        self.assertEqual(profiles['speaker-a']['machine_bengali_drafts'], 10)

    def test_single_script_anomaly_does_not_mark_a_speaker(self):
        human = [{'speaker_id': 'speaker-a', 'canonical_transcript': 'বাংলা পাঠ'}]
        machine = [{
            'speaker_id': 'speaker-a',
            'machine_transcript_quality': {'flags': ['bengali_script']},
        }]
        self.assertEqual(m.conflict_profiles(human, machine), {})

    def test_conflict_row_remains_preserved_outside_garhwali_training(self):
        row = {
            'audio_sha256': 'a', 'speaker_id': 'speaker-a',
            'audio_path': 'example.wav', 'language': 'Garhwali',
        }
        profile = {
            'human_bengali_transcripts': 8,
            'machine_bengali_drafts': 98,
            'evidence': ['repeated_human_bengali_script'],
        }
        result = m.conflict_row(row, profile)
        self.assertFalse(result['garhwali_training_eligible'])
        self.assertTrue(result['active_for_source_error_analysis'])
        self.assertEqual(result['source_language_label'], 'Garhwali')

    def test_filename_speaker_key_recovers_missing_metadata_id(self):
        row = {
            'speaker_id': 'NA',
            'audio_path': (
                'IISc_VaaniProject_S_Uttarakhand_Uttarkashi_98459_'
                '10988192_GENERIC_0201_4_8589.wav'
            ),
        }
        self.assertEqual(m.source_speaker_key(row), 'Uttarkashi:98459')


if __name__ == '__main__':
    unittest.main()
