import json
import tempfile
import unittest
from pathlib import Path

import transcribe_vaani_drafts as m


class TranscribeVaaniDraftTests(unittest.TestCase):
    def test_pending_rows_resume_by_audio_hash(self):
        rows = [
            {'audio_sha256': 'b', 'local_audio_path': 'b.wav'},
            {'audio_sha256': 'a', 'local_audio_path': 'a.wav'},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'drafts.jsonl'
            output.write_text(json.dumps({'audio_sha256': 'a'}) + '\n', encoding='utf-8')
            self.assertEqual(
                [row['audio_sha256'] for row in m.pending_rows(rows, output)],
                ['b'],
            )

    def test_draft_record_cannot_be_training_eligible(self):
        row = {'audio_sha256': 'a', 'local_audio_path': 'a.wav', 'district': 'Tehri Garhwal'}
        draft = m.build_draft_record(row, 'गढ़वाली वाक्य', -0.5, 'model/path')
        self.assertFalse(draft['training_eligible'])
        self.assertEqual(draft['review_status'], 'machine_draft_needs_native_review')
        self.assertAlmostEqual(draft['token_confidence_uncalibrated'], 0.60653066)

    def test_generation_scores_in_a_separate_forward_pass(self):
        class Number:
            def __init__(self, value):
                self.value = value

            def detach(self):
                return self

            def cpu(self):
                return self

            def __float__(self):
                return self.value

            def __neg__(self):
                return Number(-self.value)

        class Model:
            def generate(self, features, **kwargs):
                self.generation_kwargs = kwargs
                return [[1, 2, 3]]

            def __call__(self, **kwargs):
                self.score_kwargs = kwargs
                return type('Output', (), {'loss': Number(0.5)})()

        class Processor:
            def batch_decode(self, sequences, skip_special_tokens):
                return ['गढ़वाली']

        model = Model()
        transcript, score = m.generate_transcript_and_score(model, Processor(), 'features')
        self.assertEqual(transcript, 'गढ़वाली')
        self.assertEqual(score, -0.5)
        self.assertNotIn('output_scores', model.generation_kwargs)
        self.assertNotIn('return_dict_in_generate', model.generation_kwargs)


if __name__ == '__main__':
    unittest.main()
