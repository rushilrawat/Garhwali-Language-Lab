#!/usr/bin/env python3
"""OCR explicitly labeled Garhwali narrative specimens in Grierson's LSI."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PDF = ROOT / 'sources/online/lsi/18ad277529ac22ce-scan.pdf'
SOURCE_SHA256 = '18ad277529ac22ce717ed83e6677b3db2130903f0d2272c0296401d4188ccb56'
HINDI_TESSDATA = ROOT / 'data/extracted/incoming_pdfs/tessdata/hin.traineddata'
DEFAULT_OUTPUT = ROOT / 'data/extracted/historical/lsi_1916_garhwali_specimens.jsonl'
SOURCE_URL = 'https://archive.org/details/LSIV0-V11'
RIGHTS_URL = 'https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu'
LICENSE_ID = 'PDM-1.0'
LICENSE_URL = 'https://creativecommons.org/publicdomain/mark/1.0/'
ATTRIBUTION = 'George A. Grierson, Linguistic Survey of India, Volume IX, Part IV (1916).'
PDF_PAGE_OFFSET = 15

# Printed section headings identify the dialect and specimen. Body crop starts
# were checked against page images; they exclude printed headings and OCR noise.
SPECIMENS = (
    {
        'record_id': 'lsi_1916_garhwali:standard_specimen_1',
        'title': 'The Prodigal Son (Srinagar Garhwali specimen)',
        'pages': ((298, 820), (299, 340)),
        'dialect': 'standard_srinagar',
        'language_evidence': 'Printed section heading: Standard dialect of Srinagar; specimen I.',
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:standard_specimen_2',
        'title': 'Meeting of the East and West Winds (Srinagar Garhwali specimen)',
        'pages': ((303, 820), (304, 300), (305, 300)),
        'dialect': 'standard_srinagar',
        'language_evidence': 'Printed section heading: Standard dialect of Srinagar; specimen II.',
        'genre': 'folk_narrative',
    },
    {
        'record_id': 'lsi_1916_garhwali:lohbya_specimen_4',
        'title': 'The Prodigal Son (Lohbya Garhwali specimen)',
        'pages': ((325, 1250),),
        'dialect': 'lohbya',
        'language_evidence': (
            'Printed heading: Specimen of Lohbya, within the Garhwali section; '
            'the preceding text locates this dialect in British Garhwal.'
        ),
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:badhani_specimen_5',
        'title': 'The Prodigal Son (Badhani Garhwali specimen)',
        'pages': ((328, 1600), (329, 300)),
        'page_min_chars': {329: 80},
        'dialect': 'badhani',
        'language_evidence': (
            'Printed heading: Specimen of Badhani, within the Garhwali section.'
        ),
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:dasaulya_specimen_6',
        'title': 'The Prodigal Son (Dasaulya Garhwali specimen)',
        'pages': ((330, 1250),),
        'dialect': 'dasaulya',
        'language_evidence': (
            'Printed heading: Specimen of Dasaulya, within the Garhwali section; '
            'the preceding description locates the variety in British Garhwal.'
        ),
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:nagpuriya_specimen_8',
        'title': 'The Prodigal Son (Nagpuriya Garhwali specimen)',
        'pages': ((334, 1160),),
        'dialect': 'nagpuriya',
        'language_evidence': (
            'Printed heading: Specimen of the Nagpuriya dialect, within the '
            'Garhwali section; the preceding description locates it in British Garhwal.'
        ),
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:salani_specimen_9',
        'title': 'The Prodigal Son (Salani Garhwali specimen)',
        'pages': ((337, 750), (338, 220)),
        'dialect': 'salani',
        'language_evidence': (
            'Printed heading: Central Pahari (Garhwali), Salani dialect, specimen I.'
        ),
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:tehri_specimen_1',
        'title': 'The Prodigal Son (Tehri Garhwali specimen)',
        'pages': ((345, 900), (346, 300)),
        'dialect': 'tehri',
        'language_evidence': 'Printed section heading: Tehri dialect; specimen I.',
        'genre': 'narrative_translation',
    },
    {
        'record_id': 'lsi_1916_garhwali:tehri_specimen_2',
        'title': 'Garhwali narrative (Tehri specimen II)',
        'pages': ((350, 960),),
        'dialect': 'tehri',
        'language_evidence': 'Printed section heading identifies the Tehri dialect; specimen II.',
        'genre': 'folk_narrative',
    },
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def devanagari_share(text: str) -> float:
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return 0.0
    devanagari = sum('\u0900' <= char <= '\u097f' for char in letters)
    return devanagari / len(letters)


def parse_page_tsv(tsv: str, printed_page: int, body_top: int,
                   min_chars: int = 250) -> tuple[str, float]:
    groups: dict[tuple[str, str, str], list[dict]] = {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter='\t'):
        if row.get('level') != '5' or not row.get('text', '').strip():
            continue
        try:
            word = {
                'left': int(row['left']),
                'top': int(row['top']),
                'confidence': float(row['conf']),
                'text': row['text'].strip(),
            }
        except (KeyError, ValueError):
            continue
        key = (row.get('block_num', ''), row.get('par_num', ''), row.get('line_num', ''))
        groups.setdefault(key, []).append(word)

    lines = []
    confidences = []
    for words in groups.values():
        top = min(word['top'] for word in words)
        if top < body_top or top > 2500:
            continue
        words.sort(key=lambda word: word['left'])
        text = ' '.join(word['text'] for word in words)
        if devanagari_share(text) < 0.65:
            continue
        lines.append((top, text))
        confidences.extend(word['confidence'] for word in words if word['confidence'] >= 0)

    lines.sort(key=lambda item: item[0])
    text = unicodedata.normalize('NFC', ' '.join(line for _, line in lines))
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) < min_chars or devanagari_share(text) < 0.75:
        raise ValueError(f'printed page {printed_page} produced too little Garhwali-script OCR')
    mean_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return text, round(mean_confidence, 2)


def render_page_tsv(pdf: Path, printed_page: int, temp_dir: Path,
                    pdftoppm: str, tesseract: str, tessdata_dir: Path) -> str:
    pdf_page = printed_page + PDF_PAGE_OFFSET
    prefix = temp_dir / f'lsi-page-{pdf_page}'
    subprocess.run(
        [pdftoppm, '-f', str(pdf_page), '-l', str(pdf_page), '-r', '1200',
         '-png', '-singlefile', str(pdf), str(prefix)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    image_path = prefix.with_suffix('.png')
    result = subprocess.run(
        [tesseract, str(image_path), 'stdout', '--tessdata-dir', str(tessdata_dir),
         '-l', 'hin', '--psm', '6', '-c', 'tessedit_create_tsv=1'],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout.decode('utf-8', errors='replace')


def ingest(source_pdf: Path = SOURCE_PDF, output_path: Path = DEFAULT_OUTPUT,
           tessdata_path: Path = HINDI_TESSDATA,
           retrieved_at: str | None = None) -> dict:
    pdf_bytes = source_pdf.read_bytes()
    actual_sha = sha256_bytes(pdf_bytes)
    if actual_sha != SOURCE_SHA256:
        raise ValueError(f'LSI source PDF checksum mismatch: {actual_sha}')
    if not tessdata_path.is_file():
        raise FileNotFoundError(f'missing local Hindi Tesseract model: {tessdata_path}')
    model_sha = sha256_bytes(tessdata_path.read_bytes())
    tessdata_dir = tessdata_path.parent
    pdftoppm = shutil.which('pdftoppm') or (
        '/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/'
        'dependencies/bin/override/pdftoppm'
    )
    tesseract = shutil.which('tesseract')
    if not Path(pdftoppm).exists() or not tesseract:
        raise RuntimeError('pdftoppm and tesseract are required for LSI specimen extraction')

    page_texts: dict[int, tuple[str, float]] = {}
    with tempfile.TemporaryDirectory(prefix='lsi-specimens-') as temp:
        temp_dir = Path(temp)
        for specimen in SPECIMENS:
            for printed_page, body_top in specimen['pages']:
                if printed_page not in page_texts:
                    tsv = render_page_tsv(
                        source_pdf, printed_page, temp_dir, pdftoppm, tesseract,
                        tessdata_dir,
                    )
                    page_texts[printed_page] = parse_page_tsv(
                        tsv, printed_page, body_top,
                        specimen.get('page_min_chars', {}).get(printed_page, 250),
                    )

    retrieved_at = retrieved_at or date.today().isoformat()
    records = []
    for specimen in SPECIMENS:
        page_numbers = [page for page, _ in specimen['pages']]
        text = unicodedata.normalize(
            'NFC', ' '.join(page_texts[page][0] for page in page_numbers),
        )
        text = re.sub(r'\s+', ' ', text).strip()
        digest = sha256_bytes(text.encode('utf-8'))
        mean_conf = round(
            sum(page_texts[page][1] for page in page_numbers) / len(page_numbers), 2,
        )
        record = {
            'record_id': specimen['record_id'],
            'source_id': 'lsi_1916_grierson_garhwali_specimens',
            'title': specimen['title'],
            'author': 'George A. Grierson',
            'publication_year': 1916,
            'source_printed_pages': page_numbers,
            'source_pdf_pages': [page + PDF_PAGE_OFFSET for page in page_numbers],
            'text_original': text,
            'text_normalized': text,
            'text_sha256': digest,
            'source_language_evidence': specimen['language_evidence'],
            'source_url': SOURCE_URL,
            'rights_evidence_url': RIGHTS_URL,
            'source_pdf': 'sources/online/lsi/18ad277529ac22ce-scan.pdf',
            'source_pdf_sha256': SOURCE_SHA256,
            'ocr_model': 'Tesseract 5, hin.traineddata',
            'ocr_model_sha256': model_sha,
            'ocr_mean_confidence': mean_conf,
            'iso_639_3': 'gbm',
            'language': 'Garhwali',
            'script': 'Deva',
            'dialect': specimen['dialect'],
            'genre': specimen['genre'],
            'modality': 'text',
            'license_id': LICENSE_ID,
            'license_url': LICENSE_URL,
            'attribution': ATTRIBUTION,
            'rights_status': 'rights_assessed_compatible',
            'rights_evidence': RIGHTS_URL,
            'corpus_layer': 'core_open',
            'native_reviewed': False,
            'quality_status': 'historical_devanagari_ocr_unreviewed',
            'quality_flags': [
                'historical_source',
                'automated_hindi_ocr_unreviewed',
                'unicode_nfc_applied',
                'page_headings_and_non_garhwali_ocr_lines_excluded',
                'native_review_pending',
            ],
            'training_eligible': False,
            'experimental_training_eligible': True,
            'historical': True,
            'source_citation': (
                f'Grierson, Linguistic Survey of India, Vol. IX, Part IV, '
                f'{specimen["language_evidence"]} Printed page(s) '
                f'{", ".join(map(str, page_numbers))} (1916).'
            ),
            'modifications': (
                'Tesseract Hindi OCR extracted from page images; printed headings '
                'and non-Devanagari OCR lines omitted; NFC and whitespace '
                'normalization only; wording not corrected.'
            ),
            'provenance': {
                'source_url': SOURCE_URL,
                'source_pdf_sha256': SOURCE_SHA256,
                'rights_evidence_url': RIGHTS_URL,
                'source_printed_pages': page_numbers,
                'source_pdf_pages': [page + PDF_PAGE_OFFSET for page in page_numbers],
                'ocr_model_sha256': model_sha,
                'retrieved_at': retrieved_at,
            },
            'extractor_version': 'ingest_lsi_garhwali_specimens_v1',
        }
        records.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in records),
        encoding='utf-8',
    )
    temporary_path.replace(output_path)
    return {
        'source_pdf_sha256': actual_sha,
        'ocr_model_sha256': model_sha,
        'records': len(records),
        'pages': sum(len(item['pages']) for item in SPECIMENS),
        'characters': sum(len(row['text_normalized']) for row in records),
        'devanagari_characters': sum(
            sum('\u0900' <= char <= '\u097f' for char in row['text_normalized'])
            for row in records
        ),
        'unique_texts': len({row['text_sha256'] for row in records}),
        'output': str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path, default=SOURCE_PDF)
    parser.add_argument('--tessdata', type=Path, default=HINDI_TESSDATA)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(ingest(args.source_pdf, args.output, args.tessdata),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
