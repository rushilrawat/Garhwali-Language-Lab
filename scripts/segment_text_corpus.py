#!/usr/bin/env python3
"""Expose sentence-like units from every cleaned text while retaining parents."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'data/processed/model_ready/cleaned/text.jsonl'
OUT = ROOT/'data/processed/model_ready/segments'


def segment(text):
    return [part.strip() for part in re.split(r'(?<=[।!?])\s+|(?<=[^\d]\.)(?:\s+|$)', text) if part.strip()]


def split_for_hash(digest):
    bucket = int(digest[:8], 16) % 1000
    if bucket < 900: return 'train'
    if bucket < 950: return 'validation'
    return 'test'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    groups = {}; totals = Counter(); flags = Counter()
    with SOURCE.open(encoding='utf-8') as source:
        for line in source:
            if not line.strip(): continue
            row = json.loads(line); parts = segment(row['text_model'])
            totals['parent_records'] += 1; totals['source_segments'] += len(parts)
            for index, text in enumerate(parts):
                digest = hashlib.sha256(text.encode()).hexdigest()
                item_flags = []
                if len(text) < 3: item_flags.append('very_short')
                if len(text) > 1000: item_flags.append('very_long')
                if not re.search(r'[\u0900-\u097f]', text): item_flags.append('no_devanagari')
                if digest not in groups:
                    groups[digest] = {'segment_sha256':digest,'text':text,
                                      'provisional_segment_split':split_for_hash(digest),
                                      'quality_flags':item_flags,'parents':[]}
                groups[digest]['parents'].append({'text_sha256':row['text_sha256'],'segment_index':index,
                                                  'parent_split':row['split'],
                                                  'provenance':row.get('provenance',[])})
                flags.update(item_flags)
    records = sorted(groups.values(), key=lambda row: row['segment_sha256'])
    for row in records:
        row['parent_count'] = len(row['parents'])
        row['parent_splits'] = sorted({parent['parent_split'] for parent in row['parents']})
    (OUT/'all_segments.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records),encoding='utf-8')
    report = {**totals,'unique_segments':len(records),'duplicate_segment_occurrences':totals['source_segments']-len(records),
              'quality_flags':dict(flags),
              'provisional_segment_split_records':dict(Counter(r['provisional_segment_split'] for r in records)),
              'parent_split_conflict_segments':sum(len(r['parent_splits']) > 1 for r in records),
              'split_note':'Provisional segment-hash splits prevent exact segment duplication; final document-aware splits remain a later stage.'}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))


if __name__=='__main__': main()
