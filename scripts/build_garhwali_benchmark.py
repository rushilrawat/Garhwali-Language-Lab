#!/usr/bin/env python3
"""Index Garhwali evaluation assets and run a dependency-free text baseline."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARKS = ROOT / 'benchmarks'
TRAIN_TEXT = ROOT / 'data/processed/model_ready/splits/text_recommended/train.jsonl'
EVAL_TEXT = ROOT / 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl'
TRAIN_ASR = ROOT / 'data/processed/model_ready/splits/asr/train.jsonl'
EVAL_ASR = ROOT / 'data/processed/model_ready/splits/evaluation/asr_candidate.jsonl'
QUALITY_CATALOG = ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
OUT = ROOT / 'data/processed/evaluation/garhwali_bench'
TASKS = {
    'flores': ('source', 'target'),
    'crosssum': ('text', 'summary'),
    'xorqa': ('context', 'question', 'answers'),
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def audit_cross_split_text_overlap(rows):
    grouped = {}
    for index, row in enumerate(rows):
        text = normalize(row.get('text_normalized', ''))
        split = str(row.get('split') or '').strip()
        if not text or not split:
            continue
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        grouped.setdefault(text_hash, []).append((split, row.get('record_id') or str(index)))

    overlaps = []
    for text_hash, members in sorted(grouped.items()):
        splits = sorted({split for split, _ in members})
        if len(splits) < 2:
            continue
        overlaps.append({
            'text_sha256': text_hash,
            'splits': splits,
            'record_ids': sorted(record_id for _, record_id in members),
        })
    return {
        'group_count': len(overlaps),
        'row_count': sum(len(group['record_ids']) for group in overlaps),
        'groups': overlaps,
    }


def display_path(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def char_bigram_baseline(train_texts, evaluation_texts):
    vocabulary = {character for text in train_texts for character in normalize(text)}
    pair_counts = Counter()
    context_counts = Counter()
    for text in train_texts:
        sequence = '\0' + normalize(text) + '\0'
        for left, right in zip(sequence, sequence[1:]):
            pair_counts[left, right] += 1
            context_counts[left] += 1

    vocabulary_size = max(1, len(vocabulary) + 2)
    negative_log_likelihood = 0.0
    evaluated_characters = 0
    unknown_characters = 0
    for text in evaluation_texts:
        normalized = normalize(text)
        unknown_characters += sum(character not in vocabulary for character in normalized)
        sequence = '\0' + normalized + '\0'
        for left, right in zip(sequence, sequence[1:]):
            probability = (pair_counts[left, right] + 1) / (
                context_counts[left] + vocabulary_size
            )
            negative_log_likelihood -= math.log(probability)
            evaluated_characters += 1
    denominator = max(1, evaluated_characters)
    return {
        'model': 'add-one-smoothed_character_bigram',
        'train_character_vocabulary': len(vocabulary),
        'evaluated_characters_with_boundaries': evaluated_characters,
        'negative_log_likelihood_per_character': round(negative_log_likelihood / denominator, 6),
        'perplexity': round(math.exp(negative_log_likelihood / denominator), 6),
        'oov_character_rate': round(
            unknown_characters / max(1, sum(len(normalize(text)) for text in evaluation_texts)),
            8,
        ),
    }


def build_benchmark(
    benchmarks_dir=BENCHMARKS,
    train_text_path=TRAIN_TEXT,
    evaluation_text_path=EVAL_TEXT,
    train_asr_path=TRAIN_ASR,
    evaluation_asr_path=EVAL_ASR,
    quality_catalog_path=QUALITY_CATALOG,
    output_dir=OUT,
):
    benchmarks_dir = Path(benchmarks_dir)
    output_dir = Path(output_dir)
    train_text_path = Path(train_text_path)
    evaluation_text_path = Path(evaluation_text_path)
    train_asr_path = Path(train_asr_path)
    evaluation_asr_path = Path(evaluation_asr_path)
    quality_catalog_path = Path(quality_catalog_path) if quality_catalog_path else None

    train_text_rows = read_jsonl(train_text_path)
    evaluation_text_rows = read_jsonl(evaluation_text_path)
    if quality_catalog_path and quality_catalog_path.exists():
        strict_parents = {
            row['text_sha256'] for row in read_jsonl(quality_catalog_path)
            if (row.get('quality_v2') or {}).get('tier') == 'strict_gold_candidate'
            and row.get('language_bucket') == 'garhwali_candidate'
        }
        evaluation_text_rows = [
            row for row in evaluation_text_rows
            if any(
                parent.get('text_sha256') in strict_parents
                for parent in row.get('parents') or []
            )
        ]
    train_asr_rows = read_jsonl(train_asr_path)
    evaluation_asr_rows = read_jsonl(evaluation_asr_path)
    train_texts = {normalize(row.get('text', '')) for row in train_text_rows}
    evaluation_texts = [normalize(row.get('text', '')) for row in evaluation_text_rows]

    task_entries = {}
    external_total = 0
    external_overlap = 0
    for task, required_fields in TASKS.items():
        path = benchmarks_dir / f'indicgenbench_{task}.jsonl'
        rows = read_jsonl(path)
        invalid = sum(
            any(field not in row.get('source_example', {}) for field in required_fields)
            for row in rows
        )
        external_overlap += sum(normalize(row.get('text_normalized', '')) in train_texts for row in rows)
        external_total += len(rows)
        task_entries[task] = {
            'path': display_path(path),
            'records': len(rows),
            'sha256': sha256_file(path),
            'schema_errors': invalid,
            'cross_split_text_overlap': audit_cross_split_text_overlap(rows),
            'usage': 'evaluation_only',
        }

    internal_text_overlap = sum(text in train_texts for text in evaluation_texts)
    train_speakers = {row.get('speaker_id') for row in train_asr_rows if row.get('speaker_id')}
    evaluation_speakers = {row.get('speaker_id') for row in evaluation_asr_rows if row.get('speaker_id')}
    speaker_overlap = len(train_speakers & evaluation_speakers)
    if internal_text_overlap:
        raise ValueError('internal evaluation text overlaps training text')
    if speaker_overlap:
        raise ValueError('ASR evaluation speakers overlap training speakers')

    report = {
        'release_id': 'garhwali-bench-v0.1-experimental',
        'status': 'strict_automated_candidate_pending_native_review',
        'native_reviewed': False,
        'dialect_aware': False,
        'records': {
            'external_total': external_total,
            'text_evaluation': len(evaluation_text_rows),
            'asr_evaluation': len(evaluation_asr_rows),
        },
        'tasks': task_entries,
        'internal_evaluation': {
            'text': {
                'path': display_path(output_dir / 'internal_text.jsonl'),
                'sha256': None,
            },
            'asr': {'path': display_path(evaluation_asr_path), 'sha256': sha256_file(evaluation_asr_path)},
        },
        'training': {
            'text': {
                'path': display_path(train_text_path),
                'records': len(train_text_rows),
                'sha256': sha256_file(train_text_path),
            },
        },
        'leakage': {
            'external_exact_train_text': external_overlap,
            'external_cross_split_primary_text_groups': sum(
                task['cross_split_text_overlap']['group_count']
                for task in task_entries.values()
            ),
            'external_cross_split_primary_text_rows': sum(
                task['cross_split_text_overlap']['row_count']
                for task in task_entries.values()
            ),
            'internal_text_exact_train_text': internal_text_overlap,
            'asr_speaker_overlap': speaker_overlap,
        },
        'baselines': {
            'character_bigram': char_bigram_baseline(
                [row.get('text', '') for row in train_text_rows],
                evaluation_texts,
            ),
        },
        'quality_policy': (
            'Internal text is restricted to automated strict Garhwali candidates. '
            'It remains experimental until native review and dialect annotation.'
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    internal_text_path = output_dir / 'internal_text.jsonl'
    internal_text_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                for row in evaluation_text_rows),
        encoding='utf-8',
    )
    report['internal_evaluation']['text']['sha256'] = sha256_file(internal_text_path)
    split_overlap_lines = []
    for task, details in task_entries.items():
        overlap = details['cross_split_text_overlap']
        if overlap['group_count']:
            split_names = sorted({
                split
                for group in overlap['groups']
                for split in group['splits']
            })
            split_overlap_lines.append(
                f"- {task}: **{overlap['group_count']} groups / {overlap['row_count']} rows** "
                f"across {', '.join(split_names)}"
            )
        else:
            split_overlap_lines.append(f'- {task}: **0 groups / 0 rows**')
    (output_dir / 'manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    baseline = report['baselines']['character_bigram']
    markdown = f"""# GarhwaliBench v0.1 experimental baseline

