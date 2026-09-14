import json
import tempfile
import unittest
from pathlib import Path

import build_huggingface_dataset as m


class HuggingFaceDatasetBuilderTests(unittest.TestCase):
    def test_public_text_requires_every_component_to_be_publishable(self):
        allowed = {
            'parents': [{'provenance': [{
                'training_eligible': False,
                'license': 'CC-BY-4.0',
            }]}],
        }
        blocked = {
            'parents': [{'provenance': [{
                'license': 'CC-BY-4.0',
                'rights_status': 'source_component_and_consent_review_pending',
            }]}],
        }
        self.assertTrue(m.is_public_text_row(allowed))
        self.assertFalse(m.is_public_text_row(blocked))

    def test_audio_export_uses_content_addressed_relative_path(self):
        row = {
            'audio_sha256': 'ab' * 32,
            'local_audio_path': 'data/audio/source.wav',
            'asr_target_clean': 'गढ़वाली',
            'machine_transcript_quality': {'flags': ['mixed_script']},
        }
        exported = m.audio_row(row, transcript_field='asr_target_clean')
        self.assertEqual(exported['audio'], f'audio/ab/{"ab" * 32}.wav')
        self.assertEqual(exported['transcript'], 'गढ़वाली')
        self.assertEqual(exported['machine_transcript_quality']['flags'], ['mixed_script'])
        self.assertNotIn('local_audio_path', exported)

    def test_shards_are_deterministic_and_reported(self):
        rows = [{'id': str(index)} for index in range(5)]
        with tempfile.TemporaryDirectory() as directory:
            report = m.write_shards(rows, Path(directory), 'train', shard_rows=2)
            self.assertEqual(report['records'], 5)
            self.assertEqual(report['shards'], 3)
            paths = sorted(Path(directory).glob('train-*.jsonl'))
            self.assertEqual([p.name for p in paths], [
                'train-00000.jsonl', 'train-00001.jsonl', 'train-00002.jsonl'
            ])
            self.assertEqual(json.loads(paths[-1].read_text())['id'], '4')

    def test_draft_coverage_accepts_source_rows_with_duplicate_audio(self):
        queue = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        drafts = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        self.assertTrue(m.drafts_cover_queue(queue, drafts))
        self.assertFalse(m.drafts_cover_queue(queue, drafts[:1]))

    def test_duplicate_audio_rows_merge_source_paths(self):
        rows = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav', 'machine_transcript': 'पाठ'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav', 'machine_transcript': 'पाठ'},
        ]
        merged = list(m.deduplicate_audio_rows(rows, 'machine_transcript'))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['duplicate_source_audio_paths'], ['one.wav', 'two.wav'])

    def test_audio_link_report_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'source.wav'
            source.write_bytes(b'audio')
            old_root = m.ROOT
            try:
                m.ROOT = root
                row = {'audio_sha256': 'ab' * 32, 'local_audio_path': 'source.wav'}
                first = m.link_audio([row], root / 'package')
                second = m.link_audio([row], root / 'package')
            finally:
                m.ROOT = old_root
        self.assertEqual(first, {'new': 1, 'total': 1})
        self.assertEqual(second, {'new': 0, 'total': 1})


if __name__ == '__main__':
    unittest.main()
