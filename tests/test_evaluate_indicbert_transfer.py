import unittest

import evaluate_indicbert_transfer as m


class IndicBertTransferEvaluationTests(unittest.TestCase):
    def test_family_summary_and_selection_use_cross_entropy(self):
        base = m.summarize_family([
            {'cross_entropy': 6.0, 'accuracy': 0.2},
        ])
        adapted = m.summarize_family([
            {'cross_entropy': 5.5, 'accuracy': 0.21},
            {'cross_entropy': 5.7, 'accuracy': 0.22},
        ])
        self.assertEqual(adapted['mean_cross_entropy'], 5.6)
        self.assertEqual(adapted['std_cross_entropy'], 0.1)
        self.assertEqual(m.select_family({'base': base, 'adapted': adapted}), 'adapted')

    def test_subset_hash_depends_on_ordered_record_ids(self):
        rows = [{'segment_sha256': 'a'}, {'segment_sha256': 'b'}]
        self.assertEqual(m.subset_sha256(rows), m.subset_sha256(list(rows)))
        self.assertNotEqual(m.subset_sha256(rows), m.subset_sha256(list(reversed(rows))))


if __name__ == '__main__':
    unittest.main()
