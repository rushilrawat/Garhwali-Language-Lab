import hashlib
import io
import json
import shutil
import struct
import subprocess
import tempfile
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

import pyarrow as pa
import pyarrow.parquet as pq

import prepare_meta_omnilingual_asr as prepare


def write_jsonl(path, rows):
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def test_wav_bytes():
    output = io.BytesIO()
    with wave.open(output, 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(16000)
        stream.writeframes(struct.pack('<h', 0) * 1600)
    return output.getvalue()


def test_flac_bytes():
    ffmpeg = shutil.which('ffmpeg')
    samples = struct.pack('<h', 0) * 1600
    result = subprocess.run(
        [ffmpeg, '-v', 'error', '-f', 's16le', '-ar', '16000', '-ac', '1', '-i', 'pipe:0',
         '-c:a', 'flac', '-f', 'flac', 'pipe:1'],
        input=samples, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    return result.stdout


class PrepareMetaOmnilingualAsrTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.parquet_root = self.root / 'parquet'
        self.parquet_root.mkdir()
        self.source_path = self.root / 'source.jsonl'
        self.text_path = self.root / 'text.jsonl'
        self.output_path = self.root / 'output'

        source_rows = []
        text_rows = []
        for source_split, output_split, index, safe_train, safe_eval in (
            ('train', 'train', 0, True, True),
            ('dev', 'validation', 0, False, True),
            ('test', 'test', 0, False, False),
        ):
            filename = f'{source_split}-00000-of-00001.parquet'
            audio = f'fake-flac-{source_split}'.encode()
            transcript = f'गढ़वाली वाक्य {source_split}'
            text_sha = hashlib.sha256(transcript.encode()).hexdigest()
            record_id = f'meta:{source_split}:0'
            source_rows.append({
                'record_id': record_id,
                'audio_sha256': hashlib.sha256(audio).hexdigest(),
                'text_sha256': text_sha,
                'split': output_split,
                'source_split': source_split,
                'source': 'facebook/omnilingual-asr-corpus',
                'source_url': 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
                'source_revision': 'abc123',
                'source_license': 'CC-BY-4.0',
                'source_license_url': 'https://creativecommons.org/licenses/by/4.0/',
                'source_file': f'data/gbm_Deva/{filename}',
                'source_file_sha256': 'pending',
                'upstream_row_index': index,
                'duration_seconds': 0.25,
                'duplicate_audio_count': 1,
                'duplicate_text_count': 1,
                'cross_split_audio_overlap': False,
                'cross_split_text_overlap': False,
                'cross_corpus_audio_overlap': False,
                'cross_corpus_text_overlap': False,
                'transcript_conflict_for_audio': False,
                'split_safe_for_training': safe_train,
                'split_safe_for_evaluation': safe_eval,
            })
            text_rows.append({
                'record_id': record_id,
                'split': source_split,
                'upstream_row_index': index,
                'text_normalized': transcript,
                'text_sha256': text_sha,
                'speaker_id': f'spk-{source_split}',
                'prompt_id': 'prompt-1',
                'segment_id': 'segment-1',
                'prompt': 'prompt',
            })
            parquet_path = self.parquet_root / filename
            table = pa.table({
                'language': ['gbm_Deva'],
                'iso_639_3': ['gbm'],
                'glottocode': ['garh1243'],
                'iso_15924': ['Deva'],
                'duration': [0.25],
                'raw_text': [transcript],
                'prompt': ['prompt'],
                'speaker_id': [f'spk-{source_split}'],
                'prompt_id': ['prompt-1'],
                'segment_id': ['segment-1'],
                'audio': pa.array([{'bytes': audio, 'path': 'source.flac'}], type=pa.struct([
                    ('bytes', pa.binary()), ('path', pa.string()),
                ])),
            })
            pq.write_table(table, parquet_path)
            source_rows[-1]['source_file_sha256'] = prepare.sha256_file(parquet_path)

        write_jsonl(self.source_path, source_rows)
        write_jsonl(self.text_path, text_rows)

    def tearDown(self):
        self.temp.cleanup()

    def test_build_reconciles_rows_and_keeps_unsafe_test_in_audit_only(self):
        with patch.object(prepare, 'decode_flac_to_wav', return_value=test_wav_bytes()):
            report = prepare.build_manifest(
                self.source_path, self.text_path, self.parquet_root, self.output_path,
            )

        self.assertEqual(report['source_rows'], 3)
        self.assertEqual(report['safe_rows'], {'train': 1, 'validation': 1, 'test': 0})
        self.assertEqual(report['excluded_rows'], {'train': 0, 'validation': 0, 'test': 1})
        self.assertEqual(report['output_manifests']['validation']['sha256'],
                         prepare.sha256_file(self.output_path / 'validation.jsonl'))
        audit = [json.loads(line) for line in (self.output_path / 'source_audit.jsonl').read_text().splitlines()]
        self.assertEqual(len(audit), 3)
        included = next(row for row in audit if row['source_split'] == 'dev')
        self.assertEqual(included['duplicate_audio_count'], 1)
        self.assertFalse(included['cross_split_text_overlap'])
        self.assertFalse(included['transcript_conflict_for_audio'])
        excluded = next(row for row in audit if row['source_split'] == 'test')
        self.assertEqual(excluded['exclusion_reasons'], ['split_safe_for_evaluation=false'])
        self.assertIsNone(excluded['local_audio_path'])

        validation = json.loads((self.output_path / 'validation.jsonl').read_text())
        self.assertEqual(validation['record_id'], 'meta:dev:0')
        self.assertEqual(validation['asr_target_clean'], 'गढ़वाली वाक्य dev')
        self.assertEqual(validation['source_license'], 'CC-BY-4.0')
        self.assertEqual(validation['source_split'], 'dev')
        self.assertTrue(validation['split_safe_for_evaluation'])
        self.assertIn('source_file_sha256', validation)
        self.assertEqual(validation['duplicate_audio_count'], 1)
        self.assertFalse(validation['transcript_conflict_for_audio'])
        self.assertTrue((prepare.ROOT / validation['local_audio_path']).exists())

    def test_mismatched_audio_hash_fails_without_publishing_partial_output(self):
        source_rows = [json.loads(line) for line in self.source_path.read_text().splitlines()]
        source_rows[0]['audio_sha256'] = '0' * 64
        write_jsonl(self.source_path, source_rows)

        with patch.object(prepare, 'decode_flac_to_wav', return_value=test_wav_bytes()):
            with self.assertRaisesRegex(ValueError, 'audio SHA-256 mismatch'):
                prepare.build_manifest(
                    self.source_path, self.text_path, self.parquet_root, self.output_path,
                )
        self.assertFalse(self.output_path.exists())

    def test_existing_output_is_never_overwritten(self):
        self.output_path.mkdir()
        marker = self.output_path / 'keep.txt'
        marker.write_text('keep')
        with self.assertRaisesRegex(FileExistsError, 'refusing to overwrite'):
            prepare.build_manifest(self.source_path, self.text_path, self.parquet_root, self.output_path)
        self.assertEqual(marker.read_text(), 'keep')

    @unittest.skipUnless(shutil.which('ffmpeg'), 'ffmpeg CLI is not installed')
    def test_ffmpeg_decoder_writes_valid_mono_16khz_pcm_wav(self):
        flac = test_flac_bytes()
        wav_bytes = prepare.decode_flac_to_wav(flac)
        with wave.open(__import__('io').BytesIO(wav_bytes), 'rb') as stream:
            self.assertEqual((stream.getnchannels(), stream.getsampwidth(), stream.getframerate()), (1, 2, 16000))
            self.assertGreater(stream.getnframes(), 0)


if __name__ == '__main__':
    unittest.main()
