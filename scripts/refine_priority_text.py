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
REPEATED_PUNCTUATION = re.compile(r'(?<!\.)\.\.(?!\.)|([!?,;:])\1+')
URL = re.compile(r'https?://|www\.', re.IGNORECASE)
WIKI_MARKUP = re.compile(r"'''|''|[=\[\]{}*#|]")
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


def clean_wiki_markup(text):
    text = re.sub(r"'''|''", '', text)
    text = re.sub(r'[=\[\]{}*#|]+', ' ', text)
    return ' '.join(text.split())


def refine_row(row):
    original = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    genres = set((row.get('genre_quality') or {}).get('tags') or [])
    release = original
    signals = []
    changes = []
    cleanup_flags = set(row.get('cleanup_review_flags') or []) | set(
        row.get('deep_cleanup_flags') or []
    )

    if PHONE.search(original):
        signals.append('contains_phone_number')
        release = PHONE.sub('<PHONE_NUMBER>', release)
        changes.append('phone_number_redacted')
    if 'html_markup' in cleanup_flags and WIKI_MARKUP.search(release):
        release = clean_wiki_markup(release)
        changes.append('wiki_markup_removed')
    script = (row.get('language_quality') or {}).get('script_profile', {}).get('script')
    if script == 'Latn':
        signals.append('romanized_text_requires_native_review')
    if '/' in original and (
        len(original.split()) <= 6 or genres.intersection(LEXICON_GENRES)
    ):
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

    resolved_flags = set()
    if 'html_markup' in cleanup_flags and not WIKI_MARKUP.search(release):
        resolved_flags.add('html_markup')
    if 'mixed_latin_devanagari' in cleanup_flags and script not in {'Mixed', 'Mixed-Deva-Latn'}:
        resolved_flags.add('mixed_latin_devanagari')
    if 'very_short' in cleanup_flags and genres.intersection(LEXICON_GENRES):
        resolved_flags.add('very_short')
    if 'url' in cleanup_flags and not URL.search(release):
        resolved_flags.add('url')
    remaining_flags = sorted(cleanup_flags - resolved_flags)

    manual_review_required = bool(signals or remaining_flags)
    if 'phone_number_redacted' in changes:
        refinement_status = 'privacy_redacted_review_required' if manual_review_required else 'privacy_redacted'
    elif changes:
        refinement_status = 'mechanically_cleaned_review_required' if manual_review_required else 'mechanically_cleaned'
    elif manual_review_required:
        refinement_status = 'review_required'
    else:
        refinement_status = 'no_additional_issue'

    result = dict(row)
    result.update({
        'original_text': original,
        'original_text_sha256': text_digest(original),
        'release_text': release,
        'release_text_sha256': text_digest(release),
        'automatic_changes': changes,
        'resolved_cleanup_flags': sorted(resolved_flags),
        'remaining_cleanup_flags': remaining_flags,
        'review_signals': sorted(set(signals)),
        'manual_review_required': manual_review_required,
        'language_decision': 'unchanged_pending_native_review' if signals or remaining_flags else 'unchanged',
        'quality_refinement_status': refinement_status,
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
    resolved = Counter(
        flag for row in rows for flag in row['resolved_cleanup_flags']
    )
    remaining = Counter(
        flag for row in rows for flag in row['remaining_cleanup_flags']
    )
    changes = Counter(
        change for row in rows for change in row['automatic_changes']
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
        'resolved_cleanup_flag_counts': dict(sorted(resolved.items(), key=lambda item: (-item[1], item[0]))),
        'remaining_cleanup_flag_counts': dict(sorted(remaining.items(), key=lambda item: (-item[1], item[0]))),
        'automatic_change_counts': dict(sorted(changes.items(), key=lambda item: (-item[1], item[0]))),
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
