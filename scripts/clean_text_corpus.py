#!/usr/bin/env python3
"""Apply reversible, conservative cleanup to the all-data text view."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed/text/all_garhwali.jsonl'
OUTPUT = ROOT / 'data/processed/text/cleaned_all_garhwali.jsonl'
REVIEW = ROOT / 'data/processed/review/text_cleanup_review.jsonl'
INVISIBLE = dict.fromkeys(map(ord, '\u200b\u200c\u200d\u2060\ufeff'), None)


def clean_text(text):
    changes = []
    cleaned = unicodedata.normalize('NFC', text)
    without_invisible = cleaned.translate(INVISIBLE)
    if without_invisible != cleaned:
        changes.append('removed_invisible_characters')
    normalized = re.sub(r'\s+', ' ', without_invisible).strip()
    if normalized != without_invisible:
        changes.append('normalized_whitespace')
    return normalized, changes


def review_flags(text):
    flags = []
    if re.search(r'<[^>]+>', text): flags.append('html_markup')
    if re.search(r'https?://|www\.', text, re.I): flags.append('url')
    if '\ufffd' in text: flags.append('replacement_character')
    has_devanagari = bool(re.search(r'[\u0900-\u097f]', text))
    has_latin = bool(re.search(r'[A-Za-z]', text))
    if has_devanagari and has_latin: flags.append('mixed_latin_devanagari')
    if not has_devanagari: flags.append('no_devanagari')
    if len(text) < 3: flags.append('very_short')
    return flags


def main():
    counts = Counter()
    change_counts = Counter()
    flag_counts = Counter()
    REVIEW.parent.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(encoding='utf-8') as src, OUTPUT.open('w', encoding='utf-8') as dst, REVIEW.open('w', encoding='utf-8') as review:
        for line in src:
            if not line.strip(): continue
            row = json.loads(line)
            cleaned, changes = clean_text(row['text'])
            flags = review_flags(cleaned)
            row['text_clean'] = cleaned
            row['cleanup_changes'] = changes
            row['cleanup_review_flags'] = flags
            row['cleanup_status'] = 'review' if flags else 'automatic_clean'
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            if flags:
                review.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            counts['records'] += 1
            counts['changed_records'] += bool(changes)
            counts['review_records'] += bool(flags)
            change_counts.update(changes)
            flag_counts.update(flags)
    report = {
        **counts,
        'change_counts': dict(change_counts),
        'review_flag_counts': dict(flag_counts),
        'source': str(SOURCE.relative_to(ROOT)),
        'output': str(OUTPUT.relative_to(ROOT)),
        'review_output': str(REVIEW.relative_to(ROOT)),
    }
    OUTPUT.with_name('cleaned_all_garhwali_report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__': main()
