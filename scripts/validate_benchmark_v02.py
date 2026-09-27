#!/usr/bin/env python3
"""Validate current benchmark assets against the draft v0.2 data contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path


TASK_FIELDS = {
    'flores': ('source', 'target'),
    'crosssum': ('text', 'summary'),
    'xorqa': ('context', 'question', 'answers'),
}
ALLOWED_SPLITS = {'train', 'dev', 'test'}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _has_surrogate(value: object) -> bool:
    if isinstance(value, str):
        return any(unicodedata.category(char) == 'Cs' for char in value)
    if isinstance(value, dict):
        return any(_has_surrogate(key) or _has_surrogate(item) for key, item in value.items())
    if isinstance(value, (list, tuple)):
        return any(_has_surrogate(item) for item in value)
    return False


def _unicode_script(char: str) -> str:
    name = unicodedata.name(char, '')
    for prefix, script in (
        ('DEVANAGARI', 'Deva'), ('LATIN', 'Latn'), ('ARABIC', 'Arab'),
        ('BENGALI', 'Beng'), ('GURMUKHI', 'Guru'), ('TAMIL', 'Taml'),
        ('TELUGU', 'Telu'), ('GUJARATI', 'Gujr'), ('ORIYA', 'Orya'),
    ):
        if name.startswith(prefix):
            return script
    return 'Other'


def _script_profile(text: str) -> set[str]:
    return {
        _unicode_script(char)
        for char in text
        if unicodedata.category(char).startswith('L')
    }


def validate_external_records(task: str, rows: list[dict]) -> dict:
    """Validate source-specific task rows while preserving explicit empty answers."""
    if task not in TASK_FIELDS:
        raise ValueError(f'unsupported benchmark task: {task}')
    errors: list[str] = []
    seen_ids: set[str] = set()
    split_counts: Counter[str] = Counter()
    source_language_counts: Counter[str] = Counter()
    script_counts: Counter[str] = Counter()
    rights_counts: Counter[str] = Counter()
    mixed_script_records = 0
    empty_answer_records = 0

    for index, row in enumerate(rows):
        prefix = f'{task}[{index}]'
        if _has_surrogate(row):
            errors.append(f'{prefix}: malformed Unicode surrogate')
        for key in (
            'record_id', 'split', 'text_original', 'text_normalized', 'text_sha256',
            'iso_639_3', 'script', 'rights_status', 'license_id', 'license_url',
            'usage', 'training_eligible', 'provenance', 'source_example',
        ):
            if key not in row or row[key] is None:
                errors.append(f'{prefix}: missing required field {key}')
        record_id = str(row.get('record_id') or '').strip()
        if not record_id:
            errors.append(f'{prefix}: record_id is empty')
        elif record_id in seen_ids:
            errors.append(f'{prefix}: duplicate record_id {record_id}')
        seen_ids.add(record_id)

        split = str(row.get('split') or '').strip()
        if split not in ALLOWED_SPLITS:
            errors.append(f'{prefix}: unsupported split {split!r}')
        else:
            split_counts[split] += 1
        language = str(row.get('iso_639_3') or '').strip()
        script = str(row.get('script') or '').strip()
        if language != 'gbm':
            errors.append(f'{prefix}: expected Garhwali language label gbm')
        if not script:
            errors.append(f'{prefix}: script label is empty')
        script_counts[script or 'missing'] += 1
        rights = str(row.get('rights_status') or '').strip()
        license_id = str(row.get('license_id') or '').strip()
        license_url = str(row.get('license_url') or '').strip()
        if not rights or not license_id or not license_url:
            errors.append(f'{prefix}: rights/license declaration is incomplete')
        rights_counts[rights or 'missing'] += 1
        if row.get('usage') != 'evaluation_only':
            errors.append(f'{prefix}: external benchmark usage must remain evaluation_only')
        if row.get('training_eligible') is not False:
            errors.append(f'{prefix}: external benchmark row must not be training-eligible')

        original = row.get('text_original')
        normalized = row.get('text_normalized')
        if not isinstance(original, str) or not original.strip():
            errors.append(f'{prefix}: text_original is empty or not a string')
        if not isinstance(normalized, str) or not normalized.strip():
            errors.append(f'{prefix}: text_normalized is empty or not a string')
        elif isinstance(original, str):
            expected = unicodedata.normalize('NFC', original).strip()
            if expected != normalized:
                errors.append(f'{prefix}: text_normalized does not match NFC-trimmed text_original')
            if row.get('text_sha256') != sha256_bytes(normalized.encode('utf-8', errors='replace')):
                errors.append(f'{prefix}: text_sha256 does not match text_normalized')
            if len(_script_profile(original)) > 1:
                mixed_script_records += 1

        provenance = row.get('provenance')
        if not isinstance(provenance, dict) or not str(provenance.get('url') or '').strip() or not str(provenance.get('sha256') or '').strip():
            errors.append(f'{prefix}: provenance URL or source hash is missing')
        example = row.get('source_example')
        if not isinstance(example, dict):
            errors.append(f'{prefix}: source_example must be an object')
            continue
        if not str(example.get('lang') or '').strip():
            errors.append(f'{prefix}: source_example.lang is empty')
        else:
            source_language_counts[str(example['lang'])] += 1
        for field in TASK_FIELDS[task]:
            if field not in example:
                errors.append(f'{prefix}: source_example.{field} is missing')
            elif field == 'answers':
                answers = example[field]
                if not isinstance(answers, list):
                    errors.append(f'{prefix}: source_example.answers must be a list')
                elif not answers:
                    empty_answer_records += 1
                else:
                    for answer_index, answer in enumerate(answers):
                        answer_prefix = f'{prefix}: source_example.answers[{answer_index}]'
                        if not isinstance(answer, dict) or not str(answer.get('text') or '').strip():
                            errors.append(f'{answer_prefix} has empty or malformed answer text')
                        elif 'answer_start' in answer and (
                            not isinstance(answer['answer_start'], int)
                            or isinstance(answer['answer_start'], bool)
                            or answer['answer_start'] < 0
                        ):
                            errors.append(f'{answer_prefix}.answer_start must be a non-negative integer')
            elif not isinstance(example[field], str) or not example[field].strip():
                errors.append(f'{prefix}: source_example.{field} is empty or not a string')

    return {
        'records': len(rows),
        'split_counts': dict(sorted(split_counts.items())),
        'source_language_counts': dict(sorted(source_language_counts.items())),
        'declared_script_counts': dict(sorted(script_counts.items())),
        'rights_status_counts': dict(sorted(rights_counts.items())),
        'mixed_script_records': mixed_script_records,
        'empty_answer_records': empty_answer_records,
        'errors': errors,
    }


def validate_asr_records(rows: list[dict], project_root: Path) -> dict:
    errors: list[str] = []
    seen_audio: set[str] = set()
    split_counts: Counter[str] = Counter()
    speakers: set[str] = set()
    audio_files_verified = 0
    root = project_root.resolve()
    for index, row in enumerate(rows):
        prefix = f'asr[{index}]'
        if _has_surrogate(row):
            errors.append(f'{prefix}: malformed Unicode surrogate')
        for field in (
            'audio_path', 'local_audio_path', 'audio_sha256', 'asr_target',
            'asr_target_sha256', 'split', 'duration_seconds', 'speaker_id',
            'license', 'source',
        ):
            if field not in row or row[field] is None or not str(row[field]).strip():
                errors.append(f'{prefix}: {field} is missing or empty')
        audio_hash = str(row.get('audio_sha256') or '')
        if audio_hash:
            if audio_hash in seen_audio:
                errors.append(f'{prefix}: duplicate audio_sha256')
            seen_audio.add(audio_hash)
        target = row.get('asr_target')
        if isinstance(target, str) and target.strip():
            target_hash = sha256_bytes(target.encode('utf-8', errors='replace'))
            if row.get('asr_target_sha256') != target_hash:
                errors.append(f'{prefix}: ASR target hash does not match')
        split = str(row.get('split') or '')
        if split not in ALLOWED_SPLITS:
            errors.append(f'{prefix}: unsupported split {split!r}')
        else:
            split_counts[split] += 1
        try:
            duration = float(row.get('duration_seconds'))
            if duration <= 0:
                errors.append(f'{prefix}: duration_seconds must be positive')
        except (TypeError, ValueError):
            errors.append(f'{prefix}: duration_seconds must be numeric')
        if row.get('speaker_id'):
            speakers.add(str(row['speaker_id']))
        local_path = Path(str(row.get('local_audio_path') or ''))
        if local_path.is_absolute() or '..' in local_path.parts:
            errors.append(f'{prefix}: local audio path escapes project root')
            continue
        resolved = (root / local_path).resolve()
        if root not in resolved.parents:
            errors.append(f'{prefix}: local audio path escapes project root')
            continue
        if not resolved.is_file():
            errors.append(f'{prefix}: local audio file is missing')
            continue
        if sha256_bytes(resolved.read_bytes()) != audio_hash:
            errors.append(f'{prefix}: local audio hash does not match')
        else:
            audio_files_verified += 1
    return {
        'records': len(rows),
        'split_counts': dict(sorted(split_counts.items())),
        'unique_speakers': len(speakers),
        'audio_files_verified': audio_files_verified,
        'errors': errors,
    }


def validate_internal_text_records(rows: list[dict]) -> dict:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f'internal_text[{index}]'
        if _has_surrogate(row):
            errors.append(f'{prefix}: malformed Unicode surrogate')
        record_id = str(row.get('segment_sha256') or '')
        text = row.get('text')
        if not record_id or not isinstance(text, str) or not text.strip():
            errors.append(f'{prefix}: missing segment hash or text')
            continue
        if record_id in seen_ids:
            errors.append(f'{prefix}: duplicate segment hash')
        seen_ids.add(record_id)
        if sha256_bytes(text.encode('utf-8', errors='replace')) != record_id:
            errors.append(f'{prefix}: segment hash does not match text')
        if not row.get('duplicate_component_id'):
            errors.append(f'{prefix}: duplicate component ID is missing')
        if row.get('split') != 'test':
            errors.append(f'{prefix}: expected current internal text view split test')
    return {'records': len(rows), 'errors': errors}


def validate_recommended_text_records(rows: list[dict], expected_split: str) -> dict:
    errors: list[str] = []
    seen_ids: set[str] = set()
    languages: Counter[str] = Counter()
    scripts: Counter[str] = Counter()
    mixed_script_records = 0
    for index, row in enumerate(rows):
        prefix = f'text_recommended/{expected_split}[{index}]'
        if _has_surrogate(row):
            errors.append(f'{prefix}: malformed Unicode surrogate')
        record_id = str(row.get('id') or '').strip()
        text = row.get('text')
        if not record_id or not isinstance(text, str) or not text.strip():
            errors.append(f'{prefix}: missing ID or nonempty text')
        elif record_id in seen_ids:
            errors.append(f'{prefix}: duplicate ID')
        if record_id:
            seen_ids.add(record_id)
        if row.get('split') != expected_split:
            errors.append(f'{prefix}: split differs from view')
        language = str(row.get('language') or '').strip()
        script = str(row.get('script') or '').strip()
        if not language or not script:
            errors.append(f'{prefix}: language or script label is missing')
        languages[language or 'missing'] += 1
        scripts[script or 'missing'] += 1
        provenance = row.get('provenance')
        if not isinstance(provenance, list) or not provenance:
            errors.append(f'{prefix}: provenance is missing')
        if 'public_rights_basis' not in row:
            errors.append(f'{prefix}: public_rights_basis field is missing')
        if isinstance(text, str):
            if unicodedata.normalize('NFC', text) != text:
                errors.append(f'{prefix}: text is not NFC-normalized')
            if len(_script_profile(text)) > 1:
                mixed_script_records += 1
    return {
        'records': len(rows),
        'language_counts': dict(sorted(languages.items())),
        'declared_script_counts': dict(sorted(scripts.items())),
        'mixed_script_records': mixed_script_records,
        'errors': errors,
    }


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _file_summary(root: Path, relative: str) -> tuple[dict, list[dict]]:
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f'benchmark contract input is missing: {relative}')
    rows = _read_jsonl(path)
    summary = {
        'path': relative,
        'records': len(rows),
        'sha256': sha256_bytes(path.read_bytes()),
        'split_counts': dict(sorted(Counter(str(row.get('split') or '') for row in rows).items())),
    }
    return summary, rows


def validate_project(project_root: Path) -> dict:
    root = project_root.resolve()
    manifest_path = root / 'data/processed/evaluation/garhwali_bench/manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError('current GarhwaliBench manifest is missing')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    report = {
        'schema_version': 'garhwali-bench-v0.2-contract-validation-draft',
        'based_on_release_id': manifest.get('release_id'),
        'manifest_sha256': sha256_bytes(manifest_path.read_bytes()),
        'assets': {},
        'tasks': {},
        'migration_gaps': [
            'Internal text v0.1 records contain one text field; the v0.2 export should retain raw text, scoring text, and a normalizer ID separately.',
            'Internal text records do not yet declare a per-record rights state in this benchmark view; keep release rights gating separate.',
            'The exact/near overlap usage overlay is local-only and must be referenced by hash from a v0.2 card/manifest.',
        ],
        'errors': [],
    }
    expected_assets = []
    for task, entry in sorted(manifest.get('tasks', {}).items()):
        expected_assets.append((f'external/{task}', str(entry['path']), entry.get('records'), entry.get('sha256')))
    for task, entry in sorted(manifest.get('internal_evaluation', {}).items()):
        expected_assets.append((f'internal/{task}', str(entry['path']), None, entry.get('sha256')))
    train_entry = manifest.get('training', {}).get('text', {})
    expected_assets.append(('text_recommended/train', str(train_entry.get('path')), train_entry.get('records'), train_entry.get('sha256')))
    for split in ('validation', 'test'):
        expected_assets.append((
            f'text_recommended/{split}',
            f'data/processed/model_ready/splits/text_recommended/{split}.jsonl',
            None,
            None,
        ))

    for name, relative, expected_count, expected_hash in expected_assets:
        try:
            summary, rows = _file_summary(root, relative)
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            report['errors'].append(f'{name}: {exc}')
            continue
        report['assets'][name] = summary
        if expected_count is not None and summary['records'] != expected_count:
            report['errors'].append(f'{name}: record count differs from manifest')
        if expected_hash and summary['sha256'] != expected_hash:
            report['errors'].append(f'{name}: SHA-256 differs from manifest')
        if name.startswith('external/'):
            task = name.split('/', 1)[1]
            task_report = validate_external_records(task, rows)
            report['tasks'][task] = task_report
            report['errors'].extend(f'{name}: {error}' for error in task_report['errors'])
        elif name == 'internal/text':
            task_report = validate_internal_text_records(rows)
            errors = task_report['errors']
            report['tasks']['internal_text'] = task_report
            report['errors'].extend(f'internal/text: {error}' for error in errors)
        elif name == 'internal/asr':
            task_report = validate_asr_records(rows, root)
            report['tasks']['internal_asr'] = task_report
            report['errors'].extend(f'internal/asr: {error}' for error in task_report['errors'])
        else:
            expected_split = name.rsplit('/', 1)[-1]
            task_report = validate_recommended_text_records(rows, expected_split)
            report['tasks'][name] = task_report
            report['errors'].extend(f'{name}: {error}' for error in task_report['errors'])

    report['status'] = 'pass' if not report['errors'] else 'fail'
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    output_dir = args.output_dir or root / 'data/processed/evaluation/garhwali_bench'
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    result = validate_project(root)
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'v0.2_contract_validation.json'
    markdown_path = output_dir / 'v0.2_contract_validation.md'
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    lines = [
        '# GarhwaliBench v0.2 contract validation (draft)',
        '',
        f"- Status: **{result['status']}**",
        f"- Based on: `{result['based_on_release_id']}`",
        f"- v0.1 manifest SHA-256: `{result['manifest_sha256']}`",
        '',
        '## Asset inventory',
        '',
        '| View | Rows | SHA-256 | Split counts |',
        '| --- | ---: | --- | --- |',
    ]
    for name, asset in sorted(result['assets'].items()):
        lines.append(f"| `{name}` | {asset['records']:,} | `{asset['sha256']}` | `{json.dumps(asset['split_counts'], sort_keys=True)}` |")
    lines.extend(['', '## Migration gaps', ''])
    lines.extend(f'- {item}' for item in result['migration_gaps'])
    lines.extend(['', '## Errors', ''])
    lines.extend(f'- {item}' for item in result['errors'])
    lines.append('' if result['errors'] else '- None.')
    lines.append('')
    markdown_path.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({
        'status': result['status'],
        'assets': len(result['assets']),
        'errors': len(result['errors']),
        'json': str(json_path),
        'markdown': str(markdown_path),
    }, indent=2, sort_keys=True))
    return 0 if result['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
