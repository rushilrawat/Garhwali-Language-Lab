import tempfile
import unittest
import json
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

    def test_neighboring_json_sidecar_supplies_future_pdf_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            pdf = Path(tmp) / "New Grammar.pdf"
            pdf.write_bytes(b"pdf")
            pdf.with_suffix(".json").write_text(json.dumps({
                "title": "A New Garhwali Grammar",
                "author": "Example Author",
                "publication_year": 2026,
                "genre": "grammar_linguistics",
                "landing_page": "https://example.org/catalog",
                "license_or_rights_statement": "CC BY 4.0",
            }))

            metadata = m.source_metadata_for(pdf)

        self.assertEqual(metadata["source_id"], "incoming_new_grammar")
        self.assertEqual(metadata["title"], "A New Garhwali Grammar")
        self.assertEqual(metadata["author"], "Example Author")
        self.assertEqual(metadata["landing_page"], "https://example.org/catalog")

    def test_sidecar_rights_and_source_fields_reach_page_record(self):
        record = m.page_record(
            source_id="incoming_example",
            source_pdf=Path("incoming/pdfs/example.pdf"),
            source_sha256="a" * 64,
            page_number=1,
            text="गढ़वाली भाषा",
            extraction_method="embedded_pdf_text_layer",
            title="Example",
            source_metadata={
                "download_url": "https://example.org/book.pdf",
                "rights_evidence_url": "https://example.org/rights",
                "license_or_rights_statement": "CC BY 4.0",
            },
        )
        self.assertEqual(record["download_url"], "https://example.org/book.pdf")
        self.assertEqual(record["license_or_rights_statement"], "CC BY 4.0")
        self.assertNotIn("rights_unknown", record["quality_flags"])


if __name__ == "__main__":
    unittest.main()
