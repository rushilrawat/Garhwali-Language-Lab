import unittest

import tag_language_quality as m


class LanguageQualityTests(unittest.TestCase):
    def test_script_profile_marks_real_mixed_script(self):
        result = m.script_profile('गढ़वाली abc')
        self.assertEqual(result['script'], 'Mixed-Deva-Latn')
        self.assertEqual(result['counts']['devanagari'], 7)
        self.assertEqual(result['counts']['latin'], 3)

    def test_romanized_garhwali_is_not_assumed_to_be_english(self):
        result = m.assess_language('Mi theek cha.', [
            {'iso_639_3': 'gbm', 'script': 'Latn', 'source_id': 'languageshome'}])
        self.assertEqual(result['status'], 'romanized_garhwali_candidate')
        self.assertIn('source_garhwali_label', result['evidence'])
        self.assertTrue(result['review_required'])
        self.assertIn('romanized_spelling_unverified', result['review_reasons'])

    def test_published_linguistic_transcription_keeps_source_notation(self):
        result = m.assess_language('hat, hath~', [{
            'iso_639_3': 'gbm',
            'script': 'ASJPcode',
            'source_id': 'asjp',
            'genre': 'lexicon',
        }])
        self.assertEqual(result['status'], 'source_attested_garhwali_transcription')
        self.assertEqual(result['confidence'], 'high')
        self.assertFalse(result['review_required'])
        self.assertIn('source_linguistic_transcription', result['evidence'])
        self.assertEqual(m.language_bucket(result), 'garhwali_candidate')

    def test_mixed_language_scope_requires_review(self):
        result = m.assess_language('गढ़वाली और हिंदी', [
            {'iso_639_3': 'mul', 'language_scope': 'Garhwali and Hindi'}])
        self.assertEqual(result['status'], 'mixed_language_source')
        self.assertIn('source_declares_mixed_language', result['review_reasons'])

    def test_explicit_english_source_is_not_called_romanized_garhwali(self):
        result = m.assess_language('Garhwal district history', [{'iso_639_3': 'eng'}])
        self.assertEqual(result['status'], 'non_garhwali_source_language')
        self.assertIn('source_language_is_not_garhwali', result['review_reasons'])

    def test_source_language_mixed_flag_requires_review(self):
        result = m.assess_language('गढ़वाली पाठ', [{
            'iso_639_3': 'gbm', 'quality_flags': ['language_mixed']}])
        self.assertEqual(result['status'], 'mixed_language_source')
        self.assertIn('source_flags_language_mixing', result['review_reasons'])

    def test_language_confidence_accounts_for_source_uncertainty(self):
        verified = m.assess_language('गढ़वाली पाठ', [{'iso_639_3': 'gbm'}])
        uncertain = m.assess_language('गढ़वाली पाठ', [{
            'iso_639_3': 'gbm', 'quality_flags': ['source_lineage_missing']}])
        self.assertEqual(verified.get('confidence'), 'high')
        self.assertEqual(uncertain.get('confidence'), 'medium')

    def test_clean_source_evidence_is_not_downgraded_by_uncertain_duplicate(self):
        result = m.assess_language('मि ठीक छौं।', [
            {'iso_639_3': 'gbm', 'source_id': 'tatoeba'},
            {
                'iso_639_3': 'gbm',
                'source_id': 'mirror',
                'quality_flags': ['source_lineage_missing'],
            },
        ])
        self.assertEqual(result['confidence'], 'high')

    def test_medium_language_confidence_enters_review_queue(self):
        self.assertTrue(m.needs_confidence_review({'confidence': 'medium'}))
        self.assertFalse(m.needs_confidence_review({'confidence': 'high'}))

    def test_language_bucket_separates_mixed_and_context_records(self):
        self.assertEqual(m.language_bucket({'status': 'garhwali_candidate'}),
                         'garhwali_candidate')
        self.assertEqual(m.language_bucket({'status': 'mixed_language_source'}),
                         'mixed_language')
        self.assertEqual(m.language_bucket({'status': 'non_garhwali_source_language'}),
                         'non_garhwali_context')
        self.assertEqual(m.language_bucket({'status': 'mixed_script_review'}),
                         'review')

    def test_genre_prefers_explicit_metadata_and_has_source_fallback(self):
        explicit = m.infer_genres([{'genre': 'lexicon', 'file': 'corpus/asjp.jsonl'}])
        inferred = m.infer_genres([{'file': 'data/extracted/folklore/book.jsonl'}])
        self.assertEqual(explicit['tags'], ['lexicon'])
        self.assertEqual(explicit['evidence'], 'explicit_source_metadata')
        self.assertEqual(inferred['tags'], ['folk_literature'])

    def test_cultural_reference_genre_retains_subgenres(self):
        result = m.infer_genres([{
            'file': 'extracted/historical/cultural_references.jsonl',
            'linguistic_metadata': {'cultural_genres': ['ritual_religion', 'performance']},
        }])
        self.assertEqual(result['tags'], ['cultural_reference'])
        self.assertEqual(result['subgenres'], ['performance', 'ritual_religion'])

    def test_dialect_labels_remain_separate_from_geography(self):
        result = m.dialect_evidence([
            {'dialect': 'Srinagar', 'district': 'TehriGarhwal'},
            {'district': 'Uttarkashi'},
        ])
        self.assertEqual(result['dialect_labels'], ['Srinagar'])
        self.assertEqual(result['geographic_hints'], ['TehriGarhwal', 'Uttarkashi'])
        self.assertEqual(result['status'], 'explicit_label')
        unlabeled = m.dialect_evidence([{'district': 'TehriGarhwal'}])
        self.assertEqual(unlabeled['status'], 'unlabeled')

    def test_unlabeled_speech_is_prioritized_for_dialect_review(self):
        row = {'genre_quality': {'tags': ['speech_transcript']},
               'dialect_quality': {'status': 'unlabeled'}}
        self.assertTrue(m.needs_dialect_review(row))
        row['dialect_quality']['status'] = 'explicit_label'
        self.assertFalse(m.needs_dialect_review(row))

    def test_audio_tag_does_not_infer_dialect_from_district(self):
        result = m.tag_audio_record({
            'audio_sha256': 'abc', 'language': 'Garhwali', 'district': 'TehriGarhwal',
            'speaker_id': 'NA', 'gender': 'Female', 'languages_known': ['Garhwali', 'Hindi'],
            'asr_target_clean': 'मी ठीक छौं',
        })
        self.assertEqual(result['speaker_metadata']['status'], 'unidentified')
        self.assertEqual(result['dialect_quality']['status'], 'unlabeled')
        self.assertEqual(result['dialect_quality']['geographic_hints'], ['TehriGarhwal'])

    def test_untranscribed_audio_uses_source_language_label(self):
        result = m.tag_audio_record({
            'audio_sha256': 'abc', 'language': 'Garhwali', 'district': 'Uttarkashi',
            'speaker_id': 'S1', 'selected_transcript': '',
        })
        self.assertEqual(result['language_quality']['status'], 'source_labeled_garhwali_audio')
        self.assertFalse(result['language_quality']['review_required'])

    def test_text_tag_combines_quality_dimensions(self):
        row = {'text_sha256': 'abc', 'text_model': 'कुकुर', 'provenance': [{
            'iso_639_3': 'gbm', 'genre': 'thematic_lexicon', 'dialect': 'Srinagar'}]}
        result = m.tag_text_record(row)
        self.assertEqual(result['language_quality']['status'], 'garhwali_candidate')
        self.assertEqual(result['genre_quality']['tags'], ['thematic_lexicon'])
        self.assertEqual(result['dialect_quality']['dialect_labels'], ['Srinagar'])

    def test_lexicon_candidate_retains_gloss_and_domain(self):
        row = {'text_sha256': 'abc', 'text_model': 'कुकुर', 'genre_quality': {
            'tags': ['thematic_lexicon']}, 'language_quality': {'status': 'garhwali_candidate'},
            'provenance': [{'record_id': 'word:1', 'source_id': 'words', 'linguistic_metadata': {
                'english_gloss': 'dog', 'semantic_domain': 'animal'}}]}
        result = m.lexicon_candidate(row)
        self.assertEqual(result['glosses']['english'], ['dog'])
        self.assertEqual(result['semantic_domains'], ['animal'])

    def test_lexicon_candidate_derives_chan_numeric_parameter_gloss(self):
        row = {
            'text_sha256': 'abc', 'text_model': 'chār',
            'genre_quality': {'tags': ['historical_lexicon']},
            'language_quality': {'status': 'source_attested_garhwali_transcription'},
            'provenance': [{
                'source_id': 'chan_numerals_garhwali',
                'linguistic_metadata': {'parameter_id': '4'},
            }],
        }
        result = m.lexicon_candidate(row)
        self.assertEqual(result['glosses']['english'], ['4'])

    def test_lexicon_candidate_does_not_guess_lsi_gloss_from_slug(self):
        row = {
            'text_sha256': 'abc', 'text_model': 'form',
            'genre_quality': {'tags': ['historical_lexicon']},
            'language_quality': {'status': 'source_attested_garhwali_transcription'},
            'provenance': [{
                'source_id': 'lsi_cldf_garhwali',
                'linguistic_metadata': {'parameter_id': '62_ofafather'},
            }],
        }
        self.assertEqual(m.lexicon_candidate(row)['glosses']['english'], [])

    def test_parallel_entries_expand_multiple_english_alignments(self):
        row = {'text_sha256': 'abc', 'text_model': 'भासा', 'provenance': [{
            'record_id': 'translation:1', 'source_id': 'translatewiki',
            'linguistic_metadata': {'english_alignments': ['Language', 'Languages']}}]}
        result = m.parallel_entries(row)
        self.assertEqual([item['english'] for item in result], ['Language', 'Languages'])
        self.assertTrue(all(item['garhwali'] == 'भासा' for item in result))

    def test_parallel_entries_skip_missing_and_duplicate_english_across_sources(self):
        row = {'text_sha256': 'abc', 'text_model': 'भासा', 'provenance': [
            {'source_id': 'a', 'license': 'CC-BY-4.0',
             'linguistic_metadata': {'translation': '  Language ', 'english_prompt': ''}},
            {'source_id': 'b', 'linguistic_metadata': {'parallel_english': ['Language', None, 'Tongue']}},
            {'source_id': 'c'},
        ]}
        result = m.parallel_entries(row)
        self.assertEqual([(item['english'], item['source_id']) for item in result],
                         [('Language', 'a'), ('Tongue', 'b')])
        self.assertEqual(result[0]['license'], 'CC-BY-4.0')
        self.assertEqual(len({item['pair_sha256'] for item in result}), 2)

    def test_grammar_source_candidate_requires_a_grammar_genre(self):
        row = {'text_sha256': 'abc', 'text_model': 'व्याकरण',
               'genre_quality': {'tags': ['academic_thesis', 'prose']}}
        self.assertEqual(m.grammar_source_candidate(row)['genres'], ['academic_thesis', 'prose'])
        self.assertIsNone(m.grammar_source_candidate({**row, 'genre_quality': {'tags': ['prose']}}))
        self.assertIsNone(m.lexicon_candidate({**row, 'genre_quality': {'tags': ['prose']}}))





