"""Create an exact normalized-text overlap report across every ingested layer."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYER_PATHS = {
    'corpus': ROOT / 'corpus',
    'benchmarks': ROOT / 'benchmarks',
    'restricted': ROOT / 'restricted',
    'experimental': ROOT / 'experimental',
    'extracted/historical': ROOT / 'extracted' / 'historical',
}
OUTPUT = ROOT / 'outputs' / 'online-ingestion-2026-09-07' / 'dedup-report.json'


def load_rows():
    rows = []
    for layer, folder in LAYER_PATHS.items():
        for path in sorted(folder.glob('*.jsonl')):
            for line_number, line in enumerate(path.read_text().splitlines(), 1):
                row = json.loads(line)
                text = row.get('text_normalized', '')
                digest = hashlib.sha256(text.encode()).hexdigest()
                rows.append(dict(layer=layer, file=str(path.relative_to(ROOT)),
                                 line=line_number, record_id=row['record_id'],
                                 source_id=row.get('source_id'), text_sha256=digest,
                                 text_length=len(text)))
    return rows


def main():
    rows = load_rows()
    by_text = defaultdict(list)
    for row in rows:
        by_text[row['text_sha256']].append(row)
    by_layer = defaultdict(set)
    by_file = defaultdict(set)
    for row in rows:
        by_layer[row['layer']].add(row['text_sha256'])
        by_file[row['file']].add(row['text_sha256'])
    layer_names = list(LAYER_PATHS)
    pair_overlap = {}
    for index, left in enumerate(layer_names):
        for right in layer_names[index + 1:]:
            pair_overlap[f'{left} <> {right}'] = len(by_layer[left] & by_layer[right])
    duplicate_groups = [group for group in by_text.values() if len(group) > 1]
    duplicate_groups.sort(key=lambda group: (-len(group), group[0]['text_sha256']))
    report = {
        'method': 'exact SHA-256 of each record text_normalized; Unicode normalization was performed by source extractors',
        'total_records': len(rows),
        'unique_normalized_texts': len(by_text),
        'duplicate_rows': len(rows) - len(by_text),
        'layer_counts': Counter(row['layer'] for row in rows),
        'layer_unique_texts': {layer: len(values) for layer, values in by_layer.items()},
        'file_counts': Counter(row['file'] for row in rows),
        'file_unique_texts': {file: len(values) for file, values in by_file.items()},
        'pairwise_unique_text_overlap': pair_overlap,
        'duplicate_group_count': len(duplicate_groups),
        'largest_duplicate_groups': [
            {'text_sha256': group[0]['text_sha256'], 'text_length': group[0]['text_length'],
             'records': [{key: item[key] for key in ('layer', 'file', 'line', 'record_id', 'source_id')}
                         for item in group]}
            for group in duplicate_groups[:100]
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=dict))
    print(json.dumps({key: report[key] for key in
                      ('total_records', 'unique_normalized_texts', 'duplicate_rows',
                       'layer_counts', 'layer_unique_texts', 'pairwise_unique_text_overlap')},
                     ensure_ascii=False, indent=2, default=dict))


if __name__ == '__main__':
    main()
