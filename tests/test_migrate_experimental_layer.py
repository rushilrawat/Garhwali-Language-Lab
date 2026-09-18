import json
import tempfile
import unittest
from pathlib import Path

import migrate_experimental_layer as m


class ExperimentalLayerMigrationTests(unittest.TestCase):
    def test_migrates_directory_and_activates_local_experimental_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'quarantine'
            source.mkdir()
            (source / 'rows.jsonl').write_text(json.dumps({
                'record_id': 'one',
                'corpus_layer': 'quarantine',
                'usage': 'provenance_review_only',
                'training_eligible': False,
                'rights_status': 'source_rights_unresolved',
            }) + '\n', encoding='utf-8')

            report = m.migrate(root)

            self.assertFalse(source.exists())
            row = json.loads((root / 'experimental/rows.jsonl').read_text())
            self.assertEqual(report['records'], 1)
            self.assertEqual(row['corpus_layer'], 'experimental')
            self.assertEqual(row['usage'], 'all_data_experimental_user_approved')
            self.assertTrue(row['experimental_training_eligible'])
            self.assertFalse(row['training_eligible'])
            self.assertEqual(row['rights_status'], 'source_rights_unresolved')


if __name__ == '__main__':
    unittest.main()
