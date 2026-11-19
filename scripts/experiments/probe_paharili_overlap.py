#!/usr/bin/env python3
"""Show which existing release rows share text with a PahariLI record.

Read-only diagnostic: runs the all-data package build with the PahariLI
check wrapped, and prints the matching rows when it fails. Usage:

    python scripts/experiments/probe_paharili_overlap.py --profile all-data \
        --output data/huggingface/garhwali-language-lab-all-data-v0.2.9-local
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import build_huggingface_dataset as builder  # noqa: E402
from garhwali_lab.text import leakage_key  # noqa: E402
from hf_rows import source_record_ids  # noqa: E402

FIELDS = (
    'text', 'release_text', 'text_normalized', 'text_original',
    'transcript', 'asr_target_clean', 'machine_transcript', 'form',
)
original = builder.build_paharili_gbm_rows


def probe(source_rows, existing_rows):
    source_rows = list(source_rows)
    existing_rows = list(existing_rows)
    try:
        return original(source_rows, existing_rows)
    except ValueError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        keys = {}
        for row in source_rows:
            if row.get('iso_639_3') == 'gbm' and row.get('upstream_label') == 'gbm':
                text = str(row.get('text_original') or row.get('text_normalized') or '')
                keys.setdefault(leakage_key(text), []).append(row)
        hits = 0
        for row in existing_rows:
            for field in FIELDS:
                value = row.get(field)
                key = leakage_key(value) if isinstance(value, str) else ''
                if key in keys:
                    ids = sorted(source_record_ids(row))
                    paharili = sorted(r['record_id'] for r in keys[key])
                    if set(paharili) - set(ids):
                        hits += 1
                        print(json.dumps({
                            'paharili_ids': paharili,
                            'paharili_text': keys[key][0].get('text_original'),
                            'matched_field': field,
                            'matched_text': value[:300],
                            'row_keys': sorted(row)[:40],
                            'row_id': row.get('id') or row.get('record_id') or row.get('segment_sha256'),
                            'row_split': row.get('split'),
                            'row_source_ids': ids[:10],
                            'row_config_hint': row.get('config') or row.get('view') or row.get('source_dataset'),
                        }, ensure_ascii=False))
        print(f'{hits} unpreserved matches', file=sys.stderr)
        raise SystemExit(1)


builder.build_paharili_gbm_rows = probe
builder.main()
