import unittest

import run_whisper_comparison as m


class WhisperComparisonTests(unittest.TestCase):
    def test_select_rows_is_deterministic(self):
        rows = [
            {'audio_sha256': 'b'},
            {'audio_sha256': 'a'},
            {'audio_sha256': 'c'},
        ]
        self.assertEqual(
            [row['audio_sha256'] for row in m.select_rows(rows, 2)],
            ['a', 'b'],
        )

    def test_summarize_scores_micro_averages_error_counts(self):
        scores = [
            {'word_errors': 1, 'reference_words': 2,
             'character_errors': 2, 'reference_characters': 4},
            {'word_errors': 2, 'reference_words': 8,
             'character_errors': 3, 'reference_characters': 6},
        ]
        summary = m.summarize_scores(scores)
        self.assertEqual(summary['wer'], 0.3)
        self.assertEqual(summary['cer'], 0.5)


if __name__ == '__main__':
    unittest.main()
