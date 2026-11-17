#!/usr/bin/env python3
"""Explain why text validation/test fall short of 5%: read-only diagnostics.

Prints JSON with:
- the upstream document-level split ratios (parent_split, per document);
- the upstream chained components from segment_text_corpus (largest one);
- what upstream would look like if junk/boilerplate segments did not link;
- the largest downstream duplicate component, what links it, and how it
  breaks apart without each kind of edge.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))

from garhwali_lab.io import read_jsonl  # noqa: E402
import build_dataset_splits as bds  # noqa: E402


class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, item):
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, left, right):
        left, right = self.find(left), self.find(right)
        if left == right:
            return False
        self.parent[max(left, right)] = min(left, right)
        return True

    def groups(self):
        out = defaultdict(list)
        for item in list(self.parent):
            out[self.find(item)].append(item)
        return out


def ratios(counter):
    total = sum(counter.values()) or 1
    return {key: [value, round(100 * value / total, 2)] for key, value in sorted(counter.items())}


def upstream_view(rows, exempt):
    doc_split = {}
    doc_segments = Counter()
    for row in rows:
        for parent in row.get('parents', []):
            doc = parent['text_sha256']
            doc_split.setdefault(doc, parent.get('parent_split'))
            doc_segments[doc] += 1

    def components(skip):
        uf = UnionFind()
        for doc in doc_split:
            uf.find(doc)
        for row in rows:
            if row['segment_sha256'] in skip:
                continue
            docs = sorted({p['text_sha256'] for p in row.get('parents', [])})
            for doc in docs[1:]:
                uf.union(docs[0], doc)
        return uf.groups()

    def majority_split_segments(groups):
        doc_assigned = {}
        for docs in groups.values():
            counts = Counter(doc_split[d] for d in docs)
            top = max(counts.values())
            choice = sorted(s for s, c in counts.items() if c == top)[0]
            for d in docs:
                doc_assigned[d] = choice
        return Counter(doc_assigned[row['parents'][0]['text_sha256']] for row in rows if row.get('parents'))

    current = components(set())
    largest = max(current.values(), key=len)
    relinked = components(exempt)
    largest_relinked = max(relinked.values(), key=len)
    return {
        'documents': len(doc_split),
        'document_parent_split_ratio': ratios(Counter(doc_split.values())),
        'segments_by_parent_split_of_first_parent': ratios(Counter(
            row['parents'][0].get('parent_split') for row in rows if row.get('parents'))),
        'segment_split_field_ratio': ratios(Counter(row['split'] for row in rows)),
        'current_chained': {
            'components': len(current),
            'largest_component_documents': len(largest),
            'largest_component_segments': sum(doc_segments[d] for d in largest),
            'largest_component_parent_splits': ratios(Counter(doc_split[d] for d in largest)),
        },
        'if_junk_segments_do_not_link': {
            'components': len(relinked),
            'largest_component_documents': len(largest_relinked),
            'largest_component_segments': sum(doc_segments[d] for d in largest_relinked),
            'segment_split_ratio_with_majority_rule': ratios(majority_split_segments(relinked)),
        },
    }


def downstream_view(rows, semantic_path):
    by_id = {row['segment_sha256']: row for row in rows}
    normalized_groups, key_documents, exempt = bds.link_exempt_segments(rows)

    doc_edges, norm_edges, sem_edges = [], [], []
    doc_members = defaultdict(list)
    for identity, row in by_id.items():
        if identity in exempt:
            continue
        for parent in row.get('parents', []):
            if parent.get('text_sha256'):
                doc_members[str(parent['text_sha256'])].append(identity)
    for members in doc_members.values():
        doc_edges += [(members[0], other) for other in members[1:]]
    for key, members in normalized_groups.items():
        if len(members) < 2 or len(key) < bds.MIN_LINK_KEY_CHARS:
            continue
        if len(key_documents[key]) > bds.MAX_LINK_KEY_DOCUMENTS:
            continue
        norm_edges += [(members[0], other) for other in members[1:]]
    semantic_path = Path(semantic_path)
    if semantic_path.exists():
        for edge in read_jsonl(semantic_path):
            if edge.get('refined_decision') not in {'supported_candidate', 'high_confidence_near_duplicate'}:
                continue
            left, right = edge.get('left_segment_sha256'), edge.get('right_segment_sha256')
            if left in by_id and right in by_id:
                sem_edges.append((left, right))

    def build(kinds):
        uf = UnionFind()
        for identity in by_id:
            uf.find(identity)
        merges = Counter()
        for name, edges in kinds:
            for left, right in edges:
                if uf.union(left, right):
                    merges[name] += 1
        return uf, merges

    all_kinds = [('document', doc_edges), ('normalized', norm_edges), ('semantic', sem_edges)]
    uf, _ = build(all_kinds)
    groups = uf.groups()
    sizes = sorted((len(g) for g in groups.values()), reverse=True)
    largest = set(max(groups.values(), key=len))

    # Bridging merges inside the largest component, counted per edge kind
    # when documents are linked first.
    _, merges = build([(n, [(a, b) for a, b in e if a in largest]) for n, e in all_kinds])

    def largest_without(skip):
        sub, _ = build([(n, [(a, b) for a, b in e if a in largest and b in largest])
                        for n, e in all_kinds if n != skip])
        return sorted((len(g) for g in sub.groups().values() if set(g) & largest), reverse=True)[:5]

    docs = Counter()
    doc_sources = {}
    for identity in largest:
        for parent in by_id[identity].get('parents', []):
            doc = parent.get('text_sha256')
            docs[doc] += 1
            prov = parent.get('provenance') or []
            if doc not in doc_sources and prov:
                first = prov[0] if isinstance(prov, list) else prov
                doc_sources[doc] = (first.get('source_path') or first.get('source') or first.get('path')
                                    if isinstance(first, dict) else str(first))
    upstream_split_of_largest = Counter(by_id[i]['split'] for i in largest)
    samples = sorted(largest)[:5]
    max_held_out = max(bds.MIN_HELD_OUT_COMPONENT_LIMIT, int(len(by_id) * bds.MAX_HELD_OUT_COMPONENT_SHARE))

    # Where held-out loss comes from: components that keep an inherited split.
    inherited = Counter()
    hashed = Counter()
    for root, members in groups.items():
        splits = {by_id[m]['split'] for m in members}
        if len(members) > max_held_out:
            inherited['oversized_to_train'] += len(members)
        elif len(splits) == 1:
            inherited[next(iter(splits))] += len(members)
        else:
            hashed[bds.split_for_hash(root)] += len(members)
    if_hash_all = Counter()
    for root, members in groups.items():
        if len(members) > max_held_out:
            if_hash_all['train'] += len(members)
        else:
            if_hash_all[bds.split_for_hash(root)] += len(members)

    return {
        'segments': len(by_id),
        'exempt_segments': len(exempt),
        'edges': {'document': len(doc_edges), 'normalized': len(norm_edges), 'semantic': len(sem_edges)},
        'components': len(groups),
        'top_component_sizes': sizes[:15],
        'components_over_100': sum(s > 100 for s in sizes),
        'segments_in_components_over_100': sum(s for s in sizes if s > 100),
        'held_out_limit': max_held_out,
        'largest': {
            'segments': len(largest),
            'documents': len(docs),
            'top_documents': [[doc, n, doc_sources.get(doc)] for doc, n in docs.most_common(15)],
            'merges_by_edge_kind': dict(merges),
            'top5_pieces_without_document_edges': largest_without('document'),
            'top5_pieces_without_normalized_edges': largest_without('normalized'),
            'top5_pieces_without_semantic_edges': largest_without('semantic'),
            'upstream_split_field': ratios(upstream_split_of_largest),
            'sample_texts': [by_id[i].get('text', '')[:120] for i in samples],
        },
        'segments_keeping_inherited_split': ratios(inherited),
        'segments_hash_assigned': ratios(hashed),
        'if_every_component_were_hash_assigned': ratios(if_hash_all),
    }


def main():
    rows = sorted(read_jsonl(bds.TEXT_SOURCE), key=lambda row: row['segment_sha256'])
    _, _, exempt = bds.link_exempt_segments(rows)
    report = {
        'upstream': upstream_view(rows, exempt),
        'downstream': downstream_view(rows, bds.SEMANTIC_EDGES),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
