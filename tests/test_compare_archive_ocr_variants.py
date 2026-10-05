import unittest

from compare_archive_ocr_variants import compare_pages


class CompareArchiveOcrVariantsTests(unittest.TestCase):
    def test_comparison_keeps_text_out_and_prioritizes_recovery_and_disagreement(self):
        original = [
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 1,
             "text_normalized": "१२३ Garhwali sample"},
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 2,
             "text_normalized": "पुराना पाठ"},
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 4,
             "text_normalized": "same text here"},
        ]
        alternates = [
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 1,
             "alternate_ocr_text": "१२३ Garhwali sample", "mean_word_confidence": 90},
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 2,
             "alternate_ocr_text": "नई अलग सामग्री", "mean_word_confidence": 50},
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 3,
             "alternate_ocr_text": "पहली बार पढ़ा गया", "mean_word_confidence": 80},
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 5,
             "alternate_ocr_text": "", "mean_word_confidence": None},
        ]
        page_map = [
            {"source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958", "pdf_page": 3,
             "section_id": None, "section_assignment": "unreviewed_candidate_map"},
        ]

        report = compare_pages(original, alternates, page_map)
        pages = {row["pdf_page"]: row for row in report["pages"]}

        self.assertEqual(report["summary"]["pages_compared"], 4)
        self.assertTrue(pages[1]["exact_normalized_match"])
        self.assertFalse(pages[1]["text_included"])
        self.assertEqual(pages[2]["manual_inspection_priority"], "high")
        self.assertEqual(pages[3]["manual_inspection_reason"],
                         "alternate recovers text from an empty original OCR page")
        self.assertFalse(pages[5]["original_record_present"])
        self.assertEqual(pages[5]["manual_inspection_priority"], "high")
        self.assertEqual(pages[3]["section_assignment"], "unreviewed_candidate_map")
        self.assertNotIn("text", pages[3])


if __name__ == "__main__":
    unittest.main()
