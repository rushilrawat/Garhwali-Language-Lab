#!/usr/bin/env python3
"""Audit exact overlaps in nested benchmark task fields without copying text."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_JSON = Path('data/processed/evaluation/garhwali_bench/nested_overlap_candidates_2026-09-27_v2.json')
INPUTS = {
    'recommended_train': 'data/processed/model_ready/splits/text_recommended/train.jsonl',
    'flores': 'benchmarks/indicgenbench_flores.jsonl',
    'crosssum': 'benchmarks/indicgenbench_crosssum.jsonl',
    'xorqa': 'benchmarks/indicgenbench_xorqa.jsonl',
}
FIELD_SPECS = {
    'flores': (
        ('source_example.source', 'gbm'),
        ('source_example.target', 'en'),
    ),
    'crosssum': (
        ('source_example.text', 'en'),
        ('source_example.summary', 'gbm'),
    ),
    'xorqa': (
        ('source_example.context', 'en'),
        ('source_example.question', 'gbm'),
        ('source_example.oracle_question', 'en'),
        ('source_example.answers[*].text', 'en'),
        ('source_example.translated_answers[*].text', 'gbm'),
    ),
}


def normalize_text(value: object) -> str:
    text = unicodedata.normalize('NFKC', '' if value is None else str(value)).casefold()
    return ' '.join(
        ''.join(
            char if unicodedata.category(char)[0] in {'L', 'M', 'N'} else ' '
            for char in text
        ).split()
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _read_field(example: dict, field_path: str) -> list[str]:
    field = field_path.removeprefix('source_example.')
    if '[*].' in field:
        container, leaf = field.split('[*].', 1)
        values = example.get(container)
        if not isinstance(values, list):
            return []
        return [str(item[leaf]) for item in values
                if isinstance(item, dict) and isinstance(item.get(leaf), str)]
    value = example.get(field)
    return [value] if isinstance(value, str) else []


def _train_text(row: dict) -> str:
    for field in ('text', 'text_normalized', 'text_original'):
        if isinstance(row.get(field), str) and row[field].strip():
            return row[field]
    return ''


def _flatten_fields(datasets: dict[str, list[dict]]) -> list[dict]:
    fields = []
    for view, rows in sorted(datasets.items()):
        if view not in FIELD_SPECS:
            raise ValueError(f'no nested field mapping is defined for view: {view}')
        for row_index, row in enumerate(rows):
            example = row.get('source_example')
            if not isinstance(example, dict):
                continue
            split = str(row.get('split') or example.get('split') or 'unspecified')
            record_id = str(row.get('record_id') or f'{view}:row:{row_index:08d}')
            for field_path, language in FIELD_SPECS[view]:
                for value_index, raw_text in enumerate(_read_field(example, field_path)):
                    normalized = normalize_text(raw_text)
                    if not normalized:
                        continue
                    fields.append({
                        'view': view,
                        'split': split,
                        'record_id': record_id,
                        'field_path': field_path,
                        'value_index': value_index,
                        'language': language,
                        'normalized_text_sha256': _sha256(normalized),
                        'normalized_characters': len(normalized),
                        'normalized_tokens': len(normalized.split()),
                    })
    return fields


def audit_rows(
    recommended_train: list[dict],
    datasets: dict[str, list[dict]],
    *,
    min_chars: int = 20,
) -> dict:
    if min_chars < 1:
        raise ValueError('min_chars must be positive')
    training_by_hash: dict[str, set[str]] = defaultdict(set)
    for index, row in enumerate(recommended_train):
        normalized = normalize_text(_train_text(row))
        if normalized:
            training_by_hash[_sha256(normalized)].add(
                str(row.get('record_id') or f'recommended_train:{index:08d}')
            )

    fields = _flatten_fields(datasets)
    training_groups: dict[tuple[str, str, str], dict] = {}
    short_training_groups: dict[tuple[str, str, str], dict] = {}
    short_exact_match_count = 0
    long_exact_occurrences = 0
    for field in fields:
        normalized_hash = field['normalized_text_sha256']
        matching_training_ids = training_by_hash.get(normalized_hash, set())
        if not matching_training_ids:
            continue
        if field['normalized_characters'] < min_chars:
            short_exact_match_count += 1
            group_key = (field['view'], field['field_path'], normalized_hash)
            group = short_training_groups.setdefault(group_key, {
                'view': field['view'],
                'field_path': field['field_path'],
                'language': field['language'],
                'normalized_text_sha256': normalized_hash,
                'normalized_characters': field['normalized_characters'],
                'nested_members': [],
                'matched_training_record_ids': set(),
            })
            group['nested_members'].append({
                'record_id': field['record_id'],
                'split': field['split'],
                'value_index': field['value_index'],
            })
            group['matched_training_record_ids'].update(matching_training_ids)
            continue
        long_exact_occurrences += 1
        group_key = (field['view'], field['field_path'], normalized_hash)
        group = training_groups.setdefault(group_key, {
            'view': field['view'],
            'field_path': field['field_path'],
            'language': field['language'],
            'normalized_text_sha256': normalized_hash,
            'normalized_characters': field['normalized_characters'],
            'nested_members': [],
            'matched_training_record_ids': set(),
        })
        group['nested_members'].append({
            'record_id': field['record_id'],
            'split': field['split'],
            'value_index': field['value_index'],
        })
        group['matched_training_record_ids'].update(matching_training_ids)

    split_groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    cross_field_candidates: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for field in fields:
        if field['normalized_characters'] >= min_chars:
            split_groups[(
                field['language'], field['field_path'], field['normalized_text_sha256'],
            )].append(field)
            cross_field_candidates[(
                field['language'], field['normalized_text_sha256'],
            )].append(field)
    cross_split_groups = []
    for (language, field_path, normalized_hash), members in sorted(split_groups.items()):
        splits = sorted({field['split'] for field in members})
        if len(splits) < 2:
            continue
        cross_split_groups.append({
            'language': language,
            'field_path': field_path,
            'normalized_text_sha256': normalized_hash,
            'splits': splits,
            'members': [
                {
                    'view': field['view'],
                    'record_id': field['record_id'],
                    'field_path': field['field_path'],
                    'split': field['split'],
                    'value_index': field['value_index'],
                }
                for field in sorted(
                    members,
                    key=lambda item: (
                        item['view'], item['split'], item['record_id'],
                        item['field_path'], item['value_index'],
                    ),
                )
            ],
        })
    cross_field_groups = []
    for (language, normalized_hash), members in sorted(cross_field_candidates.items()):
        splits = sorted({field['split'] for field in members})
        field_paths = sorted({field['field_path'] for field in members})
        if len(splits) < 2 or len(field_paths) < 2:
            continue
        cross_field_groups.append({
            'language': language,
            'normalized_text_sha256': normalized_hash,
            'splits': splits,
            'field_paths': field_paths,
            'members': [
                {
                    'view': field['view'],
                    'record_id': field['record_id'],
                    'field_path': field['field_path'],
                    'split': field['split'],
                    'value_index': field['value_index'],
                }
                for field in sorted(
                    members,
                    key=lambda item: (
                        item['view'], item['split'], item['record_id'],
                        item['field_path'], item['value_index'],
                    ),
                )
            ],
        })

    language_label_groups: dict[str, list[dict]] = defaultdict(list)
    for field in fields:
        language_label_groups[field['normalized_text_sha256']].append(field)
    cross_language_label_groups = []
    for normalized_hash, members in sorted(language_label_groups.items()):
        languages = sorted({field['language'] for field in members})
        if len(languages) < 2:
            continue
        splits = sorted({field['split'] for field in members})
        field_paths = sorted({field['field_path'] for field in members})
        cross_language_label_groups.append({
            'normalized_text_sha256': normalized_hash,
            'normalized_characters': members[0]['normalized_characters'],
            'languages': languages,
            'splits': splits,
            'field_paths': field_paths,
            'members': [
                {
                    'view': field['view'],
                    'record_id': field['record_id'],
                    'field_path': field['field_path'],
                    'split': field['split'],
                    'language': field['language'],
                    'value_index': field['value_index'],
                }
                for field in sorted(
                    members,
                    key=lambda item: (
                        item['view'], item['split'], item['record_id'],
                        item['field_path'], item['language'], item['value_index'],
                    ),
                )
            ],
        })

    long_matches = []
    for group in training_groups.values():
        group['nested_members'].sort(
            key=lambda item: (item['split'], item['record_id'], item['value_index'])
        )
        group['matched_training_record_ids'] = sorted(group['matched_training_record_ids'])
        long_matches.append(group)
    long_matches.sort(key=lambda item: (
        item['view'], item['field_path'], item['normalized_text_sha256'],
    ))
    short_matches = []
    for group in short_training_groups.values():
        group['nested_members'].sort(
            key=lambda item: (item['split'], item['record_id'], item['value_index'])
        )
        group['matched_training_record_ids'] = sorted(group['matched_training_record_ids'])
        short_matches.append(group)
    short_matches.sort(key=lambda item: (
        item['view'], item['field_path'], item['normalized_text_sha256'],
    ))
    dataset_counts = {
        view: len(rows) for view, rows in sorted(datasets.items())
    }
    return {
        'schema_version': 1,
        'audit': 'nested_benchmark_exact_overlap_candidates_v1',
        'normalizer': 'NFKC-casefold-retain-letters-marks-numbers-v1',
        'minimum_characters_for_long_candidate': min_chars,
        'source_rows_removed': 0,
        'recommended_train_rows': len(recommended_train),
        'nested_benchmark_rows': dataset_counts,
        'nested_text_field_count': len(fields),
        'training_overlap': {
            'long_match_group_count': len(long_matches),
            'long_exact_occurrence_count': long_exact_occurrences,
            'short_exact_match_count': short_exact_match_count,
            'long_match_groups': long_matches,
            'short_match_groups': short_matches,
        },
        'cross_split': {
            'group_count': len(cross_split_groups),
            'groups': cross_split_groups,
        },
        'cross_field': {
            'group_count': len(cross_field_groups),
            'groups': cross_field_groups,
        },
        'cross_language_label_exact': {
            'group_count': len(cross_language_label_groups),
            'short_group_count': sum(
                group['normalized_characters'] < min_chars
                for group in cross_language_label_groups
            ),
            'long_group_count': sum(
                group['normalized_characters'] >= min_chars
                for group in cross_language_label_groups
            ),
            'cross_split_group_count': sum(
                len(group['splits']) > 1 for group in cross_language_label_groups
            ),
            'cross_field_group_count': sum(
                len(group['field_paths']) > 1 for group in cross_language_label_groups
            ),
            'groups': cross_language_label_groups,
        },
        'limitations': [
            'This is an exact normalized-text scan of nested fields, not semantic or paraphrase detection.',
            'Field language labels describe the task schema and do not verify each text span linguistically.',
            'Cross-language-label exact matches may be short named entities, numerals, or common answer strings; they are candidates, not confirmed translations or leakage.',
            'Short exact matches are counted separately because common short answers can match by chance.',
            'A candidate does not prove leakage or justify deleting a record; inspect its source and task context.',
            'A negative result means only that this configured exact scan found no candidate links.',
            'No source rows are removed or rewritten by this audit.',
        ],
    }


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{line_number}: expected a JSON object')
            rows.append(row)
    return rows


def build_project_report(project_root: str | Path, *, min_chars: int = 20) -> dict:
    root = Path(project_root).resolve()
    input_manifests = {}
    loaded = {}
    for name, relative in INPUTS.items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f'required nested-overlap input is missing: {relative}')
        data = path.read_bytes()
        rows = _read_jsonl(path)
        input_manifests[name] = {
            'path': relative,
            'records': len(rows),
            'sha256': hashlib.sha256(data).hexdigest(),
        }
        loaded[name] = rows
    report = audit_rows(
        loaded.pop('recommended_train'), loaded, min_chars=min_chars,
    )
    report['input_manifests'] = input_manifests
    return report


def render_markdown(report: dict) -> str:
    lines = [
        '# Nested benchmark overlap candidates',
        '',
        'This report lists exact normalized matches in nested task fields. It is a candidate audit only: it does not prove leakage, make language judgments, or remove records.',
        '',
        '## Results',
        '',
        f"- Nested text fields scanned: {report['nested_text_field_count']:,}",
        f"- Long exact matches to recommended training: {report['training_overlap']['long_match_group_count']:,} content groups / {report['training_overlap']['long_exact_occurrence_count']:,} field occurrences",
        f"- Short exact matches to recommended training: {report['training_overlap']['short_exact_match_count']:,}",
        f"- Exact nested content groups crossing source splits: {report['cross_split']['group_count']:,}",
        f"- Exact content copied across different fields/splits (separate candidates): {report['cross_field']['group_count']:,}",
        f"- Exact strings under multiple task-language labels: {report['cross_language_label_exact']['group_count']:,} ({report['cross_language_label_exact']['short_group_count']:,} short; {report['cross_language_label_exact']['cross_split_group_count']:,} cross-split)",
        '- Source rows removed: 0',
        '',
        '## Limits',
        '',
    ]
    lines.extend(f"- {limitation}" for limitation in report['limitations'])
    lines.extend([
        '',
        'The companion JSON contains IDs, field paths, splits, and normalized-text hashes only; it does not copy source text.',
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=ROOT)
    parser.add_argument('--output-json', type=Path, default=ROOT / OUTPUT_JSON)
    parser.add_argument('--output-markdown', type=Path)
    parser.add_argument('--min-chars', type=int, default=20)
    args = parser.parse_args()
    report = build_project_report(args.project_root, min_chars=args.min_chars)
    report_json = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    markdown_path = args.output_markdown or args.output_json.with_suffix('.md')
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(report_json, encoding='utf-8')
    markdown_path.write_text(render_markdown(report), encoding='utf-8')
    print(json.dumps({
        'json': str(args.output_json),
        'markdown': str(markdown_path),
        'nested_fields': report['nested_text_field_count'],
        'training_overlap_groups': report['training_overlap']['long_match_group_count'],
        'cross_split_groups': report['cross_split']['group_count'],
        'cross_field_groups': report['cross_field']['group_count'],
        'cross_language_label_groups': report['cross_language_label_exact']['group_count'],
        'cross_language_label_cross_split_groups': report['cross_language_label_exact']['cross_split_group_count'],
        'source_rows_removed': report['source_rows_removed'],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
