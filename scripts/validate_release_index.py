#!/usr/bin/env python3
"""Validate the tracked release index without requiring Git-ignored data files."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'release/v0.1.1-manifest.json'


def validate(index):
    errors = []
    if (
        'release_ready' in str(index.get('status') or '')
        and index.get('final_audit_status') != 'passed'
    ):
        errors.append('release-ready status requires a passing final audit')
    if (
        index.get('status') == 'blocked_final_audit'
        and index.get('final_audit_status') == 'passed'
    ):
        errors.append('blocked release status is stale after a passing final audit')
    for name in ('text', 'speech'):
        section = index[name]
        actual = sum(section['splits'].values())
        if actual != section['total']:
            errors.append(f"{name} split counts sum to {actual}, expected {section['total']}")
    if 'derived_audio' in index:
        section = index['derived_audio']
        actual = sum(section['splits'].values()) + section.get('flagged_review_copies', 0)
        if actual != section['total']:
            errors.append(f"derived audio counts sum to {actual}, expected {section['total']}")
    for name, value in index['leakage'].items():
        if value != 0:
            errors.append(f'{name} must be zero, found {value}')
    for name in ('internal_exact_train_text', 'asr_speaker_overlap'):
        value = index.get('garhwali_bench', {}).get(name, 0)
        if value != 0:
            errors.append(f'garhwali_bench.{name} must be zero, found {value}')
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('index', type=Path, nargs='?', default=DEFAULT_INDEX)
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding='utf-8'))
    errors = validate(index)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(json.dumps({'release_id': index['release_id'], 'status': index['status'], 'validation': 'passed'}, indent=2))


if __name__ == '__main__':
    main()
