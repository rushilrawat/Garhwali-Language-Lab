#!/usr/bin/env python3
"""Build native-review packets and adjudicate independent two-pass decisions."""

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / 'data/processed/native_review/packets'
DECISIONS = ROOT / 'data/review_decisions/native_reviews.jsonl'
RESULTS = ROOT / 'data/processed/native_review/results'
REVIEWED = ROOT / 'data/processed/native_review/reviewed'
CONSENSUS_FIELDS = ('decision', 'corrected_text', 'language', 'dialect_labels', 'pronunciation', 'notes')
PACKET_SOURCES = (
    ('language_identity', 'data/processed/review/language_identity_review.jsonl', 'text_sha256'),
    ('dialect', 'data/processed/review/dialect_review.jsonl', 'text_sha256'),
    ('lexicon', 'data/processed/model_ready/language_quality/lexicon_candidates.jsonl', 'text_sha256'),
    ('evaluation_text', 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl', 'segment_sha256'),
    ('evaluation_asr', 'data/processed/model_ready/splits/evaluation/asr_candidate.jsonl', 'audio_sha256'),
    ('ocr', 'data/processed/review/text_cleanup_review.jsonl', 'text_sha256'),
    ('transcript', 'data/processed/review/vaani_transcript_review.jsonl', 'audio_sha256'),
    ('transcript', 'data/processed/model_ready/transcripts/machine_drafts.jsonl', 'audio_sha256'),
)


def read_jsonl(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def consensus_value(row):
    value = {field: row.get(field) for field in CONSENSUS_FIELDS if row.get(field) not in (None, '', [])}
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def adjudicate_rows(decisions):
    groups = defaultdict(list)
    for row in decisions:
        groups[(row['review_type'], row['target_id'])].append(row)

    adjudicated, disagreements, pending = [], [], []
    for (review_type, target_id), rows in sorted(groups.items()):
        reviewer_ids = {row['reviewer_id'] for row in rows}
        base = {'review_type': review_type, 'target_id': target_id, 'reviews': rows}
        if len(reviewer_ids) < 2:
            pending.append({**base, 'status': 'pending_second_review'})
            continue
        values = {consensus_value(row) for row in rows}
        if len(values) != 1:
            disagreements.append({**base, 'status': 'needs_adjudication'})
            continue
        consensus = json.loads(values.pop())
        adjudicated.append({
            'review_type': review_type,
            'target_id': target_id,
            'status': 'two_pass_agreement',
            'reviewer_ids': sorted(reviewer_ids),
            **consensus,
        })
    return {'adjudicated': adjudicated, 'disagreements': disagreements, 'pending': pending}


def adjudicate(decision_path=DECISIONS, output_dir=RESULTS):
    decisions = read_jsonl(decision_path)
    result = adjudicate_rows(decisions)
    write_jsonl(output_dir / 'adjudicated.jsonl', result['adjudicated'])
    write_jsonl(output_dir / 'disagreements.jsonl', result['disagreements'])
    write_jsonl(output_dir / 'pending.jsonl', result['pending'])
    report = {
        'adjudicated': len(result['adjudicated']),
        'decisions': len(decisions),
        'disagreements': len(result['disagreements']),
        'pending_second_review': len(result['pending']),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return report


def materialize_reviewed_records(packet_dir=PACKET_DIR, result_dir=RESULTS, output_dir=REVIEWED):
    """Join adjudicated decisions to immutable source payloads without overwriting them."""
    packets = {}
    for path in sorted(Path(packet_dir).glob('*.jsonl')):
        for row in read_jsonl(path):
            packets[(row['review_type'], row['target_id'])] = row['payload']

    accepted = defaultdict(list)
    rejected = defaultdict(list)
    orphaned = []
    for review in read_jsonl(Path(result_dir) / 'adjudicated.jsonl'):
        key = (review['review_type'], review['target_id'])
        payload = packets.get(key)
        if payload is None:
            orphaned.append(review)
            continue
        record = {
            'review_type': review['review_type'],
            'target_id': review['target_id'],
            'source_payload': payload,
            'review': review,
        }
        corrected_text = review.get('corrected_text')
        source_text = payload.get('text') or payload.get('transcript')
        if corrected_text or source_text:
            record['effective_text'] = corrected_text or source_text
        destination = rejected if review.get('decision') == 'reject' else accepted
        destination[review['review_type']].append(record)

    for review_type, rows in accepted.items():
        write_jsonl(Path(output_dir) / 'accepted' / f'{review_type}.jsonl', rows)
    for review_type, rows in rejected.items():
        write_jsonl(Path(output_dir) / 'rejected' / f'{review_type}.jsonl', rows)
    write_jsonl(Path(output_dir) / 'orphaned_decisions.jsonl', orphaned)
    report = {
        'accepted': sum(map(len, accepted.values())),
        'rejected': sum(map(len, rejected.values())),
        'orphaned_decisions': len(orphaned),
        'review_types': sorted(set(accepted) | set(rejected)),
    }
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    (Path(output_dir) / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return report


def is_ocr_packet(row):
    return any(
        'machine_ocr' in provenance.get('quality_flags', [])
        for provenance in row.get('provenance', [])
    )


def build_packets(root=ROOT, output_dir=PACKET_DIR):
    grouped = defaultdict(dict)
    for review_type, relative, id_field in PACKET_SOURCES:
        rows = read_jsonl(root / relative)
        if review_type == 'ocr':
            rows = [row for row in rows if is_ocr_packet(row)]
        for row in rows:
            grouped[review_type][row[id_field]] = {
                'review_type': review_type,
                'target_id': row[id_field],
                'required_independent_reviews': 2,
                'payload': row,
            }

    counts = {}
    for review_type in sorted(grouped):
        packets = list(grouped[review_type].values())
        packets.sort(key=lambda row: row['target_id'])
        write_jsonl(output_dir / f'{review_type}.jsonl', packets)
        counts[review_type] = len(packets)
    report = {'packet_counts': dict(sorted(counts.items())), 'required_independent_reviews': 2}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    return report


if __name__ == '__main__':
    packet_report = build_packets()
    decision_report = adjudicate()
    reviewed_report = materialize_reviewed_records()
    print(json.dumps(
        {'packets': packet_report, 'decisions': decision_report, 'reviewed': reviewed_report},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))
