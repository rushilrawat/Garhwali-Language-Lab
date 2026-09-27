import json
import tempfile
import unittest
from pathlib import Path

import run_translation_baseline as m


class TranslationBaselineTests(unittest.TestCase):
    def test_identical_text_scores_perfectly(self):
        references = ['this is a complete test']
        hypotheses = ['this is a complete test']
        self.assertEqual(m.corpus_bleu(references, hypotheses), 1.0)
        self.assertEqual(m.corpus_chrf(references, hypotheses), 1.0)

    def test_metric_summary_rejects_empty_or_unpaired_corpora(self):
        with self.assertRaises(ValueError):
            m.metric_summary([], [])
        with self.assertRaises(ValueError):
            m.metric_summary(['one'], [])

    def test_empty_pair_is_counted_and_not_a_perfect_bleu(self):
        summary = m.metric_summary([''], [''])
        self.assertEqual(summary['corpus_bleu_smoothed'], 0.0)
        self.assertEqual(summary['corpus_chrf2'], 0.0)
        self.assertEqual(summary['exact_match'], 1.0)
        self.assertEqual(summary['empty_reference_records'], 1)
        self.assertEqual(summary['empty_hypothesis_records'], 1)

    def test_unicode_normalization_keeps_identical_garhwali_text_equal(self):
        summary = m.metric_summary(['म्यर घर'], ['म्यर घर'])
        self.assertEqual(summary['exact_match'], 1.0)
        self.assertEqual(summary['corpus_chrf2'], 1.0)

    def test_translation_memory_selects_closest_source(self):
        development = [
            {'source': 'म्यर घर', 'target': 'my house'},
            {'source': 'त्वेर नाम', 'target': 'your name'},
        ]
        predictions = m.translation_memory_predict(development, ['म्यर घर छ'])
        self.assertEqual(predictions[0]['hypothesis'], 'my house')
        self.assertGreater(predictions[0]['similarity'], 0)

    def test_run_defaults_to_dev_and_never_scores_test_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'flores.jsonl'
            rows = [
                {'split': 'dev', 'record_id': 'd', 'source_example': {
                    'source': 'म्यर घर', 'target': 'my house', 'translation_direction': 'xxen'}},
                {'split': 'test', 'record_id': 't'},
            ]
            source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            report = m.run(source, root / 'out')
            predictions = [json.loads(line) for line in (root / 'out/predictions.jsonl').read_text().splitlines()]
            self.assertEqual(report['evaluation_split'], 'dev')
            self.assertEqual(report['evaluation_records'], 1)
            self.assertEqual(report['development_records'], 1)
            self.assertEqual(report['selected_record_ids'], ['d'])
            self.assertEqual([row['record_id'] for row in predictions], ['d'])
            self.assertEqual(report['translation_direction'], 'gbm_to_en')
            self.assertTrue((root / 'out/predictions.jsonl').exists())
            manifest = json.loads((root / 'out/run_manifest.json').read_text())
            self.assertEqual(manifest['selected_record_count'], 1)
            self.assertEqual(manifest['selected_record_ids'], ['d'])
            self.assertIn('predictions.jsonl', manifest['outputs'])
            self.assertIn('report.json', manifest['outputs'])

    def test_historical_test_split_requires_separate_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'flores.jsonl'
            source.write_text(json.dumps({
                'split': 'test',
                'record_id': 'test-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            output = root / 'out'
            with self.assertRaisesRegex(ValueError, 'allow_historical_test'):
                m.run(source, output, split='test')
            self.assertFalse(output.exists())

    def test_dev_translation_memory_excludes_same_source(self):
        development = [
            {'source': 'म्यर घर', 'target': 'my house'},
            {'source': 'म्यर घर', 'target': 'my house duplicate'},
        ]
        predictions = m.translation_memory_predict(
            development, ['म्यर घर'], exclude_exact_source=True
        )
        self.assertEqual(predictions[0]['hypothesis'], '')
        self.assertEqual(predictions[0]['similarity'], 0)

    def test_exact_source_duplicate_counts(self):
        summary = m.exact_source_duplicate_summary([
            {'source': ' म्यर  घर '},
            {'source': 'म्यर घर'},
            {'source': 'अलग'},
        ])
        self.assertEqual(summary, {'duplicate_groups': 1, 'rows_in_duplicate_groups': 2})

    def test_explicit_split_is_sorted_and_limited(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'flores.jsonl'
            rows = [
                {'split': 'dev', 'record_id': 'd2', 'source_example': {
                    'source': 'घ', 'target': 'three', 'translation_direction': 'xxen'}},
                {'split': 'dev', 'record_id': 'd1', 'source_example': {
                    'source': 'क', 'target': 'one', 'translation_direction': 'xxen'}},
                {'split': 'test', 'record_id': 't1', 'source_example': {
                    'source': 'म्यर घर छ', 'target': 'this is my house', 'translation_direction': 'xxen'}},
            ]
            source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            report = m.run(
                source, root / 'out', split='test', max_records=1,
                allow_historical_test=True,
            )
            self.assertEqual(report['evaluation_split'], 'test')
            self.assertEqual(report['selected_record_ids'], ['t1'])
            self.assertEqual(report['evaluation_records'], 1)
            self.assertEqual(report['translation_memory_protocol'], 'dev_memory_to_historical_test')
            self.assertTrue(report['input_sha256'])
            self.assertTrue(report['selected_rows_sha256'])


if __name__ == '__main__':
    unittest.main()
