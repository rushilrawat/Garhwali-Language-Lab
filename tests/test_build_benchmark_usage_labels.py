import hashlib
import unittest

from audit_benchmark_overlap_candidates import normalize_text
from build_benchmark_usage_labels import build_usage_labels


def family_hash(context: str) -> str:
    digest = hashlib.sha256(normalize_text(context).encode('utf-8')).hexdigest()
    key = f'source_content_sha256:{digest}'
    return hashlib.sha256(key.encode('utf-8')).hexdigest()


class BuildBenchmarkUsageLabelsTests(unittest.TestCase):
    def setUp(self):
        self.context = 'A sufficiently long source passage shared by two questions.'
        self.group_hash = family_hash(self.context)
        self.report = {
            'source_family_groups': [{
                'evidence_type': 'source_content_sha256',
                'family_key_sha256': self.group_hash,
                'split_count': 2,
                'members': [
                    {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train'},
                    {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:test:2', 'split': 'test'},
                ],
            }],
        }
        self.records = [
            {
                'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train',
                'source_example': {'context': self.context},
                'usage': 'evaluation_only', 'training_eligible': False,
            },
            {
                'record_id': 'indicgenbench_xorqa:test:2', 'split': 'test',
                'source_example': {'context': self.context},
                'usage': 'evaluation_only', 'training_eligible': False,
            },
            {
                'record_id': 'indicgenbench_xorqa:dev:3', 'split': 'dev',
                'source_example': {'context': 'Unrelated context with enough characters for checking.'},
                'usage': 'evaluation_only', 'training_eligible': False,
            },
        ]

    def test_labels_only_affected_rows_without_removing_them(self):
        result = build_usage_labels(self.report, self.records)

        self.assertEqual(result['counts']['confirmed_shared_context_groups'], 1)
        self.assertEqual(result['counts']['affected_records'], 2)
        labels = {row['record_id']: row for row in result['labels']}
        self.assertEqual(set(labels), {'indicgenbench_xorqa:train:1', 'indicgenbench_xorqa:test:2'})
        self.assertTrue(all(not row['independent_source_generalization_eligible'] for row in labels.values()))
        self.assertTrue(all(row['open_diagnostic_eligible'] for row in labels.values()))
        self.assertTrue(all(row['record_retained'] for row in labels.values()))
        self.assertEqual(labels['indicgenbench_xorqa:train:1']['original_split'], 'train')
        self.assertEqual(labels['indicgenbench_xorqa:test:2']['original_split'], 'test')

    def test_rejects_group_when_source_contexts_do_not_match(self):
        self.records[1]['source_example']['context'] = 'A different source passage with enough characters.'

        with self.assertRaisesRegex(ValueError, 'context hash does not match'):
            build_usage_labels(self.report, self.records)

    def test_rejects_member_split_mismatch(self):
        self.report['source_family_groups'][0]['members'][1]['split'] = 'dev'

        with self.assertRaisesRegex(ValueError, 'split does not match'):
            build_usage_labels(self.report, self.records)

    def test_ignores_same_split_and_non_xorqa_groups(self):
        self.report['source_family_groups'].extend([
            {
                'evidence_type': 'source_content_sha256',
                'family_key_sha256': self.group_hash,
                'split_count': 1,
                'members': [
                    {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train'},
                ],
            },
            {
                'evidence_type': 'source_content_sha256',
                'family_key_sha256': self.group_hash,
                'split_count': 2,
                'members': [
                    {'view': 'flores', 'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train'},
                    {'view': 'flores', 'record_id': 'indicgenbench_xorqa:test:2', 'split': 'test'},
                ],
            },
        ])

        result = build_usage_labels(self.report, self.records)

        self.assertEqual(result['counts']['confirmed_shared_context_groups'], 1)
        self.assertEqual(result['counts']['affected_records'], 2)

    def test_rejects_duplicate_record_ids(self):
        self.records.append(dict(self.records[0]))

        with self.assertRaisesRegex(ValueError, 'duplicate record_id'):
            build_usage_labels(self.report, self.records)

    def test_adds_exact_question_overlap_and_merges_evidence(self):
        question = 'A repeated Garhwali question for the fixed synthetic fixture?'
        question_hash = hashlib.sha256(normalize_text(question).encode('utf-8')).hexdigest()
        self.records[0]['text_normalized'] = question
        self.records[2]['text_normalized'] = question
        self.report['exact_text_groups'] = [{
            'normalized_text_sha256': question_hash,
            'split_count': 2,
            'members': [
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train'},
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:dev:3', 'split': 'dev'},
            ],
        }]

        result = build_usage_labels(self.report, self.records)

        self.assertEqual(result['counts']['confirmed_cross_split_exact_question_groups'], 1)
        self.assertEqual(result['counts']['affected_records'], 3)
        labels = {row['record_id']: row for row in result['labels']}
        self.assertEqual(
            labels['indicgenbench_xorqa:train:1']['evidence_types'],
            ['exact_normalized_question', 'exact_source_context'],
        )
        self.assertEqual(
            labels['indicgenbench_xorqa:dev:3']['evidence_types'],
            ['exact_normalized_question'],
        )
        self.assertEqual(
            labels['indicgenbench_xorqa:dev:3']['normalized_question_sha256'],
            question_hash,
        )

    def test_rejects_exact_question_hash_mismatch(self):
        self.report['exact_text_groups'] = [{
            'normalized_text_sha256': '0' * 64,
            'split_count': 2,
            'members': [
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train'},
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:dev:3', 'split': 'dev'},
            ],
        }]

        with self.assertRaisesRegex(ValueError, 'normalized question hash does not match'):
            build_usage_labels(self.report, self.records)

    def test_labels_exact_nested_oracle_question_reuse_as_review_only(self):
        oracle_question = 'A repeated English oracle question with enough words to audit?'
        oracle_hash = hashlib.sha256(normalize_text(oracle_question).encode('utf-8')).hexdigest()
        rows = [
            {
                'record_id': 'indicgenbench_xorqa:train:10', 'split': 'train',
                'source_example': {'context': 'A unique training passage with enough characters.',
                                   'oracle_question': oracle_question},
                'usage': 'evaluation_only', 'training_eligible': False,
            },
            {
                'record_id': 'indicgenbench_xorqa:dev:11', 'split': 'dev',
                'source_example': {'context': 'A different development passage with enough characters.',
                                   'oracle_question': oracle_question},
                'usage': 'evaluation_only', 'training_eligible': False,
            },
        ]
        nested_report = {
            'cross_split': {'groups': [{
                'language': 'en',
                'field_path': 'source_example.oracle_question',
                'normalized_text_sha256': oracle_hash,
                'splits': ['dev', 'train'],
                'members': [
                    {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:10',
                     'field_path': 'source_example.oracle_question', 'split': 'train'},
                    {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:dev:11',
                     'field_path': 'source_example.oracle_question', 'split': 'dev'},
                ],
            }]},
        }

        result = build_usage_labels({'source_family_groups': []}, rows, nested_report=nested_report)

        self.assertEqual(result['counts']['confirmed_cross_split_exact_oracle_question_groups'], 1)
        labels = {row['record_id']: row for row in result['labels']}
        self.assertEqual(set(labels), {'indicgenbench_xorqa:train:10', 'indicgenbench_xorqa:dev:11'})
        self.assertTrue(all(row['record_retained'] for row in labels.values()))
        self.assertTrue(all(row['open_diagnostic_eligible'] for row in labels.values()))
        self.assertEqual(
            labels['indicgenbench_xorqa:dev:11']['normalized_oracle_question_sha256'],
            oracle_hash,
        )

    def test_rejects_mismatched_nested_oracle_question_hash(self):
        self.records[0]['source_example']['oracle_question'] = 'Unique oracle question first?'
        self.records[2]['source_example']['oracle_question'] = 'Different oracle question second?'
        nested_report = {'cross_split': {'groups': [{
            'language': 'en',
            'field_path': 'source_example.oracle_question',
            'normalized_text_sha256': '0' * 64,
            'splits': ['dev', 'train'],
            'members': [
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:train:1',
                 'field_path': 'source_example.oracle_question', 'split': 'train'},
                {'view': 'xorqa', 'record_id': 'indicgenbench_xorqa:dev:3',
                 'field_path': 'source_example.oracle_question', 'split': 'dev'},
            ],
        }]}}

        with self.assertRaisesRegex(ValueError, 'oracle question hash does not match'):
            build_usage_labels(self.report, self.records, nested_report=nested_report)

    def test_labels_cross_split_source_page_families_without_removing_rows(self):
        page_title_hash = hashlib.sha256('example article'.encode('utf-8')).hexdigest()
        page_family_hash = hashlib.sha256(
            f'source_page_title_sha256:{page_title_hash}'.encode('utf-8')
        ).hexdigest()
        rows = [
            {
                'record_id': 'indicgenbench_xorqa:train:21', 'split': 'train',
                'source_example': {
                    'title': 'title:Example Article_parentSection:History',
                    'context': 'First distinct article passage with enough characters.',
                },
                'usage': 'evaluation_only', 'training_eligible': False,
            },
            {
                'record_id': 'indicgenbench_xorqa:test:22', 'split': 'test',
                'source_example': {
                    'title': 'title:Example Article_parentSection:Legacy',
                    'context': 'Second distinct article passage with enough characters.',
                },
                'usage': 'evaluation_only', 'training_eligible': False,
            },
        ]
        page_report = {
            'source_page_groups': [{
                'source_page_family_sha256': page_family_hash,
                'normalized_source_page_title_sha256': page_title_hash,
                'split_count': 2,
                'members': [
                    {'record_id': rows[0]['record_id'], 'split': 'train',
                     'source_page_family_sha256': page_family_hash},
                    {'record_id': rows[1]['record_id'], 'split': 'test',
                     'source_page_family_sha256': page_family_hash},
                ],
            }],
        }

        result = build_usage_labels({}, rows, source_page_report=page_report)

        self.assertEqual(result['counts']['confirmed_cross_split_source_page_groups'], 1)
        self.assertEqual(result['counts']['affected_records'], 2)
        labels = {row['record_id']: row for row in result['labels']}
        self.assertEqual(set(labels), {row['record_id'] for row in rows})
        self.assertTrue(all(row['record_retained'] for row in labels.values()))
        self.assertTrue(all(row['open_diagnostic_eligible'] for row in labels.values()))
        self.assertTrue(all(not row['independent_source_generalization_eligible'] for row in labels.values()))
        self.assertTrue(all('exact_source_page_title' in row['evidence_types'] for row in labels.values()))
        self.assertTrue(all(row['source_page_family_sha256'] == page_family_hash for row in labels.values()))

    def test_rejects_source_page_family_hash_mismatch(self):
        rows = [
            {
                'record_id': 'indicgenbench_xorqa:dev:30', 'split': 'dev',
                'source_example': {
                    'title': 'title:Expected Article_parentSection:Intro',
                    'context': 'A source article passage long enough for review.',
                },
            },
            {
                'record_id': 'indicgenbench_xorqa:test:31', 'split': 'test',
                'source_example': {
                    'title': 'title:Expected Article_parentSection:History',
                    'context': 'A second source article passage long enough for review.',
                },
            },
        ]
        report = {'source_page_groups': [{
            'source_page_family_sha256': '0' * 64,
            'normalized_source_page_title_sha256': '1' * 64,
            'split_count': 2,
            'members': [
                {'record_id': rows[0]['record_id'], 'split': 'dev'},
                {'record_id': rows[1]['record_id'], 'split': 'test'},
            ],
        }]}
        with self.assertRaisesRegex(ValueError, 'source-page family hash does not match'):
            build_usage_labels({}, rows, source_page_report=report)


if __name__ == '__main__':
    unittest.main()
