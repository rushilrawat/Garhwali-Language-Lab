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
        self.assertIn('duplicate_identity:text/train:1', report['errors'])
