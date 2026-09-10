#!/usr/bin/env python3
"""Join VAANI records with audio checks and emit model-ready manifests."""
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/model_ready/audio'


def quality_flags(row):
    flags = []
    if not row.get('readable'): flags.append('unreadable')
    if row.get('sample_rate_hz') != 16000: flags.append('non_16khz')
    if row.get('channels') != 1: flags.append('non_mono')
    if row.get('sample_width_bytes') != 2: flags.append('non_16bit_pcm')
    if row.get('zero_sample_share', 0) >= .98: flags.append('near_silent')
    if row.get('clipped_sample_share', 0) >= .01: flags.append('high_clipping')
    return flags


def enrich(row, quality):
    result = dict(row)
    flags = list(result.get('quality_flags', []))
    flags.extend(flag for flag in quality_flags(quality) if flag not in flags)
    result['training_quality_flags'] = flags
    result['audio_quality'] = {
        key: quality.get(key) for key in ('readable', 'duration_seconds', 'sample_rate_hz',
        'channels', 'sample_width_bytes', 'peak_abs', 'zero_sample_share', 'clipped_sample_share')
    }
    return result


def read_jsonl(path):
    with path.open(encoding='utf-8') as source:
        for line in source:
            if line.strip(): yield json.loads(line)


def write_jsonl(path, rows):
    path.write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows), encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    quality = {row['audio_sha256']: row for row in read_jsonl(ROOT/'data/processed/audio/quality.jsonl')}
    supervised = []
    unlabeled = []
    missing = []
    speakers = defaultdict(set)
    for source, target, kind in (
        (ROOT/'data/processed/vaani/supervised.jsonl', supervised, 'supervised'),
        (ROOT/'data/processed/vaani/untranscribed.jsonl', unlabeled, 'untranscribed')):
        for row in read_jsonl(source):
            check = quality.get(row['audio_sha256'])
            if check is None:
                missing.append(row['audio_sha256']); continue
            item = enrich(row, check)
            item['training_status'] = kind
            target.append(item)
            speaker_id = row.get('speaker_id', 'NA')
            if kind == 'supervised' and speaker_id != 'NA':
                speakers[speaker_id].add(row['split'])
    write_jsonl(OUT/'supervised_all.jsonl', supervised)
    for split in ('train', 'validation', 'test'):
        write_jsonl(OUT/f'supervised_{split}.jsonl', [r for r in supervised if r['split'] == split])
    write_jsonl(OUT/'untranscribed_all.jsonl', unlabeled)
    flags = Counter(flag for row in supervised + unlabeled for flag in row['training_quality_flags'])
    report = {
        'supervised_records': len(supervised), 'untranscribed_records': len(unlabeled),
        'split_records': dict(Counter(r['split'] for r in supervised)),
        'quality_flags': dict(flags), 'missing_quality_records': len(missing),
        'speaker_cross_split_count': sum(len(v) > 1 for v in speakers.values()),
        'all_records_retained': not missing,
    }
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__': main()
