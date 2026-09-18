import json
import tempfile
import unittest
from pathlib import Path

import run_retrieval_baseline as m


class RetrievalBaselineTests(unittest.TestCase):
    def test_bm25_ranks_the_matching_document_first(self):
        documents = [
            {'document_id': 'a', 'text': 'apple banana orchard'},
            {'document_id': 'b', 'text': 'river mountain valley'},
        ]
        index = m.BM25Index(documents, m.word_tokens)
        result = index.rank('mountain river', top_k=2)
        self.assertEqual(result[0]['document_id'], 'b')
        self.assertGreater(result[0]['score'], result[1]['score'])

    def test_duplicate_contexts_share_one_relevant_document(self):
        rows = [
            {'source_example': {'context': 'same evidence passage'}},
            {'source_example': {'context': 'same evidence passage'}},
            {'source_example': {'context': 'different evidence passage'}},
        ]
        documents, relevant_ids = m.build_documents(rows)
        self.assertEqual(len(documents), 2)
        self.assertEqual(relevant_ids[0], relevant_ids[1])

    def test_run_evaluates_dev_and_test_but_not_train_queries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'xorqa.jsonl'
            rows = [
                self.row('train', 'train', 'hidden train evidence'),
                self.row('dev', 'mountain', 'mountain evidence'),
                self.row('test', 'river', 'river evidence'),
            ]
            source.write_text(
                ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
                encoding='utf-8',
            )
            report = m.run(source, root / 'out')
            self.assertEqual(report['corpus_documents'], 3)
            self.assertEqual(report['evaluation_queries'], 2)
            self.assertEqual(report['splits'], {'dev': 1, 'test': 1})
            self.assertEqual(
                report['baselines']['oracle_english_word_bm25']['overall']['recall_at_1'],
                1.0,
            )
            self.assertEqual(report['test_pilot_records'], 1)
            self.assertEqual(
                report['baselines']['garhwali_word_bm25']['test_pilot']['queries'],
                1,
            )
            predictions = [
                json.loads(line)
                for line in (root / 'out/predictions.jsonl').read_text().splitlines()
            ]
            self.assertEqual({row['split'] for row in predictions}, {'dev', 'test'})

    def test_empty_oracle_queries_are_reported_and_not_scored(self):
        documents = [{'document_id': m.context_id('evidence'), 'text': 'evidence'}]
        rows = [
            self.row('dev', 'evidence', 'evidence'),
            self.row('test', '', 'evidence'),
        ]
        _, relevant_ids = m.build_documents(rows)
        metrics, results = m.evaluate(
            rows,
            relevant_ids,
            m.BM25Index(documents, m.word_tokens),
            'oracle_question',
        )
        self.assertEqual(metrics['query_coverage'], {
            'requested': 2,
            'available': 1,
            'missing': 1,
        })
        self.assertEqual(metrics['overall']['queries'], 1)
        self.assertEqual(len(results), 1)

    @staticmethod
    def row(split, keyword, context):
        return {
            'record_id': f'{split}:{keyword}',
            'split': split,
            'source_example': {
                'context': context,
                'question': keyword,
                'oracle_question': keyword,
                'answers': [{'text': keyword, 'answer_start': 0}],
            },
        }


if __name__ == '__main__':
    unittest.main()
