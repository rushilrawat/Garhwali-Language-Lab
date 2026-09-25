import unittest

from build_hf_speech_release import make_release_record, release_split


class HuggingFaceSpeechReleaseTests(unittest.TestCase):
    def test_public_record_preserves_all_transcript_versions_and_license(self):
        main = {
            'row_idx': 4,
            'audio_path': 'private/source-name.wav',
            'speaker_id': 'provider-speaker-7',
            'transcript': 'मुख्य स्रोत पाठ',
            'district': 'TehriGarhwal',
            'gender': 'Female',
            'license': 'CC-BY-4.0',
            'revision': 'abc123',
            'state': 'Uttarakhand',
            'reference_image': 'private/image.jpg',
            'stay_years': 'Tehri Garhwal(22)',
        }
        transcription = {
            'row_idx': 9,
            'split': 'test',
            'transcript': 'पृथक संदर्भ पाठ',
            'source': 'ARTPARK-IISc/Vaani-transcription-part',
            'revision': 'def456',
            'license': 'CC-BY-4.0',
        }
        draft = {
            'transcript': 'मशीन मसौदा',
            'machine_transcript_model': 'ARTPARK-IISc/SraVaani-1.0',
            'review_status': 'machine_draft_noisy_experimental',
        }

        record = make_release_record(
            main=main,
            transcription=transcription,
            draft=draft,
            audio_sha256='a' * 64,
            record_id='vaani_main_000004',
        )

        self.assertEqual(record['transcript'], 'पृथक संदर्भ पाठ')
        self.assertEqual(record['main_dataset_transcript'], 'मुख्य स्रोत पाठ')
        self.assertTrue(record['transcript_conflict'])
        self.assertEqual(record['machine_draft'], 'मशीन मसौदा')
        self.assertEqual(record['source_license'], 'CC-BY-4.0')
        self.assertEqual(record['split_assignment_source'], 'Vaani-transcription-part')
        self.assertNotIn('speaker_id', record)
        self.assertNotIn('audio_path', record)
        self.assertNotIn('reference_image', record)
        self.assertNotIn('stay_years', record)
        self.assertNotIn('state', record)

    def test_untranscribed_main_record_is_training_data_not_reference_text(self):
        record = make_release_record(
            main={
                'row_idx': 3,
                'audio_path': 'private/source-name.wav',
                'speaker_id': 'NA',
                'transcript': '',
                'district': 'Uttarkashi',
                'gender': 'Male',
                'license': 'CC-BY-4.0',
                'revision': 'abc123',
            },
            transcription=None,
            draft={
                'transcript': 'machine hypothesis',
                'machine_transcript_model': 'SraVaani',
                'review_status': 'machine_draft_noisy_experimental',
            },
            audio_sha256='b' * 64,
            record_id='vaani_main_000003',
        )

        self.assertIsNone(record['transcript'])
        self.assertEqual(record['machine_draft'], 'machine hypothesis')
        self.assertEqual(record['transcript_review_status'], 'untranscribed')
        self.assertFalse(record['transcript_conflict'])
        self.assertEqual(record['district'], 'Uttarkashi')

    def test_official_human_split_overrides_main_repository_train_split(self):
        self.assertEqual(release_split({'split': 'train'}, None), 'train')
        self.assertEqual(release_split({'split': 'train'}, {'split': 'validation'}), 'validation')
        self.assertEqual(release_split(None, {'split': 'test'}), 'test')


if __name__ == '__main__':
    unittest.main()
