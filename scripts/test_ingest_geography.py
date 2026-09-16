import json
import tempfile
import unittest
from pathlib import Path

import ingest_geography as m


class GeographyIngestionTests(unittest.TestCase):
    def test_catalog_is_garhwal_only_metadata(self):
        catalog = json.loads(m.CATALOG.read_text(encoding="utf-8"))
        rows = [m.validate_place(row) for row in catalog["places"]]
        self.assertEqual(len(rows), 50)
        self.assertEqual(len({row["record_id"] for row in rows}), 50)
        self.assertEqual(len({row["name"].casefold() for row in rows}), 50)
        self.assertTrue(all(row["division"] == "Garhwal" for row in rows))
        self.assertTrue(all(row["coordinates"] is None for row in rows))
        self.assertTrue(all("text" not in row for row in rows))

    def test_run_writes_map_and_wikipedia_pointers(self):
        with tempfile.TemporaryDirectory() as directory:
            report = m.run(output=Path(directory))
            rows = [
                json.loads(line)
                for line in (Path(directory) / "records.jsonl").read_text().splitlines()
            ]
            self.assertEqual(report["records"], 50)
            self.assertEqual(report["settlements"], 36)
            self.assertEqual(report["natural_and_cultural_features"], 14)
            self.assertEqual(report["coordinates_present"], 0)
            self.assertTrue(all(row["wikipedia_url"].startswith("https://en.wikipedia.org/wiki/") for row in rows))
            self.assertTrue(all(row["osm_search_url"].startswith("https://www.openstreetmap.org/search?query=") for row in rows))


if __name__ == "__main__":
    unittest.main()
