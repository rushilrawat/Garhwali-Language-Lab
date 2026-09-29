import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ingest_upreti_1894_garhwali as m


class Upreti1894IngestionTests(unittest.TestCase):
    def test_extracts_only_explicitly_identified_garhwali_sayings(self):
        source = '\n'.join([
            '( 38 )',
            'Topala ki topa tapa chaundala ko raja.',
            'A pure Garhwali proverb.',
            '( 143 )',
            'Kumun son ditha Garha son pitha.',
            'Used only in Garhwal regarding injustice.',
            '( 173 )',
            'Kuraaiya apun kamaiya aurana so chumaiya.',
            'This is a Garhwali proverb.',
            '( 300 )',
            'Khani pini gadha raige rauntyalo kumun.',
            'A Garhwali saying.',
            '( 406 )',
            'Kankarba basi gocbba.',
            'A Garhwal proverb.',
        ])

        rows = m.extract_records(source, source_sha256='a' * 64)

        self.assertEqual(len(rows), 5)
        self.assertEqual([row['printed_page'] for row in rows], [38, 143, 173, 300, 406])
        self.assertEqual({row['iso_639_3'] for row in rows}, {'gbm'})
        self.assertEqual({row['script'] for row in rows}, {'Latn'})
        self.assertEqual({row['license_id'] for row in rows}, {'PDM-1.0'})
        self.assertTrue(all(row['english_gloss'] for row in rows))
        self.assertTrue(all(row['rights_status'] == 'rights_assessed_compatible' for row in rows))
        self.assertTrue(all(not row['native_reviewed'] for row in rows))

    def test_requires_every_source_phrase_and_language_evidence(self):
        source = 'Topala ki topa tapa chaundala ko raja. A pure Garhwali proverb.'
        with self.assertRaisesRegex(ValueError, 'missing'):
            m.extract_records(source, source_sha256='a' * 64)

    def test_writes_jsonl_atomically_with_source_checksum(self):
        source = '\n'.join([
            '( 38 )', 'Topala ki topa tapa chaundala ko raja.', 'A pure Garhwali proverb.',
            '( 143 )', 'Kumun son ditha Garha son pitha.', 'Used only in Garhwal regarding injustice.',
            '( 173 )', 'Kuraaiya apun kamaiya aurana so chumaiya.', 'This is a Garhwali proverb.',
            '( 300 )', 'Khani pini gadha raige rauntyalo kumun.', 'A Garhwali saying.',
            '( 406 )', 'Kankarba basi gocbba.', 'A Garhwal proverb.',
        ])
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / 'source.txt'
            output = Path(folder) / 'records.jsonl'
            source_path.write_text(source, encoding='utf-8')

            report = m.ingest_file(
                source_path, output, retrieved_at='2026-09-29',
                expected_source_sha256=None,
            )

            rows = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(report['records'], 5)
        self.assertEqual(report['source_sha256'], m.sha256_bytes(source.encode('utf-8')))
        self.assertEqual(len(rows), 5)
        self.assertEqual(rows[0]['source_snapshot_sha256'], report['source_sha256'])


if __name__ == '__main__':
    unittest.main()
