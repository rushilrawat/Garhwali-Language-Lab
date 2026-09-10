"""OCR targeted Garhwali units from additional UOU modules."""

import hashlib
import json
import os
import shutil
import subprocess
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from collect_online import ROOT, existing_text_hashes, make_record, save_records, snapshot


PAGE_RANGES = {
    'MAHL-204': (156, 185),
    'MAHL-611': (5, 130),
}
WORK = ROOT / 'tmp' / 'pdfs' / 'uou_more_ocr'
TESSDATA = WORK / 'tessdata'
POPPLER_BIN = Path('/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin')
FONTCONFIG = Path('/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/etc/fonts/fonts.conf')
TARGET = ROOT / 'restricted' / 'uou_more_pages.jsonl'


def unique_ocr_pages(pages, known_hashes):
    kept = []
    seen = set(known_hashes)
    batch = set()
    stats = {'known_duplicates': 0, 'within_batch_duplicates': 0}
    for item in pages:
        normalized = unicodedata.normalize('NFC', item['text']).strip()
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        if digest in known_hashes:
            stats['known_duplicates'] += 1
            continue
        if digest in batch:
            stats['within_batch_duplicates'] += 1
            continue
        batch.add(digest)
        seen.add(digest)
        kept.append(dict(item, text=normalized, text_sha256=digest))
    return kept, stats


def render(course, pdf_path, first_page, last_page):
    folder = WORK / course
    folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env['FONTCONFIG_FILE'] = str(FONTCONFIG)
    env['XDG_CACHE_HOME'] = '/private/tmp/garhwali-font-cache'
    subprocess.run([
        str(POPPLER_BIN / 'pdftoppm'), '-f', str(first_page), '-l', str(last_page),
        '-r', '180', '-jpeg', '-jpegopt', 'quality=82', str(pdf_path), str(folder / 'page'),
    ], check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return sorted(folder.glob('page-*.jpg'))


def ocr(image):
    result = subprocess.run([
        'tesseract', str(image), 'stdout', '--tessdata-dir', str(TESSDATA),
        '-l', 'hin+eng', '--psm', '6',
    ], check=True, capture_output=True, text=True)
    return image, result.stdout.strip()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    TESSDATA.mkdir(exist_ok=True)
    model, _ = snapshot('uou_cgl', 'hin.traineddata')
    (TESSDATA / 'hin.traineddata').write_bytes(model)
    shutil.copy2('/opt/homebrew/share/tessdata/eng.traineddata', TESSDATA / 'eng.traineddata')
    extracted = []
    source_info = {}
    try:
        for course, (first_page, last_page) in PAGE_RANGES.items():
            _, info = snapshot('uou_more', course + '.pdf')
            source_info[course] = info
            images = render(course, ROOT / info['raw_path'], first_page, last_page)
            expected = last_page - first_page + 1
            if len(images) != expected:
                raise ValueError(f'Expected {expected} rendered pages for {course}, found {len(images)}')
            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(ocr, images))
            for image, text in results:
                if not text:
                    continue
                page_number = int(image.stem.rsplit('-', 1)[-1])
                extracted.append({'course': course, 'page': page_number, 'text': text})

        known = existing_text_hashes(exclude=[str(TARGET.relative_to(ROOT))])
        unique_pages, duplicate_stats = unique_ocr_pages(extracted, known)
        rows = []
        for item in unique_pages:
            info = source_info[item['course']]
            text_value = item['text']
            characters = len(text_value)
            devanagari = sum('\u0900' <= char <= '\u097f' for char in text_value)
            record = make_record(
                'uou_more', f'{item["course"]}:page:{item["page"]}', text_value, info,
                'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'Uttarakhand Open University MAHL study material',
                course_code=item['course'], pdf_page=item['page'],
                usage='restricted_research', corpus_layer='restricted_nc_sa',
                genre='educational_folk_literature', modality='text',
                source_url=f'https://uou.ac.in/sites/default/files/slm/{item["course"]}.pdf',
                rights_evidence='sources/online/uou_more/terms.html.metadata.json',
                rights_status='site_declares_CC_BY_NC_SA_4; quoted_works_require_component_review',
                quality_flags=['machine_ocr', 'noncommercial',
                               'component_rights_review_required', 'needs_native_review'],
                quality_metrics={'characters': characters,
                                 'devanagari_characters': devanagari,
                                 'devanagari_share': round(devanagari / characters, 4)
                                 if characters else 0})
            record['modifications'] = 'Selected PDF page rendered at 180 DPI; Tesseract hin+eng OCR; no correction'
            rows.append(record)
        save_records(TARGET, rows)
        report = {
            'selected_pages': sum(end - start + 1 for start, end in PAGE_RANGES.values()),
            'nonempty_ocr_pages': len(extracted),
            'records_written': len(rows),
            'duplicate_pages_skipped': duplicate_stats,
            'characters': sum(len(row['text_normalized']) for row in rows),
            'excluded_duplicate_source': 'MAHL-610 duplicates the selected MAHL-204 units',
        }
        (ROOT / 'restricted' / 'uou_more_report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        for course in PAGE_RANGES:
            folder = WORK / course
            if folder.exists():
                shutil.rmtree(folder)


if __name__ == '__main__':
    main()
