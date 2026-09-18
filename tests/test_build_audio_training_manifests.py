import unittest

import build_audio_training_manifests as m


class AudioManifestTests(unittest.TestCase):
    def test_enrich_keeps_record_and_adds_quality_flags(self):
        row = {'audio_sha256': 'a', 'quality_flags': ['transcript-review']}
        quality = {'readable': True, 'sample_rate_hz': 16000, 'channels': 1,
                   'sample_width_bytes': 2, 'clipped_sample_share': 0.02,
                   'zero_sample_share': 0.0, 'duration_seconds': 1.0}
        result = m.enrich(row, quality)
        self.assertEqual(result['audio_sha256'], 'a')
        self.assertIn('high_clipping', result['training_quality_flags'])
        self.assertIn('transcript-review', result['training_quality_flags'])

    def test_clean_quality_has_no_added_flag(self):
        quality = {'readable': True, 'sample_rate_hz': 16000, 'channels': 1,
                   'sample_width_bytes': 2, 'clipped_sample_share': 0.0,
                   'zero_sample_share': 0.01, 'duration_seconds': 1.0}
        self.assertEqual(m.quality_flags(quality), [])


if __name__ == '__main__': unittest.main()