class SourceLabelMatchingTests(unittest.TestCase):
    """Free-text labels that only mention Garhwali must not count as Garhwali labels."""

    DEVANAGARI = 'गढ़वाल का इतिहास बहुत पुराना है'

    def test_label_language_uses_real_ingest_strings(self):
        cases = {
            'Garhwali': 'garhwali',
            'Garhwali; mixed Hindi/English glosses possible': 'garhwali',
            'multilingual Garhwali-focused research source': 'garhwali',
            'garhwali_focused_mixed_reference': 'garhwali',
            'Kumaoni/Garhwali': 'mixed',
            'Hindi OCR; regional history reference, not verified Garhwali text': 'other',
            'English OCR; botanical reference, vernacular Garhwali labels not confirmed': 'other',
            'Hindi/regional historical OCR; Garhwali not individually confirmed': 'other',
            'Hindi language reference concerning Garhwali; page-level language requires review': 'other',
            'English historical reference; page explicitly mentions Garhwal/Garhwali': 'other',
            'non-Garhwali': 'other',
            'upstream-labeled; not independently language-reviewed': 'unspecified',
        }
        for label, expected in cases.items():
            with self.subTest(label=label):
                self.assertEqual(m.label_language(label), expected)

    def test_negated_garhwali_language_is_not_a_garhwali_candidate(self):
        result = m.assess_language(self.DEVANAGARI, [{
            'language': 'Hindi OCR; regional history reference, not verified Garhwali text',
        }])
        self.assertEqual(result['status'], 'non_garhwali_source_language')
        self.assertTrue(result['review_required'])

    def test_topic_only_scope_needs_review(self):
        result = m.assess_language(self.DEVANAGARI, [{
            'language_scope': 'Hindi language reference concerning Garhwali; page-level language requires review',
        }])
        self.assertEqual(result['status'], 'garhwali_scope_unverified')
        self.assertNotEqual(result['confidence'], 'high')

    def test_underscore_mixed_scope_is_detected(self):
        result = m.assess_language(self.DEVANAGARI, [{
            'language': 'Garhwali', 'language_scope': 'garhwali_focused_mixed_reference',
        }])
        self.assertEqual(result['status'], 'mixed_language_source')

    def test_two_language_label_is_mixed(self):
        result = m.assess_language(self.DEVANAGARI, [{'language': 'Kumaoni/Garhwali'}])
        self.assertEqual(result['status'], 'mixed_language_source')

    def test_plain_garhwali_label_is_unchanged(self):
        result = m.assess_language(self.DEVANAGARI, [{'language': 'Garhwali'}])
        self.assertEqual((result['status'], result['confidence']), ('garhwali_candidate', 'high'))


