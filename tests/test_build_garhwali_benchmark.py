import json
import math
import tempfile
import unittest
from pathlib import Path

import build_garhwali_benchmark as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )


class GarhwaliBenchmarkTests(unittest.TestCase):
    def test_builds_index_checks_leakage_and_scores_character_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmarks = root / 'benchmarks'
            write_jsonl(benchmarks / 'indicgenbench_flores.jsonl', [
                {'text_normalized': 'अब', 'source_example': {'source': 'अब', 'target': 'now'}},
            ])
            write_jsonl(benchmarks / 'indicgenbench_crosssum.jsonl', [
                {'text_normalized': 'सार', 'source_example': {'text': 'article', 'summary': 'सार'}},
            ])
            write_jsonl(benchmarks / 'indicgenbench_xorqa.jsonl', [
                {'text_normalized': 'सवाल', 'source_example': {
                    'context': 'context', 'question': 'सवाल', 'answers': [{'text': 'answer'}],
                }},
            ])
            train_text = root / 'text/train.jsonl'
            eval_text = root / 'evaluation/text_candidate.jsonl'
            train_asr = root / 'asr/train.jsonl'
            eval_asr = root / 'evaluation/asr_candidate.jsonl'
            write_jsonl(train_text, [
                {'segment_sha256': 'a', 'text': 'अब'},
                {'segment_sha256': 'a2', 'text': 'अब घर'},
            ])
            write_jsonl(eval_text, [{'segment_sha256': 'b', 'text': 'गढ़वाली'}])
            write_jsonl(train_asr, [{'audio_sha256': 'c', 'speaker_id': 'speaker-a'}])
            write_jsonl(eval_asr, [{'audio_sha256': 'd', 'speaker_id': 'speaker-b'}])

            report = m.build_benchmark(
                benchmarks,
                train_text,
                eval_text,
                train_asr,
                eval_asr,
                None,
                root / 'out',
            )

            self.assertEqual(report['records']['external_total'], 3)
            self.assertEqual(report['records']['text_evaluation'], 1)
            self.assertEqual(report['records']['asr_evaluation'], 1)
            self.assertEqual(report['leakage']['external_exact_train_text'], 1)
            self.assertEqual(report['leakage']['internal_text_exact_train_text'], 0)
            self.assertEqual(report['leakage']['asr_speaker_overlap'], 0)
            self.assertTrue(math.isfinite(report['baselines']['character_bigram']['perplexity']))
            self.assertTrue((root / 'out/manifest.json').exists())
            self.assertTrue((root / 'out/report.md').exists())

    def test_rejects_internal_text_leakage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            benchmarks = root / 'benchmarks'
            for name in ('flores', 'crosssum', 'xorqa'):
                write_jsonl(benchmarks / f'indicgenbench_{name}.jsonl', [])
            write_jsonl(root / 'train.jsonl', [{'text': 'एक ही वाक्य'}])
            write_jsonl(root / 'eval.jsonl', [{'text': 'एक ही वाक्य'}])
            write_jsonl(root / 'train_asr.jsonl', [])
            write_jsonl(root / 'eval_asr.jsonl', [])
            with self.assertRaisesRegex(ValueError, 'internal evaluation text overlaps training text'):
                m.build_benchmark(
                    benchmarks,
                    root / 'train.jsonl',
                    root / 'eval.jsonl',
                    root / 'train_asr.jsonl',
                    root / 'eval_asr.jsonl',
                    None,
                    root / 'out',
                )


if __name__ == '__main__':
    unittest.main()
