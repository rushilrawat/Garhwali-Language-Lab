import json
import tempfile
import unittest
from pathlib import Path

from audit_hf_release_continuity import audit_packages


class HuggingFaceReleaseContinuityTests(unittest.TestCase):
    def test_counts_text_kept_in_source_linked_catalog_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / "old"
            new = root / "new"
            (old / "data" / "text").mkdir(parents=True)
            (new / "data" / "text").mkdir(parents=True)
            (new / "data" / "catalog").mkdir(parents=True)
            old_row = {
                "id": "old-segment",
                "text": "garhwali phrase",
                "provenance": [{"source_id": "source-a", "record_id": "a:1"}],
            }
            new_text_row = {"id": "new-segment", "text": "different segment"}
            catalog_row = {
                "id": "parent-a",
                "text": "context garhwali phrase context",
                "content_included": True,
                "text_publicly_available": True,
                "sources": [{"source_id": "source-a", "record_id": "a:1"}],
            }
            write_rows(old / "data" / "text" / "train.jsonl", [old_row])
            write_rows(new / "data" / "text" / "train.jsonl", [new_text_row])
            write_rows(new / "data" / "catalog" / "train.jsonl", [catalog_row])

            report = audit_packages(old, new)

        self.assertEqual(report["old_text_rows_without_same_id_in_new_text"], 1)
        self.assertEqual(report["old_unique_values_exactly_present_in_new_package"], 0)
        self.assertEqual(report["old_unique_values_in_linked_public_catalog_parent"], 1)
        self.assertEqual(report["old_unique_values_unrepresented"], 0)
        self.assertTrue(report["all_old_text_values_represented"])

    def test_flags_a_value_missing_from_all_new_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            old = root / "old"
            new = root / "new"
            (old / "data" / "text").mkdir(parents=True)
            (new / "data" / "text").mkdir(parents=True)
            write_rows(
                old / "data" / "text" / "train.jsonl",
                [{"id": "old", "text": "unrepresented phrase"}],
            )
            write_rows(
                new / "data" / "text" / "train.jsonl",
                [{"id": "new", "text": "other phrase"}],
            )

            report = audit_packages(old, new)

        self.assertEqual(report["old_unique_values_unrepresented"], 1)
        self.assertFalse(report["all_old_text_values_represented"])


def write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
