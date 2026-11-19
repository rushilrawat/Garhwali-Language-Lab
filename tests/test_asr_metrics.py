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

    def test_summarizes_duration_length_and_speaker_slices_without_inventing_audio_quality(self):
        rows = [
            {'asr_target_clean': 'एक दो', 'duration_seconds': 2, 'speaker_id': 'spk1'},
            {'asr_target_clean': 'एक दो तीन चार पाँच छह सात आठ नौ दस ग्यारह', 'duration_seconds': 9, 'speaker_id': 'spk2'},
        ]
        scores = [
            {'word_errors': 1, 'reference_words': 2, 'character_errors': 1, 'reference_characters': 4},
            {'word_errors': 2, 'reference_words': 11, 'character_errors': 2, 'reference_characters': 22},
        ]

        report = m.summarize_slices(rows, scores)

        self.assertEqual(report['duration_seconds']['<3s']['records'], 1)
        self.assertEqual(report['duration_seconds']['8-15s']['wer'], 2 / 11)
        self.assertEqual(report['reference_word_count']['11-25']['records'], 1)
        self.assertEqual(report['speaker_id']['spk1']['cer'], 1 / 4)
        self.assertIsNone(report['district'])
        self.assertFalse(report['audio_quality']['available'])

    def test_slice_scorer_rejects_unpaired_rows_and_scores(self):
        with self.assertRaisesRegex(ValueError, 'same number'):
            m.summarize_slices([{'asr_target_clean': 'एक'}], [])

    def test_district_and_audio_quality_slices_appear_only_when_every_row_has_them(self):
        rows = [
            {'asr_target_clean': 'एक', 'district': 'Tehri', 'audio_quality_status': 'clean'},
            {'asr_target_clean': 'दो', 'district': 'Pauri', 'audio_quality_status': 'noisy'},
            {'asr_target_clean': 'तीन', 'district': 'Tehri', 'audio_quality_status': 'clean'},
        ]
        scores = [
            {'word_errors': 0, 'reference_words': 1, 'character_errors': 0, 'reference_characters': 2},
            {'word_errors': 1, 'reference_words': 1, 'character_errors': 2, 'reference_characters': 2},
            {'word_errors': 1, 'reference_words': 1, 'character_errors': 1, 'reference_characters': 3},
        ]

        report = m.summarize_slices(rows, scores)

        self.assertEqual(report['district']['Tehri']['wer'], 1 / 2)
        self.assertEqual(report['district']['Pauri']['records'], 1)
        self.assertEqual(report['audio_quality']['field'], 'audio_quality_status')
        self.assertEqual(report['audio_quality']['groups']['noisy']['cer'], 1.0)
        self.assertIsNone(report['speaker_id'])

        partial = m.summarize_slices([{**rows[0]}, {'asr_target_clean': 'दो'}], scores[:2])
        self.assertIsNone(partial['district'])
        self.assertFalse(partial['audio_quality']['available'])

    def test_placeholder_speaker_ids_are_not_a_slice(self):
        rows = [{'asr_target_clean': 'एक', 'speaker_id': value} for value in ('NA', 'unknown', ' null ', '')]
        scores = [{'word_errors': 0, 'reference_words': 1, 'character_errors': 0, 'reference_characters': 2}] * 4
        self.assertIsNone(m.summarize_slices(rows, scores)['speaker_id'])

    def test_duration_and_length_bucket_edges(self):
        rows = [{'asr_target_clean': ' '.join(['एक'] * words), 'duration_seconds': seconds}
                for seconds, words in ((3, 10), (8, 11), (15, 25), (14.99, 26))]
        scores = [{'word_errors': 0, 'reference_words': 1, 'character_errors': 0, 'reference_characters': 1}] * 4
        report = m.summarize_slices(rows, scores)
        self.assertEqual({label: v['records'] for label, v in report['duration_seconds'].items()},
                         {'3-8s': 1, '8-15s': 2, '15s+': 1})
        self.assertEqual({label: v['records'] for label, v in report['reference_word_count'].items()},
                         {'1-10': 1, '11-25': 2, '26+': 1})

    def test_normalization_strips_danda_and_composes_nukta(self):
        self.assertEqual(m.normalize('गढ़वाली।  भाषा॥'), m.normalize('गढ\u093cवाली भाषा'))
        self.assertEqual(m.score('गढ़वाली भाषा।', 'गढ\u093cवाली भाषा')['wer'], 0)


if __name__ == '__main__': unittest.main()
