#!/usr/bin/env python3
"""Build a rights-cleared, high-confidence text view without altering full splits."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_huggingface_dataset import recommended_text_training_row, text_row


ROOT = Path(__file__).resolve().parents[1]
SPLIT_ROOT = ROOT / 'data/processed/model_ready/splits/text'
QUALITY_PATH = ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/splits/text_recommended'
SPLITS = ('train', 'validation', 'test')


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
        for row in rows
    )
    path.write_text(payload, encoding='utf-8')
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def build_view(split_paths=None, quality_path=QUALITY_PATH, output_dir=OUTPUT):
    split_paths = split_paths or {
        split: SPLIT_ROOT / f'{split}.jsonl' for split in SPLITS
    }
    quality_rows = read_jsonl(quality_path)
    parent_quality = {row['text_sha256']: row for row in quality_rows}
    if len(parent_quality) != len(quality_rows):
        raise ValueError('quality catalog contains duplicate parent text hashes')

    output_dir = Path(output_dir)
    artifacts = {}
    counts = {}
    for split in SPLITS:
        source_path = Path(split_paths[split])
        source_rows = read_jsonl(source_path)
        exported = [text_row(row, parent_quality) for row in source_rows]
        selected = [row for row in exported if recommended_text_training_row(row)]
        if any(row.get('split') != split for row in selected):
            raise ValueError(f'{split} view contains a row assigned to another split')
        counts[split] = {
            'source_records': len(source_rows),
            'recommended_records': len(selected),
            'excluded_records': len(source_rows) - len(selected),
        }
        relative = f'{split}.jsonl'
        destination = output_dir / relative
        artifacts[relative] = {
            'records': len(selected),
            'sha256': write_jsonl(destination, selected),
        }

    report = {
        'run_id': 'garhwali-recommended-text-view-v0.1',
        'policy': (
            'Keep only Garhwali-only source labels, strict automated quality '
            'candidates, no active quality flags, and compatible public rights. '
            'Native review is still pending; this is not a gold corpus.'
        ),
        'source_hashes': {
            split: sha256_file(path) for split, path in split_paths.items()
        },
        'quality_catalog_sha256': sha256_file(quality_path),
        'counts': counts,
        'artifacts': artifacts,
        'records_removed_from_full_corpus': 0,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(build_view(), ensure_ascii=False, indent=2, sort_keys=True))
