"""Auditable public-source collection. No credentials, access bypasses or uploads.

Snapshots are content addressed. The source ledger records successful and failed
requests. Corpus promotion is always a separate, human-reviewed operation.
"""
import argparse
import csv
import hashlib
import html
import io
import json
import gzip
import re
import subprocess
import time
import unicodedata
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, quote

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'sources' / 'online'
CORPUS = ROOT / 'corpus'
LOG = RAW / 'requests.jsonl'
VERSION = 'online-0.1'
BY = 'https://creativecommons.org/licenses/by/4.0/'
SA = 'https://creativecommons.org/licenses/by-sa/4.0/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def fetch(source, name, url, max_time=55, max_size=100000000):
    folder = RAW / source
    folder.mkdir(parents=True, exist_ok=True)
    pointer = folder / (name + '.metadata.json')
    if pointer.exists():
        info = json.loads(pointer.read_text())
        data = (ROOT / info['raw_path']).read_bytes()
        if info['url'] != url or sha(data) != info['sha256']:
            raise ValueError(f'Snapshot mismatch: {pointer}')
        return data, info
    try:
        if source == 'wiktionary_en':
            time.sleep(2)  # Respect the public API after its earlier rate-limit response.
        p = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            '--max-time', str(max_time), '--retry', '1', '--max-filesize', str(max_size),
                            '--user-agent', 'GarhwaliLanguageLab/0.1 (public corpus research)', url],
                           capture_output=True, check=True)
        data = p.stdout
        path = folder / (sha(data)[:16] + '-' + name)
        path.write_bytes(data)
        info = dict(url=url, retrieved_at=now(), sha256=sha(data),
                    raw_path=str(path.relative_to(ROOT)), bytes=len(data))
        pointer.write_text(json.dumps(info, ensure_ascii=False, indent=2))
        event = dict(source_id=source, status='downloaded', **info)
    except subprocess.CalledProcessError as e:
        event = dict(source_id=source, url=url, retrieved_at=now(), status='failed',
                     error=e.stderr.decode(errors='replace')[-1000:])
        with LOG.open('a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')
        raise RuntimeError(event['error']) from e
    with LOG.open('a') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')
    return data, info


def get_json(source, name, url):
    data, info = fetch(source, name, url)
    return json.loads(data), info


def save_derived_snapshot(source, name, data, inputs, **extra):
    """Store a deterministic derived snapshot beside its immutable inputs."""
    folder = RAW / source
    folder.mkdir(parents=True, exist_ok=True)
    pointer = folder / (name + '.metadata.json')
    digest = sha(data)
    path = folder / (digest[:16] + '-' + name)
    if pointer.exists():
        info = json.loads(pointer.read_text())
        existing = ROOT / info['raw_path']
        if not existing.exists() or sha(existing.read_bytes()) != info['sha256']:
            raise ValueError(f'Derived snapshot mismatch: {pointer}')
        if info.get('input_sha256s') != inputs:
            raise ValueError(f'Derived snapshot inputs changed: {pointer}')
        return existing.read_bytes(), info
    path.write_bytes(data)
    info = dict(url='derived:range-extracted-transcript-columns', retrieved_at=now(),
                sha256=digest, raw_path=str(path.relative_to(ROOT)), bytes=len(data),
                input_sha256s=inputs, **extra)
    pointer.write_text(json.dumps(info, ensure_ascii=False, indent=2))
    with LOG.open('a') as f:
        f.write(json.dumps(dict(source_id=source, status='derived', **info), ensure_ascii=False) + '\n')
    return data, info


class HTTPRangeReader(io.RawIOBase):
    """Seekable, block-cached HTTP reader that refuses non-range responses."""

    def __init__(self, url, size, block_size=4 * 1024 * 1024, timeout=120):
        import requests
        self.url = url
        self.size = size
        self.block_size = block_size
        self.timeout = timeout
        self.position = 0
        self.blocks = {}
        self.range_requests = 0
        self.fetched_bytes = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'GarhwaliLanguageLab/0.1 (public corpus research)'})

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        elif whence == io.SEEK_END:
            position = self.size + offset
        else:
            raise ValueError(f'Unsupported seek mode: {whence}')
        if position < 0:
            raise ValueError('Negative seek position')
        self.position = position
        return position

    def _block(self, index):
        if index in self.blocks:
            return self.blocks[index]
        start = index * self.block_size
        end = min(self.size, start + self.block_size) - 1
        expected = end - start + 1
        error = None
        for attempt in range(3):
            try:
                response = self.session.get(self.url, headers={'Range': f'bytes={start}-{end}'},
                                            timeout=self.timeout, allow_redirects=True, stream=True)
                if response.status_code != 206:
                    response.close()
                    raise OSError(f'Range request returned HTTP {response.status_code}')
                content_range = response.headers.get('Content-Range', '')
                if not content_range.startswith(f'bytes {start}-{end}/'):
                    response.close()
                    raise OSError(f'Unexpected Content-Range: {content_range!r}')
                data = response.content
                response.close()
                if len(data) != expected:
                    raise OSError(f'Short range response: {len(data)} != {expected}')
                self.blocks[index] = data
                self.range_requests += 1
                self.fetched_bytes += len(data)
                return data
            except Exception as exc:
                error = exc
                if attempt < 2:
                    time.sleep(1 + attempt)
        raise OSError(f'Failed range {start}-{end} for {self.url}: {error}')

    def read(self, size=-1):
        if self.position >= self.size:
            return b''
        if size is None or size < 0:
            size = self.size - self.position
        size = min(size, self.size - self.position)
        chunks = []
        remaining = size
        while remaining:
            block_index = self.position // self.block_size
            block_offset = self.position % self.block_size
            block = self._block(block_index)
            take = min(remaining, len(block) - block_offset)
            chunks.append(block[block_offset:block_offset + take])
            self.position += take
            remaining -= take
        return b''.join(chunks)

    def readinto(self, buffer):
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def close(self):
        if not self.closed:
            self.session.close()
        super().close()


def make_record(source, key, text, info, license_id, license_url, attribution, **extra):
    normalized = unicodedata.normalize('NFC', text).strip()
    if not normalized:
        raise ValueError('Empty text')
    return dict(record_id=f'{source}:{key}', source_id=source, text_original=text,
                text_normalized=normalized, text_sha256=sha(normalized.encode()),
                iso_639_3='gbm', script='Deva', license_id=license_id,
                license_url=license_url, attribution=attribution, provenance=info,
                extractor_version=VERSION, modifications='Unicode NFC and outer whitespace trimming only',
                native_reviewed=False, quality_status='unreviewed', training_eligible=False,
                historical=False, **extra)


def save_records(path, rows):
    ids = set()
    for row in rows:
        if not all(row.get(k) for k in ('record_id', 'text_original', 'license_url', 'attribution', 'provenance')):
            raise ValueError('Incomplete corpus record')
        if row['record_id'] in ids:
            raise ValueError('Duplicate record ID: ' + row['record_id'])
        ids.add(row['record_id'])
    if not rows:
        raise ValueError('Refusing to replace a source with an empty extraction')
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    temp.replace(path)


def csv_dict_rows(data):
    return list(csv.DictReader(io.StringIO(data.decode('utf-8-sig'))))


def latin_record(source, key, text, info, attribution, **extra):
    record = make_record(source, key, text, info, 'CC-BY-4.0', BY, attribution, **extra)
    record['script'] = 'Latn'
    return record


def sand_garhwali_records(data, info):
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'Garhwali':
            continue
        rows.append(latin_record(
            'sand_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'South Asian Numeral Database contributors; source mephd2021; Numeralbank editors',
            corpus_layer='core_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            segments=item.get('Segments'), source_bibliography=item.get('Source'),
            source_url='https://github.com/numeralbank/sand/tree/v1.0',
            rights_evidence='https://zenodo.org/records/15463198'))
    return rows


def chan_garhwali_records(data, info):
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'garh1243-2':
            continue
        rows.append(latin_record(
            'chan_numerals_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'Eugene Chan numeral data; Numeralbank CLDF editors',
            corpus_layer='core_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            segments=item.get('Segments'), other_form=item.get('Other_Form'),
            variant_id=item.get('Variant_ID'), source_bibliography=item.get('Source'),
            upstream_language_id=item.get('Language_ID'),
            source_url='https://github.com/numeralbank/channumerals/tree/v1.0.2',
            rights_evidence='https://zenodo.org/records/15654191'))
    return rows


def mamta_garhwali_records(values_data, values_info, examples_data, examples_info):
    values = []
    for item in csv_dict_rows(values_data):
        if item.get('Language_ID') != 'garh1243':
            continue
        values.append(latin_record(
            'mamta_southasia_values', item['ID'], item['Value'], values_info,
            'Special Numerals in South Asian Languages contributors and CLDF editors',
            corpus_layer='reference_open', genre='numeral_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), example_ids=item.get('Example_IDs'),
            source_url='https://github.com/cldf-datasets/mamtasouthasia/tree/v1.0',
            rights_evidence='https://zenodo.org/records/17985722'))
    examples = []
    for item in csv_dict_rows(examples_data):
        if item.get('Language_ID') != 'garh1243':
            continue
        examples.append(latin_record(
            'mamta_southasia_examples', item['ID'], item['Primary_Text'], examples_info,
            'Special Numerals in South Asian Languages contributors and CLDF editors',
            corpus_layer='core_open', genre='translated_example', modality='text',
            analyzed_word=item.get('Analyzed_Word'), gloss=item.get('Gloss'),
            translation=item.get('Translated_Text'), lgr_conformance=item.get('LGR_Conformance'),
            source_url='https://github.com/cldf-datasets/mamtasouthasia/tree/v1.0',
            rights_evidence='https://zenodo.org/records/17985722'))
    return values, examples


def lsi_cldf_garhwali_records(data, info):
    rows = []
    for item in csv_dict_rows(data):
        if item.get('Language_ID') != 'GARHWALI':
            continue
        record = latin_record(
            'lsi_cldf_garhwali', item['ID'], item.get('Form') or item['Value'], info,
            'George A. Grierson, Linguistic Survey of India; Lexibank CLDF editors',
            corpus_layer='historical_review', genre='historical_lexicon', modality='text',
            parameter_id=item.get('Parameter_ID'), value=item.get('Value'),
            segments=item.get('Segments'), source_bibliography=item.get('Source'),
            source_url='https://github.com/lexibank/lsi/tree/v1.0',
            rights_evidence='https://zenodo.org/records/8361936',
            quality_flags=['structured_derivative_of_existing_lsi_ocr',
                           'source_level_duplicate_expected'])
        record['historical'] = True
        rows.append(record)
    return rows


