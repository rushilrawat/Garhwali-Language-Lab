import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import ingest_obs_tlf as m


class OpenBibleStoriesIngestionTests(unittest.TestCase):
    def make_archive(self, path, stories=50):
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr(
                'gbm_obs/manifest.yaml',
                "language:\n  identifier: 'gbm'\nrights: 'CC BY-SA 4.0'\n",
            )
            archive.writestr(
                'gbm_obs/LICENSE.md',
                'Creative Commons Attribution-ShareAlike 4.0 International',
            )
            for number in range(1, stories + 1):
                archive.writestr(
                    f'gbm_obs/content/{number:02}.md',
                    f'# {number}. कथा {number}\n\n'
                    '![चित्र](https://example.org/image.jpg)\n\n'
                    'यु गढ़वाळि कथा कु पाठ च।\n\n'
                    '_उत्पत्ति 1:1 बट्टी एक कथा_\n',
                )

    def test_ingests_only_garhwali_story_text_and_keeps_source_rights(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'source.zip'
            output = Path(directory) / 'records.jsonl'
            self.make_archive(archive)

            report = m.ingest_archive(archive, output, retrieved_at='2026-09-28')
            rows = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]

        self.assertEqual(report['records'], 50)
        self.assertEqual(len(rows), 50)
        self.assertEqual(rows[0]['record_id'], 'obs_tlf_gbm_v1:001')
        self.assertEqual(rows[0]['iso_639_3'], 'gbm')
        self.assertEqual(rows[0]['script'], 'Deva')
        self.assertEqual(rows[0]['license_id'], 'CC-BY-SA-4.0')
        self.assertEqual(rows[0]['source_revision'], m.SOURCE_REVISION)
        self.assertTrue(rows[0]['source_archive_sha256'])
        self.assertIn('यु गढ़वाळि कथा कु पाठ च।', rows[0]['text_normalized'])
        self.assertNotIn('https://example.org/image.jpg', rows[0]['text_normalized'])
        self.assertNotIn('उत्पत्ति 1:1', rows[0]['text_normalized'])
        self.assertEqual(rows[0]['source_citation'], 'उत्पत्ति 1:1 बट्टी एक कथा')
        self.assertFalse(rows[0]['native_reviewed'])
        self.assertFalse(rows[0]['training_eligible'])

    def test_rejects_incomplete_archive_without_replacing_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / 'incomplete.zip'
            output = Path(directory) / 'records.jsonl'
            self.make_archive(archive, stories=49)
            output.write_text('keep me\n', encoding='utf-8')

            with self.assertRaisesRegex(ValueError, '50'):
                m.ingest_archive(archive, output)

            self.assertEqual(output.read_text(encoding='utf-8'), 'keep me\n')


if __name__ == '__main__':
    unittest.main()
