import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_hf_package_cloud as m


class HuggingFaceCloudValidationTests(unittest.TestCase):
    def test_duplicate_identity_fails_and_json_output_is_exact_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/text/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(
                '{"id":"same","text":"अ"}\n{"id":"same","text":"ब"}\n'
            )
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'text/train': {
                    'files': ['train-00000.jsonl'], 'records': 2,
                    'file_sha256': {'train-00000.jsonl': '0' * 64},
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(
            report['run_id'], 'garhwali-hf-all-data-cloud-validation-v0.1'
        )
        self.assertIn('duplicate_identity:text/train:1', report['errors'])
        self.assertIn('file_hash_mismatch:text/train:train-00000.jsonl', report['errors'])

    def test_structured_knowledge_requires_source_quality_and_rights_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text('{"id":"place-a"}\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'knowledge_missing_source_provenance:geography/train:1',
            report['errors'],
        )
        self.assertIn(
            'knowledge_missing_quality_metadata:geography/train:1',
            report['errors'],
        )
        self.assertIn(
            'knowledge_missing_rights_status:geography/train:1',
            report['errors'],
        )

    def test_structured_knowledge_source_id_alone_is_not_traceable_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            row = {
                'id': 'place-a',
                'knowledge_family': 'geography',
                'provenance': [{'source_id': 'source-without-locator'}],
                'quality_metadata': {'review_status': 'not_reviewed'},
                'rights_status': 'not_assessed',
            }
            shard.write_text(json.dumps(row) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                    'file_sha256': {'train-00000.jsonl': m.sha256(shard)},
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertIn(
            'knowledge_untraceable_source_provenance:geography/train:1',
            report['errors'],
        )

    def test_preflight_rejects_inconsistent_training_recommendation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/text/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps({
                'id': 'text-a',
                'text': 'Garhwali context',
                'language': 'mul',
                'source_languages': ['eng', 'gbm'],
                'language_buckets': ['mixed_language'],
                'quality_tiers': ['experimental_review'],
                'quality_flags': [],
                'public_rights_basis': [{'license_id': 'CC-BY-4.0'}],
                'recommended_for_training': True,
            }) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'public',
                'configs': {'text/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertIn('invalid_training_recommendation:text/train:1', report['errors'])

    def test_public_preflight_requires_structured_public_rights_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps({
                'id': 'place-a',
                'knowledge_family': 'geography',
                'provenance': [{'source_id': 'gazetteer'}],
                'quality_metadata': {'review_status': 'not_reviewed'},
                'rights_status': 'not_assessed',
            }) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'public',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(
            report['run_id'], 'garhwali-hf-public-cloud-validation-v0.1'
        )
        self.assertIn('knowledge_missing_public_rights:geography/train:1', report['errors'])
