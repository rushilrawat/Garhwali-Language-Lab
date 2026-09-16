#!/usr/bin/env python3
"""Materialize the reviewed Garhwali popular-song metadata catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'research/garhwali-popular-song-catalog.json'
OUTPUT = ROOT / 'data/extracted/popular_songs'


def youtube_video_id(url):
    parsed = urlparse(url)
    if parsed.netloc not in {'youtube.com', 'www.youtube.com'}:
        raise ValueError(f'Unsupported YouTube URL: {url}')
    values = parse_qs(parsed.query).get('v', [])
    if len(values) != 1 or not values[0]:
        raise ValueError(f'Missing YouTube video ID: {url}')
    return values[0]


def validate_song(row):
    required = {
        'record_id', 'title', 'artists', 'language', 'genre',
        'popularity_basis', 'youtube_url', 'caption_status',
        'lyrics_sources', 'translation_sources', 'theme_summary_en',
        'rights_status',
    }
    missing = sorted(required - row.keys())
    if missing:
        raise ValueError(f"{row.get('record_id', 'unknown')} missing {missing}")
    if row['language'] != 'Garhwali':
        raise ValueError(f"Non-Garhwali record: {row['record_id']}")
    forbidden = {'lyrics_text', 'translation_text', 'audio_path', 'transcript'}
    present = sorted(forbidden & row.keys())
    if present:
        raise ValueError(f"Copyrighted payload fields are not allowed: {present}")
    return {**row, 'youtube_video_id': youtube_video_id(row['youtube_url'])}


def run(catalog_path=CATALOG, output=OUTPUT):
    catalog = json.loads(Path(catalog_path).read_text(encoding='utf-8'))
    rows = [validate_song(row) for row in catalog['songs']]
    ids = [row['record_id'] for row in rows]
    videos = [row['youtube_video_id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate popular-song record IDs')
    if len(videos) != len(set(videos)):
        raise ValueError('Duplicate popular-song YouTube videos')

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'records.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )
    report = {
        'catalog_id': catalog['catalog_id'],
        'records': len(rows),
        'artists': dict(sorted(Counter(
            artist for row in rows for artist in row['artists']
        ).items())),
        'genres': dict(sorted(Counter(row['genre'] for row in rows).items())),
        'public_caption_checks': sum(
            row['caption_status'].startswith('no_public_caption_tracks')
            for row in rows
        ),
        'records_with_lyrics_source': sum(bool(row['lyrics_sources']) for row in rows),
        'records_with_translation_source': sum(
            bool(row['translation_sources']) for row in rows
        ),
        'full_lyrics_copied': 0,
        'full_translations_copied': 0,
        'audio_downloaded': 0,
        'status': 'metadata_and_source_layer_ready',
    }
    (output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.catalog, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
