import unittest

import validate_release_index as m


class ReleaseIndexTests(unittest.TestCase):
    def test_accepts_consistent_candidate_counts(self):
        index = {
            'release_id': 'v0.1-candidate',
            'status': 'candidate_pending_native_review',
            'text': {'total': 3, 'splits': {'train': 1, 'validation': 1, 'test': 1}},
            'speech': {'total': 2, 'splits': {'train': 1, 'validation': 0, 'test': 1}},
            'leakage': {'text_hash_cross_split': 0, 'identified_speaker_cross_split': 0},
        }
        self.assertEqual(m.validate(index), [])

    def test_rejects_count_mismatch_and_leakage(self):
        index = {
            'release_id': 'v0.1-candidate',
            'status': 'candidate_pending_native_review',
            'text': {'total': 4, 'splits': {'train': 1, 'validation': 1, 'test': 1}},
            'speech': {'total': 2, 'splits': {'train': 1, 'validation': 0, 'test': 1}},
            'leakage': {'text_hash_cross_split': 1, 'identified_speaker_cross_split': 0},
        }
        self.assertEqual(m.validate(index), [
            'text split counts sum to 3, expected 4',
            'text_hash_cross_split must be zero, found 1',
        ])

    def test_validates_training_and_review_derived_audio_total(self):
        index = {
            'release_id': 'v0.1-candidate',
            'status': 'candidate_pending_native_review',
            'text': {'total': 1, 'splits': {'train': 1, 'validation': 0, 'test': 0}},
            'speech': {'total': 1, 'splits': {'train': 1, 'validation': 0, 'test': 0}},
            'derived_audio': {
                'total': 3,
                'splits': {'train': 1, 'validation': 0, 'test': 0},
                'flagged_review_copies': 1,
            },
            'leakage': {'text_hash_cross_split': 0},
        }
        self.assertEqual(m.validate(index), [
            'derived audio counts sum to 2, expected 3',
        ])

    def test_rejects_benchmark_training_leakage(self):
        index = {
            'release_id': 'v0.1',
            'status': 'integrated_experimental_release',
            'text': {'total': 1, 'splits': {'train': 1, 'validation': 0, 'test': 0}},
            'speech': {'total': 1, 'splits': {'train': 1, 'validation': 0, 'test': 0}},
            'leakage': {'text_hash_cross_split': 0},
            'garhwali_bench': {
                'internal_exact_train_text': 1,
                'asr_speaker_overlap': 0,
            },
        }
        self.assertEqual(m.validate(index), [
            'garhwali_bench.internal_exact_train_text must be zero, found 1',
        ])

    def test_rejects_release_ready_status_without_passing_final_audit(self):
        index = {
            'status': 'release_ready_with_public_rights_filtered_export',
            'final_audit_status': 'failed',
            'text': {'total': 0, 'splits': {'train': 0, 'validation': 0, 'test': 0}},
            'speech': {'total': 0, 'splits': {'train': 0, 'validation': 0, 'test': 0}},
            'leakage': {},
        }
        self.assertEqual(
            m.validate(index), ['release-ready status requires a passing final audit']
        )


if __name__ == '__main__':
    unittest.main()
