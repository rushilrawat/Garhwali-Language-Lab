import json
import tempfile
import unittest
from pathlib import Path

import ingest_literary_people as m


REQUIRED_NAMES = {
    "Maharaja Sudarshan Shah",
    "Kumdanand Bahuguna",
    "Hari Dutt Sharma (Nautiyal)",
    "Atma Ram Gairola",
    "Devendra Dutt Raturi",
    "Suradutt Saklani",
    "Mola Ram",
    "Miya Prem Singh",
    "Hari Dutt Shastri",
    "Hari Krishna Raturi",
    "Vijaya Ram Raturi",
    "Lalit Mohan Thapalyal",
    "Lokesh Nawani",
    "Madan Mohan Duklaan",
    "Chinmay Sayar",
    "Dr. Narendra Gauniyal",
    "Leeladhar Jagudi",
}


class LiteraryPeopleIngestionTests(unittest.TestCase):
    def test_catalog_preserves_every_named_person_and_uncertainty(self):
        catalog = json.loads(m.CATALOG.read_text(encoding="utf-8"))
        source_ids = {source["source_id"] for source in catalog["sources"]}
        rows = [m.validate_person(row, source_ids) for row in catalog["people"]]
        names = {row["canonical_name"] for row in rows}
        self.assertTrue(REQUIRED_NAMES <= names)
        self.assertEqual(len(rows), len({row["person_id"] for row in rows}))
        self.assertTrue(any(row["verification_status"] == "name_uncertain" for row in rows))
        self.assertTrue(all(not (set(row) & m.FORBIDDEN) for row in rows))

    def test_run_writes_a_deduplicated_visible_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = m.run(output=output)
            rows = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
            self.assertEqual(report["records"], len(rows))
            self.assertGreaterEqual(report["records"], 25)
            self.assertEqual(report["status"], "literary_people_catalog_ready")
            self.assertEqual(report["hidden_records"], 0)


if __name__ == "__main__":
    unittest.main()
