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


if __name__ == '__main__':
    unittest.main()
