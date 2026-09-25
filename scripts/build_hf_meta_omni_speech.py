#!/usr/bin/env python3
"""Add the pinned Meta Omnilingual Garhwali speech subset to the speech release."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVISION = '8648ba8946377697b427ae952076e49fc0e5e44d'
SOURCE = 'facebook/omnilingual-asr-corpus'
SOURCE_URL = 'https://huggingface.co/datasets/facebook/omnilingual-asr-corpus'
LICENSE_URL = 'https://creativecommons.org/licenses/by/4.0/'
SPEECH_REPO = 'rushilrawat/garhwali-speech'
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-speech-2026-09-23'
SOURCE_DATA = ROOT / 'data/downloads/meta_omni_gbm/data/gbm_Deva'
TEXT_MANIFEST = ROOT / 'corpus/meta_omni.jsonl'


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def release_split(source_split: str) -> str:
    return {'dev': 'validation', 'train': 'train', 'test': 'test'}[source_split]


def annotate_audio_duplicates(rows: list[dict]) -> dict[str, dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row['audio_sha256']].append(row)

    annotations = {}
    for group in groups.values():
        duplicate_count = len(group)
        split_overlap = len({row['split'] for row in group}) > 1
        transcript_conflict = len({row['text_sha256'] for row in group}) > 1
        for row in group:
            annotations[row['record_id']] = {
                'duplicate_audio_count': duplicate_count,
                'cross_split_audio_overlap': split_overlap,
                'transcript_conflict_for_audio': transcript_conflict,
                'split_safe_for_training': duplicate_count == 1,
                'split_safe_for_evaluation': duplicate_count == 1,
            }
    return annotations


def make_release_record(row: dict, annotations: dict) -> dict:
    return {
        'record_id': row['record_id'],
        'audio_sha256': row['audio_sha256'],
        'text_sha256': row['text_sha256'],
        'language': 'gbm',
        'script': 'Deva',
        'glottocode': 'garh1243',
        'duration_seconds': row['duration_seconds'],
        'transcript': row['transcript'],
        'transcript_source': SOURCE,
        'transcript_review_status': 'upstream_reference_unadjudicated',
        'quality_status': 'unreviewed',
        'elicitation_prompt': row['elicitation_prompt'],
        'source': SOURCE,
        'source_url': SOURCE_URL,
        'source_revision': REVISION,
        'source_file': row['source_file'],
        'source_file_sha256': row['source_file_sha256'],
        'upstream_row_index': row['upstream_row_index'],
        'source_split': row['source_split'],
        'split': row['split'],
        'source_license': 'CC-BY-4.0',
        'source_license_url': LICENSE_URL,
        **annotations,
    }


def _load_vaani_hashes(path: Path) -> set[str]:
    return {row['audio_sha256'] for row in read_jsonl(path)}


def _load_vaani_text_hashes(data_dir: Path) -> dict[str, set[str]]:
    import pyarrow.parquet as pq

    hashes = {'train': set(), 'evaluation': set()}
    for path in sorted(data_dir.glob('*.parquet')):
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(
            columns=['transcript', 'machine_draft', 'machine_draft_training_eligible', 'split'],
            batch_size=2048,
        ):
            for row in batch.to_pylist():
                bucket = 'train' if row['split'] == 'train' else 'evaluation'
                for field in ('transcript', 'machine_draft'):
                    value = row.get(field)
                    draft_is_eligible = field != 'machine_draft' or row.get('machine_draft_training_eligible') is True
                    if value and draft_is_eligible:
                        normalized = unicodedata.normalize('NFC', value).strip()
                        hashes[bucket].add(hashlib.sha256(normalized.encode('utf-8')).hexdigest())
    return hashes


def annotate_text_overlaps(rows: list[dict], vaani_hashes: dict[str, set[str]]) -> dict[str, dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        groups[row['text_sha256']].append(row)
    flags = {}
    for text_hash, group in groups.items():
        split_overlap = len({row['split'] for row in group}) > 1
        external_train = text_hash in vaani_hashes['train']
        external_evaluation = text_hash in vaani_hashes['evaluation']
        for row in group:
            flags[row['record_id']] = {
                'duplicate_text_count': len(group),
                'cross_split_text_overlap': split_overlap,
                'cross_corpus_text_overlap': external_train or external_evaluation,
                'cross_corpus_train_text_overlap': external_train,
                'cross_corpus_evaluation_text_overlap': external_evaluation,
                'split_safe_for_training': not split_overlap and not external_evaluation,
                'split_safe_for_evaluation': not split_overlap and not external_train,
            }
    return flags


def combine_annotations(audio: dict[str, dict], text: dict[str, dict]) -> dict[str, dict]:
    combined = {}
    for record_id in audio:
        combined[record_id] = {**audio[record_id], **text[record_id]}
        combined[record_id]['split_safe_for_training'] = (
            audio[record_id]['split_safe_for_training'] and text[record_id]['split_safe_for_training']
        )
        combined[record_id]['split_safe_for_evaluation'] = (
            audio[record_id]['split_safe_for_evaluation'] and text[record_id]['split_safe_for_evaluation']
        )
    return combined


def scan_source() -> tuple[list[dict], list[dict], int, dict[str, set[str]]]:
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError('Install requirements-hf-release.txt to inspect Parquet source shards') from exc

    local_text = read_jsonl(TEXT_MANIFEST)
    text_by_index = {(row['split'], row['upstream_row_index']): row for row in local_text}
    if len(text_by_index) != len(local_text):
        raise ValueError('local Meta Omnilingual transcript manifest has duplicate split/index keys')

    speech_output = DEFAULT_OUTPUT
    vaani_audio_hashes = _load_vaani_hashes(speech_output / 'manifest.jsonl')
    vaani_text_hashes = _load_vaani_text_hashes(speech_output / 'data')
    observed = []
    source_files = []
    counts: Counter = Counter()
    seen_record_ids = set()
    total_audio_bytes = 0
    for source_path in sorted(SOURCE_DATA.glob('*.parquet')):
        name = source_path.name
        source_split = name.split('-', 1)[0]
        source_file_hash = file_sha256(source_path)
        source_files.append({
            'path': f'data/gbm_Deva/{name}',
            'bytes': source_path.stat().st_size,
            'sha256': source_file_hash,
        })
        pf = pq.ParquetFile(source_path)
        for batch in pf.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                index = counts[source_split]
                counts[source_split] += 1
                text = unicodedata.normalize('NFC', row['raw_text']).strip()
                transcript_row = text_by_index.get((source_split, index))
                if transcript_row is None:
                    raise ValueError(f'no local transcript for {source_split} row {index}')
                if row['language'] != 'gbm_Deva' or row['iso_639_3'] != 'gbm' or row['glottocode'] != 'garh1243' or row['iso_15924'] != 'Deva':
                    raise ValueError(f'unexpected language metadata in {source_path.name} row {index}')
                if transcript_row['text_normalized'] != text:
                    raise ValueError(f'transcript mismatch in {source_path.name} row {index}')
                if not math.isclose(transcript_row['duration_seconds'], row['duration'], abs_tol=1e-8):
                    raise ValueError(f'duration mismatch in {source_path.name} row {index}')
                audio_bytes = row['audio']['bytes']
                if not audio_bytes:
                    raise ValueError(f'empty audio in {source_path.name} row {index}')
                audio_hash = hashlib.sha256(audio_bytes).hexdigest()
                total_audio_bytes += len(audio_bytes)
                text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
                if transcript_row['text_sha256'] != text_hash:
                    raise ValueError(f'text hash mismatch in local transcript row {index}')
                record_id = transcript_row['record_id']
                if record_id in seen_record_ids:
                    raise ValueError(f'duplicate source record ID: {record_id}')
                seen_record_ids.add(record_id)
                observed.append({
                    'record_id': record_id,
                    'upstream_row_index': index,
                    'audio_sha256': audio_hash,
                    'text_sha256': text_hash,
                    'audio_bytes': len(audio_bytes),
                    'transcript': text,
                    'elicitation_prompt': row['prompt'],
                    'duration_seconds': row['duration'],
                    'source_file': f'data/gbm_Deva/{name}',
                    'source_file_sha256': source_file_hash,
                    'source_split': source_split,
                    'split': release_split(source_split),
                    'cross_corpus_audio_overlap': audio_hash in vaani_audio_hashes,
                })

    if counts != Counter({'train': 2329, 'dev': 298, 'test': 300}):
        raise ValueError(f'unexpected Meta split counts: {dict(counts)}')
    if len(observed) != len(local_text):
        raise ValueError(f'source/transcript row count mismatch: {len(observed)} != {len(local_text)}')
    if len(source_files) != 7:
        raise ValueError(f'expected seven pinned Garhwali Parquet files, found {len(source_files)}')
    return observed, source_files, total_audio_bytes, vaani_text_hashes


def add_cross_corpus_flags(rows: list[dict], annotations: dict[str, dict]) -> None:
    for row in rows:
        overlap = row['cross_corpus_audio_overlap']
        flags = annotations[row['record_id']]
        flags['cross_corpus_audio_overlap'] = overlap
        if overlap:
            flags['split_safe_for_training'] = False
            flags['split_safe_for_evaluation'] = False


def build(output: Path = DEFAULT_OUTPUT) -> dict:
    try:
        from datasets import Audio, Dataset, Features, Value, disable_progress_bars
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError('Install requirements-hf-release.txt to build Parquet audio shards') from exc

    disable_progress_bars()
    records, source_files, audio_bytes, vaani_text_hashes = scan_source()
    audio_annotations = annotate_audio_duplicates(records)
    text_annotations = annotate_text_overlaps(records, vaani_text_hashes)
    annotations = combine_annotations(audio_annotations, text_annotations)
    add_cross_corpus_flags(records, annotations)
    release_by_id = {
        row['record_id']: make_release_record(row, annotations[row['record_id']])
        for row in records
    }
    transcript_by_key = {
        (row['split'], row['upstream_row_index']): row['record_id']
        for row in read_jsonl(TEXT_MANIFEST)
    }

    data_dir = output / 'data' / 'meta_omnilingual'
    if data_dir.exists() and any(data_dir.iterdir()):
        raise FileExistsError(f'refusing to overwrite existing Meta export: {data_dir}')
    data_dir.mkdir(parents=True, exist_ok=True)
    features = Features({
        'record_id': Value('string'),
        'audio': Audio(decode=False),
        'audio_sha256': Value('string'),
        'text_sha256': Value('string'),
        'language': Value('string'),
        'script': Value('string'),
        'glottocode': Value('string'),
        'duration_seconds': Value('float64'),
        'transcript': Value('string'),
        'transcript_source': Value('string'),
        'transcript_review_status': Value('string'),
        'quality_status': Value('string'),
        'elicitation_prompt': Value('string'),
        'source': Value('string'),
        'source_url': Value('string'),
        'source_revision': Value('string'),
        'source_file': Value('string'),
        'source_file_sha256': Value('string'),
        'upstream_row_index': Value('int32'),
        'source_split': Value('string'),
        'split': Value('string'),
        'source_license': Value('string'),
        'source_license_url': Value('string'),
        'duplicate_audio_count': Value('int32'),
        'duplicate_text_count': Value('int32'),
        'cross_split_audio_overlap': Value('bool'),
        'cross_corpus_audio_overlap': Value('bool'),
        'cross_split_text_overlap': Value('bool'),
        'cross_corpus_text_overlap': Value('bool'),
        'cross_corpus_train_text_overlap': Value('bool'),
        'cross_corpus_evaluation_text_overlap': Value('bool'),
        'transcript_conflict_for_audio': Value('bool'),
        'split_safe_for_training': Value('bool'),
        'split_safe_for_evaluation': Value('bool'),
    })
    shard_manifest = []
    source_row_offsets: Counter = Counter()
    emitted_record_ids = set()
    for source_path in sorted(SOURCE_DATA.glob('*.parquet')):
        source_split = source_path.name.split('-', 1)[0]
        source_shard = source_path.name.split('-')[1]
        pf = pq.ParquetFile(source_path)
        output_records = []
        part = 0
        row_index = source_row_offsets[source_split]
        for batch in pf.iter_batches(batch_size=64):
            for row in batch.to_pylist():
                record_id = transcript_by_key[(source_split, row_index)]
                source_record = release_by_id[record_id]
                audio_hash = hashlib.sha256(row['audio']['bytes']).hexdigest()
                if audio_hash != source_record['audio_sha256']:
                    raise ValueError(f'audio/index mismatch for {record_id} at {source_split}:{row_index}')
                if record_id in emitted_record_ids:
                    raise ValueError(f'duplicate output record ID: {record_id}')
                emitted_record_ids.add(record_id)
                output_records.append({
                    **source_record,
                    'audio': {'bytes': row['audio']['bytes'], 'path': None},
                })
                row_index += 1
            # Retain each output shard near the source's size without holding an entire split in memory.
            dataset = Dataset.from_list(output_records, features=features)
            split = release_split(source_split)
            name = f'{split}-{source_shard}-{part:03d}.parquet'
            path = data_dir / name
            dataset.to_parquet(str(path))
            shard_manifest.append({
                'path': f'data/meta_omnilingual/{name}',
                'rows': len(output_records),
                'bytes': path.stat().st_size,
                'sha256': file_sha256(path),
            })
            output_records.clear()
            part += 1
        source_row_offsets[source_split] = row_index

    if len(emitted_record_ids) != len(records):
        raise ValueError(f'output row count mismatch: emitted {len(emitted_record_ids)}, expected {len(records)}')

    split_counts = dict(Counter(row['split'] for row in records))
    duration_hours = sum(row['duration_seconds'] for row in records) / 3600
    total_audio_bytes = audio_bytes
    duplicate_groups = Counter(row['audio_sha256'] for row in records)
    transcript_groups = Counter(row['text_sha256'] for row in records)
    summary = {
        'source': SOURCE,
        'source_revision': REVISION,
        'source_config': 'gbm_Deva',
        'source_license': 'CC-BY-4.0',
        'source_url': SOURCE_URL,
        'source_license_url': LICENSE_URL,
        'source_rows': len(records),
        'unique_audio_hashes': len(duplicate_groups),
        'duplicate_audio_groups': sum(count > 1 for count in duplicate_groups.values()),
        'duplicate_audio_rows': sum(count for count in duplicate_groups.values() if count > 1),
        'cross_split_duplicate_audio_groups': sum(
            len({row['split'] for row in records if row['audio_sha256'] == audio_hash}) > 1
            for audio_hash, count in duplicate_groups.items() if count > 1
        ),
        'transcript_conflict_duplicate_groups': sum(
            len({row['text_sha256'] for row in records if row['audio_sha256'] == audio_hash}) > 1
            for audio_hash, count in duplicate_groups.items() if count > 1
        ),
        'duplicate_transcript_groups': sum(count > 1 for count in transcript_groups.values()),
        'duplicate_transcript_rows': sum(count for count in transcript_groups.values() if count > 1),
        'cross_split_transcript_groups': sum(
            len({row['split'] for row in records if row['text_sha256'] == text_hash}) > 1
            for text_hash, count in transcript_groups.items() if count > 1
        ),
        'cross_corpus_audio_overlap_rows': sum(row['cross_corpus_audio_overlap'] for row in records),
        'cross_corpus_exact_text_overlap_rows': sum(
            annotations[row['record_id']]['cross_corpus_text_overlap'] for row in records
        ),
        'split_safe_for_training_rows': sum(
            annotations[row['record_id']]['split_safe_for_training'] for row in records
        ),
        'split_safe_for_evaluation_rows': sum(
            annotations[row['record_id']]['split_safe_for_evaluation'] for row in records
        ),
        'split_counts': split_counts,
        'duration_hours': round(duration_hours, 6),
        'source_audio_bytes': total_audio_bytes,
        'format': 'Parquet with Hugging Face Audio feature; Snappy compression',
        'source_files': source_files,
        'shards': shard_manifest,
    }
    (output / 'meta_omnilingual-manifest.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    with (output / 'meta_omnilingual-manifest.jsonl').open('w', encoding='utf-8') as handle:
        for record in records:
            handle.write(json.dumps({
                'record_id': record['record_id'],
                'audio_sha256': record['audio_sha256'],
                'text_sha256': record['text_sha256'],
                'split': record['split'],
                'source_split': record['source_split'],
                'source': SOURCE,
                'source_url': SOURCE_URL,
                'source_revision': REVISION,
                'source_license': 'CC-BY-4.0',
                'source_license_url': LICENSE_URL,
                'source_file': record['source_file'],
                'source_file_sha256': record['source_file_sha256'],
                'upstream_row_index': record['upstream_row_index'],
                'duration_seconds': record['duration_seconds'],
                **annotations[record['record_id']],
                'cross_corpus_audio_overlap': record['cross_corpus_audio_overlap'],
            }, ensure_ascii=False) + '\n')

    _update_release_files(output, summary)
    return summary


def _update_release_files(output: Path, meta: dict) -> None:
    manifest_path = output / 'manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['additional_sources'] = [meta]
    manifest['total_source_rows'] = manifest['source_rows'] + meta['source_rows']
    vaani_audio_hashes = _load_vaani_hashes(output / 'manifest.jsonl')
    meta_audio_hashes = {row['audio_sha256'] for row in read_jsonl(output / 'meta_omnilingual-manifest.jsonl')}
    manifest['total_unique_audio_hashes'] = len(vaani_audio_hashes | meta_audio_hashes)
    manifest['total_duration_hours'] = round(manifest['duration_hours'] + meta['duration_hours'], 6)
    manifest['total_audio_bytes'] = manifest['audio_bytes'] + meta['source_audio_bytes']
    manifest['total_audio_gib'] = round(manifest['total_audio_bytes'] / (1024 ** 3), 3)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    card_path = output / 'README.md'
    card = card_path.read_text(encoding='utf-8')
    card = re.sub(
        r'(?s)\n- config_name: meta_omnilingual\n.*?(?=\n- config_name:|\n---\n)',
        '',
        card,
    )
    card = re.sub(
        r'(?s)\n## Additional source: Meta Omnilingual ASR Corpus\n.*\Z',
        '',
        card,
    )
    card = re.sub(
        r'(?m)^- (?:Meta Omnilingual:|Overlap audit:|Meta transcripts are|Combined configs:).*\n',
        '',
        card,
    )
    card = re.sub(r'\n{3,}', '\n\n', card)
    # Keep VAANI first; preserve Meta's source partitions and publish its safety flags.
    config_end = '    path: data/test-*.parquet\n---'
    card = card.replace(
        config_end,
        '    path: data/test-*.parquet\n'
        '- config_name: meta_omnilingual\n'
        '  data_files:\n'
        '  - split: train\n'
        '    path: data/meta_omnilingual/train-*.parquet\n'
        '  - split: validation\n'
        '    path: data/meta_omnilingual/validation-*.parquet\n'
        '  - split: test\n'
        '    path: data/meta_omnilingual/test-*.parquet\n---',
        1,
    )
    if 'config_name: meta_omnilingual' not in card:
        raise ValueError('speech card does not have the expected dataset config block')
    card = card.replace(
        '## Contents\n',
        '## Contents\n\n'
        f"- Meta Omnilingual: {meta['source_rows']:,} additional recordings, "
        f"{meta['duration_hours']:.2f} hours (train {meta['split_counts']['train']:,}, "
        f"validation {meta['split_counts']['validation']:,}, test {meta['split_counts']['test']:,}).\n"
        f"- Overlap audit: {meta['duplicate_audio_rows']} rows in {meta['duplicate_audio_groups']} "
        f"exact-audio groups ({meta['cross_split_duplicate_audio_groups']} cross-split); "
        f"{meta['cross_split_transcript_groups']} exact-transcript groups cross splits. "
        f"Cross-VAANI exact audio/text overlaps: {meta['cross_corpus_audio_overlap_rows']}/"
        f"{meta['cross_corpus_exact_text_overlap_rows']}. All rows remain visible; "
        'split-safety flags mark affected rows. The source train/validation/test '
        f"partitions contain exact repeats; only {meta['split_safe_for_training_rows']:,} "
        f"of {meta['source_rows']:,} rows pass both split-safety checks. For clean use, "
        'filter train with `split_safe_for_training == true` and validation/test with '
        '`split_safe_for_evaluation == true`; this leaves rows in the dataset and '
        'does not delete or quarantine them.\n'
        '- Meta transcripts are upstream references, not native-speaker-adjudicated text.\n',
        1,
    )
    card = card.replace(
        '## Contents\n',
        '## Contents\n\n'
        f"- Combined configs: {manifest['total_source_rows']:,} source rows, "
        f"{manifest['total_unique_audio_hashes']:,} unique audio hashes, "
        f"{manifest['total_duration_hours']:.2f} hours, and about "
        f"{manifest['total_audio_gib']:.2f} GiB of source audio.\n",
        1,
    )
    card = card.replace(
        'Load with `datasets.load_dataset("rushilrawat/garhwali-speech", "garhwali_speech")`.',
        'Load VAANI with `datasets.load_dataset("rushilrawat/garhwali-speech", "garhwali_speech")` '
        'or Meta Omnilingual with `datasets.load_dataset("rushilrawat/garhwali-speech", "meta_omnilingual")`.',
    )
    card += (
        '\n## Additional source: Meta Omnilingual ASR Corpus\n\n'
        f"The `meta_omnilingual` config contains {meta['source_rows']:,} Garhwali recordings "
        f"({meta['duration_hours']:.3f} hours) from `gbm_Deva`, pinned to revision `{REVISION}`. "
        'Its original `dev` split is exposed as `validation`. The source identifies language '
        'as `gbm`, script as Devanagari, and Glottolog code as `garh1243`. The Meta source is '
        'licensed CC BY 4.0; cite the [Omnilingual ASR paper](https://arxiv.org/abs/2511.09690).\n\n'
        'The source transcripts are unadjudicated references, not native-reviewed ground truth. '
        'English elicitation prompts are preserved as a separate field. Exact duplicate audio '
        'rows and exact cross-split transcripts remain present and visible; duplicate counts, '
        'conflicting transcript flags, and split-safety fields make unsafe rows explicit. '
        f"Only {meta['split_safe_for_training_rows']:,} of {meta['source_rows']:,} rows pass "
        'both split-safety checks; filter the train and evaluation partitions using their '
        'respective boolean fields before reporting leakage-sensitive metrics. All records '
        'remain in the dataset. No '
        'speaker, prompt, or segment identifiers are republished.\n'
    )
    card_path.write_text(card, encoding='utf-8')

    attribution_path = output / 'ATTRIBUTION.md'
    attribution = attribution_path.read_text(encoding='utf-8')
    attribution = attribution.split(
        '\nMeta Omnilingual Garhwali audio and transcripts are from ', 1
    )[0].rstrip()
    attribution += (
        '\n\nMeta Omnilingual Garhwali audio and transcripts are from '
        f'[{SOURCE}](https://huggingface.co/datasets/{SOURCE}), config `gbm_Deva`, '
        f'revision `{REVISION}`, under CC BY 4.0. Cite the '
        '[Omnilingual ASR paper](https://arxiv.org/abs/2511.09690). Row-level source, '
        'revision, source shard, and license fields are preserved.\n'
    )
    attribution_path.write_text(attribution, encoding='utf-8')


if __name__ == '__main__':
    print(json.dumps(build(), ensure_ascii=False, indent=2))
