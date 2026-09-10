#!/usr/bin/env python3
"""Export minimal, model-agnostic ASR fine-tuning JSONL files."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed/model_ready/cleaned/audio_transcripts.jsonl'
OUT = ROOT / 'data/processed/model_ready/asr_finetuning'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    handles = {split: (OUT/f'{split}.jsonl').open('w', encoding='utf-8') for split in ('train','validation','test')}
    counts = Counter(); durations = Counter()
    try:
        with SOURCE.open(encoding='utf-8') as source:
            for line in source:
                if not line.strip(): continue
                row = json.loads(line); split = row['split']
                record = {
                    'audio': row['local_audio_path'], 'text': row['asr_target_clean'],
                    'audio_sha256': row['audio_sha256'], 'speaker_id': row.get('speaker_id','NA'),
                    'district': row.get('district'), 'gender': row.get('gender'),
                    'duration_seconds': row['duration_seconds'],
                    'quality_flags': row.get('transcript_review_flags',[]) + row.get('deep_cleanup_flags',[]),
                }
                handles[split].write(json.dumps(record, ensure_ascii=False, sort_keys=True)+'\n')
                counts[split] += 1; durations[split] += row['duration_seconds']
    finally:
        for handle in handles.values(): handle.close()
    report = {'records':dict(counts),'hours':{k:v/3600 for k,v in durations.items()},
              'total_records':sum(counts.values()),'all_rows_included':True}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))


if __name__=='__main__': main()
