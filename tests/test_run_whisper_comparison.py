import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from run_whisper_comparison import (
    generation_kwargs,
    make_prediction_row,
    model_weight_sha256,
    resolve_run_id,
)


class RunIdTests(unittest.TestCase):
    def test_generation_config_exposes_greedy_and_bounded_beam_settings(self):
        greedy = generation_kwargs()
        beam = generation_kwargs(num_beams=5)
        self.assertEqual(greedy['num_beams'], 1)
        self.assertEqual(beam['num_beams'], 5)
        self.assertEqual({k: v for k, v in greedy.items() if k != 'num_beams'},
                         {k: v for k, v in beam.items() if k != 'num_beams'})
        with self.assertRaisesRegex(ValueError, 'must be positive'):
            generation_kwargs(num_beams=0)

    def test_prediction_retains_manifest_identity_and_row_metrics(self):
        row = {
            'record_id': 'meta_omni:spk1:n1:s1',
            'audio_sha256': 'a' * 64,
            'source_split': 'dev',
            'split': 'validation',
            'asr_target_clean': 'गढ़वाली वाक्य',
            'source_file': 'data/gbm_Deva/dev.parquet',
            'source_file_sha256': 'f' * 64,
            'transcript_conflict_for_audio': False,
            'duplicate_audio_count': 1,
        }
        metrics = {
            'word_errors': 1, 'reference_words': 2,
            'character_errors': 1, 'reference_characters': 12,
        }

        prediction = make_prediction_row(row, 'गढ़वाली', metrics)

        self.assertEqual(prediction['record_id'], row['record_id'])
        self.assertEqual(prediction['audio_sha256'], row['audio_sha256'])
        self.assertEqual(prediction['source_split'], 'dev')
        self.assertEqual(prediction['split'], 'validation')
        self.assertEqual(prediction['source_file_sha256'], 'f' * 64)
        self.assertFalse(prediction['transcript_conflict_for_audio'])
        self.assertEqual(prediction['duplicate_audio_count'], 1)
        self.assertEqual(prediction['reference'], row['asr_target_clean'])
        self.assertEqual(prediction['hypothesis'], 'गढ़वाली')
        self.assertEqual(prediction['word_errors'], 1)

    def test_preserves_existing_default_run_id(self):
        self.assertEqual(
            resolve_run_id("openai/whisper-tiny"),
            "openai--whisper-tiny-garhwali-speaker-safe-v0.1",
        )

    def test_allows_explicit_label_for_other_evaluation_designs(self):
        self.assertEqual(
            resolve_run_id("openai/whisper-tiny", "whisper-tiny-vaani-open-test-remainder"),
            "whisper-tiny-vaani-open-test-remainder",
        )

    def test_fingerprints_local_weight_file(self):
        with TemporaryDirectory() as temp_dir:
            model_dir = Path(temp_dir)
            payload = b"small test weights"
            (model_dir / "model.safetensors").write_bytes(payload)

            self.assertEqual(
                model_weight_sha256(model_dir), sha256(payload).hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
