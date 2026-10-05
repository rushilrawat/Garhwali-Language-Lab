#!/usr/bin/env python3
"""Create auditable Whisper train/dev views within its audio and label limits."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from run_whisper_comparison import model_weight_sha256, sha256_file


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    with Path(path).open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def filter_rows(rows, tokenizer, max_target_tokens, max_audio_seconds):
    included = []
    excluded = []
    for row in rows:
        target = row.get('asr_target_clean', '')
        token_ids = tokenizer(target)['input_ids']
        token_count = len(token_ids)
        duration = row.get('duration_seconds')
        duration = float(duration) if duration is not None else None
        reasons = []
        if not target.strip():
            reasons.append('empty_transcript')
        if token_count > max_target_tokens:
            reasons.append('target_exceeds_model_token_limit')
        if duration is None:
            reasons.append('missing_duration_metadata')
        elif duration > max_audio_seconds:
            reasons.append('audio_exceeds_model_window')
        if reasons:
            excluded.append({
                'record_id': row.get('record_id'),
                'audio_sha256': row.get('audio_sha256'),
                'split': row.get('split'),
                'duration_seconds': duration,
                'target_tokens': token_count,
                'exclusion_reasons': reasons,
            })
        else:
            included.append(row)
    return included, excluded


def build_views(
    train_manifest,
    validation_manifest,
    output_dir,
    tokenizer,
    max_target_tokens,
    max_audio_seconds,
    model_id,
    model_weight_hash=None,
    tokenizer_hash=None,
):
    train_manifest = Path(train_manifest)
    validation_manifest = Path(validation_manifest)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(f'refusing to overwrite existing output: {output_dir}')
    if not train_manifest.is_file() or not validation_manifest.is_file():
        raise FileNotFoundError('both training and validation manifests must exist')

    train_rows = read_jsonl(train_manifest)
    validation_rows = read_jsonl(validation_manifest)
    if not train_rows or not validation_rows:
        raise ValueError('training and validation manifests must both be non-empty')
    train_included, train_excluded = filter_rows(
        train_rows, tokenizer, max_target_tokens, max_audio_seconds,
    )
    validation_included, validation_excluded = filter_rows(
        validation_rows, tokenizer, max_target_tokens, max_audio_seconds,
    )
    if not train_included or not validation_included:
        raise ValueError('model-compatible training and validation views must both be non-empty')

    excluded = [
        {'view_split': split, **row}
        for split, rows in (
            ('train', train_excluded), ('validation', validation_excluded),
        )
        for row in rows
    ]
    reason_counts = Counter(
        reason for row in excluded for reason in row['exclusion_reasons']
    )
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(
        prefix=f'.{output_dir.name}.tmp-', dir=output_dir.parent,
    ))
    try:
        write_jsonl(scratch / 'train.jsonl', train_included)
        write_jsonl(scratch / 'validation.jsonl', validation_included)
        write_jsonl(scratch / 'exclusions.jsonl', excluded)
        output_manifests = {}
        for name, rows in (
            ('train', train_included), ('validation', validation_included),
        ):
            path = scratch / f'{name}.jsonl'
            output_manifests[name] = {
                'rows': len(rows),
                'sha256': sha256_file(path),
                'audio_hours': round(
                    sum(float(row['duration_seconds']) for row in rows) / 3600, 6,
                ),
            }
        report = {
            'status': 'complete',
            'model': model_id,
            'model_weight_sha256': model_weight_hash,
            'tokenizer_sha256': tokenizer_hash,
            'model_limits': {
                'max_target_tokens': max_target_tokens,
                'max_audio_seconds': max_audio_seconds,
            },
            'input_manifests': {
                'train': {'name': train_manifest.name, 'sha256': sha256_file(train_manifest), 'rows': len(train_rows)},
                'validation': {'name': validation_manifest.name, 'sha256': sha256_file(validation_manifest), 'rows': len(validation_rows)},
            },
            'included_rows': {
                'train': len(train_included),
                'validation': len(validation_included),
            },
            'excluded_rows': {
                'train': len(train_excluded),
                'validation': len(validation_excluded),
            },
            'exclusion_reason_counts': dict(sorted(reason_counts.items())),
            'output_manifests': output_manifests,
            'exclusions_file_sha256': sha256_file(scratch / 'exclusions.jsonl'),
            'source_manifests_modified': False,
            'scope': 'derived Whisper experiment view only; source and safe manifests are unchanged',
        }
        (scratch / 'report.json').write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
            encoding='utf-8',
        )
        os.replace(scratch, output_dir)
        return report
    except BaseException:
        shutil.rmtree(scratch, ignore_errors=True)
        raise


def prepare_from_local_checkpoint(
    train_manifest, validation_manifest, model_path, output_dir,
):
    from transformers import WhisperConfig, WhisperProcessor

    model_path = Path(model_path)
    if not model_path.is_dir():
        raise FileNotFoundError(f'local Whisper checkpoint directory not found: {model_path}')
    config = WhisperConfig.from_pretrained(model_path, local_files_only=True)
    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    tokenizer_path = model_path / 'tokenizer.json'
    return build_views(
        train_manifest,
        validation_manifest,
        output_dir,
        processor.tokenizer,
        int(config.max_target_positions),
        float(processor.feature_extractor.chunk_length),
        str(model_path),
        model_weight_hash=model_weight_sha256(model_path),
        tokenizer_hash=sha256_file(tokenizer_path) if tokenizer_path.is_file() else None,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--train-manifest', required=True, type=Path)
    parser.add_argument('--validation-manifest', required=True, type=Path)
    parser.add_argument('--model', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare_from_local_checkpoint(
        args.train_manifest, args.validation_manifest, args.model, args.output_dir,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
