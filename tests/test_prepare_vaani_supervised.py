import unittest
import json
import tempfile
from pathlib import Path

import prepare_vaani_supervised as m


class VaaniPreparationTests(unittest.TestCase):
    def test_selects_canonical_transcript_and_normalizes_whitespace(self):
        row = {"transcript": "main", "canonical_transcript": "  म्यार\nभाषा  "}
        self.assertEqual(m.selected_transcript(row), "म्यार भाषा")

    def test_falls_back_to_main_transcript(self):
        row = {"transcript": "  मी ठीक छौं ", "canonical_transcript": ""}
        self.assertEqual(m.selected_transcript(row), "मी ठीक छौं")

    def test_detects_bengali_script(self):
        self.assertTrue(m.has_bengali_script("আমি"))
        self.assertFalse(m.has_bengali_script("मी ठीक छौं"))

    def test_quality_decision_preserves_existing_flags(self):
        row = {"quality_flags": ["manual-transcript-review"]}
        decision = m.quality_decision(row, "मी ठीक छौं")
        self.assertFalse(decision["recommended_for_supervised_training"])
        self.assertIn("manual-transcript-review", decision["quality_flags"])

    def test_bengali_row_is_flagged_for_experimental_review(self):
        decision = m.quality_decision({"quality_flags": []}, "আমি")
        self.assertFalse(decision["recommended_for_supervised_training"])
        self.assertIn("bengali-script-under-garhwali-label", decision["quality_flags"])

    def test_supervised_split_comes_from_transcription_release(self):
        row = {"audio_path": "shared.wav", "split": "train"}
        transcription_rows = {"shared.wav": {"split": "test"}}
        self.assertEqual(m.supervised_split(row, transcription_rows), "test")

    def test_untranscribed_preserves_language_and_geographic_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'rows.jsonl'
            path.write_text(json.dumps({
                'audio_path': 'a.wav', 'local_audio_path': 'a.wav', 'audio_sha256': 'abc',
                'duration_seconds': 2.0, 'district': 'TehriGarhwal', 'state': 'Uttarakhand',
                'gender': 'Female', 'speaker_id': 'S1', 'language': 'Garhwali',
                'languages_known': ['Garhwali', 'Hindi'], 'source': 'ARTPARK-IISc/Vaani',
                'config': 'Garhwali', 'license': 'CC-BY-4.0', 'transcript': '',
            }) + '\n')
            row = list(m.untranscribed(path))[0]
            self.assertEqual(row.get('language'), 'Garhwali')
            self.assertEqual(row.get('languages_known'), ['Garhwali', 'Hindi'])
            self.assertEqual(row.get('state'), 'Uttarakhand')
            self.assertEqual(row.get('source'), 'ARTPARK-IISc/Vaani')
            self.assertTrue(row.get('experimental_audio_eligible'))


if __name__ == "__main__":
    unittest.main()
