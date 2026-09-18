import json
import tempfile
import unittest
from pathlib import Path

import audit_indicbert_cloud_input as m


def record(key, incoming=False):
    provenance = [{"source_pdf": "incoming/pdfs/book.pdf"}] if incoming else []
    return {"segment_sha256": key, "parents": [{"provenance": provenance}]}


class IndicBertCloudInputAuditTests(unittest.TestCase):
    def test_verifies_pdf_coverage_and_split_isolation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = {
                "train": [record("a", True)],
                "validation": [record("b", True)],
                "test": [record("c", True)],
            }
            for split, values in rows.items():
                (root / f"{split}.jsonl").write_text(
                    "".join(json.dumps(value) + "\n" for value in values)
                )
            report = m.run(root, root / "report.json", expected_pdf_segments=3)
        self.assertEqual(report["incoming_pdf_segments_total"], 3)
        self.assertEqual(report["incoming_pdf_test_segments_excluded_from_training"], 1)
        self.assertFalse(any(report["segment_hash_overlap"].values()))

    def test_rejects_cross_split_segment_overlap(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for split in m.SPLITS:
                (root / f"{split}.jsonl").write_text(json.dumps(record("same")) + "\n")
            with self.assertRaisesRegex(ValueError, "overlap"):
                m.run(root, root / "report.json", expected_pdf_segments=0)


if __name__ == "__main__":
    unittest.main()
