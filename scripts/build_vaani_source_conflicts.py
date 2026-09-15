#!/usr/bin/env python3
"""Find repeated VAANI source-label conflicts using human and machine evidence."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / 'data/vaani/canonical-full-manifest.jsonl'
HUMAN = ROOT / 'data/vaani/canonical-supervised-manifest.jsonl'
MACHINE = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/language_quality/vaani_source_conflicts.jsonl'
REPORT = ROOT / 'data/processed/model_ready/language_quality/vaani_source_conflicts_report.json'
FILENAME_SPEAKER = re.compile(
    r'^IISc_VaaniProject_[MS]_Uttarakhand_([^_]+)_([^_]+)_'
)
PLACEHOLDER_SPEAKERS = {'', 'na', 'n/a', 'none', 'null', 'unknown', 'unidentified'}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def has_bengali_script(text):
    return any('\u0980' <= character <= '\u09ff' for character in str(text))


def source_speaker_key(row):
    match = FILENAME_SPEAKER.match(Path(row.get('audio_path') or '').name)
    if match:
        return f'{match.group(1)}:{match.group(2)}'
    speaker = str(row.get('speaker_id') or '').strip()
    return speaker if speaker.casefold() not in PLACEHOLDER_SPEAKERS else None


def conflict_profiles(human_rows, machine_rows):
    profiles = defaultdict(Counter)
    for row in human_rows:
        speaker = source_speaker_key(row)
        text = row.get('canonical_transcript') or row.get('selected_transcript') or ''
        if not speaker or not text:
            continue
        profiles[speaker]['human_transcripts'] += 1
        profiles[speaker]['human_bengali_transcripts'] += has_bengali_script(text)
    for row in machine_rows:
        speaker = source_speaker_key(row)
        if not speaker:
            continue
        flags = set((row.get('machine_transcript_quality') or {}).get('flags') or [])
        profiles[speaker]['machine_drafts'] += 1
        profiles[speaker]['machine_bengali_drafts'] += 'bengali_script' in flags

    conflicts = {}
    for speaker, counts in profiles.items():
        if (
            counts['human_bengali_transcripts'] >= 3
            and counts['human_bengali_transcripts'] == counts['human_transcripts']
            and counts['machine_bengali_drafts'] >= 10
            and counts['machine_bengali_drafts'] == counts['machine_drafts']
        ):
            conflicts[speaker] = {
                **dict(counts),
                'evidence': [
                    'repeated_human_bengali_script',
                    'repeated_machine_bengali_script',
                    'human_and_machine_evidence_agree_by_speaker',
                ],
                'inference_scope': 'source_label_conflict_not_audio_language_ground_truth',
            }
    return conflicts


def conflict_row(row, profile):
    return {
        'audio_sha256': row.get('audio_sha256'),
        'audio_path': row.get('audio_path'),
        'speaker_id': row.get('speaker_id'),
        'source_speaker_key': source_speaker_key(row),
        'source_language_label': row.get('language'),
        'languages_known': row.get('languages_known') or [],
        'district': row.get('district'),
        'transcript_available': bool(
            row.get('canonical_transcript') or row.get('transcript')
        ),
        'language_scope_status': 'source_label_conflict',
        'source_conflict_evidence': profile,
        'garhwali_training_eligible': False,
        'active_for_source_error_analysis': True,
        'record_preserved': True,
    }


def run(full_path=FULL, human_path=HUMAN, machine_path=MACHINE,
        output_path=OUTPUT, report_path=REPORT):
    full_rows = read_jsonl(full_path)
    profiles = conflict_profiles(read_jsonl(human_path), read_jsonl(machine_path))
    rows = [
        conflict_row(row, profiles[source_speaker_key(row)])
        for row in full_rows if source_speaker_key(row) in profiles
    ]
    rows.sort(key=lambda row: row['audio_sha256'])
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )
    report = {
        'source_conflict_speakers': len(profiles),
        'source_conflict_records': len(rows),
        'human_transcribed_records': sum(row['transcript_available'] for row in rows),
        'untranscribed_records': sum(not row['transcript_available'] for row in rows),
        'speaker_profiles': profiles,
        'garhwali_training_eligible': 0,
        'records_removed_or_quarantined': 0,
        'all_records_preserved_for_source_error_analysis': True,
        'policy': 'Repeated cross-layer script evidence marks a source-label conflict; it does not assert audio language ground truth.',
    }
    Path(report_path).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
