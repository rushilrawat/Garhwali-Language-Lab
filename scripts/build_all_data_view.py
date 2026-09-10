#!/usr/bin/env python3
"""Materialize an opt-in view containing every canonical Garhwali text row."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed/text/canonical.jsonl'
OUTPUT = ROOT / 'data/processed/text/all_garhwali.jsonl'

def main():
    count = 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(encoding='utf-8') as src, OUTPUT.open('w', encoding='utf-8') as dst:
        for line in src:
            if not line.strip(): continue
            row = json.loads(line)
            row['candidate_use'] = 'all_data_experimental'
            row['includes_quarantine_or_restricted'] = any(
                p.get('layer') in {'quarantine', 'restricted'} for p in row.get('provenance', [])
            )
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    report = {'source': str(SOURCE), 'output': str(OUTPUT), 'records': count, 'includes_all_canonical_rows': True}
    (OUTPUT.with_name('all_garhwali_report.json')).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
