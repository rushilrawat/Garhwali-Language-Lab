import array
import json
import tempfile
import unittest
import wave
from pathlib import Path

import render_normalized_audio as m


def write_wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(array.array('h', samples).tobytes())


class RenderNormalizedAudioTests(unittest.TestCase):
    def test_renders_gain_to_derived_wav_without_changing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.wav'
            output = root / 'derived.wav'
            original = [-1000, 0, 1000]
            write_wav(source, original)

            result = m.render_wav(source, output, gain_db=6.0206, dc_offset_normalized=0)

            with wave.open(str(source), 'rb') as handle:
                source_samples = list(array.array('h', handle.readframes(3)))
            with wave.open(str(output), 'rb') as handle:
                derived_samples = list(array.array('h', handle.readframes(3)))
            self.assertEqual(source_samples, original)
            self.assertEqual(derived_samples, [-2000, 0, 2000])
            self.assertNotEqual(result['source_sha256'], result['derived_sha256'])

    def test_build_skips_flagged_normalization_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.wav'
            write_wav(source, [-1000, 0, 1000])
            split_dir = root / 'splits'
            split_dir.mkdir()
            (split_dir / 'train.jsonl').write_text(json.dumps({
                'audio_sha256': 'a' * 64,
                'local_audio_path': 'source.wav',
                'speaker_id': 'speaker-1',
                'split': 'train',
            }) + '\n', encoding='utf-8')
            for split in ('validation', 'test'):
                (split_dir / f'{split}.jsonl').write_text('', encoding='utf-8')
            plan = root / 'normalization.jsonl'
            plan.write_text(json.dumps({
                'audio_sha256': 'a' * 64,
                'recommended_gain_db': 2,
                'dc_offset_normalized': 0,
                'flags': ['projected_clipping'],
            }) + '\n', encoding='utf-8')

            report = m.build_derived_audio(split_dir, plan, root / 'out', root=root)

            self.assertEqual(report['rendered'], 0)
            self.assertEqual(report['skipped_flagged'], 1)
            self.assertFalse(any((root / 'out').rglob('*.wav')))

    def test_build_can_render_peak_safe_flagged_review_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.wav'
            write_wav(source, [-10000, 0, 10000])
            split_dir = root / 'splits'
            split_dir.mkdir()
            (split_dir / 'train.jsonl').write_text(json.dumps({
                'audio_sha256': 'a' * 64,
                'local_audio_path': 'source.wav',
                'speaker_id': 'speaker-1',
                'split': 'train',
            }) + '\n', encoding='utf-8')
            for split in ('validation', 'test'):
                (split_dir / f'{split}.jsonl').write_text('', encoding='utf-8')
            plan = root / 'normalization.jsonl'
            plan.write_text(json.dumps({
                'audio_sha256': 'a' * 64,
                'recommended_gain_db': 12,
                'measured_peak_dbfs': -10,
                'target_rms_dbfs': -20,
                'dc_offset_normalized': 0,
                'flags': ['projected_clipping'],
            }) + '\n', encoding='utf-8')

            report = m.build_derived_audio(
                split_dir, plan, root / 'out', root=root, render_flagged_review=True
            )

            review = m.read_jsonl(root / 'out/review_manifest.jsonl')
            self.assertEqual(report['rendered_review'], 1)
            self.assertEqual(review[0]['normalization']['gain_db'], 9)
            self.assertFalse(review[0]['training_eligible'])
            self.assertTrue((root / review[0]['derived_audio_path']).exists())


if __name__ == '__main__':
    unittest.main()
