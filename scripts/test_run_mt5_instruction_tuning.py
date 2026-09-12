import unittest

import run_mt5_instruction_tuning as m


class InstructionTuningTests(unittest.TestCase):
    def test_select_rows_is_deterministic_and_task_balanced(self):
        rows = [
            {'instruction_sha256': f'a-{index}', 'task': 'a'}
            for index in range(8)
        ] + [
            {'instruction_sha256': f'b-{index}', 'task': 'b'}
            for index in range(2)
        ]
        first = m.select_rows(rows, 4, 17)
        second = m.select_rows(rows, 4, 17)
        self.assertEqual(first, second)
        self.assertEqual({row['task'] for row in first}, {'a', 'b'})

    def test_mask_padding_labels_hides_only_padding(self):
        labels = [[8, 9, 0], [7, 0, 0]]
        self.assertEqual(
            m.mask_padding_labels(labels, 0),
            [[8, 9, -100], [7, -100, -100]],
        )

    def test_metric_summary_normalizes_exact_match_and_scores_chrf(self):
        summary = m.metric_summary(
            ['  Hand ', 'हत्थ'],
            ['hand', 'हत्थ'],
        )
        self.assertEqual(summary['exact_match'], 1.0)
        self.assertEqual(summary['corpus_chrf2'], 1.0)

    def test_clean_generated_text_removes_mt5_sentinels(self):
        self.assertEqual(m.clean_generated_text('<extra_id_0>'), '')
        self.assertEqual(m.clean_generated_text('उत्तर <extra_id_1>'), 'उत्तर')

    def test_summarize_runs_selects_validation_winner(self):
        runs = [
            {'seed': 17, 'validation': {'cross_entropy': 4.0}},
            {'seed': 29, 'validation': {'cross_entropy': 3.5}},
            {'seed': 43, 'validation': {'cross_entropy': 3.8}},
        ]
        summary = m.summarize_runs({'cross_entropy': 5.0}, runs)
        self.assertEqual(summary['best_seed'], 29)
        self.assertEqual(summary['improved_seed_count'], 3)
        self.assertLess(summary['mean_cross_entropy_delta'], 0)


if __name__ == '__main__':
    unittest.main()
