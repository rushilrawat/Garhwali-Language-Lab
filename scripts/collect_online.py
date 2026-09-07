"""Auditable public-source collection. No credentials, access bypasses or uploads.

Snapshots are content addressed. The source ledger records successful and failed
requests. Corpus promotion is always a separate, human-reviewed operation.
"""
import argparse
import hashlib
import json
import re
import subprocess
import unicodedata
from collections import Counter
from datetime import datetime, timezone
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


def fetch(source, name, url):
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
        p = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                            '--max-time', '55', '--retry', '1', '--max-filesize', '100000000',
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
                if item['ns'] == 14:
                    categories.append(item['title'])
                elif item['ns'] == 0:
                    titles.add(item['title'])
            if 'continue' not in data:
                break
            params.update(data['continue'])
            page += 1
    rows = []
    for n, title in enumerate(sorted(titles)):
        params = dict(action='query', format='json', titles=title, prop='revisions', rvprop='ids|timestamp|content', rvslots='main')
        payload, info = get_json(source, f'entry-{sha(title.encode())[:16]}.json', api + urlencode(params))
        for p in payload['query']['pages'].values():
            if 'missing' in p:
                continue
            revision = p['revisions'][0]
            raw = revision['slots']['main']['*']
            text = raw if title.startswith('Appendix:') else garhwali_section(raw)
            if not text:
                continue
            rows.append(make_record(source, p['pageid'], text, info, 'CC-BY-SA-4.0', SA,
                f'English Wiktionary contributors; https://en.wiktionary.org/w/index.php?title={quote(title)}&action=history',
                title=title, revision_id=revision['revid'], item_url=f'https://en.wiktionary.org/w/index.php?oldid={revision["revid"]}',
                corpus_layer='extended_sa_raw', genre='lexicon', modality='text', text_format='wikitext'))
        print('wiktionary', n+1, '/', len(titles), flush=True)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['survey', 'meta', 'probes', 'wiktionary', 'acquire', 'extract'])
    args = parser.parse_args()
    print('result', globals()[args.action]())


if __name__ == '__main__':
    main()
