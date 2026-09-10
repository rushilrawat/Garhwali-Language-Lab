#!/usr/bin/env python3
"""Create a Garhwali-only candidate view from the PahariLI gbm layer."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'quarantine' / 'paharili_gbm.jsonl'
OUTPUT = ROOT / 'data' / 'processed' / 'text' / 'paharili_garhwali.jsonl'

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with SOURCE.open(encoding='utf-8') as src, OUTPUT.open('w', encoding='utf-8') as dst:
        for line in src:
            if not line.strip(): continue
            row = json.loads(line)
            if row.get('iso_639_3') != 'gbm' or row.get('upstream_label') != 'gbm':
                continue
            row['training_eligible'] = True
            row['corpus_layer'] = 'corpus'
            row['usage'] = 'candidate_training_user_approved'
            row['rights_status'] = 'user_approved_for_garhwali_only; retain upstream Apache-2.0 attribution'
            row['quality_flags'] = [f for f in row.get('quality_flags', []) if f != 'possible_modern_scripture_or_blog_text']
            row['quality_flags'].append('user-approved-garhwali-only-promotion')
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    report = {'source': str(SOURCE), 'output': str(OUTPUT), 'promoted_records': count, 'filter': 'iso_639_3=gbm and upstream_label=gbm'}
    (OUTPUT.with_name('paharili_garhwali_report.json')).write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__': main()
