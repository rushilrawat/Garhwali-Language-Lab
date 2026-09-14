import json
import tempfile
import unittest
from pathlib import Path

import train_whisper_garhwali as m


class WhisperTrainingTests(unittest.TestCase):
    def test_load_rows_is_stable_and_honors_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'train.jsonl'
            path.write_text(
                json.dumps({'audio_sha256': 'b', 'asr_target_clean': 'दुई'}) + '\n'
                + json.dumps({'audio_sha256': 'a', 'asr_target_clean': 'एक'}) + '\n',
                encoding='utf-8',
            )
            self.assertEqual([row['audio_sha256'] for row in m.load_rows(path, 1)], ['a'])

    def test_summarizes_asr_error_counts(self):
        scores = [
            {'word_errors': 2, 'reference_words': 4, 'character_errors': 3, 'reference_characters': 10},
            {'word_errors': 1, 'reference_words': 2, 'character_errors': 1, 'reference_characters': 5},
        ]
        self.assertEqual(m.summarize_scores(scores), {
            'word_errors': 3,
            'reference_words': 6,
            'character_errors': 4,
            'reference_characters': 15,
            'wer': 0.5,
            'cer': 4 / 15,
        })

    def test_load_rows_filters_curriculum_stage_before_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'train.jsonl'
            path.write_text(
                json.dumps({'audio_sha256': 'a', 'introduced_stage': 2}) + '\n'
                + json.dumps({'audio_sha256': 'b', 'introduced_stage': 0}) + '\n',
                encoding='utf-8',
            )
            rows = m.load_rows(path, limit=1, max_stage=0)
            self.assertEqual([row['audio_sha256'] for row in rows], ['b'])

    def test_curriculum_rows_supply_target_and_weight(self):
        row = {'target_text': 'गढ़वाली भाषा', 'sample_weight': 0.25}
        self.assertEqual(m.training_target(row), 'गढ़वाली भाषा')
        self.assertEqual(m.training_weight(row), 0.25)
        self.assertEqual(m.training_weight({'asr_target_clean': 'मानक'}), 1.0)

    def test_training_weight_rejects_nonpositive_values(self):
        with self.assertRaisesRegex(ValueError, 'positive'):
            m.training_weight({'target_text': 'पाठ', 'sample_weight': 0})

    def test_weighted_training_loss_scales_the_optimized_loss(self):
        loss = m.weighted_training_loss(8.0, {'sample_weight': 0.25})
        self.assertEqual(loss, 2.0)

    def test_curriculum_defaults_to_validation_without_changing_legacy_default(self):
        self.assertEqual(m.resolve_evaluation_split(None, 0), 'validation')
        self.assertEqual(m.resolve_evaluation_split(None, None), 'test')
        self.assertEqual(m.resolve_evaluation_split('test', 4), 'test')

    def test_previous_stage_must_be_completed_immediate_predecessor(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / 'config.json').write_text('{}', encoding='utf-8')
            (output / 'model.safetensors').write_bytes(b'model')
            (output / 'processor_config.json').write_text('{}', encoding='utf-8')
            (output / 'tokenizer.json').write_text('{}', encoding='utf-8')
            (output / 'report.json').write_text(json.dumps({
                'training_complete': True,
                'curriculum_stage': 2,
            }), encoding='utf-8')
            self.assertEqual(m.validate_previous_stage(output, 3)['curriculum_stage'], 2)
            with self.assertRaisesRegex(ValueError, 'stage 3'):
                m.validate_previous_stage(output, 4)

    def test_previous_stage_requires_model_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / 'report.json').write_text(json.dumps({
                'training_complete': True,
                'curriculum_stage': 0,
            }), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'model checkpoint'):
                m.validate_previous_stage(output, 1)

    def test_previous_stage_accepts_explicit_curriculum_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            for name in ('config.json', 'processor_config.json', 'tokenizer.json'):
                (output / name).write_text('{}', encoding='utf-8')
            (output / 'model.safetensors').write_bytes(b'model')
            (output / 'report.json').write_text(json.dumps({
                'training_complete': False,
            }), encoding='utf-8')
            (output / 'curriculum_stage_report.json').write_text(json.dumps({
                'training_complete': True,
                'curriculum_stage': 0,
            }), encoding='utf-8')
            report = m.validate_previous_stage(output, 1)
            self.assertEqual(report['curriculum_stage'], 0)

    def test_dry_run_plan_checks_audio_and_summarizes_tiers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'one.wav').write_bytes(b'RIFF')
            train = [
                {
                    'audio_sha256': 'a',
                    'local_audio_path': 'one.wav',
                    'target_text': 'एक',
                    'sample_weight': 1.0,
                    'curriculum_tier': 'human_reference',
                    'duration_seconds': 2,
                },
                {
                    'audio_sha256': 'b',
                    'local_audio_path': 'missing.wav',
                    'target_text': 'दुई',
                    'sample_weight': 0.2,
                    'curriculum_tier': 'recovery_low',
                    'duration_seconds': 3,
                },
            ]
            plan = m.build_dry_run_plan(train, train[:1], epochs=2, root=root)
            self.assertEqual(plan['train_records'], 2)
            self.assertEqual(plan['projected_training_steps'], 4)
            self.assertEqual(plan['records_by_tier'], {
                'human_reference': 1,
                'recovery_low': 1,
            })
            self.assertAlmostEqual(plan['effective_weight_mass'], 1.2)
            self.assertEqual(plan['missing_audio_files'], 1)
            self.assertEqual(plan['empty_targets'], 0)
            self.assertEqual(plan['empty_evaluation_targets'], 0)


if __name__ == '__main__':
    unittest.main()
