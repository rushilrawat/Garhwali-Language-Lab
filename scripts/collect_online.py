"""Auditable public-source collection. No credentials, access bypasses or uploads.

Snapshots are content addressed. The source ledger records successful and failed
requests. Corpus promotion is always a separate, human-reviewed operation.
"""
import argparse
import html
import io
import json
import gzip
import re
import subprocess
import time
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlencode, quote

from online_sources.records import (  # noqa: F401 - re-exported for callers and tests
    VERSION,
    BY,
    SA,
    sha,
    now,
    make_record,
    latin_record,
    save_records,
    csv_dict_rows,
)
from online_sources.parsers import (  # noqa: F401 - re-exported for callers and tests
    GenericTextParser,
    OBSTextParser,
    TableAndLineParser,
    sand_garhwali_records,
    chan_garhwali_records,
    mamta_garhwali_records,
    lsi_cldf_garhwali_records,
    obs_text_blocks,
    obs_garhwali_record,
    djvu_word_pages,
    garhwali_section,
    plain_wikitext,
    wiktionary_page_records,
    incubator_wiktionary_records,
    meta_record,
    benchmark_record,
    indic_asr_record,
    paharili_line,
    madlad_clean_records,
    madlad_provenance,
)
from online_sources.vocabulary import (  # noqa: F401 - re-exported for callers and tests
    CULTURAL_TERMS,
    cultural_chunks,
    cultural_genres,
    cultural_record,
    THEMED_DOMAINS,
    themed_domain,
    devanagari_variants,
    themed_lexicon_record,
    local_gloss_domain,
    hindi_gloss_domain,
)
from online_sources.registry import (  # noqa: F401 - re-exported for callers and tests
    WAVES,
    scholarly_open_sources,
)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'sources' / 'online'
CORPUS = ROOT / 'corpus'
LOG = RAW / 'requests.jsonl'


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
        p = subprocess.run(['curl', '--proto', '=https', '--proto-redir', '=https',
                            '--fail', '--location', '--silent', '--show-error',
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
            rows.extend(wiktionary_page_records(p, info))
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


def extract():
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
    rows = incubator_wiktionary_records(data, info)
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
            is_lsi = source == 'lsi'
            r = make_record(source, f'xml-page-{i}', text, info,
                'Public-Domain-US-UK-India',
                'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
                'George Abraham Grierson, Linguistic Survey of India IX.4 (1916)' if is_lsi else 'Ganga Datt Upreti, Proverbs & Folklore of Kumaun and Garhwal (1894)',
                corpus_layer='historical_review', genre='historical_linguistics', modality='text',
                source_url='https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu' if is_lsi else 'https://archive.org/details/cu31924089930774',
                xml_page_index=i, xml_page_identifier=p.get('usemap'),
                rights_status=(
                    'public_domain_us_uk_india_term_expired_grierson' if is_lsi
                    else 'public_domain_us_uk_india_term_expired_upreti_proverbs'
                ),
                rights_scope='United States, United Kingdom, and India; historical publication and author-life terms documented for this edition',
                rights_evidence=(
                    'Official-edition scan and public-domain status (1916, G. A. Grierson): https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu; bibliographic publication record: https://glottolog.org/resource/reference/id/50321; Grierson obituary, died 7 March 1941: https://www.nature.com/articles/147408a0; UK Copyright, Designs and Patents Act 1988 §12 (life plus 70): https://www.legislation.gov.uk/ukpga/1988/48/section/12; India Copyright Act 1957 §22 (life plus 60): https://copyright.gov.in/Copyright_Act_1957/chapter_v.html; U.S. Copyright Office statement on works published before 1931: https://www.copyright.gov/what-is-copyright/. The documented term expired in India in 2001 and the UK in 2011; Wikimedia identifies the pre-1931 edition as public domain in the United States. This assessment covers the cited 1916 volume, not other LSI editions or later editorial material.'
                    if is_lsi else
                    'Original edition scan and publication record (1894): https://archive.org/details/cu31924089930774; publisher-supplied author biography gives Ganga Datt Upreti dates 1 December 1834–1 August 1910: https://garudalife.in/proverbs-and-folklore-of-kumaun-and-garhwal; IGNCA identifies him as deceased: https://ignca.gov.in/proverbs-and-folklore-of-kumaun-and-garhwal/; Google Books title record for the 1900 Hill Dialects edition: https://books.google.com/books?id=veUTAAAAYAAJ; UK Copyright, Designs and Patents Act 1988 §12 (life plus 70): https://www.legislation.gov.uk/ukpga/1988/48/section/12; India Copyright Act 1957 §22 (life plus 60): https://copyright.gov.in/Copyright_Act_1957/chapter_v.html; U.S. Copyright Office statement on works published before 1931: https://www.copyright.gov/what-is-copyright/. The documented author-life term expired in India in 1970 and the UK in 1980; this is a source- and territory-specific assessment, not a blanket license.'
                ),
                quality_flags=['uncorrected_ocr', 'mixed_languages', 'requires_page_alignment_review'])
            r.update(iso_639_3='mul', script='mixed', historical=True,
                language_candidates=['gbm', 'eng'] if is_lsi else ['gbm', 'kfy', 'eng', 'hin'],
                printed_page_candidate=i-14 if is_lsi else None,
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
                'Bafna, Niyati; Žabokrtský, Zdeněk; España-Bonet, Cristina; van Genabith, Josef; Kumar, Lalit Samyak Lalit; Suman, Sharda; Shivay, Rahul. HinDialect 1.1 (2022), LINDAT/CLARIAH-CZ and Kavita Kosh Project. CC BY-NC-SA 4.0.',
                split=split, label=row['label'], usage='evaluation_only',
                corpus_layer='evaluation_only_restricted', genre='folk_text', modality='text',
                rights_status='dataset_deposit_declares_CC_BY_NC_SA_4',
                rights_evidence='https://b2find.eudat.eu/dataset/bd804d5e-e53c-5ee3-b48c-cd2ecbad34de; https://huggingface.co/datasets/mteb/HinDialectClassification/blob/main/README.md',
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
    pdf_raw, pdf_info = snapshot('hill_dialects_1900', 'scan.pdf')
    derived_pointer = RAW / 'hill_dialects_1900' / 'pages.json.metadata.json'
    if derived_pointer.exists():
        payload, info = snapshot('hill_dialects_1900', 'pages.json')
        if info.get('input_sha256s', [None])[0] != pdf_info['sha256']:
            raise ValueError('Cached Hill Dialects extraction was made from a different scan')
        extracted = json.loads(payload)
    else:
        import pdfplumber
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
    if len(extracted) != 25 or [item.get('pdf_page') for item in extracted] != list(range(79, 104)):
        raise ValueError('Cached Hill Dialects extraction is not the expected pages 79-103')
    if any('Garhwal' not in item.get('text', '') for item in extracted):
        raise ValueError('Cached Hill Dialects extraction contains a page outside the Garhwal section')
    rows = []
    for item in extracted:
        rec = make_record(
            'hill_dialects_1900', f'pdf-page-{item["pdf_page"]}', item['text'], info,
            'Public-Domain-US-UK-India',
            'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
            'Ganga Datt Upreti, Hill Dialects of the Kumaun Division (1900)',
            corpus_layer='historical_review', genre='historical_linguistics', modality='text',
            pdf_page=item['pdf_page'], dialect=item['dialect'],
            language_candidates=['gbm', 'eng'],
            source_url='https://books.google.com/books?id=veUTAAAAYAAJ',
            rights_status='public_domain_us_uk_india_term_expired_upreti_hill_dialects',
            rights_scope='United States, United Kingdom, and India; author-life term documented for Ganga Datt Upreti',
            rights_evidence='Google Books full-view scan and publication record (1900): https://books.google.com/books?id=veUTAAAAYAAJ; publisher-supplied author biography gives Ganga Datt Upreti dates 1 December 1834–1 August 1910: https://garudalife.in/proverbs-and-folklore-of-kumaun-and-garhwal; IGNCA identifies him as deceased: https://ignca.gov.in/proverbs-and-folklore-of-kumaun-and-garhwal; UK Copyright, Designs and Patents Act 1988 §12 (life plus 70): https://www.legislation.gov.uk/ukpga/1988/48/section/12; India Copyright Act 1957 §22 (life plus 60): https://copyright.gov.in/Copyright_Act_1957/chapter_v.html; U.S. Copyright Office statement on works published before 1931: https://www.copyright.gov/what-is-copyright/. The documented author-life term expired in India in 1970 and the UK in 1980; this is a source- and territory-specific assessment, not a blanket license.',
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
    for index, (gbm, english) in enumerate(zip(gbm_parallel, en_parallel, strict=True)):
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
            rows.append(indic_asr_record(row, row_index, info))
    if not rows:
        raise ValueError('No Garhwali ASR row snapshots found')
    save_records(ROOT / 'experimental' / 'indic_dialect_asr_gbm.jsonl', rows)
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
                'PanLex materials are part of the PanLex project of The Long Now Foundation, and are shared under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License. PanLex and The Long Now Foundation disclaim any warranties associated with the provision of these materials. For more information about PanLex, please visit panlex.org. Hugging Face mirror: lbourdois/panlex.',
                corpus_layer='restricted_nc_sa', genre='lexicon', modality='text',
                variety_code=item.get('var_code'), language_name=item.get('639-3_english_name'),
                variety_name=item.get('english_name_var'),
                source_url='https://huggingface.co/datasets/lbourdois/panlex',
                rights_status='panlex_database_explicitly_CC_BY_NC_SA_4',
                rights_evidence='https://panlex.org/license/; https://dev.panlex.org/source-registration/',
                quality_flags=['machine_aggregated_lexicon', 'meaning_links_absent_in_mirror'])
            rows.append(rec)
    save_records(ROOT / 'restricted' / 'panlex_gbm.jsonl', rows)
    print(json.dumps({'panlex_gbm_unique_forms': len(rows)}, indent=2))


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
                usage='all_data_experimental_user_approved', corpus_layer='experimental',
                experimental_training_eligible=True, genre='mixed_web_and_scripture',
                modality='text', source_url='https://github.com/rachanagusain/PahariLI',
                rights_status='repository_Apache_2; underlying_blogs_and_translated_text_not_sublicensed',
                quality_flags=['source_lineage_missing', 'component_rights_review_required',
                               'possible_modern_scripture_or_blog_text']))
    save_records(ROOT / 'experimental' / 'paharili_gbm.jsonl', rows)

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
            usage='all_data_experimental_user_approved', corpus_layer='experimental',
            experimental_training_eligible=True, genre='phrase_translation',
            modality='text', source_url='https://huggingface.co/datasets/hikinegi/Garhwali-Dataset',
            rights_status='publicly_downloadable_but_no_license_or_authorship_statement',
            quality_flags=['unlicensed', 'community_upload', 'native_accuracy_unverified'])
        rec['script'] = 'Latn'
        hikinegi_rows.append(rec)
    save_records(ROOT / 'experimental' / 'hikinegi_garhwali.jsonl', hikinegi_rows)

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
                upstream_metrics=metrics, usage='all_data_experimental_user_approved',
                corpus_layer='experimental', experimental_training_eligible=True,
                genre='web_document', modality='text',
                source_url='https://huggingface.co/datasets/openbmb/DCAD-2000',
                rights_status='dataset_LICENSE_link_missing; underlying_web_copyrights_not_cleared',
                quality_flags=['common_crawl', 'component_rights_review_required',
                               'source_url_missing'] + (['upstream_rejected'] if decision == 'remove' else [])))
    save_records(ROOT / 'experimental' / 'dcad_gbm.jsonl', dcad_rows)

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
    folders = [CORPUS, ROOT / 'benchmarks', ROOT / 'restricted', ROOT / 'experimental',
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


def third_wave_extract():
    """Add only exact-novel records from MADLAD's audited Garhwali clean split."""
    raw, info = snapshot('madlad400_gbm', 'gbm_clean_0000.jsonl.gz')
    info = madlad_provenance(info)
    if sha(raw) != info['upstream_partition_sha256']:
        raise ValueError('MADLAD Garhwali clean partition checksum mismatch')
    target = ROOT / 'experimental' / 'madlad400_gbm_clean.jsonl'
    known = existing_text_hashes(exclude=[str(target.relative_to(ROOT))])
    rows, duplicates = madlad_clean_records(raw, info, known)
    if len(rows) + duplicates != 137:
        raise ValueError(f'Expected 137 MADLAD clean documents, found {len(rows) + duplicates}')
    save_records(target, rows)
    print(json.dumps({'madlad_clean_upstream_documents': 137,
                      'exact_duplicates_skipped': duplicates,
                      'novel_documents_added_to_experimental': len(rows)}, indent=2))


def fourth_wave_acquire():
    """Acquire the newest rights-cleared CLDF and Garhwali story sources."""
    jobs = [
        ('sand_garhwali', 'forms.csv',
         'https://raw.githubusercontent.com/numeralbank/sand/v1.0/cldf/forms.csv'),
        ('sand_garhwali', 'parameters.csv',
         'https://raw.githubusercontent.com/numeralbank/sand/v1.0/cldf/parameters.csv'),
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
        ('lsi_cldf_garhwali', 'parameters.csv',
         'https://raw.githubusercontent.com/lexibank/lsi/v1.0/cldf/parameters.csv'),
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
    sand_parameters, sand_parameters_info = snapshot(
        'sand_garhwali', 'parameters.csv'
    )
    sand_rows = sand_garhwali_records(
        sand_raw, sand_info, sand_parameters, sand_parameters_info
    )
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
    lsi_parameters, lsi_parameters_info = snapshot(
        'lsi_cldf_garhwali', 'parameters.csv'
    )
    lsi_rows = lsi_cldf_garhwali_records(
        lsi_raw, lsi_info, lsi_parameters, lsi_parameters_info
    )
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
            'Public-Domain-India', 'https://copyright.gov.in/Copyright_Act_1957/chapter_v.html',
            'H. G. Walton, British Garhwal: A Gazetteer (1910)',
            scan_page=scan_page, corpus_layer='historical_review',
            genre='historical_gazetteer_language_note', modality='text',
            source_url='https://archive.org/details/in.ernet.dli.2015.48008',
            rights_status='public_domain_india_government_work_term_expired',
            rights_scope='India; classification as a Government work is based on the official government gazetteer series and Government Press imprint',
            rights_evidence='India Copyright Act §§2(k), 17(d), 28: https://copyright.gov.in/Copyright_Act_1957/chapter_i.html; https://copyright.gov.in/Copyright_Act_1957/chapter_iv.html; https://copyright.gov.in/Copyright_Act_1957/chapter_v.html; title-page and series bibliographic evidence: https://books.google.com/books/about/British_Garhwal.html?id=Pw71xwEACAAJ; https://ci.nii.ac.jp/ncid/BA22763972?l=ja&linkamp=button-menu. The scanned title page identifies Volume XXXVI of the District Gazetteers of the United Provinces, H. G. Walton, I.C.S., printed at the Government Press, Allahabad, 1910. Under §28 the term would have ended in 1970 if Government was first owner; §17(d) supplies that default for Government works. This is a documented territorial assessment, not a blanket worldwide license.',
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
            'pib_ramman_instruments', index, term, info,
            'LicenseRef-PIB-Copyright-Policy',
            'https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48',
            'Press Information Bureau, Government of India', gloss_en=gloss,
            semantic_domain='instrument', romanization=roman, confidence='high',
            source_url=info['url'],
            rights_evidence='https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48',
            rights_status='PIB_policy_permits_reproduction_of_PIB_material_with_attribution; third_party_material_excluded',
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
                'Public-Domain-US-UK-India',
                'https://copyright.gov.in/documents/international%20copyright%20order.htm',
                f'William Crooke, The Popular Religion and Folk-Lore of Northern India, volume {volume} (1896); Project Gutenberg',
                source_volume=volume, source_unit=chunk['source_unit'],
                source_url=f'https://www.gutenberg.org/ebooks/{43680 + volume}',
                rights_status='public_domain_us_uk_india_term_expired',
                rights_scope='United States, United Kingdom, and India; based on publication, author-death, and country-of-origin term evidence',
                rights_evidence='Bibliographic record: first edition published at Westminster in 1896, https://www.nature.com/articles/055577a0; William Crooke death recorded 25 October 1923, https://www.nature.com/articles/112663b0. Project Gutenberg identifies both editions as public domain in the USA: https://www.gutenberg.org/ebooks/43681; https://www.gutenberg.org/ebooks/43682. UK Copyright, Designs and Patents Act 1988 §12 uses life plus 70 years, so the term ended 31 December 1993: https://www.legislation.gov.uk/ukpga/1988/48/section/12. India International Copyright Order 1999 ¶7 caps the term at the country-of-origin term and identifies the UK as a Berne country: https://copyright.gov.in/documents/international%20copyright%20order.htm. No blanket corpus license is asserted.',
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


def tenth_wave_acquire():
    """Acquire robots-allowed Garhwali-named web goldmine sources."""
    from ingest_web_goldmines import acquire

    acquire()


def tenth_wave_extract():
    """Extract and exact-deduplicate local experimental web-source records."""
    from ingest_web_goldmines import extract

    extract()


# Every collection step callable from the command line.
ACTIONS = (
    'survey', 'meta', 'probes', 'wiktionary', 'acquire', 'extract', 'downloads',
    'restricted', 'uou', 'wayback', 'archive_open', 'archive_extract',
    'more_acquire', 'more_extract', 'historical_more_acquire', 'historical_more_extract',
    'opus_acquire', 'opus_extract', 'indic_asr_acquire', 'indic_asr_range_acquire',
    'indic_asr_extract', 'panlex_acquire', 'panlex_extract', 'third_wave_acquire',
    'third_wave_extract',
    *(action for pair in WAVES.values() for action in pair),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=ACTIONS)
    args = parser.parse_args()
    print('result', globals()[args.action]())


if __name__ == '__main__':
    main()
