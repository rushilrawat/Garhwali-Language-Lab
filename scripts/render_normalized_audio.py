#!/usr/bin/env python3
"""Render reviewed, unflagged normalization plans into derived WAV files."""

import argparse
import array
import hashlib
import json
import math
import sys
import wave
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPLIT_DIR = ROOT / 'data/processed/model_ready/splits/tts'
NORMALIZATION = ROOT / 'data/processed/model_ready/audio/normalization.jsonl'
OUT = ROOT / 'data/processed/model_ready/audio_normalized'
SPLITS = ('train', 'validation', 'test')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def render_wav(source, output, gain_db, dc_offset_normalized):
    with wave.open(str(source), 'rb') as handle:
        params = handle.getparams()
        if params.nchannels != 1 or params.sampwidth != 2 or params.comptype != 'NONE':
            raise ValueError(f'unsupported WAV format: {source}')
        samples = array.array('h', handle.readframes(params.nframes))
    if sys.byteorder == 'big':
        samples.byteswap()

    factor = math.pow(10, gain_db / 20)
    dc_samples = dc_offset_normalized * 32768
    derived = array.array('h', (
        max(-32768, min(32767, round((sample - dc_samples) * factor)))
        for sample in samples
    ))
    if sys.byteorder == 'big':
        derived.byteswap()
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), 'wb') as handle:
        handle.setparams(params)
        handle.writeframes(derived.tobytes())
    return {
        'source_sha256': file_sha256(source),
        'derived_sha256': file_sha256(output),
        'frames': params.nframes,
    }


def read_jsonl(path):
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def build_derived_audio(
    split_dir=SPLIT_DIR,
    normalization_path=NORMALIZATION,
    output_dir=OUT,
    root=ROOT,
    render_flagged_review=False,
):
    plans = {row['audio_sha256']: row for row in read_jsonl(normalization_path)}
    counts = Counter({'rendered': 0, 'skipped_flagged': 0})
    skipped = []
    review_rows = []
    manifests = {split: [] for split in SPLITS}

    for split in SPLITS:
        for row in read_jsonl(split_dir / f'{split}.jsonl'):
            plan = plans[row['audio_sha256']]
            if plan.get('flags'):
                counts['skipped_flagged'] += 1
                counts.update(f"flag:{flag}" for flag in plan['flags'])
                skipped.append({
                    'audio_sha256': row['audio_sha256'],
                    'split': split,
                    'flags': plan['flags'],
                    'status': 'requires_review',
                })
                if render_flagged_review:
                    source = Path(row['local_audio_path'])
                    if not source.is_absolute():
                        source = root / source
                    measured_peak = plan.get('measured_peak_dbfs')
                    peak_safe_gain = plan['recommended_gain_db']
                    if measured_peak is not None:
                        peak_safe_gain = min(peak_safe_gain, -1.0 - measured_peak)
                    output = output_dir / 'review' / 'wav' / split / f"{row['audio_sha256']}.wav"
                    result = render_wav(
                        source,
                        output,
                        peak_safe_gain,
                        plan.get('dc_offset_normalized') or 0,
                    )
                    review_rows.append({
                        **row,
                        'source_audio_sha256': result['source_sha256'],
                        'derived_audio_sha256': result['derived_sha256'],
                        'derived_audio_path': str(output.relative_to(root)),
                        'quality_flags': plan['flags'],
                        'training_eligible': False,
                        'experimental_training_eligible': True,
                        'review_status': 'signal_flagged_experimental',
                        'normalization': {
                            'gain_db': round(peak_safe_gain, 4),
                            'dc_offset_removed': plan.get('dc_offset_normalized') or 0,
                            'target_rms_dbfs': plan.get('target_rms_dbfs'),
                            'peak_ceiling_dbfs': -1.0,
                        },
                    })
                    counts['rendered_review'] += 1
                continue
            source = Path(row['local_audio_path'])
            if not source.is_absolute():
                source = root / source
            output = output_dir / 'wav' / split / f"{row['audio_sha256']}.wav"
            result = render_wav(
                source,
                output,
                plan['recommended_gain_db'],
                plan.get('dc_offset_normalized') or 0,
            )
            manifests[split].append({
                **row,
                'source_audio_sha256': result['source_sha256'],
                'derived_audio_sha256': result['derived_sha256'],
                'derived_audio_path': str(output.relative_to(root)),
                'normalization': {
                    'gain_db': plan['recommended_gain_db'],
                    'dc_offset_removed': plan.get('dc_offset_normalized') or 0,
                    'target_rms_dbfs': plan['target_rms_dbfs'],
                },
            })
            counts['rendered'] += 1
            counts[f'rendered_{split}'] += 1

    manifest_dir = output_dir / 'manifests'
    manifest_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in manifests.items():
        (manifest_dir / f'{split}.jsonl').write_text(
            ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
            encoding='utf-8',
        )
    (output_dir / 'requires_review.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in skipped),
        encoding='utf-8',
    )
    (output_dir / 'review_manifest.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in review_rows),
        encoding='utf-8',
    )
    report = {
        **dict(sorted(counts.items())),
        'source_audio_unchanged': True,
        'selection': 'strict ASR/TTS candidates with an unflagged normalization plan',
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render-flagged-review', action='store_true')
    args = parser.parse_args()
    print(json.dumps(
        build_derived_audio(render_flagged_review=args.render_flagged_review),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ))
