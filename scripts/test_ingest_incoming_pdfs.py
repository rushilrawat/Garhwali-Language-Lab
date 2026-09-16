import tempfile
import unittest
from pathlib import Path

import ingest_incoming_pdfs as m


class IncomingPdfIngestionTests(unittest.TestCase):
    def test_find_exact_duplicate_ignores_candidate_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "incoming" / "book.pdf"
            duplicate = root / "downloads" / "old-copy.pdf"
            candidate.parent.mkdir()
            duplicate.parent.mkdir()
            candidate.write_bytes(b"same scan")
            duplicate.write_bytes(b"same scan")

            self.assertEqual(
                m.find_exact_duplicate(candidate, [candidate, duplicate]),
                duplicate.resolve(),
            )

    def test_page_record_is_active_even_when_ocr_needs_review(self):
        record = m.page_record(
            source_id="incoming_pdf_example",
            source_pdf=Path("incoming/pdfs/example.pdf"),
            source_sha256="a" * 64,
            page_number=7,
            text="  गढ़वाली   भाषा  ",
            extraction_method="tesseract_hin_eng",
            title="Example",
        )

        self.assertEqual(record["text"], "गढ़वाली भाषा")
        self.assertEqual(record["corpus_layer"], "experimental")
        self.assertEqual(record["usage"], "all_data_experimental_user_approved")
        self.assertTrue(record["experimental_training_eligible"])
        self.assertEqual(record["attribution"], "Example")
        self.assertIn("machine_ocr", record["quality_flags"])
        self.assertIn("needs_native_review", record["quality_flags"])

    def test_embedded_text_is_preferred_when_substantive(self):
        text = "A Syntactic Sketch of Garhwali " * 20
        self.assertTrue(m.has_substantive_embedded_text(text))
        self.assertFalse(m.has_substantive_embedded_text("page 1"))


if __name__ == "__main__":
    unittest.main()
