#!/usr/bin/env python3
"""Build a compact, reversible recovery queue for flagged SraVaani drafts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_queue.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_report.json'


def compact_repetitions(text, maximum=2):
    output = []
    count = 0
    previous = None
    for token in str(text).split():
        count = count + 1 if token == previous else 1
        if count <= maximum:
            output.append(token)
        previous = token
    return ' '.join(output)


def route_row(row):
    quality = row.get('machine_transcript_quality') or {}
    flags = set(quality.get('flags') or [])
    actions = []
    priority = 0
    if 'empty_transcript' in flags:
        actions.append('redecode_empty'); priority += 100
    if flags & {'bengali_script', 'no_devanagari_letters', 'mixed_script'}:
        actions.append('redecode_with_devanagari_constraint'); priority += 80
    if 'repeated_token_loop' in flags:
        actions.append('compare_repetition_compaction'); priority += 60
    if flags & {'implausibly_short_for_duration', 'implausibly_long_for_duration'}:
        actions.append('resegment_and_redecode'); priority += 70
    if 'frequent_identical_hypothesis' in flags:
        actions.append('redecode_frequent_hypothesis'); priority += 40
    original = row.get('machine_transcript', '')
    candidate = compact_repetitions(original) if 'repeated_token_loop' in flags else original
    return {
        'audio_sha256': row.get('audio_sha256'),
        'local_audio_path': row.get('local_audio_path'),
        'duration_seconds': row.get('duration_seconds'),
        'original_machine_transcript': original,
        'mechanical_candidate': candidate,
        'mechanical_candidate_changed': candidate != original,
        'quality_level': quality.get('level'),
        'quality_flags': sorted(flags),
        'recovery_actions': actions,
        'recovery_priority': priority,
        'active_for_experiment': True,
        'supervised_training_eligible': False,
    }


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run(input_path=INPUT, output_path=OUTPUT, report_path=REPORT):
    rows = []
    total = 0
    action_counts = Counter()
    with Path(input_path).open(encoding='utf-8') as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            source = json.loads(line)
            if not (source.get('machine_transcript_quality') or {}).get('flags'):
                continue
            routed = route_row(source)
            rows.append(routed)
            action_counts.update(routed['recovery_actions'])
    rows.sort(key=lambda row: (-row['recovery_priority'], row['audio_sha256']))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )
    report = {
        'run_id': 'sravaani-draft-recovery-routing-v0.1',
        'input_sha256': sha256_file(input_path),
        'source_records': total,
        'recovery_records': len(rows),
        'mechanical_candidates_changed': sum(row['mechanical_candidate_changed'] for row in rows),
        'recovery_actions': dict(sorted(action_counts.items())),
        'all_source_records_remain_active': True,
        'records_removed_or_quarantined': 0,
        'automatic_corrections_promoted': 0,
        'original_transcripts_preserved': True,
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.report), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
