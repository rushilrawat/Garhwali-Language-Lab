from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_archive_intake_quality import profile_ocr, profile_text, read_ocr_records


class ArchiveIntakeQualityTests(unittest.TestCase):
    def test_script_profile_distinguishes_scripts_without_claiming_language(self):
        dev = profile_text("गढ़वाली भाषा और लोकगीत")
        latin = profile_text("Garhwali language and folk songs")
        mixed = profile_text("Garhwali भाषा")

        self.assertEqual(dev["script_profile"], "mostly_devanagari")
        self.assertEqual(latin["script_profile"], "mostly_latin")
        self.assertEqual(mixed["script_profile"], "mixed_devanagari_latin")

    def test_ocr_warning_flags_are_signals_and_preserve_counts(self):
        result = profile_text("abc\ufffd\x01 11111 !!!!\u200c")

        self.assertEqual(result["replacement_characters"], 1)
        self.assertEqual(result["control_characters"], 1)
        self.assertIn("replacement_character", result["warning_flags"])
        self.assertIn("control_character", result["warning_flags"])
        self.assertIn("high_digit_ratio", result["warning_flags"])
        self.assertEqual(result["orthographic_joiners"], 1)
        self.assertNotIn("unexpected_unicode_format_character", result["warning_flags"])

    def test_profile_ocr_counts_empty_exact_duplicates_and_review_flags(self):
        records = [
            {"path": Path("a.jsonl"), "row": {"source_id": "book-a", "text": "Garhwali", "text_sha256": "same", "record_id": "1", "training_eligible": False, "language": "Hindi OCR"}},
            {"path": Path("a.jsonl"), "row": {"source_id": "book-a", "text": "Garhwali", "text_sha256": "same", "record_id": "2", "training_eligible": False, "language": "Hindi OCR"}},
            {"path": Path("b.jsonl"), "row": {"source_id": "book-b", "text": "", "text_sha256": "empty", "record_id": "3", "training_eligible": False, "language": "unlabeled"}},
        ]

        result = profile_ocr(records)

        self.assertEqual(result["records"], 3)
        self.assertEqual(result["exact_unique_texts"], 2)
        self.assertEqual(result["exact_duplicate_text_rows_within_intake"], 1)
        self.assertEqual(result["empty_text_rows"], 1)
        self.assertEqual(result["missing_record_id_rows"], 0)
        self.assertEqual(result["missing_source_id_rows"], 0)
        self.assertEqual(result["missing_text_hash_rows"], 0)
        self.assertEqual(result["sources"]["book-a"]["training_eligible_true"], 0)
        self.assertEqual(result["sources"]["book-a"]["language_labels"], {"Hindi OCR": 2})
        self.assertIn("does not identify Garhwali versus Hindi", result["language_classification_note"])

    def test_read_ocr_records_reports_bad_json_and_reads_valid_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "data/extracted/research/internet_archive_language_studies_2026-10-03"
            directory.mkdir(parents=True)
            (directory / "pages.jsonl").write_text(
                json.dumps({"text": "Garhwali", "source_id": "book-a"}) + "\n{bad json\n",
                encoding="utf-8",
            )

            records, errors = read_ocr_records(root)

        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 1)
        self.assertIn("pages.jsonl:2", errors[0])


if __name__ == "__main__":
    unittest.main()
