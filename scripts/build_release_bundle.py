#!/usr/bin/env python3
"""Copy compact generated reports and supporting artifacts into the Git release."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'release/v0.1.0/artifacts'
MAX_BYTES = 10 * 1024 * 1024
REPORT_NAMES = {
    'full_draft_audit.json', 'indicbert_head_adaptation.json',
    'indicbert_lora_adaptation.json', 'indicbert_lora_long.json',
    'indicbert_transfer_test.json', 'indicbertv2_masked_lm.json',
    'manifest.json', 'report.json', 'report.md', 'text_scaling.json',
    'tokenizer_report.json',
}


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def selected_files():
    processed = ROOT / 'data/processed'
    for path in processed.rglob('*'):
        if path.is_file() and path.stat().st_size <= MAX_BYTES and (
            path.name in REPORT_NAMES or path.name.endswith('_report.json')
        ):
            yield path
    for path in (ROOT / 'outputs').rglob('*'):
        if path.is_file() and path.stat().st_size <= MAX_BYTES:
            yield path
    package = ROOT / 'data/huggingface/garhwali-language-lab'
    for name in ('README.md', 'manifest.json'):
        yield package / name


def build(output=OUTPUT):
    output = Path(output)
    if output.exists():
        shutil.rmtree(output)
    entries = []
    for source in sorted(set(selected_files())):
        relative = source.relative_to(ROOT)
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        entries.append({
            'path': relative.as_posix(),
            'bytes': source.stat().st_size,
            'sha256': sha256(source),
        })
    index = {
        'release_id': 'garhwali-language-lab-v0.1.0',
        'files': len(entries),
        'bytes': sum(item['bytes'] for item in entries),
        'artifacts': entries,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.json').write_text(
        json.dumps(index, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return index


if __name__ == '__main__':
    print(json.dumps(build(), indent=2, sort_keys=True))
