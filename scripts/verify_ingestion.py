"""Verify immutable snapshots and safety boundaries across every corpus layer."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAYERS = ['corpus', 'benchmarks', 'restricted', 'experimental', 'extracted/historical']


def training_use_is_authorized(row, layer):
    if not row.get('training_eligible', False):
        return True
    return layer in {'restricted', 'experimental'} and row.get('usage') == 'all_data_experimental_user_approved'


def rights_are_documented(row):
    if not row.get('attribution'):
        return False
    if row.get('license_url'):
        return True
    return bool((row.get('source_url') or row.get('source_pdf')) and row.get('rights_status'))


def main():
    snapshots = 0
    for pointer in (ROOT / 'sources' / 'online').rglob('*.metadata.json'):
        info = json.loads(pointer.read_text())
        raw = Path(info['raw_path'])
        if not raw.is_absolute():
            raw = ROOT / raw
        assert raw.exists(), f'missing snapshot: {raw}'
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == info['sha256'], pointer
        snapshots += 1

    counts = {}
    all_ids = set()
    for layer in LAYERS:
        rows = []
        for path in (ROOT / layer).glob('*.jsonl'):
            rows.extend(json.loads(line) for line in path.read_text().splitlines())
        ids = [row['record_id'] for row in rows]
        assert len(ids) == len(set(ids)), f'duplicate ID within {layer}'
        assert not all_ids.intersection(ids), f'duplicate ID across layers: {layer}'
        all_ids.update(ids)
        assert all(training_use_is_authorized(row, layer) for row in rows), layer
        assert all(rights_are_documented(row) for row in rows), layer
        counts[layer] = len(rows)

    uou = [json.loads(line) for line in (ROOT / 'restricted' / 'uou_cgl_pages.jsonl').read_text().splitlines()]
    assert len(uou) == 436
    devanagari = sum('\u0900' <= char <= '\u097f' for row in uou for char in row['text_normalized'])
    characters = sum(len(row['text_normalized']) for row in uou)
    assert devanagari / characters > 0.5, 'UOU OCR is not predominantly Unicode Devanagari'

    madlad = [json.loads(line) for line in
              (ROOT / 'experimental' / 'madlad400_gbm_clean.jsonl').read_text().splitlines()]
    assert len(madlad) == 18
    assert all(row.get('corpus_layer') == 'experimental' for row in madlad)
    assert all(row.get('experimental_training_eligible') for row in madlad)
    assert all('component_rights_review_required' in row.get('quality_flags', [])
               for row in madlad)
    assert all(0 <= row['quality_metrics']['devanagari_share_of_nonspace'] <= 1
               for row in madlad)

    print(json.dumps({'snapshots_verified': snapshots, 'layer_counts': counts,
                      'total_records': len(all_ids), 'uou_devanagari_ratio': round(devanagari / characters, 3)},
                     indent=2))


if __name__ == '__main__':
    main()
