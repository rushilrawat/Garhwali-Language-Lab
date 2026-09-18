import unittest

import prepare_audio_normalization as m


class AudioNormalizationTests(unittest.TestCase):
    def test_recommends_gain_toward_target(self):
        result = m.recommend({'rms_dbfs': -26, 'peak_dbfs': -10, 'dc_offset_normalized': 0})
        self.assertEqual(result['recommended_gain_db'], 6)
        self.assertNotIn('projected_clipping', result['flags'])

    def test_flags_gain_that_would_clip(self):
        result = m.recommend({'rms_dbfs': -35, 'peak_dbfs': -0.1, 'dc_offset_normalized': 0.03})
        self.assertIn('projected_clipping', result['flags'])
        self.assertIn('high_dc_offset', result['flags'])

    def test_distribution_interpolates_percentiles(self):
        result = m.distribution([0, 10, 20, None])
        self.assertEqual(result['p50'], 10)
        self.assertEqual(result['min'], 0)
        self.assertEqual(result['max'], 20)


if __name__ == '__main__': unittest.main()
