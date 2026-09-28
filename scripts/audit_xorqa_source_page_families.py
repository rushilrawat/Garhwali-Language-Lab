#!/usr/bin/env python3
"""Find XORQA source-page title families that span original splits."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from audit_benchmark_overlap_candidates import normalize_text


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
OUTPUT_JSON = Path('data/processed/evaluation/garhwali_bench/xorqa_source_page_families_2026-09-28.json')
OUTPUT_MARKDOWN = Path('data/processed/evaluation/garhwali_bench/xorqa_source_page_families_2026-09-28.md')


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def normalize_page_title(value: object) -> str:
    text = unicodedata.normalize('NFKC', '' if value is None else str(value)).casefold()
    return re.sub(r'\s+', ' ', text).strip()


def source_page_title(row: dict) -> str | None:
    """Return the page-level portion of the upstream title locator, if valid."""
    example = row.get('source_example')
    raw = example.get('title') if isinstance(example, dict) else None
    if not isinstance(raw, str) or not raw.startswith('title:'):
        return None
    if '_parentSection:' not in raw:
        return None
    title = raw[len('title:'):].split('_parentSection:', 1)[0].strip()
    return title or None


def source_page_hashes(row: dict) -> tuple[str, str] | None:
    title = source_page_title(row)
    normalized = normalize_page_title(title)
    if not normalized:
        return None
    title_hash = sha256_text(normalized)
    family_hash = sha256_text(f'source_page_title_sha256:{title_hash}')
    return title_hash, family_hash


def audit_rows(rows: list[dict]) -> dict:
    """Group XORQA records by exact normalized page title, without copying text."""
    groups: dict[str, list[dict]] = defaultdict(list)
    seen_ids: set[str] = set()
    unparsed = 0
    for index, row in enumerate(rows):
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError(f'row {index} is missing record_id')
        if record_id in seen_ids:
            raise ValueError(f'duplicate record_id: {record_id}')
        seen_ids.add(record_id)
        hashes = source_page_hashes(row)
        if hashes is None:
            unparsed += 1
            continue
        title_hash, family_hash = hashes
        example = row.get('source_example') or {}
        context = example.get('context')
        normalized_context = normalize_text(context) if isinstance(context, str) else ''
        groups[family_hash].append({
            'record_id': record_id,
            'split': str(row.get('split') or ''),
            'normalized_source_page_title_sha256': title_hash,
            'source_page_family_sha256': family_hash,
            'normalized_context_sha256': sha256_text(normalized_context) if normalized_context else None,
        })

    cross_split_groups = []
    split_patterns: Counter[str] = Counter()
    for family_hash, members in sorted(groups.items()):
        splits = sorted({member['split'] for member in members if member['split']})
        if len(splits) < 2:
            continue
        context_hashes = {member['normalized_context_sha256'] for member in members
                          if member['normalized_context_sha256']}
        title_hashes = {member['normalized_source_page_title_sha256'] for member in members}
        if len(title_hashes) != 1:
            raise ValueError(f'{family_hash}: members disagree on normalized page title')
        split_patterns['+'.join(splits)] += 1
        cross_split_groups.append({
            'source_page_family_sha256': family_hash,
            'normalized_source_page_title_sha256': next(iter(title_hashes)),
            'split_count': len(splits),
            'splits': splits,
            'record_count': len(members),
            'distinct_contexts': len(context_hashes),
            'members': sorted(members, key=lambda member: (member['split'], member['record_id'])),
        })

    return {
        'schema_version': 'xorqa-source-page-families-v1',
        'normalization': 'source title: NFKC + casefold + whitespace collapse; page segment before _parentSection:',
        'summary': {
            'records': len(rows),
            'source_page_families': len(groups),
            'unparsed_source_page_titles': unparsed,
            'cross_split_page_groups': len(cross_split_groups),
            'cross_split_records': len({
                member['record_id'] for group in cross_split_groups for member in group['members']
            }),
            'cross_split_groups_with_multiple_contexts': sum(
                group['distinct_contexts'] > 1 for group in cross_split_groups
            ),
            'cross_split_groups_by_split_pattern': dict(sorted(split_patterns.items())),
        },
        'source_page_groups': cross_split_groups,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def run(input_path: Path = INPUT, output_json: Path = OUTPUT_JSON,
        output_markdown: Path = OUTPUT_MARKDOWN) -> dict:
    input_path = Path(input_path)
    rows = _read_jsonl(input_path)
    report = audit_rows(rows)
    report['input'] = {
        'path': str(input_path),
        'sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
    }
    output_json = Path(output_json)
    output_markdown = Path(output_markdown)
    report['outputs'] = {'json': str(output_json), 'markdown': str(output_markdown)}
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    summary = report['summary']
    markdown = [
        '# XORQA source-page family audit — 2026-09-28', '',
        'This review groups records by the exact normalized Wikipedia page title encoded in the upstream title locator. It is source-lineage evidence, not proof of answer leakage, model exposure, or semantic equivalence. The JSON contains row IDs and hashes only; no source title, question, answer, or passage text is copied.', '',
        f"- Rows scanned: {summary['records']}",
        f"- Parsed source-page families: {summary['source_page_families']}",
        f"- Unparsed source-page titles: {summary['unparsed_source_page_titles']}",
        f"- Page families crossing original splits: {summary['cross_split_page_groups']}",
        f"- Rows in cross-split page families: {summary['cross_split_records']}",
        f"- Cross-split page families with distinct context passages: {summary['cross_split_groups_with_multiple_contexts']}",
        f"- Split patterns: `{json.dumps(summary['cross_split_groups_by_split_pattern'], sort_keys=True)}`", '',
        f"Input SHA-256: `{report['input']['sha256']}`.", '',
        'These labels support open diagnostics while preventing same-page rows from being presented as independent source-generalization examples. All benchmark rows and original splits remain intact.', '',
    ]
    output_markdown.write_text('\n'.join(markdown), encoding='utf-8')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output-json', type=Path, default=OUTPUT_JSON)
    parser.add_argument('--output-markdown', type=Path, default=OUTPUT_MARKDOWN)
    args = parser.parse_args()
    report = run(args.input, args.output_json, args.output_markdown)
    print(json.dumps({
        'summary': report['summary'],
        'input_sha256': report['input']['sha256'],
        'outputs': report['outputs'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
