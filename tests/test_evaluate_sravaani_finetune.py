import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

import evaluate_sravaani_finetune as m


class Hypothesis:
    text = "  गढ़वाली पाठ  "


class SraVaaniFineTuneEvaluationTests(unittest.TestCase):
    def test_hypothesis_text_supports_string_and_nemo_object(self):
        self.assertEqual(m.hypothesis_text("  पाठ "), "पाठ")
        self.assertEqual(m.hypothesis_text(Hypothesis()), "गढ़वाली पाठ")

    def test_scores_are_micro_averaged(self):
        result = m.summarize_scores([
            {"word_errors": 1, "reference_words": 2, "character_errors": 2, "reference_characters": 4},
            {"word_errors": 2, "reference_words": 8, "character_errors": 3, "reference_characters": 6},
        ])
        self.assertEqual(result["wer"], 0.3)
        self.assertEqual(result["cer"], 0.5)

    def test_manifest_and_archive_must_match_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"audio_filepath": "a.wav", "text": "पाठ"}) + "\n")
            rows = m.read_manifest(manifest)
            archive = root / "audio.tar"
            payload = b"RIFF"
            with tarfile.open(archive, "w") as tar:
                info = tarfile.TarInfo("a.wav")
                info.size = len(payload)
                tar.addfile(info, io.BytesIO(payload))
            output = root / "audio"
            m.extract_audio(archive, output, {row["audio_filepath"] for row in rows})
            self.assertEqual((output / "a.wav").read_bytes(), payload)


if __name__ == "__main__":
    unittest.main()
