#!/usr/bin/env python3
"""Extract explicitly labeled Garhwali forms from Grierson's 1916 LSI table.

The source is public domain. Tesseract output is preserved as a historical OCR
transcription and is not presented as native-reviewed or model-ready text.
"""

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
DEFAULT_OUTPUT = ROOT / 'data/extracted/historical/lsi_1916_garhwali_dialect_table.jsonl'
SOURCE_URL = 'https://archive.org/details/LSIV0-V11'
RIGHTS_URL = 'https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu'
LICENSE_ID = 'PDM-1.0'
LICENSE_URL = 'https://creativecommons.org/publicdomain/mark/1.0/'
ATTRIBUTION = 'George A. Grierson, Linguistic Survey of India, Volume IX, Part IV (1916).'

# The table has entries 1–241. The first printed page has 25 rows; later pages
# each carry 27. Even-numbered scans between these table pages are blank.
TABLE_PAGES = (
    (355, 1, 25),
    (357, 26, 52),
    (359, 53, 79),
    (361, 80, 106),
    (363, 107, 133),
    (365, 134, 160),
    (367, 161, 187),
    (369, 188, 214),
    (371, 215, 241),
)
PDF_PAGE_OFFSET = 15
ROW_ANCHOR_CROP = (1310, 50)
COLUMN_CROPS = {
    'standard': (340, 320),
    'rathi': (670, 290),
    'tehri': (980, 310),
    'english': (1360, 340),
}
CROP_TOP = 250
CROP_HEIGHT = 2220
TOKEN_RE = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿĀ-ȳ]')


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean_cell_token(text: str) -> str:
    """Remove table rules/dot-leaders while preserving the OCR spelling."""
    text = unicodedata.normalize('NFC', text.strip())
    text = re.sub(r'^[^A-Za-zÀ-ÖØ-öø-ÿĀ-ȳ]+', '', text)
    text = re.sub(r'[^A-Za-zÀ-ÖØ-öø-ÿĀ-ȳ0-9?]+$', '', text)
    return text


def line_groups(tsv: str, y_offset: int = CROP_TOP) -> list[dict]:
    groups = {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter='\t'):
        if row.get('level') != '5' or not row.get('text', '').strip():
            continue
        try:
            word = {
                'x': int(row['left']),
                'top': int(row['top']),
                'y': int(row['top']) + int(row['height']) / 2 + y_offset,
                'width': int(row['width']),
                'height': int(row['height']),
                'confidence': float(row['conf']),
                'text': row['text'].strip(),
            }
        except (KeyError, ValueError):
            continue
        key = (row.get('block_num', ''), row.get('par_num', ''), row.get('line_num', ''))
        groups.setdefault(key, []).append(word)

    lines = []
    for words in groups.values():
        lines.append({
            'center': sum(word['y'] for word in words) / len(words),
            'top': min(word['top'] for word in words),
            'words': words,
        })
    return sorted(lines, key=lambda line: line['center'])


