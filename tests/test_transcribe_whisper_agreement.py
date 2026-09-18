import unittest

from transcribe_whisper_agreement import row_identity


class WhisperAgreementTests(unittest.TestCase):
    def test_row_identity_prefers_content_hash(self):
        row = {"audio_sha256": "digest", "audio_path": "audio/example.wav"}
        self.assertEqual(row_identity(row), "digest")

    def test_row_identity_falls_back_to_audio_path(self):
        self.assertEqual(row_identity({"audio_path": "audio/example.wav"}),
                         "audio/example.wav")


if __name__ == "__main__":
    unittest.main()
