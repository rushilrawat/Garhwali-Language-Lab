import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import evaluation_run_manifest as m


class EvaluationRunManifestTests(unittest.TestCase):
    def test_writes_reconciled_prediction_report_and_hash_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            predictions = [{'record_id': 'dev-1', 'hypothesis': 'उत्तर'}]
            report = {
                'run_id': 'fixture-run',
                'evaluation_split': 'dev',
                'evaluation_records': 1,
                'input_sha256': 'a' * 64,
                'selected_rows_sha256': 'b' * 64,
            }
            manifest = m.write_run_artifacts(
                root / 'out', predictions, report,
                config={'split': 'dev', 'decoder': {'beams': 1}},
                model={'id': 'fixture-model', 'revision': 'abc123'},
                runtime={'python': '3.test'},
                code_paths=(),
                git_root=None,
                started_at_utc='2026-09-26T00:00:00+00:00',
            )
            prediction_path = root / 'out' / 'predictions.jsonl'
            report_path = root / 'out' / 'report.json'
            manifest_path = root / 'out' / 'run_manifest.json'
            self.assertEqual(json.loads(prediction_path.read_text()), predictions[0])
            self.assertEqual(json.loads(report_path.read_text()), report)
            self.assertEqual(manifest['status'], 'complete')
            self.assertEqual(manifest['evaluation_split'], 'dev')
            self.assertEqual(manifest['selected_record_count'], 1)
            self.assertEqual(
                manifest['outputs']['predictions.jsonl'],
                hashlib.sha256(prediction_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(
                manifest['outputs']['report.json'],
                hashlib.sha256(report_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(json.loads(manifest_path.read_text()), manifest)

    def test_rejects_prediction_count_mismatch_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'out'
            with self.assertRaisesRegex(ValueError, 'prediction count'):
                m.write_run_artifacts(
                    output,
                    [],
                    {'evaluation_records': 1, 'evaluation_split': 'dev'},
                    config={},
                    code_paths=(),
                    git_root=None,
                )
            self.assertFalse(output.exists())

    def test_rejects_duplicate_prediction_ids_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'out'
            with self.assertRaisesRegex(ValueError, 'duplicate record_id'):
                m.write_run_artifacts(
                    output,
                    [{'record_id': 'same'}, {'record_id': 'same'}],
                    {
                        'evaluation_records': 2,
                        'evaluation_split': 'dev',
                        'selected_record_ids': ['same', 'same'],
                    },
                    config={},
                    code_paths=(),
                    git_root=None,
                )
            self.assertFalse(output.exists())

    def test_config_hash_is_key_order_independent(self):
        left = {'split': 'dev', 'decoder': {'beams': 1, 'sampling': False}}
        right = {'decoder': {'sampling': False, 'beams': 1}, 'split': 'dev'}
        self.assertEqual(m.config_sha256(left), m.config_sha256(right))


if __name__ == '__main__':
    unittest.main()
