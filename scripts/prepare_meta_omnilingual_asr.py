#!/usr/bin/env python3
"""Reconcile local Meta Omnilingual Parquet rows into safe ASR manifests."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import tempfile
import unicodedata
import wave
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEXT_MANIFEST = ROOT / 'corpus/meta_omni.jsonl'
OUTPUT_SPLITS = {'train': 'train', 'dev': 'validation', 'test': 'test'}


def read_jsonl(path: Path) -> list[dict]:
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def normalized_text(value: str) -> str:
    return unicodedata.normalize('NFC', value).strip()


def decode_flac_to_wav(audio_bytes: bytes, ffmpeg: str = 'ffmpeg') -> bytes:
    """Decode FLAC to a deterministic-layout, mono 16 kHz PCM WAV."""
    if not shutil.which(ffmpeg):
        raise RuntimeError(f'ffmpeg executable not found: {ffmpeg}')
    result = subprocess.run(
        [ffmpeg, '-nostdin', '-v', 'error', '-i', 'pipe:0', '-ac', '1', '-ar', '16000',
         '-f', 's16le', 'pipe:1'],
        input=audio_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if result.returncode != 0:
        detail = result.stderr.decode('utf-8', errors='replace').strip()
        raise ValueError(f'ffmpeg could not decode source FLAC: {detail}')
    pcm = result.stdout
    if not pcm or len(pcm) % 2:
        raise ValueError('ffmpeg returned empty or malformed 16-bit PCM')
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        wav.writeframes(pcm)
    return output.getvalue()


def ffmpeg_version(ffmpeg: str) -> str | None:
    if not shutil.which(ffmpeg):
        return None
    result = subprocess.run(
        [ffmpeg, '-version'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        check=False, text=True, timeout=10,
    )
    return result.stdout.splitlines()[0] if result.stdout else None


def write_jsonl_row(handle, row: dict) -> None:
    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def _key(row: dict) -> tuple[str, int]:
    return str(row.get('source_split', row.get('split'))), int(row['upstream_row_index'])


def _unique_index(rows: list[dict], label: str) -> dict[tuple[str, int], dict]:
    indexed = {}
    for row in rows:
        key = _key(row)
        if key in indexed:
            raise ValueError(f'duplicate {label} split/index key: {key}')
        indexed[key] = row
    return indexed


def _safe_split(row: dict) -> tuple[str, list[str]]:
    source_split = row['source_split']
    if source_split not in OUTPUT_SPLITS:
        raise ValueError(f'unknown source split: {source_split}')
    if source_split == 'train':
        allowed = row.get('split_safe_for_training') is True
        reason = 'split_safe_for_training=false'
    else:
        allowed = row.get('split_safe_for_evaluation') is True
        reason = 'split_safe_for_evaluation=false'
    return OUTPUT_SPLITS[source_split], ([] if allowed else [reason])


def build_manifest(
    source_manifest_path: Path,
    text_manifest_path: Path,
    parquet_root: Path,
    output_dir: Path,
    ffmpeg: str = 'ffmpeg',
) -> dict:
    """Verify every pinned source row, emit the complete audit and safe splits.

    Existing output directories are never replaced. Output is assembled in a
    temporary sibling and atomically renamed only after every check succeeds.
    """
    source_manifest_path = Path(source_manifest_path).resolve()
    text_manifest_path = Path(text_manifest_path).resolve()
    parquet_root = Path(parquet_root).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f'refusing to overwrite existing output: {output_dir}')
    if not parquet_root.is_dir():
        raise FileNotFoundError(f'Parquet directory not found: {parquet_root}')

    source_rows = read_jsonl(source_manifest_path)
    text_rows = read_jsonl(text_manifest_path)
    source_by_key = _unique_index(source_rows, 'source manifest')
    text_by_key = _unique_index(text_rows, 'transcript manifest')
    if set(source_by_key) != set(text_by_key):
        missing_text = sorted(set(source_by_key) - set(text_by_key))[:5]
        missing_source = sorted(set(text_by_key) - set(source_by_key))[:5]
        raise ValueError(f'source/transcript key mismatch; missing text={missing_text}, missing source={missing_source}')
    if not source_rows:
        raise ValueError('source manifest is empty')

    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError('Install pyarrow from requirements-asr.txt to read local Parquet shards') from exc

    parquet_files = sorted(parquet_root.glob('*.parquet'))
    expected_files = {Path(row['source_file']).name for row in source_rows}
    found_files = {path.name for path in parquet_files}
    if not parquet_files or found_files != expected_files:
        raise ValueError(
            f'Parquet shard mismatch; missing={sorted(expected_files - found_files)}, '
            f'unexpected={sorted(found_files - expected_files)}'
        )
    source_hashes = {}
    for parquet_path in parquet_files:
        actual_hash = sha256_file(parquet_path)
        expected_hashes = {
            row['source_file_sha256'] for row in source_rows
            if Path(row['source_file']).name == parquet_path.name
        }
        if expected_hashes != {actual_hash}:
            raise ValueError(f'source Parquet SHA-256 mismatch: {parquet_path.name}')
        source_hashes[parquet_path.name] = actual_hash

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix=f'.{output_dir.name}.tmp-', dir=output_dir.parent))
    split_counts: Counter = Counter()
    excluded_counts: Counter = Counter()
    source_split_counts: Counter = Counter()
    seen_keys = set()
    seen_ids = set()
    audio_hash_to_wav = {}
    source_audio_bytes = 0
    derived_wav_bytes = 0
    next_index: Counter = Counter()

    try:
        audio_dir = scratch / 'audio'
        audio_dir.mkdir()
        final_audio_dir = output_dir / 'audio'
        audit_path = scratch / 'source_audit.jsonl'
        split_handles = {
            split: (scratch / f'{split}.jsonl').open('w', encoding='utf-8')
            for split in ('train', 'validation', 'test')
        }
        try:
            with audit_path.open('w', encoding='utf-8') as audit:
                for parquet_path in parquet_files:
                    filename = parquet_path.name
                    source_split = filename.split('-', 1)[0]
                    if source_split not in OUTPUT_SPLITS:
                        raise ValueError(f'unrecognized Meta Parquet filename: {filename}')
                    parquet = pq.ParquetFile(parquet_path)
                    for batch in parquet.iter_batches(batch_size=128):
                        for row in batch.to_pylist():
                            index = next_index[source_split]
                            next_index[source_split] += 1
                            key = (source_split, index)
                            source = source_by_key.get(key)
                            text = text_by_key.get(key)
                            if source is None or text is None:
                                raise ValueError(f'no source/transcript manifest row for {key}')
                            if key in seen_keys:
                                raise ValueError(f'duplicate Parquet split/index key: {key}')
                            seen_keys.add(key)
                            if source['record_id'] != text['record_id']:
                                raise ValueError(f'record ID mismatch for {key}')
                            if source['source_split'] != source_split or source['split'] != OUTPUT_SPLITS[source_split]:
                                raise ValueError(f'source split metadata mismatch for {key}')
                            if text['split'] != source_split:
                                raise ValueError(f'transcript split metadata mismatch for {key}')
                            if Path(source['source_file']).name != filename:
                                raise ValueError(f'source-file mapping mismatch for {key}')
                            if source['source_file_sha256'] != source_hashes[filename]:
                                raise ValueError(f'source-file hash metadata mismatch for {key}')
                            if source['record_id'] in seen_ids:
                                raise ValueError(f'duplicate source record ID: {source["record_id"]}')
                            seen_ids.add(source['record_id'])

                            if (row.get('language'), row.get('iso_639_3'), row.get('glottocode'), row.get('iso_15924')) != (
                                'gbm_Deva', 'gbm', 'garh1243', 'Deva'
                            ):
                                raise ValueError(f'unexpected Garhwali language metadata for {source["record_id"]}')
                            transcript = normalized_text(row['raw_text'])
                            if transcript != text['text_normalized']:
                                raise ValueError(f'transcript mismatch for {source["record_id"]}')
                            text_hash = sha256_bytes(transcript.encode('utf-8'))
                            if text_hash != text['text_sha256'] or text_hash != source['text_sha256']:
                                raise ValueError(f'transcript SHA-256 mismatch for {source["record_id"]}')
                            duration = float(row['duration'])
                            if not math.isclose(duration, float(source['duration_seconds']), abs_tol=1e-8):
                                raise ValueError(f'duration mismatch for {source["record_id"]}')
                            audio_bytes = row['audio']['bytes']
                            if not audio_bytes:
                                raise ValueError(f'empty source audio for {source["record_id"]}')
                            audio_hash = sha256_bytes(audio_bytes)
                            if audio_hash != source['audio_sha256']:
                                raise ValueError(f'audio SHA-256 mismatch for {source["record_id"]}')
                            source_audio_bytes += len(audio_bytes)

                            target_split, exclusion_reasons = _safe_split(source)
                            audio_path = None
                            derived_hash = None
                            if not exclusion_reasons:
                                wav_name = f'{audio_hash}.wav'
                                wav_path = audio_dir / wav_name
                                if audio_hash not in audio_hash_to_wav:
                                    wav_bytes = decode_flac_to_wav(audio_bytes, ffmpeg=ffmpeg)
                                    wav_path.write_bytes(wav_bytes)
                                    derived_hash = sha256_bytes(wav_bytes)
                                    audio_hash_to_wav[audio_hash] = (wav_name, derived_hash, len(wav_bytes))
                                    derived_wav_bytes += len(wav_bytes)
                                else:
                                    wav_name, derived_hash, _ = audio_hash_to_wav[audio_hash]
                                local_path = os.path.relpath(final_audio_dir / wav_name, ROOT)
                                audio_path = local_path
                                output_row = {
                                    'record_id': source['record_id'],
                                    'audio_sha256': audio_hash,
                                    'derived_audio_sha256': derived_hash,
                                    'local_audio_path': audio_path,
                                    'asr_target_clean': transcript,
                                    'transcript': transcript,
                                    'text_sha256': text_hash,
                                    'source_split': source_split,
                                    'split': target_split,
                                    'duration_seconds': duration,
                                    'speaker_id': text.get('speaker_id'),
                                    'prompt_id': text.get('prompt_id'),
                                    'segment_id': text.get('segment_id'),
                                    'elicitation_prompt': text.get('prompt'),
                                    'source': source['source'],
                                    'source_url': source['source_url'],
                                    'source_revision': source['source_revision'],
                                    'source_file': source['source_file'],
                                    'source_file_sha256': source['source_file_sha256'],
                                    'upstream_row_index': index,
                                    'source_license': source['source_license'],
                                    'source_license_url': source['source_license_url'],
                                    'transcript_review_status': 'upstream_reference_unadjudicated',
                                    'quality_status': 'unreviewed',
                                    'split_safe_for_training': source['split_safe_for_training'],
                                    'split_safe_for_evaluation': source['split_safe_for_evaluation'],
                                    'duplicate_audio_count': source['duplicate_audio_count'],
                                    'duplicate_text_count': source['duplicate_text_count'],
                                    'cross_split_audio_overlap': source['cross_split_audio_overlap'],
                                    'cross_corpus_audio_overlap': source.get('cross_corpus_audio_overlap', False),
                                    'cross_split_text_overlap': source['cross_split_text_overlap'],
                                    'cross_corpus_text_overlap': source.get('cross_corpus_text_overlap', False),
                                    'cross_corpus_train_text_overlap': source.get('cross_corpus_train_text_overlap', False),
                                    'cross_corpus_evaluation_text_overlap': source.get('cross_corpus_evaluation_text_overlap', False),
                                    'transcript_conflict_for_audio': source['transcript_conflict_for_audio'],
                                    'evaluation_status': 'unresolved' if target_split == 'test' else 'development_only',
                                }
                                write_jsonl_row(split_handles[target_split], output_row)
                                split_counts[target_split] += 1
                            else:
                                excluded_counts[target_split] += 1

                            audit_row = {
                                **source,
                                'transcript': transcript,
                                'speaker_id': text.get('speaker_id'),
                                'prompt_id': text.get('prompt_id'),
                                'segment_id': text.get('segment_id'),
                                'elicitation_prompt': text.get('prompt'),
                                'local_audio_path': audio_path,
                                'derived_audio_sha256': derived_hash,
                                'included_in_model_split': not exclusion_reasons,
                                'model_split': target_split,
                                'exclusion_reasons': exclusion_reasons,
                            }
                            write_jsonl_row(audit, audit_row)
                            source_split_counts[source_split] += 1
        finally:
            for handle in split_handles.values():
                handle.close()

        if seen_keys != set(source_by_key) or seen_keys != set(text_by_key):
            missing = sorted(set(source_by_key) - seen_keys)[:5]
            raise ValueError(f'Parquet/source manifest row-count mismatch; missing keys={missing}')
        if sum(source_split_counts.values()) != len(source_rows):
            raise ValueError('reconciled source row count does not match source manifest')

        report = {
            'status': 'complete',
            'source': 'facebook/omnilingual-asr-corpus',
            'source_revision': next(iter({row['source_revision'] for row in source_rows})),
            'source_license': 'CC-BY-4.0',
            'source_rows': len(source_rows),
            'source_rows_by_split': dict(sorted(source_split_counts.items())),
            'safe_rows': {split: split_counts[split] for split in ('train', 'validation', 'test')},
            'excluded_rows': {split: excluded_counts[split] for split in ('train', 'validation', 'test')},
            'audio_files_written': len(audio_hash_to_wav),
            'source_audio_bytes': source_audio_bytes,
            'derived_wav_bytes': derived_wav_bytes,
            'derived_audio_format': 'WAV PCM signed 16-bit, mono, 16000 Hz',
            'ffmpeg_version': ffmpeg_version(ffmpeg),
            'source_manifest_sha256': sha256_file(source_manifest_path),
            'transcript_manifest_sha256': sha256_file(text_manifest_path),
            'output_manifests': {
                split: {
                    'rows': split_counts[split],
                    'sha256': sha256_file(scratch / f'{split}.jsonl'),
                }
                for split in ('train', 'validation', 'test')
            },
            'source_audit_sha256': sha256_file(audit_path),
            'parquet_files': [
                {'path': name, 'sha256': source_hashes[name], 'bytes': (parquet_root / name).stat().st_size}
                for name in sorted(source_hashes)
            ],
            'safety_policy': {
                'train': 'include only split_safe_for_training=true',
                'validation': 'include only split_safe_for_evaluation=true; development only',
                'test': 'include only split_safe_for_evaluation=true; unresolved lineage, do not score',
                'excluded_rows_retained_in': 'source_audit.jsonl',
            },
        }
        (scratch / 'report.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8',
        )
        os.replace(scratch, output_dir)
        return report
    except BaseException:
        shutil.rmtree(scratch, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-manifest', required=True, type=Path)
    parser.add_argument('--text-manifest', type=Path, default=DEFAULT_TEXT_MANIFEST)
    parser.add_argument('--parquet-root', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--ffmpeg', default='ffmpeg')
    args = parser.parse_args()
    result = build_manifest(
        args.source_manifest, args.text_manifest, args.parquet_root, args.output_dir, args.ffmpeg,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
