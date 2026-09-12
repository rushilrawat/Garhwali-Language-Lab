import unittest

import build_instruction_accuracy_split as m


def row(parent, task, index):
    return {
        'parent_text_sha256': parent,
        'task': task,
        'instruction_sha256': f'{parent}-{task}-{index}',
        'active_for_experiment': True,
    }


class InstructionAccuracySplitTests(unittest.TestCase):
    def setUp(self):
        self.rows = []
        for index in range(20):
            self.rows.extend([
                row(f'p-{index}', 'garhwali_to_english', index),
                row(f'p-{index}', 'english_to_garhwali', index),
            ])

    def test_prior_seen_parents_reconstructs_seed_training_prefixes(self):
        parents = m.prior_seen_parent_ids(
            self.rows, seeds=(17, 29), steps=2, batch_size=1,
        )
        expected = {
            item['parent_text_sha256']
            for seed in (17, 29)
            for item in m.tuning.select_rows(self.rows, len(self.rows), seed)[:2]
        }
        self.assertEqual(parents, expected)

    def test_holdout_excludes_seen_parents_and_covers_tasks(self):
        excluded = m.prior_seen_parent_ids(
            self.rows, seeds=(17, 29, 43), steps=2, batch_size=1,
        )
        holdout = m.select_holdout_parent_ids(
            self.rows, excluded, target_records=8, seed=211,
        )
        test_rows = [
            item for item in self.rows
            if item['parent_text_sha256'] in holdout
        ]
        self.assertFalse(holdout & excluded)
        self.assertGreaterEqual(len(test_rows), 8)
        self.assertEqual(
            {item['task'] for item in test_rows},
            {'garhwali_to_english', 'english_to_garhwali'},
        )

    def test_split_has_no_parent_crossing_and_keeps_records_active(self):
        result = m.split_rows(
            self.rows,
            [row('validation-parent', 'garhwali_to_english', 0)],
            target_test_records=8,
            prior_seeds=(17, 29, 43),
            prior_steps=2,
            prior_batch_size=1,
        )
        self.assertEqual(result['integrity']['parent_cross_split'], 0)
        self.assertEqual(result['integrity']['prior_seen_parent_test_overlap'], 0)
        self.assertTrue(result['integrity']['all_records_active_for_experiment'])


if __name__ == '__main__':
    unittest.main()
