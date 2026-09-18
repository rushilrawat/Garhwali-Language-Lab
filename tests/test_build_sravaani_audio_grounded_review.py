import math
import tempfile
import unittest
import wave
from array import array
from pathlib import Path

import build_sravaani_audio_grounded_review as m


class SraVaaniAudioGroundedReviewTests(unittest.TestCase):
    def test_score_percentile_is_empirical(self):
        self.assertEqual(m.percentile([0.1, 0.2, 0.3, 0.4], 0.3), 0.75)

    def test_calibration_reports_negative_confidence_cer_relation(self):
        rows = [
            {'audio_sha256': 'a', 'machine_transcript': 'क', 'token_confidence_uncalibrated': 0.9},
            {'audio_sha256': 'b', 'machine_transcript': 'x', 'token_confidence_uncalibrated': 0.1},
        ]
        result = m.calibration(rows, {'a': 'क', 'b': 'ख'})
        self.assertEqual(result['records'], 2)
        self.assertLess(result['confidence_to_cer_pearson'], 0)
        self.assertEqual(result['scope'], 'review_ranking_only_not_accuracy_probability')

    def test_waveform_evidence_measures_energy_without_claiming_speech(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'tone.wav'
            samples = array('h', [int(8000 * math.sin(index / 10)) for index in range(16000)])
            with wave.open(str(path), 'wb') as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(16000)
                output.writeframes(samples.tobytes())
            result = m.waveform_evidence(path)
        self.assertEqual(result['sample_rate_hz'], 16000)
        self.assertEqual(result['duration_seconds'], 1.0)
        self.assertGreater(result['energy_active_frame_share'], 0.9)
        self.assertIn('not_speech_or_language_ground_truth', result['interpretation'])

    def test_review_categories_do_not_auto_resolve_faults(self):
        self.assertEqual(
            m.review_category(['empty_transcript'], False),
            'empty_output_requires_new_transcription',
        )
        self.assertEqual(
            m.review_category(['repeated_token_loop'], False),
            'decoder_loop_requires_listening',
        )
        self.assertEqual(
            m.review_category(['frequent_identical_hypothesis'], True),
            'common_short_exact_consensus_requires_spot_check',
        )


if __name__ == '__main__':
    unittest.main()
