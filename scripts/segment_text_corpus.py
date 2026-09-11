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


def assign_document_aware_splits(records):
    """Keep every document connected by a shared segment in one split."""
    parents = {}
    original_splits = {}

    def find(document):
        parents.setdefault(document, document)
        while parents[document] != document:
            parents[document] = parents[parents[document]]
            document = parents[document]
        return document

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root == right_root:
            return
        first, second = sorted((left_root, right_root))
        parents[second] = first

    for row in records:
        documents = sorted({parent['text_sha256'] for parent in row['parents']})
        for parent in row['parents']:
            original_splits.setdefault(parent['text_sha256'], parent['parent_split'])
        for document in documents:
            find(document)
        for document in documents[1:]:
            union(documents[0], document)

    components = {}
    for document in sorted(parents):
        components.setdefault(find(document), []).append(document)

    document_metadata = {}
    for documents in components.values():
        component_sha256 = hashlib.sha256('\0'.join(documents).encode()).hexdigest()
        split_counts = Counter(original_splits[document] for document in documents)
        largest_count = max(split_counts.values())
        candidate_splits = {split for split, count in split_counts.items() if count == largest_count}
        first_document_split = original_splits[documents[0]]
        component_split = (
            first_document_split
            if first_document_split in candidate_splits
            else sorted(candidate_splits)[0]
        )
        for document in documents:
            document_metadata[document] = {
                'text_sha256': document,
                'component_sha256': component_sha256,
                'component_document_count': len(documents),
                'split': component_split,
            }

    assigned = []
    for source_row in records:
        row = dict(source_row)
        row['parents'] = [
            {**parent, 'document_split': document_metadata[parent['text_sha256']]['split']}
            for parent in source_row['parents']
        ]
        component = document_metadata[row['parents'][0]['text_sha256']]
        row['component_sha256'] = component['component_sha256']
        row['split'] = component['split']
        assigned.append(row)

    documents = [document_metadata[key] for key in sorted(document_metadata)]
    return assigned, documents


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
    parent_split_conflicts = sum(len(row['parent_splits']) > 1 for row in records)
    records, documents = assign_document_aware_splits(records)
    (OUT/'all_segments.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records),encoding='utf-8')
    (OUT/'document_splits.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in documents),encoding='utf-8')
    for split in ('train', 'validation', 'test'):
        split_records = [row for row in records if row['split'] == split]
        (OUT/f'{split}.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in split_records),encoding='utf-8')
    document_split_by_hash = {row['text_sha256']: row['split'] for row in documents}
    report = {**totals,'unique_segments':len(records),'duplicate_segment_occurrences':totals['source_segments']-len(records),
              'quality_flags':dict(flags),
              'provisional_segment_split_records':dict(Counter(r['provisional_segment_split'] for r in records)),
              'parent_split_conflict_segments':parent_split_conflicts,
              'document_components':len({row['component_sha256'] for row in documents}),
              'document_split_records':dict(Counter(row['split'] for row in documents)),
              'segment_split_records':dict(Counter(row['split'] for row in records)),
              'documents_remapped_from_provisional_split':sum(
                  document_split_by_hash[parent['text_sha256']] != parent['parent_split']
                  for row in records for parent in row['parents']
                  if parent['segment_index'] == 0
              ),
              'remaining_cross_split_segments':sum(
                  len({parent['document_split'] for parent in row['parents']}) > 1
                  for row in records
              ),
              'split_note':'Connected documents sharing any exact segment receive one deterministic component split.'}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))


if __name__=='__main__': main()