class OBSTextParser(HTMLParser):
    TARGET_CLASSES = {'mt', 's', 'p', 'pmr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.div_depth = 0
        self.content_depth = None
        self.capture_depth = None
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'div':
            self.div_depth += 1
            if self.content_depth is None and attrs.get('id') == 'content':
                self.content_depth = self.div_depth
            elif self.content_depth is not None and self.capture_depth is None:
                classes = set(attrs.get('class', '').split())
                if classes & self.TARGET_CLASSES:
                    self.capture_depth = self.div_depth
                    self.parts = []
        elif tag == 'br' and self.capture_depth is not None:
            self.parts.append(' ')

    def handle_data(self, data):
        if self.capture_depth is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag != 'div':
            return
        if self.capture_depth == self.div_depth:
            text = ' '.join(''.join(self.parts).split())
            if text and text != '&nbsp;':
                self.blocks.append(text)
            self.capture_depth = None
            self.parts = []
        if self.content_depth == self.div_depth:
            self.content_depth = None
        self.div_depth -= 1


def obs_text_blocks(data):
    parser = OBSTextParser()
    parser.feed(data.decode('utf-8'))
    return parser.blocks


def obs_garhwali_record(story_number, data, info):
    blocks = obs_text_blocks(data)
    if len(blocks) < 2:
        raise ValueError(f'OBS story {story_number} has too little extracted text')
    text_value = '\n\n'.join(blocks)
    devanagari = sum('\u0900' <= char <= '\u097f' for char in text_value)
    alphabetic = sum(char.isalpha() for char in text_value)
    if alphabetic == 0 or devanagari / alphabetic < 0.5:
        raise ValueError(f'OBS story {story_number} is not predominantly Devanagari')
    return make_record(
        'obs_garhwali', f'{story_number:03d}', text_value, info,
        'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'Garhwali Open Bible Stories translators; Free Bibles India / IPS Apps',
        story_number=story_number, corpus_layer='restricted_nc_sa',
        genre='translated_bible_story', modality='text',
        source_url=f'https://media.ipsapps.org/in/osa/stories/36-Garhwali-{story_number:03d}.html',
        rights_evidence='sources/online/obs_garhwali/catalog.html.metadata.json',
        quality_flags=['translation_quality_unreviewed', 'item_page_has_no_license_block',
                       'illustrations_excluded'])


def djvu_word_pages(data):
    root = ET.fromstring(data)
    pages = []
    for page in root.findall('.//OBJECT'):
        lines = []
        for line in page.findall('.//LINE'):
            text = ' '.join((word.text or '').strip() for word in line.findall('WORD')).strip()
            if text:
                lines.append(text)
        pages.append('\n'.join(lines))
    return pages


def obs_garhwali_record(story_number, data, info):
    blocks = obs_text_blocks(data)
    if len(blocks) < 2:
        raise ValueError(f'Open Bible Story {story_number} has too little text')
    return make_record(
        'obs_garhwali', f'{story_number:03d}', '\n\n'.join(blocks), info,
        'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'Garhwali Open Bible Stories contributors; Free Bibles India / unfoldingWord source family',
        corpus_layer='restricted_nc_sa', genre='religious_narrative', modality='text',
        story_number=story_number,
        source_url=f'https://media.ipsapps.org/in/osa/stories/36-Garhwali-{story_number:03d}.html',
        rights_evidence='sources/online/obs_garhwali/catalog.html.metadata.json',
        rights_status='catalog_footer_CC_BY_NC_SA_4; item_page_has_no_license_block',
        quality_flags=['item_page_has_no_license_block', 'translation_quality_unreviewed',
                       'illustrations_excluded'])


def garhwali_section(text):
    match = re.search(r'^==\s*Garhwali\s*==\s*\n(.*?)(?=^==[^=]|\Z)', text, re.M | re.S)
    return match.group(1).strip() if match else ''


def meta_record(row, split, index, info):
    if row.get('iso_639_3') != 'gbm':
        raise ValueError('Non-Garhwali row in Garhwali configuration')
    key = ':'.join(str(row.get(k, '')) for k in ('speaker_id', 'prompt_id', 'segment_id'))
    return make_record('meta_omni', key, row['raw_text'], info, 'CC-BY-4.0', BY,
                       'Meta Omnilingual ASR Corpus contributors; see saved upstream dataset card',
                       split=split, upstream_row_index=index, speaker_id=row.get('speaker_id'),
                       prompt_id=row.get('prompt_id'), prompt=row.get('prompt'),
                       segment_id=row.get('segment_id'), duration_seconds=row.get('duration'),
                       modality='speech_transcript', genre='prompted_speech', corpus_layer='core_open',
                       source_url='https://huggingface.co/datasets/facebook/omnilingual-asr-corpus',
                       rights_evidence='sources/online/meta_omni/card.md.metadata.json',
                       audio_downloaded=False)


def meta():
    dataset = 'facebook/omnilingual-asr-corpus'
    card, _ = fetch('meta_omni', 'card.md', f'https://huggingface.co/datasets/{dataset}/raw/main/README.md')
    if b'cc-by-4.0' not in card.lower():
        raise ValueError('Upstream CC BY license evidence absent')
    payload, _ = get_json('meta_omni', 'splits.json', 'https://datasets-server.huggingface.co/splits?' + urlencode(dict(dataset=dataset)))
    splits = [s for s in payload['splits'] if s['config'] == 'gbm_Deva']
    if not splits:
        raise ValueError('No upstream gbm_Deva configuration')
    rows = []
    for s in splits:
        offset = 0
        while True:
            params = dict(dataset=dataset, config='gbm_Deva', split=s['split'], offset=offset, length=100)
            data, info = get_json('meta_omni', f'{s["split"]}-{offset}.json',
                                  'https://datasets-server.huggingface.co/rows?' + urlencode(params))
            batch = data['rows']
            if not batch:
                raise ValueError('Pagination ended before upstream total')
            for r in batch:
                if 'raw_text' in r.get('truncated_cells', []):
                    raise ValueError('Truncated transcript')
                rows.append(meta_record(r['row'], s['split'], r['row_idx'], info))
            offset += len(batch)
            print(f'meta {s["split"]}: {offset}/{data["num_rows_total"]}', flush=True)
            if offset >= data['num_rows_total']:
                break
    save_records(CORPUS / 'meta_omni.jsonl', rows)
    return len(rows)


def survey():
    queries = {
        'hf_garhwali': 'https://huggingface.co/api/datasets?' + urlencode(dict(search='garhwali', limit=100, full='true')),
        'hf_gbm': 'https://huggingface.co/api/datasets?' + urlencode(dict(filter='language:gbm', limit=100, full='true')),
        'hf_pahari': 'https://huggingface.co/api/datasets?' + urlencode(dict(search='pahari', limit=100, full='true')),
        'ia_garhwali': 'https://archive.org/advancedsearch.php?' + urlencode({'q': 'garhwali', 'output': 'json', 'rows': 1000, 'page': 1, 'fl[]': ['identifier', 'title', 'creator', 'date', 'language', 'licenseurl']}, doseq=True),
        'github_garhwali': 'https://api.github.com/search/repositories?' + urlencode(dict(q='garhwali', per_page=100)),
        'vaani_splits': 'https://datasets-server.huggingface.co/splits?' + urlencode(dict(dataset='ARTPARK-IISc/Vaani-transcription-part')),
        'vaani_card': 'https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part/raw/main/README.md',
        'lsi_metadata': 'https://archive.org/metadata/LSIV0-V11',
        'proverbs_metadata': 'https://archive.org/metadata/cu31924089930774',
        'kaikki': 'https://kaikki.org/dictionary/Garhwali/',
        'ukc': 'https://datascientiafoundation.github.io/LiveLanguage/datasets/gbm-ukc-lexicon-/',
        'panlex': 'https://panlex.org/downloads/',
    }
    results = {}
    for name, url in queries.items():
        try:
            data, info = fetch('discovery', name + '.txt', url)
            results[name] = dict(status='downloaded', **info)
            print(name, len(data), flush=True)
        except Exception as e:
            results[name] = dict(status='failed', url=url, error=str(e))
            print(name, str(e), flush=True)
    (RAW / 'discovery' / 'survey.json').write_text(json.dumps(results, indent=2))


def probes():
    jobs = [
        ('lsi', 'rights.html', 'https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu'),
        ('lsi', 'pages.xml', 'https://archive.org/download/LSIV0-V11/LSI-V9-4_djvu.xml'),
        ('lsi', 'page-numbers.json', 'https://archive.org/download/LSIV0-V11/LSI-V9-4_page_numbers.json'),
        ('lsi', 'scan.pdf', 'https://archive.org/download/LSIV0-V11/LSI-V9-4_text.pdf'),
        ('panlex', 'license.html', 'https://panlex.org/license/'),
        ('panlex', 'dev.html', 'https://dev.panlex.org/'),
        ('panlex', 'varieties.json', 'https://api.panlex.org/lv?iso639=gbm'),
        ('ukc', 'metadata.md', 'https://raw.githubusercontent.com/datascientiafoundation/LiveLanguage/gh-pages/_datasets/gbm-ukc-lexicon-.md'),
    ]
    for dataset in ['google/IndicGenBench_flores_in', 'google/IndicGenBench_xorqa_in',
                    'google/IndicGenBench_crosssum_in', 'lbourdois/panlex', 'jake-anto/wiktionary',
                    'hikinegi/Garhwali-Dataset', 'KuchBhi327/GarhwaliLanguage', 'openbmb/DCAD-2000',
                    'mteb/HinDialectClassification']:
        source = dataset.replace('/', '__')
        jobs += [(source, 'info.json', 'https://huggingface.co/api/datasets/' + dataset),
                 (source, 'tree.json', 'https://huggingface.co/api/datasets/' + dataset + '/tree/main?recursive=true'),
                 (source, 'card.md', 'https://huggingface.co/datasets/' + dataset + '/raw/main/README.md')]
    for source, name, url in jobs:
        try:
            data, _ = fetch(source, name, url)
            print(source, name, len(data), flush=True)
        except Exception as e:
            print(source, name, str(e), flush=True)


def wiktionary():
    source = 'wiktionary_en'
    api = 'https://en.wiktionary.org/w/api.php?'
    titles = {'Appendix:Garhwali Swadesh list'}
    categories = ['Category:Garhwali lemmas', 'Category:Garhwali non-lemma forms']
    seen = set()
    while categories:
        category = categories.pop(0)
        if category in seen:
            continue
        seen.add(category)
        params = dict(action='query', format='json', list='categorymembers', cmtitle=category, cmlimit=500)
        page = 0
        while True:
            data, _ = get_json(source, sha(category.encode())[:12]+f'-{page}.json', api + urlencode(params))
            for item in data['query']['categorymembers']:
                # Root lemma/non-lemma categories already enumerate their terms.
                # Avoid redundant recursive requests after API rate limiting.
                if item['ns'] == 0:
                    titles.add(item['title'])
            if 'continue' not in data:
                break
            params.update(data['continue'])
            page += 1
    rows = []
    titles = sorted(titles)
    for n in range(0, len(titles), 20):
        batch = '|'.join(titles[n:n+20])
        params = dict(action='query', format='json', titles=batch, prop='revisions', rvprop='ids|timestamp|content', rvslots='main')
        payload, info = get_json(source, f'batch-{sha(batch.encode())[:16]}.json', api + urlencode(params))
        for p in payload['query']['pages'].values():
            if 'missing' in p:
                continue
            title = p['title']
            revision = p['revisions'][0]
            raw = revision['slots']['main']['*']
            text = raw if title.startswith('Appendix:') else garhwali_section(raw)
            if not text:
                continue
            rows.append(make_record(source, p['pageid'], text, info, 'CC-BY-SA-4.0', SA,
                f'English Wiktionary contributors; https://en.wiktionary.org/w/index.php?title={quote(title)}&action=history',
                title=title, revision_id=revision['revid'], item_url=f'https://en.wiktionary.org/w/index.php?oldid={revision["revid"]}',
                corpus_layer='extended_sa_raw', genre='lexicon', modality='text', text_format='wikitext'))
        print('wiktionary', min(n+20, len(titles)), '/', len(titles), flush=True)
    save_records(CORPUS / 'wiktionary_en.jsonl', rows)
    return len(rows)


def acquire():
    for kind in ['flores', 'xorqa', 'crosssum']:
        dataset = f'google/IndicGenBench_{kind}_in'
        source = dataset.replace('/', '__')
        info = json.loads((RAW / source / 'info.json.metadata.json').read_text())
        revision = json.loads((ROOT / info['raw_path']).read_text())['sha']
        tree_meta = json.loads((RAW / source / 'tree.json.metadata.json').read_text())
        tree = json.loads((ROOT / tree_meta['raw_path']).read_text())
        for item in tree:
            if 'gbm' in item['path']:
                data, _ = fetch(source, item['path'], f'https://huggingface.co/datasets/{dataset}/resolve/{revision}/' + item['path'])
                print(source, item['path'], len(data), flush=True)
    jobs = [
        ('panlex', 'vocabulary.html', 'https://vocab.panlex.org/gbm-000'),
        ('ukc', 'lexicon.zip', 'https://datascientiafoundation.github.io/LiveLanguage/resources/b2b93805-a9a1-490a-b468-11f2dd29b62a/output-gbm.zip'),
        ('proverbs1894', 'pages.xml', 'https://archive.org/download/cu31924089930774/cu31924089930774_djvu.xml'),
        ('proverbs1894', 'scandata.xml', 'https://archive.org/download/cu31924089930774/cu31924089930774_scandata.xml'),
        ('proverbs1894', 'rights.html', 'https://commons.wikimedia.org/wiki/File:Proverbs_%26amp;_folklore_of_Kumaun_and_Garhwal_(IA_cu31924089930774).pdf'),
        ('storyweaver', 'languages.json', 'https://api.github.com/repos/global-asp/pb-source/contents'),
        ('incubator_wt', 'pages.json', 'https://incubator.wikimedia.org/w/api.php?' + urlencode(dict(action='query', format='json', generator='allpages', gapnamespace=0, gapprefix='Wt/gbm/', gaplimit=500, prop='revisions', rvprop='ids|timestamp|content', rvslots='main'))),
    ]
    for source, name, url in jobs:
        try:
            data, _ = fetch(source, name, url)
            print(source, name, len(data), flush=True)
        except Exception as e:
            print(source, name, str(e), flush=True)


def snapshot(source, name):
    info = json.loads((RAW / source / (name + '.metadata.json')).read_text())
    data = (ROOT / info['raw_path']).read_bytes()
    if sha(data) != info['sha256']:
        raise ValueError('Snapshot checksum mismatch')
    return data, info


def benchmark_record(kind, row, split, index, info, canary):
    licenses = {'flores': ('CC-BY-SA-4.0', SA),
                'xorqa': ('MIT', 'https://opensource.org/license/mit'),
                'crosssum': ('CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/')}
    if row.get('lang', 'gbm') != 'gbm':
        raise ValueError('Wrong benchmark language')
    text = row['source'] if kind == 'flores' else row['question'] if kind == 'xorqa' else row['summary']
    rec = make_record('indicgenbench_' + kind, f'{split}:{index}', text, info, *licenses[kind],
                       'Singh et al. (2024), Google IndicGenBench; upstream dataset card and source example retained',
                       split=split, usage='evaluation_only', benchmark_canary=canary,
                       source_example=row, corpus_layer='evaluation_only', genre=kind, modality='text',
                       rights_status='upstream_declared_license; component_rights_review_before_redistribution')
    return rec


def extract():
    import xml.etree.ElementTree as ET
    counts = {}
    for kind in ['flores', 'xorqa', 'crosssum']:
        source = f'google__IndicGenBench_{kind}_in'
        rows = []
        for p in sorted((RAW / source).glob('*gbm*.json.metadata.json')):
            name = p.name.removesuffix('.metadata.json')
            if kind == 'flores' and not name.startswith('flores_gbm_en_'):
                continue  # Reverse direction is the same parallel pair, saved raw only.
            raw, info = snapshot(source, name)
            data = json.loads(raw)
            split = name.rsplit('_', 1)[-1].removesuffix('.json')
            for i, row in enumerate(data['examples']):
                rows.append(benchmark_record(kind, row, split, i, info, data.get('canary')))
        save_records(ROOT / 'benchmarks' / f'indicgenbench_{kind}.jsonl', rows)
        counts['indicgenbench_' + kind] = len(rows)
    raw, info = snapshot('incubator_wt', 'pages.json')
    data = json.loads(raw)
    if 'continue' in data:
        raise ValueError('Unprocessed Incubator pagination')
    rows = []
    for p in data['query']['pages'].values():
        rev = p['revisions'][0]
        text = rev['slots']['main']['*']
        if not text.strip() or re.match(r'^\s*#redirect', text, re.I):
            continue
        rows.append(make_record('incubator_wt', p['pageid'], text, info, 'CC-BY-SA-4.0', SA,
            f'Wikimedia Incubator contributors; https://incubator.wikimedia.org/w/index.php?title={quote(p["title"])}&action=history',
            title=p['title'], revision_id=rev['revid'], corpus_layer='extended_sa_raw',
            item_url=f'https://incubator.wikimedia.org/w/index.php?oldid={rev["revid"]}',
            text_format='wikitext', genre='lexicon', modality='text', quality_flags=['may_contain_scaffolding']))
    save_records(CORPUS / 'incubator_wt.jsonl', rows)
    counts['incubator_wt'] = len(rows)
    for source in ['lsi', 'proverbs1894']:
        raw, info = snapshot(source, 'pages.xml')
        pages = ET.fromstring(raw).findall('.//OBJECT')
        rows = []
        # XML object sequence was checked against OCR page headings. Archive's
        # auto-generated page-number JSON is offset and is NOT used as truth.
        indices = range(293, 387) if source == 'lsi' else range(len(pages))
        for i in indices:
            p = pages[i]
            lines = [' '.join(w.text or '' for w in line.findall('WORD')) for line in p.findall('.//LINE')]
            text = '\n'.join(lines).strip()
            if not text:
                continue
            r = make_record(source, f'xml-page-{i}', text, info, 'Public-domain-US',
                'https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu' if source == 'lsi' else 'https://archive.org/details/cu31924089930774',
                'George Abraham Grierson, Linguistic Survey of India IX.4 (1916)' if source == 'lsi' else 'Ganga Datt Upreti, Proverbs & Folklore of Kumaun and Garhwal (1894)',
                corpus_layer='historical_review', genre='historical_linguistics', modality='text',
                xml_page_index=i, xml_page_identifier=p.get('usemap'),
                quality_flags=['uncorrected_ocr', 'mixed_languages', 'requires_page_alignment_review'])
            r.update(iso_639_3='mul', script='mixed', historical=True,
                language_candidates=['gbm', 'eng'] if source == 'lsi' else ['gbm', 'kfy', 'eng', 'hin'],
                rights_status='public_domain_evidence_saved' if source == 'lsi' else 'US_PD_1894; India_author_death_evidence_pending',
                printed_page_candidate=i-14 if source == 'lsi' else None,
                modifications='OCR word tokens joined by spaces; line boundaries preserved; no corrections')
            rows.append(r)
        save_records(ROOT / 'extracted' / 'historical' / f'{source}.jsonl', rows)
        counts[source] = len(rows)
    print(json.dumps(counts, indent=2))


def downloads():
    jobs = json.loads((RAW / 'download-plan.json').read_text())
    for job in jobs:
        try:
            data, _ = fetch(job['source'], job['name'], job['url'])
            print(job['source'], job['name'], len(data), flush=True)
        except Exception as e:
            print(job['source'], job['name'], str(e), flush=True)


def restricted():
    """Extract evaluation-only Garhwali rows from a benchmark parquet snapshot.

    The upstream dataset is CC BY-NC-SA and contains other languages, so this
    output is deliberately kept outside corpus/ and marked non-training.
    """
    import pyarrow.parquet as pq
    rows = []
    for split, filename in [('train', 'train.parquet'), ('test', 'test.parquet')]:
        pointer = json.loads((RAW / 'hindialect' / (filename + '.metadata.json')).read_text())
        info = pointer
        raw_path = ROOT / pointer['raw_path']
        for i, row in enumerate(pq.read_table(raw_path).to_pylist()):
            if row['label'] != 'garhwali-gbm':
                continue
            rows.append(make_record('hindialect_gbm', f'{split}:{i}', row['text'], info,
                'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'HinDialectClassification / LINDAT dataset contributors; evaluation-only extract',
                split=split, label=row['label'], usage='evaluation_only',
                corpus_layer='evaluation_only_restricted', genre='folk_text', modality='text',
                rights_status='noncommercial_sharealike; upstream component review required',
                source_url='https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-4839'))
    save_records(ROOT / 'restricted' / 'hindialect_gbm.jsonl', rows)
    print(json.dumps({'hindialect_gbm': len(rows)}, indent=2))


def uou():
    """Snapshot the complete, openly licensed Garhwali certificate course."""
    jobs = [
        ('terms.html', 'https://uou.ac.in/terms-use'),
        ('programme.html', 'https://uou.ac.in/progdetail?pid=CGL-21'),
        ('hin.traineddata', 'https://github.com/tesseract-ocr/tessdata_fast/raw/main/hin.traineddata'),
    ] + [(f'CGL-{n}.pdf', f'https://uou.ac.in/sites/default/files/slm/CGL-{n}.pdf')
         for n in range(101, 105)]
    for name, url in jobs:
        data, _ = fetch('uou_cgl', name, url)
        print('uou_cgl', name, len(data), flush=True)


def wayback():
    """Inventory unique archived captures for known Garhwali-content domains."""
    domains = [
        'garhwali.com/*',
        'bolpahadi.in/*',
        'garhwalilanguage.com/*',
        'garhwalikosh.blogspot.com/*',
        'e-magazineofuttarakhand.blogspot.com/*',
        'garhwalii.com/*',
        'vijaymadhur.blogspot.com/*',
        'pahadiaavaj.blogspot.com/*',
        'learnpahadi.neocities.org/*',
    ]
    summary = {}
    for domain in domains:
        params = dict(url=domain, output='json', fl='timestamp,original,statuscode,mimetype,digest',
                      filter=['statuscode:200', 'mimetype:text/html'], collapse='digest', limit=10000)
        try:
            data, _ = get_json('wayback', domain.replace('/*', '').replace('.', '_') + '.json',
                               'https://web.archive.org/cdx/search/cdx?' + urlencode(params, doseq=True))
            count = max(0, len(data) - 1)
            summary[domain] = {'status': 'indexed', 'unique_html_captures': count}
            print(domain, count, flush=True)
        except Exception as exc:
            summary[domain] = {'status': 'failed', 'error': str(exc)}
            print(domain, 'failed', str(exc), flush=True)
    (RAW / 'wayback' / 'summary.json').write_text(json.dumps(summary, indent=2))


def archive_open():
    """Acquire additional Archive.org items with explicit reuse evidence."""
    manuscript = 'aoml_garhwali-khanyatitji-administrative-record-garhwali-history-paper-manuscrip'
    manuscript_base = 'Garhwali Khanyatitji Administrative Record Garhwali History Paper Manuscript 1865 - Unknown - Jagannath Bhattarai Collection'
    thesis = 'sgng.1764-a-themetic-study-of-garhwali-folk-songs-lokgeet'
    jobs = [
        ('archive_1865', 'scan.pdf', f'https://archive.org/download/{manuscript}/' + quote(manuscript_base + '.pdf')),
        ('archive_1865', 'pages.xml', f'https://archive.org/download/{manuscript}/' + quote(manuscript_base + '_djvu.xml')),
        ('archive_1865', 'ocr.txt', f'https://archive.org/download/{manuscript}/' + quote(manuscript_base + '_djvu.txt')),
        ('archive_folksong_thesis', 'ocr.txt', f'https://archive.org/download/{thesis}/{thesis}_djvu.txt'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url)
        print(source, name, len(data), flush=True)


def archive_extract():
    import xml.etree.ElementTree as ET
    raw, info = snapshot('archive_1865', 'pages.xml')
    pages = ET.fromstring(raw).findall('.//OBJECT')
    rows = []
    for i, page in enumerate(pages, 1):
        if i != 1:
            continue  # Later pages are a modern collector portrait/CV, not the 1865 record.
        lines = [' '.join(w.text or '' for w in line.findall('WORD')) for line in page.findall('.//LINE')]
        text = '\n'.join(lines).strip()
        if not text:
            continue
        rec = make_record('archive_1865', f'page:{i}', text, info, 'CC0-1.0',
            'https://creativecommons.org/publicdomain/zero/1.0/',
            'Jagannath Bhattarai Collection; anonymous 1865 Garhwali administrative manuscript',
            pdf_page=i, corpus_layer='historical_review', genre='administrative_record',
            modality='text', quality_flags=['uncorrected_ocr', 'ocr_unusable',
                                             'handwritten_manuscript', 'requires_manual_transcription'],
            source_url='https://archive.org/details/aoml_garhwali-khanyatitji-administrative-record-garhwali-history-paper-manuscrip',
            rights_status='1865_public_domain; archive_item_declares_CC0')
        rec.update(script='mixed', iso_639_3='gbm', historical=True,
                   modifications='Internet Archive OCR line boundaries retained; no corrections')
        rows.append(rec)
    save_records(ROOT / 'extracted' / 'historical' / 'archive_1865.jsonl', rows)

    raw, info = snapshot('archive_folksong_thesis', 'ocr.txt')
    text = raw.decode(errors='replace').strip()
    rec = make_record('archive_folksong_thesis', 'document', text, info,
        'CC-BY-NC-SA-4.0', 'https://creativecommons.org/licenses/by-nc-sa/4.0/',
        'Sudama Singh Bhandari, A Thematic Study of Garhwali Folk Songs',
        corpus_layer='restricted_nc_sa', genre='academic_thesis', modality='text',
        usage='restricted_research', quality_flags=['uncorrected_ocr', 'mixed_languages',
                                                     'component_rights_review_required'],
        source_url='https://archive.org/details/sgng.1764-a-themetic-study-of-garhwali-folk-songs-lokgeet',
        rights_status='archive_item_declares_CC_BY_NC_SA_4; quoted_songs_require_component_review')
    rec.update(iso_639_3='mul', script='mixed',
               modifications='Internet Archive OCR retained; Unicode NFC and outer whitespace trimming only')
    save_records(ROOT / 'restricted' / 'archive_folksong_thesis.jsonl', [rec])
    print(json.dumps({'archive_1865_pages': len(rows), 'archive_folksong_thesis': 1}, indent=2))


def more_acquire():
    """Snapshot newly verified public machine-readable corpus candidates."""
    jobs = [
        ('paharili', 'README.md', 'https://raw.githubusercontent.com/rachanagusain/PahariLI/main/README.md'),
        ('paharili', 'LICENSE', 'https://raw.githubusercontent.com/rachanagusain/PahariLI/main/LICENSE'),
        ('paharili', 'train.txt', 'https://raw.githubusercontent.com/rachanagusain/PahariLI/main/data/train.txt'),
        ('paharili', 'test.txt', 'https://raw.githubusercontent.com/rachanagusain/PahariLI/main/data/test.txt'),
        ('hikinegi_garhwali', 'info.json', 'https://huggingface.co/api/datasets/hikinegi/Garhwali-Dataset'),
        ('hikinegi_garhwali', 'train.jsonl', 'https://huggingface.co/datasets/hikinegi/Garhwali-Dataset/resolve/1f4c1f45d5dd788b82a153510cd2cbac2bade7a6/train.jsonl'),
        ('dcad_gbm', 'info.json', 'https://huggingface.co/api/datasets/openbmb/DCAD-2000'),
        ('dcad_gbm', 'README.md', 'https://huggingface.co/datasets/openbmb/DCAD-2000/raw/main/README.md'),
        ('dcad_gbm', 'keep.jsonl', 'https://huggingface.co/datasets/openbmb/DCAD-2000/resolve/main/gbm_Deva/mala_000001_keep.jsonl'),
        ('dcad_gbm', 'remove.jsonl', 'https://huggingface.co/datasets/openbmb/DCAD-2000/resolve/main/gbm_Deva/mala_000001_remove.jsonl'),
        ('dcad_gbm', 'stats.jsonl', 'https://huggingface.co/datasets/openbmb/DCAD-2000/resolve/main/gbm_Deva/mala_000001_stas.jsonl'),
        ('glottolog_gbm', 'language.json', 'https://glottolog.org/resource/languoid/id/garh1243.json'),
        ('glottolog_gbm', 'language.html', 'https://glottolog.org/resource/languoid/id/garh1243'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url)
        print(source, name, len(data), flush=True)


def historical_more_acquire():
    """Snapshot additional public-domain Garhwali linguistic source material."""
    source = 'hill_dialects_1900'
    landing_url = 'https://books.google.com/books?id=veUTAAAAYAAJ&pg=PP1'
    landing, _ = fetch(source, 'landing.html', landing_url, max_time=120)
    text_value = landing.decode(errors='replace')
    match = re.search(r'id=pdf_download href="([^"]+)"', text_value)
    if not match:
        raise ValueError('Google Books full-view PDF link absent')
    pdf_url = html.unescape(match.group(1))
    if 'id=veUTAAAAYAAJ' not in pdf_url or 'output=pdf' not in pdf_url:
        raise ValueError('Unexpected Hill Dialects PDF URL')
    data, _ = fetch(source, 'scan.pdf', pdf_url, max_time=300, max_size=200000000)
    if not data.startswith(b'%PDF'):
        raise ValueError('Hill Dialects download is not a PDF')
    print(json.dumps({'hill_dialects_1900_pdf_bytes': len(data)}, indent=2))


def historical_more_extract():
    """Extract only the four Garhwali dialect sections of the 1900 volume."""
    import pdfplumber
    pdf_raw, pdf_info = snapshot('hill_dialects_1900', 'scan.pdf')
    pdf_path = ROOT / pdf_info['raw_path']
    extracted = []
    with pdfplumber.open(pdf_path) as pdf:
        if len(pdf.pages) != 135:
            raise ValueError(f'Expected 135 scan pages, found {len(pdf.pages)}')
        for pdf_page in range(79, 104):
            text_value = (pdf.pages[pdf_page - 1].extract_text() or '').strip()
            if pdf_page == 79:
                marker = 'Srinagar (Garhwal) dialect.'
                if marker not in text_value:
                    raise ValueError('Srinagar section boundary missing on scan page 79')
                text_value = marker + text_value.split(marker, 1)[1]
            if 'Garhwal' not in text_value:
                raise ValueError(f'Garhwal section heading absent from scan page {pdf_page}')
            if pdf_page <= 84:
                dialect = 'Srinagar'
            elif pdf_page == 85:
                dialect = 'Srinagar; Tihri'
            elif pdf_page <= 90:
                dialect = 'Tihri'
            elif pdf_page == 91:
                dialect = 'Tihri; Lohba'
            elif pdf_page <= 96:
                dialect = 'Lohba'
            elif pdf_page == 97:
                dialect = 'Lohba; Malla Dasoli'
            else:
                dialect = 'Malla Dasoli'
            extracted.append(dict(pdf_page=pdf_page, dialect=dialect, text=text_value))
    payload = json.dumps(extracted, ensure_ascii=False, separators=(',', ':')).encode()
    _, info = save_derived_snapshot(
        'hill_dialects_1900', 'pages.json', payload,
        [pdf_info['sha256'], f'pdfplumber:{pdfplumber.__version__}'],
        extraction='pdfplumber text layer; scan pages 79-103; pre-Garhwali text removed from page 79',
        pdf_page_start=79, pdf_page_end=103, page_count=len(extracted))
    rows = []
    for item in extracted:
        rec = make_record(
            'hill_dialects_1900', f'pdf-page-{item["pdf_page"]}', item['text'], info,
            'Public-domain-US', 'https://books.google.com/books?id=veUTAAAAYAAJ',
            'Ganga Datt Upreti, Hill Dialects of the Kumaun Division (1900)',
            corpus_layer='historical_review', genre='historical_linguistics', modality='text',
            pdf_page=item['pdf_page'], dialect=item['dialect'],
            language_candidates=['gbm', 'eng'],
            source_url='https://books.google.com/books?id=veUTAAAAYAAJ',
            rights_status='Google_Books_full_view_and_public_domain_flag; US_PD_1900; India_author_death_evidence_pending',
            quality_flags=['uncorrected_embedded_ocr', 'mixed_Garhwali_English',
                           'Devanagari_and_Latin_transliteration'])
        rec.update(iso_639_3='mul', script='mixed', historical=True,
                   modifications='Embedded OCR extracted page by page; page 79 cropped at the Garhwali section heading; no text correction')
        rows.append(rec)
    save_records(ROOT / 'extracted' / 'historical' / 'hill_dialects_1900.jsonl', rows)
    print(json.dumps({'hill_dialects_1900_garhwali_section_pages': len(rows)}, indent=2))


def opus_acquire():
    """Snapshot the current OPUS export of Garhwali translatewiki messages."""
    version = 'v2026-07-01'
    root = f'https://object.pouta.csc.fi/OPUS-translatewiki/{version}'
    jobs = [
        ('translatewiki_about.json', 'https://translatewiki.net/w/api.php?' + urlencode({
            'action': 'parse', 'page': 'Project:About', 'prop': 'wikitext',
            'format': 'json', 'formatversion': 2})),
        ('gbm.txt.gz', root + '/mono/gbm.txt.gz'),
        ('en-gbm.txt.zip', root + '/moses/en-gbm.txt.zip'),
    ]
    for name, url in jobs:
        data, _ = fetch('opus_translatewiki', name, url, max_time=180, max_size=100000000)
        print('opus_translatewiki', name, len(data), flush=True)


def opus_extract():
    """Extract Garhwali localisations, retaining English alignments when available."""
    mono_raw, mono_info = snapshot('opus_translatewiki', 'gbm.txt.gz')
    mono_lines = gzip.decompress(mono_raw).decode().splitlines()
    zip_raw, zip_info = snapshot('opus_translatewiki', 'en-gbm.txt.zip')
    with zipfile.ZipFile(io.BytesIO(zip_raw)) as archive:
        names = archive.namelist()
        gbm_name = next((name for name in names if name.endswith('.gbm')), None)
        en_name = next((name for name in names if name.endswith('.en')), None)
        ids_name = next((name for name in names if name.endswith('.ids')), None)
        if not gbm_name or not en_name:
            raise ValueError(f'Unexpected OPUS Moses archive members: {names}')
        gbm_parallel = archive.read(gbm_name).decode().splitlines()
        en_parallel = archive.read(en_name).decode().splitlines()
        pair_ids = archive.read(ids_name).decode().splitlines() if ids_name else []
    if len(gbm_parallel) != len(en_parallel):
        raise ValueError('OPUS Garhwali/English alignment length mismatch')
    english_by_gbm = {}
    ids_by_gbm = {}
    for index, (gbm, english) in enumerate(zip(gbm_parallel, en_parallel)):
        english_by_gbm.setdefault(gbm, []).append(english)
        if pair_ids:
            ids_by_gbm.setdefault(gbm, []).append(pair_ids[index])
    rows = []
    first_line = {}
    duplicate_lines = defaultdict(list)
    for index, text_value in enumerate(mono_lines):
        if not text_value.strip():
            raise ValueError(f'Blank OPUS Garhwali line {index}')
        if text_value in first_line:
            duplicate_lines[text_value].append(index)
            continue
        first_line[text_value] = index
        rec = make_record(
            'opus_translatewiki_gbm', len(rows), text_value, mono_info, 'CC-BY-3.0',
            'https://creativecommons.org/licenses/by/3.0/',
            'translatewiki.net volunteer translators; distributed through OPUS',
            corpus_layer='core_open', genre='software_localization', modality='text',
            upstream_version='v2026-07-01', english_alignments=english_by_gbm.get(text_value, []),
            opus_pair_ids=ids_by_gbm.get(text_value, []), parallel_snapshot=zip_info,
            upstream_mono_line=index, duplicate_mono_lines=duplicate_lines.get(text_value, []),
            source_url='https://opus.nlpl.eu/datasets/translatewiki',
            rights_status='translatewiki_translations_declared_CC_BY_3.0',
            quality_flags=['software_interface_fragment', 'native_accuracy_unverified'])
        rows.append(rec)
    for row in rows:
        if row['text_original'] in duplicate_lines:
            row['duplicate_mono_lines'] = duplicate_lines[row['text_original']]
    save_records(CORPUS / 'opus_translatewiki_gbm.jsonl', rows)
    print(json.dumps({'opus_translatewiki_gbm': len(rows),
                      'parallel_rows': len(gbm_parallel),
                      'mono_source_lines': len(mono_lines),
                      'mono_unique_texts': len(set(mono_lines)),
                      'duplicate_mono_lines_dropped': len(mono_lines) - len(set(mono_lines))}, indent=2))


def indic_asr_acquire():
    """Snapshot all public transcript rows for the Garhwali ASR configuration."""
    dataset = 'grushaaaaa/indic-dialect-asr'
    info_payload, _ = get_json('indic_dialect_asr', 'info.json',
                               'https://huggingface.co/api/datasets/' + dataset)
    revision = info_payload['sha']
    fetch('indic_dialect_asr', 'README.md',
          f'https://huggingface.co/datasets/{dataset}/raw/{revision}/README.md')
    splits, _ = get_json('indic_dialect_asr', 'splits.json',
                         'https://datasets-server.huggingface.co/splits?' + urlencode(dict(dataset=dataset)))
    if not any(row['config'] == 'garhwali' and row['split'] == 'train' for row in splits['splits']):
        raise ValueError('Garhwali configuration absent from public split inventory')
    offset = 0
    total = None
    while total is None or offset < total:
        params = dict(dataset=dataset, config='garhwali', split='train', offset=offset, length=100)
        payload, _ = get_json('indic_dialect_asr', f'rows-{offset}.json',
                              'https://datasets-server.huggingface.co/rows?' + urlencode(params))
        batch = payload.get('rows', [])
        total = payload['num_rows_total']
        if not batch:
            raise ValueError(f'Garhwali row pagination stopped at {offset}/{total}')
        if any('sentence' in row.get('truncated_cells', []) for row in batch):
            raise ValueError('Dataset server truncated a Garhwali transcript')
        offset += len(batch)
        print('indic_dialect_asr', offset, '/', total, flush=True)
    print(json.dumps({'revision': revision, 'garhwali_rows': total}, indent=2))


def indic_asr_range_acquire():
    """Read only transcript columns from pinned Parquet shards, leaving audio remote."""
    import pyarrow.parquet as pq
    source = 'indic_dialect_asr'
    dataset = 'grushaaaaa/indic-dialect-asr'
    info_raw, info = snapshot(source, 'info.json')
    info_payload = json.loads(info_raw)
    revision = info_payload['sha']
    tree_url = (f'https://huggingface.co/api/datasets/{dataset}/tree/{revision}/garhwali?'
                + urlencode(dict(recursive='true', expand='true')))
    tree, tree_info = get_json(source, 'tree.json', tree_url)
    shards = sorted((item for item in tree if item.get('path', '').endswith('.parquet')),
                    key=lambda item: item['path'])
    if not shards:
        raise ValueError('No Garhwali Parquet shards in the pinned dataset tree')
    inputs = [info['sha256'], tree_info['sha256']] + [item['lfs']['oid'] for item in shards]
    pointer = RAW / source / 'transcripts.json.metadata.json'
    if pointer.exists():
        data, existing_info = save_derived_snapshot(source, 'transcripts.json', b'', inputs)
        payload = json.loads(data)
        print(json.dumps({'revision': revision, 'garhwali_rows': len(payload['rows']),
                          'range_bytes_fetched': existing_info.get('range_bytes_fetched', 0),
                          'cached': True}, indent=2))
        return

    rows = []
    remote_stats = []
    for shard_index, item in enumerate(shards):
        remote_url = (f'https://huggingface.co/datasets/{dataset}/resolve/{revision}/'
                      + quote(item['path']))
        reader = HTTPRangeReader(remote_url, item['size'])
        table = pq.ParquetFile(reader, pre_buffer=False).read(
            columns=['sentence', 'language', 'source'], use_threads=False)
        shard_rows = table.to_pylist()
        for file_row_index, row in enumerate(shard_rows):
            if row.get('language') != 'garhwali' or not (row.get('sentence') or '').strip():
                raise ValueError(f'Unexpected row in {item["path"]}:{file_row_index}')
            rows.append(dict(upstream_row_index=len(rows), shard=item['path'],
                             file_row_index=file_row_index, sentence=row['sentence'],
                             language=row['language'], source=row.get('source')))
        remote_stats.append(dict(path=item['path'], size=item['size'],
                                 lfs_sha256=item['lfs']['oid'], url=remote_url,
                                 row_count=len(shard_rows), range_requests=reader.range_requests,
                                 range_bytes_fetched=reader.fetched_bytes))
        reader.close()
        print('indic_dialect_asr range', shard_index + 1, '/', len(shards),
              'rows', len(rows), 'bytes', remote_stats[-1]['range_bytes_fetched'], flush=True)
    if len(rows) != 7823:
        raise ValueError(f'Expected 7,823 Garhwali rows, found {len(rows)}')
    payload = json.dumps(dict(dataset=dataset, revision=revision, rows=rows),
                         ensure_ascii=False, separators=(',', ':')).encode()
    _, derived_info = save_derived_snapshot(
        source, 'transcripts.json', payload, inputs, dataset=dataset, revision=revision,
        extraction='PyArrow projection of sentence, language, and source; audio column not downloaded',
        remote_shards=remote_stats,
        range_bytes_fetched=sum(item['range_bytes_fetched'] for item in remote_stats),
        range_requests=sum(item['range_requests'] for item in remote_stats))
    print(json.dumps({'revision': revision, 'garhwali_rows': len(rows),
                      'range_bytes_fetched': derived_info['range_bytes_fetched'],
                      'range_requests': derived_info['range_requests']}, indent=2))


def indic_asr_extract():
    rows = []
    transcript_pointer = RAW / 'indic_dialect_asr' / 'transcripts.json.metadata.json'
    if transcript_pointer.exists():
        raw, info = snapshot('indic_dialect_asr', 'transcripts.json')
        source_rows = json.loads(raw)['rows']
    else:
        source_rows = []
        for pointer in sorted((RAW / 'indic_dialect_asr').glob('rows-*.json.metadata.json'),
                              key=lambda p: int(p.name.split('-')[1].split('.')[0])):
            name = pointer.name.removesuffix('.metadata.json')
            raw, info = snapshot('indic_dialect_asr', name)
            for item in json.loads(raw)['rows']:
                source_rows.append(dict(upstream_row_index=item['row_idx'], **item['row']))
    for row in source_rows:
            row_index = row['upstream_row_index']
            if row.get('language') != 'garhwali' or not row.get('sentence', '').strip():
                raise ValueError(f'Unexpected Garhwali ASR row {row_index}')
            source_name = row.get('source') or 'not_reported'
            rec = make_record('indic_dialect_asr_gbm', row_index, row['sentence'], info,
                'CC-BY-4.0', BY,
                f'Indic Dialect ASR dataset by grushaaaaa; declared source: {source_name}',
                split='train', upstream_row_index=row_index, upstream_source=source_name,
                usage='provenance_review_only', corpus_layer='quarantine', genre='speech_transcript',
                modality='speech_transcript', audio_referenced=True,
                source_url='https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr',
                rights_status='dataset_declares_CC_BY_4; source_component_and_consent_review_pending',
                quality_flags=['community_aggregation', 'possible_upstream_duplicate',
                               'source_lineage_review_required'])
            rows.append(rec)
    if not rows:
        raise ValueError('No Garhwali ASR row snapshots found')
    save_records(ROOT / 'quarantine' / 'indic_dialect_asr_gbm.jsonl', rows)
    sources = Counter(row['upstream_source'] for row in rows)
    print(json.dumps({'indic_dialect_asr_gbm': len(rows), 'upstream_sources': sources}, indent=2))


def panlex_acquire():
    """Acquire the smaller generated Parquet representation of the PanLex mirror."""
    dataset = 'lbourdois/panlex'
    info_payload, _ = get_json('panlex_full', 'info.json',
                               'https://huggingface.co/api/datasets/' + dataset)
    fetch('panlex_full', 'README.md',
          f'https://huggingface.co/datasets/{dataset}/raw/{info_payload["sha"]}/README.md')
    fetch('panlex_full', 'official-license.html', 'https://panlex.org/license/')
    index, _ = get_json('panlex_full', 'parquet-index.json',
                        'https://datasets-server.huggingface.co/parquet?' + urlencode(dict(dataset=dataset)))
    files = [row for row in index['parquet_files'] if row['config'] == 'panlex' and row['split'] == 'train']
    if not files:
        raise ValueError('No generated PanLex Parquet files')
    for i, item in enumerate(files):
        data, _ = fetch('panlex_full', f'part-{i:04d}.parquet', item['url'],
                        max_time=300, max_size=200000000)
        if len(data) != item['size']:
            raise ValueError(f'PanLex part {i} size mismatch')
        print('panlex_full', i + 1, '/', len(files), len(data), flush=True)


def panlex_extract():
    import pyarrow.compute as pc
    import pyarrow.parquet as pq
    rows = []
    seen = set()
    for pointer in sorted((RAW / 'panlex_full').glob('part-*.parquet.metadata.json')):
        info = json.loads(pointer.read_text())
        table = pq.read_table(ROOT / info['raw_path'], columns=['vocab', '639-3', '639-3_english_name',
                                                                'var_code', 'english_name_var'])
        table = table.filter(pc.equal(table['639-3'], 'gbm'))
        for item in table.to_pylist():
            text_value = (item.get('vocab') or '').strip()
            key = (item.get('var_code'), text_value)
            if not text_value or key in seen:
                continue
            seen.add(key)
            rec = make_record('panlex_gbm', f'{item.get("var_code") or "gbm"}:{len(rows)}',
                text_value, info, 'CC-BY-NC-SA-4.0',
                'https://creativecommons.org/licenses/by-nc-sa/4.0/',
                'PanLex project of The Long Now Foundation; Hugging Face mirror by lbourdois',
                corpus_layer='restricted_nc_sa', genre='lexicon', modality='text',
                variety_code=item.get('var_code'), language_name=item.get('639-3_english_name'),
                variety_name=item.get('english_name_var'),
                source_url='https://huggingface.co/datasets/lbourdois/panlex',
                rights_status='official_current_page_CC_BY_NC_SA_4; mirror_card_says_CC0; conservative_license_applied',
                quality_flags=['machine_aggregated_lexicon', 'meaning_links_absent_in_mirror'])
            rows.append(rec)
    save_records(ROOT / 'restricted' / 'panlex_gbm.jsonl', rows)
    print(json.dumps({'panlex_gbm_unique_forms': len(rows)}, indent=2))


def paharili_line(line):
    fields = line.rstrip('\n').rsplit('\t', 1)
    if len(fields) != 2 or not fields[0].strip() or not re.fullmatch(r'[a-z]{3}', fields[1]):
        raise ValueError('Malformed PahariLI labeled sentence')
    return fields[0], fields[1]


def more_extract():
    """Extract public candidates whose component rights still require review."""
    rows = []
    for split in ['train', 'test']:
        raw, info = snapshot('paharili', split + '.txt')
        for index, line in enumerate(raw.decode().splitlines()):
            text_value, label = paharili_line(line)
            if label != 'gbm':
                continue
            rows.append(make_record('paharili_gbm', f'{split}:{index}', text_value, info,
                'Apache-2.0-repository-declared', 'https://www.apache.org/licenses/LICENSE-2.0',
                'Rachana Gusain, PahariLI repository', split=split, upstream_label=label,
                usage='provenance_review_only', corpus_layer='quarantine', genre='mixed_web_and_scripture',
                modality='text', source_url='https://github.com/rachanagusain/PahariLI',
                rights_status='repository_Apache_2; underlying_blogs_and_translated_text_not_sublicensed',
                quality_flags=['source_lineage_missing', 'component_rights_review_required',
                               'possible_modern_scripture_or_blog_text']))
    save_records(ROOT / 'quarantine' / 'paharili_gbm.jsonl', rows)

    raw, info = snapshot('hikinegi_garhwali', 'train.jsonl')
    hikinegi_rows = []
    for index, line in enumerate(raw.decode().splitlines()):
        item = json.loads(line)
        text_value = item.get('output', '').strip()
        if not text_value:
            raise ValueError(f'Empty hikinegi output at row {index}')
        rec = make_record('hikinegi_garhwali', index, text_value, info, 'NOASSERTION',
            'https://huggingface.co/datasets/hikinegi/Garhwali-Dataset',
            'hikinegi/Garhwali-Dataset uploader; authorship and license not stated',
            english_prompt=item.get('instruction'), script_variant='Latin_transliteration',
            usage='provenance_review_only', corpus_layer='quarantine', genre='phrase_translation',
            modality='text', source_url='https://huggingface.co/datasets/hikinegi/Garhwali-Dataset',
            rights_status='publicly_downloadable_but_no_license_or_authorship_statement',
            quality_flags=['unlicensed', 'community_upload', 'native_accuracy_unverified'])
        rec['script'] = 'Latn'
        hikinegi_rows.append(rec)
    save_records(ROOT / 'quarantine' / 'hikinegi_garhwali.jsonl', hikinegi_rows)

    dcad_rows = []
    for decision in ['keep', 'remove']:
        raw, info = snapshot('dcad_gbm', decision + '.jsonl')
        for index, line in enumerate(raw.decode().splitlines()):
            item = json.loads(line)
            if item.get('original_code') != 'gbm' or not item.get('text', '').strip():
                raise ValueError(f'Unexpected DCAD Garhwali row {decision}:{index}')
            metrics = {key: value for key, value in item.items()
                       if key not in {'text', 'url', 'collection', 'source', 'original_code'}}
            dcad_rows.append(make_record('dcad_gbm', f'{decision}:{index}', item['text'], info,
                'NOASSERTION', 'https://huggingface.co/datasets/openbmb/DCAD-2000',
                'OpenBMB DCAD-2000; underlying Common Crawl/MADLAD pages retain source copyrights',
                upstream_filter_decision=decision, upstream_collection=item.get('collection'),
                common_crawl_source=item.get('source'), upstream_url=item.get('url') or None,
                upstream_metrics=metrics, usage='provenance_review_only', corpus_layer='quarantine',
                genre='web_document', modality='text',
                source_url='https://huggingface.co/datasets/openbmb/DCAD-2000',
                rights_status='dataset_LICENSE_link_missing; underlying_web_copyrights_not_cleared',
                quality_flags=['common_crawl', 'component_rights_review_required',
                               'source_url_missing'] + (['upstream_rejected'] if decision == 'remove' else [])))
    save_records(ROOT / 'quarantine' / 'dcad_gbm.jsonl', dcad_rows)

    print(json.dumps({'paharili_gbm': len(rows), 'hikinegi_garhwali': len(hikinegi_rows),
                      'dcad_gbm': len(dcad_rows)}, indent=2))


def third_wave_acquire():
    """Snapshot a third, rights-aware pass of verified Garhwali sources."""
    madlad_revision = '9d886a76bd8fa69b294f2dd3843dacb8388ee5a5'
    asr_revision = '827942102590caf0184dcfa5defaab7f73109974'
    jobs = [
        ('madlad400_gbm', 'info.json', 'https://huggingface.co/api/datasets/allenai/MADLAD-400'),
        ('madlad400_gbm', 'README.md',
         f'https://huggingface.co/datasets/allenai/MADLAD-400/raw/{madlad_revision}/README.md'),
        ('madlad400_gbm', 'tree.json',
         f'https://huggingface.co/api/datasets/allenai/MADLAD-400/tree/{madlad_revision}/data/gbm?recursive=true&expand=true'),
        ('madlad400_gbm', 'gbm_clean_0000.jsonl.gz',
         f'https://huggingface.co/datasets/allenai/MADLAD-400/resolve/{madlad_revision}/data/gbm/gbm_clean_0000.jsonl.gz'),
        ('glotlid_gbm', 'info.json', 'https://huggingface.co/api/datasets/cis-lmu/glotlid-corpus'),
        ('glotlid_gbm', 'sources.md', 'https://raw.githubusercontent.com/cisnlp/GlotLID/main/sources.md'),
        ('glotlid_gbm', 'languages-v3.md', 'https://raw.githubusercontent.com/cisnlp/GlotLID/main/languages-v3.md'),
        ('chaashini_gbm', 'info.json', 'https://huggingface.co/api/datasets/kapturecx/Chaashini'),
        ('garhwali_asr_research', 'repo.json', 'https://api.github.com/repos/soodashima91/Garhwali-ASR'),
        ('garhwali_asr_research', 'tree.json',
         f'https://api.github.com/repos/soodashima91/Garhwali-ASR/git/trees/{asr_revision}?recursive=1'),
        ('garhwali_asr_research', 'README.md',
         f'https://raw.githubusercontent.com/soodashima91/Garhwali-ASR/{asr_revision}/README.md'),
        ('garhwali_asr_research', 'DATA.md',
         f'https://raw.githubusercontent.com/soodashima91/Garhwali-ASR/{asr_revision}/DATA.md'),
        ('acl_dialect_matters', 'landing.html', 'https://aclanthology.org/2026.vardial-1.12/'),
        ('acl_dialect_matters', 'paper.pdf', 'https://aclanthology.org/2026.vardial-1.12.pdf'),
        ('arxiv_seeds_before_objectives', 'landing.html', 'https://arxiv.org/abs/2608.10670'),
        ('arxiv_seeds_before_objectives', 'paper.pdf', 'https://arxiv.org/pdf/2608.10670'),
        ('ignca_primal_elements', 'landing.html', 'https://ignca.gov.in/prakriti/'),
        ('ignca_primal_elements', 'volume.pdf', 'https://ignca.gov.in/eBooks/100007.pdf'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url, max_time=240, max_size=200000000)
        print(source, name, len(data), flush=True)


def existing_text_hashes(exclude=None):
    """Return normalized-text hashes already stored across every corpus layer."""
    excluded = {str(Path(item)) for item in (exclude or [])}
    folders = [CORPUS, ROOT / 'benchmarks', ROOT / 'restricted', ROOT / 'quarantine',
               ROOT / 'extracted' / 'historical']
    hashes = set()
    for folder in folders:
        for path in folder.glob('*.jsonl'):
            if str(path.relative_to(ROOT)) in excluded:
                continue
            for line in path.read_text().splitlines():
                row = json.loads(line)
                text_value = row.get('text_normalized', '')
                hashes.add(row.get('text_sha256') or sha(text_value.encode()))
    return hashes


def madlad_clean_records(raw, info, known_hashes):
    """Extract novel clean Garhwali documents while retaining conservative rights flags."""
    rows = []
    duplicate_rows = 0
    seen = set(known_hashes)
    for index, line in enumerate(gzip.decompress(raw).decode().splitlines()):
        item = json.loads(line)
        if set(item) != {'text'} or not item['text'].strip():
            raise ValueError(f'Unexpected MADLAD Garhwali row {index}')
        normalized = unicodedata.normalize('NFC', item['text']).strip()
        digest = sha(normalized.encode())
        if digest in seen:
            duplicate_rows += 1
            continue
        seen.add(digest)
        devanagari = sum('\u0900' <= char <= '\u097f' for char in normalized)
        alphabetic = sum(char.isalpha() for char in normalized)
        nonspace = sum(not char.isspace() for char in normalized)
        copyright_marker = bool(re.search(r'copyright|©|all rights reserved', normalized, re.I))
        flags = ['common_crawl', 'dataset_clean_partition',
                 'component_rights_review_required', 'source_url_removed']
        if copyright_marker:
            flags.append('copyright_notice_detected')
        rows.append(make_record(
            'madlad400_gbm_clean', index, item['text'], info,
            'ODC-BY-1.0-database-only', 'https://opendatacommons.org/licenses/by/1-0/',
            'Kudugunta et al. (2023), MADLAD-400; original web authors retain component rights',
            upstream_row=index, upstream_split='clean', dataset_revision=info.get('dataset_revision'),
            usage='provenance_review_only', corpus_layer='quarantine', genre='web_document',
            modality='text', source_url='https://huggingface.co/datasets/allenai/MADLAD-400',
            rights_status='ODC_BY_1_covers_database; underlying_page_copyrights_not_cleared',
            quality_flags=flags,
            quality_metrics={'characters': len(normalized), 'alphabetic_characters': alphabetic,
                             'devanagari_characters': devanagari,
                             'devanagari_share_of_nonspace': round(devanagari / nonspace, 4)
                             if nonspace else 0,
                             'line_count': len(normalized.splitlines()),
                             'copyright_marker': copyright_marker}))
    return rows, duplicate_rows


def madlad_provenance(info):
    """Attach the immutable dataset revision to downloaded file provenance."""
    enriched = dict(info)
    enriched['dataset_revision'] = '9d886a76bd8fa69b294f2dd3843dacb8388ee5a5'
    enriched['upstream_partition_sha256'] = '6516174f88d38e5c6db032a3e3d83d002e20a34df0f02f52c9188884b6bb6999'
    return enriched


def third_wave_extract():
    """Add only exact-novel records from MADLAD's audited Garhwali clean split."""
    raw, info = snapshot('madlad400_gbm', 'gbm_clean_0000.jsonl.gz')
    info = madlad_provenance(info)
    if sha(raw) != info['upstream_partition_sha256']:
        raise ValueError('MADLAD Garhwali clean partition checksum mismatch')
    target = ROOT / 'quarantine' / 'madlad400_gbm_clean.jsonl'
    known = existing_text_hashes(exclude=[str(target.relative_to(ROOT))])
    rows, duplicates = madlad_clean_records(raw, info, known)
    if len(rows) + duplicates != 137:
        raise ValueError(f'Expected 137 MADLAD clean documents, found {len(rows) + duplicates}')
    save_records(target, rows)
    print(json.dumps({'madlad_clean_upstream_documents': 137,
                      'exact_duplicates_skipped': duplicates,
                      'novel_documents_added_to_quarantine': len(rows)}, indent=2))


def fourth_wave_acquire():
    """Acquire the newest rights-cleared CLDF and Garhwali story sources."""
    jobs = [
        ('sand_garhwali', 'forms.csv',
         'https://raw.githubusercontent.com/numeralbank/sand/v1.0/cldf/forms.csv'),
        ('sand_garhwali', 'cldf-metadata.json',
         'https://raw.githubusercontent.com/numeralbank/sand/v1.0/cldf/cldf-metadata.json'),
        ('chan_numerals_garhwali', 'forms.csv',
         'https://raw.githubusercontent.com/numeralbank/channumerals/v1.0.2/cldf/forms.csv'),
        ('chan_numerals_garhwali', 'cldf-metadata.json',
         'https://raw.githubusercontent.com/numeralbank/channumerals/v1.0.2/cldf/cldf-metadata.json'),
        ('mamta_southasia', 'values.csv',
         'https://raw.githubusercontent.com/cldf-datasets/mamtasouthasia/v1.0/cldf/values.csv'),
        ('mamta_southasia', 'examples.csv',
         'https://raw.githubusercontent.com/cldf-datasets/mamtasouthasia/v1.0/cldf/examples.csv'),
        ('mamta_southasia', 'cldf-metadata.json',
         'https://raw.githubusercontent.com/cldf-datasets/mamtasouthasia/v1.0/cldf/cldf-metadata.json'),
        ('lsi_cldf_garhwali', 'forms.csv',
         'https://raw.githubusercontent.com/lexibank/lsi/v1.0/cldf/forms.csv'),
        ('lsi_cldf_garhwali', 'cldf-metadata.json',
         'https://raw.githubusercontent.com/lexibank/lsi/v1.0/cldf/cldf-metadata.json'),
        ('obs_garhwali', 'catalog.html', 'https://www.freebiblesindia.in/obs/'),
        ('garhwali_new_testament', 'license.html',
         'https://www.freebiblesindia.in/bible/gbm/license.html'),
        ('garhwali_new_testament', 'download.html',
         'https://www.freebiblesindia.in/bible/gbm/download.html'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url, max_time=120)
        print(source, name, len(data), flush=True)
    for story_number in range(1, 51):
        name = f'story-{story_number:03d}.html'
        url = f'https://media.ipsapps.org/in/osa/stories/36-Garhwali-{story_number:03d}.html'
        data, _ = fetch('obs_garhwali', name, url, max_time=60)
        print('obs_garhwali', name, len(data), flush=True)


def fourth_wave_extract():
    """Extract open numeral forms/examples and restricted OBS story text."""
    sand_raw, sand_info = snapshot('sand_garhwali', 'forms.csv')
    sand_rows = sand_garhwali_records(sand_raw, sand_info)
    if len(sand_rows) != 123:
        raise ValueError(f'Expected 123 SAND Garhwali forms, found {len(sand_rows)}')

    chan_raw, chan_info = snapshot('chan_numerals_garhwali', 'forms.csv')
    chan_rows = chan_garhwali_records(chan_raw, chan_info)
    if len(chan_rows) != 40:
        raise ValueError(f'Expected 40 Chan Garhwali forms, found {len(chan_rows)}')

    values_raw, values_info = snapshot('mamta_southasia', 'values.csv')
    examples_raw, examples_info = snapshot('mamta_southasia', 'examples.csv')
    mamta_values, mamta_examples = mamta_garhwali_records(
        values_raw, values_info, examples_raw, examples_info)
    if len(mamta_values) != 65 or len(mamta_examples) != 67:
        raise ValueError(
            f'Expected 65 Mamta values and 67 examples, found '
            f'{len(mamta_values)} and {len(mamta_examples)}')

    lsi_raw, lsi_info = snapshot('lsi_cldf_garhwali', 'forms.csv')
    lsi_rows = lsi_cldf_garhwali_records(lsi_raw, lsi_info)
    if len(lsi_rows) != 185:
        raise ValueError(f'Expected 185 LSI CLDF Garhwali forms, found {len(lsi_rows)}')

    obs_rows = []
    for story_number in range(1, 51):
        raw, info = snapshot('obs_garhwali', f'story-{story_number:03d}.html')
        obs_rows.append(obs_garhwali_record(story_number, raw, info))

    targets = [
        ROOT / 'corpus' / 'sand_garhwali.jsonl',
        ROOT / 'corpus' / 'chan_numerals_garhwali.jsonl',
        ROOT / 'corpus' / 'mamta_southasia_examples.jsonl',
        ROOT / 'restricted' / 'obs_garhwali.jsonl',
        ROOT / 'extracted' / 'historical' / 'lsi_cldf_garhwali.jsonl',
    ]
    known = existing_text_hashes(
        exclude=[str(path.relative_to(ROOT)) for path in targets])
    overlap = {}
    seen = set(known)
    for label, rows in [
        ('sand_garhwali', sand_rows),
        ('chan_numerals_garhwali', chan_rows),
        ('mamta_southasia_examples', mamta_examples),
        ('obs_garhwali', obs_rows),
        ('lsi_cldf_garhwali', lsi_rows),
    ]:
        hashes = [row['text_sha256'] for row in rows]
        overlap[label] = sum(digest in seen for digest in hashes)
        seen.update(hashes)

    save_records(targets[0], sand_rows)
    save_records(targets[1], chan_rows)
    save_records(targets[2], mamta_examples)
    save_records(targets[3], obs_rows)
    save_records(targets[4], lsi_rows)
    print(json.dumps({
        'sand_garhwali_forms': len(sand_rows),
        'chan_garhwali_forms': len(chan_rows),
        'mamta_values_catalogued_not_ingested_due_conceptual_overlap': len(mamta_values),
        'mamta_translated_examples': len(mamta_examples),
        'obs_garhwali_stories_restricted': len(obs_rows),
        'lsi_cldf_historical_forms': len(lsi_rows),
        'exact_text_overlap_with_prior_or_earlier_wave4_sources': overlap,
    }, indent=2))


def fifth_wave_acquire():
    """Acquire public-domain OCR and its item-level rights evidence."""
    jobs = [
        ('kellogg_1893', 'ocr.xml',
         'https://archive.org/download/grammarofhindl00kell/grammarofhindl00kell_djvu.xml'),
        ('kellogg_1893', 'scandata.xml',
         'https://archive.org/download/grammarofhindl00kell/grammarofhindl00kell_scandata.xml'),
        ('kellogg_1893', 'commons-rights.html',
         'https://commons.wikimedia.org/wiki/File:Hindi_grammar_(Kellogg).djvu'),
        ('walton_gazetteer_1910', 'ocr.xml',
         'https://archive.org/download/in.ernet.dli.2015.48008/2015.48008.British-Garhwal---A-Gazetteer_djvu.xml'),
        ('walton_gazetteer_1910', 'metadata.json',
         'https://archive.org/metadata/in.ernet.dli.2015.48008'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url, max_time=180, max_size=100000000)
        print(source, name, len(data), flush=True)


def fifth_wave_extract():
    """Extract only page-level historical witnesses relevant to Garhwali."""
    kellogg_raw, kellogg_info = snapshot('kellogg_1893', 'ocr.xml')
    kellogg_pages = djvu_word_pages(kellogg_raw)
    if len(kellogg_pages) != 662:
        raise ValueError(f'Expected 662 Kellogg scan pages, found {len(kellogg_pages)}')
    kellogg_rows = []
    for scan_page, text_value in enumerate(kellogg_pages, 1):
        if not re.search(r'garhw', text_value, re.I):
            continue
        record = make_record(
            'kellogg_1893', f'scan-page-{scan_page}', text_value, kellogg_info,
            'Public-Domain-Mark-1.0', 'https://creativecommons.org/publicdomain/mark/1.0/',
            'Samuel H. Kellogg, A Grammar of the Hindi Language, second edition (1893)',
            scan_page=scan_page, corpus_layer='historical_review',
            genre='historical_linguistics', modality='text',
            source_url='https://archive.org/details/grammarofhindl00kell',
            rights_evidence='sources/online/kellogg_1893/commons-rights.html.metadata.json',
            quality_flags=['uncorrected_ocr', 'mixed_Garhwali_English_Hindi',
                           'keyword_selected_page', 'overlaps_lsi_witness'])
        record.update(iso_639_3='mul', script='mixed', historical=True,
                      modifications='Internet Archive OCR lines retained; no correction')
        kellogg_rows.append(record)
    if len(kellogg_rows) != 34:
        raise ValueError(f'Expected 34 Garhwali-mention Kellogg pages, found {len(kellogg_rows)}')

    walton_raw, walton_info = snapshot('walton_gazetteer_1910', 'ocr.xml')
    walton_pages = djvu_word_pages(walton_raw)
    if len(walton_pages) != 266:
        raise ValueError(f'Expected 266 Walton scan pages, found {len(walton_pages)}')
    walton_rows = []
    for scan_page in (90, 91):
        text_value = walton_pages[scan_page - 1]
        if not re.search(r'language|dialect|Garhwali', text_value, re.I):
            raise ValueError(f'Walton language passage absent from scan page {scan_page}')
        record = make_record(
            'walton_gazetteer_1910', f'scan-page-{scan_page}', text_value, walton_info,
            'Public-Domain', 'https://archive.org/details/in.ernet.dli.2015.48008',
            'H. G. Walton, British Garhwal: A Gazetteer (1910)',
            scan_page=scan_page, corpus_layer='historical_review',
            genre='historical_gazetteer_language_note', modality='text',
            source_url='https://archive.org/details/in.ernet.dli.2015.48008',
            rights_evidence='sources/online/walton_gazetteer_1910/metadata.json.metadata.json',
            quality_flags=['uncorrected_ocr', 'predominantly_English',
                           'historical_language_description'])
        record.update(iso_639_3='mul', script='mixed', historical=True,
                      modifications='Internet Archive OCR lines retained; no correction')
        walton_rows.append(record)

    save_records(ROOT / 'extracted' / 'historical' / 'kellogg_1893.jsonl', kellogg_rows)
    save_records(ROOT / 'extracted' / 'historical' / 'walton_gazetteer_1910.jsonl', walton_rows)
    print(json.dumps({'kellogg_1893_relevant_pages': len(kellogg_rows),
                      'walton_1910_language_passage_pages': len(walton_rows)}, indent=2))


def sixth_wave_acquire():
    """Acquire additional openly licensed Uttarakhand Open University modules."""
    jobs = [
        ('MAHL-204.pdf', 'https://uou.ac.in/sites/default/files/slm/MAHL-204.pdf'),
        ('MAHL-610.pdf', 'https://www.uou.ac.in/sites/default/files/slm/MAHL-610.pdf'),
        ('MAHL-611.pdf', 'https://www.uou.ac.in/sites/default/files/slm/MAHL-611.pdf'),
        ('terms.html', 'https://uou.ac.in/terms-use'),
    ]
    for name, url in jobs:
        data, _ = fetch('uou_more', name, url, max_time=300, max_size=200000000)
        print('uou_more', name, len(data), flush=True)


def sixth_wave_extract():
    import ocr_uou_more
    ocr_uou_more.main()


def scholarly_open_sources():
    """Rights-audited scholarship used as reference material, never corpus rows."""
    return [
        {
            'source_id': 'acl_dialect_matters',
            'title': 'Dialect Matters: Cross-Lingual ASR Transfer for Low-Resource Indic Language Varieties',
            'authors': ['Akriti Dhasmana', 'Aarohi Srivastava', 'David Chiang'],
            'year': 2026,
            'topic': 'Garhwali ASR, code-mixing, dialect transfer, and error analysis',
            'landing_page': 'https://aclanthology.org/2026.vardial-1.12/',
            'license_id': 'CC-BY-4.0',
            'license_url': BY,
            'license_evidence': 'https://aclanthology.org/faq/copyright/',
            'artifacts': ['landing.html', 'paper.pdf', 'copyright.html'],
            'disposition': 'open_research_reference',
        },
        {
            'source_id': 'scholarly_montaut_2022',
            'title': "On the Non-Lexical Categories of avyay 'Invariables' and Their Grammaticalization in Pahari Languages, with a Comparison to Standard Hindi",
            'authors': ['Annie Montaut'],
            'year': 2022,
            'topic': 'Garhwali and Kumaoni adpositions, case marking, particles, and grammaticalization',
            'landing_page': 'https://hasp.ub.uni-heidelberg.de/catalog/book/919',
            'license_id': 'CC-BY-SA-4.0',
            'license_url': SA,
            'license_evidence': 'https://hasp.ub.uni-heidelberg.de/catalog/book/919',
            'artifacts': [
                'book.html (access-challenge response)',
                'chapter.html (access-challenge response)',
            ],
            'local_access_status': 'automated_full_text_blocked_by_anubis_challenge',
            'disposition': 'catalogued_open_license_access_challenge',
        },
        {
            'source_id': 'scholarly_sahu_2023',
            'title': 'Preserving the Linguistic Diversity of Uttarakhand: Role of Language and Education Policies',
            'authors': ['Preety Sahu'],
            'year': 2023,
            'topic': 'Garhwali language vitality, education, policy, and intergenerational transmission',
            'landing_page': 'https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194',
            'license_id': 'CC-BY-4.0',
            'license_url': BY,
            'license_evidence': 'https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'open_research_reference',
        },
        {
            'source_id': 'scholarly_uniyal_2019',
            'title': 'English-Garhwali SMT System – Development and Evaluation',
            'authors': ['Arushi Uniyal'],
            'year': 2019,
            'topic': 'English-Garhwali parallel corpora, statistical MT, evaluation, and error categories',
            'landing_page': 'https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation',
            'license_id': 'CC-BY-NC-3.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc/3.0/',
            'license_evidence': 'https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'restricted_noncommercial_research_reference',
        },
        {
            'source_id': 'scholarly_stronski_2010',
            'title': 'Non-Nominative Subjects in Rajasthani and Central Pahari: The Status of the Ergative and Obligatory Constructions',
            'authors': ['Krzysztof Stroński'],
            'year': 2010,
            'topic': 'Central Pahari split ergativity, obligation, and non-nominative subjects',
            'landing_page': 'https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9',
            'license_id': 'CC-BY-NC-ND-4.0',
            'license_url': 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
            'license_evidence': 'https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9',
            'artifacts': ['landing.html', 'paper.pdf'],
            'disposition': 'unaltered_noncommercial_research_reference',
        },
    ]


def seventh_wave_acquire():
    """Acquire openly licensed scholarship that directly informs Garhwali work."""
    jobs = [
        ('acl_dialect_matters', 'copyright.html', 'https://aclanthology.org/faq/copyright/'),
        ('scholarly_montaut_2022', 'book.html', 'https://hasp.ub.uni-heidelberg.de/catalog/book/919'),
        ('scholarly_montaut_2022', 'chapter.html', 'https://hasp.ub.uni-heidelberg.de/catalog/view/919/1911/99513'),
        ('scholarly_sahu_2023', 'landing.html', 'https://www.journals.asianresassoc.org/index.php/ijll/article/view/1194'),
        ('scholarly_sahu_2023', 'paper.pdf', 'https://www.journals.asianresassoc.org/index.php/ijll/article/download/1194/755/2774'),
        ('scholarly_uniyal_2019', 'landing.html', 'https://www.researchpublish.com/papers/english-garhwali-smt-system--development-and-evaluation'),
        ('scholarly_uniyal_2019', 'paper.pdf', 'https://www.researchpublish.com/upload/book/English%20Garhwali-6998.pdf'),
        ('scholarly_stronski_2010', 'landing.html', 'https://pressto.amu.edu.pl/index.php/linpo/article/view/v10122-010-0007-9'),
        ('scholarly_stronski_2010', 'paper.pdf', 'https://pressto.amu.edu.pl/index.php/linpo/article/download/v10122-010-0007-9/28671'),
    ]
    for source, name, url in jobs:
        data, _ = fetch(source, name, url, max_time=180, max_size=50000000)
        print(source, name, len(data), flush=True)


def seventh_wave_extract():
    """Create a tracked manifest; scholarly prose stays outside language data layers."""
    sources = scholarly_open_sources()
    for source in sources:
        for artifact in source['artifacts']:
            snapshot_name = artifact.split(' (', 1)[0]
            snapshot(source['source_id'], snapshot_name)
    destination = ROOT / 'research' / 'scholarly-open-sources.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps({
        'purpose': 'Rights-audited scholarly references for corpus design and linguistic analysis',
        'corpus_records_added': 0,
        'sources': sources,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'scholarly_sources': len(sources), 'corpus_records_added': 0}, indent=2))


CULTURAL_TERMS = (
    'garhwal', 'garhwál', 'garhwâl', 'garhwalí', 'garhwali', 'gurhwal', 'gurwal',
    'गढ़वाल', 'गढ़वाली', 'गढ़वाल', 'गढ़वाली',
)


def cultural_chunks(text, terms=CULTURAL_TERMS, source_kind='page'):
    """Select page- or paragraph-level cultural evidence without copying whole books."""
    if source_kind == 'page':
        if '\f' in text:
            units = text.split('\f')
        else:
            paragraphs = re.split(r'\n\s*\n', text)
            units = []
            current = []
            current_size = 0
            for paragraph in paragraphs:
                if current and current_size + len(paragraph) > 6000:
                    units.append('\n\n'.join(current))
                    current = []
                    current_size = 0
                current.append(paragraph)
                current_size += len(paragraph)
            if current:
                units.append('\n\n'.join(current))
    elif source_kind == 'passage':
        units = re.split(r'\n\s*\n', text)
    else:
        raise ValueError(f'Unknown cultural source kind: {source_kind}')
    selected = []
    lowered_terms = tuple(term.casefold() for term in terms)
    for index, unit in enumerate(units, 1):
        cleaned = re.sub(r'[ \t]+', ' ', unit)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        if len(cleaned) < 40:
            continue
        folded = cleaned.casefold()
        if any(term in folded for term in lowered_terms):
            selected.append({'source_unit': index, 'text': cleaned})
    return selected


def cultural_genres(text):
    vocabulary = {
        'folk_narrative': ('folklore', 'folk-lore', 'legend', 'tale', 'story', 'myth', 'गाथा', 'कथा'),
        'performance': ('song', 'ballad', 'dance', 'drum', 'theatre', 'play', 'गीत', 'नाटक', 'नृत्य', 'ढोल'),
        'ritual_religion': ('ritual', 'worship', 'deity', 'god', 'goddess', 'shrine', 'temple', 'पूजा', 'देव', 'मंदिर'),
        'social_custom': ('marriage', 'custom', 'caste', 'festival', 'fair', 'विवाह', 'रीति', 'त्योहार', 'मेला'),
        'material_culture': ('food', 'dress', 'house', 'craft', 'agriculture', 'crop', 'भोजन', 'वेश', 'शिल्प', 'कृषि'),
        'language_literature': ('language', 'dialect', 'proverb', 'poem', 'literature', 'भाषा', 'बोली', 'कहावत', 'कविता'),
        'place_history': ('history', 'king', 'village', 'district', 'इतिहास', 'राजा', 'गांव', 'जिला'),
    }
    folded = text.casefold()
    labels = [label for label, markers in vocabulary.items()
              if any(marker.casefold() in folded for marker in markers)]
    return labels or ['general_cultural_context']


def cultural_record(source, key, text, info, license_id, license_url, attribution, **extra):
    record = make_record(source, key, text, info, license_id, license_url, attribution, **extra)
    record.update(iso_639_3='eng', script='Latn', corpus_layer='cultural_reference',
                  usage='research_context_only', historical=True, training_eligible=False)
    return record


class GenericTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.skipped = 0

    def handle_starttag(self, tag, _attrs):
        if tag in ('script', 'style'):
            self.skipped += 1
        elif tag in ('p', 'li', 'h1', 'h2', 'h3', 'br') and not self.skipped:
            self.parts.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skipped:
            self.skipped -= 1
        elif tag in ('p', 'li', 'h1', 'h2', 'h3') and not self.skipped:
            self.parts.append('\n')

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)

    def text(self):
        value = html.unescape(''.join(self.parts))
        value = re.sub(r'[ \t]+', ' ', value)
        return re.sub(r'\n{3,}', '\n\n', value).strip()


class TableAndLineParser(HTMLParser):
    """Retain table cells and visual block boundaries from vocabulary pages."""

    def __init__(self):
        super().__init__()
        self.parts, self.rows = [], []
        self.row = self.cell = None
        self.skipped = 0

    def handle_starttag(self, tag, _attrs):
        if tag in ('script', 'style'):
            self.skipped += 1
        elif not self.skipped:
            if tag in ('div', 'p', 'li', 'br', 'tr'):
                self.parts.append('\n')
            if tag == 'tr':
                self.row = []
            elif tag in ('td', 'th') and self.row is not None:
                self.cell = []

    def handle_endtag(self, tag):
        if tag in ('script', 'style') and self.skipped:
            self.skipped -= 1
        elif not self.skipped:
            if tag in ('td', 'th') and self.cell is not None:
                self.row.append(re.sub(r'\s+', ' ', ''.join(self.cell)).strip())
                self.cell = None
            elif tag == 'tr' and self.row is not None:
                if self.row:
                    self.rows.append(self.row)
                self.row = None
            if tag in ('div', 'p', 'li', 'tr'):
                self.parts.append('\n')

    def handle_data(self, data):
        if not self.skipped:
            self.parts.append(data)
            if self.cell is not None:
                self.cell.append(data)

    def lines(self):
        value = html.unescape(''.join(self.parts))
        return [re.sub(r'\s+', ' ', line).strip()
                for line in value.splitlines() if line.strip()]


THEMED_DOMAINS = {
    'bird': {'bird', 'pigeon', 'kite', 'eagle', 'vulture', 'partridge', 'hen',
             'sparrow', 'monal', 'crow', 'cuckoo', 'owl', 'starling', 'blackbird'},
    'animal': {'animal', 'fish', 'dog', 'snake', 'worm', 'cow', 'buffalo', 'goat',
               'sheep', 'ape', 'fox', 'lizard', 'rat', 'ox', 'horse', 'cat', 'tiger',
               'frog', 'bear', 'jackal', 'deer', 'elephant', 'monkey', 'mule', 'kid',
               'calf', 'snail', 'earthworm', 'crab', 'porcupine', 'leopard'},
    'insect': {'insect', 'fly', 'louse', 'leech', 'firefly', 'nit', 'locust',
               'cricket', 'scorpion', 'ant', 'bug', 'cockroach', 'flea', 'honeybee'},
    'plant_nature': {'tree', 'forest', 'fruit', 'seed', 'leaf', 'root', 'bark',
                     'flower', 'grass', 'sun', 'moon', 'star', 'water', 'rain',
                     'river', 'lake', 'sea', 'stone', 'sand', 'earth', 'cloud',
                     'fog', 'sky', 'wind', 'snow', 'ice'},
    'body': {'skin', 'meat', 'blood', 'bone', 'fat', 'egg', 'horn', 'tail', 'feather',
             'hair', 'head', 'ear', 'eye', 'nose', 'mouth', 'tooth', 'tongue',
             'fingernail', 'foot', 'leg', 'knee', 'hand', 'wing', 'belly', 'guts',
             'neck', 'back', 'breast', 'heart', 'liver'},
    'kinship_people': {'woman', 'man', 'child', 'wife', 'husband', 'mother', 'father'},
}


def themed_domain(gloss):
    tokens = set(re.sub(r'[^a-z ]', ' ', gloss.casefold()).split())
    for domain, words in THEMED_DOMAINS.items():
        if tokens & words:
            return domain
    return 'basic_vocabulary'


def devanagari_variants(value):
    """Extract written forms while dropping romanization and editorial notes."""
    value = re.sub(r'\([^)]*\)', '', value)
    value = re.sub(r'\[[^]]*\]|\{[^}]*\}', '', value)
    variants = []
    for piece in re.split(r'[,/;]', value):
        piece = piece.strip(' .?–—-')
        if piece and any('\u0900' <= char <= '\u097f' for char in piece):
            variants.append(piece)
    return variants


def themed_lexicon_record(source, key, term, info, license_id, license_url,
                           attribution, gloss_en=None, gloss_hi=None, **extra):
    script = extra.pop('script', 'Deva')
    record = make_record(source, key, term, info, license_id, license_url, attribution,
                         gloss_en=gloss_en, gloss_hi=gloss_hi,
                         semantic_domain=extra.pop('semantic_domain', themed_domain(gloss_en or '')),
                         genre='thematic_lexicon', modality='text',
                         corpus_layer='research_lexicon', usage='research_and_native_review',
                         **extra)
    record['training_eligible'] = False
    record['script'] = script
    return record


def local_gloss_domain(gloss):
    folded = gloss.casefold()
    rules = {
        'food': ('dish', 'bread', 'flour', 'food', 'sugar', 'butter', 'wine', 'grain'),
        'plant_nature': ('plant', 'tree', 'forest', 'grass', 'flower', 'seed', 'fruit', 'meadow'),
        'household_object': ('vessel', 'utensil', 'basket', 'stove', 'mill', 'blanket', 'rug'),
        'clothing_ornament': ('blouse', 'cloth', 'skirt', 'bangle', 'ring', 'slipper', 'trousers'),
        'agriculture_livestock': ('agricultur', 'crop', 'cattle', 'livestock', 'grazing', 'pastoral'),
        'ritual_culture': ('festival', 'deity', 'goddess', 'worship', 'ritual', 'dance', 'marriage'),
        'land_geography': ('river', 'stream', 'land', 'village', 'mountain', 'gullies'),
    }
    for domain, markers in rules.items():
        if any(marker in folded for marker in markers):
            return domain
    return 'local_cultural_term'


def hindi_gloss_domain(gloss, default='basic_vocabulary'):
    compact = re.sub(r'\s+', '', gloss)
    markers = {
        'bird': ('पक्षी', 'कठफोड़ा'),
        'insect': ('पिस्सू', 'खटमल', 'मच्छर', 'कनखजूरा', 'ततैया', 'मक्खी', 'चींटी',
                   'तितली', 'मकड़ा', 'बिच्छु', 'जूं', 'लीख', 'जुगुनू', 'कीड़ा'),
        'plant_nature': ('सूरज', 'चन्द्रमा', 'तारे', 'उज्याला', 'अन्धेरा', 'आसमान', 'हवा',
                         'नदि', 'पर्वत', 'बर्फ', 'पानी', 'पत्थर', 'फूल', 'काँटा', 'जड़',
                         'लकड़ी', 'घास', 'झारना', 'चमक', 'जंगल', 'पेड़', 'बिजली', 'तूफान'),
        'kinship_people': ('पत्नी', 'औरत', 'लडका'),
    }
    for domain, words in markers.items():
        if any(word in compact for word in words):
            return domain
    return default


def ninth_wave_acquire():
    """Acquire rendered public pages containing Garhwali thematic vocabulary."""
    jobs = [
        ('wiktionary-swadesh-rendered.json',
         'https://en.wiktionary.org/w/api.php?action=parse&page=Appendix%3AGarhwali_Swadesh_list&prop=text%7Crevid&format=json&formatversion=2'),
        ('animals-birds-uttarakhandiwords.html', 'https://uttarakhandiwords.blogspot.com/2011/09/blog-post.html'),
        ('animals-emagazine.html', 'https://e-magazineofuttarakhand.blogspot.com/2012/02/names-of-animals-birds-etc-in-garhwali.html'),
        ('dictionary-garhwalilanguage.html', 'https://www.garhwalilanguage.com/en/garhwali-dictionary'),
        ('occupations-dhyani.html', 'https://sites.google.com/view/dhyani/%E0%A4%B0%E0%A4%AE%E0%A4%95%E0%A4%A4-%E0%A4%AC%E0%A4%9C%E0%A4%B5%E0%A4%B2/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B2-%E0%A4%AE-%E0%A4%B2%E0%A4%95-%E0%A4%B5%E0%A4%AF%E0%A4%B5%E0%A4%B8%E0%A4%AF-%E0%A4%B8%E0%A4%AE%E0%A4%AC%E0%A4%A8%E0%A4%A7-%E0%A4%B6%E0%A4%AC%E0%A4%A6%E0%A4%B5%E0%A4%B2'),
        ('mountainvoices-glossary.html', 'https://mountainvoices.org/i_glossary.html'),
        ('ramman-pib.pdf', 'https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/sep/doc2025929651301.pdf'),
    ]
    for name, url in jobs:
        data, _ = fetch('themed_vocabulary', name, url, max_time=180, max_size=20000000)
        print(name, len(data), flush=True)


def ninth_wave_extract():
    """Build a provenance-rich, review-gated semantic lexicon from web sources."""
    rows = []
    raw, info = snapshot('themed_vocabulary', 'wiktionary-swadesh-rendered.json')
    payload = json.loads(raw)
    parser = TableAndLineParser(); parser.feed(payload['parse']['text'])
    for table_row in parser.rows[1:]:
        if len(table_row) < 3 or not table_row[2].strip():
            continue
        gloss = table_row[1].strip()
        for variant_index, term in enumerate(devanagari_variants(table_row[2]), 1):
            rows.append(themed_lexicon_record(
                'wiktionary_swadesh_thematic', f'{table_row[0]}:{variant_index}', term, info,
                'CC-BY-SA-4.0', SA, 'English Wiktionary contributors', gloss_en=gloss,
                source_entry_number=int(table_row[0]), source_revision=payload['parse'].get('revid'),
                confidence='medium', quality_flags=['community_edited', 'needs_native_review']))

    raw, info = snapshot('themed_vocabulary', 'dictionary-garhwalilanguage.html')
    parser = TableAndLineParser(); parser.feed(raw.decode('utf-8', errors='replace'))
    for index, table_row in enumerate(parser.rows[1:], 1):
        if len(table_row) != 2:
            continue
        for variant_index, term in enumerate(devanagari_variants(table_row[1]), 1):
            rows.append(themed_lexicon_record(
                'garhwalilanguage_dictionary', f'{index}:{variant_index}', term, info,
                'LicenseRef-All-Rights-Reserved', info['url'], 'GarhwaliLanguage.com',
                gloss_hi=table_row[0], semantic_domain=hindi_gloss_domain(table_row[0]), confidence='low',
                quality_flags=['publisher_license_not_stated', 'needs_native_review']))

    raw, info = snapshot('themed_vocabulary', 'animals-birds-uttarakhandiwords.html')
    parser = TableAndLineParser(); parser.feed(raw.decode('utf-8', errors='replace'))
    for line_index, line in enumerate(parser.lines()[12:69], 12):
        parts = [part.strip() for part in re.split(r'\s*[-–—]\s*', line) if part.strip()]
        if len(parts) < 3 or not re.search(r'[A-Za-z]', parts[0]):
            continue
        gloss_en = 'bear' if parts[0].casefold() == 'beer' else parts[0]
        for variant_index, term in enumerate(devanagari_variants(parts[2]), 1):
            flags = ['community_compilation', 'needs_native_review']
            if parts[0].casefold() == 'beer':
                flags.append('source_gloss_typo_normalized_bear')
            rows.append(themed_lexicon_record(
                'uttarakhandiwords_animals', f'{line_index}:{variant_index}', term, info,
                'LicenseRef-All-Rights-Reserved', info['url'], 'Uttarakhandi Words blog contributors',
                gloss_en=gloss_en, gloss_hi=parts[1], confidence='low', quality_flags=flags))

    raw, info = snapshot('themed_vocabulary', 'animals-emagazine.html')
    parser = TableAndLineParser(); parser.feed(raw.decode('utf-8', errors='replace'))
    for line_index, line in enumerate(parser.lines(), 1):
        parts = [part.strip() for part in re.split(r'-{5,}', line)]
        if len(parts) < 3 or not any('\u0900' <= char <= '\u097f' for char in parts[0]):
            continue
        for variant_index, term in enumerate(devanagari_variants(parts[-1]), 1):
            rows.append(themed_lexicon_record(
                'emagazine_animals', f'{line_index}:{variant_index}', term, info,
                'LicenseRef-All-Rights-Reserved', info['url'], 'Bhishma Kukreti; E-Magazine of Uttarakhand',
                gloss_hi=parts[0], semantic_domain=hindi_gloss_domain(parts[0], 'animal'), confidence='low',
                quality_flags=['community_compilation', 'dialect_variation_possible', 'needs_native_review']))

    raw, info = snapshot('themed_vocabulary', 'occupations-dhyani.html')
    parser = TableAndLineParser(); parser.feed(raw.decode('utf-8', errors='replace'))
    for line_index, line in enumerate(parser.lines(), 1):
        match = re.fullmatch(r'(.+?)-\s*\((.+)\)\s*', line)
        if not match:
            continue
        for variant_index, term in enumerate(devanagari_variants(match.group(1)), 1):
            rows.append(themed_lexicon_record(
                'dhyani_occupations', f'{line_index}:{variant_index}', term, info,
                'LicenseRef-All-Rights-Reserved', info['url'],
                'Ramakant Benjwal and Beena Benjwal dictionary; reproduced by Bal Krishna D. Dhyani',
                gloss_hi=match.group(2), semantic_domain='occupation', confidence='medium',
                quality_flags=['dictionary_attribution_present', 'publisher_license_not_stated', 'needs_native_review']))

    _, info = snapshot('themed_vocabulary', 'ramman-pib.pdf')
    instruments = [('ढोल', 'Dhol', 'drum'), ('दमाऊ', 'Damau', 'smaller percussion drum'),
                   ('मंजीरा', 'Manjira', 'small hand cymbals'), ('झांझर', 'Jhanjhar', 'larger cymbals'),
                   ('भंकोरा', 'Bhankora', 'trumpet')]
    for index, (term, roman, gloss) in enumerate(instruments, 1):
        rows.append(themed_lexicon_record(
            'pib_ramman_instruments', index, term, info, 'LicenseRef-Government-Publication', info['url'],
            'Press Information Bureau, Government of India', gloss_en=gloss,
            semantic_domain='instrument', romanization=roman, confidence='high',
            quality_flags=['manual_transcription_from_source_list', 'needs_native_review']))

    raw, info = snapshot('themed_vocabulary', 'mountainvoices-glossary.html')
    parser = TableAndLineParser(); parser.feed(raw.decode('windows-1252', errors='replace'))
    glossary_index = 0
    for table_row in parser.rows:
        if len(table_row) != 2 or not table_row[0].strip() or not table_row[1].strip():
            continue
        term = table_row[0].strip().strip('–—- ').replace('\ufffd', '')
        gloss = table_row[1].strip().replace('\ufffd', '–')
        if not term or len(term) > 80:
            continue
        glossary_index += 1
        rows.append(themed_lexicon_record(
            'mountainvoices_local_glossary', glossary_index, term, info,
            'LicenseRef-Panos-Website-Terms-Unverified', info['url'],
            'Panos London, Mountain Voices oral testimony project', gloss_en=gloss,
            semantic_domain=local_gloss_domain(gloss), script='Latn', confidence='low',
            language_scope='Garhwali_or_regional_Hindi; source_does_not_separate',
            quality_flags=['regional_glossary', 'language_identity_requires_native_review',
                           'publisher_license_not_stated']))

    exact_seen, unique_rows = set(), []
    for row in rows:
        identity = (row['source_id'], row['text_normalized'], row.get('gloss_en'), row.get('gloss_hi'))
        if identity not in exact_seen:
            exact_seen.add(identity); unique_rows.append(row)
    counts = Counter(row['semantic_domain'] for row in unique_rows)
    source_counts = Counter(row['source_id'] for row in unique_rows)
    unique_form_count = len({row['text_normalized'] for row in unique_rows})
    (ROOT / 'research' / 'garhwali-thematic-lexicon.json').write_text(json.dumps({
        'purpose': 'Web-scraped Garhwali thematic vocabulary for research and native-speaker review',
        'training_eligible': False, 'record_count': len(unique_rows),
        'unique_written_form_count': unique_form_count,
        'source_counts': dict(sorted(source_counts.items())),
        'domain_counts': dict(sorted(counts.items())), 'records': unique_rows,
    }, ensure_ascii=False, indent=2) + '\n')
    save_records(ROOT / 'restricted' / 'thematic_web_lexicon.jsonl', unique_rows)
    print(json.dumps({'thematic_lexicon_records': len(unique_rows),
                      'domain_counts': dict(sorted(counts.items()))}, ensure_ascii=False, indent=2))
    return len(unique_rows)


def eighth_wave_acquire():
    """Acquire open cultural history, folklore, and media metadata."""
    gazetteer_files = {
        'v1p1': ('1882himalayangazetteervol1pt1', '1882 Himalayan Gazetteer Vol 1 Pt 1_djvu.txt'),
        'v1p2': ('1882himalayangazetteervol1pt2', '1882 Himalayan Gazetteer Vol 1 Pt 2_djvu.txt'),
        'v2p1': ('1882himalayangazetteervol2pt1', '1882 Himalayan Gazetteer Vol 2 Pt 1_djvu.txt'),
        'v2p2': ('1882himalayangazetteervol2pt2', '1882 Himalayan Gazetteer Vol 2 Pt 2_djvu.txt'),
        'v3p1': ('1882himalayangazetteervol3pt1', '1882 Himalayan Gazetteer Vol 3 Pt 1_djvu.txt'),
        'v3p2': ('1882himalayangazetteervol3pt2', '1882 Himalayan Gazetteer Vol 3 Pt 2_djvu.txt'),
    }
    for part, (identifier, filename) in gazetteer_files.items():
        base = f'https://archive.org/download/{identifier}/'
        fetch('atkinson_himalayan_gazetteer', f'{part}.txt', base + quote(filename),
              max_time=300, max_size=30000000)
        fetch('atkinson_himalayan_gazetteer', f'{part}-metadata.json',
              f'https://archive.org/metadata/{identifier}', max_time=120, max_size=3000000)

    for volume, ebook in ((1, 43681), (2, 43682)):
        fetch('crooke_northern_india_folklore', f'volume-{volume}.txt',
              f'https://www.gutenberg.org/cache/epub/{ebook}/pg{ebook}.txt',
              max_time=180, max_size=5000000)
        fetch('crooke_northern_india_folklore', f'volume-{volume}-landing.html',
              f'https://www.gutenberg.org/ebooks/{ebook}', max_time=120, max_size=3000000)

    for index, title in enumerate((
            '1911 Encyclopædia Britannica/Garhwal',
            '1911 Encyclopædia Britannica/Pahari'), 1):
        url = 'https://en.wikisource.org/w/api.php?' + urlencode({
            'action': 'parse', 'page': title, 'prop': 'text|displaytitle',
            'disableeditsection': '1', 'format': 'json', 'formatversion': '2',
        })
        fetch('wikisource_garhwal_culture', f'parsed-article-{index}.json', url)

    commons_params = {
        'action': 'query', 'generator': 'categorymembers',
        'gcmtitle': 'Category:Garhwali people', 'gcmtype': 'file', 'gcmlimit': '500',
        'prop': 'imageinfo', 'iiprop': 'url|extmetadata',
        'format': 'json', 'formatversion': '2',
    }
    page_number = 0
    while True:
        commons_url = 'https://commons.wikimedia.org/w/api.php?' + urlencode(commons_params)
        name = 'media.json' if page_number == 0 else f'media-page-{page_number:03d}.json'
        raw, _ = fetch('commons_garhwali_culture', name, commons_url,
                       max_time=180, max_size=20000000)
        continuation = json.loads(raw).get('continue', {}).get('gcmcontinue')
        if not continuation:
            break
        commons_params['gcmcontinue'] = continuation
        page_number += 1


def eighth_wave_extract():
    """Extract source-specific cultural references and exact-deduplicate them."""
    pdm = 'https://creativecommons.org/publicdomain/mark/1.0/'
    rows = []
    for part in ('v1p1', 'v1p2', 'v2p1', 'v2p2', 'v3p1', 'v3p2'):
        raw, info = snapshot('atkinson_himalayan_gazetteer', f'{part}.txt')
        metadata_raw, metadata_info = snapshot('atkinson_himalayan_gazetteer', f'{part}-metadata.json')
        metadata = json.loads(metadata_raw)
        for chunk in cultural_chunks(raw.decode('utf-8', errors='replace'), source_kind='page'):
            rows.append(cultural_record(
                'atkinson_himalayan_gazetteer', f'{part}:page-{chunk["source_unit"]:04d}',
                chunk['text'], dict(info, rights_snapshot=metadata_info,
                                    archive_identifier=metadata['metadata']['identifier']),
                'Public-Domain', pdm,
                'Edwin T. Atkinson, The Himalayan Districts of the North-Western Provinces of India (1882–1886)',
                source_part=part, source_unit=chunk['source_unit'],
                cultural_genres=cultural_genres(chunk['text']),
                quality_flags=['historical_colonial_source', 'machine_ocr', 'garhwali_relevance_keyword_selected']))

    for volume in (1, 2):
        raw, info = snapshot('crooke_northern_india_folklore', f'volume-{volume}.txt')
        _, landing_info = snapshot('crooke_northern_india_folklore', f'volume-{volume}-landing.html')
        for chunk in cultural_chunks(raw.decode('utf-8', errors='replace'), source_kind='passage'):
            rows.append(cultural_record(
                'crooke_northern_india_folklore', f'volume-{volume}:passage-{chunk["source_unit"]:04d}',
                chunk['text'], dict(info, rights_snapshot=landing_info, gutenberg_ebook=43680 + volume),
                'Project-Gutenberg-Public-Domain-US',
                'https://www.gutenberg.org/policy/permission.html',
                f'William Crooke, The Popular Religion and Folk-Lore of Northern India, volume {volume} (1896); Project Gutenberg',
                source_volume=volume, source_unit=chunk['source_unit'],
                cultural_genres=cultural_genres(chunk['text']),
                quality_flags=['historical_colonial_source', 'garhwali_relevance_keyword_selected']))

    for index, title in enumerate(('Garhwal', 'Pahari'), 1):
        raw, info = snapshot('wikisource_garhwal_culture', f'parsed-article-{index}.json')
        parsed = json.loads(raw)['parse']
        parser = GenericTextParser()
        parser.feed(parsed.get('text', ''))
        text_value = parser.text()
        if text_value:
            rows.append(cultural_record(
                'wikisource_garhwal_culture', title.casefold(), text_value, info,
                'Public-Domain', pdm,
                f'1911 Encyclopædia Britannica, “{title}”, via Wikisource',
                source_title=parsed['title'],
                source_url=f'https://en.wikisource.org/wiki/{quote(parsed["title"].replace(" ", "_"), safe="/_")}',
                cultural_genres=cultural_genres(text_value),
                quality_flags=['historical_encyclopedia', 'dated_terminology_review_required']))

    seen = set()
    unique_rows = []
    for row in rows:
        if row['text_sha256'] in seen:
            continue
        seen.add(row['text_sha256'])
        unique_rows.append(row)
    save_records(ROOT / 'extracted' / 'historical' / 'cultural_references.jsonl', unique_rows)

    media = []
    page_number = 0
    while True:
        name = 'media.json' if page_number == 0 else f'media-page-{page_number:03d}.json'
        pointer = RAW / 'commons_garhwali_culture' / f'{name}.metadata.json'
        if not pointer.exists():
            break
        raw, info = snapshot('commons_garhwali_culture', name)
        for page in json.loads(raw).get('query', {}).get('pages', []):
            imageinfo = (page.get('imageinfo') or [{}])[0]
            metadata = imageinfo.get('extmetadata', {})
            media.append({
                'source_id': 'commons_garhwali_culture', 'title': page.get('title'),
                'page_id': page.get('pageid'), 'description_url': imageinfo.get('descriptionurl'),
                'original_url': imageinfo.get('url'),
                'license_short_name': metadata.get('LicenseShortName', {}).get('value'),
                'license_url': metadata.get('LicenseUrl', {}).get('value'),
                'artist': metadata.get('Artist', {}).get('value'),
                'credit': metadata.get('Credit', {}).get('value'),
                'description': metadata.get('ImageDescription', {}).get('value'),
                'provenance': info,
            })
        page_number += 1
    media_destination = ROOT / 'research' / 'garhwali-cultural-media.json'
    media_destination.write_text(json.dumps({
        'purpose': 'Open-media discovery metadata; media binaries are referenced, not bulk downloaded',
        'records': media,
    }, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cultural_reference_records': len(unique_rows),
                      'commons_media_records': len(media)}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['survey', 'meta', 'probes', 'wiktionary', 'acquire', 'extract', 'downloads', 'restricted', 'uou', 'wayback', 'archive_open', 'archive_extract', 'more_acquire', 'more_extract', 'historical_more_acquire', 'historical_more_extract', 'opus_acquire', 'opus_extract', 'indic_asr_acquire', 'indic_asr_range_acquire', 'indic_asr_extract', 'panlex_acquire', 'panlex_extract', 'third_wave_acquire', 'third_wave_extract', 'fourth_wave_acquire', 'fourth_wave_extract', 'fifth_wave_acquire', 'fifth_wave_extract', 'sixth_wave_acquire', 'sixth_wave_extract', 'seventh_wave_acquire', 'seventh_wave_extract', 'eighth_wave_acquire', 'eighth_wave_extract', 'ninth_wave_acquire', 'ninth_wave_extract'])
    args = parser.parse_args()
    print('result', globals()[args.action]())


if __name__ == '__main__':
    main()
