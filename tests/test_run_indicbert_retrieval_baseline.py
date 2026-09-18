import unittest

import run_indicbert_retrieval_baseline as m


class IndicBertRetrievalBaselineTests(unittest.TestCase):
    def test_selects_sorted_test_rows_only(self):
        rows = [
            {'split': 'dev', 'record_id': '0'},
            {'split': 'test', 'record_id': 'b'},
            {'split': 'test', 'record_id': 'a'},
        ]
        selected = m.select_evaluation_rows(rows, 1)
        self.assertEqual([row['record_id'] for row in selected], ['a'])

    def test_rank_scores_uses_document_id_to_break_ties(self):
        result = m.rank_scores(['b', 'a', 'c'], [0.5, 0.5, 0.1], 'b', top_k=2)
        self.assertEqual(result['rank'], 2)
        self.assertEqual([row['document_id'] for row in result['top']], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
