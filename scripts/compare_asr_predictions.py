#!/usr/bin/env python3
"""Compare ASR prediction files on one exact manifest without exposing text."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from asr_metrics import normalize, score


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def prediction_key(row, label):
    record_id = row.get('record_id')
    audio_hash = row.get('audio_sha256')
    if record_id is None or not audio_hash:
        raise ValueError(f'{label} row is missing record_id or audio_sha256')
    return str(record_id), str(audio_hash)


def index_rows(rows, label):
    indexed = {}
    for row in rows:
        key = prediction_key(row, label)
        if key in indexed:
            raise ValueError(f'duplicate {label} prediction key: {key}')
        indexed[key] = row
    return indexed


def aggregate(references, hypotheses):
    scores = [score(reference, hypothesis) for reference, hypothesis in zip(references, hypotheses)]
    totals = {
        field: sum(row[field] for row in scores)
        for field in (
            'word_errors', 'reference_words',
            'character_errors', 'reference_characters',
        )
    }
    return {
        **totals,
        'records': len(scores),
        'wer': totals['word_errors'] / max(1, totals['reference_words']),
        'cer': totals['character_errors'] / max(1, totals['reference_characters']),
    }, scores


def paired_summary(rows):
    references = [reference for reference, _, _ in rows]
    baseline_hypotheses = [baseline for _, baseline, _ in rows]
    candidate_hypotheses = [candidate for _, _, candidate in rows]
    baseline, _ = aggregate(references, baseline_hypotheses)
    candidate, _ = aggregate(references, candidate_hypotheses)
    return {
        'records': len(rows),
        'baseline': baseline,
        'candidate': candidate,
        'delta_percentage_points': {
            'wer': round((candidate['wer'] - baseline['wer']) * 100, 6),
            'cer': round((candidate['cer'] - baseline['cer']) * 100, 6),
        },
    }


def duration_bucket(row):
    duration = row.get('duration_seconds')
    if duration is None:
        return 'unknown'
    duration = float(duration)
    return '<3s' if duration < 3 else '3-8s' if duration < 8 else '8-15s' if duration < 15 else '15s+'


def reference_length_bucket(reference):
    word_count = len(normalize(reference).split())
    return '1-10' if word_count <= 10 else '11-25' if word_count <= 25 else '26+'


def compare_predictions(
    manifest_rows,
    baseline_rows,
    candidate_rows,
    baseline_field='hypothesis',
    candidate_field='prediction',
):
    manifest = index_rows(manifest_rows, 'manifest')
    baseline = index_rows(baseline_rows, 'baseline')
    candidate = index_rows(candidate_rows, 'candidate')
    expected = set(manifest)
    if set(candidate) != expected:
        raise ValueError('candidate predictions do not exactly match the evaluation manifest')
    if not expected <= set(baseline):
        raise ValueError('baseline predictions do not cover the evaluation manifest')

    ordered_keys = sorted(expected)
    references = []
    baseline_hypotheses = []
    candidate_hypotheses = []
    for key in ordered_keys:
        manifest_row = manifest[key]
        reference = manifest_row['asr_target_clean']
        base = baseline[key]
        proposed = candidate[key]
        if base.get('reference') != reference or proposed.get('reference') != reference:
            raise ValueError(f'reference mismatch for record {key[0]}')
        if baseline_field not in base or candidate_field not in proposed:
            raise ValueError(f'missing prediction field for record {key[0]}')
        references.append(reference)
        baseline_hypotheses.append(base[baseline_field])
        candidate_hypotheses.append(proposed[candidate_field])

    baseline_metrics, baseline_scores = aggregate(references, baseline_hypotheses)
    candidate_metrics, candidate_scores = aggregate(references, candidate_hypotheses)
    directions = Counter()
    speaker_rows = defaultdict(list)
    duration_rows = defaultdict(list)
    reference_length_rows = defaultdict(list)
    for key, manifest_row, base_score, candidate_score in zip(
        ordered_keys, (manifest[item] for item in ordered_keys),
        baseline_scores, candidate_scores,
    ):
        base_prediction = baseline[key]
        candidate_prediction = candidate[key]
        for metric, error_field in (
            ('wer', 'word_errors'), ('cer', 'character_errors'),
        ):
            base_errors = base_score[error_field]
            candidate_errors = candidate_score[error_field]
            direction = (
                'better_rows' if candidate_errors < base_errors
                else 'worse_rows' if candidate_errors > base_errors
                else 'equal_rows'
            )
            directions[f'{metric}_{direction}'] += 1
        speaker = manifest_row.get('speaker_id')
        if speaker is not None and str(speaker).strip().casefold() not in {
            '', 'na', 'unknown', 'null', 'none',
        }:
            speaker_rows[str(speaker)].append((manifest_row, base_prediction, candidate_prediction))
        paired = (
            manifest_row['asr_target_clean'],
            base_prediction[baseline_field],
            candidate_prediction[candidate_field],
        )
        duration_rows[duration_bucket(manifest_row)].append(paired)
        reference_length_rows[reference_length_bucket(manifest_row['asr_target_clean'])].append(paired)

    by_speaker = {}
    for speaker, rows in sorted(speaker_rows.items()):
        speaker_references = [row['asr_target_clean'] for row, _, _ in rows]
        base_hypotheses = [base[baseline_field] for _, base, _ in rows]
        candidate_hypotheses = [proposed[candidate_field] for _, _, proposed in rows]
        base_metrics, _ = aggregate(speaker_references, base_hypotheses)
        candidate_speaker_metrics, _ = aggregate(speaker_references, candidate_hypotheses)
        by_speaker[speaker] = {
            'records': len(rows),
            'baseline': base_metrics,
            'candidate': candidate_speaker_metrics,
        }

    return {
        'status': 'complete',
        'matched_records': len(ordered_keys),
        'baseline': baseline_metrics,
        'candidate': candidate_metrics,
        'delta_percentage_points': {
            'wer': round((candidate_metrics['wer'] - baseline_metrics['wer']) * 100, 6),
            'cer': round((candidate_metrics['cer'] - baseline_metrics['cer']) * 100, 6),
        },
        'row_directions': {
            name: directions[name]
            for name in (
                'wer_better_rows', 'wer_worse_rows', 'wer_equal_rows',
                'cer_better_rows', 'cer_worse_rows', 'cer_equal_rows',
            )
        },
        'by_duration': {
            bucket: paired_summary(rows)
            for bucket, rows in sorted(duration_rows.items())
        },
        'by_reference_length': {
            bucket: paired_summary(rows)
            for bucket, rows in sorted(reference_length_rows.items())
        },
        'by_speaker': by_speaker,
    }


def compare_files(
    manifest_path,
    baseline_path,
    candidate_path,
    baseline_field='hypothesis',
    candidate_field='prediction',
):
    report = compare_predictions(
        read_jsonl(manifest_path), read_jsonl(baseline_path), read_jsonl(candidate_path),
        baseline_field, candidate_field,
    )
    report['input_sha256'] = {
        'manifest': sha256_file(manifest_path),
        'baseline_predictions': sha256_file(baseline_path),
        'candidate_predictions': sha256_file(candidate_path),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--baseline-field', default='hypothesis')
    parser.add_argument('--candidate-field', default='prediction')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = compare_files(
        args.manifest, args.baseline, args.candidate,
        args.baseline_field, args.candidate_field,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    else:
        print(rendered, end='')


if __name__ == '__main__':
    main()
