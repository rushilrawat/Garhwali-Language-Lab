#!/usr/bin/env python3
"""Second-pass mechanical cleanup for text and audio transcript targets."""
import html
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/model_ready/cleaned'
REVIEW = ROOT / 'data/processed/review'


def clean_model_text(source):
    text = unicodedata.normalize('NFC', source)
    changes = []
    cleaned = re.sub(
        r'<\/?(?:noise|pause)>|\[[^\]]*\]|\{\{[^{}]*\}\}|\{[^{}]*\}',
        ' ', text, flags=re.I,
    )
    if cleaned != text: changes.append('removed_speech_annotations')
    decoded = html.unescape(cleaned)
    if decoded != cleaned: changes.append('decoded_html_entities')
    without_markup = re.sub(r'<[^>]*>', ' ', decoded)
    if without_markup != decoded: changes.append('removed_markup_tags')
    truncated = bool(re.search(r'\s*--+\s*$', without_markup))
    without_truncation = re.sub(r'\s*--+\s*$', '', without_markup)
    if truncated: changes.append('removed_truncation_marker')
    final = re.sub(r'\s+', ' ', without_truncation).strip()
    flags = []
    if truncated: flags.append('possibly_incomplete')
    if re.search(r'https?://|www\.', final, re.I): flags.append('url')
    if '\ufffd' in final: flags.append('replacement_character')
    if re.search(r'[\u0980-\u09ff]', final): flags.append('bengali_script')
    if not final: flags.append('empty_after_cleanup')
    return final, changes, flags


def process(source, output, review, field, target_field):
    counts = Counter()
    with source.open(encoding='utf-8') as src, output.open('w', encoding='utf-8') as dst, review.open('w', encoding='utf-8') as rev:
        for line in src:
            if not line.strip(): continue
            row = json.loads(line)
            cleaned, changes, flags = clean_model_text(row[field])
            row[target_field] = cleaned
            row['deep_cleanup_changes'] = changes
            row['deep_cleanup_flags'] = flags
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
            if flags: rev.write(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n')
            counts['records'] += 1
            counts['changed_records'] += bool(changes)
            counts['review_records'] += bool(flags)
            for change in changes: counts[f'change:{change}'] += 1
            for flag in flags: counts[f'flag:{flag}'] += 1
    return dict(counts)


def main():
    OUT.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
    text = process(ROOT/'data/processed/text/cleaned_all_garhwali.jsonl', OUT/'text.jsonl',
                   REVIEW/'deep_text_review.jsonl', 'text_clean', 'text_model')
    audio = process(ROOT/'data/processed/model_ready/transcripts/supervised.jsonl', OUT/'audio_transcripts.jsonl',
                    REVIEW/'deep_audio_transcript_review.jsonl', 'asr_target', 'asr_target_clean')
    report = {'text': text, 'audio_transcripts': audio}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__': main()