def row_centers_from_number_column(tsv: str, printed_page: int,
                                  first_item: int, last_item: int) -> list[float]:
    expected = last_item - first_item + 1
    anchors = []
    for line in line_groups(tsv):
        if not 80 < line['top'] < 2200:
            continue
        for word in line['words']:
            match = re.fullmatch(r'\D*(\d{1,3})\D*', word['text'])
            if not match:
                continue
            item_number = int(match.group(1))
            if first_item <= item_number <= last_item and 10 <= word['height'] <= 45:
                anchors.append((item_number, word['y']))
    if len(anchors) < 2:
        raise ValueError(
            f'printed page {printed_page} has too few readable item numbers to '
            f'align {expected} table rows'
        )

    # Number OCR is imperfect, so fit the page's row grid from all token pairs
    # whose item-number delta and vertical delta imply the known ~76px pitch.
    # A robust median offset tolerates occasional misread digits and tall OCR
    # boxes; item IDs, rather than line order, prevent leading misses from
    # shifting every dialect cell onto the next row.
    candidate_pitches = []
    for index, (item_a, y_a) in enumerate(anchors):
        for item_b, y_b in anchors[index + 1:]:
            if item_a == item_b:
                continue
            pitch = (y_b - y_a) / (item_b - item_a)
            if 65 <= pitch <= 85:
                candidate_pitches.append(pitch)
    if not candidate_pitches:
        raise ValueError(f'printed page {printed_page} has no consistent item-number anchors')

    candidate_pitches.sort()
    median_pitch = candidate_pitches[len(candidate_pitches) // 2]
    offsets = sorted(y - (item_number - first_item) * median_pitch
                     for item_number, y in anchors)
    offset = offsets[len(offsets) // 2]
    residuals = [
        abs(y - (offset + (item_number - first_item) * median_pitch))
        for item_number, y in anchors
    ]
    inlier_count = sum(residual <= 16 for residual in residuals)
    if inlier_count < 2:
        raise ValueError(f'printed page {printed_page} has inconsistent item-number anchors')
    return [offset + index * median_pitch for index in range(expected)]


def cells_from_column_tsv(tsv: str, row_centers: list[float]) -> list[dict]:
    if len(row_centers) > 1:
        ordered_pitches = sorted(
            right - left for left, right in zip(row_centers, row_centers[1:])
        )
        pitch = ordered_pitches[len(ordered_pitches) // 2]
    else:
        pitch = 76
    output = [{'text': '', 'confidence': None} for _ in row_centers]
    words_by_row = [[] for _ in row_centers]
    for line in line_groups(tsv):
        for word in line['words']:
            if word['width'] < 10 or word['height'] < 8 or not TOKEN_RE.search(word['text']):
                continue
            index = min(range(len(row_centers)), key=lambda i: abs(word['y'] - row_centers[i]))
            if abs(word['y'] - row_centers[index]) <= pitch * 0.49:
                words_by_row[index].append(word)
    for index, words in enumerate(words_by_row):
        words.sort(key=lambda word: (word['y'], word['x']))
        tokens = [clean_cell_token(word['text']) for word in words]
        tokens = [token for token in tokens if token]
        output[index] = {
            'text': ' '.join(tokens),
            'confidence': (
                round(sum(word['confidence'] for word in words) / len(words), 2)
                if words else None
            ),
        }
    return output


def parse_cropped_page(printed_page: int, first_item: int, last_item: int,
                       anchor_tsv: str, column_tsvs: dict[str, str]) -> list[dict]:
    centers = row_centers_from_number_column(
        anchor_tsv, printed_page, first_item, last_item,
    )
    cells = {
        name: cells_from_column_tsv(tsv, centers)
        for name, tsv in column_tsvs.items()
    }
    output = []
    for offset, item_number in enumerate(range(first_item, last_item + 1)):
        for dialect in ('standard', 'rathi', 'tehri'):
            text = cells[dialect][offset]['text']
            if not text:
                continue
            digest = sha256_bytes(text.encode('utf-8'))
            mean_conf = cells[dialect][offset]['confidence']
            flags = [
                'historical_latin_transliteration', 'automated_ocr_unreviewed',
                'column_cropped_row_aligned_ocr',
            ]
            if mean_conf is None or mean_conf < 60:
                flags.append('low_ocr_confidence')
            output.append({
                'record_id': f'lsi_1916_garhwali_table:{printed_page}:{item_number:03d}:{dialect}',
                'source_id': 'lsi_1916_grierson_garhwali_table',
                'title': 'Linguistic Survey of India, Volume IX, Part IV',
                'author': 'George A. Grierson',
                'publication_year': 1916,
                'printed_page': printed_page,
                'table_item': item_number,
                'text_original': text,
                'text_normalized': text,
                'text_sha256': digest,
                'english_gloss_ocr': cells['english'][offset]['text'],
                'english_gloss_ocr_confidence': cells['english'][offset]['confidence'],
                'source_url': SOURCE_URL,
                'rights_evidence_url': RIGHTS_URL,
                'source_pdf': 'sources/online/lsi/18ad277529ac22ce-scan.pdf',
                'source_pdf_sha256': SOURCE_SHA256,
                'source_pdf_page': printed_page + PDF_PAGE_OFFSET,
                'source_ocr_method': 'Tesseract 5 English OCR on cropped Garhwali dialect columns; row centers fitted from OCR item-number anchors so missed numbers do not shift dialect cells onto neighboring rows',
                'source_row_alignment_method': 'robust linear fit to OCR-recognized printed table item numbers in a separate crop; fixed printed item range used to generate row centers',
                'source_cell_ocr_confidence': mean_conf,
                'source_table_column': f'Garhwali ({dialect.title()})',
                'source_standard_form_ocr': cells['standard'][offset]['text'],
                'iso_639_3': 'gbm',
                'language': 'Garhwali',
                'script': 'Latn',
                'dialect': dialect,
                'genre': 'historical_lexicon_or_phrase_table',
                'modality': 'text',
                'license_id': LICENSE_ID,
                'license_url': LICENSE_URL,
                'attribution': ATTRIBUTION,
                'rights_status': 'rights_assessed_compatible',
                'rights_evidence': RIGHTS_URL,
                'corpus_layer': 'core_open',
                'native_reviewed': False,
                'quality_status': 'historical_source_ocr_unreviewed',
                'quality_flags': flags,
                'training_eligible': False,
                'experimental_training_eligible': True,
                'historical': True,
                'source_citation': f'Grierson, Linguistic Survey of India, Vol. IX, Part IV, table item {item_number}, printed page {printed_page} (1916).',
                'modifications': 'OCR spelling retained; table dot leaders and vertical-rule artifacts removed; NFC and outer whitespace normalization only.',
                'provenance': {
                    'source_url': SOURCE_URL,
                    'source_pdf_sha256': SOURCE_SHA256,
                    'rights_evidence_url': RIGHTS_URL,
                    'printed_page': printed_page,
                    'source_pdf_page': printed_page + PDF_PAGE_OFFSET,
                    'table_item': item_number,
                    'table_column': f'Garhwali ({dialect.title()})',
                    'ocr_confidence': mean_conf,
                    'retrieved_at': date.today().isoformat(),
                },
                'extractor_version': 'ingest_lsi_garhwali_table_v2',
            })
    return output


def render_crop_tsv(pdf: Path, printed_page: int, crop_x: int, crop_width: int,
                    temp_dir: Path, pdftoppm: str, tesseract: str) -> str:
    pdf_page = printed_page + PDF_PAGE_OFFSET
    prefix = temp_dir / f'lsi-page-{pdf_page}-x{crop_x}'
    subprocess.run(
        [pdftoppm, '-f', str(pdf_page), '-l', str(pdf_page), '-r', '1200',
         '-x', str(crop_x), '-y', str(CROP_TOP), '-W', str(crop_width),
         '-H', str(CROP_HEIGHT),
         '-png', '-singlefile', str(pdf), str(prefix)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    image_path = Path(str(prefix) + '.png')
    result = subprocess.run(
        [tesseract, str(image_path), 'stdout', '-l', 'eng', '--psm', '6',
         '-c', 'tessedit_create_tsv=1'],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    return result.stdout.decode('utf-8', errors='replace')


def ingest(source_pdf: Path = SOURCE_PDF, output_path: Path = DEFAULT_OUTPUT,
           retrieved_at: str | None = None) -> dict:
    pdf_bytes = source_pdf.read_bytes()
    actual_sha = sha256_bytes(pdf_bytes)
    if actual_sha != SOURCE_SHA256:
        raise ValueError(f'LSI source PDF checksum mismatch: {actual_sha}')
    pdftoppm = shutil.which('pdftoppm') or (
        '/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/'
        'dependencies/bin/override/pdftoppm'
    )
    tesseract = shutil.which('tesseract')
    if not Path(pdftoppm).exists() or not tesseract:
        raise RuntimeError('pdftoppm and tesseract are required for LSI table extraction')

    all_rows = []
    with tempfile.TemporaryDirectory(prefix='lsi-garhwali-') as temp:
        temp_dir = Path(temp)
        for page, first_item, last_item in TABLE_PAGES:
            anchor_tsv = render_crop_tsv(
                source_pdf, page, *ROW_ANCHOR_CROP, temp_dir, pdftoppm, tesseract,
            )
            column_tsvs = {
                name: render_crop_tsv(
                    source_pdf, page, x, width, temp_dir, pdftoppm, tesseract,
                )
                for name, (x, width) in COLUMN_CROPS.items()
            }
            all_rows.extend(parse_cropped_page(
                page, first_item, last_item, anchor_tsv, column_tsvs,
            ))
    if retrieved_at:
        for row in all_rows:
            row['provenance']['retrieved_at'] = retrieved_at

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in all_rows),
        encoding='utf-8',
    )
    temporary_path.replace(output_path)
    return {
        'source_pdf_sha256': actual_sha,
        'printed_pages': [page for page, _, _ in TABLE_PAGES],
        'table_items': 241,
        'records': len(all_rows),
        'unique_texts': len({row['text_sha256'] for row in all_rows}),
        'dialect_record_counts': {
            dialect: sum(row['dialect'] == dialect for row in all_rows)
            for dialect in ('standard', 'rathi', 'tehri')
        },
        'low_ocr_confidence_records': sum(
            'low_ocr_confidence' in row['quality_flags'] for row in all_rows
        ),
        'output': str(output_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-pdf', type=Path, default=SOURCE_PDF)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    print(json.dumps(ingest(args.source_pdf, args.output), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
