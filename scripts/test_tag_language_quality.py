import unittest
from pathlib import Path

import tag_language_quality as m


class LanguageQualityTests(unittest.TestCase):
    def call(self, name, *args):
        function = getattr(m, name, None)
        return function(*args) if function else None

    def test_language_quality_module_exists(self):
        self.assertTrue((Path(__file__).parent / 'tag_language_quality.py').exists())

    def test_script_profile_marks_real_mixed_script(self):
        result = self.call('script_profile', 'गढ़वाली abc')
        self.assertEqual(result and result['script'], 'Mixed-Deva-Latn')
        self.assertEqual(result and result['counts']['devanagari'], 7)
        self.assertEqual(result and result['counts']['latin'], 3)

    def test_romanized_garhwali_is_not_assumed_to_be_english(self):
        result = self.call('assess_language', 'Mi theek cha.', [
            {'iso_639_3': 'gbm', 'script': 'Latn', 'source_id': 'languageshome'}])
        self.assertEqual(result and result['status'], 'romanized_garhwali_candidate')
        self.assertIn('source_garhwali_label', result['evidence'])
        self.assertTrue(result['review_required'])
        self.assertIn('romanized_spelling_unverified', result['review_reasons'])

    def test_mixed_language_scope_requires_review(self):
        result = self.call('assess_language', 'गढ़वाली और हिंदी', [
            {'iso_639_3': 'mul', 'language_scope': 'Garhwali and Hindi'}])
        self.assertEqual(result and result['status'], 'mixed_language_source')
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

    def test_medium_language_confidence_enters_review_queue(self):
        self.assertTrue(self.call('needs_confidence_review', {'confidence': 'medium'}))
        self.assertFalse(self.call('needs_confidence_review', {'confidence': 'high'}))

    def test_language_bucket_separates_mixed_and_context_records(self):
        self.assertEqual(self.call('language_bucket', {'status': 'garhwali_candidate'}),
                         'garhwali_candidate')
        self.assertEqual(self.call('language_bucket', {'status': 'mixed_language_source'}),
                         'mixed_language')
        self.assertEqual(self.call('language_bucket', {'status': 'non_garhwali_source_language'}),
                         'non_garhwali_context')
        self.assertEqual(self.call('language_bucket', {'status': 'mixed_script_review'}),
                         'review')

    def test_genre_prefers_explicit_metadata_and_has_source_fallback(self):
        explicit = self.call('infer_genres', [{'genre': 'lexicon', 'file': 'corpus/asjp.jsonl'}])
        inferred = self.call('infer_genres', [{'file': 'data/extracted/folklore/book.jsonl'}])
        self.assertEqual(explicit and explicit['tags'], ['lexicon'])
        self.assertEqual(explicit and explicit['evidence'], 'explicit_source_metadata')
        self.assertEqual(inferred and inferred['tags'], ['folk_literature'])

    def test_cultural_reference_genre_retains_subgenres(self):
        result = m.infer_genres([{
            'file': 'extracted/historical/cultural_references.jsonl',
            'linguistic_metadata': {'cultural_genres': ['ritual_religion', 'performance']},
        }])
        self.assertEqual(result['tags'], ['cultural_reference'])
        self.assertEqual(result['subgenres'], ['performance', 'ritual_religion'])

    def test_dialect_labels_remain_separate_from_geography(self):
        result = self.call('dialect_evidence', [
            {'dialect': 'Srinagar', 'district': 'TehriGarhwal'},
            {'district': 'Uttarkashi'},
        ])
        self.assertEqual(result and result['dialect_labels'], ['Srinagar'])
        self.assertEqual(result and result['geographic_hints'], ['TehriGarhwal', 'Uttarkashi'])
        self.assertEqual(result and result['status'], 'explicit_label')
        unlabeled = self.call('dialect_evidence', [{'district': 'TehriGarhwal'}])
        self.assertEqual(unlabeled and unlabeled['status'], 'unlabeled')

    def test_unlabeled_speech_is_prioritized_for_dialect_review(self):
        row = {'genre_quality': {'tags': ['speech_transcript']},
               'dialect_quality': {'status': 'unlabeled'}}
        self.assertTrue(self.call('needs_dialect_review', row))
        row['dialect_quality']['status'] = 'explicit_label'
        self.assertFalse(self.call('needs_dialect_review', row))

    def test_audio_tag_does_not_infer_dialect_from_district(self):
        result = self.call('tag_audio_record', {
            'audio_sha256': 'abc', 'language': 'Garhwali', 'district': 'TehriGarhwal',
            'speaker_id': 'NA', 'gender': 'Female', 'languages_known': ['Garhwali', 'Hindi'],
            'asr_target_clean': 'मी ठीक छौं',
        })
        self.assertEqual(result and result['speaker_metadata']['status'], 'unidentified')
        self.assertEqual(result and result['dialect_quality']['status'], 'unlabeled')
        self.assertEqual(result and result['dialect_quality']['geographic_hints'], ['TehriGarhwal'])

    def test_untranscribed_audio_uses_source_language_label(self):
        result = self.call('tag_audio_record', {
            'audio_sha256': 'abc', 'language': 'Garhwali', 'district': 'Uttarkashi',
            'speaker_id': 'S1', 'selected_transcript': '',
        })
        self.assertEqual(result and result['language_quality']['status'], 'source_labeled_garhwali_audio')
        self.assertFalse(result and result['language_quality']['review_required'])

    def test_text_tag_combines_quality_dimensions(self):
        row = {'text_sha256': 'abc', 'text_model': 'कुकुर', 'provenance': [{
            'iso_639_3': 'gbm', 'genre': 'thematic_lexicon', 'dialect': 'Srinagar'}]}
        result = self.call('tag_text_record', row)
        self.assertEqual(result and result['language_quality']['status'], 'garhwali_candidate')
        self.assertEqual(result and result['genre_quality']['tags'], ['thematic_lexicon'])
        self.assertEqual(result and result['dialect_quality']['dialect_labels'], ['Srinagar'])

    def test_lexicon_candidate_retains_gloss_and_domain(self):
        row = {'text_sha256': 'abc', 'text_model': 'कुकुर', 'genre_quality': {
            'tags': ['thematic_lexicon']}, 'language_quality': {'status': 'garhwali_candidate'},
            'provenance': [{'record_id': 'word:1', 'source_id': 'words', 'linguistic_metadata': {
                'english_gloss': 'dog', 'semantic_domain': 'animal'}}]}
        result = self.call('lexicon_candidate', row)
        self.assertEqual(result and result['glosses']['english'], ['dog'])
        self.assertEqual(result and result['semantic_domains'], ['animal'])

    def test_parallel_entries_expand_multiple_english_alignments(self):
        row = {'text_sha256': 'abc', 'text_model': 'भासा', 'provenance': [{
            'record_id': 'translation:1', 'source_id': 'translatewiki',
            'linguistic_metadata': {'english_alignments': ['Language', 'Languages']}}]}
        result = self.call('parallel_entries', row)
        self.assertEqual([item['english'] for item in (result or [])], ['Language', 'Languages'])
        self.assertTrue(all(item['garhwali'] == 'भासा' for item in result))


if __name__ == '__main__': unittest.main()
