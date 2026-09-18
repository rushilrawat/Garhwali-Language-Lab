import json
import tempfile
import unittest
from pathlib import Path

import integrate_reocr_evidence as ocr
import integrate_whisper_turbo_evidence as asr


class ReleaseEvidenceTests(unittest.TestCase):
    def test_reocr_requires_two_layouts_and_preserves_original(self):
        evidence = {
            "selected_candidate_index": 0,
            "exact_variant_agreement": 2,
            "original_text": "पुराण पाठ",
            "candidates": [{"text": "पुराना पाठ", "psm": 11,
                            "mean_word_confidence": 90}],
        }
        self.assertEqual(ocr.accepted_candidate(evidence)["text"], "पुराना पाठ")
        evidence["exact_variant_agreement"] = 1
        self.assertIsNone(ocr.accepted_candidate(evidence))

    def test_whisper_integration_does_not_replace_source_transcript(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / "base.jsonl"
            base.write_text(json.dumps({"audio_sha256": "a", "machine_transcript": "मूल"}) + "\n")
            evidence_dir = root / "evaluation"
            cloud = evidence_dir / "low_confidence_whisper_turbo_x" / "cloud_output"
            cloud.mkdir(parents=True)
            (cloud / "predictions.jsonl").write_text(json.dumps({
                "audio_sha256": "a", "whisper_transcript": "दूसर",
                "agreement_wer": 1.0, "agreement_cer": 1.0,
            }) + "\n")
            output = root / "output.jsonl"
            report = asr.run(base, evidence_dir, output, root / "report.json")
            row = json.loads(output.read_text())
            self.assertEqual(row["machine_transcript"], "मूल")
            self.assertEqual(row["independent_asr_evidence"]["transcript"], "दूसर")
            self.assertEqual(report["original_transcripts_changed"], 0)


if __name__ == "__main__":
    unittest.main()
