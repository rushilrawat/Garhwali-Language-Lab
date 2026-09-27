import unittest

import run_indicbert_retrieval_baseline as m


class IndicBertRetrievalBaselineTests(unittest.TestCase):
    def test_selects_sorted_development_rows_only_by_default(self):
        rows = [
            {'split': 'dev', 'record_id': 'b'},
            {'split': 'test', 'record_id': 'b'},
            {'split': 'test', 'record_id': 'a'},
            {'split': 'dev', 'record_id': 'a'},
        ]
        selected = m.select_evaluation_rows(rows, 1)
        self.assertEqual([row['record_id'] for row in selected], ['a'])

    def test_rejects_non_development_selection(self):
        with self.assertRaisesRegex(ValueError, 'only dev'):
            m.select_evaluation_rows([{'split': 'test', 'record_id': 'x'}], 1, 'test')

    def test_rank_scores_uses_document_id_to_break_ties(self):
        result = m.rank_scores(['b', 'a', 'c'], [0.5, 0.5, 0.1], 'b', top_k=2)
        self.assertEqual(result['rank'], 2)
        self.assertEqual([row['document_id'] for row in result['top']], ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
