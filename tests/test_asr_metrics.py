import unittest

import asr_metrics as m


class AsrMetricTests(unittest.TestCase):
    def test_normalization_ignores_case_and_punctuation(self):
        self.assertEqual(m.normalize('Hello,  गढ़वाली।'), 'hello गढ़वाली')

    def test_error_rates(self):
        result = m.score('म्यार भाषा छ', 'म्यार भासा छ')
        self.assertEqual(result['word_errors'], 1)
        self.assertEqual(result['reference_words'], 3)
        self.assertAlmostEqual(result['wer'], 1/3)
        self.assertGreater(result['cer'], 0)

    def test_exact_match_is_zero(self):
        result = m.score('गढ़वाली भाषा', 'गढ़वाली भाषा')
        self.assertEqual(result['wer'], 0)
        self.assertEqual(result['cer'], 0)


if __name__ == '__main__': unittest.main()
