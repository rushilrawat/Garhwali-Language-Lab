import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_huggingface_dataset as m


class HuggingFaceDatasetBuilderTests(unittest.TestCase):
    def test_failed_managed_build_preserves_previous_package(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'package'
            output.mkdir()
            marker = output / 'manifest.json'
            marker.write_text('previous')
            with (
                patch.object(m, 'DEFAULT_OUTPUT', output),
                patch.object(m, '_build_at', side_effect=RuntimeError('failed')),
                self.assertRaisesRegex(RuntimeError, 'failed'),
            ):
                m.build(output)
            self.assertEqual(marker.read_text(), 'previous')

    def test_package_builder_refuses_to_delete_existing_custom_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / 'scripts'
            existing.mkdir()
            marker = existing / 'keep.py'
            marker.write_text('keep')
            with self.assertRaisesRegex(ValueError, 'refusing to replace'):
                m.prepare_package_output(existing)
            self.assertEqual(marker.read_text(), 'keep')

    def test_knowledge_configs_cover_every_structured_cultural_catalog(self):
        self.assertEqual(
            set(m.KNOWLEDGE_CONFIGS),
            {
                'geography', 'historical_terms', 'literary_people',
                'literary_works', 'popular_songs', 'university_research',
            },
        )

    def test_knowledge_row_adds_a_stable_common_id_without_losing_metadata(self):
        exported = m.knowledge_row(
            {
                'person_id': 'literary-person:example',
                'canonical_name': 'Example',
                'source_ids': ['catalog-a'],
                'verification_status': 'corroborated_in_project',
            },
            'literary_people',
        )
        self.assertEqual(exported['id'], 'literary-person:example')
        self.assertEqual(exported['knowledge_family'], 'literary_people')
        self.assertEqual(exported['canonical_name'], 'Example')
        self.assertEqual(exported['provenance'][0]['source_id'], 'catalog-a')
        self.assertEqual(exported['rights_status'], 'not_assessed')
        self.assertFalse(exported['quality_metadata']['native_reviewed'])

        with self.assertRaisesRegex(ValueError, 'stable ID'):
            m.knowledge_row({'title': 'No identifier'}, 'literary_works')

    def test_knowledge_row_resolves_source_ids_to_traceable_metadata(self):
        exported = m.knowledge_row(
            {
                'term_id': 'history:term:example',
                'source_refs': ['history-source'],
            },
            'historical_terms',
            source_catalog={
                'history-source': {
                    'title': 'Official history page',
                    'url': 'https://example.org/history',
                    'source_kind': 'government_page',
                    'sha256': 'a' * 64,
                    'capture_id': 'capture-17',
                    'local_capture': 'sources/manual/history.md',
                },
            },
        )
        self.assertEqual(exported['provenance'][0]['source_id'], 'history-source')
        self.assertEqual(exported['provenance'][0]['source_url'], 'https://example.org/history')
        self.assertEqual(exported['provenance'][0]['source_title'], 'Official history page')
        self.assertEqual(exported['provenance'][0]['source_snapshot_sha256'], 'a' * 64)
        self.assertEqual(exported['provenance'][0]['source_capture_id'], 'capture-17')
        self.assertEqual(exported['provenance'][0]['source_capture_path'], 'sources/manual/history.md')

    def test_source_catalog_resolves_geography_evidence_and_shared_capture(self):
        geography_sources = m.source_catalog_for_family('geography')
        geography = m.knowledge_row(
            {
                'record_id': 'place:example',
                'evidence': ['district_portal'],
                'wikipedia_url': 'https://en.wikipedia.org/wiki/Example',
            },
            'geography', geography_sources,
        )
        self.assertEqual(
            geography['provenance'][0]['source_url'],
            'https://uttarakhand.s3waas.gov.in/',
        )
        people_sources = m.source_catalog_for_family('literary_people')
        capture = m.source_provenance('itihaas-garhwali-capture', people_sources)
        self.assertEqual(
            capture['source_snapshot_sha256'],
            'f1f5870478d5f290509606f9c6d05f4bd86925b7d9080a80735cfbf05c756ae5',
        )

    def test_public_text_requires_at_least_one_publishable_exact_source(self):
        allowed = {
            'parents': [{'provenance': [{
                'training_eligible': False,
                'license': 'CC-BY-4.0',
                'iso_639_3': 'gbm',
            }]}],
        }
        blocked = {
            'parents': [{'provenance': [{
                'license': 'CC-BY-4.0',
                'rights_status': 'source_component_and_consent_review_pending',
            }]}],
        }
        self.assertTrue(m.is_public_text_row(allowed))
        self.assertFalse(m.is_public_text_row(blocked))
        self.assertTrue(m.is_public_garhwali_text_row(allowed))
        allowed['parents'][0]['provenance'][0]['iso_639_3'] = 'eng'
        self.assertFalse(m.is_public_garhwali_text_row(allowed))

        exact_duplicate = {
            'provenance': [
                {
                    'source_id': 'open', 'iso_639_3': 'gbm',
                    'license_id': 'CC-BY-4.0',
                },
                {
                    'source_id': 'mirror', 'iso_639_3': 'gbm',
                    'license_id': 'CC-BY-4.0',
                    'rights_status': 'source_component_and_consent_review_pending',
                },
            ],
        }
        self.assertTrue(m.is_public_text_row(exact_duplicate))
        self.assertTrue(m.is_public_garhwali_text_row(exact_duplicate))
        self.assertEqual(
            [item['source_id'] for item in m.publishable_provenance_items(exact_duplicate)],
            ['open'],
        )

    def test_public_knowledge_requires_explicit_rights_basis(self):
        cleared = {
            'rights_status': 'rights_assessed_compatible',
            'public_rights_basis': [{
                'license': 'CC-BY-4.0',
                'attribution': 'Source attribution',
                'source_url': 'https://example.org/record',
            }],
        }
        pending = {
            'rights_status': 'not_assessed',
            'provenance': [{
                'source_url': 'https://example.org/record',
            }],
        }
        self.assertTrue(m.is_public_knowledge_row(cleared))
        self.assertFalse(m.is_public_knowledge_row(pending))

    def test_rights_warnings_are_blocked_across_separator_styles(self):
        for rights_status in (
            'upstream component review required',
            'quoted_works_require_component_review',
            'catalog footer CC BY; item page has no license block',
        ):
            with self.subTest(rights_status=rights_status):
                self.assertFalse(m.is_publishable_provenance({
                    'license_id': 'CC-BY-NC-SA-4.0',
                    'rights_status': rights_status,
                }))

    def test_noncommercial_and_no_derivatives_cc_licenses_are_not_public(self):
        for license_id, license_url in (
            ('CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/'),
            ('CC-BY-ND-4.0', 'https://creativecommons.org/licenses/by-nd/4.0/'),
        ):
            with self.subTest(license_id=license_id):
                self.assertFalse(m.is_publishable_provenance({
                    'license_id': license_id,
                    'license_url': license_url,
                }))

    def test_open_license_matching_requires_mit_token_not_substring(self):
        self.assertTrue(m.is_publishable_provenance({'license_id': 'MIT'}))
        self.assertFalse(m.is_publishable_provenance({'license': 'limited permission'}))

    def test_text_export_derives_script(self):
        base = {'segment_sha256': 'a', 'split': 'train', 'quality_flags': []}
        open_row = {
            **base, 'text': 'गढ़वाली',
            'provenance': [{'source_id': 'open', 'license_id': 'CC-BY-4.0'}],
        }
        exported = m.text_row(open_row)
        self.assertEqual(exported['script'], 'Deva')
        self.assertEqual(exported['public_rights_basis'][0]['source_id'], 'open')
        self.assertEqual(exported['language'], 'und')
        self.assertEqual(m.text_row({**base, 'text': 'garhwali'})['script'], 'Latn')

    def test_text_export_does_not_label_english_or_mixed_context_as_garhwali(self):
        base = {'segment_sha256': 'a', 'split': 'train', 'quality_flags': []}
        english = m.text_row({
            **base,
            'text': 'Garhwal district history',
            'parents': [{'text_sha256': 'eng-parent', 'provenance': [
                {'source_id': 'gazetteer', 'iso_639_3': 'eng'},
            ]}],
        })
        mixed = m.text_row({
            **base,
            'text': 'Garhwali गढ़वाली',
            'parents': [{'text_sha256': 'mixed-parent', 'provenance': [
                {'source_id': 'survey', 'iso_639_3': 'mul'},
            ]}],
        })
        self.assertEqual(english['language'], 'eng')
        self.assertEqual(mixed['language'], 'mul')
        self.assertFalse(english['recommended_for_training'])

    def test_text_export_carries_parent_quality_and_recommendation(self):
        row = {
            'segment_sha256': 'a', 'split': 'train', 'text': 'गढ़वाली',
            'quality_flags': [],
            'parents': [{'text_sha256': 'parent', 'provenance': [
                {'source_id': 'open', 'iso_639_3': 'gbm', 'license_id': 'CC-BY-4.0'},
            ]}],
        }
        parent_quality = {
            'parent': {
                'language_bucket': 'garhwali_candidate',
                'quality_v2': {'tier': 'strict_gold_candidate'},
            },
        }
        exported = m.text_row(row, parent_quality)
        self.assertEqual(exported['language'], 'gbm')
        self.assertEqual(exported['quality_tiers'], ['strict_gold_candidate'])
        self.assertTrue(exported['recommended_for_training'])

    def test_refreshes_references_after_public_filtering(self):
        rows = [
            {'task': 'translation', 'instruction': 'Same prompt',
             'response': 'one', 'acceptable_responses': ['one', 'two']},
        ]
        refreshed = m.refresh_acceptable_responses(rows)
        self.assertEqual(refreshed[0]['acceptable_responses'], ['one'])

    def test_catalog_keeps_every_identity_but_redacts_unlicensed_text(self):
        row = {
            'text_sha256': 'a' * 64,
            'text': 'गढ़वाली पाठ',
            'split': 'train',
            'language_bucket': 'garhwali_candidate',
            'quality_v2': {'tier': 'high_quality_rights_pending'},
            'provenance': [{
                'source_id': 'example',
                'source_url': 'https://example.test/garhwali',
                'iso_639_3': 'gbm',
                'rights_status': 'public_webpage_no_open_license_stated',
            }],
        }
        exported = m.catalog_row(row, refinement={
            'automatic_changes': [],
            'review_signals': ['romanized_text_requires_native_review'],
            'manual_review_required': True,
            'language_decision': 'unchanged_pending_native_review',
            'quality_refinement_status': 'review_required',
            'release_text': 'protected corrected text',
            'release_text_sha256': 'c' * 64,
            'quality_dimensions': {'language_identity': {'status': 'pending'}},
            'review_priority': {'rank': 2, 'reasons': ['native_accuracy_unverified']},
        })
        self.assertIsNone(exported['text'])
        self.assertFalse(exported['text_publicly_available'])
        self.assertEqual(exported['text_sha256'], row['text_sha256'])
        self.assertEqual(exported['sources'][0]['source_url'], 'https://example.test/garhwali')
        self.assertEqual(exported['quality_v2']['tier'], 'high_quality_rights_pending')
        self.assertEqual(
            exported['text_refinement']['review_signals'],
            ['romanized_text_requires_native_review'],
        )
        self.assertNotIn('release_text', exported['text_refinement'])
        self.assertEqual(
            exported['text_refinement']['quality_dimensions']['language_identity']['status'],
            'pending',
        )
        self.assertEqual(exported['text_refinement']['review_priority']['rank'], 2)

    def test_all_data_catalog_keeps_full_text_and_rights_metadata(self):
        row = {
            'text_sha256': 'a' * 64,
            'text': 'गढ़वाली पाठ',
            'quality_v2': {'tier': 'high_quality_rights_pending'},
            'provenance': [{
                'source_id': 'example',
                'rights_status': 'public_webpage_no_open_license_stated',
            }],
        }
        exported = m.catalog_row(row, include_all_text=True)
        self.assertEqual(exported['text'], 'गढ़वाली पाठ')
        self.assertTrue(exported['content_included'])
        self.assertTrue(exported['active_for_quality_work'])
        self.assertFalse(exported['text_publicly_available'])
        self.assertEqual(exported['redistribution_status'], 'rights_pending')
        self.assertIsNone(exported['redaction_reason'])

    def test_catalog_preserves_pdf_page_provenance(self):
        row = {
            'text_sha256': 'd' * 64,
            'text': 'गढ़वाली पाठ',
            'provenance': [{
                'source_id': 'incoming_book',
                'source_pdf_sha256': 'a' * 64,
                'pdf_page': 7,
                'title': 'Garhwali Book',
                'author': 'Example Author',
                'publication_year': 1954,
                'extraction_method': 'tesseract_hin_eng',
            }],
        }
        exported = m.catalog_row(row, include_all_text=True)
        source = exported['sources'][0]
        self.assertEqual(source['source_pdf_sha256'], 'a' * 64)
        self.assertEqual(source['pdf_page'], 7)
        self.assertEqual(source['title'], 'Garhwali Book')
        self.assertEqual(source['author'], 'Example Author')
        self.assertEqual(source['publication_year'], 1954)
        self.assertEqual(source['extraction_method'], 'tesseract_hin_eng')

    def test_all_data_profile_is_first_class(self):
        self.assertTrue(m.profile_includes_all_data('all-data'))
        self.assertFalse(m.profile_includes_all_data('public'))
        self.assertEqual(m.asr_split_directory('all-data'), 'asr_experimental')
        self.assertEqual(m.asr_split_directory('public'), 'asr')

    def test_all_data_card_states_that_no_text_is_redacted(self):
        report = {
            'release_id': 'test',
            'profile': 'all-data',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 1,
            'catalog_records': 2,
            'catalog_redacted_text_records': 0,
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
        }
        card = m.dataset_card(report)
        self.assertIn('complete all-data package', card)
        self.assertIn('No catalog text values are redacted', card)
        self.assertNotIn('This rights-filtered package', card)
        self.assertNotIn('config_name: literary_works', card)
        self.assertNotIn('config_name: university_research', card)

    def test_public_card_discloses_structured_metadata_clearance_gap(self):
        report = {
            'release_id': 'test',
            'profile': 'public',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 1,
            'catalog_records': 2,
            'catalog_redacted_text_records': 1,
            'structured_knowledge_excluded_for_rights': {'geography': 50},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
        }
        card = m.dataset_card(report)
        self.assertIn('public-profile package', card)
        self.assertIn('omits **50 structured-knowledge records**', card)
        self.assertNotIn('config_name: geography', card)
        self.assertIn('They remain intact in the complete all-data package', card)

    def test_catalog_includes_open_text(self):
        row = {
            'text_sha256': 'b' * 64,
            'text': 'गढ़वाली पाठ',
            'provenance': [{'iso_639_3': 'gbm', 'license': 'CC-BY-4.0'}],
        }
        exported = m.catalog_row(row)
        self.assertEqual(exported['text'], 'गढ़वाली पाठ')
        self.assertTrue(exported['text_publicly_available'])
        self.assertIsNone(exported['redaction_reason'])
        self.assertEqual(exported['public_rights_basis'][0]['license'], 'CC-BY-4.0')

    def test_catalog_names_open_basis_when_other_exact_source_is_blocked(self):
        row = {
            'text_sha256': 'c' * 64,
            'text': 'गढ़वाली पाठ',
            'provenance': [
                {'source_id': 'open', 'iso_639_3': 'gbm', 'license_id': 'CC-BY-4.0'},
                {
                    'source_id': 'mirror', 'iso_639_3': 'gbm',
                    'license_id': 'CC-BY-4.0',
                    'rights_status': 'component_rights_review_required',
                },
            ],
        }
        exported = m.catalog_row(row)
        self.assertEqual(exported['text'], 'गढ़वाली पाठ')
        self.assertEqual(
            [item['source_id'] for item in exported['public_rights_basis']], ['open']
        )
        self.assertEqual(len(exported['sources']), 2)

    def test_audio_export_uses_content_addressed_relative_path(self):
        row = {
            'audio_sha256': 'ab' * 32,
            'local_audio_path': 'data/audio/source.wav',
            'source': 'VAANI',
            'speaker_id': 'raw-speaker-id',
            'asr_target_clean': 'गढ़वाली',
            'machine_transcript_quality': {'flags': ['mixed_script']},
            'recovery_status': 'confidence_scored_alternative_available',
            'recovery_confidence': {
                'confidence_band': 'very_low',
                'confidence_is_accuracy_probability': False,
                'whisper_candidate': 'गढ़वाली',
            },
            'duplicate_source_audio_paths': ['private-1.wav', 'private-2.wav'],
            'language_scope_status': 'source_label_conflict',
            'source_conflict_evidence': {'human_bengali_transcripts': 8},
            'active_for_source_error_analysis': True,
            'recovery_adjudication': {
                'evidence_status': 'related_checkpoint_consensus_clean',
                'automatic_correction': False,
            },
            'recovery_third_checkpoint': {
                'transcript': 'गढ़वाली',
                'confidence_is_calibrated': False,
            },
            'audio_grounded_review': {
                'machine_audio_review_complete': True,
                'human_listening_review_required': True,
                'automatic_correction': False,
            },
        }
        exported = m.audio_row(row, transcript_field='asr_target_clean')
        self.assertEqual(exported['audio'], f'audio/ab/{"ab" * 32}.wav')
        self.assertEqual(exported['transcript'], 'गढ़वाली')
        self.assertEqual(exported['machine_transcript_quality']['flags'], ['mixed_script'])
        self.assertEqual(exported['recovery_status'], 'confidence_scored_alternative_available')
        self.assertEqual(exported['recovery_confidence']['confidence_band'], 'very_low')
        self.assertTrue(exported['speaker_id'].startswith('speaker_'))
        self.assertNotEqual(exported['speaker_id'], 'raw-speaker-id')
        self.assertEqual(exported['source_audio_records'], 2)
        self.assertNotIn('duplicate_source_audio_paths', exported)
        self.assertNotIn('local_audio_path', exported)
        self.assertEqual(exported['language_scope_status'], 'source_label_conflict')
        self.assertTrue(exported['active_for_source_error_analysis'])
        self.assertFalse(exported['recovery_adjudication']['automatic_correction'])
        self.assertFalse(exported['recovery_third_checkpoint']['confidence_is_calibrated'])
        self.assertTrue(exported['audio_grounded_review']['human_listening_review_required'])

    def test_recovery_adjudication_join_omits_local_review_paths(self):
        rows = [{'audio_sha256': 'a', 'machine_transcript': 'मूल'}]
        evidence = [{
            'audio_sha256': 'a',
            'local_audio_path': 'private/audio.wav',
            'speaker_id': 'private-speaker',
            'proposed_machine_transcript': 'प्रस्ताव',
            'automatic_correction': False,
        }]
        result = m.attach_recovery_adjudication(rows, evidence)[0]
        self.assertEqual(
            result['recovery_adjudication']['proposed_machine_transcript'], 'प्रस्ताव'
        )
        self.assertNotIn('local_audio_path', result['recovery_adjudication'])
        self.assertNotIn('speaker_id', result['recovery_adjudication'])

    def test_third_checkpoint_join_exports_all_evidence_without_local_paths(self):
        rows = [{'audio_sha256': 'a'}]
        evidence = [{
            'audio_sha256': 'a',
            'local_audio_path': 'private/audio.wav',
            'machine_transcript': 'गढ़वळि पाठ',
            'mean_token_log_probability': -1.5,
            'token_confidence_uncalibrated': 0.22,
        }]
        result = m.attach_recovery_third_checkpoint(rows, evidence)[0]
        exported = result['recovery_third_checkpoint']
        self.assertEqual(exported['transcript'], 'गढ़वळि पाठ')
        self.assertFalse(exported['confidence_is_calibrated'])
        self.assertFalse(exported['human_reference_available'])
        self.assertNotIn('local_audio_path', exported)

    def test_audio_grounded_review_join_omits_local_paths(self):
        rows = [{'audio_sha256': 'a'}]
        evidence = [{
            'audio_sha256': 'a',
            'local_audio_path': 'private/audio.wav',
            'audio_grounded_evidence': {'waveform': {'duration_seconds': 1.0}},
            'machine_audio_review_complete': True,
            'human_listening_review_required': True,
            'automatic_correction': False,
        }]
        result = m.attach_audio_grounded_review(rows, evidence)[0]
        exported = result['audio_grounded_review']
        self.assertTrue(exported['machine_audio_review_complete'])
        self.assertTrue(exported['human_listening_review_required'])
        self.assertNotIn('local_audio_path', exported)

    def test_shards_are_deterministic_and_reported(self):
        rows = [{'id': str(index)} for index in range(5)]
        with tempfile.TemporaryDirectory() as directory:
            report = m.write_shards(rows, Path(directory), 'train', shard_rows=2)
            self.assertEqual(report['records'], 5)
            self.assertEqual(report['shards'], 3)
            paths = sorted(Path(directory).glob('train-*.jsonl'))
            self.assertEqual([p.name for p in paths], [
                'train-00000.jsonl', 'train-00001.jsonl', 'train-00002.jsonl'
            ])
            self.assertEqual(json.loads(paths[-1].read_text())['id'], '4')
            self.assertEqual(
                report['file_sha256'],
                {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
            )

    def test_draft_coverage_accepts_source_rows_with_duplicate_audio(self):
        queue = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        drafts = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav'},
        ]
        self.assertTrue(m.drafts_cover_queue(queue, drafts))
        self.assertFalse(m.drafts_cover_queue(queue, drafts[:1]))

    def test_duplicate_audio_rows_merge_source_paths(self):
        rows = [
            {'audio_sha256': 'same', 'audio_path': 'one.wav', 'machine_transcript': 'पाठ'},
            {'audio_sha256': 'same', 'audio_path': 'two.wav', 'machine_transcript': 'पाठ'},
        ]
        merged = list(m.deduplicate_audio_rows(rows, 'machine_transcript'))
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['duplicate_source_audio_paths'], ['one.wav', 'two.wav'])

    def test_audio_link_report_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'data/vaani/audio/source.wav'
            source.parent.mkdir(parents=True)
            source.write_bytes(b'audio')
            old_root = m.ROOT
            try:
                m.ROOT = root
                row = {
                    'audio_sha256': m.sha256_file(source),
                    'local_audio_path': 'data/vaani/audio/source.wav',
                }
                first = m.link_audio([row], root / 'package')
                second = m.link_audio([row], root / 'package')
            finally:
                m.ROOT = old_root
        self.assertEqual(first, {'new': 1, 'total': 1})
        self.assertEqual(second, {'new': 0, 'total': 1})

    def test_audio_link_rejects_path_outside_audio_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'secret.txt'
            source.write_text('secret')
            old_root = m.ROOT
            try:
                m.ROOT = root
                with self.assertRaisesRegex(ValueError, 'unsafe audio source'):
                    m.link_audio([{
                        'audio_sha256': m.sha256_file(source),
                        'local_audio_path': 'secret.txt',
                    }], root / 'package')
            finally:
                m.ROOT = old_root

    def test_transcript_only_cleanup_removes_packaged_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / 'audio/ab/file.wav'
            audio.parent.mkdir(parents=True)
            audio.write_bytes(b'audio')
            self.assertEqual(m.remove_packaged_audio(root), 1)
            self.assertFalse((root / 'audio').exists())


if __name__ == '__main__':
    unittest.main()
