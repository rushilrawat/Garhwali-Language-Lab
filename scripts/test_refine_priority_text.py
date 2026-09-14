import unittest

import refine_priority_text as m


class PriorityTextRefinementTests(unittest.TestCase):
    def test_redacts_indian_phone_number_but_preserves_original(self):
        result = m.refine_row({
            'text_sha256': 'a' * 64,
            'text_model': 'Myaar mobile number cha 9818123456.',
            'language_quality': {'script_profile': {'script': 'Latn'}},
            'provenance': [{'source_id': 'example'}],
        })
        self.assertEqual(result['original_text'], 'Myaar mobile number cha 9818123456.')
        self.assertEqual(result['release_text'], 'Myaar mobile number cha <PHONE_NUMBER>.')
        self.assertIn('phone_number_redacted', result['automatic_changes'])
        self.assertIn('contains_phone_number', result['review_signals'])
        self.assertIn('romanized_text_requires_native_review', result['review_signals'])

    def test_flags_variants_editorial_notation_and_punctuation(self):
        result = m.refine_row({
            'text_sha256': 'b' * 64,
            'text_model': 'O.. chalun/ hiton maa(n)',
            'language_quality': {'script_profile': {'script': 'Latn'}},
            'provenance': [],
        })
        self.assertIn('slash_separated_variants', result['review_signals'])
        self.assertIn('editorial_nasal_notation', result['review_signals'])
        self.assertIn('repeated_punctuation', result['review_signals'])
        self.assertEqual(result['automatic_changes'], [])

    def test_flags_short_fragment_and_regional_identity_without_relabeling(self):
        result = m.refine_row({
            'text_sha256': 'c' * 64,
            'text_model': 'Wu',
            'language_quality': {'script_profile': {'script': 'Latn'}},
            'provenance': [],
        })
        self.assertIn('very_short_fragment', result['review_signals'])
        self.assertEqual(result['language_decision'], 'unchanged_pending_native_review')

        regional = m.refine_row({
            'text_sha256': 'd' * 64,
            'text_model': 'Me Kumaon bitik chaoun.',
            'language_quality': {'script_profile': {'script': 'Latn'}},
            'provenance': [],
        })
        self.assertIn('regional_identity_review', regional['review_signals'])
        self.assertEqual(regional['language_decision'], 'unchanged_pending_native_review')

    def test_clean_devanagari_value_is_unchanged(self):
        result = m.refine_row({
            'text_sha256': 'e' * 64,
            'text_model': 'गढ़वाली पाठ।',
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'provenance': [],
        })
        self.assertEqual(result['release_text'], 'गढ़वाली पाठ।')
        self.assertEqual(result['review_signals'], [])
        self.assertFalse(result['manual_review_required'])

    def test_short_lexicon_and_numeral_values_are_not_surface_noise(self):
        lexical = m.refine_row({
            'text_sha256': 'f' * 64,
            'text_model': 'मा',
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['lexicon']},
            'provenance': [],
        })
        numeral = m.refine_row({
            'text_sha256': '0' * 64,
            'text_model': '१२',
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['numeral_lexicon']},
            'provenance': [],
        })
        self.assertNotIn('very_short_fragment', lexical['review_signals'])
        self.assertNotIn('contains_digits', numeral['review_signals'])


if __name__ == '__main__':
    unittest.main()
