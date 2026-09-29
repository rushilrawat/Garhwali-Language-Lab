#!/usr/bin/env python3
"""Ingest the licensed, versioned Garhwali Open Bible Stories text release."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
import zipfile
from datetime import date
from pathlib import Path


SOURCE_URL = 'https://git.door43.org/OBS-TLF/gbm_obs'
SOURCE_REVISION = 'f08afc73e1770129fbcd3089181f2faf2abbf54d'
SOURCE_VERSION = 'v1'
LICENSE_ID = 'CC-BY-SA-4.0'
LICENSE_URL = 'https://creativecommons.org/licenses/by-sa/4.0/'
ATTRIBUTION = 'The Love Fellowship, Garhwali Open Bible Stories (TLF), version 1'
DEFAULT_ARCHIVE = Path('data/downloads/obs_tlf_gbm_v1/gbm_obs_v1.zip')
DEFAULT_OUTPUT = Path('data/extracted/obs_tlf_v1/records.jsonl')


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def parse_story(markdown: str, number: int) -> tuple[str, str, str]:
    markdown = unicodedata.normalize('NFC', markdown)
    lines = markdown.splitlines()
    if not lines:
        raise ValueError(f'Story {number} is empty')
    heading = re.fullmatch(rf'\s*#\s*{number}\.\s*(.+?)\s*', lines[0])
    if not heading:
        raise ValueError(f'Story {number} has an unexpected heading')
    title = heading.group(1).strip()

    content = [line.strip() for line in lines[1:]]
    while content and not content[-1]:
        content.pop()
    citation = ''
    if content and re.fullmatch(r'_([^\n]+)_', content[-1]):
        citation = content.pop()[1:-1].strip()

    body_lines = []
    for line in content:
        if re.fullmatch(r'!\[[^\]]*\]\([^)]*\)', line):
            continue
        # Refuse embedded Markdown links/images rather than silently retaining
        # inaccessible markup in a plain-text training/export view.
        line = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', line)
        if line:
            body_lines.append(line)
    body = re.sub(r'\s+', ' ', ' '.join(body_lines)).strip()
    text = f'{title}. {body}'.strip()
    if not body:
        raise ValueError(f'Story {number} has no narrative text')
    devanagari = sum('\u0900' <= char <= '\u097f' for char in text)
    letters = sum(char.isalpha() for char in text)
    if letters == 0 or devanagari / letters < 0.5:
        raise ValueError(f'Story {number} is not predominantly Devanagari')
    return title, text, citation


def ingest_archive(archive_path: Path, output_path: Path,
                   retrieved_at: str | None = None) -> dict:
    archive_path = Path(archive_path)
    output_path = Path(output_path)
    archive_bytes = archive_path.read_bytes()
    archive_sha256 = sha256_bytes(archive_bytes)
    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        manifest_path = 'gbm_obs/manifest.yaml'
        license_path = 'gbm_obs/LICENSE.md'
        if manifest_path not in names or license_path not in names:
            raise ValueError('Archive is missing its language manifest or license text')
        manifest = archive.read(manifest_path).decode('utf-8')
        license_text = archive.read(license_path).decode('utf-8')
        if not re.search(r'identifier:\s*[\'\"]?gbm\b', manifest):
            raise ValueError('Archive manifest does not identify Garhwali (gbm)')
        if not re.search(r'rights:\s*[\'\"]?CC BY-SA 4\.0', manifest):
            raise ValueError('Archive manifest does not declare CC BY-SA 4.0')
        if 'Creative Commons Attribution-ShareAlike 4.0 International' not in license_text:
            raise ValueError('Archive does not contain the expected CC BY-SA 4.0 license')

        story_paths = [f'gbm_obs/content/{number:02}.md' for number in range(1, 51)]
        missing = [path for path in story_paths if path not in names]
        if missing:
            raise ValueError(f'Expected all 50 stories; missing {len(missing)} story files')

        retrieved_at = retrieved_at or date.today().isoformat()
        rows = []
        for number, path in enumerate(story_paths, start=1):
            source_text = archive.read(path).decode('utf-8')
            title, text, citation = parse_story(source_text, number)
            text = unicodedata.normalize('NFC', text)
            rows.append({
                'record_id': f'obs_tlf_gbm_v1:{number:03d}',
                'source_id': 'obs_tlf_gbm_v1',
                'title': title,
                'text_original': text,
                'text_normalized': text,
                'text_sha256': sha256_bytes(text.encode('utf-8')),
                'source_citation': citation,
                'source_url': SOURCE_URL,
                'source_version': SOURCE_VERSION,
                'source_revision': SOURCE_REVISION,
                'source_file': path,
                'source_archive_sha256': archive_sha256,
                'source_snapshot_sha256': sha256_bytes(archive.read(path)),
                'retrieved_at': retrieved_at,
                'iso_639_3': 'gbm',
                'language': 'Garhwali',
                'script': 'Deva',
                'genre': 'religious_narrative',
                'modality': 'text',
                'license_id': LICENSE_ID,
                'license_url': LICENSE_URL,
                'attribution': ATTRIBUTION,
                'rights_status': 'rights_assessed_compatible',
                'rights_evidence': f'{SOURCE_URL}/src/tag/{SOURCE_VERSION}/gbm_obs/manifest.yaml',
                'provenance': {
                    'source_url': SOURCE_URL,
                    'source_revision': SOURCE_REVISION,
                    'source_version': SOURCE_VERSION,
                    'source_file': path,
                    'source_archive_sha256': archive_sha256,
                    'source_snapshot_sha256': sha256_bytes(archive.read(path)),
                    'retrieved_at': retrieved_at,
                },
                'corpus_layer': 'core_open',
                'native_reviewed': False,
                'quality_status': 'unreviewed',
                'quality_flags': [
                    'translation_quality_unreviewed',
                    'native_review_pending',
                    'illustrations_excluded',
                    'official_source_version',
                ],
                'training_eligible': False,
                'experimental_training_eligible': True,
                'historical': False,
                'modifications': 'Markdown title and narrative extracted; image links and final source citation removed from text; Unicode NFC.',
                'extractor_version': 'ingest_obs_tlf_v1',
            })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )
    temporary_path.replace(output_path)
    return {
        'records': len(rows),
        'characters': sum(len(row['text_normalized']) for row in rows),
        'unique_texts': len({row['text_sha256'] for row in rows}),
        'source_url': SOURCE_URL,
        'source_revision': SOURCE_REVISION,
        'source_version': SOURCE_VERSION,
        'source_archive_sha256': archive_sha256,
        'license_id': LICENSE_ID,
        'output': str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(ingest_archive(args.archive, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
