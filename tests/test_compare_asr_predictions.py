import unittest

from compare_asr_predictions import compare_predictions


class CompareAsrPredictionsTests(unittest.TestCase):
    @staticmethod
    def manifest_row(record_id, audio_hash, reference, speaker):
        return {
            'record_id': record_id,
            'audio_sha256': audio_hash,
            'asr_target_clean': reference,
            'speaker_id': speaker,
        }

    @staticmethod
    def prediction(record_id, audio_hash, reference, text, field):
        return {
            'record_id': record_id,
            'audio_sha256': audio_hash,
            'reference': reference,
            field: text,
        }

    def test_compares_exactly_matched_predictions_and_summarizes_speakers(self):
        manifest = [
            self.manifest_row('r1', 'a1', 'one two', 'speaker-a'),
            self.manifest_row('r2', 'a2', 'three four', 'speaker-b'),
        ]
        baseline = [
            self.prediction('r1', 'a1', 'one two', 'one', 'hypothesis'),
            self.prediction('r2', 'a2', 'three four', 'three', 'hypothesis'),
        ]
        candidate = [
            self.prediction('r1', 'a1', 'one two', 'one two', 'prediction'),
            self.prediction('r2', 'a2', 'three four', 'three', 'prediction'),
        ]

        report = compare_predictions(manifest, baseline, candidate)

        self.assertEqual(report['matched_records'], 2)
        self.assertEqual(report['baseline']['word_errors'], 2)
        self.assertEqual(report['candidate']['word_errors'], 1)
        self.assertEqual(report['row_directions']['wer_better_rows'], 1)
        self.assertEqual(report['row_directions']['wer_equal_rows'], 1)
        self.assertEqual(report['by_speaker']['speaker-a']['records'], 1)

    def test_rejects_candidate_missing_manifest_records(self):
        manifest = [self.manifest_row('r1', 'a1', 'one', 'speaker-a')]
        baseline = [self.prediction('r1', 'a1', 'one', 'one', 'hypothesis')]

        with self.assertRaisesRegex(ValueError, 'candidate predictions do not exactly match'):
            compare_predictions(manifest, baseline, [])

    def test_rejects_prediction_reference_mismatch(self):
        manifest = [self.manifest_row('r1', 'a1', 'one', 'speaker-a')]
        baseline = [self.prediction('r1', 'a1', 'different', 'one', 'hypothesis')]
        candidate = [self.prediction('r1', 'a1', 'one', 'one', 'prediction')]

        with self.assertRaisesRegex(ValueError, 'reference mismatch'):
            compare_predictions(manifest, baseline, candidate)

    def test_rejects_duplicate_prediction_identity(self):
        row = self.manifest_row('r1', 'a1', 'one', 'speaker-a')
        baseline = [self.prediction('r1', 'a1', 'one', 'one', 'hypothesis')]
        candidate = [
            self.prediction('r1', 'a1', 'one', 'one', 'prediction'),
            self.prediction('r1', 'a1', 'one', 'one', 'prediction'),
        ]

        with self.assertRaisesRegex(ValueError, 'duplicate candidate prediction key'):
            compare_predictions([row], baseline, candidate)


if __name__ == '__main__':
    unittest.main()
