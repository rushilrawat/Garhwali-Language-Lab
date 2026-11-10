#!/usr/bin/env python3
"""Freeze a benchmark export directory with a hash manifest, or verify one.

A freeze records, for every data file in the directory, its byte size,
line count and SHA-256, plus a single combined digest over all files. It
contains hashes and counts only, never records, so the freeze file can be
committed to Git and quoted in reports while the data stays local.

    python scripts/freeze_benchmark.py freeze DIR --out FREEZE.json
    python scripts/freeze_benchmark.py verify DIR FREEZE.json
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

from garhwali_lab.hashing import sha256_file
from garhwali_lab.io import read_json, write_json

FREEZE_SCHEMA = 'garhwali-benchmark-freeze/1'
FREEZE_FILENAME = 'FREEZE.json'
DATA_SUFFIXES = {'.jsonl', '.json', '.csv', '.tsv', '.txt', '.parquet'}


def _line_count(path: Path) -> int:
    count = 0
    with path.open('rb') as handle:
        for _ in handle:
            count += 1
    return count


def file_entries(directory: Path) -> list[dict]:
    entries = []
    for path in sorted(directory.rglob('*')):
        if not path.is_file() or path.suffix not in DATA_SUFFIXES or path.name == FREEZE_FILENAME:
            continue
        entries.append({
            'path': path.relative_to(directory).as_posix(),
            'bytes': path.stat().st_size,
            'lines': _line_count(path),
            'sha256': sha256_file(path),
        })
    if not entries:
        raise ValueError(f'no data files found in {directory}')
    return entries


def combined_digest(entries: list[dict]) -> str:
    joined = ''.join(f"{e['sha256']}  {e['path']}\n" for e in sorted(entries, key=lambda e: e['path']))
    return hashlib.sha256(joined.encode('utf-8')).hexdigest()


def build_freeze(directory: Path, *, frozen_at: str | None = None) -> dict:
    directory = Path(directory)
    entries = file_entries(directory)
    freeze = {
        'schema': FREEZE_SCHEMA,
        'frozen_at': frozen_at or datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'directory': directory.name,
        'file_count': len(entries),
        'total_bytes': sum(e['bytes'] for e in entries),
        'combined_sha256': combined_digest(entries),
        'files': entries,
    }
    manifest_path = directory / 'manifest.json'
    if manifest_path.exists():
        manifest = read_json(manifest_path)
        for key in ('benchmark_id', 'schema_version', 'source_release_id', 'total_records', 'status'):
            if key in manifest:
                freeze.setdefault('benchmark', {})[key] = manifest[key]
    return freeze


def verify_freeze(directory: Path, freeze: dict) -> list[str]:
    """Return a list of human-readable differences; empty means it matches."""
    problems = []
    if freeze.get('schema') != FREEZE_SCHEMA:
        problems.append(f"unknown freeze schema {freeze.get('schema')!r}")
    expected = {e['path']: e for e in freeze.get('files', [])}
    actual = {e['path']: e for e in file_entries(Path(directory))}
    for path in sorted(expected.keys() - actual.keys()):
        problems.append(f'missing: {path}')
    for path in sorted(actual.keys() - expected.keys()):
        problems.append(f'unexpected: {path}')
    for path in sorted(expected.keys() & actual.keys()):
        for field in ('sha256', 'bytes', 'lines'):
            if expected[path][field] != actual[path][field]:
                problems.append(f'changed {field}: {path}')
                break
    if not problems and combined_digest(list(actual.values())) != freeze.get('combined_sha256'):
        problems.append('combined digest mismatch')
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    freeze_cmd = sub.add_parser('freeze', help='write a freeze manifest')
    freeze_cmd.add_argument('directory', type=Path)
    freeze_cmd.add_argument('--out', type=Path, help=f'default: DIR/{FREEZE_FILENAME}')
    verify_cmd = sub.add_parser('verify', help='check a directory against a freeze manifest')
    verify_cmd.add_argument('directory', type=Path)
    verify_cmd.add_argument('freeze', type=Path)
    args = parser.parse_args(argv)

    if args.command == 'freeze':
        freeze = build_freeze(args.directory)
        out = args.out or args.directory / FREEZE_FILENAME
        write_json(out, freeze)
        print(f"froze {freeze['file_count']} files ({freeze['total_bytes']:,} bytes) "
              f"combined_sha256={freeze['combined_sha256']} -> {out}")
        return 0

    problems = verify_freeze(args.directory, read_json(args.freeze))
    if problems:
        print('FREEZE MISMATCH', *problems, sep='\n  ')
        return 1
    print('freeze verified')
    return 0


if __name__ == '__main__':
    sys.exit(main())
