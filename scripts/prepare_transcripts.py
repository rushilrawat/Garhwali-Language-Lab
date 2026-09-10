#!/usr/bin/env python3
"""Derive ASR targets and balanced queues while preserving source transcripts."""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/model_ready/transcripts'


def spoken_text(text):
    value = unicodedata.normalize('NFC', text)
    value = re.sub(r'<\/?(?:noise|pause)>', ' ', value, flags=re.I)
    value = re.sub(r'\[[^\]]*\]', ' ', value)
    value = re.sub(r'\{[^}]*\}', ' ', value)
    return re.sub(r'\s+', ' ', value).strip()


def annotation_flags(text):
    flags = []
    for tag in ('noise', 'pause'):
        opens = len(re.findall(fr'<{tag}>', text, re.I))
        closes = len(re.findall(fr'</{tag}>', text, re.I))
        if opens != closes: flags.append(f'unbalanced_{tag}_tag')
    if re.search(r'[\u0980-\u09ff]', text): flags.append('bengali_script')
    if not spoken_text(text): flags.append('empty_spoken_text')
    return flags


def batch_id(index, size=1000):
    return f'batch-{index // size + 1:04d}'


def read_jsonl(path):
    with path.open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True)+'\n' for row in rows), encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    supervised = []
    review = []
    flag_counts = Counter()
    for row in read_jsonl(ROOT/'data/processed/model_ready/audio/supervised_all.jsonl'):
        target = spoken_text(row['selected_transcript'])
        flags = list(row.get('training_quality_flags', []))
        flags.extend(flag for flag in annotation_flags(row['selected_transcript']) if flag not in flags)
        row['asr_target'] = target
        row['asr_target_sha256'] = hashlib.sha256(target.encode()).hexdigest()
        row['transcript_review_flags'] = flags
        supervised.append(row)
        flag_counts.update(flags)
        if flags: review.append(row)

    unlabeled = read_jsonl(ROOT/'data/processed/model_ready/audio/untranscribed_all.jsonl')
    unlabeled.sort(key=lambda r: (r.get('district') or '', r.get('gender') or '', r.get('duration_seconds') or 0, r['audio_sha256']))
    for index, row in enumerate(unlabeled):
        row['transcription_batch'] = batch_id(index)
        row['transcription_priority'] = index + 1

    write_jsonl(OUT/'supervised.jsonl', supervised)
    write_jsonl(OUT/'supervised_review.jsonl', review)
    write_jsonl(OUT/'untranscribed_queue.jsonl', unlabeled)
    report = {
        'supervised_records': len(supervised), 'review_records': len(review),
        'untranscribed_records': len(unlabeled), 'transcription_batches': len({r['transcription_batch'] for r in unlabeled}),
        'batch_size': 1000, 'review_flags': dict(flag_counts),
        'empty_asr_targets': sum(not r['asr_target'] for r in supervised),
    }
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__': main()
