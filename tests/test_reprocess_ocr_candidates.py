import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import reprocess_ocr_candidates as module


class ReprocessOcrCandidatesTests(unittest.TestCase):
    def test_weakness_prioritizes_corrupt_surface_text(self):
        clean = module.weakness("गढ़वाली भाषा और लोक साहित्य")
        corrupt = module.weakness("गढ़वाली ��� ###")
        self.assertGreater(corrupt, clean)

    def test_choose_candidate_requires_exact_variant_agreement(self):
        candidates = [
            {"text": "एक", "text_sha256": "a", "mean_word_confidence": 80, "confident_word_count": 1},
            {"text": "एक", "text_sha256": "a", "mean_word_confidence": 90, "confident_word_count": 1},
            {"text": "ऐक", "text_sha256": "b", "mean_word_confidence": 95, "confident_word_count": 1},
        ]
        index, agreement = module.choose_candidate(candidates)
        self.assertEqual((index, agreement), (1, 2))

    @patch.object(module, "TESSERACT", "tesseract")
    @patch.object(module.subprocess, "run")
    def test_ocr_variant_requests_tsv_output_explicitly(self, run):
        run.return_value.stdout = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t91.0\tगढ़वाली\n"
        )
        result = module.ocr_variant(Path("page.png"), Path("tessdata"), 6)
        command = run.call_args.args[0]
        self.assertIn("tessedit_create_tsv=1", command)
        self.assertEqual(result["text"], "गढ़वाली")
        self.assertEqual(result["mean_word_confidence"], 91.0)

    @patch.object(module, "locate_tessdata", return_value=Path("tessdata"))
    @patch.object(module, "render_page")
    @patch.object(module, "ocr_variant")
    def test_run_resumes_without_duplicate_records(self, ocr, render, locate):
        ocr.return_value = {"psm": 3, "text": "गढ़वाली", "mean_word_confidence": 90,
                            "confident_word_count": 1, "text_sha256": "hash"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            source = root / "input.jsonl"
            rows = [
                {"record_id": "a", "source_id": "s", "source_pdf": "a.pdf", "pdf_page": 1,
                 "text": "एक", "text_sha256": "one", "extraction_method": "tesseract_hin_eng"},
                {"record_id": "b", "source_id": "s", "source_pdf": "a.pdf", "pdf_page": 2,
                 "text": "दो", "text_sha256": "two", "extraction_method": "tesseract_hin_eng"},
            ]
            source.write_text("".join(json.dumps(row) + "\n" for row in rows))
            output = root / "output"
            output.mkdir()
            existing = {"record_id": "a", "exact_variant_agreement": 1}
            (output / "candidates.jsonl").write_text(json.dumps(existing) + "\n")
            with patch.object(module, "ROOT", root):
                report = module.run(source, output, 2, 300, (3,))
            saved = list(module.read_jsonl(output / "candidates.jsonl"))
            self.assertEqual([row["record_id"] for row in saved], ["a", "b"])
            self.assertEqual(report["resumed_from_pages"], 1)
            self.assertEqual(ocr.call_count, 1)


if __name__ == "__main__":
    unittest.main()
