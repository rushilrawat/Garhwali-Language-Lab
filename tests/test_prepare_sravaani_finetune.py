import hashlib
import json
import tarfile
import tempfile
import unittest
import wave
from pathlib import Path

import prepare_sravaani_finetune as m


def write_wav(path, samples=1600):
    with wave.open(str(path), 'wb') as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b'\x00\x00' * samples)


class PrepareSraVaaniFinetuneTests(unittest.TestCase):
    def test_builds_official_manifest_row_from_verified_pcm_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / 'source.wav'
            write_wav(audio)
            digest = hashlib.sha256(audio.read_bytes()).hexdigest()
            row = {
                'audio_sha256': digest,
                'local_audio_path': 'source.wav',
                'asr_target_clean': 'गढ़वाली पाठ',
                'speaker_id': 'speaker-a',
                'license': 'CC-BY-4.0',
            }
            manifest, evidence = m.prepare_row(row, root)
            self.assertEqual(manifest, {
                'audio_filepath': f'{digest}.wav',
                'text': 'गढ़वाली पाठ',
                'duration': 0.1,
            })
            self.assertEqual(evidence['sample_rate_hz'], 16000)
            self.assertEqual(evidence['channels'], 1)
            self.assertEqual(evidence['sample_width_bytes'], 2)

    def test_rejects_audio_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_wav(root / 'source.wav')
            row = {
                'audio_sha256': 'wrong',
                'local_audio_path': 'source.wav',
                'asr_target_clean': 'पाठ',
            }
            with self.assertRaisesRegex(ValueError, 'hash'):
                m.prepare_row(row, root)

    def test_writes_deterministic_tar_members_in_manifest_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for name in ('b', 'a'):
                audio = root / f'{name}.wav'
                write_wav(audio, samples=800 if name == 'a' else 1600)
                rows.append({
                    'audio_sha256': hashlib.sha256(audio.read_bytes()).hexdigest(),
                    'local_audio_path': audio.name,
                    'asr_target_clean': name,
                    'speaker_id': f'speaker-{name}',
                    'license': 'CC-BY-4.0',
                })
            output = root / 'output'
            report = m.write_split('train', rows, output, root)
            manifest_path = output / 'train/shard_0000.json'
            manifest = [json.loads(line) for line in manifest_path.read_text().splitlines()]
            with tarfile.open(output / 'train/shard_0000.tar') as archive:
                members = archive.getmembers()
            self.assertEqual([item['audio_filepath'] for item in manifest], [x.name for x in members])
            self.assertTrue(all(member.mtime == 0 for member in members))
            self.assertEqual(report['records'], 2)
            self.assertEqual(report['identified_speakers'], 2)

    def test_split_audit_rejects_audio_or_speaker_leakage(self):
        split_rows = {
            'train': [{'audio_sha256': 'a', 'speaker_id': 'speaker-a'}],
            'validation': [{'audio_sha256': 'b', 'speaker_id': 'speaker-b'}],
            'test': [{'audio_sha256': 'c', 'speaker_id': 'speaker-c'}],
        }
        self.assertEqual(m.audit_split_leakage(split_rows), {
            'audio_hash_cross_split': 0,
            'identified_speaker_cross_split': 0,
        })
        split_rows['test'][0]['speaker_id'] = 'speaker-a'
        with self.assertRaisesRegex(ValueError, 'speaker'):
            m.audit_split_leakage(split_rows)


if __name__ == '__main__':
    unittest.main()
