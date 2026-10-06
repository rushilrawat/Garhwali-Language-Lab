import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import build_huggingface_dataset as m


class HuggingFaceDatasetBuilderTests(unittest.TestCase):
    def test_normalized_text_key_preserves_devanagari_vowel_marks(self):
        self.assertNotEqual(
            m.normalized_text_key('कला'), m.normalized_text_key('काली')
        )
        self.assertEqual(
            m.normalized_text_key('गढ़वाली वाक्य।'),
            m.normalized_text_key('  गढ़वाली   वाक्य! '),
        )

    def test_meta_cc_by_decision_is_narrow_and_makes_strict_training_candidate_eligible(self):
        original = {
            'source_id': 'meta_omni',
            'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
            'rights_status': 'upstream_meta_cc_by_4_0',
            'rights_evidence': 'sources/online/meta_omni/card.md.metadata.json',
            'license_id': 'CC-BY-4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'training_eligible': False,
            'quality_flags': [],
        }
        row = {
            'id': 'meta-row-1',
            'text': 'गढ़वाली का साफ उदाहरण।',
            'language': 'gbm',
            'source_languages': ['gbm'],
            'language_buckets': ['garhwali_candidate'],
            'quality_tiers': ['strict_gold_candidate'],
            'quality_flags': [],
            'record_quality_flags': [],
            'split': 'train',
            'source_split_overlap_status': 'no_upstream_eval_match_detected',
            'provenance': [original],
            'public_rights_basis': [original],
        }

        decided = m.apply_meta_training_rights_decision(row)

        self.assertTrue(m.recommended_text_training_row(decided))
        self.assertFalse(original['training_eligible'])
        self.assertFalse(decided['provenance'][0]['training_eligible_before_project_decision'])
        self.assertTrue(decided['provenance'][0]['training_eligible'])
        self.assertTrue(decided['public_rights_basis'][0]['training_eligible'])

    def test_meta_training_rights_decision_does_not_apply_to_other_or_restrictive_sources(self):
        base = {
            'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
            'rights_status': 'upstream_meta_cc_by_4_0',
            'rights_evidence': 'sources/online/meta_omni/card.md.metadata.json',
            'license_id': 'CC-BY-4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'training_eligible': False,
            'quality_flags': [],
        }
        other_source = {**base, 'source_id': 'other'}
        restricted_meta = {**base, 'source_id': 'meta_omni', 'license_id': 'CC-BY-NC-SA-4.0'}

        self.assertFalse(m.apply_meta_training_rights_decision({'provenance': [other_source]})['provenance'][0]['training_eligible'])
        self.assertFalse(m.apply_meta_training_rights_decision({'provenance': [restricted_meta]})['provenance'][0]['training_eligible'])

    def test_quality_text_view_excludes_blank_and_audits_normalized_duplicates(self):
        source = {
            'source_id': 'meta_omni',
            'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
            'rights_status': 'upstream_meta_cc_by_4_0',
            'rights_evidence': 'sources/online/meta_omni/card.md.metadata.json',
            'license_id': 'CC-BY-4.0',
            'license_url': 'https://creativecommons.org/licenses/by/4.0/',
            'training_eligible': False,
            'quality_flags': [],
        }
        base = {
            'language': 'gbm',
            'source_languages': ['gbm'],
            'language_buckets': ['garhwali_candidate'],
            'quality_tiers': ['strict_gold_candidate'],
            'quality_flags': [],
            'record_quality_flags': [],
            'split': 'train',
            'source_split_overlap_status': 'no_upstream_eval_match_detected',
            'provenance': [source],
            'public_rights_basis': [source],
            'recommended_for_training': False,
        }
        rows = {
            'text': [
                {**base, 'id': 'one', 'text': 'गढ़वाली वाक्य।'},
                {**base, 'id': 'blank', 'text': '  '},
            ],
            'text_expansion': [],
        }

        selected, metrics = m.build_quality_screened_meta_text(rows)

        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]['id'], 'one')
        self.assertTrue(selected[0]['recommended_for_training'])
        self.assertFalse(selected[0]['native_reviewed'])
        self.assertEqual(metrics['blank_excluded'], 1)
        self.assertEqual(metrics['selected_rows'], 1)

        duplicate_rows = {
            'text': [
                {**base, 'id': 'one', 'text': 'गढ़वाली वाक्य।'},
                {**base, 'id': 'two', 'text': '  गढ़वाली   वाक्य। '},
            ],
            'text_expansion': [],
        }
        deduplicated, duplicate_metrics = m.build_quality_screened_meta_text(duplicate_rows)
        self.assertEqual([row['id'] for row in deduplicated], ['one'])
        self.assertEqual(duplicate_metrics['normalized_duplicate_excluded'], 1)
        self.assertEqual(
            duplicate_metrics['duplicate_exclusions'][0]['excluded_id'], 'two'
        )

    def test_default_release_version_targets_next_additive_candidate(self):
        self.assertEqual(m.RELEASE_VERSION, '0.2.8')

    def test_hf_feature_schema_merges_null_list_types_across_splits(self):
        value_null = {'dtype': 'null', '_type': 'Value'}
        value_string = {'dtype': 'string', '_type': 'Value'}
        overlap_features = {
            'dialect_quality': {
                'dialect_labels': {'feature': value_null, '_type': 'List'},
            },
            'source_split_overlap_source_ids': {
                'feature': value_string, '_type': 'List',
            },
            'text_refinement': {
                'automatic_changes': {'feature': value_null, '_type': 'List'},
            },
        }
        train_features = {
            'dialect_quality': {
                'dialect_labels': {'feature': value_string, '_type': 'List'},
            },
            'source_split_overlap_source_ids': {
                'feature': value_null, '_type': 'List',
            },
            'text_refinement': {
                'automatic_changes': {'feature': value_string, '_type': 'List'},
            },
        }

        merged = m.merge_hf_feature_schemas([overlap_features, train_features])

        for field in (
            merged['dialect_quality']['dialect_labels'],
            merged['source_split_overlap_source_ids'],
            merged['text_refinement']['automatic_changes'],
        ):
            self.assertEqual(field, {'feature': value_string, '_type': 'List'})

    def test_hf_feature_schema_rejects_conflicting_non_null_types(self):
        with self.assertRaisesRegex(ValueError, 'incompatible Hugging Face feature'):
            m.merge_hf_feature_schemas([
                {'label': {'dtype': 'string', '_type': 'Value'}},
                {'label': {'dtype': 'bool', '_type': 'Value'}},
            ])

    @unittest.skipUnless(
        importlib.util.find_spec('datasets'),
        'Hugging Face datasets is installed by requirements-hf-release.txt',
    )
    def test_inferred_card_features_load_empty_list_fields_across_splits(self):
        from datasets import Dataset, Features

        with tempfile.TemporaryDirectory() as directory:
            overlap = Path(directory) / 'source_overlap-00000.jsonl'
            train = Path(directory) / 'train-00000.jsonl'
            overlap.write_text(json.dumps({
                'dialect_quality': {'dialect_labels': []},
                'source_split_overlap_source_ids': ['meta:test:1'],
            }) + '\n', encoding='utf-8')
            train.write_text(json.dumps({
                'dialect_quality': {'dialect_labels': ['rathi']},
                'source_split_overlap_source_ids': [],
            }) + '\n', encoding='utf-8')

            features = Features._from_yaml_list(
                m.infer_hf_config_features(Path(directory))
            )
            self.assertEqual(
                features['dialect_quality']['dialect_labels'].feature.dtype,
                'string',
            )
            self.assertEqual(
                features['source_split_overlap_source_ids'].feature.dtype,
                'string',
            )
            for path in (overlap, train):
                loaded = Dataset.from_json(
                    str(path), features=features, keep_in_memory=True,
                    cache_dir=str(Path(directory) / 'cache'),
                    chunksize=path.stat().st_size + 1,
                )
                self.assertEqual(len(loaded), 1)

    @unittest.skipUnless(
        importlib.util.find_spec('datasets'),
        'Hugging Face datasets is installed by requirements-hf-release.txt',
    )
    def test_release_card_declares_stable_text_and_resource_schemas(self):
        from datasets import Dataset, Features

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            config_rows = {
                'text': [
                    {'id': 'text-1', 'text': 'पहिलो', 'optional_label': None},
                    {'id': 'text-2', 'text': 'दोस्रो', 'optional_label': 'verified'},
                ],
                'text_resources': [
                    {'id': 'resource-1', 'forms': []},
                    {'id': 'resource-2', 'forms': ['गढ़वाली']},
                ],
                'paharili_gbm': [
                    {'id': 'paharili-1', 'text': 'गढ़वाली वाक्य', 'source_record_ids': ['paharili_gbm:train:1']},
                    {'id': 'paharili-2', 'text': 'दूसरा वाक्य', 'source_record_ids': []},
                ],
            }
            for config_name, rows in config_rows.items():
                config_dir = output / 'data' / config_name
                config_dir.mkdir(parents=True)
                (config_dir / 'train-00000.jsonl').write_text(
                    ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
                    encoding='utf-8',
                )

            config_report = {
                f'{config_name}/train': {'records': len(rows)}
                for config_name, rows in config_rows.items()
            }
            dataset_info = m.dataset_info_for_release(output, config_report)

            self.assertEqual(
                [entry['config_name'] for entry in dataset_info],
                ['text', 'text_resources', 'paharili_gbm'],
            )
            for entry in dataset_info:
                config_name = entry['config_name']
                features = Features._from_yaml_list(entry['features'])
                loaded = Dataset.from_json(
                    str(output / 'data' / config_name / 'train-00000.jsonl'),
                    features=features,
                    keep_in_memory=True,
                    cache_dir=str(output / 'cache' / config_name),
                )
                self.assertEqual(len(loaded), 2)
            self.assertEqual(
                Features._from_yaml_list(dataset_info[0]['features'])[
                    'optional_label'
                ].dtype,
                'string',
            )
            self.assertEqual(
                Features._from_yaml_list(dataset_info[1]['features'])[
                    'forms'
                ].feature.dtype,
                'string',
            )

    def test_upstream_eval_link_keeps_text_but_moves_it_out_of_train(self):
        original = {
            'id': 'row-1', 'text': 'गढ़वाली वाक्य', 'split': 'train',
            'original_split': 'train',
            'provenance': [{'source_id': 'meta_omni', 'record_id': 'meta:test:1'}],
            'split_assignment': 'existing assignment',
            'recommended_for_training': True,
        }

        routed = m.route_upstream_split_overlap(
            original, {'meta:test:1'}, set()
        )

        self.assertEqual(routed['split'], 'source_overlap')
        self.assertEqual(routed['original_split'], 'train')
        self.assertEqual(routed['source_split_overlap_status'], 'upstream_eval_record_id_match')
        self.assertEqual(routed['source_split_overlap_source_ids'], ['meta:test:1'])
        self.assertFalse(routed['recommended_for_training'])
        self.assertIn('text retained', routed['split_assignment'])
        self.assertEqual(original['split'], 'train')

    def test_ambiguous_transcript_match_is_visible_but_not_in_default_train(self):
        row = {
            'id': 'row-2', 'split': 'train',
            'sources': [{'source_id': 'indic_dialect_asr_gbm',
                         'record_id': 'indic_dialect_asr_gbm:14'}],
        }

        routed = m.route_upstream_split_overlap(
            row, set(), {'indic_dialect_asr_gbm:14'}
        )

        self.assertEqual(routed['split'], 'source_overlap')
        self.assertEqual(
            routed['source_split_overlap_status'], 'upstream_eval_transcript_match'
        )

    def test_non_train_rows_are_labeled_without_being_moved(self):
        row = {
            'id': 'row-3', 'split': 'test',
            'provenance': [{'source_id': 'meta_omni', 'record_id': 'meta:test:2'}],
        }

        routed = m.route_upstream_split_overlap(row, {'meta:test:2'}, set())

        self.assertEqual(routed['split'], 'test')
        self.assertEqual(routed['source_split_overlap_status'], 'upstream_eval_record_id_match')

    def test_rows_without_upstream_overlap_keep_their_split(self):
        row = {'id': 'row-4', 'split': 'train', 'provenance': []}

        routed = m.route_upstream_split_overlap(row, set(), set())

        self.assertEqual(routed['split'], 'train')
        self.assertEqual(
            routed['source_split_overlap_status'], 'no_upstream_eval_match_detected'
        )
        self.assertEqual(routed['source_split_overlap_source_ids'], [])

    def test_vaani_official_test_remainder_rows_are_routed_out_of_train(self):
        row = {
            'id': 'row-5', 'text': 'गढ़वाली वाक्य', 'split': 'train',
            'provenance': [{
                'source_id': 'vaani-transcription-part',
                'record_id': 'vaani:official-test-row',
                'transcription_split': 'test',
                'canonical_transcript_source': 'ARTPARK-IISc/Vaani-transcription-part',
            }],
        }

        routed = m.route_upstream_split_overlap(row, set(), set())

        self.assertEqual(routed['split'], 'source_overlap')
        self.assertEqual(
            routed['source_split_overlap_status'],
            'upstream_vaani_test_source_record_match',
        )
        self.assertEqual(
            routed['source_split_overlap_source_ids'], ['vaani:official-test-row']
        )
        self.assertFalse(routed['recommended_for_training'])

    def test_source_attribution_overlay_preserves_lineage_and_adds_reviewable_evidence(self):
        source = {
            'source_id': 'tatoeba',
            'record_id': 'tatoeba:42',
            'line': 7,
            'quality_flags': ['missing_contributor'],
        }
        overlays = {
            'tatoeba:42': {
                'source_id': 'tatoeba',
                'attribution_name': 'sabretou',
                'contributor_profile_url': 'https://tatoeba.org/en/user/profile/sabretou',
                'source_url': 'https://tatoeba.org/en/sentences/show/42',
                'quality_flags': ['upstream_sentence_orphaned'],
            },
        }

        enriched = m.enrich_source_attribution(source, overlays)

        self.assertEqual(enriched['line'], 7)
        self.assertEqual(enriched['attribution_name'], 'sabretou')
        self.assertEqual(enriched['source_url'], 'https://tatoeba.org/en/sentences/show/42')
        self.assertEqual(enriched['quality_flags'], ['upstream_sentence_orphaned'])
        self.assertEqual(source['quality_flags'], ['missing_contributor'])

    def test_source_attribution_overlay_rejects_source_identity_mismatch(self):
        with self.assertRaisesRegex(ValueError, 'Source ID mismatch'):
            m.enrich_source_attribution(
                {'source_id': 'tatoeba', 'record_id': 'tatoeba:42'},
                {'tatoeba:42': {'source_id': 'wiktionary_en'}},
            )

    def test_audited_attribution_overlay_enriches_tatoeba_and_wiki_provenance(self):
        overlays = m.source_attribution_overlays()
        self.assertEqual(len(overlays), 355)
        self.assertNotIn('text_normalized', json.dumps(overlays, ensure_ascii=False))

        tatoeba = m.catalog_provenance({
            'source_id': 'tatoeba',
            'record_id': 'tatoeba:4648044',
            'quality_flags': ['missing_contributor'],
        })
        self.assertEqual(tatoeba['attribution_name'], 'sabretou')
        self.assertEqual(tatoeba['contributor'], 'sabretou')
        self.assertNotIn('missing_contributor', tatoeba['quality_flags'])
        self.assertIn('upstream_sentence_orphaned', tatoeba['quality_flags'])
        self.assertTrue(tatoeba['attribution_evidence_sha256'])

        wiki_id, wiki_overlay = next(
            (record_id, item) for record_id, item in overlays.items()
            if item.get('source_id') == 'wikimedia'
        )
        wiki = m.catalog_provenance({
            'source_id': 'wikimedia',
            'record_id': wiki_id,
        })
        self.assertEqual(wiki['source_revision'], wiki_overlay['source_revision'])
        self.assertIn(f"oldid={wiki['source_revision']}", wiki['source_url'])
        self.assertIn('action=history', wiki['source_history_url'])

    def test_failed_managed_build_preserves_previous_package(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'package'
            output.mkdir()
            marker = output / 'manifest.json'
            marker.write_text('previous')
            with (
                patch.object(m, 'DEFAULT_OUTPUT', output),
                patch.object(m, 'MANAGED_OUTPUTS', {output.resolve()}),
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

    def test_training_recommendation_respects_explicit_source_eligibility(self):
        rights_basis = {
            'source_id': 'open',
            'record_id': 'open:1',
            'source_url': 'https://example.org/open/1',
            'license_id': 'CC-BY-4.0',
            'attribution': 'Open source contributors',
        }
        row = {
            'language': 'gbm',
            'source_languages': ['gbm'],
            'language_buckets': ['garhwali_candidate'],
            'quality_tiers': ['strict_gold_candidate'],
            'quality_flags': [],
            'provenance': [{**rights_basis, 'training_eligible': False}],
            'public_rights_basis': [rights_basis],
        }
        self.assertFalse(m.recommended_text_training_row(row))
        row['provenance'][0]['training_eligible'] = True
        self.assertTrue(m.recommended_text_training_row(row))
        row['split'] = 'validation'
        self.assertFalse(m.recommended_text_training_row(row))
        row['split'] = 'train'
        self.assertTrue(m.recommended_text_training_row(row))
        row['provenance'][0].pop('training_eligible')
        self.assertTrue(m.recommended_text_training_row(row))

    def test_catalog_provenance_preserves_source_training_flags(self):
        exported = m.catalog_provenance({
            'source_id': 'open',
            'record_id': 'open:1',
            'training_eligible': False,
            'experimental_training_eligible': True,
        })
        self.assertIs(exported['training_eligible'], False)
        self.assertIs(exported['experimental_training_eligible'], True)

    def test_catalog_provenance_preserves_upstream_transcript_split(self):
        exported = m.catalog_provenance({
            'source_id': 'vaani-transcription-part',
            'record_id': 'vaani:official-test-row',
            'canonical_transcript_source': 'ARTPARK-IISc/Vaani-transcription-part',
            'transcription_split': 'test',
            'main_split': 'train',
        })
        self.assertEqual(exported['transcription_split'], 'test')
        self.assertEqual(exported['main_split'], 'train')
        self.assertEqual(
            exported['canonical_transcript_source'],
            'ARTPARK-IISc/Vaani-transcription-part',
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

    def test_catalog_text_expansion_filters_rights_duplicates_and_eval_records(self):
        license_basis = {
            'source_id': 'open-source',
            'record_id': 'open-source:1',
            'source_url': 'https://example.org/source/1',
            'license_id': 'CC-BY-4.0',
            'attribution': 'Example source',
        }

        def candidate(record_id, text, **overrides):
            row = {
                'id': record_id,
                'text': text,
                'redistribution_status': 'rights_cleared',
                'language_bucket': 'garhwali_candidate',
                'quality_v2': {'tier': 'strict_gold_candidate'},
                'public_rights_basis': [dict(license_basis, record_id=record_id)],
                'sources': [{
                    'source_id': 'open-source',
                    'record_id': record_id,
                    'source_url': 'https://example.org/source/1',
                    'iso_639_3': 'gbm',
                }],
                'record_quality_flags': [],
            }
            row.update(overrides)
            return row

        rows, metrics = m.build_catalog_text_expansion(
            [
                candidate('new-1', 'नयाँ वाक्य'),
                candidate('new-2', 'नयाँ वाक्य!'),
                candidate('new-3', 'समुदायबाट संकलित अर्को वाक्य', record_quality_flags=['community_aggregation']),
                candidate('new-4', 'गुणस्तर चिन्ह भएको वाक्य', record_quality_flags=['community_aggregation']),
                candidate('eval-duplicate', 'मूल्याङ्कनसँग जोडिएको', sources=[{
                    'source_id': 'open-source', 'record_id': 'heldout:1',
                    'source_url': 'https://example.org/source/1', 'iso_639_3': 'gbm',
                }]),
                candidate('rights-pending', 'अधिकार जाँच बाँकी', redistribution_status='rights_pending'),
                candidate('quality-pending', 'गुणस्तर जाँच बाँकी', quality_v2={'tier': 'experimental_review'}),
            ],
            [
                {'id': 'existing', 'text': 'पहिलेको वाक्य', 'split': 'train'},
                {'id': 'heldout', 'text': 'held out', 'split': 'test', 'provenance': [
                    {'record_id': 'heldout:1'},
                ]},
                {'id': 'other-config', 'text': 'समुदायबाट संकलित अर्को वाक्य', 'split': 'train'},
            ],
        )

        self.assertEqual([row['id'] for row in rows], ['new-1', 'new-4'])
        self.assertEqual(metrics['strict_rights_language_candidates'], 5)
        self.assertEqual(metrics['excluded_evaluation_source_record'], 1)
        self.assertEqual(metrics['excluded_normalized_internal_duplicate'], 1)
        self.assertEqual(metrics['excluded_normalized_existing_text'], 1)
        self.assertEqual(metrics['records'], 2)
        self.assertEqual(metrics['recommended_for_training'], 1)
        self.assertFalse(rows[1]['recommended_for_training'])
        self.assertEqual(rows[0]['public_rights_basis'][0]['license_id'], 'CC-BY-4.0')
        self.assertEqual(rows[0]['split'], 'train')

    def test_paharili_view_deduplicates_and_preserves_upstream_provenance(self):
        def source(record_id, text, split, language='gbm'):
            source_split = record_id.split(':')[1]
            return {
                'record_id': record_id,
                'text_original': text,
                'text_normalized': text,
                'split': split,
                'iso_639_3': language,
                'upstream_label': language,
                'source_id': 'paharili_gbm',
                'source_url': 'https://github.com/rachanagusain/PahariLI',
                'attribution': 'Rachana Gusain, PahariLI repository',
                'license_id': 'Apache-2.0-repository-declared',
                'license_url': 'https://www.apache.org/licenses/LICENSE-2.0',
                'rights_status': (
                    'repository_Apache_2; underlying_blogs_and_translated_text_not_sublicensed'
                ),
                'quality_status': 'unreviewed',
                'quality_flags': [
                    'source_lineage_missing', 'component_rights_review_required',
                    'possible_modern_scripture_or_blog_text',
                ],
                'provenance': {
                    'url': f'https://raw.githubusercontent.com/rachanagusain/PahariLI/main/data/{source_split}.txt',
                    'sha256': 'a' * 64 if source_split == 'train' else 'b' * 64,
                    'bytes': 123,
                },
            }

        rows, metrics = m.build_paharili_gbm_rows(
            [
                source('paharili_gbm:train:1', 'गार्हवाली वाक्य।', 'train'),
                source('paharili_gbm:test:2', 'गार्हवाली वाक्य!', 'test'),
                source('paharili_gbm:test:3', 'मि ठीक छौं।', 'test'),
                source('paharili_gbm:train:4', 'नयाँ वाक्य', 'train'),
                source('paharili_gbm:train:5', 'अन्य भाषा।', 'train', language='doi'),
            ],
            [
                {
                    'text': 'मि ठीक छौं।',
                    'provenance': [{'record_id': 'paharili_gbm:test:3'}],
                },
            ],
        )

        self.assertEqual(len(rows), 2)
        overlap = next(row for row in rows if row['split'] == 'source_overlap')
        train = next(row for row in rows if row['split'] == 'train')
        self.assertEqual(
            overlap['source_record_ids'],
            ['paharili_gbm:test:2', 'paharili_gbm:train:1'],
        )
        self.assertEqual(overlap['upstream_splits'], ['test', 'train'])
        self.assertEqual(overlap['source_text_variants'], ['गार्हवाली वाक्य!', 'गार्हवाली वाक्य।'])
        self.assertEqual(train['text'], 'नयाँ वाक्य')
        self.assertFalse(train['training_eligible'])
        self.assertEqual(train['rights_status'], (
            'repository_Apache_2; underlying_blogs_and_translated_text_not_sublicensed'
        ))
        self.assertIn('component_rights_review_required', train['record_quality_flags'])
        self.assertEqual(metrics['input_records'], 5)
        self.assertEqual(metrics['garhwali_source_records'], 4)
        self.assertEqual(metrics['normalized_unique_source_texts'], 3)
        self.assertEqual(metrics['collapsed_duplicate_source_records'], 1)
        self.assertEqual(metrics['already_present_in_existing_configs'], 1)
        self.assertEqual(metrics['new_records'], 2)
        self.assertEqual(metrics['split_records'], {'source_overlap': 1, 'train': 1})

    def test_catalog_text_resources_keep_broad_rights_cleared_text_separate(self):
        open_basis = {
            'source_id': 'open-source',
            'record_id': 'open-source:1',
            'source_url': 'https://example.org/source/1',
            'license_id': 'CC-BY-4.0',
            'attribution': 'Example source',
        }
        nc_basis = {
            'source_id': 'nc-source',
            'record_id': 'nc-source:1',
            'source_url': 'https://example.org/nc/1',
            'license_id': 'CC-BY-NC-SA-4.0',
            'attribution': 'NC source attribution',
            'commercial_use_status': 'noncommercial_only',
        }

        def candidate(record_id, text, basis, **overrides):
            row = {
                'id': record_id,
                'text': text,
                'redistribution_status': 'rights_cleared',
                'language_bucket': 'garhwali_candidate',
                'quality_v2': {'tier': 'experimental_review'},
                'public_rights_basis': [dict(basis, record_id=record_id)],
                'noncommercial_rights_basis': [],
                'sources': [{
                    'source_id': basis['source_id'],
                    'record_id': record_id,
                    'source_url': basis['source_url'],
                    'iso_639_3': 'gbm',
                }],
                'record_quality_flags': ['needs_language_review'],
            }
            row.update(overrides)
            return row

        nc_row = candidate(
            'nc-resource', 'गढवाळी पूरक पाठ', nc_basis,
            redistribution_status='rights_cleared_noncommercial_sharealike',
            public_rights_basis=[],
            noncommercial_rights_basis=[dict(nc_basis, record_id='nc-resource')],
        )
        eval_row = candidate(
            'eval-resource', 'मूल्यांकन स्रोत वाला पाठ', open_basis,
            sources=[{
                'source_id': 'open-source', 'record_id': 'heldout:1',
                'source_url': 'https://example.org/source/1', 'iso_639_3': 'gbm',
            }],
        )
        rows, metrics = m.build_catalog_text_resources(
            [
                candidate('open-resource', 'गढवाळी पूरक वाक्य', open_basis),
                nc_row,
                eval_row,
                candidate('existing-copy', 'पहिले से मौजूद पाठ', open_basis),
                candidate('pending-resource', 'अधिकार लंबित पाठ', open_basis,
                          redistribution_status='rights_pending'),
            ],
            [
                {'id': 'existing-id', 'text': 'पहिले से मौजूद पाठ', 'split': 'train'},
                {'id': 'heldout', 'text': 'held out', 'split': 'test', 'provenance': [
                    {'record_id': 'heldout:1'},
                ]},
            ],
        )

        self.assertEqual([row['id'] for row in rows], ['nc-resource', 'open-resource'])
        self.assertEqual(metrics['rights_and_language_candidates'], 4)
        self.assertEqual(metrics['excluded_evaluation_source_record'], 1)
        self.assertEqual(metrics['excluded_normalized_existing_text'], 1)
        self.assertEqual(metrics['records'], 2)
        self.assertEqual(metrics['recommended_for_training'], 0)
        self.assertTrue(all(not row['recommended_for_evaluation'] for row in rows))
        self.assertEqual(rows[0]['provenance'][0]['license_id'], 'CC-BY-NC-SA-4.0')
        self.assertEqual(rows[0]['redistribution_status'], 'rights_cleared_noncommercial_sharealike')
        self.assertEqual(rows[1]['quality_flags'], ['needs_language_review'])

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

    def test_territorial_public_domain_requires_exact_status_and_complete_evidence(self):
        cases = (
            {
                'license_id': 'Public-Domain-US-UK-India',
                'license_url': 'https://copyright.gov.in/documents/international%20copyright%20order.htm',
                'rights_status': 'public_domain_us_uk_india_term_expired',
                'rights_evidence': ' '.join(
                    'https://' + url for url in
                    m.TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE[
                        'public_domain_us_uk_india_term_expired'
                    ]['required_evidence']
                ),
                'source_url': 'https://www.gutenberg.org/ebooks/43681',
                'attribution': 'William Crooke, 1896',
            },
            {
                'license_id': 'Public-Domain-India',
                'license_url': 'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
                'rights_status': 'public_domain_india_government_work_term_expired',
                'rights_evidence': ' '.join(
                    'https://' + url for url in
                    m.TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE[
                        'public_domain_india_government_work_term_expired'
                    ]['required_evidence']
                ),
                'source_url': 'https://archive.org/details/in.ernet.dli.2015.48008',
                'attribution': 'H. G. Walton, 1910',
            },
            {
                'license_id': 'Public-Domain-US-UK-India',
                'license_url': 'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
                'rights_status': 'public_domain_us_uk_india_term_expired_upreti_proverbs',
                'rights_evidence': ' '.join(
                    'https://' + url for url in
                    m.TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE[
                        'public_domain_us_uk_india_term_expired_upreti_proverbs'
                    ]['required_evidence']
                ),
                'source_url': 'https://archive.org/details/cu31924089930774',
                'attribution': 'Ganga Datt Upreti, 1894',
            },
            {
                'license_id': 'Public-Domain-US-UK-India',
                'license_url': 'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
                'rights_status': 'public_domain_us_uk_india_term_expired_upreti_hill_dialects',
                'rights_evidence': ' '.join(
                    'https://' + url for url in
                    m.TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE[
                        'public_domain_us_uk_india_term_expired_upreti_hill_dialects'
                    ]['required_evidence']
                ),
                'source_url': 'https://books.google.com/books?id=veUTAAAAYAAJ',
                'attribution': 'Ganga Datt Upreti, 1900',
            },
            {
                'license_id': 'Public-Domain-US-UK-India',
                'license_url': 'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
                'rights_status': 'public_domain_us_uk_india_term_expired_grierson',
                'rights_evidence': ' '.join(
                    'https://' + url for url in
                    m.TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE[
                        'public_domain_us_uk_india_term_expired_grierson'
                    ]['required_evidence']
                ),
                'source_url': 'https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu',
                'attribution': 'George Abraham Grierson, 1916',
            },
        )
        for item in cases:
            with self.subTest(rights_status=item['rights_status']):
                self.assertTrue(m.is_publishable_provenance(item))
                incomplete = {**item, 'rights_evidence': 'Archive says public domain'}
                self.assertFalse(m.is_publishable_provenance(incomplete))
        self.assertFalse(m.is_publishable_provenance({
            'license_id': 'Public-Domain',
            'license_url': 'https://archive.org/details/example',
            'rights_status': 'public_domain',
            'rights_evidence': 'Archive says public domain',
        }))

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
        self.assertEqual(exported['original_split'], '')
        self.assertEqual(exported['split_assignment'], '')
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

    def test_catalog_exposes_explicit_noncommercial_rows_with_restrictions(self):
        row = {
            'text_sha256': 'b' * 64,
            'text': 'गढ़वाली लोकपाठ',
            'provenance': [{
                'source_id': 'hindialect_gbm',
                'record_id': 'hindialect_gbm:train:1',
                'source_url': 'http://hdl.handle.net/11234/1-4839',
                'iso_639_3': 'gbm',
                'license_id': 'CC-BY-NC-SA-4.0',
                'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'rights_status': 'noncommercial_sharealike; upstream component review required',
                'attribution': 'HinDialect contributors',
            }],
        }
        exported = m.catalog_row(row)
        self.assertEqual(exported['text'], 'गढ़वाली लोकपाठ')
        self.assertTrue(exported['text_publicly_available'])
        self.assertEqual(
            exported['redistribution_status'],
            'rights_cleared_noncommercial_sharealike',
        )
        self.assertEqual(exported['commercial_use_status'], 'noncommercial_only')
        self.assertEqual(
            exported['noncommercial_rights_basis'][0]['license_id'],
            'CC-BY-NC-SA-4.0',
        )
        self.assertFalse(m.is_public_garhwali_text_row(row))

    def test_uou_sitewide_nc_sa_does_not_clear_conflicting_pdf_excerpt(self):
        row = {
            'text_sha256': 'c' * 64,
            'text': 'OCR excerpt from a UOU course PDF',
            'provenance': [{
                'source_id': 'uou_cgl',
                'source_url': 'https://uou.ac.in/sites/default/files/slm/CGL-101.pdf',
                'iso_639_3': 'gbm',
                'license_id': 'CC-BY-NC-SA-4.0',
                'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'rights_status': 'site_declares_CC_BY_NC_SA_4; quoted_works_require_component_review',
                'attribution': 'Uttarakhand Open University',
                'quality_flags': ['component_rights_review_required'],
            }],
        }
        source = row['provenance'][0]
        self.assertIsNone(m.noncommercial_catalog_provenance(source))
        self.assertFalse(m.is_publishable_provenance(source))
        exported = m.catalog_row(row)
        self.assertIsNone(exported['text'])
        self.assertEqual(exported['redistribution_status'], 'rights_pending')

        # Even without the component-review flag, the exact conflicted UOU
        # status is not one of the specifically reviewed NC-SA sources.
        source_without_flag = {**source, 'quality_flags': []}
        self.assertIsNone(m.noncommercial_catalog_provenance(source_without_flag))

    def test_obs_project_release_overrides_the_weaker_host_site_footer(self):
        item = {
            'source_id': 'obs_garhwali',
            'record_id': 'obs_garhwali:007',
            'source_url': 'https://media.ipsapps.org/in/osa/stories/36-Garhwali-007.html',
            'license_id': 'CC-BY-NC-SA-4.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
            'rights_status': 'catalog_footer_CC_BY_NC_SA_4; item_page_has_no_license_block',
            'attribution': 'Free Bibles India / unfoldingWord',
            'quality_flags': ['item_page_has_no_license_block', 'translation_quality_unreviewed'],
        }
        resolved = m.open_bible_stories_provenance(item)
        self.assertEqual(resolved['license_id'], 'CC-BY-SA-4.0')
        self.assertEqual(resolved['commercial_use_status'], 'permitted_with_attribution_and_sharealike')
        self.assertTrue(resolved['sharealike_required'])
        self.assertTrue(m.is_publishable_provenance(item))
        self.assertFalse(m.open_bible_stories_provenance({
            **item, 'record_id': 'obs_garhwali:051',
        }))

    def test_noncommercial_rights_mapping_does_not_clear_unmatched_or_blocked_rows(self):
        base = {
            'source_id': 'panlex_gbm',
            'source_url': 'https://huggingface.co/datasets/lbourdois/panlex',
            'license_id': 'CC-BY-NC-SA-4.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
            'rights_status': 'official_current_page_CC_BY_NC_SA_4; mirror_card_says_CC0; conservative_license_applied',
            'attribution': 'PanLex',
        }
        self.assertIsNotNone(m.noncommercial_catalog_provenance(base))
        self.assertIsNone(m.noncommercial_catalog_provenance({
            **base, 'source_url': 'https://example.org/other',
        }))
        self.assertIsNone(m.noncommercial_catalog_provenance({
            **base, 'quality_flags': ['component_rights_review_required'],
        }))

    def test_pib_policy_only_clears_the_five_instrument_records(self):
        provenance = {
            'source_id': 'pib_ramman_instruments',
            'record_id': 'pib_ramman_instruments:4',
            'license_id': 'LicenseRef-Government-Publication',
            'license_url': 'https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/sep/doc2025929651301.pdf',
            'rights_status': 'not_recorded',
            'attribution': 'Press Information Bureau, Government of India',
        }
        cleared = m.pib_policy_catalog_provenance(provenance)
        self.assertEqual(cleared['license_id'], 'LicenseRef-PIB-Copyright-Policy')
        self.assertEqual(
            cleared['commercial_use_status'],
            'not_explicitly_addressed_by_source_policy',
        )
        self.assertIsNone(m.pib_policy_catalog_provenance({
            **provenance, 'record_id': 'pib_ramman_instruments:6',
        }))

    def test_panos_policy_exposes_only_cited_glossary_rows_for_research_use(self):
        source = {
            'source_id': 'mountainvoices_local_glossary',
            'record_id': 'mountainvoices_local_glossary:1',
            'license_id': 'LicenseRef-Panos-Website-Terms-Unverified',
            'license_url': 'https://mountainvoices.org/i_glossary.html',
            'attribution': 'Panos London, Mountain Voices oral testimony project',
            'quality_flags': [
                'regional_glossary', 'language_identity_requires_native_review',
                'publisher_license_not_stated',
            ],
        }
        row = {
            'text_sha256': 'd' * 64,
            'text': 'Andolan',
            'provenance': [source],
        }

        exported = m.catalog_row(row)

        self.assertEqual(exported['text'], 'Andolan')
        self.assertTrue(exported['text_publicly_available'])
        self.assertEqual(exported['redistribution_status'], 'reproduced_under_source_policy')
        self.assertEqual(
            exported['commercial_use_status'],
            'not_explicitly_addressed_by_source_policy',
        )
        self.assertEqual(
            exported['public_rights_basis'][0]['model_training_status'],
            'separate_model_training_permission_not_established',
        )
        self.assertEqual(
            exported['public_rights_basis'][0]['license_id'],
            'LicenseRef-Panos-Source-Policy-Restricted',
        )
        self.assertEqual(
            exported['public_rights_basis'][0]['permitted_audiences'],
            ['press', 'educational institutions', 'research institutions', 'nonprofit organisations'],
        )
        self.assertIsNone(m.panos_reproduction_policy_provenance({
            **source, 'record_id': 'mountainvoices_local_glossary:194',
        }))
        self.assertIsNone(m.panos_reproduction_policy_provenance({
            **source, 'source_id': 'other_glossary',
        }))

    def test_individual_word_fact_projection_does_not_clear_dictionary_expression(self):
        source = {
            'source_id': 'languageshome',
            'record_id': 'languageshome:18',
            'source_url': 'https://www.languageshome.com/English-Garhwali.htm',
            'license_id': 'not_stated',
            'rights_status': 'not_recorded',
        }
        word = {
            'text_sha256': 'e' * 64,
            'text': 'Jitun',
            'provenance': [source],
        }

        exported = m.catalog_row(word)

        self.assertEqual(exported['text'], 'Jitun')
        self.assertEqual(exported['redistribution_status'], 'individual_word_fact')
        self.assertFalse(m.is_public_garhwali_text_row(word))
        self.assertEqual(
            exported['factual_publication_basis'][0]['basis_type'],
            'individual_lexical_token_only',
        )
        self.assertNotIn('record_id', exported['factual_publication_basis'][0])
        self.assertTrue(all('record_id' not in item for item in exported['sources']))
        self.assertIsNone(m.catalog_row({
            **word, 'text': 'Jitun aa',
        })['text'])
        self.assertIsNone(m.catalog_row({
            **word, 'provenance': [{**source, 'record_id': 'languageshome:19'}],
        })['text'])

    def test_thematic_lexicon_token_is_fact_only_and_ocr_is_not(self):
        source = {
            'source_id': 'emagazine_animals',
            'record_id': 'emagazine_animals:28:1',
            'source_url': 'https://e-magazineofuttarakhand.blogspot.com/2012/02/names-of-animals-birds-etc-in-garhwali.html',
            'license_id': 'LicenseRef-All-Rights-Reserved',
            'rights_status': 'not_recorded',
            'genre': 'thematic_lexicon',
            'quality_flags': ['community_compilation', 'needs_native_review'],
        }
        corroborating_source = {
            **source,
            'source_id': 'uttarakhandiwords_animals',
            'record_id': 'uttarakhandiwords_animals:45:1',
            'source_url': 'https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html',
        }
        word = {
            'text_sha256': 'f' * 64,
            'text': 'काखड़',
            'provenance': [source, corroborating_source],
        }

        exported = m.catalog_row(word)

        self.assertEqual(exported['text'], 'काखड़')
        self.assertEqual(exported['redistribution_status'], 'individual_word_fact')
        self.assertFalse(m.is_public_garhwali_text_row(word))
        self.assertNotIn('record_id', exported['sources'][0])
        self.assertIsNone(m.catalog_row({
            **word, 'provenance': [source],
        })['text'])
        self.assertIsNone(m.catalog_row({
            **word, 'text': 'काखड़ पशु',
        })['text'])
        self.assertIsNone(m.catalog_row({
            **word, 'provenance': [source, {
                **corroborating_source, 'quality_flags': ['uncorrected_ocr'],
            }],
        })['text'])
        self.assertIsNone(m.catalog_row({
            **word, 'provenance': [{**source, 'source_id': 'other_site'}],
        })['text'])

    def test_catalog_adds_known_source_locator_without_changing_rights(self):
        row = {
            'text_sha256': 'a' * 64,
            'text': 'काखड़',
            'provenance': [{
                'source_id': 'emagazine_animals',
                'license_id': 'LicenseRef-All-Rights-Reserved',
                'license_url': 'https://e-magazineofuttarakhand.blogspot.com/2012/02/names-of-animals-birds-etc-in-garhwali.html',
                'rights_status': 'not_recorded',
                'genre': 'thematic_lexicon',
                'quality_flags': ['needs_native_review'],
            }, {
                'source_id': 'uttarakhandiwords_animals',
                'license_id': 'LicenseRef-All-Rights-Reserved',
                'license_url': 'https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html',
                'rights_status': 'not_recorded',
                'genre': 'thematic_lexicon',
            }],
        }

        exported = m.catalog_row(row)

        sources = {item['source_id']: item for item in exported['sources']}
        self.assertEqual(
            sources['emagazine_animals']['source_url'],
            'https://e-magazineofuttarakhand.blogspot.com/2012/02/names-of-animals-birds-etc-in-garhwali.html',
        )
        self.assertEqual(
            sources['uttarakhandiwords_animals']['source_url'],
            'https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html',
        )
        self.assertEqual(
            sources['emagazine_animals']['license_id'],
            'LicenseRef-All-Rights-Reserved',
        )
        self.assertEqual(
            sources['emagazine_animals']['rights_status'], 'not_recorded'
        )

    def test_catalog_resolves_item_url_from_stable_social_capture_reference(self):
        row = {
            'text_sha256': 'b' * 64,
            'text': 'Garhwali social example',
            'provenance': [{
                'source_id': 'records',
                'file': 'data/extracted/social_garhwali/records.jsonl',
                'line': 1,
                'record_id': 'social-garhwali:0001',
                'rights_status': 'public_social_post_no_open_license_recorded',
                'training_eligible': False,
            }],
        }
        with patch.object(m, 'source_record_locator', return_value={
            'source_url': 'https://www.reddit.com/r/example/comments/post',
            'source_title': 'Example post',
            'source_kind': 'social_media_reddit',
        }):
            exported = m.catalog_row(row)

        self.assertEqual(
            exported['sources'][0]['source_url'],
            'https://www.reddit.com/r/example/comments/post',
        )
        self.assertEqual(
            exported['sources'][0]['rights_status'],
            'public_social_post_no_open_license_recorded',
        )

    def test_public_knowledge_projection_keeps_facts_and_drops_expressive_fields(self):
        row = m.knowledge_row({
            'record_id': 'work:example',
            'title': 'Example Title',
            'creators': ['A. Author'],
            'notes': 'Unlicensed descriptive paragraph',
            'source_ids': ['catalog-source'],
        }, 'literary_works', source_catalog={
            'catalog-source': {
                'title': 'Example source capture',
                'local_capture': 'sources/manual/example.md',
            },
        })
        exported = m.public_factual_metadata_row(row, 'literary_works')
        self.assertEqual(exported['title'], 'Example Title')
        self.assertEqual(exported['creators'], ['A. Author'])
        self.assertNotIn('notes', exported)
        self.assertFalse(exported['expressive_source_content_included'])
        self.assertEqual(exported['record_scope'], 'factual_bibliographic_metadata_only')
        self.assertTrue(m.is_public_factual_metadata_row(exported, 'literary_works'))
        self.assertEqual(
            exported['provenance'][0]['source_capture_path'],
            'sources/manual/example.md',
        )
        self.assertEqual(exported['quality_metadata']['review_status'], 'not_reviewed')
        self.assertFalse(m.is_public_factual_metadata_row(
            {**exported, 'notes': 'expressive text'}, 'literary_works'
        ))

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

    def test_dataset_card_declares_each_split_once_for_sharded_configs(self):
        report = {
            'release_id': 'test',
            'profile': 'all-data',
            'configs': {
                'catalog/train': {
                    'records': 2,
                    'files': ['train-00000.jsonl', 'train-00001.jsonl'],
                },
                'record_index/train': {
                    'records': 2,
                    'files': ['train-00000.jsonl'],
                },
            },
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 0,
            'catalog_records': 2,
            'catalog_redacted_text_records': 0,
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
        }

        card = m.dataset_card(report)

        self.assertEqual(card.count('  - split: train'), 2)
        self.assertIn('path: data/catalog/train-*.jsonl', card)
        self.assertIn('path: data/record_index/train-*.jsonl', card)
        self.assertNotIn('path: data/catalog/train-00001.jsonl', card)

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
            'structured_knowledge_excluded_for_rights': {'geography': 0},
            'structured_knowledge_metadata_only': {'geography': 50},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
        }
        card = m.dataset_card(report)
        self.assertIn('public-profile package', card)
        self.assertIn('## Project history', card)
        self.assertIn('## Developer quick start', card)
        self.assertIn('## Configurations and current row counts', card)
        self.assertIn('across 1 named configuration (1 config/split entries)', card)
        self.assertIn('All **50 structured geography, history, literature, song, and research records**', card)
        self.assertIn('factual/bibliographic form', card)
        self.assertNotIn('university-research resources built by the Garhwali Language Lab', card)
        self.assertNotIn('config_name: geography', card)
        self.assertIn('For retained catalog entries, the full text not included in this public profile remains in the local all-data package', card)
        self.assertIn('Garhwali Speech', card)
        self.assertIn('rushilrawat/garhwali-speech', card)

    def test_v0_2_1_public_card_documents_source_delta_and_keeps_quality_limits(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.1',
            'profile': 'public',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 1,
            'catalog_records': 2,
            'catalog_redacted_text_records': 1,
            'structured_knowledge_excluded_for_rights': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'source_expansion': {
                'jambu': {
                    'source_records': 763,
                    'unique_forms': 738,
                    'cross_source_overlap': 28,
                    'new_vs_other_sources': 710,
                    'already_in_current_corpus': 738,
                },
                'language_library': {
                    'source_records': 180,
                    'unique_strings': 180,
                    'cross_source_overlap': 16,
                    'new_vs_current_corpus': 164,
                    'records_by_type': {'lexicon': 131, 'phrase': 33, 'proverb': 10, 'riddle': 6},
                },
            },
        }

        card = m.dataset_card(report)

        self.assertIn('Release: **garhwali-language-lab-v0.2.1**', card)
        self.assertIn('source additions included in v0.2.1', card)
        self.assertIn('164 exact-new', card)
        self.assertLess(card.index('v0.1.x — establish the corpus workflow'),
                        card.index('v0.2.1 — continue the corpus and make it easier to use'))
        self.assertIn('strings. Types: lexicon 131', card)
        self.assertRegex(card, r'adds \*\*0\*\*\s+new forms')
        self.assertIn('generated inflection forms are excluded', card)
        self.assertIn(
            'Neither source entry has received native-speaker review',
            ' '.join(card.split()),
        )

    def test_public_card_distinguishes_empty_speech_drafts_from_audio_hash_rows(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.1',
            'profile': 'public',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 5,
            'draft_unique_nonempty_audio': 3,
            'draft_empty_audio': 2,
            'catalog_records': 2,
            'catalog_redacted_text_records': 1,
            'structured_knowledge_excluded_for_rights': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
        }

        card = m.dataset_card(report)

        self.assertIn('The SraVaani draft config covers **5 unique audio hashes**', card)
        self.assertIn('**3** have non-empty draft text and **2** are empty', card)
        self.assertNotIn('including transcripts for **5', card)

    def test_v0_2_2_card_describes_traceability_and_text_expansion(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.2',
            'profile': 'public',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 1,
            'catalog_records': 2,
            'catalog_redacted_text_records': 1,
            'structured_knowledge_excluded_for_rights': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'text_expansion_metrics': {'records': 1658, 'recommended_for_training': 607},
        }
        card = m.dataset_card(report)
        self.assertIn('Release: **garhwali-language-lab-v0.2.2**', card)
        self.assertIn('v0.2.2 — improve traceability and report usable counts', card)
        self.assertIn('deduplicated `text_expansion` view', card)
        self.assertIn('`text_expansion` config adds **1,658** Garhwali candidate texts', card)
        self.assertIn("**607** currently meet the project's conservative training-recommendation rule", card)
        self.assertIn('**1,051** do not pass the current source-eligibility or quality gates', card)
        self.assertIn('figures below describe the current v0.2.2 package', card)

    def test_v0_2_7_card_explains_paharili_addition_and_rights_limits(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.7',
            'profile': 'public',
            'configs': {
                'paharili_gbm/train': {'records': 11989},
                'paharili_gbm/test': {'records': 2995},
                'paharili_gbm/source_overlap': {'records': 4},
            },
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 0,
            'catalog_records': 0,
            'catalog_redacted_text_records': 0,
            'structured_knowledge_excluded_for_rights': {},
            'structured_knowledge_metadata_only': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'paharili_gbm_metrics': {
                'garhwali_source_records': 15000,
                'normalized_unique_source_texts': 14989,
                'collapsed_duplicate_source_records': 11,
                'already_present_in_existing_configs': 1,
                'new_records': 14988,
                'split_records': {'source_overlap': 4, 'test': 2995, 'train': 11989},
            },
        }

        card = m.dataset_card(report)

        self.assertIn('config_name: paharili_gbm', card)
        self.assertIn('adds **14,988 normalized-unique Garhwali-labeled sentence records**', card)
        self.assertIn('11 repeated source rows', card)
        self.assertIn('4 text groups that occur in both upstream splits', card)
        self.assertIn('README does not identify the sentence-level source of each item', card)

    def test_v0_2_4_card_documents_metadata_only_attribution_update(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.4',
            'profile': 'public',
            'configs': {'text/train': {'records': 1}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 0,
            'catalog_records': 1,
            'catalog_redacted_text_records': 0,
            'structured_knowledge_excluded_for_rights': {},
            'structured_knowledge_metadata_only': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'text_expansion_metrics': {},
            'text_resource_metrics': {'records': 1, 'recommended_for_training': 0},
        }

        card = m.dataset_card(report)

        flattened_card = ' '.join(card.split())
        self.assertIn('v0.2.4 — improve source attribution and revision traceability', flattened_card)
        self.assertIn('creator attribution for 36 existing Tatoeba sentences', flattened_card)
        self.assertIn('319 existing Wikimedia and Wiktionary records', flattened_card)
        self.assertIn('No new text is added', flattened_card)
        self.assertIn('**0** are currently recommended for training', flattened_card)
        self.assertLess(flattened_card.index('v0.2.2 — improve traceability'),
                        flattened_card.index('v0.2.3 — surface additional'))

    def test_v0_2_5_card_documents_source_overlap_split(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.5',
            'profile': 'public',
            'configs': {'text/train': {'records': 2}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 0,
            'catalog_records': 2,
            'catalog_redacted_text_records': 0,
            'structured_knowledge_excluded_for_rights': {},
            'structured_knowledge_metadata_only': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'text_source_overlap_records': 1308,
            'text_expansion_metrics': {
                'records': 1647,
                'recommended_for_training': 0,
                'source_split_overlap_records': 363,
            },
            'text_resource_metrics': {'records': 246, 'recommended_for_training': 0},
        }

        card = ' '.join(m.dataset_card(report).split())

        self.assertIn('v0.2.5 — prevent upstream evaluation-source overlap', card)
        self.assertIn('routes text linked to upstream Meta/VAANI development or test sources', card)
        self.assertIn('text/source_overlap', card)
        self.assertIn('**1,308** rows previously assigned to `text/train`', card)
        self.assertIn('**363** similar catalog additions', card)
        self.assertIn('The text package preserves every row', card)

    def test_card_can_declare_explicit_features_for_problematic_config(self):
        report = {
            'release_id': 'garhwali-language-lab-v0.2.5',
            'profile': 'public',
            'configs': {'text_expansion/train': {'records': 1}},
            'linked_audio_files': 0,
            'include_audio': False,
            'draft_unique_audio': 0,
            'catalog_records': 0,
            'catalog_redacted_text_records': 0,
            'structured_knowledge_excluded_for_rights': {},
            'structured_knowledge_metadata_only': {},
            'drafts_complete': True,
            'draft_third_checkpoint_records': 0,
            'draft_three_checkpoint_review_records': 0,
            'draft_audio_grounded_review_records': 0,
            'draft_source_label_conflicts': 0,
            'text_expansion_metrics': {
                'records': 1, 'recommended_for_training': 0,
                'source_split_overlap_records': 0,
            },
            'text_resource_metrics': {'records': 0, 'recommended_for_training': 0},
        }
        dataset_info = [{
            'config_name': 'text_expansion',
            'features': [{'name': 'dialect_quality', 'struct': [
                {'name': 'dialect_labels', 'list': {'dtype': 'string'}},
            ]}],
        }]

        card = m.dataset_card(report, dataset_info=dataset_info)
        metadata_line = next(
            line for line in card.splitlines() if line.startswith('dataset_info: ')
        )

        self.assertEqual(json.loads(metadata_line.partition(': ')[2]), dataset_info)

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

    def test_audio_export_uses_string_for_missing_speaker(self):
        exported = m.audio_row(
            {'audio_sha256': 'ab' * 32, 'asr_target_clean': 'गढ़वाली'},
            transcript_field='asr_target_clean', include_audio_reference=False,
        )
        self.assertEqual(exported['speaker_id'], '')

    def test_draft_evidence_json_is_stable_and_preserves_sparse_values(self):
        row = {
            'audio_sha256': 'ab' * 32,
            'machine_transcript': 'गढ़वाली',
            'machine_transcript_quality': {'flags': ['mixed_script']},
            'quality_flags': [],
            'training_quality_flags': ['needs_review'],
            'recovery_adjudication': {'automatic_correction': False},
        }

        exported = m.audio_row(
            row, 'machine_transcript', serialize_evidence=True
        )

        self.assertEqual(
            json.loads(exported['machine_transcript_quality']),
            {'flags': ['mixed_script']},
        )
        self.assertEqual(json.loads(exported['quality_flags']), [])
        self.assertEqual(
            json.loads(exported['training_quality_flags']), ['needs_review']
        )
        self.assertEqual(
            json.loads(exported['recovery_adjudication']),
            {'automatic_correction': False},
        )
        self.assertEqual(exported['recovery_confidence'], '')
        self.assertEqual(exported['audio_grounded_review'], '')
        self.assertFalse(exported['active_for_source_error_analysis'])
        self.assertEqual(exported['language_scope_status'], '')

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
            final_row = json.loads(paths[-1].read_text())
            for field in (
                'rights_status', 'reuse_scope', 'license_labels',
                'quality_status', 'record_quality_flags',
            ):
                self.assertIn(field, final_row)
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
