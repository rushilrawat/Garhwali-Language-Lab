import json
import tempfile
import unittest
from pathlib import Path

import build_recommended_text_view as m


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )


class RecommendedTextViewTests(unittest.TestCase):
    def test_builds_separate_quality_and_rights_filtered_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quality_path = root / 'quality.jsonl'
            write_jsonl(quality_path, [
                {
                    'text_sha256': 'parent-open',
                    'language_bucket': 'garhwali_candidate',
                    'quality_v2': {'tier': 'strict_gold_candidate'},
                },
                {
                    'text_sha256': 'parent-mixed',
                    'language_bucket': 'mixed_language',
                    'quality_v2': {'tier': 'experimental_review'},
                },
            ])
            open_source = {
                'source_id': 'open-source',
                'iso_639_3': 'gbm',
                'license_id': 'CC-BY-4.0',
                'attribution': 'Test source',
            }
            split_paths = {}
            for split in m.SPLITS:
                split_paths[split] = root / f'{split}.jsonl'
            write_jsonl(split_paths['train'], [
                {
                    'segment_sha256': 'segment-open', 'text': 'गढ़वाली पाठ',
                    'split': 'train', 'quality_flags': [],
                    'parents': [{
                        'text_sha256': 'parent-open',
                        'provenance': [open_source],
                    }],
                },
                {
                    'segment_sha256': 'segment-mixed', 'text': 'मिश्रित पाठ',
                    'split': 'train', 'quality_flags': [],
                    'parents': [{
                        'text_sha256': 'parent-mixed',
                        'provenance': [open_source],
                    }],
                },
            ])
            write_jsonl(split_paths['validation'], [])
            write_jsonl(split_paths['test'], [])

            report = m.build_view(split_paths, quality_path, root / 'output')

            self.assertEqual(report['counts']['train']['source_records'], 2)
            self.assertEqual(report['counts']['train']['recommended_records'], 1)
            self.assertEqual(report['records_removed_from_full_corpus'], 0)
            selected = [json.loads(line) for line in (
                root / 'output/train.jsonl'
            ).read_text().splitlines()]
            self.assertEqual([row['id'] for row in selected], ['segment-open'])

    def test_rejects_duplicate_quality_parent_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            quality_path = root / 'quality.jsonl'
            write_jsonl(quality_path, [
                {'text_sha256': 'same'}, {'text_sha256': 'same'},
            ])
            split_paths = {split: root / f'{split}.jsonl' for split in m.SPLITS}
            for path in split_paths.values():
                write_jsonl(path, [])
            with self.assertRaisesRegex(ValueError, 'duplicate parent text hashes'):
                m.build_view(split_paths, quality_path, root / 'output')


if __name__ == '__main__':
    unittest.main()
