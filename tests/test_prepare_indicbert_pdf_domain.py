import json
import tempfile
import unittest
from pathlib import Path

import prepare_indicbert_pdf_domain as m


class PdfDomainInputTests(unittest.TestCase):
    def test_filters_pdf_rows_and_does_not_write_test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incoming, output = root / "input", root / "output"
            incoming.mkdir()
            for split in ("train", "validation", "test"):
                rows = [
                    {
                        "segment_sha256": f"{split}-pdf",
                        "parents": [{"provenance": [{"source_pdf": "incoming/pdfs/book.pdf"}]}],
                    },
                    {"segment_sha256": f"{split}-web", "parents": []},
                ]
                (incoming / f"{split}.jsonl").write_text(
                    "".join(json.dumps(row) + "\n" for row in rows)
                )
            report = m.run(incoming, output)
            self.assertEqual(report["records"], {"train": 1, "validation": 1, "test": 1})
            self.assertFalse((output / "test.jsonl").exists())
            self.assertEqual(report["test_records_written"], 0)


if __name__ == "__main__":
    unittest.main()
