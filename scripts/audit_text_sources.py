#!/usr/bin/env python3
"""Audit exact-unique text rights and review state by upstream source."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from build_huggingface_dataset import (
    is_public_text_row,
    is_publishable_provenance,
    provenance_items,
)


ROOT = Path(__file__).resolve().parents[1]
QUALITY = ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
REVIEW = ROOT / 'data/processed/model_ready/text_quality_v2/review_queue.jsonl'
OUT = ROOT / 'data/processed/model_ready/text_source_audit'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def source_id(item):
    return item.get('source_id') or 'unknown'


def audit_rows(rows, review_rows):
    tiers = Counter()
    source_records = defaultdict(set)
    source_open = defaultdict(set)
    source_blocked = defaultdict(set)
    source_mixed = defaultdict(set)
    public = rights_pending = mixed = strict_overlap = high_pending = 0

    for row in rows:
        digest = row['text_sha256']
        tier = (row.get('quality_v2') or {}).get('tier') or 'unclassified'
        tiers[tier] += 1
        items = provenance_items(row)
        open_items = [item for item in items if is_publishable_provenance(item)]
        blocked_items = [item for item in items if not is_publishable_provenance(item)]
        public_row = is_public_text_row(row)
        if public_row:
            public += 1
        else:
            rights_pending += 1
        mixed_row = bool(open_items and blocked_items)
        if mixed_row:
            mixed += 1
        if mixed_row and tier == 'strict_gold_candidate':
            strict_overlap += 1
        if not public_row and tier == 'high_quality_rights_pending':
            high_pending += 1

        for item in items:
            key = source_id(item)
            source_records[key].add(digest)
            if is_publishable_provenance(item):
                source_open[key].add(digest)
            else:
                source_blocked[key].add(digest)
            if mixed_row:
                source_mixed[key].add(digest)

    review_priorities = Counter()
    review_sources = Counter()
    review_count = 0
    for row in review_rows:
        review_count += 1
        review_priorities[(row.get('review_priority') or {}).get('label') or 'unclassified'] += 1
        for key in {
            source_id(item) for item in provenance_items(row)
        }:
            review_sources[key] += 1

    all_sources = sorted(source_records)
    summary = {
        key: {
            'records': len(source_records[key]),
            'open_basis_records': len(source_open[key]),
            'blocked_records': len(source_blocked[key]),
            'mixed_rights_overlap_records': len(source_mixed[key]),
        }
        for key in all_sources
    }
    records = sum(tiers.values())
    if public + rights_pending != records:
        raise ValueError('Public and rights-pending counts do not cover every record')
    return {
        'records': records,
        'public_text_records': public,
        'rights_pending_text_records': rights_pending,
        'mixed_rights_exact_duplicate_records': mixed,
        'strict_records_using_open_overlap': strict_overlap,
        'high_quality_rights_pending_records': high_pending,
        'quality_tier_counts': dict(sorted(tiers.items())),
        'review_queue_records': review_count,
        'review_priority_counts': dict(sorted(review_priorities.items())),
        'review_source_counts': dict(sorted(review_sources.items())),
        'source_summary': summary,
        'policy': {
            'exact_duplicate_rights': (
                'An exact-unique text is publishable when at least one retained provenance '
                'record supplies compatible redistribution evidence. Blocked mirror '
                'provenance remains attached and does not revoke the open source grant.'
            ),
            'blocked_only_text': (
                'Text with no publishable provenance remains rights-pending; its identity '
                'and source evidence remain present in the public catalog.'
            ),
            'accuracy': (
                'A source language label or open license is not evidence of native '
                'orthographic, semantic, or transcription accuracy.'
            ),
        },
    }


def main():
    report = audit_rows(read_jsonl(QUALITY), read_jsonl(REVIEW))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
