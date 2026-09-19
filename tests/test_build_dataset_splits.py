import json
import tempfile
import unittest
from pathlib import Path

import build_dataset_splits as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )


class DatasetSplitTests(unittest.TestCase):
    def test_builds_strict_audio_and_pending_evaluation_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            out = root / 'out'
            write_jsonl(text_path, [
                {'segment_sha256': 'a' * 64, 'split': 'train', 'quality_flags': []},
                {'segment_sha256': 'b' * 64, 'split': 'test', 'quality_flags': []},
                {'segment_sha256': 'c' * 64, 'split': 'test', 'quality_flags': ['very_short']},
            ])
            clean = {
                'recommended_for_supervised_training': True,
                'language_quality': {
                    'status': 'garhwali_candidate',
                    'review_required': False,
                },
                'transcript_review_flags': [],
                'training_quality_flags': [],
                'audio_quality': {'readable': True},
                'asr_target_clean': 'गढ़वाली पाठ',
                'duration_seconds': 2.0,
            }
            write_jsonl(audio_path, [
                {**clean, 'audio_sha256': '1' * 64, 'speaker_id': 'speaker-1', 'split': 'train'},
                {**clean, 'audio_sha256': '2' * 64, 'speaker_id': 'speaker-2', 'split': 'test'},
                {**clean, 'audio_sha256': '3' * 64, 'speaker_id': 'NA', 'split': 'test'},
                {
                    **clean,
                    'audio_sha256': '4' * 64,
                    'speaker_id': 'speaker-3',
                    'split': 'validation',
                    'transcript_review_flags': ['script_review'],
                },
            ])

            report = m.build_splits(text_path, audio_path, out, semantic_path=None)

            self.assertEqual(report['text']['records'], {'test': 2, 'train': 1, 'validation': 0})
            self.assertEqual(report['asr_strict']['records'], {'test': 1, 'train': 1, 'validation': 0})
            self.assertEqual(report['tts_candidate']['records'], {'test': 1, 'train': 1, 'validation': 0})
            self.assertEqual(report['asr_experimental_all']['records'], {
                'test': 2, 'train': 1, 'validation': 1,
            })
            self.assertEqual(report['excluded_audio']['unidentified_speaker'], 1)
            self.assertEqual(report['excluded_audio']['transcript_or_language_review'], 1)
            evaluation = [json.loads(line) for line in (out / 'evaluation/asr_candidate.jsonl').read_text().splitlines()]
            self.assertEqual([row['audio_sha256'] for row in evaluation], ['2' * 64])
            self.assertEqual(evaluation[0]['review_status'], 'automated_quality_screened')
            self.assertTrue(evaluation[0]['experimental_evaluation_eligible'])
            text_evaluation = [json.loads(line) for line in (out / 'evaluation/text_candidate.jsonl').read_text().splitlines()]
            self.assertEqual([row['segment_sha256'] for row in text_evaluation], ['b' * 64])
            experimental = [
                json.loads(line)
                for line in (out / 'asr_experimental/test.jsonl').read_text().splitlines()
            ]
            self.assertEqual(len(experimental), 2)
            self.assertTrue(all(row['experimental_training_eligible'] for row in experimental))

    def test_rejects_identified_speaker_crossing_splits(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            write_jsonl(text_path, [])
            base = {
                'recommended_for_supervised_training': True,
                'language_quality': {'status': 'garhwali_candidate', 'review_required': False},
                'transcript_review_flags': [],
                'training_quality_flags': [],
                'audio_quality': {'readable': True},
                'asr_target_clean': 'गढ़वाली पाठ',
                'duration_seconds': 2.0,
                'speaker_id': 'same-speaker',
            }
            write_jsonl(audio_path, [
                {**base, 'audio_sha256': '1' * 64, 'split': 'train'},
                {**base, 'audio_sha256': '2' * 64, 'split': 'test'},
            ])

            with self.assertRaisesRegex(ValueError, 'speaker crosses splits'):
                m.build_splits(text_path, audio_path, root / 'out')

    def test_supported_semantic_duplicates_are_reassigned_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text_path = root / 'text.jsonl'
            audio_path = root / 'audio.jsonl'
            semantic_path = root / 'semantic.jsonl'
            write_jsonl(text_path, [
                {'segment_sha256': 'a' * 64, 'split': 'train', 'text': 'भौत शुक्रिया!'},
                {'segment_sha256': 'b' * 64, 'split': 'test', 'text': 'भौत शुक्रिया।'},
            ])
            write_jsonl(audio_path, [])
            write_jsonl(semantic_path, [{
                'left_segment_sha256': 'a' * 64,
                'right_segment_sha256': 'b' * 64,
                'refined_decision': 'supported_candidate',
            }])
            report = m.build_splits(
                text_path, audio_path, root / 'out', semantic_path=semantic_path
            )
            self.assertEqual(report['text']['records']['test'], 0)
            self.assertEqual(report['text']['records']['train'], 2)
            self.assertEqual(
                report['text_duplicate_components']['records_reassigned'], 1
            )


if __name__ == '__main__':
    unittest.main()
