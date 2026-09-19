#!/usr/bin/env python3
"""Build leakage-checked text, ASR, TTS, and evaluation candidate splits."""

import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SOURCE = ROOT / 'data/processed/model_ready/segments/all_segments.jsonl'
AUDIO_SOURCE = ROOT / 'data/processed/model_ready/language_quality/audio_supervised.jsonl'
OUT = ROOT / 'data/processed/model_ready/splits'
SEMANTIC_EDGES = ROOT / (
    'data/processed/evaluation/data_quality/'
    'semantic_duplicates_refined_v0_2/cloud_output/refined_candidates.jsonl'
)
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


def normalized_text_key(text):
    normalized = unicodedata.normalize('NFKC', str(text or '')).casefold()
    return ''.join(char for char in normalized if char.isalnum())


def component_safe_text_splits(rows, semantic_path=SEMANTIC_EDGES):
    """Keep normalized and model-supported near duplicates in one split."""
    by_id = {row['segment_sha256']: dict(row) for row in rows}
    parent = {identity: identity for identity in by_id}

    def find(identity):
        while parent[identity] != identity:
            parent[identity] = parent[parent[identity]]
            identity = parent[identity]
        return identity

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    normalized_groups = defaultdict(list)
    for identity, row in by_id.items():
        key = normalized_text_key(row.get('text'))
        if key:
            normalized_groups[key].append(identity)
    normalized_edges = 0
    for identities in normalized_groups.values():
        for identity in identities[1:]:
            union(identities[0], identity)
            normalized_edges += 1

    semantic_edges = 0
    semantic_path = Path(semantic_path) if semantic_path else None
    if semantic_path and semantic_path.exists():
        for edge in read_jsonl(semantic_path):
            if edge.get('refined_decision') not in {
                'supported_candidate', 'high_confidence_near_duplicate',
            }:
                continue
            left = edge.get('left_segment_sha256')
            right = edge.get('right_segment_sha256')
            if left in by_id and right in by_id:
                union(left, right)
                semantic_edges += 1

    components = defaultdict(list)
    for identity in by_id:
        components[find(identity)].append(identity)
    split_priority = {'train': 0, 'validation': 1, 'test': 2}
    moved = 0
    for root, identities in components.items():
        assigned = min(
            (by_id[identity]['split'] for identity in identities),
            key=split_priority.__getitem__,
        )
        for identity in identities:
            row = by_id[identity]
            if row['split'] != assigned:
                row['original_split'] = row['split']
                row['split'] = assigned
                row['split_assignment'] = 'duplicate_component_isolation'
                moved += 1
            row['duplicate_component_id'] = root
    return list(by_id.values()), {
        'normalized_edges': normalized_edges,
        'supported_semantic_edges': semantic_edges,
        'components': len(components),
        'records_reassigned': moved,
    }


def build_splits(text_path=TEXT_SOURCE, audio_path=AUDIO_SOURCE, output_dir=OUT,
                 semantic_path=SEMANTIC_EDGES):
    text_rows = sorted(read_jsonl(text_path), key=lambda row: row['segment_sha256'])
    text_rows, text_component_report = component_safe_text_splits(
        text_rows, semantic_path
    )
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
    experimental_audio = [{
        **row,
        'experimental_training_eligible': True,
        'experimental_quality_flags': sorted(set(
            row.get('transcript_review_flags', [])
            + row.get('training_quality_flags', [])
            + row.get('language_quality', {}).get('review_reasons', [])
        )),
    } for row in audio_rows if str(row.get('asr_target_clean') or '').strip()]

    speaker_splits = defaultdict(set)
    for row in strict_audio:
        speaker_splits[row['speaker_id']].add(row['split'])
    if any(len(splits) > 1 for splits in speaker_splits.values()):
        raise ValueError('speaker crosses splits')

    artifacts = {}
    text_counts = Counter()
    audio_counts = Counter()
    audio_hours = Counter()
    experimental_audio_counts = Counter()
    experimental_audio_hours = Counter()
    for split in SPLITS:
        split_text = [row for row in text_rows if row['split'] == split]
        split_audio = [row for row in strict_audio if row['split'] == split]
        split_experimental_audio = [row for row in experimental_audio if row['split'] == split]
        text_counts[split] = len(split_text)
        audio_counts[split] = len(split_audio)
        audio_hours[split] = round(sum(row.get('duration_seconds', 0) for row in split_audio) / 3600, 6)
        experimental_audio_counts[split] = len(split_experimental_audio)
        experimental_audio_hours[split] = round(
            sum(row.get('duration_seconds', 0) for row in split_experimental_audio) / 3600, 6
        )
        artifacts[f'text/{split}.jsonl'] = write_jsonl(output_dir / 'text' / f'{split}.jsonl', split_text)
        artifacts[f'asr/{split}.jsonl'] = write_jsonl(output_dir / 'asr' / f'{split}.jsonl', split_audio)
        artifacts[f'tts/{split}.jsonl'] = write_jsonl(output_dir / 'tts' / f'{split}.jsonl', split_audio)
        artifacts[f'asr_experimental/{split}.jsonl'] = write_jsonl(
            output_dir / 'asr_experimental' / f'{split}.jsonl', split_experimental_audio
        )
        artifacts[f'tts_experimental/{split}.jsonl'] = write_jsonl(
            output_dir / 'tts_experimental' / f'{split}.jsonl', split_experimental_audio
        )

    text_evaluation = [
        {**row, 'review_status': 'automated_quality_screened',
         'experimental_evaluation_eligible': True, 'native_review_optional': True}
        for row in text_rows
        if row['split'] == 'test' and not row.get('quality_flags')
    ]
    asr_evaluation = [
        {**row, 'review_status': 'automated_quality_screened',
         'experimental_evaluation_eligible': True, 'native_review_optional': True}
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
        'release_status': 'integrated_experimental_candidate',
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
        'asr_experimental_all': {
            'records': dict(sorted(experimental_audio_counts.items())),
            'hours': dict(sorted(experimental_audio_hours.items())),
            'quality_flags_retained': True,
        },
        'tts_experimental_all': {
            'records': dict(sorted(experimental_audio_counts.items())),
            'hours': dict(sorted(experimental_audio_hours.items())),
            'quality_flags_retained': True,
        },
        'evaluation_candidates': {
            'text_records': len(text_evaluation),
            'asr_records': len(asr_evaluation),
            'review_status': 'automated_quality_screened',
            'native_review_optional': True,
        },
        'excluded_audio': dict(sorted(excluded.items())),
        'leakage_checks': {
            'text_hash_cross_split': 0,
            'normalized_text_cross_split': 0,
            'supported_semantic_edge_cross_split': 0,
            'identified_speaker_cross_split': 0,
        },
        'text_duplicate_components': text_component_report,
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
