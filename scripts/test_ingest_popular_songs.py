import json
import tempfile
import unittest
from pathlib import Path

import ingest_popular_songs as m


class PopularSongIngestionTests(unittest.TestCase):
    def test_catalog_is_garhwali_youtube_metadata_without_lyric_payloads(self):
        catalog = json.loads(m.CATALOG.read_text(encoding='utf-8'))
        rows = [m.validate_song(row) for row in catalog['songs']]
        self.assertEqual(len(rows), 30)
        self.assertGreaterEqual(
            sum('Narendra Singh Negi' in row['artists'] for row in rows), 21
        )
        self.assertTrue(all(row['language'] == 'Garhwali' for row in rows))
        self.assertTrue(all(row['youtube_video_id'] for row in rows))
        self.assertTrue(all('lyrics_text' not in row for row in rows))
        self.assertTrue(all('translation_text' not in row for row in rows))

    def test_run_writes_complete_deduplicated_catalog_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = m.run(output=output)
            rows = [
                json.loads(line)
                for line in (output / 'records.jsonl').read_text().splitlines()
            ]
            self.assertEqual(report['records'], 30)
            self.assertEqual(len(rows), 30)
            self.assertEqual(len({row['record_id'] for row in rows}), 30)
            self.assertEqual(len({row['youtube_video_id'] for row in rows}), 30)
            self.assertEqual(report['public_caption_checks'], 6)
            self.assertEqual(report['records_with_lyrics_source'], 5)
            self.assertEqual(report['records_with_translation_source'], 3)
            self.assertEqual(report['audio_downloaded'], 0)


if __name__ == '__main__':
    unittest.main()
