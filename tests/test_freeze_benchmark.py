import json
import tempfile
import unittest
from pathlib import Path

import freeze_benchmark as fb


class FreezeBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / 'v0.2-draft'
        self.dir.mkdir()
        (self.dir / 'internal__text.jsonl').write_text('{"a": 1}\n{"a": 2}\n', encoding='utf-8')
        (self.dir / 'manifest.json').write_text(json.dumps({'benchmark_id': 'gb', 'schema_version': '0.2', 'total_records': 2}), encoding='utf-8')
        (self.dir / 'notes.md').write_text('ignored', encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def test_freeze_records_hashes_counts_and_benchmark_identity(self):
        freeze = fb.build_freeze(self.dir, frozen_at='2026-11-10T00:00:00Z')
        self.assertEqual(freeze['file_count'], 2)
        paths = [e['path'] for e in freeze['files']]
        self.assertEqual(paths, ['internal__text.jsonl', 'manifest.json'])
        self.assertEqual(freeze['files'][0]['lines'], 2)
        self.assertEqual(freeze['benchmark']['benchmark_id'], 'gb')
        self.assertEqual(fb.verify_freeze(self.dir, freeze), [])

    def test_freeze_is_deterministic_apart_from_timestamp(self):
        a = fb.build_freeze(self.dir, frozen_at='x')
        b = fb.build_freeze(self.dir, frozen_at='x')
        self.assertEqual(a, b)

    def test_verify_detects_changed_missing_and_unexpected_files(self):
        freeze = fb.build_freeze(self.dir)
        (self.dir / 'internal__text.jsonl').write_text('{"a": 1}\n{"a": 3}\n', encoding='utf-8')
        (self.dir / 'extra.jsonl').write_text('{}\n', encoding='utf-8')
        (self.dir / 'manifest.json').unlink()
        problems = fb.verify_freeze(self.dir, freeze)
        self.assertIn('changed sha256: internal__text.jsonl', problems)
        self.assertIn('unexpected: extra.jsonl', problems)
        self.assertIn('missing: manifest.json', problems)

    def test_cli_writes_default_freeze_file_and_verifies_it(self):
        self.assertEqual(fb.main(['freeze', str(self.dir)]), 0)
        freeze_path = self.dir / fb.FREEZE_FILENAME
        self.assertTrue(freeze_path.exists())
        # The freeze file itself is excluded, so verifying in place still passes.
        self.assertEqual(fb.main(['verify', str(self.dir), str(freeze_path)]), 0)

    def test_empty_directory_is_an_error(self):
        empty = Path(self.tmp.name) / 'empty'
        empty.mkdir()
        with self.assertRaises(ValueError):
            fb.build_freeze(empty)


if __name__ == '__main__':
    unittest.main()
