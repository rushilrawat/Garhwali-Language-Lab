#!/usr/bin/env python3
"""Create a checksum-bound upload plan and prevent public all-data uploads."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / 'data/huggingface/garhwali-language-lab-all-data'
DEFAULT_OUTPUT = ROOT / 'release/v0.1.1/huggingface-all-data-upload.json'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def build(package, target_repo=None, visibility='private'):
    package = Path(package)
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    profile = manifest.get('profile')
    if visibility == 'public' and profile != 'public':
        raise ValueError(
            'Only an explicit public profile can be planned as a public upload.'
        )
    if not isinstance(manifest.get('configs'), dict) or not manifest.get('release_id'):
        raise ValueError('Package manifest is missing release_id or configs')
    if target_repo is None:
        target_repo = (
            'rushilrawat/garhwali-language-lab'
            if profile == 'public'
            else 'rushilrawat/garhwali-language-lab-all-data'
        )
    expected_files = {
        'README.md', 'manifest.json', 'LICENSE_POLICY.md',
        'ATTRIBUTION.md', 'REMOVAL_POLICY.md',
    }
    for key, config in manifest['configs'].items():
        group, _ = key.split('/', 1)
        expected_files.update(
            f'data/{group}/{filename}' for filename in config.get('files', [])
        )
    actual_files = {
        path.relative_to(package).as_posix()
        for path in package.rglob('*') if path.is_file() or path.is_symlink()
    }
    symlinks = sorted(
        path.relative_to(package).as_posix()
        for path in package.rglob('*') if path.is_symlink()
    )
    unexpected = sorted(
        path for path in actual_files - expected_files
        if not (manifest.get('include_audio') and path.startswith('audio/'))
    )
    if symlinks or unexpected:
        raise ValueError(
            f'Package contains symlinks or unmanifested files: '
            f'symlinks={symlinks}, unexpected={unexpected}'
        )
    artifacts = []
    aggregate = hashlib.sha256()
    for path in sorted(item for item in package.rglob('*') if item.is_file()):
        relative = path.relative_to(package).as_posix()
        digest = sha256(path)
        aggregate.update(f'{relative}\0{digest}\n'.encode())
        artifacts.append({
            'path': relative,
            'bytes': path.stat().st_size,
            'sha256': digest,
        })
    return {
        'release_id': manifest['release_id'],
        'generated': date.today().isoformat(),
        'target_repo': target_repo,
        'repo_type': 'dataset',
        'planned_visibility': visibility,
        'publication_status': (
            'blocked_pending_rights_and_quality_review'
            if profile == 'all-data'
            else 'ready_after_final_approval'
        ),
        'profile': profile,
        'include_audio': bool(manifest.get('include_audio')),
        'records': sum(
            config['records'] for config in manifest.get('configs', {}).values()
        ),
        'configurations': len(manifest.get('configs', {})),
        'catalog_records': manifest.get('catalog_records'),
        'catalog_redacted_text_records': manifest.get(
            'catalog_redacted_text_records'
        ),
        'files': len(artifacts),
        'bytes': sum(item['bytes'] for item in artifacts),
        'aggregate_sha256': aggregate.hexdigest(),
        'artifacts': artifacts,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--target-repo')
    parser.add_argument('--visibility', choices=('private', 'public'), default='private')
    args = parser.parse_args()
    report = build(args.package, args.target_repo, args.visibility)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
