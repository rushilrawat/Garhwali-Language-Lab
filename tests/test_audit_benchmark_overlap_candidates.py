import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import audit_benchmark_overlap_candidates as audit_module
except ModuleNotFoundError as error:
    if error.name != 'audit_benchmark_overlap_candidates':
        raise
    audit_module = None


class BenchmarkOverlapCandidateTests(unittest.TestCase):
    def audit(self, records):
        audit_records = getattr(audit_module, 'audit_records', None)
        self.assertTrue(callable(audit_records), 'audit_records() is not implemented yet')
        return audit_records(records)

    def collect(self, project_root):
        collect_project_records = getattr(audit_module, 'collect_project_records', None)
        self.assertTrue(
            callable(collect_project_records),
            'collect_project_records() is not implemented yet',
        )
        return collect_project_records(project_root)

    def build_report(self, project_root):
        build_project_report = getattr(audit_module, 'build_project_report', None)
        self.assertTrue(
            callable(build_project_report),
            'build_project_report() is not implemented yet',
        )
        return build_project_report(project_root)

    def source_family_keys(self, row, *, internal):
        source_family_keys = getattr(audit_module, '_source_family_keys', None)
        self.assertTrue(callable(source_family_keys), '_source_family_keys() is not implemented yet')
        return source_family_keys(row, internal=internal)

    def test_exact_normalized_groups_are_reported_without_mutating_rows(self):
        records = [
            {
                'view': 'text_train', 'record_id': 'train-1', 'split': 'train',
                'language': 'gbm', 'script': 'Deva', 'text': 'गढ़वाली—भाषा!',
            },
            {
                'view': 'flores', 'record_id': 'dev-1', 'split': 'dev',
                'language': 'gbm', 'script': 'Deva', 'text': 'गढ़वाली भाषा',
            },
            {
                'view': 'internal_text', 'record_id': 'train-mirror', 'split': 'train',
                'language': 'gbm', 'script': 'Deva', 'text': 'गढ़वाली भाषा',
            },
        ]
        original = copy.deepcopy(records)

        report = self.audit(records)

        self.assertEqual(records, original)
        self.assertEqual(report['counts']['exact_text_groups'], 1)
        group = report['exact_text_groups'][0]
        self.assertEqual(
            [(item['view'], item['record_id']) for item in group['members']],
            [('flores', 'dev-1'), ('internal_text', 'train-mirror'), ('text_train', 'train-1')],
        )
        self.assertEqual(group['split_count'], 2)
        self.assertEqual(group['view_count'], 3)
        self.assertEqual(group.get('review_state'), 'unreviewed_candidate')
        self.assertEqual(report['counts']['exact_cross_split_groups'], 1)
        self.assertIn('not_proof_of_no_leakage', report['interpretation'])

    def test_same_split_cross_view_match_is_not_counted_as_cross_split(self):
        records = [
            {
                'view': 'text_recommended/test', 'record_id': 'a', 'split': 'test',
                'language': 'gbm', 'script': 'Deva', 'text': 'समान गढ़वाली पाठ',
            },
            {
                'view': 'internal_text', 'record_id': 'b', 'split': 'test',
                'language': 'gbm', 'script': 'Deva', 'text': 'समान गढ़वाली पाठ',
            },
        ]

        report = self.audit(records)

        self.assertEqual(report['counts'].get('exact_cross_split_groups'), 0)
        self.assertEqual(report['counts'].get('exact_cross_view_groups'), 1)

    def test_near_duplicate_candidates_require_matching_language_and_script(self):
        original = (
            'गढ़वाली भाषा के बोलने वाले लोग अपने गाँव की कहानियाँ पीढ़ी दर पीढ़ी '
            'सुनाते हैं और भाषा को जीवित रखते हैं।'
        )
        near = original.replace('सुनाते हैं', 'बताते हैं')
        records = [
            {
                'view': 'text_train', 'record_id': 'train-1', 'split': 'train',
                'language': 'gbm', 'script': 'Deva', 'text': original,
            },
            {
                'view': 'benchmark', 'record_id': 'dev-1', 'split': 'dev',
                'language': 'gbm', 'script': 'Deva', 'text': near,
            },
            {
                'view': 'other-language', 'record_id': 'dev-2', 'split': 'dev',
                'language': 'hin', 'script': 'Deva', 'text': near,
            },
        ]

        report = self.audit(records)

        pairs = report['near_duplicate_pairs']
        self.assertEqual(len(pairs), 1)
        self.assertEqual(
            {(pairs[0]['left']['record_id'], pairs[0]['right']['record_id'])},
            {('dev-1', 'train-1')},
        )
        self.assertGreaterEqual(pairs[0]['similarity'], report['parameters']['min_jaccard'])
        self.assertEqual(pairs[0].get('review_state'), 'unreviewed_candidate')

    def test_source_family_keys_link_different_languages_without_comparing_text(self):
        records = [
            {
                'view': 'garhwali', 'record_id': 'gbm-1', 'split': 'train',
                'language': 'gbm', 'script': 'Deva', 'text': 'गढ़वाली वाक्य',
                'source_family_keys': ['url:https://example.org/story/1'],
            },
            {
                'view': 'english', 'record_id': 'en-1', 'split': 'dev',
                'language': 'eng', 'script': 'Latn', 'text': 'An English translation',
                'source_family_keys': ['url:https://example.org/story/1'],
            },
        ]

        report = self.audit(records)

        self.assertEqual(report['counts']['source_family_groups'], 1)
        family = report['source_family_groups'][0]
        self.assertEqual(family.get('record_language_label_count'), 2)
        self.assertEqual(family['split_count'], 2)
        self.assertEqual(family.get('view_count'), 2)
        self.assertEqual(family.get('review_state'), 'unreviewed_candidate')
        self.assertEqual(len(family['members']), 2)

    def test_dataset_repository_url_is_not_mistaken_for_record_source_family(self):
        keys = self.source_family_keys({
            'provenance': [{
                'source_id': 'record-17',
                'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
            }],
        }, internal=True)

        self.assertNotIn('source_id:record-17', keys)
        self.assertFalse(any(key.startswith('url:') for key in keys))

    def test_report_is_deterministic_under_input_reordering(self):
        records = [
            {
                'view': 'b', 'record_id': '2', 'split': 'train',
                'language': 'gbm', 'script': 'Deva', 'text': 'यह वाक्य दोहराया गया है।',
                'source_family_keys': ['id:shared'],
            },
            {
                'view': 'a', 'record_id': '1', 'split': 'dev',
                'language': 'gbm', 'script': 'Deva', 'text': 'यह वाक्य दोहराया गया है।',
                'source_family_keys': ['id:shared'],
            },
        ]

        self.assertEqual(self.audit(records), self.audit(list(reversed(records))))

    def test_project_collector_joins_text_views_and_source_links(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            train_path = root / 'data/processed/model_ready/splits/text_recommended/train.jsonl'
            train_path.parent.mkdir(parents=True)
            training_text = (
                'गढ़वाली भाषा के बोलने वाले लोग अपने गाँव की कहानियाँ पीढ़ी दर पीढ़ी '
                'सुनाते हैं और भाषा को जीवित रखते हैं।'
            )
            train_path.write_text(json.dumps({
                'id': 'train-1', 'language': 'gbm', 'script': 'Deva',
                'split': 'train', 'text': training_text,
                'provenance': [{'source_url': 'https://example.org/story/1'}],
            }, ensure_ascii=False) + '\n', encoding='utf-8')
            for split in ('validation', 'test'):
                (train_path.parent / f'{split}.jsonl').write_text('', encoding='utf-8')

            internal_path = root / 'data/processed/evaluation/garhwali_bench/internal_text.jsonl'
            internal_path.parent.mkdir(parents=True)
            internal_path.write_text(json.dumps({
                'segment_sha256': 'internal-1', 'split': 'test',
                'text': 'यह गढ़वाली पाठ है।',
                'parents': [{'provenance': [{'source_url': 'https://example.org/story/1'}]}],
            }, ensure_ascii=False) + '\n', encoding='utf-8')

            benchmark_directory = root / 'benchmarks'
            benchmark_directory.mkdir()
            similar_text = training_text.replace('सुनाते हैं', 'बताते हैं')
            flores = {
                'record_id': 'flores:dev:1', 'split': 'dev', 'iso_639_3': 'gbm',
                'script': 'Deva', 'text_normalized': similar_text,
                'source_example': {
                    'source': 'A source sentence', 'target': similar_text,
                    'source_url': 'https://example.org/story/1',
                },
            }
            (benchmark_directory / 'indicgenbench_flores.jsonl').write_text(
                json.dumps(flores, ensure_ascii=False) + '\n', encoding='utf-8'
            )
            for task in ('crosssum', 'xorqa'):
                (benchmark_directory / f'indicgenbench_{task}.jsonl').write_text(
                    '', encoding='utf-8'
                )

            records = self.collect(root)
            project_report = self.build_report(root)
            output_directory = root / 'audit-output'
            command = subprocess.run(
                [
                    sys.executable,
                    str(Path(audit_module.__file__).resolve()),
                    '--project-root', str(root),
                    '--output-dir', str(output_directory),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(command.returncode, 0, command.stderr)
            self.assertTrue((output_directory / 'overlap_candidates.json').is_file())
            self.assertTrue((output_directory / 'overlap_candidates.md').is_file())

        self.assertEqual(len(records), 3)
        self.assertEqual(
            {record['view'] for record in records},
            {'text_recommended/train', 'internal_text', 'flores'},
        )
        internal_record = next(record for record in records if record['view'] == 'internal_text')
        self.assertEqual(internal_record['script'], 'Deva')
        self.assertEqual(
            len({tuple(record['source_family_keys']) for record in records}),
            1,
        )
        report = self.audit(records)
        self.assertEqual(report['counts']['source_family_groups'], 1)
        self.assertEqual(report['counts']['near_duplicate_pairs'], 1)
        self.assertEqual(project_report['counts']['input_records'], 3)
        self.assertEqual(len(project_report['input_manifests']), 7)
        self.assertTrue(all(item['sha256'] for item in project_report['input_manifests']))


if __name__ == '__main__':
    unittest.main()
