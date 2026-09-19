import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_release_bundle as m


class ReleaseBundleTests(unittest.TestCase):
    def test_failed_managed_build_preserves_previous_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'bundle'
            output.mkdir()
            marker = output / 'index.json'
            marker.write_text('previous')
            with (
                patch.object(m, 'OUTPUT', output),
                patch.object(m, '_build_at', side_effect=RuntimeError('failed')),
                self.assertRaisesRegex(RuntimeError, 'failed'),
            ):
                m.build(output)
            self.assertEqual(marker.read_text(), 'previous')

    def test_build_refuses_to_delete_existing_custom_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / 'keep.py'
            marker.write_text('keep')
            with self.assertRaisesRegex(ValueError, 'refusing to replace'):
                m.build(root)
            self.assertEqual(marker.read_text(), 'keep')

    def test_verify_detects_modified_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'report.json'
            artifact.write_text('{}\n')
            (root / 'index.json').write_text(json.dumps({
                'release_id': 'garhwali-language-lab-v0.1.0',
                'files': 1,
                'bytes': artifact.stat().st_size,
                'artifacts': [{
                    'path': 'report.json',
                    'bytes': artifact.stat().st_size,
                    'sha256': m.sha256(artifact),
                }],
            }))
            self.assertEqual(m.verify(root, check_sources=False), [])
            artifact.write_text('{"changed":true}\n')
            self.assertIn('size:report.json', m.verify(root, check_sources=False))

    def test_verify_rejects_machine_specific_home_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / 'report.json'
            artifact.write_text('{"path":"/Users/example/private"}\n')
            (root / 'index.json').write_text(json.dumps({
                'release_id': 'garhwali-language-lab-v0.1.0',
                'files': 1,
                'bytes': artifact.stat().st_size,
                'artifacts': [{
                    'path': 'report.json',
                    'bytes': artifact.stat().st_size,
                    'sha256': m.sha256(artifact),
                }],
            }))
            self.assertIn(
                'machine_specific_path:report.json',
                m.verify(root, check_sources=False)
            )

    def test_verify_rejects_unindexed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'secret.txt').write_text('not indexed')
            (root / 'index.json').write_text(json.dumps({
                'release_id': 'garhwali-language-lab-v0.1.0',
                'files': 0, 'bytes': 0, 'artifacts': [],
            }))
            self.assertIn(
                'unindexed:secret.txt', m.verify(root, check_sources=False)
            )

    def test_verify_rejects_index_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'bundle'
            root.mkdir()
            outside = root.parent / 'outside.json'
            outside.write_text('{}\n')
            (root / 'index.json').write_text(json.dumps({
                'release_id': 'garhwali-language-lab-v0.1.0',
                'files': 1,
                'bytes': outside.stat().st_size,
                'artifacts': [{
                    'path': '../outside.json',
                    'bytes': outside.stat().st_size,
                    'sha256': m.sha256(outside),
                }],
            }))
            self.assertIn(
                'unsafe_path:../outside.json',
                m.verify(root, check_sources=False),
            )
