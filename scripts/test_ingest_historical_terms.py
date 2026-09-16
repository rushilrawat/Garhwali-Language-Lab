import json
import tempfile
import unittest
from pathlib import Path

import ingest_historical_terms as m


class HistoricalTermIngestionTests(unittest.TestCase):
    def test_catalog_is_unique_metadata_with_valid_sources(self):
        catalog = json.loads(m.CATALOG.read_text(encoding="utf-8"))
        source_ids = {source["source_id"] for source in catalog["sources"]}
        rows = [m.validate_term(row, source_ids) for row in catalog["terms"]]
        self.assertEqual(len(rows), 36)
        self.assertEqual(len({row["term_id"] for row in rows}), 36)
        self.assertEqual(len({row["term"].casefold() for row in rows}), 36)
        self.assertGreaterEqual(len({row["term_type"] for row in rows}), 20)
        self.assertTrue(all(not (set(row) & m.FORBIDDEN) for row in rows))

    def test_run_writes_reproducible_metadata_view(self):
        with tempfile.TemporaryDirectory() as directory:
            report = m.run(output=Path(directory))
            records = (Path(directory) / "records.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(report["records"], 36)
            self.assertEqual(len(records), 36)
            self.assertEqual(report["payload_fields_present"], [])
            self.assertEqual(report["status"], "historical_term_metadata_layer_ready")
            self.assertTrue(all("context_en" in json.loads(row) for row in records))


if __name__ == "__main__":
    unittest.main()