class ContentMarkerTests(unittest.TestCase):
    def test_hindi_sentence_with_garhwali_label_goes_to_review(self):
        result = m.assess_language('मैं घर जा रहा हूँ और वह भी आएगा, यह सच है', [{'iso_639_3': 'gbm'}])
        self.assertEqual(result['status'], 'garhwali_candidate')
        self.assertEqual(result['confidence'], 'medium')
        self.assertIn('hindi_function_words_dominant', result['review_reasons'])
        self.assertTrue(result['review_required'])

    def test_garhwali_sentence_keeps_high_confidence(self):
        result = m.assess_language('मी घौर जाणू छौं अर वु भी आलु', [{'iso_639_3': 'gbm'}])
        self.assertEqual(result['confidence'], 'high')
        self.assertGreaterEqual(result['content_markers']['garhwali'], 2)

    def test_every_row_carries_content_markers(self):
        # The Hugging Face package needs one schema per shard, so Latin and
        # Devanagari rows must have the same language_quality keys.
        latin = m.assess_language('mi ghar jaanu chhaun', [{'iso_639_3': 'gbm'}])
        devanagari = m.assess_language('मी घौर जाणू छौं', [{'iso_639_3': 'gbm'}])
        self.assertEqual(set(latin), set(devanagari))
        self.assertEqual(latin['content_markers'], {'tokens': 0, 'hindi': 0, 'garhwali': 0})

    def test_short_text_is_not_scored(self):
        markers = m.content_markers('है और')
        self.assertFalse(m.hindi_marker_dominant(markers))


if __name__ == '__main__':
    unittest.main()
