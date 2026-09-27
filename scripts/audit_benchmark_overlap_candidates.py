#!/usr/bin/env python3
"""Find review-only exact, near-duplicate, and source-family candidates."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


INPUT_PATHS = [
    *(f'data/processed/model_ready/splits/text_recommended/{split}.jsonl'
      for split in ('train', 'validation', 'test')),
    'data/processed/evaluation/garhwali_bench/internal_text.jsonl',
    'benchmarks/indicgenbench_flores.jsonl',
    'benchmarks/indicgenbench_crosssum.jsonl',
    'benchmarks/indicgenbench_xorqa.jsonl',
]


def normalize_text(text: object) -> str:
    """Normalize Unicode while preserving letters, combining marks, and digits."""
    value = unicodedata.normalize('NFKC', str(text or '')).casefold()
    return ' '.join(
        ''.join(
            char if unicodedata.category(char)[0] in {'L', 'M', 'N'} else ' '
            for char in value
        ).split()
    )


def _member(record: dict) -> dict:
    return {
        'view': str(record.get('view') or ''),
        'record_id': str(record.get('record_id') or ''),
        'split': str(record.get('split') or ''),
        'language': str(record.get('language') or 'unknown'),
        'script': str(record.get('script') or 'unknown'),
    }


def _member_key(member: dict) -> tuple[str, str, str, str, str]:
    return (
        member['view'], member['split'], member['record_id'],
        member['language'], member['script'],
    )


def _ngrams(text: str, size: int) -> set[str]:
    return {text[index:index + size] for index in range(len(text) - size + 1)}


def _infer_script(text: str) -> str:
    counts: dict[str, int] = defaultdict(int)
    for char in text:
        name = unicodedata.name(char, '')
        for prefix, script in (
            ('DEVANAGARI', 'Deva'), ('LATIN', 'Latn'), ('ARABIC', 'Arab'),
            ('BENGALI', 'Beng'), ('GURMUKHI', 'Guru'), ('TAMIL', 'Taml'),
            ('TELUGU', 'Telu'), ('GUJARATI', 'Gujr'), ('ORIYA', 'Orya'),
        ):
            if name.startswith(prefix):
                counts[script] += 1
                break
    return max(sorted(counts), key=counts.get) if counts else 'unknown'


def _canonical_url(value: object) -> str:
    raw = str(value or '').strip()
    parts = urlsplit(raw)
    if not parts.scheme or not parts.netloc:
        return raw.casefold()
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), parts.path, parts.query, ''))


def _url_family_key(value: object) -> str | None:
    canonical = _canonical_url(value)
    parts = urlsplit(canonical)
    if (parts.hostname or '').casefold() in {'huggingface.co', 'www.huggingface.co'} and parts.path.startswith('/datasets/'):
        return None
    return f'url:{canonical}' if canonical else None


def _provenance_family_keys(value: object) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, list):
        for item in value:
            keys.update(_provenance_family_keys(item))
    elif isinstance(value, dict):
        for field in ('source_url', 'url'):
            item = value.get(field)
            if item:
                family_key = _url_family_key(item)
                if family_key:
                    keys.add(family_key)
        if value.get('provenance') is not None:
            keys.update(_provenance_family_keys(value['provenance']))
    return keys


def _source_family_keys(row: dict, *, internal: bool) -> list[str]:
    keys: set[str] = set()
    if internal:
        keys.update(_provenance_family_keys(row.get('provenance')))
        for parent in row.get('parents') or []:
            keys.update(_provenance_family_keys(parent.get('provenance')))
            parent_hash = str(parent.get('text_sha256') or '').strip().casefold()
            if parent_hash:
                keys.add(f'parent_text_sha256:{parent_hash}')
        component_id = str(row.get('duplicate_component_id') or '').strip()
        if component_id:
            keys.add(f'duplicate_component:{component_id.casefold()}')
        return sorted(keys)

    example = row.get('source_example') or {}
    for field in ('source_url', 'target_url'):
        if example.get(field):
            family_key = _url_family_key(example[field])
            if family_key:
                keys.add(family_key)
    for field in ('source', 'text', 'context'):
        value = normalize_text(example.get(field, ''))
        if len(value) >= 20:
            digest = hashlib.sha256(value.encode('utf-8')).hexdigest()
            keys.add(f'source_content_sha256:{digest}')
    return sorted(keys)


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{line_number}: expected a JSON object')
            rows.append(row)
    return rows


def _collect_project_records(project_root: str | Path) -> tuple[list[dict], list[dict]]:
    root = Path(project_root).resolve()
    records = []
    input_manifests = []
    for relative in INPUT_PATHS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f'required overlap-audit input is missing: {relative}')
        rows = _read_jsonl(path)
        input_manifests.append({
            'path': relative,
            'records': len(rows),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        })
        internal = relative.startswith('data/')
        if '/text_recommended/' in relative:
            view = f"text_recommended/{relative.rsplit('/', 1)[-1].removesuffix('.jsonl')}"
        elif relative.endswith('/internal_text.jsonl'):
            view = 'internal_text'
        else:
            view = Path(relative).stem.replace('indicgenbench_', '')
        for index, row in enumerate(rows):
            text = row.get('text')
            if text is None:
                text = row.get('text_normalized', '')
            language = row.get('language') or row.get('iso_639_3') or 'gbm'
            script = row.get('script') or _infer_script(str(text or ''))
            record_id = (
                row.get('record_id') or row.get('id') or row.get('segment_sha256')
                or row.get('component_sha256') or f'{view}:{index}'
            )
            records.append({
                'view': view,
                'record_id': str(record_id),
                'split': str(row.get('split') or row.get('original_split') or ''),
                'language': str(language),
                'script': str(script),
                'text': str(text or ''),
                'source_family_keys': _source_family_keys(row, internal=internal),
            })
    records.sort(key=lambda record: _member_key(_member(record)))
    return records, input_manifests


def collect_project_records(project_root: str | Path) -> list[dict]:
    """Load the frozen text benchmark/training views and their source links."""
    return _collect_project_records(project_root)[0]


def build_project_report(project_root: str | Path) -> dict:
    """Build a reproducible local audit with content-addressed inputs."""
    records, input_manifests = _collect_project_records(project_root)
    report = audit_records(records)
    report['input_manifests'] = input_manifests
    report['limitations'] = [
        'Near-duplicate candidates use character n-gram Jaccard and compare only equal language/script labels.',
        'Grams occurring in more than max_gram_frequency records are excluded from candidate generation.',
        'Source-family groups require an exact shared URL, parent hash, component ID, or source-content hash.',
        'Hugging Face dataset repository URLs are collection-level metadata and are not used as record-family keys.',
        'No embedding, translation, paraphrase, or semantic similarity model is used.',
        'Cross-language semantic matching is not attempted; record language labels may not describe nested source fields.',
        'A negative result means only that this configured scan found no candidate links.',
        'Candidate links do not prove leakage; inspect source, task, and split context before changing eligibility.',
    ]
    return report


def render_markdown(report: dict) -> str:
    counts = report['counts']
    lines = [
        '# Benchmark overlap candidate audit',
        '',
        'This report links possible exact duplicates, same-language near duplicates, and shared source families. It does not remove records or determine whether a match is leakage.',
        '',
        '## Counts',
        '',
    ]
    for key, value in counts.items():
        lines.append(f'- `{key}`: {value:,}')
    lines.extend(['', '## Method limits', ''])
    lines.extend(f'- {item}' for item in report['limitations'])
    lines.extend([
        '',
        'Row IDs, pair scores, and hashed source-family links are in the companion JSON. It contains no copied source text or raw source URLs.',
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output_dir = args.output_dir or root / 'data/processed/evaluation/garhwali_bench'
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_project_report(root)
    json_path = output_dir / 'overlap_candidates.json'
    markdown_path = output_dir / 'overlap_candidates.md'
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    markdown_path.write_text(render_markdown(report), encoding='utf-8')
    print(json.dumps({
        'json': str(json_path),
        'markdown': str(markdown_path),
        'counts': report['counts'],
        'interpretation': report['interpretation'],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def audit_records(
    records: list[dict],
    *,
    ngram_size: int = 5,
    min_chars: int = 40,
    min_jaccard: float = 0.85,
    max_gram_frequency: int = 100,
) -> dict:
    """Return stable candidate links without changing or excluding source rows."""
    if ngram_size < 1 or min_chars < ngram_size:
        raise ValueError('ngram_size must be positive and min_chars must cover it')
    if not 0 < min_jaccard <= 1:
        raise ValueError('min_jaccard must be in (0, 1]')
    if max_gram_frequency < 2:
        raise ValueError('max_gram_frequency must be at least 2')

    prepared = []
    exact_groups: dict[str, list[dict]] = defaultdict(list)
    source_groups: dict[str, list[dict]] = defaultdict(list)
    family_types: dict[str, str] = {}
    for record in records:
        member = _member(record)
        text = normalize_text(record.get('text', ''))
        if text:
            exact_groups[hashlib.sha256(text.encode('utf-8')).hexdigest()].append(member)
            if len(text) >= min_chars:
                prepared.append((member, text, _ngrams(text, ngram_size)))
        for value in record.get('source_family_keys') or []:
            key = str(value).strip().casefold()
            if not key:
                continue
            digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
            source_groups[digest].append(member)
            family_types[digest] = key.partition(':')[0] if ':' in key else 'source_key'

    exact_text_groups = []
    for digest, members in sorted(exact_groups.items()):
        if len(members) < 2:
            continue
        members = sorted(members, key=_member_key)
        exact_text_groups.append({
            'normalized_text_sha256': digest,
            'review_state': 'unreviewed_candidate',
            'members': members,
            'record_language_label_count': len({item['language'] for item in members}),
            'split_count': len({item['split'] for item in members}),
            'view_count': len({item['view'] for item in members}),
        })

    postings: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for index, (member, _text, grams) in enumerate(prepared):
        language_script = (member['language'], member['script'])
        for gram in grams:
            postings[(*language_script, gram)].append(index)

    candidate_indexes = set()
    for indexes in postings.values():
        if 2 <= len(indexes) <= max_gram_frequency:
            candidate_indexes.update(combinations(indexes, 2))

    near_duplicate_pairs = []
    for left_index, right_index in sorted(candidate_indexes):
        left_member, left_text, left_grams = prepared[left_index]
        right_member, right_text, right_grams = prepared[right_index]
        if left_text == right_text:
            continue
        intersection = len(left_grams & right_grams)
        union = len(left_grams | right_grams)
        similarity = intersection / union if union else 0.0
        if similarity < min_jaccard:
            continue
        left_key = _member_key(left_member)
        right_key = _member_key(right_member)
        if right_key < left_key:
            left_member, right_member = right_member, left_member
            left_text, right_text = right_text, left_text
        near_duplicate_pairs.append({
            'left': left_member,
            'right': right_member,
            'review_state': 'unreviewed_candidate',
            'similarity': round(similarity, 6),
            'method': f'char_{ngram_size}gram_jaccard',
            'left_text_sha256': hashlib.sha256(left_text.encode('utf-8')).hexdigest(),
            'right_text_sha256': hashlib.sha256(right_text.encode('utf-8')).hexdigest(),
        })
    near_duplicate_pairs.sort(
        key=lambda pair: (
            _member_key(pair['left']), _member_key(pair['right']), -pair['similarity']
        )
    )

    source_family_groups = []
    for digest, members in sorted(source_groups.items()):
        unique_members = {tuple(_member_key(member)): member for member in members}
        members = sorted(unique_members.values(), key=_member_key)
        if len(members) < 2:
            continue
        source_family_groups.append({
            'family_key_sha256': digest,
            'evidence_type': family_types[digest],
            'review_state': 'unreviewed_candidate',
            'members': members,
            'record_language_label_count': len({item['language'] for item in members}),
            'split_count': len({item['split'] for item in members}),
            'view_count': len({item['view'] for item in members}),
        })

    counts = {
        'input_records': len(records),
        'exact_text_groups': len(exact_text_groups),
        'exact_cross_view_or_split_groups': sum(
            group['split_count'] > 1 or group['view_count'] > 1
            for group in exact_text_groups
        ),
        'exact_cross_split_groups': sum(
            group['split_count'] > 1 for group in exact_text_groups
        ),
        'exact_cross_view_groups': sum(
            group['view_count'] > 1 for group in exact_text_groups
        ),
        'near_duplicate_pairs': len(near_duplicate_pairs),
        'near_duplicate_cross_view_or_split_pairs': sum(
            (pair['left']['view'], pair['left']['split'])
            != (pair['right']['view'], pair['right']['split'])
            for pair in near_duplicate_pairs
        ),
        'near_duplicate_cross_split_pairs': sum(
            pair['left']['split'] != pair['right']['split']
            for pair in near_duplicate_pairs
        ),
        'near_duplicate_cross_view_pairs': sum(
            pair['left']['view'] != pair['right']['view']
            for pair in near_duplicate_pairs
        ),
        'source_family_groups': len(source_family_groups),
        'source_family_cross_view_or_split_groups': sum(
            group['split_count'] > 1 or group['view_count'] > 1
            for group in source_family_groups
        ),
        'source_family_cross_split_groups': sum(
            group['split_count'] > 1 for group in source_family_groups
        ),
        'source_family_cross_view_groups': sum(
            group['view_count'] > 1 for group in source_family_groups
        ),
        'source_family_multiple_record_language_label_groups': sum(
            group['record_language_label_count'] > 1 for group in source_family_groups
        ),
    }
    return {
        'schema_version': 'garhwali-benchmark-overlap-candidates-v0.1',
        'parameters': {
            'normalization': 'NFKC, casefold, retain Unicode letters/marks/numbers, collapse separators',
            'ngram_size': ngram_size,
            'min_chars': min_chars,
            'min_jaccard': min_jaccard,
            'max_gram_frequency': max_gram_frequency,
            'near_duplicates_compared_within': 'same language and script only',
        },
        'interpretation': 'candidate_links_only; not_proof_of_no_leakage',
        'counts': counts,
        'exact_text_groups': exact_text_groups,
        'near_duplicate_pairs': near_duplicate_pairs,
        'source_family_groups': source_family_groups,
    }


if __name__ == '__main__':
    raise SystemExit(main())
