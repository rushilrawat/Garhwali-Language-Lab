import unittest

from reocr_archive_quality_pages import select_targets, tesseract_words


class ReocrArchiveQualityPagesTests(unittest.TestCase):
    def test_selects_only_scoped_empty_or_flagged_pages(self):
        rows = [
            {
                "source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958",
                "pdf_page": 1,
                "ocr_empty": False,
                "candidate_ocr_warning_flags": ["high_digit_ratio"],
            },
            {
                "source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958",
                "pdf_page": 2,
                "ocr_empty": True,
                "candidate_ocr_warning_flags": [],
            },
            {
                "source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958",
                "pdf_page": 3,
                "ocr_empty": False,
                "candidate_ocr_warning_flags": [],
            },
            {
                "source_id": "unrelated_source",
                "pdf_page": 4,
                "ocr_empty": True,
                "candidate_ocr_warning_flags": [],
            },
        ]

        targets = select_targets(rows)

        self.assertEqual([row["pdf_page"] for row in targets], [1, 2])

    def test_reads_word_text_and_confidence_from_tsv(self):
        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\t"
            "top\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t10\t20\t40\t12\t92.5\tनमस्कार\n"
            "5\t1\t1\t1\t1\t2\t55\t20\t40\t12\t80.0\tमित्र\n"
        )

        text, confidences = tesseract_words(tsv)

        self.assertEqual(text, "नमस्कार मित्र")
        self.assertEqual(confidences, [92.5, 80.0])


if __name__ == "__main__":
    unittest.main()
