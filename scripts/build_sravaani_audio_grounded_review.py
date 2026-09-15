#!/usr/bin/env python3
"""Attach waveform and calibrated model-score evidence to unresolved ASR drafts."""

from __future__ import annotations

import hashlib
import json
import math
import wave
from array import array
from collections import Counter
from pathlib import Path

from asr_metrics import score


ROOT = Path(__file__).resolve().parents[1]
ADJUDICATION = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_adjudication.jsonl'
WHISPER_V02_SCORES = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_audio_scored.jsonl'
CALIBRATION_MANIFEST = ROOT / 'data/processed/evaluation/asr/audio_score_calibration_manifest.jsonl'
WHISPER_V01_CALIBRATION = ROOT / 'data/processed/evaluation/asr/whisper_v0.1_audio_scores.jsonl'
WHISPER_V02_CALIBRATION = ROOT / 'data/processed/evaluation/asr/whisper_v0.2_audio_scores.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_audio_grounded_review.jsonl'
REVIEW = ROOT / 'data/processed/review/sravaani_recovery_audio_grounded_review.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_audio_grounded_review_report.json'


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def percentile(sorted_values, value):
    if not sorted_values:
        return None
    return sum(item <= value for item in sorted_values) / len(sorted_values)


def pearson(pairs):
    if len(pairs) < 2:
        return None
    x_mean = sum(x for x, _ in pairs) / len(pairs)
    y_mean = sum(y for _, y in pairs) / len(pairs)
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    x_scale = math.sqrt(sum((x - x_mean) ** 2 for x, _ in pairs))
    y_scale = math.sqrt(sum((y - y_mean) ** 2 for _, y in pairs))
    return numerator / (x_scale * y_scale) if x_scale and y_scale else None


def calibration(rows, references):
    pairs = []
    exact_hashes = set()
    for row in rows:
        reference = references[row['audio_sha256']]
        metrics = score(reference, row.get('machine_transcript', ''))
        pairs.append((row['token_confidence_uncalibrated'], metrics['cer']))
        exact_hashes.add(row['audio_sha256'])
    values = sorted(value for value, _ in pairs)
    bins = []
    for low, high in ((0.0, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 1.01)):
        selected = [cer for value, cer in pairs if low <= value < high]
        if selected:
            bins.append({
                'minimum_score': low,
                'maximum_score_exclusive': high,
                'records': len(selected),
                'mean_row_cer': round(sum(selected) / len(selected), 6),
            })
    return {
        'records': len(rows),
        'unique_audio_hashes': len(exact_hashes),
        'confidence_to_cer_pearson': round(pearson(pairs), 6),
        'score_values': values,
        'empirical_bins': bins,
        'scope': 'review_ranking_only_not_accuracy_probability',
    }


def waveform_evidence(path, frame_samples=320):
    with wave.open(str(path), 'rb') as source:
        channels = source.getnchannels()
        width = source.getsampwidth()
        sample_rate = source.getframerate()
        samples = array('h')
        samples.frombytes(source.readframes(source.getnframes()))
    if (channels, width, sample_rate) != (1, 2, 16000):
        raise ValueError(f'expected mono 16-bit 16kHz PCM: {path}')
    scale = 32768.0
    frame_db = []
    for offset in range(0, len(samples), frame_samples):
        frame = samples[offset:offset + frame_samples]
        if not frame:
            continue
        rms = math.sqrt(sum(value * value for value in frame) / len(frame)) / scale
        frame_db.append(20 * math.log10(max(rms, 1e-8)))
    ordered = sorted(frame_db)
    noise_floor = ordered[max(0, int(0.1 * (len(ordered) - 1)))] if ordered else -160.0
    activity_threshold = max(-50.0, min(-25.0, noise_floor + 10.0))
    active = [value >= activity_threshold for value in frame_db]
    first = next((index for index, value in enumerate(active) if value), len(active))
    last = next(
        (index for index, value in enumerate(reversed(active)) if value), len(active)
    )
    overall_rms = math.sqrt(
        sum(value * value for value in samples) / max(1, len(samples))
    ) / scale
    return {
        'sample_rate_hz': sample_rate,
        'duration_seconds': round(len(samples) / sample_rate, 6),
        'overall_rms_dbfs': round(20 * math.log10(max(overall_rms, 1e-8)), 3),
        'energy_noise_floor_dbfs': round(noise_floor, 3),
        'energy_activity_threshold_dbfs': round(activity_threshold, 3),
        'energy_active_frame_share': round(sum(active) / max(1, len(active)), 6),
        'leading_inactive_seconds': round(first * frame_samples / sample_rate, 3),
        'trailing_inactive_seconds': round(last * frame_samples / sample_rate, 3),
        'zero_sample_share': round(sum(value == 0 for value in samples) / max(1, len(samples)), 6),
        'clipped_sample_share': round(
            sum(abs(value) >= 32767 for value in samples) / max(1, len(samples)), 6
        ),
        'interpretation': 'energy_activity_is_not_speech_or_language_ground_truth',
    }


def review_category(flags, exact_three_model_match):
    flags = set(flags)
    if 'empty_transcript' in flags:
        return 'empty_output_requires_new_transcription'
    if 'decoding_replacement_character' in flags:
        return 'decoding_corruption_requires_listening'
    if flags & {'repeated_token_loop', 'implausibly_long_for_duration'}:
        return 'decoder_loop_requires_listening'
    if flags == {'frequent_identical_hypothesis'} and exact_three_model_match:
        return 'common_short_exact_consensus_requires_spot_check'
    return 'unresolved_audio_review'


