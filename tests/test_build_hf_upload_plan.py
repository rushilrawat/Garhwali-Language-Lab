import json
import tempfile
import unittest
from pathlib import Path

import build_hf_upload_plan as m


class HuggingFaceUploadPlanTests(unittest.TestCase):
    def package(self, root, profile):
        (root / 'data/text').mkdir(parents=True)
        (root / 'data/text/train-00000.jsonl').write_text('{"id":"a"}\n')
        (root / 'README.md').write_text('dataset card\n')
        (root / 'manifest.json').write_text(json.dumps({
            'release_id': 'candidate',
            'profile': profile,
            'include_audio': False,
            'catalog_records': 1,
            'catalog_redacted_text_records': 0,
            'configs': {'text/train': {
                'records': 1, 'files': ['train-00000.jsonl'],
            }},
        }))

    def test_all_data_plan_cannot_be_public(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root, 'all-data')
            with self.assertRaisesRegex(ValueError, 'explicit public profile'):
                m.build(root, 'owner/all-data', 'public')

    def test_unknown_profile_cannot_fail_open_to_public(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root, 'all_data_typo')
            with self.assertRaisesRegex(ValueError, 'explicit public profile'):
                m.build(root, 'owner/all-data', 'public')

    def test_private_plan_is_bound_to_every_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root, 'all-data')
            report = m.build(root, 'owner/all-data', 'private')
        self.assertEqual(report['planned_visibility'], 'private')
        self.assertEqual(report['publication_status'], 'blocked_pending_rights_and_quality_review')
        self.assertEqual(report['files'], 3)
        self.assertEqual(report['records'], 1)
        self.assertEqual(len(report['aggregate_sha256']), 64)

    def test_public_plan_defaults_to_public_dataset_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.package(root, 'public')
            report = m.build(root, visibility='public')
        self.assertEqual(report['target_repo'], 'rushilrawat/garhwali-language-lab')
        self.assertEqual(report['publication_status'], 'ready_after_final_approval')
