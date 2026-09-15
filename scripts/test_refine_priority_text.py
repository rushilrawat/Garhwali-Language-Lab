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
        self.assertNotIn('repeated_punctuation', result['review_signals'])
        self.assertEqual(result['release_text'], 'O… chalun/ hiton maa(n)')
        self.assertIn('double_period_normalized', result['automatic_changes'])

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

    def test_devanagari_marks_count_toward_localization_fragment_length(self):
        result = m.refine_row({
            'text_sha256': 'a1' * 32,
            'text_model': 'जुन',
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['software_localization']},
            'provenance': [{
                'source_id': 'localization',
                'linguistic_metadata': {'english_alignments': ['June']},
                'quality_flags': ['native_accuracy_unverified'],
            }],
        })
        self.assertNotIn('very_short_fragment', result['review_signals'])

    def test_removes_wiki_markup_only_from_flagged_release_text(self):
        result = m.refine_row({
            'text_sha256': '1' * 64,
            'text_model': "'''गढ़वाली''' =भाखा= * पाठ ] }",
            'cleanup_review_flags': ['html_markup', 'mixed_latin_devanagari'],
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['encyclopedia']},
            'provenance': [],
        })
        self.assertEqual(result['release_text'], 'गढ़वाली भाखा पाठ')
        self.assertIn('wiki_markup_removed', result['automatic_changes'])
        self.assertIn('html_markup', result['resolved_cleanup_flags'])
        self.assertIn('mixed_latin_devanagari', result['resolved_cleanup_flags'])
        self.assertEqual(result['remaining_cleanup_flags'], [])
        self.assertEqual(result['quality_refinement_status'], 'mechanically_cleaned')

    def test_does_not_strip_unflagged_apostrophes_or_ellipsis(self):
        text = "हां... 'पाठ'"
        result = m.refine_row({
            'text_sha256': '2' * 64,
            'text_model': text,
            'cleanup_review_flags': [],
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['sentence']},
            'provenance': [],
        })
        self.assertEqual(result['release_text'], text)
        self.assertNotIn('repeated_punctuation', result['review_signals'])

    def test_romanized_source_form_resolves_no_devanagari_as_a_defect(self):
        result = m.refine_row({
            'text_sha256': '8' * 64,
            'text_model': 'mero ghar',
            'cleanup_review_flags': ['no_devanagari'],
            'language_quality': {
                'confidence': 'medium',
                'evidence': ['source_garhwali_label'],
                'review_required': True,
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['lexicon']},
            'provenance': [{'source_id': 'romanized', 'iso_639_3': 'gbm'}],
        })
        self.assertIn('no_devanagari', result['resolved_cleanup_flags'])
        self.assertNotIn('no_devanagari', result['remaining_cleanup_flags'])
        self.assertIn('romanized_text_requires_native_review', result['review_signals'])

    def test_source_attested_transcription_does_not_request_devanagari_rewrite(self):
        result = m.refine_row({
            'text_sha256': 'b1' * 32,
            'text_model': 'hat, hath~',
            'cleanup_review_flags': ['no_devanagari'],
            'language_quality': {
                'status': 'source_attested_garhwali_transcription',
                'confidence': 'high',
                'evidence': ['source_garhwali_label', 'source_linguistic_transcription'],
                'review_required': False,
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['lexicon']},
            'provenance': [{'source_id': 'asjp', 'iso_639_3': 'gbm'}],
        })
        self.assertNotIn('romanized_text_requires_native_review', result['review_signals'])
        self.assertFalse(result['quality_dimensions']['orthography']['native_validation_required'])
        self.assertEqual(
            result['quality_dimensions']['orthography']['status'],
            'source_attested_linguistic_notation',
        )

    def test_source_attested_parallel_example_keeps_alignment_as_published(self):
        result = m.refine_row({
            'text_sha256': 'b2' * 32,
            'text_model': 'ek ləɖki',
            'cleanup_review_flags': ['no_devanagari'],
            'language_quality': {
                'status': 'source_attested_garhwali_transcription',
                'confidence': 'high',
                'evidence': ['source_garhwali_label', 'source_linguistic_transcription'],
                'review_required': False,
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['translated_example']},
            'provenance': [{
                'source_id': 'mamta_southasia_examples',
                'iso_639_3': 'gbm',
                'linguistic_metadata': {'translation': 'one girl'},
            }],
        })
        alignment = result['quality_dimensions']['semantic_alignment']
        self.assertEqual(alignment['status'], 'source_attested_parallel_alignment')
        self.assertFalse(alignment['native_validation_required'])

    def test_source_attested_transcription_slash_is_published_not_scaffolding(self):
        result = m.refine_row({
            'text_sha256': 'b3' * 32,
            'text_model': 'mem/mjɑr pɑs ek bɛɡ čə',
            'cleanup_review_flags': ['no_devanagari'],
            'language_quality': {
                'status': 'source_attested_garhwali_transcription',
                'confidence': 'high',
                'evidence': ['source_garhwali_label', 'source_linguistic_transcription'],
                'review_required': False,
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['translated_example']},
            'provenance': [{
                'source_id': 'mamta_southasia_examples',
                'iso_639_3': 'gbm',
                'linguistic_metadata': {'translation': 'I have one bag.'},
            }],
        })
        self.assertNotIn('slash_separated_variants', result['review_signals'])
        self.assertFalse(result['manual_review_required'])

    def test_long_sentence_with_slash_is_not_treated_as_variant_list(self):
        result = m.refine_row({
            'text_sha256': '3' * 64,
            'text_model': 'स्विम ट्रंक/शॉर्ट्स मर्दों खातिर अलग प्रकार का कपड़ा छन।',
            'language_quality': {'script_profile': {'script': 'Deva'}},
            'genre_quality': {'tags': ['sentence']},
            'provenance': [],
        })
        self.assertNotIn('slash_separated_variants', result['review_signals'])

    def test_quality_dimensions_separate_identity_orthography_and_alignment(self):
        result = m.refine_row({
            'text_sha256': '9' * 64,
            'text_model': 'mero ghar',
            'language_quality': {
                'confidence': 'medium',
                'evidence': ['source_garhwali_label'],
                'review_required': True,
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['translated_example']},
            'provenance': [{
                'source_id': 'example_parallel',
                'iso_639_3': 'gbm',
                'quality_flags': ['native_accuracy_unverified'],
            }],
        })
        dimensions = result['quality_dimensions']
        self.assertEqual(
            dimensions['language_identity']['status'],
            'source_declared_garhwali_pending_native_validation',
        )
        self.assertEqual(
            dimensions['orthography']['status'],
            'romanized_source_form_pending_native_review',
        )
        self.assertEqual(
            dimensions['semantic_alignment']['status'],
            'translation_or_alignment_pending_native_validation',
        )
        self.assertEqual(
            dimensions['source_evidence']['status'],
            'native_accuracy_unverified',
        )
        self.assertEqual(result['review_priority']['rank'], 2)

    def test_multiple_source_ids_are_recorded_as_corroboration_not_accuracy(self):
        result = m.refine_row({
            'text_sha256': '5' * 64,
            'text_model': 'गढ़वाली पाठ',
            'language_quality': {
                'confidence': 'medium',
                'evidence': ['source_garhwali_label'],
                'review_required': False,
                'script_profile': {'script': 'Deva'},
            },
            'genre_quality': {'tags': ['lexicon']},
            'provenance': [
                {'source_id': 'source_a', 'iso_639_3': 'gbm'},
                {'source_id': 'source_b', 'iso_639_3': 'gbm'},
            ],
        })
        evidence = result['quality_dimensions']['source_evidence']
        self.assertEqual(evidence['distinct_source_count'], 2)
        self.assertEqual(evidence['source_ids'], ['source_a', 'source_b'])
        self.assertFalse(evidence['corroboration_is_accuracy_proof'])

    def test_review_queue_keeps_each_unresolved_public_candidate_once(self):
        resolved = m.refine_row({
            'text_sha256': '6' * 64,
            'text_model': 'हां.. ठीक छ।',
            'language_quality': {
                'confidence': 'high', 'review_required': False,
                'evidence': ['source_garhwali_label'],
                'script_profile': {'script': 'Deva'},
            },
            'genre_quality': {'tags': ['prompted_speech']},
            'provenance': [{'source_id': 'clean', 'iso_639_3': 'gbm'}],
        })
        unresolved = m.refine_row({
            'text_sha256': '7' * 64,
            'text_model': 'ma ghar',
            'language_quality': {
                'confidence': 'medium', 'review_required': True,
                'evidence': ['source_garhwali_label'],
                'script_profile': {'script': 'Latn'},
            },
            'genre_quality': {'tags': ['lexicon']},
            'provenance': [{'source_id': 'romanized', 'iso_639_3': 'gbm'}],
        })
        queue = m.build_review_queue([resolved, unresolved, unresolved])
        self.assertEqual([row['text_sha256'] for row in queue], ['7' * 64])


if __name__ == '__main__':
    unittest.main()
