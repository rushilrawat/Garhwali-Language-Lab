import importlib
import unittest


try:
    audit = importlib.import_module('audit_saved_asr_heldout_lineage')
except ModuleNotFoundError as error:
    if error.name != 'audit_saved_asr_heldout_lineage':
        raise
    audit = None


class SavedAsrHeldoutLineageTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(audit, 'audit_saved_asr_heldout_lineage module is missing')
        return audit

    def fixtures(self):
        audio_a = 'a' * 64
        audio_b = 'b' * 64
        manifest_rows = [
            {'audio_sha256': audio_a, 'asr_target_clean': 'one'},
            {'audio_sha256': audio_b, 'asr_target_clean': 'two words'},
        ]
        prediction_rows = [
            {
                'audio_filepath': f'/private/cache/{audio_a}.wav',
                'reference': 'one',
                'word_errors': 0,
                'reference_words': 1,
                'character_errors': 0,
                'reference_characters': 3,
            },
            {
                'audio_filepath': f'/private/cache/{audio_b}.wav',
                'reference': 'two words',
                'word_errors': 1,
                'reference_words': 2,
                'character_errors': 1,
                'reference_characters': 9,
            },
        ]
        return manifest_rows, prediction_rows

    def test_reconciles_audio_ids_clean_references_and_saved_aggregate(self):
        manifest_rows, prediction_rows = self.fixtures()
        result = self.module().reconcile_prediction_rows(
            manifest_rows,
            prediction_rows,
            {
                'word_errors': 1,
                'reference_words': 3,
                'character_errors': 1,
                'reference_characters': 12,
                'wer': 1 / 3,
                'cer': 1 / 12,
            },
        )

        self.assertEqual(result['record_count'], 2)
        self.assertEqual(result['audio_ids_match'], 2)
        self.assertEqual(result['clean_references_match'], 2)
        self.assertAlmostEqual(result['wer'], 1 / 3)
        self.assertAlmostEqual(result['cer'], 1 / 12)

    def test_rejects_duplicate_or_missing_audio_ids(self):
        manifest_rows, prediction_rows = self.fixtures()
        prediction_rows[1]['audio_filepath'] = prediction_rows[0]['audio_filepath']

        with self.assertRaisesRegex(ValueError, 'duplicate prediction audio hash'):
            self.module().reconcile_prediction_rows(manifest_rows, prediction_rows, {})

        manifest_rows, prediction_rows = self.fixtures()
        prediction_rows.pop()
        with self.assertRaisesRegex(ValueError, 'prediction audio IDs must exactly match'):
            self.module().reconcile_prediction_rows(manifest_rows, prediction_rows, {})

    def test_rejects_reference_or_aggregate_drift(self):
        manifest_rows, prediction_rows = self.fixtures()
        prediction_rows[0]['reference'] = 'different'
        with self.assertRaisesRegex(ValueError, 'clean reference mismatch'):
            self.module().reconcile_prediction_rows(manifest_rows, prediction_rows, {})

        manifest_rows, prediction_rows = self.fixtures()
        with self.assertRaisesRegex(ValueError, 'reported aggregate'):
            self.module().reconcile_prediction_rows(
                manifest_rows,
                prediction_rows,
                {
                    'word_errors': 9,
                    'reference_words': 3,
                    'character_errors': 1,
                    'reference_characters': 12,
                    'wer': 3.0,
                    'cer': 1 / 12,
                },
            )

    def test_accepts_audio_hash_field_and_bootstraps_complete_speaker_groups(self):
        module = self.module()
        manifest_rows = [
            {'audio_sha256': 'a' * 64, 'asr_target_clean': 'a', 'speaker_id': 'speaker-a'},
            {'audio_sha256': 'b' * 64, 'asr_target_clean': 'b', 'speaker_id': 'speaker-a'},
            {'audio_sha256': 'c' * 64, 'asr_target_clean': 'c', 'speaker_id': 'speaker-b'},
        ]
        predictions = [
            {'audio_sha256': 'a' * 64, 'reference': 'a', 'word_errors': 0,
             'reference_words': 1, 'character_errors': 0, 'reference_characters': 1},
            {'audio_sha256': 'b' * 64, 'reference': 'b', 'word_errors': 0,
             'reference_words': 1, 'character_errors': 0, 'reference_characters': 1},
            {'audio_sha256': 'c' * 64, 'reference': 'c', 'word_errors': 1,
             'reference_words': 1, 'character_errors': 1, 'reference_characters': 1},
        ]
        module.reconcile_prediction_rows(
            manifest_rows, predictions,
            {'word_errors': 1, 'reference_words': 3, 'character_errors': 1,
             'reference_characters': 3, 'wer': 1 / 3, 'cer': 1 / 3},
        )
        candidate = [dict(row) for row in predictions]
        candidate[0]['word_errors'] = candidate[0]['character_errors'] = 1
        candidate[1]['word_errors'] = candidate[1]['character_errors'] = 1
        candidate[2]['word_errors'] = candidate[2]['character_errors'] = 0

        first = module.paired_speaker_bootstrap(
            manifest_rows, predictions, candidate, replicates=250, seed=17)
        second = module.paired_speaker_bootstrap(
            manifest_rows, predictions, candidate, replicates=250, seed=17)

        self.assertEqual(first, second)
        self.assertEqual(first['speaker_cluster_count'], 2)
        self.assertEqual(first['record_count'], 3)
        self.assertAlmostEqual(first['wer_delta_candidate_minus_base'], 1 / 3)
        self.assertAlmostEqual(first['cer_delta_candidate_minus_base'], 1 / 3)


if __name__ == '__main__':
    unittest.main()
