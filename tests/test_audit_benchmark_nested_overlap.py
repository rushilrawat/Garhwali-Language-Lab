import importlib
import json
import unittest


try:
    audit = importlib.import_module('audit_benchmark_nested_overlap')
except ModuleNotFoundError as error:
    if error.name != 'audit_benchmark_nested_overlap':
        raise
    audit = None


class NestedBenchmarkOverlapTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(audit, 'audit_benchmark_nested_overlap module is missing')
        return audit

    def test_finds_nested_garhwali_reference_overlap_and_emits_hashes_only(self):
        train = [{
            'record_id': 'train:1',
            'text': 'गढ़वाली भाषा मा हिमालयी लोककथा लिखी गेछी।',
        }]
        datasets = {
            'crosssum': [{
                'record_id': 'crosssum:dev:1',
                'split': 'dev',
                'source_example': {
                    'text': 'An English source article that is long enough to count.',
                    'summary': 'गढ़वाली भाषा मा हिमालयी लोककथा लिखी गेछी।',
                },
            }],
        }

        report = self.module().audit_rows(train, datasets, min_chars=20)

        self.assertEqual(report['training_overlap']['long_match_group_count'], 1)
        match = report['training_overlap']['long_match_groups'][0]
        self.assertEqual(match['field_path'], 'source_example.summary')
        self.assertEqual(match['nested_members'][0]['record_id'], 'crosssum:dev:1')
        self.assertEqual(match['matched_training_record_ids'], ['train:1'])
        self.assertIn('normalized_text_sha256', match)
        self.assertNotIn('गढ़वाली भाषा', json.dumps(report, ensure_ascii=False))

    def test_exact_nested_content_across_splits_is_grouped_without_deleting_rows(self):
        datasets = {
            'xorqa': [
                {
                    'record_id': 'xorqa:train:1', 'split': 'train',
                    'source_example': {'translated_answers': [{'text': 'दीर्घ उत्तर हिमालयी परंपरा'}]},
                },
                {
                    'record_id': 'xorqa:test:2', 'split': 'test',
                    'source_example': {'translated_answers': [{'text': 'दीर्घ उत्तर हिमालयी परंपरा'}]},
                },
            ],
        }

        report = self.module().audit_rows([], datasets, min_chars=20)

        self.assertEqual(report['cross_split']['group_count'], 1)
        group = report['cross_split']['groups'][0]
        self.assertEqual(group['language'], 'gbm')
        self.assertEqual({member['split'] for member in group['members']}, {'train', 'test'})
        self.assertEqual(len(group['members']), 2)
        self.assertEqual(report['source_rows_removed'], 0)

    def test_cross_field_copy_is_separated_from_same_field_split_repeats(self):
        phrase = 'A sufficiently long exact English source phrase.'
        datasets = {
            'xorqa': [
                {
                    'record_id': 'xorqa:dev:1', 'split': 'dev',
                    'source_example': {'context': phrase},
                },
                {
                    'record_id': 'xorqa:test:2', 'split': 'test',
                    'source_example': {'answers': [{'text': phrase}]},
                },
            ],
        }

        report = self.module().audit_rows([], datasets, min_chars=20)

        self.assertEqual(report['cross_split']['group_count'], 0)
        self.assertEqual(report['cross_field']['group_count'], 1)

    def test_exact_text_across_language_labels_is_reported_separately(self):
        phrase = 'A sufficiently long answer shared across labels.'
        datasets = {
            'xorqa': [
                {
                    'record_id': 'xorqa:train:1', 'split': 'train',
                    'source_example': {'answers': [{'text': phrase}, {'text': 'राम'}]},
                },
                {
                    'record_id': 'xorqa:test:2', 'split': 'test',
                    'source_example': {'translated_answers': [{'text': phrase}, {'text': 'राम'}]},
                },
            ],
        }

        report = self.module().audit_rows([], datasets, min_chars=20)

        self.assertEqual(report['cross_split']['group_count'], 0)
        self.assertEqual(report['cross_field']['group_count'], 0)
        candidates = report['cross_language_label_exact']
        self.assertEqual(candidates['group_count'], 2)
        self.assertEqual(candidates['short_group_count'], 1)
        self.assertEqual(candidates['long_group_count'], 1)
        self.assertEqual(candidates['cross_split_group_count'], 2)
        group = next(group for group in candidates['groups'] if group['normalized_characters'] > 20)
        self.assertEqual(group['languages'], ['en', 'gbm'])
        self.assertEqual(group['field_paths'], [
            'source_example.answers[*].text',
            'source_example.translated_answers[*].text',
        ])
        self.assertNotIn(phrase, json.dumps(report, ensure_ascii=False))

    def test_short_training_matches_are_counted_but_not_treated_as_long_candidates(self):
        train = [{'record_id': 'train:short', 'text': 'गढ़वाली शब्द'}]
        datasets = {
            'flores': [{
                'record_id': 'flores:dev:1', 'split': 'dev',
                'source_example': {'source': 'गढ़वाली शब्द', 'target': 'English target sentence.'},
            }],
        }

        report = self.module().audit_rows(train, datasets, min_chars=20)

        self.assertEqual(report['training_overlap']['long_match_group_count'], 0)
        self.assertEqual(report['training_overlap']['short_exact_match_count'], 1)
        short_match = report['training_overlap']['short_match_groups'][0]
        self.assertEqual(short_match['matched_training_record_ids'], ['train:short'])


if __name__ == '__main__':
    unittest.main()
