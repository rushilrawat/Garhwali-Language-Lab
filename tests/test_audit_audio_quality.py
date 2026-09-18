import struct
import tempfile
import unittest
import wave
import math
from pathlib import Path

import audit_audio_quality as m


class AudioQualityTests(unittest.TestCase):
    def test_reads_pcm_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.wav"
            samples = [0, 0, 1000, -1000, 32767]
            with wave.open(str(path), "wb") as output:
                output.setnchannels(1); output.setsampwidth(2); output.setframerate(16000)
                output.writeframes(struct.pack("<5h", *samples))
            result = m.audit_wav(path)
            self.assertTrue(result["readable"])
            self.assertEqual(result["sample_rate_hz"], 16000)
            self.assertEqual(result["frames"], 5)
            self.assertEqual(result["zero_sample_share"], 0.4)
            self.assertEqual(result["clipped_sample_share"], 0.2)
            expected_rms = math.sqrt(sum(x*x for x in samples) / len(samples))
            self.assertAlmostEqual(result["rms_amplitude"], expected_rms)
            self.assertAlmostEqual(result["dc_offset_normalized"], sum(samples) / len(samples) / 32768)

    def test_corrupt_file_returns_failure_record(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.wav"
            path.write_bytes(b"bad")
            result = m.audit_wav(path)
            self.assertFalse(result["readable"])
            self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
