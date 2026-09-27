import hashlib
import tempfile
import unittest
from pathlib import Path

from validate_benchmark_v02 import (
    validate_asr_records,
    validate_external_records,
    validate_internal_text_records,
    validate_recommended_text_records,
)


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def flores_row(record_id='f:dev:1'):
    text = 'गढ़वाली वाक्य'
    return {
        'record_id': record_id,
        'split': 'dev',
        'text_original': text,
        'text_normalized': text,
        'text_sha256': sha(text),
        'iso_639_3': 'gbm',
        'script': 'Deva',
        'rights_status': 'upstream_declared_license; review_before_redistribution',
        'license_id': 'MIT',
        'license_url': 'https://opensource.org/license/mit',
        'provenance': {'url': 'https://example.test/source', 'sha256': 'a' * 64},
        'usage': 'evaluation_only',
        'training_eligible': False,
        'source_example': {
            'lang': 'en', 'source': 'English source.', 'target': 'Garhwali target.',
            'translation_direction': 'en-gbm',
        },
    }


class ValidateBenchmarkV02Tests(unittest.TestCase):
    def test_accepts_structurally_valid_external_translation_record(self):
        result = validate_external_records('flores', [flores_row()])

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['records'], 1)
        self.assertEqual(result['split_counts'], {'dev': 1})
        self.assertEqual(result['source_language_counts'], {'en': 1})

    def test_reports_duplicate_ids_and_empty_task_references(self):
        first = flores_row()
        second = flores_row()
        second['source_example']['target'] = '  '

        result = validate_external_records('flores', [first, second])

        self.assertTrue(any('duplicate record_id' in error for error in result['errors']))
        self.assertTrue(any('source_example.target is empty' in error for error in result['errors']))

    def test_allows_explicitly_empty_xorqa_answers_as_unanswerable(self):
        row = flores_row('x:dev:1')
        row['source_example'] = {'lang': 'en', 'context': 'Context passage.', 'question': 'Question?', 'answers': []}

        result = validate_external_records('xorqa', [row])

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['empty_answer_records'], 1)

    def test_flags_malformed_unicode_and_normalized_hash_mismatch(self):
        row = flores_row()
        row['text_original'] = 'broken\ud800'
        row['text_normalized'] = 'wrong'

        result = validate_external_records('flores', [row])

        self.assertTrue(any('malformed Unicode surrogate' in error for error in result['errors']))
        self.assertTrue(any('text_sha256 does not match' in error for error in result['errors']))

    def test_checks_asr_local_path_and_audio_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / 'audio' / 'clip.wav'
            audio.parent.mkdir()
            audio.write_bytes(b'fake audio bytes')
            row = {
                'audio_path': 'upstream/clip.wav',
                'local_audio_path': 'audio/clip.wav',
                'audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
                'asr_target': 'Garhwali transcript',
                'asr_target_sha256': sha('Garhwali transcript'),
                'split': 'test',
                'duration_seconds': 1.25,
                'speaker_id': 'speaker-local',
                'license': 'CC-BY-4.0',
                'source': 'example/source',
            }

            result = validate_asr_records([row], root)

            self.assertEqual(result['errors'], [])
            self.assertEqual(result['records'], 1)
            self.assertEqual(result['unique_speakers'], 1)
            self.assertEqual(result['audio_files_verified'], 1)

    def test_rejects_asr_path_escape_and_hash_mismatch(self):
        row = {
            'audio_path': 'upstream/clip.wav', 'local_audio_path': '../outside.wav',
            'audio_sha256': '0' * 64, 'asr_target': 'transcript',
            'asr_target_sha256': '0' * 64, 'split': 'test',
            'duration_seconds': 1.0, 'speaker_id': 'speaker', 'license': 'CC-BY-4.0',
            'source': 'example/source',
        }

        result = validate_asr_records([row], Path('/tmp/project'))

        self.assertTrue(any('escapes project root' in error for error in result['errors']))
        self.assertTrue(any('ASR target hash does not match' in error for error in result['errors']))

    def test_validates_recommended_text_metadata_without_rejecting_script_mix(self):
        rows = [{
            'id': 'text-1', 'text': 'गढ़वाली English मिश्रित', 'split': 'train',
            'language': 'gbm', 'script': 'Deva', 'provenance': [{'url': 'https://example.test'}],
            'public_rights_basis': 'source_recorded',
        }]

        result = validate_recommended_text_records(rows, 'train')

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['records'], 1)
        self.assertEqual(result['mixed_script_records'], 1)

    def test_rejects_missing_text_metadata_or_split_mismatch(self):
        row = {
            'id': 'text-1', 'text': 'गढ़वाली वाक्य', 'split': 'test',
            'language': 'gbm', 'script': 'Deva', 'provenance': [],
        }

        result = validate_recommended_text_records([row], 'train')

        self.assertTrue(any('split differs from view' in error for error in result['errors']))
        self.assertTrue(any('provenance is missing' in error for error in result['errors']))

    def test_validates_internal_text_hash_and_unique_segment_id(self):
        text = 'गढ़वाली वाक्य'
        row = {
            'segment_sha256': sha(text), 'duplicate_component_id': 'component-1',
            'text': text, 'split': 'test',
        }

        result = validate_internal_text_records([row])

        self.assertEqual(result['errors'], [])
        self.assertEqual(result['records'], 1)

        row['segment_sha256'] = '0' * 64
        result = validate_internal_text_records([row])
        self.assertTrue(any('segment hash does not match text' in error for error in result['errors']))


if __name__ == '__main__':
    unittest.main()
