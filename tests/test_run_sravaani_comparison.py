import tempfile
import unittest
import json
from pathlib import Path

import run_sravaani_comparison as m
import transcribe_sravaani_drafts as drafts


class SraVaaniComparisonTests(unittest.TestCase):
    def test_prediction_retains_manifest_identity_and_row_metrics(self):
        row = {
            'record_id': 'meta_omni:spk1:n1:s1',
            'audio_sha256': 'a' * 64,
            'source_split': 'dev',
            'split': 'validation',
            'asr_target_clean': 'गढ़वाली वाक्य',
            'source_file': 'data/gbm_Deva/dev.parquet',
            'source_file_sha256': 'f' * 64,
            'transcript_conflict_for_audio': False,
            'duplicate_audio_count': 1,
        }
        metrics = {
            'word_errors': 1, 'reference_words': 2,
            'character_errors': 1, 'reference_characters': 12,
        }

        prediction = m.make_prediction_row(row, 'गढ़वाली', metrics)

        self.assertEqual(prediction['record_id'], row['record_id'])
        self.assertEqual(prediction['audio_sha256'], row['audio_sha256'])
        self.assertEqual(prediction['source_split'], 'dev')
        self.assertEqual(prediction['split'], 'validation')
        self.assertEqual(prediction['source_file_sha256'], 'f' * 64)
        self.assertFalse(prediction['transcript_conflict_for_audio'])
        self.assertEqual(prediction['duplicate_audio_count'], 1)
        self.assertEqual(prediction['reference'], row['asr_target_clean'])
        self.assertEqual(prediction['hypothesis'], 'गढ़वाली')
        self.assertEqual(prediction['word_errors'], 1)

    def test_project_relative_input_path_is_resolved(self):
        self.assertEqual(
            m.resolve_input_path(Path('data/example.jsonl')),
            m.ROOT / 'data/example.jsonl',
        )

    def test_select_rows_is_deterministic(self):
        rows = [
            {'audio_sha256': 'b'},
            {'audio_sha256': 'a'},
            {'audio_sha256': 'c'},
        ]
        self.assertEqual(
            [row['audio_sha256'] for row in m.select_rows(rows, 2)],
            ['a', 'b'],
        )

    def test_summarize_scores_micro_averages_error_counts(self):
        scores = [
            {'word_errors': 1, 'reference_words': 2,
             'character_errors': 2, 'reference_characters': 4},
            {'word_errors': 2, 'reference_words': 8,
             'character_errors': 3, 'reference_characters': 6},
        ]
        summary = m.summarize_scores(scores)
        self.assertEqual(summary['wer'], 0.3)
        self.assertEqual(summary['cer'], 0.5)

    def test_validate_model_dir_requires_all_pinned_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            model_dir = Path(directory)
            for name in m.REQUIRED_ARTIFACTS[:-1]:
                (model_dir / name).touch()
            with self.assertRaisesRegex(FileNotFoundError, m.REQUIRED_ARTIFACTS[-1]):
                m.validate_model_dir(model_dir)

    def test_pending_rows_resumes_by_audio_hash(self):
        rows = [
            {'audio_sha256': 'b', 'transcription_priority': 1},
            {'audio_sha256': 'a', 'transcription_priority': 1},
        ]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'drafts.jsonl'
            output.write_text(json.dumps({'audio_sha256': 'a'}) + '\n', encoding='utf-8')
            self.assertEqual(
                [row['audio_sha256'] for row in drafts.pending_rows(rows, output)],
                ['b'],
            )

    def test_draft_record_is_active_experimental_with_pinned_model(self):
        row = {'audio_sha256': 'a', 'transcript_status': 'untranscribed'}
        draft = drafts.build_draft_record(row, 'गढ़वाली वाक्य')
        self.assertEqual(draft['machine_transcript_model'], m.MODEL_ID)
        self.assertEqual(draft['machine_transcript_model_revision'], m.REVISION)
        self.assertFalse(draft['training_eligible'])
        self.assertTrue(draft['experimental_training_eligible'])
        self.assertEqual(draft['review_status'], 'machine_draft_noisy_experimental')


if __name__ == '__main__':
    unittest.main()
