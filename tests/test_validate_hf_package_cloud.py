import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate_hf_package_cloud as m


class HuggingFaceCloudValidationTests(unittest.TestCase):
    def _write_schema_v1_package(self, root, row):
        package = root / 'package'
        for relative in (
            'README.md', 'LICENSE_POLICY.md', 'ATTRIBUTION.md',
            'REMOVAL_POLICY.md', 'DEVELOPER_QUICKSTART.md',
            'DATASET_SCHEMA.md', 'search_garhwali_lexicon.py',
            'research/text-rights-resolution-2026-09-30.md',
        ):
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture\n')
        shard = package / 'data/lexicon/train-00000.jsonl'
        shard.parent.mkdir(parents=True, exist_ok=True)
        shard.write_text(json.dumps(row) + '\n')
        (package / 'manifest.json').write_text(json.dumps({
            'release_id': 'garhwali-language-lab-v0.2.1',
            'profile': 'public',
            'record_schema_version': '1.0.0',
            'configs': {'lexicon/train': {
                'files': [shard.name], 'records': 1,
                'file_sha256': {shard.name: m.sha256(shard)},
            }},
        }))
        return package

    def test_preflight_rejects_upstream_heldout_record_left_in_train(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._write_schema_v1_package(root, {
                'id': 'placeholder', 'rights_status': 'not_assessed',
                'reuse_scope': 'not assessed', 'license_labels': [],
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
            })
            (package / 'data/lexicon/train-00000.jsonl').unlink()
            text = 'गढ़वाली वाक्य।'
            row = {
                'id': hashlib.sha256(text.encode('utf-8')).hexdigest(),
                'text': text, 'language': 'gbm', 'source_languages': ['gbm'],
                'language_buckets': ['garhwali_candidate'],
                'quality_tiers': ['experimental_review'], 'quality_flags': [],
                'recommended_for_training': False, 'split': 'train',
                'public_rights_basis': [], 'rights_status': 'not_assessed',
                'reuse_scope': 'not assessed', 'license_labels': [],
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
                'provenance': [{
                    'source_id': 'meta_omni', 'record_id': 'meta:test:1',
                    'training_eligible': False,
                }],
                'source_split_overlap_status': 'no_upstream_eval_match_detected',
                'source_split_overlap_source_ids': [],
            }
            shard = package / 'data/text/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps(row, ensure_ascii=False) + '\n')
            audit = package / 'research/huggingface-upstream-split-overlap-2026-10-05.json'
            audit.parent.mkdir(parents=True, exist_ok=True)
            audit.write_text('{}\n')
            (audit.parent / 'huggingface-upstream-split-overlap-2026-10-05.md').write_text('audit\n')
            manifest_path = package / 'manifest.json'
            manifest = json.loads(manifest_path.read_text())
            manifest['configs'] = {'text/train': {
                'files': [shard.name], 'records': 1,
                'file_sha256': {shard.name: m.sha256(shard)},
            }}
            manifest['upstream_split_overlap_audit'] = {
                'schema_version': 'garhwali-upstream-split-overlap-v1',
                'sha256': m.sha256(audit),
            }
            manifest_path.write_text(json.dumps(manifest))
            output = root / 'preflight.json'
            with (
                patch.object(m, 'upstream_split_overlap_ids',
                             return_value=({'meta:test:1'}, set())),
                patch.object(sys, 'argv', [
                    'validate_hf_package_cloud.py', '--package', str(package),
                    '--output', str(output),
                ]),
                contextlib.redirect_stdout(io.StringIO()),
                self.assertRaises(SystemExit),
            ):
                m.main()
            report = json.loads(output.read_text())

        self.assertIn('upstream_eval_overlap_left_in_train:text/train:1', report['errors'])
        self.assertIn('source_split_evidence_mismatch:text/train:2', report['errors'])

    def test_record_schema_envelope_accepts_empty_optional_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._write_schema_v1_package(root, {
                'id': 'word-a', 'rights_status': 'not_assessed',
                'reuse_scope': 'not assessed', 'license_labels': [],
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
            })
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['record_schema_version'], '1.0.0')

    def test_quality_status_and_detailed_evidence_are_distinct_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._write_schema_v1_package(root, {
                'id': 'word-a', 'rights_status': 'not_assessed',
                'reuse_scope': 'not assessed', 'license_labels': [],
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
                'quality_flags': [],
            })
            shard = package / 'data/lexicon/train-00000.jsonl'
            rows = [
                json.loads(shard.read_text(encoding='utf-8')),
                {
                    'id': 'word-b', 'rights_status': 'licensed',
                    'reuse_scope': 'attribution', 'license_labels': ['CC-BY-4.0'],
                    'quality_status': 'automated_quality_assessed_unreviewed',
                    'record_quality_flags': [], 'quality_flags': ['script_check'],
                },
            ]
            shard.write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8'
            )
            manifest_path = package / 'manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            config = manifest['configs']['lexicon/train']
            config['records'] = len(rows)
            config['file_sha256'][shard.name] = m.sha256(shard)
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            report = json.loads(output.read_text())

        stats = report['configs']['lexicon/train']
        self.assertEqual(stats['rows_with_quality_status'], 2)
        self.assertEqual(stats['rows_with_quality_evidence_fields_present'], 2)
        self.assertEqual(stats['rows_with_nonempty_quality_evidence'], 1)
        self.assertEqual(stats['rows_with_quality_metadata'], 2)
        self.assertEqual(stats['rows_with_provenance_array'], 0)
        self.assertEqual(stats['rights_status_counts'], {
            'licensed': 1, 'not_assessed': 1,
        })
        self.assertEqual(stats['reuse_scope_counts'], {
            'attribution': 1, 'not assessed': 1,
        })
        self.assertEqual(stats['license_label_counts'], {'CC-BY-4.0': 1})
        self.assertEqual(stats['rows_with_public_rights_basis'], 0)
        self.assertIn('not a human-review or correctness measure', report['metric_definitions']['rows_with_nonempty_quality_evidence'])
        self.assertIn(
            'values are counted as-is',
            report['metric_definitions']['rights_status_counts'],
        )

    def test_traceability_accepts_stable_item_references_and_attributed_urls(self):
        self.assertTrue(m.has_source_traceability('lexicon', {
            'provenance': [{
                'source_id': 'dictionary-a', 'record_id': 'dictionary-a:line-8',
            }],
        }))
        self.assertTrue(m.has_source_traceability('source_catalog', {
            'source_ref_id': 'stable-source-reference',
            'source_id': 'tatoeba',
            'attribution': 'Tatoeba sentence 4648070; see sentence history for attribution',
        }))

    def test_scorecard_measures_traceability_with_a_config_appropriate_locator(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._write_schema_v1_package(root, {
                'id': 'word-a', 'rights_status': 'not_assessed',
                'reuse_scope': 'not assessed', 'license_labels': [],
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
                'provenance': [{
                    'source_id': 'dictionary-a',
                    'source_url': 'https://example.org/entry/word-a',
                }],
            })
            shard = package / 'data/lexicon/train-00000.jsonl'
            rows = [
                json.loads(shard.read_text(encoding='utf-8')),
                {
                    'id': 'word-b', 'rights_status': 'not_assessed',
                    'reuse_scope': 'not assessed', 'license_labels': [],
                    'quality_status': 'not_reviewed', 'record_quality_flags': [],
                    'provenance': [{'source_id': 'dictionary-b'}],
                },
            ]
            shard.write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8'
            )
            manifest_path = package / 'manifest.json'
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            config = manifest['configs']['lexicon/train']
            config['records'] = len(rows)
            config['file_sha256'][shard.name] = m.sha256(shard)
            manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            report = json.loads(output.read_text())

        stats = report['configs']['lexicon/train']
        self.assertEqual(stats['rows_with_source_traceability'], 1)
        self.assertEqual(stats['rows_without_source_traceability'], 1)
        self.assertIn(
            'does not establish reuse rights',
            report['metric_definitions']['rows_with_source_traceability'],
        )

    def test_record_schema_envelope_rejects_missing_and_wrongly_typed_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._write_schema_v1_package(root, {
                'id': 'word-a', 'rights_status': 7,
                'reuse_scope': 'not assessed', 'license_labels': 'MIT',
                'quality_status': 'not_reviewed', 'record_quality_flags': [],
            })
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'record_envelope_missing_rights_status:lexicon/train:1',
            report['errors'],
        )
        self.assertIn(
            'record_envelope_invalid_license_labels:lexicon/train:1',
            report['errors'],
        )

    def test_public_reference_index_tables_are_validated_as_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            rows = {
                'record_index': {'record_ref': 'r1'},
                'source_catalog': {'source_ref_id': 's1'},
                'record_sources': {'record_ref': 'r1', 'source_ref_id': 's1'},
            }
            configs = {}
            table_report = {}
            for name, row in rows.items():
                shard = package / f'data/{name}/train-00000.jsonl'
                shard.parent.mkdir(parents=True, exist_ok=True)
                shard.write_text(json.dumps(row) + '\n')
                digest = m.sha256(shard)
                configs[f'{name}/train'] = {
                    'files': [shard.name], 'records': 1,
                    'file_sha256': {shard.name: digest},
                }
                table_report[name] = {
                    'file': f'data/{name}/{shard.name}',
                    'records': 1, 'sha256': digest,
                }
            (package / 'reference_index_manifest.json').write_text('{}\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'garhwali-language-lab-v0.2.0',
                'profile': 'public',
                'reference_index': {'tables': table_report},
                'configs': configs,
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['errors'], [])
        self.assertEqual(
            report['run_id'], 'garhwali-hf-public-cloud-validation-v0.2.0'
        )

    def test_duplicate_identity_fails_and_json_output_is_exact_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/text/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(
                '{"id":"same","text":"अ"}\n{"id":"same","text":"ब"}\n'
            )
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'text/train': {
                    'files': ['train-00000.jsonl'], 'records': 2,
                    'file_sha256': {'train-00000.jsonl': '0' * 64},
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(
            report['run_id'], 'garhwali-hf-all-data-cloud-validation-v0.1'
        )
        self.assertIn('duplicate_identity:text/train:1', report['errors'])
        self.assertIn('file_hash_mismatch:text/train:train-00000.jsonl', report['errors'])

    def test_structured_knowledge_requires_source_quality_and_rights_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text('{"id":"place-a"}\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertIn(
            'knowledge_missing_source_provenance:geography/train:1',
            report['errors'],
        )
        self.assertIn(
            'knowledge_missing_quality_metadata:geography/train:1',
            report['errors'],
        )
        self.assertIn(
            'knowledge_missing_rights_status:geography/train:1',
            report['errors'],
        )

    def test_structured_knowledge_source_id_alone_is_not_traceable_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            row = {
                'id': 'place-a',
                'knowledge_family': 'geography',
                'provenance': [{'source_id': 'source-without-locator'}],
                'quality_metadata': {'review_status': 'not_reviewed'},
                'rights_status': 'not_assessed',
            }
            shard.write_text(json.dumps(row) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'all-data',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                    'file_sha256': {'train-00000.jsonl': m.sha256(shard)},
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertIn(
            'knowledge_untraceable_source_provenance:geography/train:1',
            report['errors'],
        )

    def test_preflight_rejects_inconsistent_training_recommendation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/text/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps({
                'id': 'text-a',
                'text': 'Garhwali context',
                'language': 'mul',
                'source_languages': ['eng', 'gbm'],
                'language_buckets': ['mixed_language'],
                'quality_tiers': ['experimental_review'],
                'quality_flags': [],
                'public_rights_basis': [{'license_id': 'CC-BY-4.0'}],
                'recommended_for_training': True,
            }) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'public',
                'configs': {'text/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertIn('invalid_training_recommendation:text/train:1', report['errors'])

    def test_public_preflight_requires_structured_public_rights_basis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            shard.write_text(json.dumps({
                'id': 'place-a',
                'knowledge_family': 'geography',
                'provenance': [{'source_id': 'gazetteer'}],
                'quality_metadata': {'review_status': 'not_reviewed'},
                'rights_status': 'not_assessed',
            }) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'public',
                'configs': {'geography/train': {
                    'files': ['train-00000.jsonl'], 'records': 1,
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(
            report['run_id'], 'garhwali-hf-public-cloud-validation-v0.1'
        )
        self.assertIn('knowledge_missing_public_rights:geography/train:1', report['errors'])

    def test_public_factual_metadata_projection_needs_no_underlying_work_license(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'package'
            shard = package / 'data/geography/train-00000.jsonl'
            shard.parent.mkdir(parents=True)
            row = {
                'id': 'place-a',
                'name': 'Example place',
                'knowledge_family': 'geography',
                'record_scope': 'factual_bibliographic_metadata_only',
                'rights_status': 'metadata_only; no license asserted for underlying work',
                'expressive_source_content_included': False,
                'omitted_content_fields': ['source_passages', 'full_work_text'],
                'provenance': [{
                    'source_id': 'user-capture',
                    'source_capture_path': 'sources/manual/example.md',
                }],
                'public_metadata_note': 'Names and source citations only.',
                'quality_metadata': {'review_status': 'not_reviewed'},
                'reuse_scope': 'metadata facts only; underlying-work rights are not asserted',
                'license_labels': [],
                'quality_status': 'not_reviewed',
                'record_quality_flags': [],
            }
            self.assertTrue(m.is_public_factual_metadata_row(row, 'geography'))
            shard.write_text(json.dumps(row) + '\n')
            (package / 'manifest.json').write_text(json.dumps({
                'release_id': 'candidate',
                'profile': 'public',
                'configs': {'geography/train': {
                    'files': [shard.name], 'records': 1,
                    'file_sha256': {shard.name: m.sha256(shard)},
                }},
            }))
            output = root / 'preflight.json'
            with patch.object(sys, 'argv', [
                'validate_hf_package_cloud.py', '--package', str(package),
                '--output', str(output),
            ]), contextlib.redirect_stdout(io.StringIO()):
                m.main()
            report = json.loads(output.read_text())
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['errors'], [])
        self.assertFalse(m.is_public_factual_metadata_row(
            {**row, 'notes': 'unlicensed expressive passage'}, 'geography'
        ))
