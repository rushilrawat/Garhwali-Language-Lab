#!/usr/bin/env python3
"""Audit the five v0.2 Garhwali-only source expansion workstreams."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'lsi_dialect_table': ROOT / 'data/extracted/historical/lsi_1916_garhwali_dialect_table.jsonl',
    'lsi_dialect_specimens': ROOT / 'data/extracted/historical/lsi_1916_garhwali_specimens.jsonl',
    'upreti_1894_proverbs': ROOT / 'data/extracted/folklore/upreti_1894_garhwali_proverbs.jsonl',
    'door43_obs_tlf': ROOT / 'data/extracted/obs_tlf_v1/records.jsonl',
}
INPUT_DIRS = ('corpus', 'restricted', 'experimental', 'extracted', 'data/extracted')
REPORT = ROOT / 'data/extracted/expansion_audit/v0.2.0.json'


def normalize(value: str) -> str:
    return ' '.join(value.split())


def row_text(row: dict) -> str:
    for key in ('text_normalized', 'text', 'transcript'):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return normalize(value)
    return ''


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def load_hashes(paths: list[Path]) -> set[str]:
    hashes = set()
    for path in paths:
        if not path.is_file():
            continue
        with path.open(encoding='utf-8', errors='replace') as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                text = row_text(row)
                if text:
                    hashes.add(digest_text(text))
    return hashes


def audit(sources: dict[str, Path], existing_paths: list[Path]) -> dict:
    missing = [name for name, path in sources.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f'missing expansion outputs: {missing}')

    new_hashes: set[str] = set()
    source_hashes: dict[str, set[str]] = {}
    source_reports = {}
    licenses = Counter()
    invalid_language_rows = []
    rows_seen = 0
    characters = 0
    for name, path in sources.items():
        rows = []
        with path.open(encoding='utf-8') as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                row = json.loads(line)
                text = row_text(row)
                if not text:
                    continue
                digest = digest_text(text)
                rows.append((row, text, digest))
                new_hashes.add(digest)
                licenses[str(row.get('license_id') or 'not_recorded')] += 1
                if row.get('iso_639_3') != 'gbm' or row.get('language') != 'Garhwali':
                    invalid_language_rows.append({
                        'source': name, 'line': line_number,
                        'iso_639_3': row.get('iso_639_3'),
                        'language': row.get('language'),
                    })
        hashes = {digest for _, _, digest in rows}
        source_hashes[name] = hashes
        try:
            display_path = path.relative_to(ROOT).as_posix()
        except ValueError:
            display_path = str(path)
        source_reports[name] = {
            'path': display_path,
            'records_with_text': len(rows),
            'unique_texts': len(hashes),
            'characters_including_duplicates': sum(len(text) for _, text, _ in rows),
            'rights_status_counts': dict(Counter(
                str(row.get('rights_status') or 'not_recorded') for row, _, _ in rows
            )),
            'quality_status_counts': dict(Counter(
                str(row.get('quality_status') or 'not_recorded') for row, _, _ in rows
            )),
        }
        rows_seen += len(rows)
        characters += sum(len(text) for _, text, _ in rows)

    existing_hashes = load_hashes([path for path in existing_paths if path not in sources.values()])
    cross_source_duplicates = sum(
        len(source_hashes[left] & source_hashes[right])
        for index, left in enumerate(source_hashes)
        for right in list(source_hashes)[index + 1:]
    )
    return {
        'audit_version': 'garhwali_expansion_v1',
        'source_rows_with_text': rows_seen,
        'source_characters_including_duplicates': characters,
        'new_exact_unique_texts': len(new_hashes),
        'new_exact_unique_not_in_prior_layers': len(new_hashes - existing_hashes),
        'new_texts_already_in_prior_layers': len(new_hashes & existing_hashes),
        'cross_source_duplicate_pairs': cross_source_duplicates,
        'invalid_garhwali_only_rows': invalid_language_rows,
        'license_record_counts': dict(sorted(licenses.items())),
        'workstreams': source_reports,
    }


def main() -> None:
    existing = []
    for dirname in INPUT_DIRS:
        folder = ROOT / dirname
        if folder.exists():
            existing.extend(folder.rglob('*.jsonl'))
    report = audit(SOURCES, sorted(set(existing)))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
