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


if __name__ == '__main__':
    unittest.main()
