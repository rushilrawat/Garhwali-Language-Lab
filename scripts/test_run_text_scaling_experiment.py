import json
import math
import tempfile
import unittest
from pathlib import Path

import run_text_scaling_experiment as m


class TextScalingExperimentTests(unittest.TestCase):
    def test_hash_sample_is_deterministic_and_nested(self):
        rows = [{'segment_sha256': str(index), 'text': f'पाठ {index}'} for index in range(20)]
        small = m.hash_sample(rows, 0.25, 17)
        large = m.hash_sample(rows, 0.50, 17)
        self.assertEqual(small, m.hash_sample(rows, 0.25, 17))
        self.assertTrue({row['segment_sha256'] for row in small} <= {
            row['segment_sha256'] for row in large
        })

    def test_character_ngram_score_is_finite(self):
        score = m.character_ngram_score(['अब अब अब'], ['अब अब'], order=2)
        self.assertTrue(math.isfinite(score['cross_entropy']))
        self.assertGreaterEqual(score['perplexity'], 1.0)
        self.assertEqual(score['order'], 2)

    def test_selection_uses_validation_and_test_only_scores_selected_configuration(self):
        train = [
            {'segment_sha256': f'train-{index}', 'text': 'गढ़वाली भाषा पाठ'}
            for index in range(20)
        ]
        validation = [
            {'segment_sha256': f'validation-{index}', 'text': 'गढ़वाली भाषा'}
            for index in range(4)
        ]
        test = [
            {'segment_sha256': f'test-{index}', 'text': 'गढ़वाली पाठ'}
            for index in range(3)
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {}
            for name, rows in [('train', train), ('validation', validation), ('test', test)]:
                path = root / f'{name}.jsonl'
                path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
                paths[name] = path
            report = m.run(
                paths['train'], paths['validation'], paths['test'], root / 'report.json',
                fractions=(0.5, 1.0), seeds=(17, 29), orders=(2, 3),
            )
            self.assertEqual(report['selection']['metric'], 'mean_validation_cross_entropy')
            self.assertEqual(len(report['validation_runs']), 8)
            self.assertEqual(len(report['frozen_test_runs']), 2)
            selected = report['selection']['configuration']
            self.assertEqual(selected['fraction'], 1.0)
            self.assertIn(selected['order'], (2, 3))
            self.assertEqual(report['integrity']['test_records_used_during_selection'], 0)


if __name__ == '__main__':
    unittest.main()
