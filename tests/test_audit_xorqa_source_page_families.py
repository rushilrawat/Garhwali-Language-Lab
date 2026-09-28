import importlib
import json
import tempfile
import unittest
from pathlib import Path


try:
    audit = importlib.import_module('audit_xorqa_source_page_families')
except ModuleNotFoundError as error:
    if error.name != 'audit_xorqa_source_page_families':
        raise
    audit = None


class XorqaSourcePageFamilyTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(audit, 'audit_xorqa_source_page_families module is missing')
        return audit

    def test_groups_different_sections_of_same_page_across_splits(self):
        rows = [
            {
                'record_id': 'indicgenbench_xorqa:train:1', 'split': 'train',
                'source_example': {
                    'title': 'title:Example Article_parentSection:History_sectionName:Early period',
                    'context': 'A first passage from the same source article.',
                },
            },
            {
                'record_id': 'indicgenbench_xorqa:test:2', 'split': 'test',
                'source_example': {
                    'title': 'title:Example Article_parentSection:Legacy_sectionName:Later period',
                    'context': 'A second, different passage from the same source article.',
                },
            },
            {
                'record_id': 'indicgenbench_xorqa:dev:3', 'split': 'dev',
                'source_example': {
                    'title': 'title:Another Article_parentSection:Intro_sectionName:Intro',
                    'context': 'A passage from an unrelated source article.',
                },
            },
        ]

        report = self.module().audit_rows(rows)

        self.assertEqual(report['summary']['source_page_families'], 2)
        self.assertEqual(report['summary']['cross_split_page_groups'], 1)
        self.assertEqual(report['summary']['cross_split_records'], 2)
        self.assertEqual(report['summary']['cross_split_groups_with_multiple_contexts'], 1)
        group = report['source_page_groups'][0]
        self.assertEqual(group['splits'], ['test', 'train'])
        self.assertEqual(group['distinct_contexts'], 2)
        self.assertNotIn('title', group)
        self.assertTrue(all('source_page_family_sha256' in row for row in group['members']))

    def test_rejects_duplicate_record_ids(self):
        row = {
            'record_id': 'duplicate', 'split': 'dev',
            'source_example': {'title': 'title:Example_parentSection:Intro', 'context': 'context'},
        }
        with self.assertRaisesRegex(ValueError, 'duplicate record_id'):
            self.module().audit_rows([row, dict(row)])

    def test_run_writes_hash_linked_report_without_source_titles(self):
        row = {
            'record_id': 'indicgenbench_xorqa:dev:3', 'split': 'dev',
            'source_example': {
                'title': 'title:Private Fixture Article_parentSection:Intro',
                'context': 'A source passage used only in the test fixture.',
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'xorqa.jsonl'
            source.write_text(json.dumps(row) + '\n', encoding='utf-8')
            output_json = root / 'report.json'
            output_markdown = root / 'report.md'

            report = self.module().run(source, output_json, output_markdown)
            saved = json.loads(output_json.read_text(encoding='utf-8'))

            self.assertEqual(saved['input']['sha256'], report['input']['sha256'])
            self.assertEqual(saved['outputs']['json'], str(output_json))
            self.assertNotIn('Private Fixture Article', output_json.read_text(encoding='utf-8'))
            self.assertNotIn('Private Fixture Article', output_markdown.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
