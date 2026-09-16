import json
import tempfile
import unittest
from pathlib import Path

import ingest_university_research as m


REQUIRED_INSTITUTIONS = {
    "Hemvati Nandan Bahuguna Garhwal University",
    "Doon University",
    "Uttarakhand Open University",
    "Shri Guru Ram Rai University",
    "University of Kashmir",
    "Tokyo University of Foreign Studies",
}


class UniversityResearchIngestionTests(unittest.TestCase):
    def test_catalog_has_primary_institutional_provenance(self):
        catalog = json.loads(m.CATALOG.read_text(encoding="utf-8"))
        rows = [m.validate_record(row) for row in catalog["records"]]
        institutions = {row["institution"] for row in rows}
        self.assertTrue(REQUIRED_INSTITUTIONS <= institutions)
        self.assertGreaterEqual(len(rows), 8)
        self.assertEqual(len(rows), len({row["record_id"] for row in rows}))
        self.assertTrue(all(row["source_url"].startswith("https://") for row in rows))
        self.assertTrue(all(row["visibility"] == "catalogued" for row in rows))

    def test_run_writes_research_context_without_duplicate_payload_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            report = m.run(output=output)
            rows = [json.loads(line) for line in (output / "records.jsonl").read_text().splitlines()]
            self.assertEqual(report["records"], len(rows))
            self.assertEqual(report["hidden_records"], 0)
            self.assertGreaterEqual(report["already_covered_records"], 1)
            self.assertTrue(all(row["ingestion_status"] in m.VALID_STATUSES for row in rows))
            self.assertTrue(all("full text" not in row.get("notes", "").casefold() or row["access_level"] != "metadata_only" for row in rows))


if __name__ == "__main__":
    unittest.main()