This checksum-addressed benchmark contains {external_total:,} external task records,
{len(evaluation_text_rows):,} held-out text segments, and {len(evaluation_asr_rows):,}
speaker-safe ASR rows. The internal text is an automated strict candidate set,
not a native-reviewed or dialect-aware gold benchmark.

## Integrity

- Internal text overlaps with training: **{internal_text_overlap}**
- ASR speakers shared with training: **{speaker_overlap}**
- External benchmark texts matching training exactly: **{external_overlap}**

## Exact primary-text repeats across source splits

These counts use each record's normalized `text_normalized` field. Source rows
remain unchanged and evaluation-only; inspect any overlap before using source
train/dev partitions for model fitting or selection.

{chr(10).join(split_overlap_lines)}

## Dependency-free text baseline

Training view: `{display_path(train_text_path)}` ({len(train_text_rows):,} rows;
SHA-256 `{report['training']['text']['sha256']}`).

- Character bigram perplexity: **{baseline['perplexity']}**
- Evaluation character OOV rate: **{baseline['oov_character_rate']}**
- Training character vocabulary: **{baseline['train_character_vocabulary']}**

The bigram result is a reproducible floor for later language-model comparisons.
External exact matches are reported rather than silently removed so benchmark
contamination remains measurable.
"""
    (output_dir / 'report.md').write_text(markdown, encoding='utf-8')
    return report


if __name__ == '__main__':
    print(json.dumps(build_benchmark(), ensure_ascii=False, indent=2, sort_keys=True))
