#!/usr/bin/env python3
"""Build small, deterministic human-review queues from prepared views."""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sample(path: Path, predicate, limit=100):
    rows=[]
    with path.open(encoding='utf-8') as f:
        for line in f:
            if line.strip():
                row=json.loads(line)
                if predicate(row) and len(rows)<limit: rows.append(row)
    return rows

def main():
    out=ROOT/'data/processed/review'; out.mkdir(parents=True, exist_ok=True)
    queues={
      'vaani_transcript_review': sample(ROOT/'data/processed/vaani/supervised.jsonl', lambda r: bool(r.get('quality_flags')) or not r.get('recommended_for_supervised_training', True)),
      'vaani_audio_review': sample(ROOT/'data/processed/audio/quality.jsonl', lambda r: (not r.get('readable')) or r.get('high_clipping', False) or r.get('zero_sample_share',0)>=.98 or r.get('clipped_sample_share',0)>=.01),
      'text_low_quality': sample(ROOT/'data/processed/text/canonical.jsonl', lambda r: r.get('quality',{}).get('quality_band')=='low'),
      'text_review': sample(ROOT/'data/processed/text/canonical.jsonl', lambda r: r.get('quality',{}).get('quality_band')=='review'),
    }
    for name, rows in queues.items():
        (out/(name+'.jsonl')).write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in rows),encoding='utf-8')
    # Speaker partition check over supervised rows.
    speakers=defaultdict(set)
    with (ROOT/'data/processed/vaani/supervised.jsonl').open(encoding='utf-8') as f:
        for line in f:
            r=json.loads(line); speakers[r.get('speaker_id','NA')].add(r.get('split'))
    cross={s:sorted(v) for s,v in speakers.items() if len(v)>1 and s!='NA'}
    report={'queue_sizes':{k:len(v) for k,v in queues.items()},'speaker_cross_split_count':len(cross),'speaker_cross_split_examples':dict(list(cross.items())[:20])}
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__': main()
