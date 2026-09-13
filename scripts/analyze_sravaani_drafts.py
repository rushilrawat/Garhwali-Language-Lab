#!/usr/bin/env python3
"""Attach reversible quality signals to every SraVaani machine transcript."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from tag_language_quality import script_profile


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani_quality_report.json'
REVIEW = ROOT / 'data/processed/review/sravaani_draft_quality.jsonl'


def normalize_hypothesis(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def repeated_token_loop(tokens):
    longest = 1
    current = 1
    for left, right in zip(tokens, tokens[1:]):
        current = current + 1 if left == right else 1
        longest = max(longest, current)
    return longest >= 4


def analyze_row(row, hypothesis_frequency):
    result = dict(row)
    text = normalize_hypothesis(row.get('machine_transcript', ''))
    profile = script_profile(text)
    duration = max(float(row.get('duration_seconds') or 0), 0.001)
    letters = sum(profile['counts'].values())
    tokens = text.split()
    flags = []
    if not text:
        flags.append('empty_transcript')
    if profile['counts']['bengali']:
        flags.append('bengali_script')
    if letters and not profile['counts']['devanagari']:
        flags.append('no_devanagari_letters')
    if profile['script'].startswith('Mixed'):
        flags.append('mixed_script')
    if repeated_token_loop(tokens):
        flags.append('repeated_token_loop')
    character_rate = len(text.replace(' ', '')) / duration
    token_rate = len(tokens) / duration
    if text and duration >= 5 and character_rate < 0.5:
        flags.append('implausibly_short_for_duration')
    if character_rate > 25 or token_rate > 7:
        flags.append('implausibly_long_for_duration')
    if hypothesis_frequency >= 10:
        flags.append('frequent_identical_hypothesis')
    severe = {
        'empty_transcript', 'bengali_script', 'no_devanagari_letters',
        'repeated_token_loop', 'implausibly_short_for_duration',
        'implausibly_long_for_duration',
    }
    result['machine_transcript'] = text
    result['machine_transcript_quality'] = {
        'flags': flags,
        'level': 'high_risk' if severe.intersection(flags) else
                 ('flagged' if flags else 'standard'),
        'usage': 'active_experimental',
        'script_profile': profile,
        'characters_per_second': round(character_rate, 6),
        'tokens_per_second': round(token_rate, 6),
        'identical_hypothesis_frequency': hypothesis_frequency,
        'confidence_available': False,
        'human_reference_available': False,
    }
    result['training_eligible'] = False
    result['experimental_training_eligible'] = True
    return result


def read_rows(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run(input_path=INPUT, output_path=OUTPUT, report_path=REPORT, review_path=REVIEW):
    input_path = Path(input_path)
    rows = read_rows(input_path)
    frequencies = Counter(normalize_hypothesis(row.get('machine_transcript', '')) for row in rows)
    counts = Counter()
    audio_hashes = Counter(row['audio_sha256'] for row in rows)
    output_path = Path(output_path)
    review_path = Path(review_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as output, review_path.open('w', encoding='utf-8') as review:
        for row in rows:
            hypothesis = normalize_hypothesis(row.get('machine_transcript', ''))
            tagged = analyze_row(row, frequencies[hypothesis])
            output.write(json.dumps(tagged, ensure_ascii=False, sort_keys=True) + '\n')
            quality = tagged['machine_transcript_quality']
            counts['records'] += 1
            counts[f"level:{quality['level']}"] += 1
            for flag in quality['flags']:
                counts[f'flag:{flag}'] += 1
            if quality['flags']:
                review.write(json.dumps(tagged, ensure_ascii=False, sort_keys=True) + '\n')
                counts['flagged_records'] += 1
    report = {
        'run_id': 'sravaani-full-draft-quality-v0.1',
        'input': str(input_path.relative_to(ROOT)),
        'input_sha256': sha256_file(input_path),
        'output': str(output_path.relative_to(ROOT)),
        'records': len(rows),
        'unique_audio_hashes': len(audio_hashes),
        'inherited_duplicate_audio_rows': len(rows) - len(audio_hashes),
        'unique_hypotheses': len(frequencies),
        'all_records_active_experimentally': True,
        'automatic_promotion_to_human_transcript': False,
        'counts': dict(sorted(counts.items())),
        'thresholds': {
            'frequent_identical_hypothesis': 10,
            'repeated_identical_token_run': 4,
            'minimum_characters_per_second_for_5s_audio': 0.5,
            'maximum_characters_per_second': 25,
            'maximum_tokens_per_second': 7,
        },
    }
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    parser.add_argument('--review', type=Path, default=REVIEW)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.report, args.review), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
