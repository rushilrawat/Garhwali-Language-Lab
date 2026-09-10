import unittest

import build_vaani_corpus_manifests as m


class VaaniCanonicalManifestTests(unittest.TestCase):
    def test_transcription_split_is_preserved_for_shared_audio(self):
        main = {"split": "train", "audio_path": "shared.wav"}
        transcription = {"split": "validation", "transcript": "मी ठीक छौं"}
        merged = m.apply_transcription_metadata(main, transcription)
        self.assertEqual(merged["main_split"], "train")
        self.assertEqual(merged["transcription_split"], "validation")
        self.assertEqual(merged["split"], "validation")


if __name__ == "__main__":
    unittest.main()
