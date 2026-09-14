#!/usr/bin/env python3
"""Refine the highest-value text queue without guessing linguistic corrections."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from build_huggingface_dataset import is_public_garhwali_text_row


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
OUT = ROOT / 'data/processed/model_ready/text_quality_v2'
PHONE = re.compile(r'(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)')
EDITORIAL_NASAL = re.compile(r'\([nm]\)', re.IGNORECASE)
REPEATED_PUNCTUATION = re.compile(r'([.!?,;:])\1+')
REGIONAL_IDENTITY = re.compile(
    r'\b(kumaon|kumaoni|lohaghat|champawat|nainital)\b', re.IGNORECASE
)
LEXICON_GENRES = {'lexicon', 'thematic_lexicon', 'historical_lexicon', 'numeral_lexicon'}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def refine_row(row):
    original = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    genres = set((row.get('genre_quality') or {}).get('tags') or [])
    release = original
    signals = []
    changes = []

    if PHONE.search(original):
        signals.append('contains_phone_number')
        release = PHONE.sub('<PHONE_NUMBER>', release)
        changes.append('phone_number_redacted')
    script = (row.get('language_quality') or {}).get('script_profile', {}).get('script')
    if script == 'Latn':
        signals.append('romanized_text_requires_native_review')
    if '/' in original:
        signals.append('slash_separated_variants')
    if EDITORIAL_NASAL.search(original):
        signals.append('editorial_nasal_notation')
    if REPEATED_PUNCTUATION.search(original):
        signals.append('repeated_punctuation')
    if REGIONAL_IDENTITY.search(original):
        signals.append('regional_identity_review')
    alphanumeric = sum(character.isalnum() for character in original)
    if alphanumeric <= 2 and not genres.intersection(LEXICON_GENRES):
        signals.append('very_short_fragment')
    if any(character.isdigit() for character in original) and 'numeral_lexicon' not in genres:
        signals.append('contains_digits')

    result = dict(row)
    result.update({
        'original_text': original,
        'original_text_sha256': text_digest(original),
        'release_text': release,
        'release_text_sha256': text_digest(release),
        'automatic_changes': changes,
        'review_signals': sorted(set(signals)),
        'manual_review_required': bool(signals),
        'language_decision': 'unchanged_pending_native_review' if signals else 'unchanged',
        'quality_refinement_status': 'privacy_redacted' if changes else (
            'review_required' if signals else 'no_additional_issue'
        ),
    })
    return result


def main():
    rows = [
        refine_row(row) for row in read_jsonl(SOURCE)
        if is_public_garhwali_text_row(row)
        and row.get('language_bucket') == 'garhwali_candidate'
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / 'priority_text.jsonl'
    with output.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')

    signals = Counter(
        signal for row in rows for signal in row['review_signals']
    )
    sources = Counter(
        source.get('source_id') or 'unknown'
        for row in rows for source in row.get('provenance') or []
    )
    report = {
        'records': len(rows),
        'values_automatically_changed': sum(bool(row['automatic_changes']) for row in rows),
        'manual_review_required': sum(row['manual_review_required'] for row in rows),
        'no_additional_issue': sum(not row['manual_review_required'] for row in rows),
        'review_signal_counts': dict(sorted(signals.items(), key=lambda item: (-item[1], item[0]))),
        'source_record_counts': dict(sorted(sources.items(), key=lambda item: (-item[1], item[0]))),
        'policy': {
            'linguistic_values': 'No automatic spelling, transliteration, language, or dialect correction.',
            'privacy': 'High-confidence Indian phone-number patterns are redacted in release_text; original_text remains preserved locally.',
            'regional_terms': 'Regional place/language mentions trigger review but never automatic relabeling.',
        },
    }
    (OUT / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
