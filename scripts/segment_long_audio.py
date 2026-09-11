#!/usr/bin/env python3
"""Segment archived long-form Garhwali audio into reviewable derived WAV clips."""

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'data/downloads/folklore/podcast/manifest.json'
DEFAULT_OUTPUT = ROOT / 'data/processed/long_form_audio'
SILENCE_END = re.compile(r'silence_end:\s*([0-9]+(?:\.[0-9]+)?)')


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def parse_silence_ends(output):
    return [float(match.group(1)) for match in SILENCE_END.finditer(output)]


def build_segment_bounds(duration, silence_ends, min_seconds=2.0, max_seconds=29.5):
    """Cover an audio file with segments, preferring the latest usable silence."""
    if duration <= 0:
        return []
    silences = sorted({point for point in silence_ends if 0 < point < duration})
    bounds = []
    start = 0.0
    while duration - start > max_seconds:
        usable = [
            point for point in silences
            if start + min_seconds <= point <= start + max_seconds
        ]
        end = usable[-1] if usable else min(start + max_seconds, duration)
        bounds.append((round(start, 3), round(end, 3)))
        start = end
    if duration - start > 0.001:
        if bounds and duration - start < min_seconds:
            previous_start, _ = bounds.pop()
            bounds.append((previous_start, round(duration, 3)))
        else:
            bounds.append((round(start, 3), round(duration, 3)))
    return bounds


def probe_duration(path):
    result = subprocess.run(
        [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def detect_silence(path, noise_db=-35, silence_duration=0.5):
    result = subprocess.run(
        [
            'ffmpeg', '-hide_banner', '-nostats', '-i', str(path),
            '-af', f'silencedetect=noise={noise_db}dB:d={silence_duration}',
            '-f', 'null', '-',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return parse_silence_ends(result.stderr)


def render_clip(source, output, start, end):
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
            '-ss', str(start), '-i', str(source), '-t', str(end - start),
            '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', str(output),
        ],
        check=True,
    )


def segment_collection(
    manifest_path=DEFAULT_MANIFEST,
    output_dir=DEFAULT_OUTPUT,
    root=ROOT,
    max_seconds=29.5,
):
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    source_manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    rows = []
    counts = Counter()
    for episode in source_manifest['episodes']:
        source = manifest_path.parent / episode['local_file']
        if file_sha256(source) != episode['sha256']:
            raise ValueError(f"source hash mismatch: {source}")
        duration = probe_duration(source)
        silences = detect_silence(source)
        bounds = build_segment_bounds(duration, silences, max_seconds=max_seconds)
        episode_key = f"{episode['position']:03d}_{episode['guid']}"
        for index, (start, end) in enumerate(bounds, start=1):
            output = output_dir / 'wav' / episode_key / f'{index:05d}.wav'
            if not output.exists():
                render_clip(source, output, start, end)
                counts['rendered_clips'] += 1
            else:
                counts['reused_clips'] += 1
            try:
                derived_path = str(output.relative_to(root))
            except ValueError:
                derived_path = str(output)
            rows.append({
                'clip_id': f'{episode_key}:{index:05d}',
                'episode_guid': episode['guid'],
                'episode_position': episode['position'],
                'episode_title': episode['title'],
                'source_url': episode['source_url'],
                'source_audio_path': str(source.relative_to(root)),
                'source_audio_sha256': episode['sha256'],
                'source_duration_seconds': round(duration, 3),
                'start_seconds': start,
                'end_seconds': end,
                'duration_seconds': round(end - start, 3),
                'derived_audio_path': derived_path,
                'derived_audio_sha256': file_sha256(output),
                'audio_format': 'wav_pcm_s16le_mono_16000hz',
                'rights_status': episode['rights_status'],
                'training_eligible': False,
                'review_status': 'needs_transcription_and_rights_review',
            })
        counts['episodes'] += 1
        counts['clips'] += len(bounds)
        print(f"episode={episode['position']}/66 clips={len(bounds)}", flush=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'manifest.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )
    report = {
        **dict(sorted(counts.items())),
        'total_duration_hours': round(sum(row['duration_seconds'] for row in rows) / 3600, 6),
        'max_segment_seconds': max_seconds,
        'source_audio_unchanged': True,
        'training_eligible': False,
        'reason': 'creator-copyright audio requires rights and transcript review',
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--max-seconds', type=float, default=29.5)
    args = parser.parse_args()
    print(json.dumps(segment_collection(args.manifest, args.output, max_seconds=args.max_seconds), indent=2))


if __name__ == '__main__':
    main()
