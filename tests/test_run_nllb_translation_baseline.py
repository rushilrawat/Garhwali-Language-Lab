import unittest
import json
import sys
import tempfile
import types
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

import run_nllb_translation_baseline as m


class NllbTranslationBaselineTests(unittest.TestCase):
    def test_defaults_to_deterministic_dev_subset(self):
        rows = [
            {'split': 'dev', 'record_id': 'b'},
            {'split': 'dev', 'record_id': 'a'},
            {'split': 'test', 'record_id': 'b'},
        ]
        self.assertEqual(
            [row['record_id'] for row in m.select_rows(rows, limit=1)],
            ['a'],
        )

    def test_test_requires_an_explicit_split_and_is_sorted(self):
        rows = [
            {'split': 'test', 'record_id': 'b'},
            {'split': 'dev', 'record_id': 'd'},
            {'split': 'test', 'record_id': 'a'},
        ]
        self.assertEqual(
            [row['record_id'] for row in m.select_rows(rows, split='test')],
            ['a', 'b'],
        )

    def test_zero_limit_keeps_complete_requested_split(self):
        rows = [{'split': 'dev', 'record_id': value} for value in ('b', 'a')]
        self.assertEqual(len(m.select_rows(rows, limit=0)), 2)

    def test_negative_limit_is_rejected(self):
        with self.assertRaises(ValueError):
            m.select_rows([], limit=-1)

    def test_test_split_requires_historical_opt_in_before_model_loading(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'rows.jsonl'
            source.write_text(json.dumps({
                'split': 'test',
                'record_id': 'test-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'allow_historical_test'):
                m.run(input_path=source, split='test')

    def test_missing_input_fails_before_model_runtime_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileNotFoundError):
                m.run(
                    input_path=Path(tmp) / 'missing.jsonl',
                    model_path=Path(tmp) / 'missing-model',
                )

    def test_missing_checkpoint_fails_before_model_runtime_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'rows.jsonl'
            source.write_text(json.dumps({
                'split': 'dev',
                'record_id': 'dev-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            with self.assertRaises(FileNotFoundError):
                m.run(input_path=source, model_path=root / 'missing-model')

    def test_checkpoint_without_config_fails_before_model_runtime_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'rows.jsonl'
            source.write_text(json.dumps({
                'split': 'dev',
                'record_id': 'dev-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            checkpoint = root / 'checkpoint'
            checkpoint.mkdir()
            with self.assertRaisesRegex(ValueError, 'config.json'):
                m.run(input_path=source, model_path=checkpoint)

    def test_mocked_dev_run_writes_hash_linked_manifest(self):
        class FakeTensor:
            def to(self, device):
                return self

        class FakeModel:
            def to(self, device):
                return self

            def eval(self):
                return None

            def generate(self, **kwargs):
                return [[1]]

        class FakeTokenizer:
            def convert_tokens_to_ids(self, token):
                return 1

            def __call__(self, *args, **kwargs):
                return {'input_ids': FakeTensor()}

            def batch_decode(self, generated, **kwargs):
                return ['my house']

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'rows.jsonl'
            source.write_text(json.dumps({
                'split': 'dev',
                'record_id': 'dev-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            checkpoint = root / 'checkpoint'
            checkpoint.mkdir()
            (checkpoint / 'config.json').write_text('{"model_type":"fixture"}')
            fake_torch = types.ModuleType('torch')
            fake_torch.__version__ = '2.fixture'
            fake_torch.backends = types.SimpleNamespace(
                mps=types.SimpleNamespace(is_available=lambda: False),
            )
            fake_torch.no_grad = nullcontext
            fake_transformers = types.ModuleType('transformers')
            fake_transformers.__version__ = '4.fixture'
            fake_transformers.AutoTokenizer = types.SimpleNamespace(
                from_pretrained=lambda *args, **kwargs: FakeTokenizer(),
            )
            fake_transformers.AutoModelForSeq2SeqLM = types.SimpleNamespace(
                from_pretrained=lambda *args, **kwargs: FakeModel(),
            )
            output = root / 'out'
            with patch.dict(sys.modules, {'torch': fake_torch, 'transformers': fake_transformers}):
                report = m.run(
                    input_path=source,
                    output_dir=output,
                    model_path=checkpoint,
                )
            manifest = json.loads((output / 'run_manifest.json').read_text())
            self.assertEqual(report['evaluation_records'], 1)
            self.assertEqual(manifest['selected_record_ids'], ['dev-1'])
            self.assertEqual(manifest['runtime']['torch'], '2.fixture')
            self.assertEqual(manifest['runtime']['transformers'], '4.fixture')
            self.assertIn('predictions.jsonl', manifest['outputs'])

    def test_unavailable_mps_fails_before_loading_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'rows.jsonl'
            source.write_text(json.dumps({
                'split': 'dev',
                'record_id': 'dev-1',
                'source_example': {
                    'source': 'म्यर घर',
                    'target': 'my house',
                    'translation_direction': 'xxen',
                },
            }) + '\n', encoding='utf-8')
            checkpoint = root / 'checkpoint'
            checkpoint.mkdir()
            (checkpoint / 'config.json').write_text('{"model_type":"fixture"}')
            fake_torch = types.ModuleType('torch')
            fake_torch.__version__ = '2.fixture'
            fake_torch.backends = types.SimpleNamespace(
                mps=types.SimpleNamespace(is_available=lambda: False),
            )
            fake_transformers = types.ModuleType('transformers')
            fake_transformers.__version__ = '4.fixture'
            fake_transformers.AutoTokenizer = types.SimpleNamespace(
                from_pretrained=lambda *args, **kwargs: self.fail('tokenizer loaded before device check'),
            )
            fake_transformers.AutoModelForSeq2SeqLM = types.SimpleNamespace(
                from_pretrained=lambda *args, **kwargs: self.fail('model loaded before device check'),
            )
            with patch.dict(sys.modules, {'torch': fake_torch, 'transformers': fake_transformers}):
                with self.assertRaisesRegex(ValueError, 'MPS.*not available'):
                    m.run(input_path=source, model_path=checkpoint, device='mps')


if __name__ == '__main__':
    unittest.main()
