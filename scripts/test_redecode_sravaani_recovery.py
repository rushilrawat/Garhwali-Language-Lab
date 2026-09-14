import unittest
import json
import tempfile
from pathlib import Path

import redecode_sravaani_recovery as m


class SraVaaniRecoveryRedecodeTests(unittest.TestCase):
    def test_clean_devanagari_candidate_is_preferred_over_empty_original(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2.0,
            'original_machine_transcript': '',
            'quality_flags': ['empty_transcript'],
        }
        result = m.build_result(row, 'गढ़वाली भाषा')
        self.assertEqual(result['structural_preference'], 'whisper_candidate')
        self.assertGreater(result['quality_advantage'], 0)
        self.assertFalse(result['automatic_promotion'])

    def test_wrong_script_candidate_is_not_preferred(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2.0,
            'original_machine_transcript': 'गढ़वाली भाषा',
            'quality_flags': [],
        }
        result = m.build_result(row, 'আমি ভালো')
        self.assertEqual(result['structural_preference'], 'sravaani_original')
        self.assertLess(result['quality_advantage'], 0)

    def test_candidate_corpus_frequency_is_flagged(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2.0,
            'original_machine_transcript': '',
            'quality_flags': ['empty_transcript'],
        }
        result = m.build_result(row, 'और', candidate_frequency=19)
        self.assertIn('frequent_identical_hypothesis', result['whisper_candidate_flags'])
        self.assertEqual(result['whisper_candidate_frequency'], 19)

    def test_replacement_character_is_flagged(self):
        row = {
            'audio_sha256': 'a',
            'duration_seconds': 2.0,
            'original_machine_transcript': '',
            'quality_flags': ['empty_transcript'],
        }
        result = m.build_result(row, 'गढ़वाली �')
        self.assertIn(
            'decoding_replacement_character', result['whisper_candidate_flags']
        )

    def test_summary_verifies_input_coverage(self):
        original = {
            'audio_sha256': 'a',
            'duration_seconds': 2.0,
            'original_machine_transcript': '',
            'quality_flags': ['empty_transcript'],
        }
        result = m.build_result(original, 'गढ़वाली भाषा')
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / 'input.jsonl'
            output_path = Path(directory) / 'output.jsonl'
            input_path.write_text(json.dumps(original) + '\n', encoding='utf-8')
            output_path.write_text(
                json.dumps(result, ensure_ascii=False) + '\n', encoding='utf-8'
            )
            summary = m.summarize(output_path, input_path)
        self.assertEqual(summary['records'], 1)
        self.assertEqual(summary['unique_audio_hashes'], 1)
        self.assertEqual(summary['coverage']['missing_audio_hashes'], 0)
        self.assertEqual(summary['automatic_promotions'], 0)
        self.assertTrue(summary['originals_preserved'])


if __name__ == '__main__':
    unittest.main()
