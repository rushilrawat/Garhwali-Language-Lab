#!/usr/bin/env python3
"""Extract only sayings explicitly identified as Garhwali in Upreti (1894)."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path


SOURCE_URL = 'https://archive.org/details/cu31924089930774'
RIGHTS_EVIDENCE_URL = (
    'https://commons.wikimedia.org/wiki/File:Proverbs_%26amp,_folklore_of_Kumaun_and_Garhwal_(IA_cu31924089930774).pdf'
)
SOURCE_TITLE = 'Proverbs & folklore of Kumaun and Garhwal'
SOURCE_AUTHOR = 'Pandit Gaea Datt Upreti'
SOURCE_YEAR = 1894
SOURCE_OCR = Path('data/downloads/archive_cu31924089930774/cu31924089930774_djvu.txt')
EXPECTED_SOURCE_SHA256 = '81e9f4c34dd3cb96efe6118adb75566085a172eeffb9fc2affe894dce8d1f438'
DEFAULT_OUTPUT = Path('data/extracted/folklore/upreti_1894_garhwali_proverbs.jsonl')
LICENSE_ID = 'PDM-1.0'
LICENSE_URL = 'https://creativecommons.org/publicdomain/mark/1.0/'
ATTRIBUTION = 'Pandit Gaea Datt Upreti, Proverbs & folklore of Kumaun and Garhwal (1894); digitized by Cornell University Library and Internet Archive.'

# Preserve the source's Latin transliteration. Include only items with an
# explicit Garhwali/Garhwal label in the printed text; do not infer language
# from neighboring Kumauni/Garhwali material.
SAYINGS = (
    {
        'record_id': 'upreti_1894_garhwali:page038_item01',
        'text': 'Topala ki topa tapa chaundala ko raja.',
        'printed_page': 38,
        'language_evidence': 'pure Garhwali proverb',
        'english_gloss': 'While Topal was getting his cannons ready, Chaundal seized his kingdom; counsel to stay ready and not let matters slide.',
        'quality_flags': ['historical_transliteration', 'not_native_reviewed'],
    },
    {
        'record_id': 'upreti_1894_garhwali:page143_item08',
        'text': 'Kumun son ditha Garha son pitha.',
        'printed_page': 143,
        'language_evidence': 'Used only in Garhwal regarding injustice.',
        'english_gloss': 'One looks toward Kumaun and turns one’s back toward Garhwal; used about partiality and injustice.',
        'quality_flags': ['historical_transliteration', 'not_native_reviewed'],
    },
    {
        'record_id': 'upreti_1894_garhwali:page173_item41',
        'text': 'Kuraaiya apun kamaiya aurana so chumaiya.',
        'printed_page': 173,
        'language_evidence': 'This is a Garhwali proverb',
        'english_gloss': 'Kumaun people earn for themselves but are miserly to others; a historically regional stereotype recorded by the source.',
        'quality_flags': ['historical_transliteration', 'not_native_reviewed', 'historical_regional_stereotype_context'],
    },
    {
        'record_id': 'upreti_1894_garhwali:page300_item38',
        'text': 'Khani pini gadha raige rauntyalo kumun.',
        'printed_page': 300,
        'language_evidence': 'A Garhwali saying.',
        'english_gloss': 'Food and drink are left in Garhwal, but beautiful scenery in Kumaun.',
        'quality_flags': ['historical_transliteration', 'not_native_reviewed'],
    },
    {
        'record_id': 'upreti_1894_garhwali:page406_item75',
        'text': 'Kankarba basi gocbba.',
        'printed_page': 406,
        'language_evidence': 'Garhwal proverb',
        'english_gloss': 'The Kakar bleats; the source applies it to inability or failure.',
        'quality_flags': ['historical_transliteration', 'ocr_transliteration_uncertain', 'not_native_reviewed'],
    },
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def extract_records(source_text: str, source_sha256: str) -> list[dict]:
    lines = source_text.splitlines()
    normalized_lines = [normalize(line) for line in lines]
    normalized_source = ' '.join(normalized_lines)
    line_starts = []
    offset = 0
    for line in normalized_lines:
        line_starts.append(offset)
        offset += len(line) + 1
    matched_line_by_id = {}
    for item in SAYINGS:
        phrase = normalize(item['text'])
        pattern = r'\s+'.join(re.escape(token) for token in phrase.split())
        matches = list(re.finditer(pattern, normalized_source, flags=re.IGNORECASE))
        if len(matches) != 1:
            raise ValueError(f"source phrase missing or ambiguous: {item['text']}")
        first = matches[0].start()
        source_line = next(
            index for index, start in reversed(list(enumerate(line_starts)))
            if start <= first
        )
        matched_line_by_id[item['record_id']] = source_line

    page_markers = []
    for index, line in enumerate(lines):
        match = re.fullmatch(r'\s*\(\s*(\d+)\s*\)\s*', line)
        if match:
            page_markers.append((index, int(match.group(1))))

    rows = []
    for item in SAYINGS:
        source_line = matched_line_by_id[item['record_id']]
        actual_page = next(
            (page for index, page in reversed(page_markers) if index < source_line),
            None,
        )
        if actual_page != item['printed_page']:
            raise ValueError(
                f"unexpected printed page for {item['record_id']}: {actual_page}"
            )
        evidence = normalize(' '.join(lines[source_line:min(len(lines), source_line + 18)]))
        if normalize(item['language_evidence']).casefold() not in evidence.casefold():
            raise ValueError(f"Garhwali language evidence missing for {item['record_id']}")

        text = normalize(item['text'])
        rows.append({
            'record_id': item['record_id'],
            'source_id': 'upreti_1894_garhwali',
            'title': SOURCE_TITLE,
            'author': SOURCE_AUTHOR,
            'publication_year': SOURCE_YEAR,
            'printed_page': item['printed_page'],
            'ocr_line': source_line + 1,
            'text_original': text,
            'text_normalized': text,
            'text_sha256': sha256_bytes(text.encode('utf-8')),
            'english_gloss': item['english_gloss'],
            'source_language_evidence': item['language_evidence'],
            'source_url': SOURCE_URL,
            'rights_evidence_url': RIGHTS_EVIDENCE_URL,
            'source_snapshot_sha256': source_sha256,
            'iso_639_3': 'gbm',
            'language': 'Garhwali',
            'script': 'Latn',
            'genre': 'idiom_or_proverb',
            'modality': 'text',
            'license_id': LICENSE_ID,
            'license_url': LICENSE_URL,
            'attribution': ATTRIBUTION,
            'rights_status': 'rights_assessed_compatible',
            'rights_evidence': RIGHTS_EVIDENCE_URL,
            'corpus_layer': 'core_open',
            'native_reviewed': False,
            'quality_status': 'historical_source_transcription_unreviewed',
            'quality_flags': list(item['quality_flags']),
            'training_eligible': False,
            'experimental_training_eligible': True,
            'historical': True,
            'source_citation': f'{SOURCE_AUTHOR}, {SOURCE_TITLE}, printed page {item["printed_page"]} (1894).',
            'source_file': 'cu31924089930774_djvu.txt',
            'modifications': 'Historical Latin transliteration transcribed from OCR; spelling retained as printed; English gloss stored as metadata, not part of the Garhwali text.',
            'provenance': {
                'source_url': SOURCE_URL,
                'source_snapshot_sha256': source_sha256,
                'printed_page': item['printed_page'],
                'ocr_line': source_line + 1,
                'source_language_evidence': item['language_evidence'],
                'retrieved_at': date.today().isoformat(),
            },
        })
    return rows


def ingest_file(source_path: Path, output_path: Path, retrieved_at: str | None = None,
                expected_source_sha256: str | None = EXPECTED_SOURCE_SHA256) -> dict:
    source_path = Path(source_path)
    output_path = Path(output_path)
    source_bytes = source_path.read_bytes()
    source_sha256 = sha256_bytes(source_bytes)
    if expected_source_sha256 and source_sha256 != expected_source_sha256:
        raise ValueError(f'source OCR checksum mismatch: {source_sha256}')
    rows = extract_records(source_bytes.decode('utf-8'), source_sha256)
    if retrieved_at:
        for row in rows:
            row['provenance']['retrieved_at'] = retrieved_at

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows),
        encoding='utf-8',
    )
    temporary_path.replace(output_path)
    return {
        'records': len(rows),
        'unique_texts': len({row['text_sha256'] for row in rows}),
        'characters': sum(len(row['text_normalized']) for row in rows),
        'source_sha256': source_sha256,
        'source_url': SOURCE_URL,
        'license_id': LICENSE_ID,
        'output': str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE_OCR)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(ingest_file(args.source, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