def build_row(row, v02_score, v01_calibration, v02_calibration):
    candidates = {item['model']: item['transcript'] for item in row['candidates']}
    v02_text = candidates['whisper-tiny-garhwali-v0.2']
    if v02_score.get('machine_transcript', '') != v02_text:
        raise ValueError(f"Whisper v0.2 re-decode changed for {row['audio_sha256']}")
    transcripts = set(candidates.values())
    exact_three = len(transcripts) == 1
    v01_score = row['whisper_v0.1_token_confidence_uncalibrated']
    v02_value = v02_score['token_confidence_uncalibrated']
    waveform = waveform_evidence(ROOT / row['local_audio_path'])
    category = review_category(row['proposed_machine_transcript_flags'], exact_three)
    priority = row['review_priority']
    if category == 'empty_output_requires_new_transcription':
        priority += 40
    elif category in {'decoding_corruption_requires_listening', 'decoder_loop_requires_listening'}:
        priority += 25
    if waveform['energy_active_frame_share'] < 0.1:
        priority += 10
    return {
        **row,
        'audio_grounded_evidence': {
            'waveform': waveform,
            'whisper_v0.1': {
                'token_confidence_uncalibrated': v01_score,
                'calibration_percentile': round(
                    percentile(v01_calibration['score_values'], v01_score), 6
                ),
            },
            'whisper_v0.2': {
                'token_confidence_uncalibrated': v02_value,
                'calibration_percentile': round(
                    percentile(v02_calibration['score_values'], v02_value), 6
                ),
                'exact_redecode_match': True,
            },
            'raw_scores_are_accuracy_probabilities': False,
        },
        'audio_review_category': category,
        'audio_review_priority': round(priority, 3),
        'machine_audio_review_complete': True,
        'human_listening_review_required': True,
        'automatic_correction': False,
        'human_reference_available': False,
        'supervised_training_eligible': False,
        'recommended_for_machine_label_training': False,
        'original_transcript_preserved': True,
    }


def run():
    adjudication = [
        row for row in read_jsonl(ADJUDICATION)
        if row['evidence_status'] == 'unresolved_structural_risk'
    ]
    v02_rows = read_jsonl(WHISPER_V02_SCORES)
    v02_by_hash = {row['audio_sha256']: row for row in v02_rows}
    if len(v02_by_hash) != len(v02_rows):
        raise ValueError('Whisper v0.2 score hashes are not unique')
    missing = {row['audio_sha256'] for row in adjudication} - set(v02_by_hash)
    if missing:
        raise ValueError(f'Audio score evidence is incomplete: {len(missing)} missing')
    manifest = {
        row['audio_sha256']: row['asr_target_clean']
        for row in read_jsonl(CALIBRATION_MANIFEST)
    }
    v01_calibration = calibration(read_jsonl(WHISPER_V01_CALIBRATION), manifest)
    v02_calibration = calibration(read_jsonl(WHISPER_V02_CALIBRATION), manifest)
    rows = [
        build_row(row, v02_by_hash[row['audio_sha256']], v01_calibration, v02_calibration)
        for row in adjudication
    ]
    rows.sort(key=lambda row: (-row['audio_review_priority'], row['audio_sha256']))
    write_jsonl(OUTPUT, sorted(rows, key=lambda row: row['audio_sha256']))
    write_jsonl(REVIEW, rows)
    report = {
        'run_id': 'sravaani-unresolved-audio-grounded-review-v0.1',
        'records': len(rows),
        'unique_audio_hashes': len({row['audio_sha256'] for row in rows}),
        'duration_seconds': round(sum(row['duration_seconds'] for row in rows), 3),
        'review_categories': dict(sorted(Counter(
            row['audio_review_category'] for row in rows
        ).items())),
        'v0.2_exact_redecode_matches': sum(
            row['audio_grounded_evidence']['whisper_v0.2']['exact_redecode_match']
            for row in rows
        ),
        'machine_audio_review_complete': sum(row['machine_audio_review_complete'] for row in rows),
        'human_listening_review_required': sum(row['human_listening_review_required'] for row in rows),
        'automatic_corrections': 0,
        'supervised_training_promotions': 0,
        'recommended_machine_label_training_records': 0,
        'all_originals_preserved': all(row['original_transcript_preserved'] for row in rows),
        'calibration': {
            'whisper_v0.1': {key: value for key, value in v01_calibration.items() if key != 'score_values'},
            'whisper_v0.2': {key: value for key, value in v02_calibration.items() if key != 'score_values'},
        },
        'evidence_limit': (
            'Waveform energy is not speech or language ground truth, raw model scores '
            'are weak review-ranking signals, and no target has a human reference.'
        ),
        'inputs': {
            'adjudication_sha256': sha256_file(ADJUDICATION),
            'whisper_v0.2_scores_sha256': sha256_file(WHISPER_V02_SCORES),
            'whisper_v0.1_calibration_sha256': sha256_file(WHISPER_V01_CALIBRATION),
            'whisper_v0.2_calibration_sha256': sha256_file(WHISPER_V02_CALIBRATION),
        },
        'output': str(OUTPUT.relative_to(ROOT)),
        'review_queue': str(REVIEW.relative_to(ROOT)),
    }
    REPORT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
