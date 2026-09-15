import unittest

import audit_text_sources as m


class TextSourceAuditTests(unittest.TestCase):
    def test_audit_accounts_for_open_overlap_and_blocked_only_rows(self):
        rows = [
            {
                'text_sha256': 'a',
                'quality_v2': {'tier': 'strict_gold_candidate'},
                'provenance': [
                    {'source_id': 'open', 'license_id': 'CC-BY-4.0'},
                    {
                        'source_id': 'mirror',
                        'license_id': 'CC-BY-4.0',
                        'rights_status': 'component_rights_review_required',
                    },
                ],
            },
            {
                'text_sha256': 'b',
                'quality_v2': {'tier': 'high_quality_rights_pending'},
                'provenance': [{
                    'source_id': 'web',
                    'rights_status': 'public_webpage_no_open_license_stated',
                }],
            },
        ]
        report = m.audit_rows(rows, review_rows=[])
        self.assertEqual(report['records'], 2)
        self.assertEqual(report['public_text_records'], 1)
        self.assertEqual(report['rights_pending_text_records'], 1)
        self.assertEqual(report['mixed_rights_exact_duplicate_records'], 1)
        self.assertEqual(report['strict_records_using_open_overlap'], 1)
        self.assertEqual(report['high_quality_rights_pending_records'], 1)
        self.assertEqual(report['source_summary']['open']['open_basis_records'], 1)
        self.assertEqual(report['source_summary']['mirror']['blocked_records'], 1)
        self.assertEqual(report['source_summary']['web']['blocked_records'], 1)

    def test_review_queue_is_grouped_by_source_and_priority(self):
        rows = [{
            'text_sha256': 'a',
            'quality_v2': {'tier': 'experimental_review'},
            'provenance': [{'source_id': 'open', 'license_id': 'CC-BY-4.0'}],
        }]
        review = [{
            'text_sha256': 'a',
            'review_priority': {'label': 'romanized_orthography'},
            'provenance': [{'source_id': 'open'}],
        }]
        report = m.audit_rows(rows, review)
        self.assertEqual(report['review_queue_records'], 1)
        self.assertEqual(report['review_priority_counts'], {'romanized_orthography': 1})
        self.assertEqual(report['review_source_counts'], {'open': 1})


if __name__ == '__main__':
    unittest.main()
