import json
import tempfile
import unittest
from pathlib import Path

import freeze_benchmark
import score_benchmark_predictions as scorer


def asr_rows():
    # Four records; two share a source page, so they form one cluster.
    rows = [
        {'record_id': 'a', 'split': 'dev', 'text': {'text_scoring': 'अ ब स'},
         'lineage': {'source_page_family_sha256': 'page-1'}},
        {'record_id': 'b', 'split': 'dev', 'text': {'text_scoring': 'द ए'},
         'lineage': {'source_page_family_sha256': 'page-1'}},
        {'record_id': 'c', 'split': 'dev', 'text': {'text_scoring': 'फ ग ह'},
         'lineage': {'speaker_id': 'spk-9'}},
        {'record_id': 'd', 'split': 'dev', 'text': {'text_scoring': 'ज क'}},
    ]
    predictions = [
        {'record_id': 'a', 'hypothesis': 'अ ब स'},
        {'record_id': 'b', 'hypothesis': 'द'},
        {'record_id': 'c', 'hypothesis': 'फ x ह'},
        {'record_id': 'd', 'hypothesis': ''},
    ]
    return rows, predictions


class UncertaintyTests(unittest.TestCase):
    def test_cluster_keys_prefer_the_most_specific_shared_source(self):
        rows, _ = asr_rows()
        keys, used = scorer.cluster_keys(rows, [row['record_id'] for row in rows])
        self.assertEqual(keys[0], keys[1])
        self.assertEqual(keys[2], 'speaker_id:spk-9')
        self.assertEqual(keys[3], 'record:d')
        self.assertEqual(used, {'source_page_family_sha256': 2, 'speaker_id': 1, 'record_id': 1})

    def test_asr_bootstrap_intervals_bracket_the_point_estimate_and_are_reproducible(self):
        rows, predictions = asr_rows()
        kwargs = dict(task='asr', benchmark_rows=rows, prediction_rows=predictions,
                      prediction_field='hypothesis', bootstrap_replicates=300)
        report, _ = scorer.evaluate_rows(**kwargs)
        again, _ = scorer.evaluate_rows(**kwargs)
        uncertainty = report['uncertainty']
        self.assertEqual(uncertainty['method'], 'cluster_percentile_bootstrap')
        self.assertEqual(uncertainty['clusters'], 3)
        low, high = uncertainty['intervals']['wer']
        self.assertLessEqual(low, report['metrics']['wer'])
        self.assertGreaterEqual(high, report['metrics']['wer'])
        self.assertEqual(uncertainty, again['uncertainty'])

    def test_bootstrap_is_off_by_default_and_says_so(self):
        rows, predictions = asr_rows()
        report, _ = scorer.evaluate_rows(task='asr', benchmark_rows=rows,
                                         prediction_rows=predictions, prediction_field='hypothesis')
        self.assertEqual(report['uncertainty']['method'], 'not_computed')
        self.assertIn('not computed', report['limitations'][-1])

    def test_qa_bootstrap_uses_only_scored_records(self):
        rows = [
            {'record_id': str(i), 'split': 'dev',
             'source_example': {'translated_answers': [{'text': 'हाँ' if i % 2 else 'ना'}]}}
            for i in range(6)
        ] + [{'record_id': 'empty', 'split': 'dev', 'source_example': {'translated_answers': []}}]
        predictions = [{'record_id': row['record_id'], 'hypothesis': 'हाँ'} for row in rows]
        report, _ = scorer.evaluate_rows(task='question_answering', benchmark_rows=rows,
                                         prediction_rows=predictions, prediction_field='hypothesis',
                                         bootstrap_replicates=200)
        self.assertEqual(report['uncertainty']['records'], 6)
        low, high = report['uncertainty']['intervals']['exact_match']
        self.assertTrue(0.0 <= low <= 0.5 <= high <= 1.0)


class SnapshotLinkTests(unittest.TestCase):
    def test_run_records_the_snapshot_and_rejects_unpinned_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bench_dir = root / 'v0.2-draft'
            bench_dir.mkdir()
            benchmark = bench_dir / 'internal__asr.jsonl'
            benchmark.write_text(json.dumps({'record_id': 'a', 'split': 'dev',
                                             'text': {'text_scoring': 'अ'}}, ensure_ascii=False) + '\n',
                                 encoding='utf-8')
            predictions = root / 'predictions.jsonl'
            predictions.write_text(json.dumps({'record_id': 'a', 'hypothesis': 'अ'}, ensure_ascii=False) + '\n',
                                   encoding='utf-8')
            snapshot = root / 'snapshot.json'
            freeze_benchmark.main(['freeze', str(bench_dir), '--out', str(snapshot)])

            report = scorer.run(task='asr', benchmark_path=benchmark, predictions_path=predictions,
                                output_dir=root / 'run', prediction_field='hypothesis',
                                model={'id': 'm', 'revision': 'r'}, git_root=None,
                                snapshot_path=snapshot)
            pinned = json.loads(snapshot.read_text(encoding='utf-8'))
            self.assertEqual(report['benchmark_snapshot']['combined_sha256'], pinned['combined_sha256'])
            self.assertEqual(report['benchmark_snapshot']['benchmark_file'], 'internal__asr.jsonl')

            benchmark.write_text(benchmark.read_text(encoding='utf-8').replace('अ', 'ब'), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'not part of snapshot'):
                scorer.run(task='asr', benchmark_path=benchmark, predictions_path=predictions,
                           output_dir=root / 'run2', prediction_field='hypothesis',
                           model={'id': 'm', 'revision': 'r'}, git_root=None,
                           snapshot_path=snapshot)


if __name__ == '__main__':
    unittest.main()
