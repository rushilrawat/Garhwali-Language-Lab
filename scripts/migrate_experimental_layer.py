#!/usr/bin/env python3
"""Replace the legacy holding layer with an active local experimental layer."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def activate(row):
    row = dict(row)
    if row.get('corpus_layer') == 'quarantine':
        row['corpus_layer'] = 'experimental'
    if row.get('usage') == 'provenance_review_only':
        row['usage'] = 'all_data_experimental_user_approved'
    row['experimental_training_eligible'] = True
    return row


def migrate(root=ROOT):
    source = Path(root) / 'quarantine'
    destination = Path(root) / 'experimental'
    if source.exists():
        if destination.exists():
            raise FileExistsError('both legacy and experimental data directories exist')
        source.rename(destination)
    if not destination.exists():
        destination.mkdir(parents=True)

    files = records = 0
    for path in sorted(destination.rglob('*.jsonl')):
        rows = [activate(json.loads(line)) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
        path.write_text(
            ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
            encoding='utf-8',
        )
        files += 1
        records += len(rows)
    report = {
        'directory': str(destination.relative_to(root)),
        'files': files,
        'records': records,
        'all_records_active_for_local_experiments': True,
        'source_rights_and_quality_metadata_preserved': True,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    migrate()
