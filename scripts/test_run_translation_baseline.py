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

    def test_translation_memory_selects_closest_source(self):
        development = [
            {'source': 'म्यर घर', 'target': 'my house'},
            {'source': 'त्वेर नाम', 'target': 'your name'},
        ]
        predictions = m.translation_memory_predict(development, ['म्यर घर छ'])
        self.assertEqual(predictions[0]['hypothesis'], 'my house')
        self.assertGreater(predictions[0]['similarity'], 0)

    def test_run_uses_dev_as_memory_and_test_as_evaluation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'flores.jsonl'
            rows = [
                {'split': 'dev', 'record_id': 'd', 'source_example': {
                    'source': 'म्यर घर', 'target': 'my house', 'translation_direction': 'xxen'}},
                {'split': 'test', 'record_id': 't', 'source_example': {
                    'source': 'म्यर घर छ', 'target': 'this is my house', 'translation_direction': 'xxen'}},
            ]
            source.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            report = m.run(source, root / 'out')
            self.assertEqual(report['development_records'], 1)
            self.assertEqual(report['test_records'], 1)
            self.assertEqual(report['translation_direction'], 'gbm_to_en')
            self.assertTrue((root / 'out/predictions.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
