"""OCR UOU's legacy-font Garhwali course PDFs into auditable page records."""
import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from collect_online import ROOT, make_record, save_records, snapshot
from ingest_incoming_pdfs import FONTCONFIG, PDFTOPPM, TESSERACT, locate_tessdata

WORK = ROOT / 'tmp' / 'pdfs' / 'uou_ocr'
TESSDATA = WORK / 'tessdata'
def render(course, pdf_path):
    if not PDFTOPPM:
        raise FileNotFoundError('pdftoppm is required; install Poppler or set PDFTOPPM_BIN')
    folder = WORK / course
    folder.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if FONTCONFIG and FONTCONFIG.exists():
        env['FONTCONFIG_FILE'] = str(FONTCONFIG)
    env.setdefault('XDG_CACHE_HOME', str(WORK / 'font-cache'))
    subprocess.run([PDFTOPPM, '-r', '180', '-jpeg', '-jpegopt', 'quality=82',
                    str(pdf_path), str(folder / 'page')], check=True, env=env,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return sorted(folder.glob('page-*.jpg'))


def ocr(image):
    if not TESSERACT:
        raise FileNotFoundError('tesseract is required; install it or set TESSERACT_BIN')
    result = subprocess.run([TESSERACT, str(image), 'stdout', '--tessdata-dir',
                             str(TESSDATA), '-l', 'hin+eng', '--psm', '6'],
                            check=True, capture_output=True, text=True)
    return image, result.stdout.strip()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    TESSDATA.mkdir(exist_ok=True)
    model, _ = snapshot('uou_cgl', 'hin.traineddata')
    (TESSDATA / 'hin.traineddata').write_bytes(model)
    locate_tessdata(WORK)
    rows = []
    counts = {}
    try:
        for n in range(101, 105):
            course = f'CGL-{n}'
            _, info = snapshot('uou_cgl', course + '.pdf')
            images = render(course, ROOT / info['raw_path'])
            course_rows = 0
            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(ocr, images))
            for image, text in results:
                if not text:
                    continue
                page_number = int(image.stem.rsplit('-', 1)[-1])
                rec = make_record('uou_cgl', f'{n}:page:{page_number}', text, info,
                    'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                    'Uttarakhand Open University, Certificate in Garhwali Language study material',
                    course_code=course, pdf_page=page_number, usage='restricted_research',
                    corpus_layer='restricted_nc_sa', genre='educational_material', modality='text',
                    quality_flags=['machine_ocr', 'noncommercial',
                                   'component_rights_review_required', 'needs_native_review'],
                    source_url=f'https://uou.ac.in/sites/default/files/slm/{course}.pdf',
                    rights_evidence='sources/online/uou_cgl/terms.html.metadata.json',
                    rights_status='site_declares_CC_BY_NC_SA_4; quoted_works_require_component_review')
                rec['modifications'] = 'PDF page rendered at 180 DPI; Tesseract hin+eng OCR; Unicode NFC and outer whitespace trimming'
                rec['ocr_engine'] = subprocess.check_output([TESSERACT, '--version'], text=True).splitlines()[0]
                rows.append(rec)
                course_rows += 1
            counts[course] = course_rows
            print(course, course_rows, flush=True)
        save_records(ROOT / 'restricted' / 'uou_cgl_pages.jsonl', rows)
        report = {'records': len(rows), 'course_counts': counts,
                  'characters': sum(len(r['text_normalized']) for r in rows)}
        (ROOT / 'restricted' / 'uou_cgl_report.json').write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        for course in [f'CGL-{n}' for n in range(101, 105)]:
            folder = WORK / course
            if folder.exists():
                shutil.rmtree(folder)


if __name__ == '__main__':
    main()
