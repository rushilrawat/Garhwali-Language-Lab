import json
import tempfile
import unittest
from pathlib import Path

import build_language_resources as m


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')


class LanguageResourceTests(unittest.TestCase):
    def test_builds_train_only_tokenizer_pronunciation_and_tts_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            text = root / 'text.jsonl'
            lexicon = root / 'lexicon.jsonl'
            audio = root / 'audio'
            out = root / 'out'
            write_jsonl(text, [
                {'segment_sha256': 'a', 'text': 'गढ़वाली भाषा', 'split': 'train'},
                {'segment_sha256': 'b', 'text': 'परीक्षण', 'split': 'test'},
            ])
            write_jsonl(lexicon, [
                {
                    'text_sha256': 'c',
                    'form': 'चार',
                    'glosses': {'english': ['four']},
                    'provenance': [{'linguistic_metadata': {'segments': 'tʃ aː r'}}],
                },
                {
                    'text_sha256': 'd',
                    'form': 'पाणी',
                    'glosses': {'english': ['water']},
                    'provenance': [],
                },
            ])
            for split in ('train', 'validation', 'test'):
                rows = [] if split != 'train' else [{
                    'audio_sha256': 'e',
                    'derived_audio_sha256': 'f',
                    'derived_audio_path': 'derived.wav',
                    'asr_target_clean': 'गढ़वाली भाषा',
                    'speaker_id': 'speaker-1',
                    'license': 'CC-BY-4.0',
                    'split': 'train',
                }]
                write_jsonl(audio / f'{split}.jsonl', rows)

            report = m.build_resources(text, lexicon, audio, out)

            tokenizer = json.loads((out / 'tokenizer/tokenizer.json').read_text())
            self.assertIn('ग', tokenizer['vocab'])
            self.assertNotIn('प', tokenizer['vocab'])
            pronunciations = [json.loads(line) for line in (out / 'pronunciation/lexicon.jsonl').read_text().splitlines()]
            self.assertEqual(pronunciations[0]['source_phonetic_segments'], ['tʃ', 'aː', 'r'])
            self.assertEqual(pronunciations[1]['pronunciation_status'], 'grapheme_only_pending_native_review')
            tts = [json.loads(line) for line in (out / 'tts/train.jsonl').read_text().splitlines()]
            self.assertEqual(tts[0]['text'], 'गढ़वाली भाषा')
            self.assertEqual(tts[0]['audio'], 'derived.wav')
            self.assertEqual(report['tts_pairs'], 1)


if __name__ == '__main__':
    unittest.main()
