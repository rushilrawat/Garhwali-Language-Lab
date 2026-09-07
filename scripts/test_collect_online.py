import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name('collect_online.py')


class CollectionTests(unittest.TestCase):
    def load(self):
        self.assertTrue(MODULE.exists(), 'Online collector has not been implemented')
        spec = importlib.util.spec_from_file_location('collect_online', MODULE)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_failed_validation_preserves_previous_source(self):
        mod = self.load()
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'source.jsonl'
            p.write_text('previous\n')
            with self.assertRaises(ValueError):
                mod.save_records(p, [{'record_id': 'x', 'text_original': ''}])
            self.assertEqual(p.read_text(), 'previous\n')

    def test_duplicate_identifiers_are_rejected(self):
        mod = self.load()
        r = mod.make_record('test', '1', 'गढ़वाली', {'raw_path': 'a', 'sha256': 'b'},
                            'CC-BY-4.0', 'https://creativecommons.org/licenses/by/4.0/', 'test')
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.save_records(Path(d) / 'x.jsonl', [r, r])

    def test_wiktionary_extracts_only_garhwali_section(self):
        mod = self.load()
        text = '==Hindi==\nHindi text\n==Garhwali==\n===Noun===\n# water\n==Nepali==\nNepali text'
        self.assertEqual(mod.garhwali_section(text), '===Noun===\n# water')

    def test_transcript_keeps_upstream_split_and_is_unreviewed(self):
        mod = self.load()
        row = {'iso_639_3': 'gbm', 'raw_text': 'मि ठीक छौं।', 'speaker_id': '12',
               'prompt_id': 'p1', 'segment_id': 's1', 'duration': 4.2}
        rec = mod.meta_record(row, 'test', 0, {'raw_path': 'x', 'sha256': 'y'})
        self.assertEqual(rec['split'], 'test')
        self.assertFalse(rec['native_reviewed'])
        self.assertFalse(rec['training_eligible'])
        self.assertEqual(rec['text_original'], row['raw_text'])
        with self.assertRaises(ValueError):
            mod.meta_record(dict(row, iso_639_3='hin'), 'test', 0, {})

    def test_benchmark_train_named_split_still_cannot_train(self):
        mod = self.load()
        self.assertTrue(hasattr(mod, 'benchmark_record'), 'Benchmark isolation not implemented')
        row = {'lang': 'gbm', 'question': 'कन छा तुम?', 'translated_answers': [{'text': 'ठीक'}]}
        rec = mod.benchmark_record('xorqa', row, 'train', 0, {'raw_path': 'x', 'sha256': 'y'}, 'canary')
        self.assertEqual(rec['split'], 'train')
        self.assertEqual(rec['usage'], 'evaluation_only')
        self.assertFalse(rec['training_eligible'])


if __name__ == '__main__':
    unittest.main()
