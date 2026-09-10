import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import ingest_open as m


class LegacyIngestionTests(unittest.TestCase):
    def test_missing_author_is_explicit_and_preserves_attribution_gap(self):
        payload = b'123\tgbm\tsample\t\\N\n'
        with patch.object(m, 'fetch', return_value=(payload, {'raw_path': 'x'})):
            row = m.tatoeba()[0]
        self.assertIsNone(row['contributor'])
        self.assertIn('missing_contributor', row['quality_flags'])
        self.assertFalse(row['training_eligible'])

    def test_record_defaults_do_not_promote_unreviewed_material(self):
        row = m.record('x', '1', 'text', 'CC-BY-4.0', m.BY, 'author', {})
        self.assertFalse(row['training_eligible'])


if __name__ == '__main__':
    unittest.main()
