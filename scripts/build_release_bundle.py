#!/usr/bin/env python3
"""Copy compact generated reports and supporting artifacts into the Git release."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'release/v0.1.1/artifacts'
MAX_BYTES = 10 * 1024 * 1024
REPORT_NAMES = {
    'full_draft_audit.json', 'indicbert_head_adaptation.json',
    'indicbert_lora_adaptation.json', 'indicbert_lora_long.json',
    'indicbert_transfer_test.json', 'indicbertv2_masked_lm.json',
    'manifest.json', 'report.json', 'report.md', 'text_scaling.json',
    'tokenizer_report.json',
}
OUTPUT_FILES = (
    'outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx',
    'outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx.inspect.ndjson',
    'outputs/garhwali-corpus-inventory-2026-09-07/corpus-schema.png',
    'outputs/garhwali-corpus-inventory-2026-09-07/inspection.txt',
    'outputs/garhwali-corpus-inventory-2026-09-07/inventory.png',
    'outputs/garhwali-corpus-inventory-2026-09-07/rights-guide.png',
    'outputs/online-ingestion-2026-09-07/dedup-report.json',
    'outputs/online-ingestion-2026-09-07/lsi-page-check.png',
    'outputs/online-ingestion-2026-09-07/report.md',
)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def selected_files():
    processed = ROOT / 'data/processed'
    for path in processed.rglob('*'):
        if (not path.is_symlink() and path.is_file()
                and path.resolve().is_relative_to(ROOT.resolve())
                and path.stat().st_size <= MAX_BYTES
                and (path.name in REPORT_NAMES or path.name.endswith('_report.json'))):
            yield path
    for relative in OUTPUT_FILES:
        path = ROOT / relative
        if (path.exists() and not path.is_symlink() and path.is_file()
                and path.resolve().is_relative_to(ROOT.resolve())
                and path.stat().st_size <= MAX_BYTES):
            yield path
    package = ROOT / 'data/huggingface/garhwali-language-lab'
    for name in (
        'README.md', 'manifest.json', 'LICENSE_POLICY.md',
        'ATTRIBUTION.md', 'REMOVAL_POLICY.md',
    ):
        path = package / name
        if path.is_file() and not path.is_symlink():
            yield path


def _build_at(output):
    output = Path(output)
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
        'release_id': 'garhwali-language-lab-v0.1.1',
        'files': len(entries),
        'bytes': sum(item['bytes'] for item in entries),
        'artifacts': entries,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'index.json').write_text(
        json.dumps(index, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return index


def build(output=OUTPUT):
    output = Path(output)
    if output.exists() and output.resolve() != OUTPUT.resolve():
        raise ValueError(
            'refusing to replace an existing custom release bundle directory'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'release bundle output must be a regular directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.building-'
    ))
    staging.rmdir()
    backup = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.previous-'
    ))
    backup.rmdir()
    try:
        index = _build_at(staging)
        if output.exists():
            output.rename(backup)
        staging.rename(output)
        if backup.exists():
            shutil.rmtree(backup)
        return index
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and not output.exists():
            backup.rename(output)
        elif backup.exists():
            shutil.rmtree(backup)
        raise


def verify(output=OUTPUT, check_sources=True):
    output = Path(output)
    index_path = output / 'index.json'
    if not index_path.exists():
        return ['release artifact index is missing']
    index = json.loads(index_path.read_text(encoding='utf-8'))
    errors = []
    entries = index.get('artifacts', [])
    indexed_paths = [item.get('path') for item in entries]
    if len(indexed_paths) != len(set(indexed_paths)):
        errors.append('duplicate artifact paths in index')
    for item in index.get('artifacts', []):
        path = output / item['path']
        if (path.is_symlink()
                or not path.resolve().is_relative_to(output.resolve())):
            errors.append(f"unsafe_path:{item['path']}")
        elif not path.exists():
            errors.append(f"missing:{item['path']}")
        elif path.stat().st_size != item['bytes']:
            errors.append(f"size:{item['path']}")
        elif sha256(path) != item['sha256']:
            errors.append(f"sha256:{item['path']}")
        elif path.stat().st_size <= MAX_BYTES:
            content = path.read_bytes()
            if any(marker in content for marker in (
                b'/Users/', b'/home/', b'C:\\Users\\',
            )):
                errors.append(f"machine_specific_path:{item['path']}")
    if len(index.get('artifacts', [])) != index.get('files'):
        errors.append('index file count does not match artifact entries')
    if sum(item.get('bytes', 0) for item in entries) != index.get('bytes'):
        errors.append('index byte count does not match artifact entries')
    if index.get('release_id') != 'garhwali-language-lab-v0.1.1':
        errors.append('unexpected release ID')
    indexed = set(indexed_paths)
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob('*')
        if (path.is_file() or path.is_symlink()) and path.name != 'index.json'
    }
    for path in sorted(output.rglob('*')):
        if path.is_symlink():
            errors.append(f'unsafe_symlink:{path.relative_to(output).as_posix()}')
    for path in sorted(actual - indexed):
        errors.append(f'unindexed:{path}')
    for path in sorted(indexed - actual):
        errors.append(f'index_missing:{path}')
    source_tree_available = (
        (ROOT / 'data/processed').is_dir()
        and (ROOT / 'data/huggingface/garhwali-language-lab').is_dir()
    )
    if check_sources and source_tree_available:
        current = {
            source.relative_to(ROOT).as_posix(): {
                'bytes': source.stat().st_size,
                'sha256': sha256(source),
            }
            for source in set(selected_files())
        }
        recorded = {
            item['path']: {'bytes': item['bytes'], 'sha256': item['sha256']}
            for item in entries
        }
        for path in sorted(set(current) - set(recorded)):
            errors.append(f'stale_index_missing_current:{path}')
        for path in sorted(set(recorded) - set(current)):
            errors.append(f'stale_index_removed_source:{path}')
        for path in sorted(set(current) & set(recorded)):
            if current[path] != recorded[path]:
                errors.append(f'stale_index_changed_source:{path}')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        errors = verify(args.output)
        print(json.dumps({'status': 'passed' if not errors else 'failed',
                          'errors': errors}, indent=2, sort_keys=True))
        if errors:
            raise SystemExit(1)
    else:
        print(json.dumps(build(args.output), indent=2, sort_keys=True))
