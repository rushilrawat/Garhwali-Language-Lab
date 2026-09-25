#!/usr/bin/env python3
"""Build a public, transcript-aware VAANI speech dataset for Hugging Face."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-speech-2026-09-23'
TEXT_REPO = 'rushilrawat/garhwali-corpus'
SPEECH_REPO = 'rushilrawat/garhwali-speech'


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def release_split(main: dict | None, transcription: dict | None) -> str:
    """Prefer transcription-part's fixed split over the broad main config's train label."""
    if transcription and transcription.get('split') in {'train', 'validation', 'test'}:
        return transcription['split']
    if main and main.get('split') in {'train', 'validation', 'test'}:
        return main['split']
    return 'train'


def make_release_record(
    *, main: dict | None, transcription: dict | None, draft: dict | None,
    audio_sha256: str, record_id: str,
) -> dict:
    source = transcription or main or {}
    transcript = (transcription or {}).get('transcript')
    transcript = transcript if transcript else None
    main_transcript = (main or {}).get('transcript') or None
    machine_draft = (draft or {}).get('transcript') or None
    return {
        'record_id': record_id,
        'audio_sha256': audio_sha256,
        'language': source.get('language') or 'Garhwali',
        'district': source.get('district'),
        'gender': source.get('gender'),
        'duration_seconds': (main or {}).get('duration_seconds'),
        'transcript': transcript,
        'transcript_source': 'ARTPARK-IISc/Vaani-transcription-part' if transcription else None,
        'transcript_revision': (transcription or {}).get('revision'),
        'transcript_review_status': 'provider_transcript_unadjudicated' if transcription else 'untranscribed',
        'main_dataset_transcript': main_transcript,
        'transcript_conflict': bool(transcript and main_transcript and transcript != main_transcript),
        'machine_draft': machine_draft,
        'machine_draft_model': (draft or {}).get('machine_transcript_model'),
        'machine_draft_model_revision': (draft or {}).get('machine_transcript_model_revision'),
        'machine_draft_review_status': (draft or {}).get('review_status'),
        'machine_draft_quality': (draft or {}).get('machine_transcript_quality'),
        'machine_draft_training_eligible': (draft or {}).get('training_eligible'),
        'source': source.get('source') or 'ARTPARK-IISc/Vaani',
        'source_revision': source.get('revision'),
        'main_source_revision': (main or {}).get('revision'),
        'source_license': source.get('license') or (main or {}).get('license'),
        'split_assignment_source': 'Vaani-transcription-part' if transcription else 'main-untranscribed-train',
        'split': release_split(main, transcription),
    }


def build_records() -> list[tuple[dict, Path]]:
    vaani = ROOT / 'data/vaani'
    main_rows = read_jsonl(vaani / 'garhwali-main-metadata.jsonl')
    transcription_rows = read_jsonl(vaani / 'garhwali-transcriptions.jsonl')
    audio_rows = read_jsonl(vaani / 'audio-local-manifest.jsonl')
    extra_audio_rows = read_jsonl(vaani / 'transcription-only-audio-manifest.jsonl')
    public = ROOT / 'data/huggingface/garhwali-language-lab/data/sravaani_drafts'
    draft_rows = [row for shard in sorted(public.glob('*.jsonl')) for row in read_jsonl(shard)]

    audio_by_source_path = {row['audio_path']: row for row in audio_rows}
    extra_by_source_path = {row['audio_path']: row for row in extra_audio_rows}
    transcription_by_source_path = {row['audio_path']: row for row in transcription_rows}
    draft_by_hash = {row['audio_sha256']: row for row in draft_rows}
    main_paths = {row['audio_path'] for row in main_rows}

    output: list[tuple[dict, Path]] = []
    for main in main_rows:
        source_path = main['audio_path']
        audio_meta = audio_by_source_path[source_path]
        transcription = transcription_by_source_path.get(source_path)
        audio_path = ROOT / audio_meta['local_path']
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        if audio_path.stat().st_size != audio_meta['bytes']:
            raise ValueError(f'audio size changed: {audio_path}')
        record = make_release_record(
            main=main, transcription=transcription,
            draft=draft_by_hash.get(audio_meta['sha256']),
            audio_sha256=audio_meta['sha256'],
            record_id=f"vaani-main-{main['row_idx']:06d}",
        )
        record['duration_seconds'] = audio_meta.get('duration_seconds', record['duration_seconds'])
        output.append((record, audio_path))

    extra_idx = 0
    for transcription in transcription_rows:
        source_path = transcription['audio_path']
        if source_path in main_paths:
            continue
        audio_meta = extra_by_source_path[source_path]
        audio_path = ROOT / audio_meta['local_path']
        if not audio_path.is_file():
            raise FileNotFoundError(audio_path)
        record = make_release_record(
            main=None, transcription=transcription, draft=None,
            audio_sha256=audio_meta['sha256'],
            record_id=f"vaani-transcription-part-{transcription['split']}-{transcription['row_idx']:06d}",
        )
        record['duration_seconds'] = audio_meta['duration_seconds']
        output.append((record, audio_path))
        extra_idx += 1

    if extra_idx != len(extra_audio_rows):
        raise ValueError(f'expected {len(extra_audio_rows)} transcription-only clips, found {extra_idx}')
    if len(output) != len(main_rows) + len(extra_audio_rows):
        raise ValueError('speech package row count does not reconcile with source manifests')
    licenses = {record['source_license'] for record, _ in output}
    if licenses != {'CC-BY-4.0'}:
        raise ValueError(f'unexpected source licenses in public speech package: {licenses}')
    record_ids = [record['record_id'] for record, _ in output]
    if len(set(record_ids)) != len(record_ids):
        raise ValueError('speech package contains duplicate record IDs')
    return output


def write_cards(output: Path, counts: Counter, total_bytes: int) -> None:
    card = f'''---
license: cc-by-4.0
language:
- gbm
tags:
- audio
- speech
- garhwali
task_categories:
- automatic-speech-recognition
configs:
- config_name: garhwali_speech
  data_files:
  - split: train
    path: data/train-*.parquet
  - split: validation
    path: data/validation-*.parquet
  - split: test
    path: data/test-*.parquet
---

# Garhwali Speech

Companion to [Garhwali Corpus](https://huggingface.co/datasets/{TEXT_REPO}). This
repository has separate configs for Project VAANI and Meta Omnilingual speech;
choose one source config at a time because their splits and transcript histories differ.

## Contents

- {counts['source_rows']:,} source audio rows ({total_bytes / (1024**3):.2f} GiB audio).
- {counts['human_transcript']:,} provider-transcribed rows, including the
  provider's train/validation/test splits.
- {counts['machine_draft_rows']:,} rows with SraVaani draft output, of which
  {counts['machine_draft_nonempty']:,} have non-empty text; all are marked as
  unreviewed hypotheses rather than reference transcripts.
- {counts['transcript_conflicts']:,} records retain differing transcript values
  from the two upstream VAANI repositories, with a conflict flag and both
  supplied text values preserved.
- Audio is embedded in Parquet shards; file paths from the upstream dataset and
  reference images are not republished.

## Source and license

Audio and provider transcripts are from
[ARTPARK-IISc/VAANI](https://huggingface.co/datasets/ARTPARK-IISc/Vaani) and
[ARTPARK-IISc/VAANI-transcription-part](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part).
The upstream Hub card marks VAANI CC BY 4.0 and gates access behind acceptance
of its terms and contact-information form. This package preserves attribution,
source revisions, and row-level license metadata. Please cite the VAANI paper
and review upstream access conditions before use. SraVaani hypotheses are
generated by `ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27` and are not human references.

## Splits and privacy

The transcription-part split is authoritative for every labeled audio row,
including the transcription-only files absent from the main repository. The
complete release contains {counts['source_rows']:,} source rows and
{counts['unique_audio_hashes']:,} unique audio hashes, totaling
{counts['duration_hours']:.3f} hours.
The {counts['untranscribed_rows']:,} remaining VAANI rows stay in train without a provider transcript; where
available, machine drafts are separately labeled. We omit exact source filenames,
reference images, speaker IDs, stay-duration, and fine-grained
location fields. District and gender labels are retained as supplied by VAANI.
No Garhwali native-speaker adjudication has been completed; model drafts must not
be treated as validated text.

Load with `datasets.load_dataset("{SPEECH_REPO}", "garhwali_speech")`.
For the text/resource companion, use
`datasets.load_dataset("{TEXT_REPO}")`.
'''
    (output / 'README.md').write_text(card, encoding='utf-8')
    attribution = '''# Attribution

Audio and provider transcripts originate from Project VAANI (IISc/ARTPARK),
released by its source repositories under CC BY 4.0. Cite the VAANI paper listed
on the upstream dataset card and retain the source/revision/license fields in
each row. Machine drafts identify the SraVaani model and revision separately.
'''
    (output / 'ATTRIBUTION.md').write_text(attribution, encoding='utf-8')


def build(output: Path, rows: list[tuple[dict, Path]], batch_size: int = 512) -> dict:
    try:
        from datasets import Audio, Dataset, Features, Value
    except ImportError as exc:
        raise RuntimeError('Install requirements-hf-release.txt to build Parquet audio shards') from exc

    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f'refusing to overwrite non-empty output: {output}')
    output.mkdir(parents=True, exist_ok=True)
    data_dir = output / 'data'
    data_dir.mkdir(exist_ok=True)
    features = Features({
        'record_id': Value('string'),
        'audio': Audio(decode=False),
        'audio_sha256': Value('string'),
        'language': Value('string'),
        'district': Value('string'),
        'gender': Value('string'),
        'duration_seconds': Value('float32'),
        'transcript': Value('string'),
        'transcript_source': Value('string'),
        'transcript_revision': Value('string'),
        'transcript_review_status': Value('string'),
        'main_dataset_transcript': Value('string'),
        'transcript_conflict': Value('bool'),
        'machine_draft': Value('string'),
        'machine_draft_model': Value('string'),
        'machine_draft_model_revision': Value('string'),
        'machine_draft_review_status': Value('string'),
        'machine_draft_quality': Value('string'),
        'machine_draft_training_eligible': Value('bool'),
        'source': Value('string'),
        'source_revision': Value('string'),
        'main_source_revision': Value('string'),
        'source_license': Value('string'),
        'split_assignment_source': Value('string'),
        'split': Value('string'),
    })
    grouped = {name: [] for name in ('train', 'validation', 'test')}
    for record, audio_path in rows:
        grouped[record['split']].append((record, audio_path))

    counts = Counter()
    counts['source_rows'] = len(rows)
    counts['unique_audio_hashes'] = len({record['audio_sha256'] for record, _ in rows})
    counts['duration_hours'] = sum(
        (record.get('duration_seconds') or 0) for record, _ in rows
    ) / 3600
    total_audio_bytes = 0
    shard_manifest = []
    manifest_path = output / 'manifest.jsonl'
    with manifest_path.open('w', encoding='utf-8') as manifest:
        for split in ('train', 'validation', 'test'):
            for start in range(0, len(grouped[split]), batch_size):
                shard_rows = grouped[split][start:start + batch_size]
                shard_name = f"{split}-{start // batch_size:05d}.parquet"
                examples = []
                for row_index, (record, audio_path) in enumerate(shard_rows):
                    raw_audio = audio_path.read_bytes()
                    if hashlib.sha256(raw_audio).hexdigest() != record['audio_sha256']:
                        raise ValueError(f'audio hash mismatch: {record["record_id"]}')
                    total_audio_bytes += len(raw_audio)
                    counts['human_transcript'] += bool(record['transcript'])
                    counts['untranscribed_rows'] += not bool(record['transcript'])
                    counts['machine_draft_rows'] += bool(record['machine_draft_model'])
                    counts['machine_draft_nonempty'] += bool(record['machine_draft'])
                    counts['transcript_conflicts'] += record['transcript_conflict']
                    record = dict(record)
                    record['machine_draft_quality'] = (
                        json.dumps(record['machine_draft_quality'], ensure_ascii=False, sort_keys=True)
                        if record['machine_draft_quality'] is not None else None
                    )
                    examples.append({**record, 'audio': {'path': None, 'bytes': raw_audio}})
                    manifest.write(json.dumps({
                        'record_id': record['record_id'],
                        'audio_sha256': record['audio_sha256'],
                        'split': split,
                        'parquet_shard': f'data/{shard_name}',
                        'row_in_shard': row_index,
                        'source': record['source'],
                        'source_revision': record['source_revision'],
                        'source_license': record['source_license'],
                    }, ensure_ascii=False) + '\n')
                dataset = Dataset.from_list(examples, features=features)
                shard_path = data_dir / shard_name
                dataset.to_parquet(str(shard_path))
                shard_manifest.append({
                    'path': f'data/{shard_name}',
                    'rows': len(shard_rows),
                    'bytes': shard_path.stat().st_size,
                    'sha256': hashlib.sha256(shard_path.read_bytes()).hexdigest(),
                })
    shard_counts = {split: len(items) for split, items in grouped.items()}
    summary = {
        'dataset_id': SPEECH_REPO,
        'created_date': '2026-09-23',
        'source_rows': sum(shard_counts.values()),
        'unique_audio_hashes': counts['unique_audio_hashes'],
        'split_counts': shard_counts,
        'human_transcript_rows': counts['human_transcript'],
        'untranscribed_rows': counts['untranscribed_rows'],
        'machine_draft_rows': counts['machine_draft_rows'],
        'machine_draft_nonempty_transcripts': counts['machine_draft_nonempty'],
        'provider_transcript_conflicts': counts['transcript_conflicts'],
        'duration_hours': round(counts['duration_hours'], 3),
        'audio_bytes': total_audio_bytes,
        'audio_gib': round(total_audio_bytes / (1024 ** 3), 3),
        'format': 'Parquet with Hugging Face Audio feature; Snappy compression',
        'source_audio_rows_retained': True,
        'source_filenames_published': False,
        'reference_images_published': False,
        'shards': shard_manifest,
    }
    write_json(output / 'manifest.json', summary)
    write_cards(output, counts, total_audio_bytes)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--batch-size', type=int, default=512)
    args = parser.parse_args()
    rows = build_records()
    print(json.dumps(build(args.output, rows, args.batch_size), indent=2))


if __name__ == '__main__':
    main()
