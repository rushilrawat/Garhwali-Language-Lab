import importlib
import json
import tempfile
import unittest
from pathlib import Path


try:
    analysis = importlib.import_module('analyze_translation_uncertainty')
except ModuleNotFoundError as error:
    if error.name != 'analyze_translation_uncertainty':
        raise
    analysis = None


class TranslationUncertaintyTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(analysis, 'analyze_translation_uncertainty module is missing')
        return analysis

    def test_identical_systems_have_zero_paired_delta_and_interval(self):
        rows = [
            {'record_id': f'id-{index}', 'reference': ref, 'system_a': hyp, 'system_b': hyp}
            for index, (ref, hyp) in enumerate([
                ('one short reference', 'one short output'),
                ('another reference text', 'different output'),
                ('गढ़वाली अंग्रेजी संदर्भ', 'garhwali english output'),
            ])
        ]

        report, paired = self.module().analyze_rows(
            rows, baseline_field='system_a', candidate_field='system_b',
            replicates=100, seed=23,
        )

        self.assertEqual(report['evaluation_records'], 3)
        for metric in ('corpus_bleu_smoothed', 'corpus_chrf2', 'exact_match'):
            self.assertEqual(report['paired_deltas'][metric]['candidate_minus_baseline'], 0.0)
            self.assertEqual(report['paired_deltas'][metric]['confidence_interval'], [0.0, 0.0])
        self.assertEqual(len(paired), 3)

    def test_bootstrap_is_reproducible_for_a_fixed_seed(self):
        rows = [
            {'record_id': 'a', 'reference': 'alpha beta', 'baseline': 'alpha', 'candidate': 'alpha beta'},
            {'record_id': 'b', 'reference': 'gamma delta', 'baseline': 'gamma delta', 'candidate': ''},
        ]
        args = {'baseline_field': 'baseline', 'candidate_field': 'candidate', 'replicates': 250, 'seed': 7}

        first, _ = self.module().analyze_rows(rows, **args)
        second, _ = self.module().analyze_rows(rows, **args)

        self.assertEqual(first['paired_deltas'], second['paired_deltas'])
        self.assertEqual(first['bootstrap']['seed'], 7)

    def test_precomputed_resample_metrics_match_project_metric_functions(self):
        metric_module = self.module()
        references = ['short text', 'a longer example sentence']
        hypotheses = ['short output', 'a longer sample sentence']
        indices = [0, 1, 1, 0]
        components = [
            metric_module._record_components(reference, hypothesis)
            for reference, hypothesis in zip(references, hypotheses)
        ]
        expected = metric_module.metric_summary(
            [references[index] for index in indices],
            [hypotheses[index] for index in indices],
        )

        actual = metric_module._score_resample(indices, components)

        for name in ('corpus_bleu_smoothed', 'corpus_chrf2', 'exact_match'):
            self.assertEqual(actual[name], expected[name])

    def test_requires_unique_ids_and_nonempty_references(self):
        with self.assertRaisesRegex(ValueError, 'duplicate record_id'):
            self.module().analyze_rows([
                {'record_id': 'same', 'reference': 'x', 'base': 'x', 'new': 'x'},
                {'record_id': 'same', 'reference': 'y', 'base': 'y', 'new': 'y'},
            ], baseline_field='base', candidate_field='new', replicates=10)
        with self.assertRaisesRegex(ValueError, 'non-empty reference'):
            self.module().analyze_rows([
                {'record_id': 'empty', 'reference': '  ', 'base': 'x', 'new': 'x'},
            ], baseline_field='base', candidate_field='new', replicates=10)

    def test_run_writes_hash_linked_analysis_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'predictions.jsonl'
            source.write_text(
                ''.join(json.dumps(row) + '\n' for row in [
                    {'record_id': 'a', 'reference': 'same text', 'base': 'same text', 'new': 'same text'},
                    {'record_id': 'b', 'reference': 'other text', 'base': 'other', 'new': 'other text'},
                ]),
                encoding='utf-8',
            )

            report = self.module().run(
                predictions_path=source, output_dir=root / 'output',
                baseline_field='base', candidate_field='new', replicates=40,
                seed=13, git_root=None,
            )

            manifest = json.loads((root / 'output/run_manifest.json').read_text())
            self.assertEqual(manifest['evaluation_split'], 'dev')
            self.assertEqual(manifest['selected_record_count'], 2)
            self.assertEqual(manifest['selected_record_ids'], ['a', 'b'])
            self.assertEqual(report['evaluation_records'], 2)
            self.assertIn('report.json', manifest['outputs'])


if __name__ == '__main__':
    unittest.main()
