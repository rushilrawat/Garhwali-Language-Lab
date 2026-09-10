#!/usr/bin/env python3
"""Derive non-destructive loudness recommendations from measured WAV metrics."""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'data/processed/audio/quality.jsonl'
OUT = ROOT/'data/processed/model_ready/audio/normalization.jsonl'
REVIEW = ROOT/'data/processed/review/audio_normalization_review.jsonl'


def distribution(values):
    values = sorted(value for value in values if value is not None)
    if not values: return {}
    def percentile(p):
        position = (len(values) - 1) * p
        lower = int(position); upper = min(lower + 1, len(values) - 1)
        value = values[lower] + (values[upper] - values[lower]) * (position - lower)
        return round(value, 6)
    return {'min':round(values[0],6),'p01':percentile(.01),'p05':percentile(.05),
            'p50':percentile(.5),'p95':percentile(.95),'p99':percentile(.99),
            'max':round(values[-1],6)}


def recommend(row, target_rms_dbfs=-20.0):
    rms = row.get('rms_dbfs'); peak = row.get('peak_dbfs'); dc = row.get('dc_offset_normalized', 0)
    gain = None if rms is None else round(max(-12.0, min(12.0, target_rms_dbfs-rms)), 4)
    flags = []
    if rms is None: flags.append('missing_rms')
    elif rms < -40: flags.append('very_quiet')
    elif rms > -10: flags.append('very_loud')
    if abs(dc) > .02: flags.append('high_dc_offset')
    if row.get('clipped_sample_share', 0) >= .01: flags.append('high_clipping')
    if gain is not None and peak is not None and peak + gain > -1: flags.append('projected_clipping')
    return {'target_rms_dbfs':target_rms_dbfs,'recommended_gain_db':gain,
            'projected_peak_dbfs':round(peak+gain,4) if peak is not None and gain is not None else None,
            'flags':flags}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True); REVIEW.parent.mkdir(parents=True, exist_ok=True)
    counts = Counter(); measurements = {'rms_dbfs':[],'peak_dbfs':[],'dc_offset_normalized':[],
                                         'zero_sample_share':[],'duration_seconds':[]}
    with SOURCE.open(encoding='utf-8') as source, OUT.open('w',encoding='utf-8') as output, REVIEW.open('w',encoding='utf-8') as review:
        for line in source:
            if not line.strip(): continue
            row=json.loads(line); advice=recommend(row)
            record={'audio_sha256':row['audio_sha256'],'local_audio_path':row['local_audio_path'],
                    'subset':row['subset'],'measured_rms_dbfs':row.get('rms_dbfs'),
                    'measured_peak_dbfs':row.get('peak_dbfs'),'dc_offset_normalized':row.get('dc_offset_normalized'),**advice}
            output.write(json.dumps(record,sort_keys=True)+'\n'); counts['records']+=1
            for name in measurements: measurements[name].append(row.get(name))
            counts.update(advice['flags'])
            if any(flag in advice['flags'] for flag in ('very_quiet','very_loud','high_dc_offset','high_clipping')):
                review.write(json.dumps(record,sort_keys=True)+'\n'); counts['review_records']+=1
    report={**dict(counts),'thresholds':{'target_rms_dbfs':-20.0,'very_quiet_below_dbfs':-40.0,
            'very_loud_above_dbfs':-10.0,'high_dc_offset_absolute_above':.02,
            'high_clipping_sample_share_at_least':.01,'projected_peak_ceiling_dbfs':-1.0},
            'distributions':{name:distribution(values) for name,values in measurements.items()}}
    OUT.with_name('normalization_report.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,sort_keys=True))


if __name__=='__main__': main()
