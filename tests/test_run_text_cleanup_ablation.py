import json
import tempfile
import unittest
from pathlib import Path

import run_text_cleanup_ablation as m


class TextCleanupAblationTests(unittest.TestCase):
    def test_spelling_application_replaces_only_complete_devanagari_tokens(self):
        candidates = [{'observed': 'गढ़वालि', 'candidate': 'गढ़वाली'}]
        self.assertEqual(
            m.apply_spelling_candidates('गढ़वालि, अगढ़वालि।', candidates),
            'गढ़वाली, अगढ़वालि।',
        )

    def test_variant_text_does_not_mutate_source_proposal(self):
        row = {
            'text_current': 'गढ़वालि', 'proposed_text': 'गढ़वालि',
            'spelling_candidates': [{'observed': 'गढ़वालि', 'candidate': 'गढ़वाली'}],
        }
        self.assertEqual(m.variant_text(row, 'spelling'), 'गढ़वाली')
        self.assertEqual(row['text_current'], 'गढ़वालि')

    def test_ablation_compares_fixed_train_and_test_partitions(self):
        proposals = [
            {
                'text_sha256': 'a', 'split': 'train', 'text_current': 'गढ़वाली भाषा',
                'proposed_text': 'गढ़वाली भाषा', 'mechanical_changes': [],
                'spelling_candidates': [], 'active_for_experiment': True,
            },
            {
                'text_sha256': 'b', 'split': 'test', 'text_current': 'गढ़वालि  भाषा',
                'proposed_text': 'गढ़वालि भाषा', 'mechanical_changes': ['collapsed_whitespace'],
                'spelling_candidates': [{'observed': 'गढ़वालि', 'candidate': 'गढ़वाली'}],
                'active_for_experiment': True,
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'proposals.jsonl'
            source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in proposals))
            report = m.run(source, root / 'report.json')
            self.assertEqual(report['records']['total'], 2)
            self.assertEqual(report['records']['excluded'], 0)
            self.assertEqual(report['partitions'], {'train': 1, 'validation': 0, 'test': 1})
            self.assertEqual(report['variants']['baseline']['test_records'], 1)
            self.assertEqual(report['promotion']['spelling']['status'], 'not_promoted')


if __name__ == '__main__':
    unittest.main()
