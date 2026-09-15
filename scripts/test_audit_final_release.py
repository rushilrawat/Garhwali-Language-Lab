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
        provenance = [{
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'iso_639_3': 'gbm',
        }]
        rows = {
            'text/train': [{'id': 'text-a', 'text': 'अ', 'language': 'gbm', 'provenance': provenance}],
            'text/validation': [{'id': 'text-b', 'text': 'ब', 'language': 'gbm', 'provenance': provenance}],
            'text/test': [{'id': 'text-c', 'text': 'क', 'language': 'gbm', 'provenance': provenance}],
            'asr/train': [{'audio': 'audio/audio-a.wav', 'audio_sha256': 'audio-a', 'speaker_id': 'speaker-a', 'transcript': 'अ', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/validation': [{'audio': 'audio/audio-b.wav', 'audio_sha256': 'audio-b', 'speaker_id': 'speaker-b', 'transcript': 'ब', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'asr/test': [{'audio': 'audio/audio-c.wav', 'audio_sha256': 'audio-c', 'speaker_id': 'speaker-c', 'transcript': 'क', 'source': 'VAANI', 'license': 'CC-BY-4.0'}],
            'sravaani_drafts/train': [{'audio': 'audio/draft-a.wav', 'audio_sha256': 'draft-a', 'transcript': '', 'training_eligible': False, 'experimental_training_eligible': True, 'machine_transcript_quality': {'level': 'high_risk'}}],
            'lexicon/train': [{'form': 'अ', 'provenance': provenance}],
            'instructions/train': [{'instruction': 'a', 'response': 'b', 'provenance': provenance}],
            'instructions/validation': [{'instruction': 'c', 'response': 'd', 'provenance': provenance}],
            'instructions/test': [{'instruction': 'e', 'response': 'f', 'provenance': provenance}],
            'catalog/train': [
                {'id': 'text-a', 'text': 'अ', 'sources': provenance},
                {'id': 'text-b', 'text': None, 'redaction_reason': 'rights_pending', 'sources': provenance},
                {'id': 'text-c', 'text': 'क', 'sources': provenance},
            ],
        }
        for key, content in rows.items():
            config, split = key.split('/')
            name = f'{split}-00000.jsonl'
            write_jsonl(root / 'data' / config / name, content)
            configs[key] = {'files': [name], 'records': len(content), 'shards': 1}
        manifest = {
            'release_id': 'candidate',
            'configs': configs,
            'draft_queue_records': 1,
            'draft_records': 1,
            'draft_unique_audio': 1,
            'draft_inherited_duplicate_rows': 0,
            'draft_source_label_conflicts': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_third_checkpoint_records': 0,
            'draft_audio_grounded_review_records': 0,
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
        self.assertIn('audio_not_included', report['warnings'])

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

    def test_requires_every_audio_file_when_audio_is_included(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['include_audio'] = True
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn('4 referenced audio files are missing', report['errors'])

    def test_rejects_source_conflict_as_garhwali_training_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            write_jsonl(path, [{
                'audio_sha256': 'draft-a',
                'transcript': 'বাংলা পাঠ',
                'training_eligible': False,
                'experimental_training_eligible': True,
                'machine_transcript_quality': {'level': 'high_risk'},
                'language_scope_status': 'source_label_conflict',
                'active_for_source_error_analysis': True,
            }])
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 source-label conflict drafts are marked as Garhwali training data',
            report['errors'],
        )

    def test_rejects_unsupported_recovery_accuracy_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['recovery_adjudication'] = {
                'automatic_correction': True,
                'human_reference_available': False,
                'supervised_training_eligible': False,
                'recommended_for_machine_label_training': False,
                'original_transcript_preserved': True,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_three_checkpoint_review_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 recovery adjudications make an unsupported training or accuracy claim',
            report['errors'],
        )

    def test_rejects_calibrated_claim_for_third_checkpoint_score(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['recovery_third_checkpoint'] = {
                'transcript': 'गढ़वळि पाठ',
                'confidence_is_calibrated': True,
                'human_reference_available': False,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_third_checkpoint_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 third-checkpoint records make an unsupported confidence or reference claim',
            report['errors'],
        )

    def test_audio_grounded_review_must_remain_pending_human_listening(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            index = self.fixture(root)
            path = root / 'data/sravaani_drafts/train-00000.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            rows[0]['audio_grounded_review'] = {
                'machine_audio_review_complete': True,
                'human_listening_review_required': False,
                'automatic_correction': False,
                'human_reference_available': False,
                'supervised_training_eligible': False,
                'recommended_for_machine_label_training': False,
                'original_transcript_preserved': True,
            }
            write_jsonl(path, rows)
            manifest_path = root / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['draft_audio_grounded_review_records'] = 1
            manifest_path.write_text(json.dumps(manifest))
            report = m.audit(index, root)
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            '1 audio-grounded reviews make an unsupported completion, training, or accuracy claim',
            report['errors'],
        )


if __name__ == '__main__':
    unittest.main()
