import json
import tempfile
import unittest
from pathlib import Path

import prepare_whisper_compatible_manifests as m


class SpaceSeparatedTokenizer:
    def __call__(self, text):
        return {'input_ids': text.split()}


class WhisperCompatibleManifestTests(unittest.TestCase):
    @staticmethod
    def row(record_id, audio_hash, text, duration=5):
        return {
            'record_id': record_id,
            'audio_sha256': audio_hash,
            'asr_target_clean': text,
            'duration_seconds': duration,
            'split_safe_for_training': True,
            'split_safe_for_evaluation': True,
        }

    def test_filter_retains_compatible_rows_and_audits_limit_exclusions(self):
        rows = [
            self.row('short', 'a', 'one two', duration=5),
            self.row('long-text', 'b', 'one two three', duration=5),
            self.row('long-audio', 'c', 'one two', duration=31),
            self.row('both-long', 'd', 'one two three', duration=31),
        ]

        included, excluded = m.filter_rows(
            rows, SpaceSeparatedTokenizer(), max_target_tokens=2,
            max_audio_seconds=30,
        )

        self.assertEqual([row['record_id'] for row in included], ['short'])
        self.assertEqual(
            [row['record_id'] for row in excluded],
            ['long-text', 'long-audio', 'both-long'],
        )
        self.assertEqual(excluded[0]['exclusion_reasons'], ['target_exceeds_model_token_limit'])
        self.assertEqual(excluded[1]['exclusion_reasons'], ['audio_exceeds_model_window'])
        self.assertEqual(excluded[2]['exclusion_reasons'], [
            'target_exceeds_model_token_limit', 'audio_exceeds_model_window',
        ])
        self.assertNotIn('asr_target_clean', excluded[0])

    def test_build_writes_hash_linked_manifests_and_exclusion_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_path = root / 'train.jsonl'
            validation_path = root / 'validation.jsonl'
            output = root / 'compatible'
            train_rows = [self.row('train-1', 'a', 'one two')]
            validation_rows = [self.row('validation-1', 'b', 'one two')]
            for path, rows in ((train_path, train_rows), (validation_path, validation_rows)):
                path.write_text(''.join(json.dumps(row) + '\n' for row in rows))

            report = m.build_views(
                train_path, validation_path, output, SpaceSeparatedTokenizer(),
                max_target_tokens=2, max_audio_seconds=30,
                model_id='test-checkpoint',
            )

            self.assertEqual(report['included_rows'], {'train': 1, 'validation': 1})
            self.assertEqual(report['excluded_rows'], {'train': 0, 'validation': 0})
            self.assertEqual(report['model_limits'], {
                'max_target_tokens': 2, 'max_audio_seconds': 30,
            })
            self.assertEqual(len((output / 'train.jsonl').read_text().splitlines()), 1)
            self.assertEqual(len((output / 'validation.jsonl').read_text().splitlines()), 1)
            self.assertEqual((output / 'exclusions.jsonl').read_text(), '')
            self.assertTrue((output / 'report.json').is_file())

    def test_build_refuses_to_overwrite_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train_path = root / 'train.jsonl'
            validation_path = root / 'validation.jsonl'
            train_path.write_text(json.dumps(self.row('train', 'a', 'one')) + '\n')
            validation_path.write_text(json.dumps(self.row('validation', 'b', 'two')) + '\n')
            output = root / 'compatible'
            output.mkdir()
            marker = output / 'keep.txt'
            marker.write_text('keep')

            with self.assertRaisesRegex(FileExistsError, 'refusing to overwrite'):
                m.build_views(
                    train_path, validation_path, output, SpaceSeparatedTokenizer(),
                    max_target_tokens=2, max_audio_seconds=30,
                    model_id='test-checkpoint',
                )
            self.assertEqual(marker.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
