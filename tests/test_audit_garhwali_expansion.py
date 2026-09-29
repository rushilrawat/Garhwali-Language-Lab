import json
import tempfile
import unittest
from pathlib import Path

import audit_garhwali_expansion as module


class ExpansionAuditTests(unittest.TestCase):
    def test_counts_new_unique_and_duplicate_garhwali_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / 'old.jsonl'
            new = root / 'new.jsonl'
            old.write_text(json.dumps({'text': 'पहिले पाठ'}) + '\n', encoding='utf-8')
            new.write_text('\n'.join([
                json.dumps({'text_normalized': 'पहिले पाठ', 'iso_639_3': 'gbm', 'language': 'Garhwali', 'license_id': 'PDM-1.0'}),
                json.dumps({'text_normalized': 'नयाँ पाठ', 'iso_639_3': 'gbm', 'language': 'Garhwali', 'license_id': 'CC-BY-SA-4.0'}),
            ]) + '\n', encoding='utf-8')
            report = module.audit({'sample': new}, [old, new])

        self.assertEqual(report['source_rows_with_text'], 2)
        self.assertEqual(report['new_exact_unique_texts'], 2)
        self.assertEqual(report['new_exact_unique_not_in_prior_layers'], 1)
        self.assertEqual(report['new_texts_already_in_prior_layers'], 1)
        self.assertEqual(report['invalid_garhwali_only_rows'], [])

    def test_rejects_missing_workstream_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'missing.jsonl'
            with self.assertRaisesRegex(FileNotFoundError, 'missing'):
                module.audit({'missing': path}, [])


if __name__ == '__main__':
    unittest.main()
