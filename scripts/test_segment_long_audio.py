import unittest

import segment_long_audio as m


class SegmentLongAudioTests(unittest.TestCase):
    def test_parse_silence_ends_ignores_unrelated_ffmpeg_output(self):
        output = """
        [silencedetect @ 0x1] silence_start: 11.2
        [silencedetect @ 0x1] silence_end: 12.75 | silence_duration: 1.55
        size=N/A time=00:00:20.00 bitrate=N/A
        [silencedetect @ 0x1] silence_end: 29.5 | silence_duration: 0.8
        """
        self.assertEqual(m.parse_silence_ends(output), [12.75, 29.5])

    def test_segment_bounds_use_silence_and_cover_complete_audio(self):
        bounds = m.build_segment_bounds(
            duration=70.0,
            silence_ends=[18.0, 34.0, 52.0],
            min_seconds=5.0,
            max_seconds=30.0,
        )
        self.assertEqual(bounds, [(0.0, 18.0), (18.0, 34.0), (34.0, 52.0), (52.0, 70.0)])

    def test_segment_bounds_cap_long_regions_without_silence(self):
        bounds = m.build_segment_bounds(
            duration=74.0,
            silence_ends=[],
            min_seconds=5.0,
            max_seconds=30.0,
        )
        self.assertEqual(bounds, [(0.0, 30.0), (30.0, 60.0), (60.0, 74.0)])


if __name__ == '__main__':
    unittest.main()
