#!/usr/bin/env python3
"""Assign conservative use labels to exact XORQA source-context overlaps."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from audit_benchmark_overlap_candidates import normalize_text


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _context_family_hash(context: object) -> tuple[str, str]:
    normalized = normalize_text(context)
    if len(normalized) < 20:
        raise ValueError('source context is missing or shorter than 20 normalized characters')
    context_hash = _sha256(normalized)
    family_hash = _sha256(f'source_content_sha256:{context_hash}')
    return context_hash, family_hash


def build_usage_labels(candidate_report: dict, benchmark_records: list[dict]) -> dict:
    """Verify and label exact XORQA context reuse without changing source rows."""
    rows_by_id: dict[str, dict] = {}
    for row in benchmark_records:
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError('benchmark record is missing record_id')
        if record_id in rows_by_id:
            raise ValueError(f'duplicate record_id in benchmark input: {record_id}')
        rows_by_id[record_id] = row

    labels_by_id: dict[str, dict] = {}
    split_patterns: Counter[str] = Counter()
    exact_question_patterns: Counter[str] = Counter()

    def add_label(
        record_id: str,
        row: dict,
        split: str,
        evidence_type: str,
        *,
        group_hash: str,
        content_hash: str,
    ) -> None:
        label = labels_by_id.get(record_id)
        if label is None:
            label = {
                'record_id': record_id,
                'benchmark': 'IndicGenBench_XORQA_Garhwali',
                'original_split': split,
                'original_usage': str(row.get('usage') or ''),
                'original_training_eligible': bool(row.get('training_eligible', False)),
                'source_family_sha256': None,
                'normalized_context_sha256': None,
                'normalized_question_sha256': None,
                'evidence_types': [],
                'usage_label': 'open_diagnostic_only_split_overlap',
                'independent_source_generalization_eligible': False,
                'open_diagnostic_eligible': True,
                'record_retained': True,
                'reason_code': 'exact_question_or_context_reused_across_original_splits',
            }
            labels_by_id[record_id] = label
        elif label['original_split'] != split:
            raise ValueError(f'{record_id}: conflicting split labels')
        if evidence_type not in label['evidence_types']:
            label['evidence_types'].append(evidence_type)
        if evidence_type == 'exact_source_context':
            if label['source_family_sha256'] not in (None, group_hash):
                raise ValueError(f'{record_id}: multiple source context groups need manual review')
            label['source_family_sha256'] = group_hash
            label['normalized_context_sha256'] = content_hash
        elif evidence_type == 'exact_normalized_question':
            if label['normalized_question_sha256'] not in (None, content_hash):
                raise ValueError(f'{record_id}: multiple exact question groups need manual review')
            label['normalized_question_sha256'] = content_hash
    for group in candidate_report.get('source_family_groups', []):
        members = group.get('members') or []
        member_views = {str(member.get('view') or '') for member in members}
        member_splits = {str(member.get('split') or '') for member in members}
        if (
            group.get('evidence_type') != 'source_content_sha256'
            or group.get('split_count', 0) <= 1
            or member_views != {'xorqa'}
        ):
            continue
        if len(member_splits) <= 1:
            raise ValueError('cross-split group has fewer than two distinct member splits')
        group_hash = str(group.get('family_key_sha256') or '')
        group_records = []
        group_context_hashes = set()
        for member in members:
            record_id = str(member.get('record_id') or '')
            if record_id not in rows_by_id:
                raise ValueError(f'candidate member missing from XORQA input: {record_id}')
            row = rows_by_id[record_id]
            split = str(member.get('split') or '')
            if str(row.get('split') or '') != split:
                raise ValueError(f'{record_id}: member split does not match benchmark row')
            if not record_id.startswith('indicgenbench_xorqa:'):
                raise ValueError(f'candidate member is not an XORQA record: {record_id}')
            context = (row.get('source_example') or {}).get('context')
            context_hash, verified_family_hash = _context_family_hash(context)
            if verified_family_hash != group_hash:
                raise ValueError(f'{record_id}: source context hash does not match candidate group')
            group_context_hashes.add(context_hash)
            group_records.append((record_id, row, split, context_hash))
        if len(group_context_hashes) != 1:
            raise ValueError('candidate group does not share one exact normalized source context')
        split_pattern = '+'.join(sorted(member_splits))
        split_patterns[split_pattern] += 1
        for record_id, row, split, context_hash in group_records:
            add_label(
                record_id, row, split, 'exact_source_context',
                group_hash=group_hash, content_hash=context_hash,
            )

    for group in candidate_report.get('exact_text_groups', []):
        members = group.get('members') or []
        member_views = {str(member.get('view') or '') for member in members}
        member_splits = {str(member.get('split') or '') for member in members}
        if group.get('split_count', 0) <= 1 or member_views != {'xorqa'}:
            continue
        digest = str(group.get('normalized_text_sha256') or '')
        if len(member_splits) <= 1 or not digest:
            raise ValueError('cross-split exact-question group is missing split/hash evidence')
        for member in members:
            record_id = str(member.get('record_id') or '')
            if record_id not in rows_by_id:
                raise ValueError(f'exact-question member missing from XORQA input: {record_id}')
            row = rows_by_id[record_id]
            split = str(member.get('split') or '')
            if str(row.get('split') or '') != split:
                raise ValueError(f'{record_id}: exact-question member split does not match benchmark row')
            question = normalize_text(row.get('text_normalized') or row.get('text_original') or '')
            if _sha256(question) != digest:
                raise ValueError(f'{record_id}: normalized question hash does not match candidate group')
            add_label(
                record_id, row, split, 'exact_normalized_question',
                group_hash=digest, content_hash=digest,
            )
        exact_question_patterns['+'.join(sorted(member_splits))] += 1

    labels = list(labels_by_id.values())
    for label in labels:
        label['evidence_types'].sort()
    labels.sort(key=lambda row: (row['source_family_sha256'] or row['normalized_question_sha256'], row['record_id']))
    return {
        'schema_version': 'garhwali-benchmark-usage-labels-v0.1',
        'interpretation': 'conservative_row_level_usage_overlay; source_rows_are_retained',
        'decision_basis': (
            'Each flagged XORQA group was verified against source_example.context: '
            'the normalized context hash is identical across at least two original splits.'
        ),
        'counts': {
            'confirmed_shared_context_groups': sum(split_patterns.values()),
            'confirmed_cross_split_exact_question_groups': sum(exact_question_patterns.values()),
            'affected_records': len(labels),
            'groups_by_original_split_pattern': dict(sorted(split_patterns.items())),
            'exact_question_groups_by_split_pattern': dict(sorted(exact_question_patterns.items())),
        },
        'limitations': [
            'Shared source context is a conservative source-independence warning, not proof that question answers are identical or that a model saw the rows.',
            'All flagged rows remain present and eligible for explicitly labeled open diagnostic analysis.',
            'This overlay does not establish rights, language correctness, or cross-language semantic independence.',
            'Near-duplicate text pairs are not adjudicated by this exact-context overlay.',
        ],
        'labels': labels,
    }


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--candidate-report', type=Path)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()

    root = args.project_root.resolve()
    candidate_path = args.candidate_report or root / 'data/processed/evaluation/garhwali_bench/overlap_candidates.json'
    if not candidate_path.is_absolute():
        candidate_path = root / candidate_path
    benchmark_path = root / 'benchmarks/indicgenbench_xorqa.jsonl'
    output_dir = args.output_dir or root / 'data/processed/evaluation/garhwali_bench'
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    if not candidate_path.is_file():
        raise FileNotFoundError(f'overlap candidate report is missing: {candidate_path}')
    if not benchmark_path.is_file():
        raise FileNotFoundError(f'XORQA benchmark input is missing: {benchmark_path}')

    candidate_report = json.loads(candidate_path.read_text(encoding='utf-8'))
    candidate_input = next(
        (item for item in candidate_report.get('input_manifests', [])
         if item.get('path') == 'benchmarks/indicgenbench_xorqa.jsonl'),
        None,
    )
    benchmark_hash = _file_sha256(benchmark_path)
    if candidate_input is None or candidate_input.get('sha256') != benchmark_hash:
        raise ValueError('overlap report XORQA input hash does not match current benchmark file')

    result = build_usage_labels(candidate_report, _read_jsonl(benchmark_path))
    result['input_hashes'] = {
        'overlap_candidate_report_sha256': _file_sha256(candidate_path),
        'xorqa_benchmark_sha256': benchmark_hash,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'benchmark_usage_labels.json'
    jsonl_path = output_dir / 'benchmark_usage_labels.jsonl'
    markdown_path = output_dir / 'benchmark_usage_labels.md'
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    with jsonl_path.open('w', encoding='utf-8') as handle:
        for row in result['labels']:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    counts = result['counts']
    markdown = [
        '# XORQA source-context usage labels',
        '',
        'This local overlay flags exact question and source-context reuse across original XORQA splits. It preserves every source row and permits only explicitly labeled open diagnostic analysis for the affected families.',
        '',
        f"- Confirmed exact shared-context groups: {counts['confirmed_shared_context_groups']}",
        f"- Affected records: {counts['affected_records']}",
        f"- Cross-split exact-question groups: {counts['confirmed_cross_split_exact_question_groups']}",
        f"- Split patterns: `{json.dumps(counts['groups_by_original_split_pattern'], sort_keys=True)}`",
        f"- Candidate report SHA-256: `{result['input_hashes']['overlap_candidate_report_sha256']}`",
        f"- XORQA input SHA-256: `{benchmark_hash}`",
        '',
        'Flagged rows receive `open_diagnostic_only_split_overlap`; they are not eligible for independent source-generalization claims. This does not assert answer duplication, model exposure, or semantic equivalence.',
        '',
        'Near-duplicate pairs and all other candidate types remain unresolved; this overlay makes no language-quality or rights determination.',
        '',
    ]
    markdown_path.write_text('\n'.join(markdown), encoding='utf-8')
    print(json.dumps({
        'json': str(json_path),
        'jsonl': str(jsonl_path),
        'markdown': str(markdown_path),
        'counts': counts,
        'input_hashes': result['input_hashes'],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
