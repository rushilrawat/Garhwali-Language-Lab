import unittest

from audit_archive_alternate_ocr_overlap import audit_alternates


class ArchiveAlternateOcrOverlapTests(unittest.TestCase):
    def test_reports_exact_and_within_alternate_duplicates_without_text(self):
        text = "Garhwali page text with a sufficiently descriptive phrase."
        alternates = [
            {
                "source_id": "source-a",
                "pdf_page": 12,
                "alternate_ocr_text": text,
            },
            {
                "source_id": "source-b",
                "pdf_page": 17,
                "alternate_ocr_text": text,
            },
        ]

        result = audit_alternates(alternates, [{"text_clean": text}])

        self.assertEqual(result["exact"]["normalized_match_rows"], 2)
        self.assertEqual(result["exact"]["within_archive_duplicate_groups"], 1)
        self.assertNotIn(text, str(result))


if __name__ == "__main__":
    unittest.main()
