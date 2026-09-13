import json
import tempfile
import unittest
from pathlib import Path

import audit_final_release as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8'
    )


class FinalReleaseAuditTests(unittest.TestCase):
    def fixture(self, root):
        configs = {}
        provenance = [{'license_url': 'https://creativecommons.org/licenses/by/4.0/'}]
        rows = {
            'text/train': [{'id': 'text-a', 'text': 'अ', 'language': 'gbm', 'provenance': provenance}],
            'text/validation': [{'id': 'text-b', 'text': 'ब', 'language': 'gbm', 'provenance': provenance}],
            'text/test': [{'id': 'text-c', 'text': 'क', 'language': 'gbm', 'provenance': provenance}],
            'asr/train': [{'audio_sha256': 'audio-a', 'speaker_id': 'speaker-a', 'transcript': 'अ', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/validation': [{'audio_sha256': 'audio-b', 'speaker_id': 'speaker-b', 'transcript': 'ब', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/test': [{'audio_sha256': 'audio-c', 'speaker_id': 'speaker-c', 'transcript': 'क', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'sravaani_drafts/train': [{'audio_sha256': 'draft-a', 'transcript': '', 'training_eligible': False, 'experimental_training_eligible': True, 'machine_transcript_quality': {'level': 'high_risk'}}],
            'lexicon/train': [{'form': 'अ', 'provenance': provenance}],
            'instructions/train': [{'instruction': 'a', 'response': 'b', 'provenance': provenance}],
            'instructions/validation': [{'instruction': 'c', 'response': 'd', 'provenance': provenance}],
            'instructions/test': [{'instruction': 'e', 'response': 'f', 'provenance': provenance}],
        }
        for key, content in rows.items():
            config, split = key.split('/')
            name = f'{split}-00000.jsonl'
            write_jsonl(root / 'data' / config / name, content)
            configs[key] = {'files': [name], 'records': len(content), 'shards': 1}
        manifest = {
            'configs': configs,
            'draft_queue_records': 1,
            'draft_records': 1,
            'draft_unique_audio': 1,
            'draft_inherited_duplicate_rows': 0,
            'drafts_complete': True,
            'include_audio': False,
        }
        (root / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        index = {
            'release_id': 'candidate',
            'status': 'integrated_experimental_release',
            'text': {'total': 3, 'splits': {'train': 1, 'validation': 1, 'test': 1}},
            'speech': {
                'total': 3,
                'splits': {'train': 1, 'validation': 1, 'test': 1},
                'strict_comparison_rows': 3,
            },
            'leakage': {'text_hash_cross_split': 0, 'identified_speaker_cross_split': 0},
            'speech_baseline_comparison': {
                'sravaani_draft_rows': 1,
                'sravaani_draft_unique_audio': 1,
                'sravaani_draft_inherited_duplicate_rows': 0,
            },
        }
        return index

    def test_accepts_complete_package_and_reports_draft_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = m.audit(self.fixture(root), root)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['drafts']['empty_transcripts'], 1)
        self.assertIn('metadata_only_audio_paths', report['warnings'])

    def test_rejects_shard_mismatch_and_split_leakage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/text/test-00000.jsonl'
            write_jsonl(path, [{'id': 'text-a', 'text': 'क', 'language': 'gbm'}])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('text IDs overlap across train and test', report['errors'])
        self.assertIn('text/test has 1 rows without provenance', report['errors'])


if __name__ == '__main__':
    unittest.main()
