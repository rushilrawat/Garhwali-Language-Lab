#!/usr/bin/env python3
"""Build leakage-checked text, ASR, TTS, and evaluation candidate splits."""

import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from garhwali_lab.hashing import sha256_file as file_sha256
from garhwali_lab.io import read_jsonl
from garhwali_lab.io import write_jsonl as _write_jsonl
from garhwali_lab.text import leakage_key as normalized_text_key


ROOT = Path(__file__).resolve().parents[1]
TEXT_SOURCE = ROOT / 'data/processed/model_ready/segments/all_segments.jsonl'
AUDIO_SOURCE = ROOT / 'data/processed/model_ready/language_quality/audio_supervised.jsonl'
OUT = ROOT / 'data/processed/model_ready/splits'
SEMANTIC_EDGES = ROOT / (
    'data/processed/evaluation/data_quality/'
    'semantic_duplicates_refined_v0_2/cloud_output/refined_candidates.jsonl'
)
SPLITS = ('train', 'validation', 'test')
REQUIRE_SEMANTIC_ENV = 'GARHWALI_REQUIRE_SEMANTIC_EDGES'


def split_for_hash(digest):
    """Deterministic 90/5/5 bucket, matching the upstream segment split rule."""
    bucket = int(hashlib.sha256(str(digest).encode('utf-8')).hexdigest()[:8], 16) % 1000
    if bucket < 900:
        return 'train'
    if bucket < 950:
        return 'validation'
    return 'test'
PLACEHOLDER_SPEAKERS = {'', 'na', 'n/a', 'none', 'null', 'unknown', 'unidentified'}



def write_jsonl(path, rows):
    """Write a split file and return its artifact entry for the report."""
    rows = list(rows)
    return {'records': len(rows), 'sha256': _write_jsonl(path, rows)}

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


def flag_experimental_audio_leakage(rows):
    """Flag, without moving, experimental audio rows that leak across splits.

    The experimental views keep upstream splits and unidentified speakers, so
    they cannot be speaker-disjoint by construction. Rows whose identified
    speaker or normalized transcript also occurs in another split get a
    quality flag, and the counts go into the report.
    """
    speaker_splits = defaultdict(set)
    transcript_splits = defaultdict(set)
    for row in rows:
        if identified_speaker(row):
            speaker_splits[str(row['speaker_id']).strip().casefold()].add(row['split'])
        key = normalized_text_key(row.get('asr_target_clean'))
        if key:
            transcript_splits[key].add(row['split'])
    counts = Counter()
    for row in rows:
        flags = set(row['experimental_quality_flags'])
        if not identified_speaker(row):
            counts['experimental_unidentified_speaker_records'] += 1
            flags.add('speaker_unidentified')
        elif len(speaker_splits[str(row['speaker_id']).strip().casefold()]) > 1:
            counts['experimental_speaker_cross_split_records'] += 1
            flags.add('speaker_crosses_splits')
        key = normalized_text_key(row.get('asr_target_clean'))
        if key and len(transcript_splits[key]) > 1:
            counts['experimental_transcript_cross_split_records'] += 1
            flags.add('transcript_crosses_splits')
        row['experimental_quality_flags'] = sorted(flags)
    if counts['experimental_speaker_cross_split_records'] or counts['experimental_transcript_cross_split_records']:
        print('warning: experimental audio splits leak across splits: '
              f'{dict(counts)}; filter on experimental_quality_flags', file=sys.stderr)
    return {name: counts[name] for name in (
        'experimental_unidentified_speaker_records',
        'experimental_speaker_cross_split_records',
        'experimental_transcript_cross_split_records',
    )}


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

    document_segments = defaultdict(list)
    for identity, row in by_id.items():
        for source_document in row.get('parents', []):
            document_id = source_document.get('text_sha256')
            if document_id:
                document_segments[str(document_id)].append(identity)
    for identities in document_segments.values():
        for identity in identities[1:]:
            union(identities[0], identity)

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
    if semantic_path is None:
        semantic_source = 'disabled'
    elif semantic_path.exists():
        semantic_source = 'loaded'
    else:
        semantic_source = 'missing'
        message = (f'semantic duplicate edges not found at {semantic_path}; '
                   'near-duplicate isolation is limited to exact normalized matches')
        if os.environ.get(REQUIRE_SEMANTIC_ENV) == '1':
            raise FileNotFoundError(message)
        print(f'warning: {message}', file=sys.stderr)
    if semantic_source == 'loaded':
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
    moved = 0
    hashed_components = 0
    for root, identities in components.items():
        member_splits = {by_id[identity]['split'] for identity in identities}
        if len(member_splits) == 1:
            assigned = member_splits.pop()
        else:
            # Conflicting components are placed by a hash of their root. Always
            # choosing train (the earlier rule) halved validation and test.
            assigned = split_for_hash(root)
            hashed_components += 1
        for identity in identities:
            row = by_id[identity]
            if row['split'] != assigned:
                row['original_split'] = row['split']
                row['split'] = assigned
                row['split_assignment'] = 'duplicate_component_isolation'
                moved += 1
            row['duplicate_component_id'] = root
    return list(by_id.values()), {
        'parent_documents': len(document_segments),
        'parent_document_links': sum(len(identities) - 1 for identities in document_segments.values()),
        'normalized_edges': normalized_edges,
        'supported_semantic_edges': semantic_edges,
        'components': len(components),
        'records_reassigned': moved,
        'conflicting_components_hash_assigned': hashed_components,
        'semantic_edges_source': semantic_source,
    }


def build_splits(text_path=TEXT_SOURCE, audio_path=AUDIO_SOURCE, output_dir=OUT,
                 semantic_path=SEMANTIC_EDGES,
                 release_id='garhwali-splits-candidate-2026-09-10'):
    text_rows = sorted(read_jsonl(text_path), key=lambda row: row['segment_sha256'])
    text_rows, text_component_report = component_safe_text_splits(
        text_rows, semantic_path
    )
    audio_rows = sorted(read_jsonl(audio_path), key=lambda row: row['audio_sha256'])

    text_hash_splits = defaultdict(set)
    parent_document_splits = defaultdict(set)
    for row in text_rows:
        text_hash_splits[row['segment_sha256']].add(row['split'])
        for source_document in row.get('parents', []):
            document_id = source_document.get('text_sha256')
            if document_id:
                parent_document_splits[str(document_id)].add(row['split'])
    if any(len(splits) > 1 for splits in text_hash_splits.values()):
        raise ValueError('text segment crosses splits')
    parent_document_cross_split = sum(
        len(splits) > 1 for splits in parent_document_splits.values()
    )
    if parent_document_cross_split:
        raise ValueError('parent document crosses splits')

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

    experimental_leakage = flag_experimental_audio_leakage(experimental_audio)

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
        'release_id': release_id,
        'release_status': 'integrated_experimental_candidate',
        'source_hashes': {
            'text_segments': file_sha256(text_path),
            'audio_supervised': file_sha256(audio_path),
            'semantic_edges': (
                file_sha256(semantic_path)
                if semantic_path and Path(semantic_path).is_file()
                else None
            ),
        },
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
            'parent_document_cross_split': parent_document_cross_split,
            'identified_speaker_cross_split': 0,
            **experimental_leakage,
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
