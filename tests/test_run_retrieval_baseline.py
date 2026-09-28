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
        documents, relevant_ids, source_ids = m.build_documents(rows)
        self.assertEqual(len(documents), 2)
        self.assertEqual(relevant_ids[0], relevant_ids[1])
        self.assertEqual(
            source_ids[relevant_ids[0]],
            ['source_row:00000000', 'source_row:00000001'],
        )

    def test_run_defaults_to_dev_only_and_records_reproducible_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'xorqa.jsonl'
            rows = [
                self.row('train', 'train', 'hidden train evidence'),
                self.row('dev', 'mountain', 'mountain evidence'),
                self.row('test', 'river', 'hidden train evidence'),
            ]
            source.write_text(
                ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
                encoding='utf-8',
            )
            report = m.run(source, root / 'out')
            self.assertEqual(report['corpus_documents'], 2)
            self.assertEqual(report['evaluation_queries'], 1)
            self.assertEqual(report['splits'], {'dev': 1})
            self.assertEqual(report['selection_split'], 'dev')
            self.assertEqual(report['evaluation_status'], 'development_selection_only')
            self.assertFalse(report['test_scored'])
            self.assertEqual(report['evaluated_record_ids'], ['dev:mountain'])
            self.assertEqual(len(report['input_manifest_sha256']), 64)
            self.assertEqual(len(report['passage_corpus_sha256']), 64)
            self.assertEqual(
                report['duplicate_passage_groups'][m.context_id('hidden train evidence')],
                ['test:river', 'train:train'],
            )
            self.assertEqual(
                report['baselines']['oracle_english_word_bm25']['overall']['recall_at_1'],
                1.0,
            )
            self.assertEqual(report['test_pilot_records'], 0)
            self.assertIsNone(report['baselines']['garhwali_word_bm25']['test_pilot'])
            manifest = json.loads((root / 'out/run_manifest.json').read_text())
            self.assertEqual(manifest['evaluation_split'], 'dev')
            self.assertEqual(manifest['selected_record_ids'], ['dev:mountain'])
            self.assertEqual(manifest['model']['id'], 'local-bm25-retrieval')
            self.assertIn('report.json', manifest['outputs'])
            predictions = [
                json.loads(line)
                for line in (root / 'out/predictions.jsonl').read_text().splitlines()
            ]
            self.assertEqual({row['split'] for row in predictions}, {'dev'})

    def test_empty_oracle_queries_are_reported_and_not_scored(self):
        documents = [{'document_id': m.context_id('evidence'), 'text': 'evidence'}]
        rows = [
            self.row('dev', 'evidence', 'evidence'),
            self.row('test', '', 'evidence'),
        ]
        _, relevant_ids, _ = m.build_documents(rows)
        metrics, results = m.evaluate(
            rows,
            relevant_ids,
            m.BM25Index(documents, m.word_tokens),
            'oracle_question',
            selection_split='dev',
        )
        self.assertEqual(metrics['query_coverage'], {
            'requested': 1,
            'available': 1,
            'missing': 0,
        })
        self.assertEqual(metrics['overall']['queries'], 1)
        self.assertEqual(len(results), 1)

    def test_duplicate_passages_keep_all_source_record_ids(self):
        rows = [
            {'record_id': 'xorqa:1', 'source_example': {'context': 'same evidence passage'}},
            {'record_id': 'xorqa:2', 'source_example': {'context': 'same evidence passage'}},
        ]
        documents, relevant_ids, source_ids = m.build_documents(rows)
        self.assertEqual(len(documents), 1)
        self.assertEqual(source_ids[relevant_ids[0]], ['xorqa:1', 'xorqa:2'])

    def test_evaluation_rejects_non_development_selection(self):
        rows = [self.row('test', 'river', 'river evidence')]
        _, relevant_ids, _ = m.build_documents(rows)
        index = m.BM25Index(
            [{'document_id': relevant_ids[0], 'text': 'river evidence'}], m.word_tokens
        )
        with self.assertRaisesRegex(ValueError, 'only dev'):
            m.evaluate(rows, relevant_ids, index, 'question', selection_split='test')

    def test_zero_score_positive_is_not_counted_as_retrieved(self):
        rows = [self.row('dev', 'volcano', 'river evidence')]
        _, relevant_ids, _ = m.build_documents(rows)
        index = m.BM25Index(
            [{'document_id': relevant_ids[0], 'text': 'river evidence'}], m.word_tokens
        )
        metrics, results = m.evaluate(rows, relevant_ids, index, 'question')
        self.assertIsNone(results[0]['rank'])
        self.assertEqual(metrics['overall']['recall_at_10'], 0.0)
        self.assertEqual(metrics['overall']['mrr_at_10'], 0.0)
        self.assertEqual(metrics['overall']['not_retrieved_queries'], 1)

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
