#!/usr/bin/env python3
"""Build leakage-checked text, ASR, TTS, and evaluation candidate splits."""

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SOURCE = ROOT / 'data/processed/model_ready/segments/all_segments.jsonl'
AUDIO_SOURCE = ROOT / 'data/processed/model_ready/language_quality/audio_supervised.jsonl'
OUT = ROOT / 'data/processed/model_ready/splits'
SPLITS = ('train', 'validation', 'test')
PLACEHOLDER_SPEAKERS = {'', 'na', 'n/a', 'none', 'null', 'unknown', 'unidentified'}


def read_jsonl(path):
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows)
    path.write_text(payload, encoding='utf-8')
    return {'records': len(rows), 'sha256': hashlib.sha256(payload.encode()).hexdigest()}


def identified_speaker(row):
    return str(row.get('speaker_id') or '').strip().casefold() not in PLACEHOLDER_SPEAKERS


def audio_exclusion_reason(row):
    if not identified_speaker(row):
        return 'unidentified_speaker'
    language = row.get('language_quality', {})
    if (
        language.get('status') != 'garhwali_candidate'
        or language.get('review_required')
        or row.get('transcript_review_flags')
        or not str(row.get('asr_target_clean') or '').strip()
    ):
        return 'transcript_or_language_review'
    if (
        not row.get('recommended_for_supervised_training', False)
        or not row.get('audio_quality', {}).get('readable', False)
        or row.get('training_quality_flags')
    ):
        return 'audio_quality_review'
    return None


def build_splits(text_path=TEXT_SOURCE, audio_path=AUDIO_SOURCE, output_dir=OUT):
    text_rows = sorted(read_jsonl(text_path), key=lambda row: row['segment_sha256'])
    audio_rows = sorted(read_jsonl(audio_path), key=lambda row: row['audio_sha256'])

    text_hash_splits = defaultdict(set)
    for row in text_rows:
        text_hash_splits[row['segment_sha256']].add(row['split'])
    if any(len(splits) > 1 for splits in text_hash_splits.values()):
        raise ValueError('text segment crosses splits')

    excluded = Counter()
    strict_audio = []
    for row in audio_rows:
        reason = audio_exclusion_reason(row)
        if reason:
            excluded[reason] += 1
        else:
            strict_audio.append(row)

    speaker_splits = defaultdict(set)
    for row in strict_audio:
        speaker_splits[row['speaker_id']].add(row['split'])
    if any(len(splits) > 1 for splits in speaker_splits.values()):
        raise ValueError('speaker crosses splits')

    artifacts = {}
    text_counts = Counter()
    audio_counts = Counter()
    audio_hours = Counter()
    for split in SPLITS:
        split_text = [row for row in text_rows if row['split'] == split]
        split_audio = [row for row in strict_audio if row['split'] == split]
        text_counts[split] = len(split_text)
        audio_counts[split] = len(split_audio)
        audio_hours[split] = round(sum(row.get('duration_seconds', 0) for row in split_audio) / 3600, 6)
        artifacts[f'text/{split}.jsonl'] = write_jsonl(output_dir / 'text' / f'{split}.jsonl', split_text)
        artifacts[f'asr/{split}.jsonl'] = write_jsonl(output_dir / 'asr' / f'{split}.jsonl', split_audio)
        artifacts[f'tts/{split}.jsonl'] = write_jsonl(output_dir / 'tts' / f'{split}.jsonl', split_audio)

    text_evaluation = [
        {**row, 'review_status': 'pending_native_review'}
        for row in text_rows
        if row['split'] == 'test' and not row.get('quality_flags')
    ]
    asr_evaluation = [
        {**row, 'review_status': 'pending_native_review'}
        for row in strict_audio
        if row['split'] == 'test'
    ]
    artifacts['evaluation/text_candidate.jsonl'] = write_jsonl(
        output_dir / 'evaluation/text_candidate.jsonl', text_evaluation
    )
    artifacts['evaluation/asr_candidate.jsonl'] = write_jsonl(
        output_dir / 'evaluation/asr_candidate.jsonl', asr_evaluation
    )

    report = {
        'release_id': 'garhwali-splits-candidate-2026-09-10',
        'release_status': 'candidate_pending_native_review',
        'text': {'records': dict(sorted(text_counts.items()))},
        'asr_strict': {
            'records': dict(sorted(audio_counts.items())),
            'hours': dict(sorted(audio_hours.items())),
            'identified_speakers': len(speaker_splits),
        },
        'tts_candidate': {
            'records': dict(sorted(audio_counts.items())),
            'hours': dict(sorted(audio_hours.items())),
            'identified_speakers': len(speaker_splits),
        },
        'evaluation_candidates': {
            'text_records': len(text_evaluation),
            'asr_records': len(asr_evaluation),
            'review_status': 'pending_native_review',
        },
        'excluded_audio': dict(sorted(excluded.items())),
        'leakage_checks': {
            'text_hash_cross_split': 0,
            'identified_speaker_cross_split': 0,
        },
        'artifacts': dict(sorted(artifacts.items())),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    print(json.dumps(build_splits(), ensure_ascii=False, indent=2, sort_keys=True))
