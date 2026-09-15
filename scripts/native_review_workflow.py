#!/usr/bin/env python3
"""Build native-review packets and adjudicate independent two-pass decisions."""

import json
import csv
import argparse
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_DIR = ROOT / 'data/processed/native_review/packets'
DECISIONS = ROOT / 'data/review_decisions/native_reviews.jsonl'
RESULTS = ROOT / 'data/processed/native_review/results'
REVIEWED = ROOT / 'data/processed/native_review/reviewed'
TEMPLATES = ROOT / 'data/processed/native_review/templates'
CONSENSUS_FIELDS = ('decision', 'corrected_text', 'language', 'dialect_labels', 'pronunciation')
PACKET_SOURCES = (
    ('text_accuracy', 'data/processed/model_ready/text_quality_v2/review_queue.jsonl', 'text_sha256'),
    ('language_identity', 'data/processed/review/language_identity_review.jsonl', 'text_sha256'),
    ('dialect', 'data/processed/review/dialect_review.jsonl', 'text_sha256'),
    ('lexicon', 'data/processed/model_ready/language_quality/lexicon_candidates.jsonl', 'text_sha256'),
    ('evaluation_text', 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl', 'segment_sha256'),
    ('evaluation_asr', 'data/processed/model_ready/splits/evaluation/asr_candidate.jsonl', 'audio_sha256'),
    ('ocr', 'data/processed/review/text_cleanup_review.jsonl', 'text_sha256'),
    ('transcript', 'data/processed/review/vaani_transcript_review.jsonl', 'audio_sha256'),
    ('transcript', 'data/processed/model_ready/transcripts/supervised_review_model_evidence.jsonl', 'audio_sha256'),
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
        reviewer_notes = {
            row['reviewer_id']: row['notes'] for row in rows if row.get('notes')
        }
        adjudicated.append({
            'review_type': review_type,
            'target_id': target_id,
            'status': 'two_pass_agreement',
            'reviewer_ids': sorted(reviewer_ids),
            'reviewer_notes': reviewer_notes,
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


def review_context(review_type, row):
    if review_type == 'text_accuracy':
        meanings = []
        source_ids = set()
        for provenance in row.get('provenance', []):
            source_ids.add(provenance.get('source_id'))
            metadata = provenance.get('linguistic_metadata') or {}
            values = list(metadata.get('english_alignments') or [])
            if metadata.get('translation'):
                values.append(metadata['translation'])
            for value in values:
                if value and value not in meanings:
                    meanings.append(value)
        priority = row.get('review_priority') or {}
        return {
            'display_text': row.get('release_text') or row.get('text'),
            'aligned_meanings': meanings,
            'source_ids': sorted(value for value in source_ids if value),
            'review_priority': priority.get('label'),
            'review_reasons': priority.get('reasons') or [],
            'decision_options': [
                'accept_source_form', 'correct_text', 'keep_experimental',
                'reject_wrong_language',
            ],
            'source_evidence_is_native_review': False,
        }
    if review_type == 'transcript':
        evidence = row.get('model_evidence') or {}
        return {
            'audio_path': row.get('local_audio_path') or row.get('audio_path'),
            'duration_seconds': row.get('duration_seconds') or row.get('duration'),
            'district': row.get('district'),
            'reference_text': row.get('reference_text') or row.get('transcript'),
            'model_hypotheses': evidence.get('hypotheses') or {},
            'requires_audio_listening': True,
            'decision_options': [
                'accept_reference', 'correct_transcript', 'keep_review',
                'reject_wrong_language',
            ],
        }
    return {}


def _cell(value):
    if value in (None, '', []):
        return ''
    if isinstance(value, list):
        return ' | '.join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def write_review_templates(packet_dir=PACKET_DIR, output_dir=TEMPLATES):
    """Write flat copies that two reviewers can fill independently."""
    fields = (
        'review_type', 'target_id', 'source_text', 'aligned_meanings',
        'source_ids', 'review_priority', 'review_reasons', 'audio_path',
        'duration_seconds', 'district', 'model_hypotheses',
        'decision_options', 'decision', 'corrected_text', 'language',
        'dialect_labels', 'pronunciation', 'notes', 'reviewer_id', 'round',
    )
    counts = {}
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for stale in output_dir.glob('*.csv'):
        stale.unlink()
    for path in sorted(Path(packet_dir).glob('*.jsonl')):
        packets = read_jsonl(path)
        if not packets or not any(packet.get('review_context') for packet in packets):
            continue
        target = output_dir / f'{path.stem}.csv'
        with target.open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for packet in packets:
                context = packet.get('review_context') or {}
                writer.writerow({
                    'review_type': packet['review_type'],
                    'target_id': packet['target_id'],
                    'source_text': _cell(
                        context.get('display_text') or context.get('reference_text')
                    ),
                    'aligned_meanings': _cell(context.get('aligned_meanings')),
                    'source_ids': _cell(context.get('source_ids')),
                    'review_priority': _cell(context.get('review_priority')),
                    'review_reasons': _cell(context.get('review_reasons')),
                    'audio_path': _cell(context.get('audio_path')),
                    'duration_seconds': _cell(context.get('duration_seconds')),
                    'district': _cell(context.get('district')),
                    'model_hypotheses': _cell(context.get('model_hypotheses')),
                    'decision_options': _cell(context.get('decision_options')),
                    'decision': '',
                    'corrected_text': '',
                    'language': '',
                    'dialect_labels': '',
                    'pronunciation': '',
                    'notes': '',
                    'reviewer_id': '',
                    'round': '',
                })
        counts[path.stem] = len(packets)
    report = {
        'template_counts': dict(sorted(counts.items())),
        'required_independent_reviews': 2,
        'instructions': 'Give separate template copies to two reviewers; import completed rows into data/review_decisions/native_reviews.jsonl.',
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def import_review_csv_files(paths, output=DECISIONS):
    """Import completed reviewer copies into the two-pass decision stream."""
    decisions = []
    seen = set()
    for path in map(Path, paths):
        with path.open(encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                if not (row.get('decision') or '').strip():
                    continue
                review_type = (row.get('review_type') or '').strip()
                target_id = (row.get('target_id') or '').strip()
                reviewer_id = (row.get('reviewer_id') or '').strip()
                if not review_type or not target_id or not reviewer_id:
                    raise ValueError(f'Completed decision in {path} lacks review identity')
                try:
                    round_number = int((row.get('round') or '').strip())
                except ValueError as error:
                    raise ValueError(f'Completed decision in {path} has invalid round') from error
                key = (review_type, target_id, reviewer_id)
                if key in seen:
                    raise ValueError(f'Duplicate reviewer decision: {key}')
                seen.add(key)
                decision = {
                    'review_type': review_type,
                    'target_id': target_id,
                    'reviewer_id': reviewer_id,
                    'round': round_number,
                    'decision': row['decision'].strip(),
                }
                for field in CONSENSUS_FIELDS[1:] + ('notes',):
                    value = (row.get(field) or '').strip()
                    if not value:
                        continue
                    decision[field] = (
                        [item.strip() for item in value.split('|') if item.strip()]
                        if field == 'dialect_labels' else value
                    )
                decisions.append(decision)
    decisions.sort(key=lambda row: (
        row['review_type'], row['target_id'], row['reviewer_id'], row['round']
    ))
    write_jsonl(output, decisions)
    return {
        'files': len(paths),
        'decisions': len(decisions),
        'targets': len({(row['review_type'], row['target_id']) for row in decisions}),
        'reviewers': len({row['reviewer_id'] for row in decisions}),
    }


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
                'review_context': review_context(review_type, row),
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


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--import-decisions', nargs='+', metavar='CSV',
        help='Import one or more independently completed review templates before adjudication.',
    )
    args = parser.parse_args(argv)
    packet_report = build_packets()
    template_report = write_review_templates()
    import_report = (
        import_review_csv_files(args.import_decisions)
        if args.import_decisions else None
    )
    decision_report = adjudicate()
    reviewed_report = materialize_reviewed_records()
    print(json.dumps(
        {
            'packets': packet_report,
            'templates': template_report,
            'import': import_report,
            'decisions': decision_report,
            'reviewed': reviewed_report,
        },
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))


if __name__ == '__main__':
    main()
