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

    def test_corpus_rates_pool_error_counts_not_record_rates(self):
        result = m.score_corpus(
            ['अ', 'एक दो तीन चार'],
            ['', 'एक दो तीन चार'],
            record_ids=['short', 'long'],
        )
        self.assertEqual(result['word_errors'], 1)
        self.assertEqual(result['reference_words'], 5)
        self.assertEqual(result['wer'], 0.2)
        self.assertEqual(result['character_errors'], 1)
        self.assertEqual(result['reference_characters'], 11)
        self.assertAlmostEqual(result['cer'], 1 / 11)
        self.assertEqual(result['scored_records'], 2)
        self.assertEqual(
            [row['wer'] for row in result['per_record_scores']],
            [1, 0],
        )
        self.assertEqual([row['record_id'] for row in result['per_record_scores']], ['short', 'long'])

    def test_blank_hypothesis_is_scored_as_deletions(self):
        result = m.score_corpus(['गढ़वाली भाषा'], [''])
        self.assertEqual(result['word_errors'], 2)
        self.assertEqual(result['character_errors'], len(m.normalize('गढ़वाली भाषा').replace(' ', '')))
        self.assertEqual(result['wer'], 1)
        self.assertEqual(result['cer'], 1)

    def test_empty_reference_is_listed_and_excluded(self):
        result = m.score_corpus(
            ['', 'ठीक छ'], ['noise', 'ठीक छ'], record_ids=['empty', 'valid'],
        )
        self.assertEqual(result['requested_records'], 2)
        self.assertEqual(result['scored_records'], 1)
        self.assertEqual(result['excluded_records'], [{'record_id': 'empty', 'reason': 'empty_reference_after_normalization'}])
        self.assertEqual(result['wer'], 0)
        self.assertEqual(result['cer'], 0)

    def test_corpus_scorer_rejects_mismatched_lengths_and_no_valid_references(self):
        with self.assertRaises(ValueError):
            m.score_corpus(['एक'], [])
        with self.assertRaises(ValueError):
            m.score_corpus([''], ['कुछ'])


if __name__ == '__main__': unittest.main()
