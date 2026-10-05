import json
import tempfile
import unittest
from pathlib import Path

from audit_benchmark_v02_rights import audit


class BenchmarkRightsAuditTests(unittest.TestCase):
    def test_reports_per_view_clearance_and_recommended_text_basis(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp)
            (draft / 'manifest.json').write_text(json.dumps({
                'total_records': 4,
                'public_upload_allowed': False,
            }), encoding='utf-8')
            rows = [
                {
                    'view': 'text_recommended/train',
                    'rights': {'public_release_cleared': False, 'public_rights_basis_as_recorded': [
                        {
                            'rights_status': 'rights_assessed_compatible',
                            'source_id': 'open_a',
                            'attribution': 'Creator name',
                            'license_url': 'https://example.test/license',
                            'source_url': 'https://example.test/source',
                        },
                        {'rights_status': 'rights_assessed_compatible', 'source_id': 'open_b'},
                    ]},
                    'privacy': {'public_upload_allowed': False},
                },
                {
                    'view': 'text_recommended/train',
                    'rights': {'public_release_cleared': False, 'public_rights_basis_as_recorded': [
                        {'rights_status': 'not_recorded', 'source_id': 'open_b'},
                    ]},
                    'privacy': {'public_upload_allowed': False},
                },
                {
                    'view': 'external/flores',
                    'provenance': {
                        'attribution': 'source attribution',
                        'source_id': 'flores',
                        'provenance': {
                            'url': 'https://example.test/snapshot',
                            'sha256': 'abc123',
                            'retrieved_at': '2026-10-05T00:00:00Z',
                        },
                    },
                    'payload': {'source_example': {'source': 'source', 'target': 'target'}},
                    'rights': {
                        'public_release_cleared': False,
                        'declared_license_id': 'CC-BY-SA-4.0',
                        'component_rights_status': 'not_assessed',
                        'redistribution_status': 'not_cleared',
                    },
                    'privacy': {'public_upload_allowed': False},
                    'usage': {'training_eligibility_as_recorded': False, 'usage_label': 'dev_select'},
                },
                {
                    'view': 'internal/asr',
                    'rights': {'public_release_cleared': False, 'license_declaration': 'CC-BY-4.0'},
                    'privacy': {
                        'public_upload_allowed': False,
                        'contains_local_audio_locator': True,
                        'contains_local_identifiers': True,
                    },
                },
            ]
            (draft / 'records.jsonl').write_text(
                ''.join(json.dumps(row) + '\n' for row in rows), encoding='utf-8',
            )

            result = audit(draft)

        self.assertEqual(result['view_rows'], 4)
        self.assertEqual(result['manifest_public_upload_allowed'], False)
        self.assertEqual(result['public_upload_allowed_by_value'], {'False': 4})
        self.assertEqual(result['public_release_cleared_by_value'], {'False': 4})
        self.assertEqual(result['recommended_text_rights_rows'], {
            'all_components_compatible': 1,
            'all_components_not_recorded': 1,
        })
        self.assertEqual(result['recommended_text_rows_with_basis_by_source'], {
            'open_a': 1,
            'open_b': 2,
        })
        self.assertEqual(result['recommended_text_basis_components_by_source'], {
            'open_a': 1,
            'open_b': 2,
        })
        self.assertEqual(result['external_declared_license_rows'], {'CC-BY-SA-4.0': 1})
        self.assertEqual(result['external_provenance_coverage_by_view'], {
            'external/flores': {
                'attribution_present': 1,
                'source_id_present': 1,
                'source_snapshot_url_present': 1,
                'source_snapshot_sha256_present': 1,
                'source_snapshot_retrieved_at_present': 1,
                'source_example_present': 1,
                'source_example_source_url_present': 0,
                'source_example_target_url_present': 0,
            },
        })
        self.assertEqual(result['external_training_eligibility_by_view'], {
            'external/flores': {'False': 1},
        })
        self.assertEqual(result['external_rights_statuses_by_view'], {
            'external/flores': {
                'component_rights_status=not_assessed': 1,
                'redistribution_status=not_cleared': 1,
                'rights_status=missing': 1,
            },
        })
        self.assertEqual(result['recommended_text_rights_evidence_coverage_by_source'], {
            'open_a': {
                'attribution_present': 1,
                'author_present': 0,
                'license_url_present': 1,
                'source_url_present': 1,
                'rights_evidence_present': 0,
                'source_snapshot_sha256_present': 0,
                'source_pdf_sha256_present': 0,
            },
            'open_b': {
                'attribution_present': 0,
                'author_present': 0,
                'license_url_present': 0,
                'source_url_present': 0,
                'rights_evidence_present': 0,
                'source_snapshot_sha256_present': 0,
                'source_pdf_sha256_present': 0,
            },
        })
        self.assertEqual(result['asr_license_declaration_rows'], {'CC-BY-4.0': 1})
        self.assertEqual(result['asr_local_field_flags'], {
            'contains_local_audio_locator=True': 1,
            'contains_local_identifiers=True': 1,
        })

    def test_rejects_manifest_row_count_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp)
            (draft / 'manifest.json').write_text(json.dumps({'total_records': 1}), encoding='utf-8')
            (draft / 'records.jsonl').write_text('{}\n{}\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'does not match manifest'):
                audit(draft)


if __name__ == '__main__':
    unittest.main()
