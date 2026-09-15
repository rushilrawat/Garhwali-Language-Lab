#!/usr/bin/env python3
"""Package strict Garhwali ASR splits for official SraVaani NeMo fine-tuning."""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import wave
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/splits/asr'
OUTPUT = ROOT / 'data/processed/model_ready/sravaani_finetune'
SPLITS = ('train', 'validation', 'test')
TRAINING_REPOSITORY = 'https://github.com/ARTPARK-Speech-Models/SraVaani'
TRAINING_REVISION = '11026fa0f97386ae05270872d899800151b2a8ef'
CHECKPOINT_URL = (
    'https://drive.usercontent.google.com/download?'
    'id=1v5VaYibAaDSFuWvROsPbCzeG3iM6VbxY&export=download&confirm=t'
)


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_row(row, root=ROOT):
    audio_path = Path(root) / row['local_audio_path']
    if not audio_path.is_file():
        raise FileNotFoundError(f'Missing source audio: {audio_path}')
    actual_hash = sha256_file(audio_path)
    if actual_hash != row['audio_sha256']:
        raise ValueError(f'Audio hash mismatch: {audio_path}')
    text = row['asr_target_clean'].strip()
    if not text:
        raise ValueError(f'Empty ASR target: {row["audio_sha256"]}')
    with wave.open(str(audio_path), 'rb') as handle:
        channels = handle.getnchannels()
        sample_width = handle.getsampwidth()
        sample_rate = handle.getframerate()
        frames = handle.getnframes()
    if (sample_rate, channels, sample_width) != (16000, 1, 2):
        raise ValueError(f'Audio is not 16 kHz mono 16-bit PCM: {audio_path}')
    duration = frames / sample_rate
    return (
        {
            'audio_filepath': f'{actual_hash}.wav',
            'text': text,
            'duration': round(duration, 6),
        },
        {
            'source_path': audio_path,
            'sample_rate_hz': sample_rate,
            'channels': channels,
            'sample_width_bytes': sample_width,
            'frames': frames,
            'duration_seconds': duration,
        },
    )


def deterministic_tar_entry(archive, source_path, archive_name):
    info = tarfile.TarInfo(archive_name)
    info.size = source_path.stat().st_size
    info.mtime = 0
    info.mode = 0o644
    info.uid = 0
    info.gid = 0
    info.uname = ''
    info.gname = ''
    with source_path.open('rb') as handle:
        archive.addfile(info, handle)


def write_split(split, rows, output=OUTPUT, root=ROOT):
    rows = sorted(rows, key=lambda row: row['audio_sha256'])
    hashes = [row['audio_sha256'] for row in rows]
    if len(hashes) != len(set(hashes)):
        raise ValueError(f'Duplicate audio hash in {split} split')
    prepared = [(*prepare_row(row, root), row) for row in rows]
    split_dir = Path(output) / split
    split_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = split_dir / 'shard_0000.json'
    archive_path = split_dir / 'shard_0000.tar'
    manifest_path.write_text(
        ''.join(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True) + '\n'
            for manifest, _, _ in prepared
        ),
        encoding='utf-8',
    )
    with tarfile.open(archive_path, 'w') as archive:
        for manifest, evidence, _ in prepared:
            deterministic_tar_entry(
                archive,
                evidence['source_path'],
                manifest['audio_filepath'],
            )
    speakers = {
        row.get('speaker_id') for _, _, row in prepared if row.get('speaker_id')
    }
    licenses = Counter(row.get('license', 'unknown') for _, _, row in prepared)
    return {
        'records': len(prepared),
        'duration_seconds': round(
            sum(evidence['duration_seconds'] for _, evidence, _ in prepared), 6
        ),
        'identified_speakers': len(speakers),
        'licenses': dict(sorted(licenses.items())),
        'audio_format': 'WAV PCM 16-bit mono 16000 Hz',
        'manifest': str(manifest_path.relative_to(output)),
        'manifest_sha256': sha256_file(manifest_path),
        'archive': str(archive_path.relative_to(output)),
        'archive_sha256': sha256_file(archive_path),
        'archive_bytes': archive_path.stat().st_size,
        'source_audio_hashes_verified': len(prepared),
    }


def audit_split_leakage(split_rows):
    audio_sets = {
        split: {row['audio_sha256'] for row in rows}
        for split, rows in split_rows.items()
    }
    speaker_sets = {
        split: {
            row['speaker_id'] for row in rows
            if row.get('speaker_id')
            and row.get('speaker_metadata', {}).get('status', 'identified') == 'identified'
        }
        for split, rows in split_rows.items()
    }
    audio_overlap = set()
    speaker_overlap = set()
    for index, left in enumerate(SPLITS):
        for right in SPLITS[index + 1:]:
            audio_overlap.update(audio_sets[left] & audio_sets[right])
            speaker_overlap.update(speaker_sets[left] & speaker_sets[right])
    if audio_overlap:
        raise ValueError('SraVaani fine-tuning splits leak audio hashes')
    if speaker_overlap:
        raise ValueError('SraVaani fine-tuning splits leak identified speakers')
    return {
        'audio_hash_cross_split': 0,
        'identified_speaker_cross_split': 0,
    }


def run(input_dir=INPUT, output=OUTPUT, root=ROOT):
    input_dir = Path(input_dir)
    output = Path(output)
    split_rows = {
        split: read_jsonl(input_dir / f'{split}.jsonl') for split in SPLITS
    }
    leakage = audit_split_leakage(split_rows)
    reports = {
        split: write_split(split, split_rows[split], output, root)
        for split in SPLITS
    }
    report = {
        'run_id': 'garhwali-sravaani-nemo-finetune-package-v0.1',
        'model_id': 'ARTPARK-IISc/SraVaani-1.0',
        'training_repository': TRAINING_REPOSITORY,
        'training_repository_revision': TRAINING_REVISION,
        'source_split_manifests': {
            split: {
                'path': str((input_dir / f'{split}.jsonl').relative_to(root)),
                'sha256': sha256_file(input_dir / f'{split}.jsonl'),
            }
            for split in SPLITS
        },
        'splits': reports,
        'leakage': leakage,
        'source_audio_unchanged': True,
        'test_split_held_out_from_training': True,
        'package_status': 'ready_for_nemo_cuda_training',
        'external_requirements': {
            'checkpoint': 'SraVaani-nemo-checkpoint.nemo (~1.7 GB)',
            'checkpoint_in_huggingface_inference_repo': False,
            'checkpoint_source': CHECKPOINT_URL,
            'checkpoint_access': 'official_direct_download_verified_2026-09-15',
            'runtime': 'NVIDIA NeMo ASR with matching CUDA extra',
            'hardware': 'CUDA-capable NVIDIA GPU; 16 GB VRAM recommended',
        },
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
