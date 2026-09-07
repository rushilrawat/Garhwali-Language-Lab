"""Download small open Garhwali sources; reruns reuse immutable raw snapshots."""
import argparse
import bz2
import csv
import hashlib
import io
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'sources' / 'web'
OUT = ROOT / 'corpus'
BY = 'https://creativecommons.org/licenses/by/4.0/'
SA = 'https://creativecommons.org/licenses/by-sa/4.0/'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def fetch(source, name, url):
    folder = RAW / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    meta = folder / (name + '.metadata.json')
    if path.exists() and meta.exists():
        content = path.read_bytes()
        info = json.loads(meta.read_text())
        assert digest(content) == info['sha256'], f'Raw checksum mismatch: {path}'
        return content, info
    result = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                             '--max-time', '60', '--retry', '2', '--user-agent',
                             'GarhwaliCorpus/0.1 (language research)', url],
                            check=True, capture_output=True)
    content = result.stdout
    info = {'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'sha256': digest(content), 'raw_path': str(path.relative_to(ROOT))}
    path.write_bytes(content)
    meta.write_text(json.dumps(info, indent=2))
    return content, info

def record(source, key, text, license_id, license_url, attribution, info, **extra):
    normalized = unicodedata.normalize('NFC', text).strip()
    return dict(record_id=f'{source}:{key}', source_id=source, text_original=text,
                text_normalized=normalized, iso_639_3='gbm', license_id=license_id,
                license_url=license_url, attribution=attribution,
                quality_status='unreviewed', native_reviewed=False,
                text_sha256=digest(normalized.encode()), provenance=info, **extra)

def asjp():
    data, info = fetch('asjp', 'GARHWALI.txt', 'https://asjp.clld.org/languages/GARHWALI.txt')
    evidence, _ = fetch('asjp', 'license-page.html', 'https://asjp.clld.org/languages/GARHWALI')
    assert BY.encode() in evidence, 'ASJP license evidence missing'
    rows = []
    for line in data.decode().splitlines():
        match = re.match(r'^(\d+)\s+([^\t]+)\t(.+?)\s*//', line)
        if match:
            concept, meaning, form = match.groups()
            rows.append(record('asjp', concept, form, 'CC-BY-4.0', BY,
                'ASJP Database; Garhwali compiled by Viktoria Smirnova, source Kogan 2017; database editors Wichmann et al.',
                info, concept_id=concept, english_gloss=meaning, script='ASJPcode',
                genre='lexicon', corpus_layer='core_open'))
    assert rows, 'ASJP parser produced no records'
    return rows

def tatoeba():
    url = 'https://downloads.tatoeba.org/exports/per_language/gbm/gbm_sentences_detailed.tsv.bz2'
    local = Path('/private/tmp/gbm_sentences_detailed.tsv')
    if local.exists():
        data = local.read_bytes()
        info = {'url': url, 'retrieved_at': datetime.fromtimestamp(local.stat().st_mtime, timezone.utc).isoformat(),
                'sha256': digest(data), 'raw_path': str(local)}
        raw_path = RAW / 'tatoeba' / 'gbm_sentences_detailed.tsv'
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(data)
        info['raw_path'] = str(raw_path.relative_to(ROOT))
        (raw_path.with_name(raw_path.name + '.metadata.json')).write_text(json.dumps(info, indent=2))
    else:
        compressed, info = fetch('tatoeba', 'gbm_sentences_detailed.tsv.bz2', url)
        data = bz2.decompress(compressed)
    rows = []
    for fields in csv.reader(io.StringIO(data.decode()), delimiter='\t'):
        assert len(fields) >= 4 and fields[1] == 'gbm', 'Unexpected Tatoeba schema'
        key, _, text, author = fields[:4]
        rows.append(record('tatoeba', key, text, 'CC-BY-2.0-FR',
            'https://creativecommons.org/licenses/by/2.0/fr/',
            f'Tatoeba sentence {key}; contributor {author}; see sentence history for attribution', info,
            item_url=f'https://tatoeba.org/en/sentences/show/{key}', contributor=author,
            source_fields=fields, script='Deva', genre='sentence', corpus_layer='review_queue'))
    assert rows, 'Tatoeba parser produced no records'
    return rows

def wiki():
    api = 'https://incubator.wikimedia.org/w/api.php?'
    params = dict(action='query', format='json', generator='allpages', gapnamespace=0,
                  gapprefix='Wp/gbm/', gaplimit=50, prop='revisions', rvprop='ids|timestamp|content', rvslots='main')
    rows, page = [], 0
    while True:
        raw, info = fetch('wikimedia', f'pages-{page}.json', api + urlencode(params))
        payload = json.loads(raw)
        assert 'error' not in payload, payload.get('error')
        for item in payload.get('query', {}).get('pages', {}).values():
            revision = item['revisions'][0]
            text = revision['slots']['main']['*']
            if not text.strip() or re.match(r'^\s*#redirect', text, re.I):
                continue
            rows.append(record('wikimedia', item['pageid'], text, 'CC-BY-SA-4.0', SA,
                f'Wikimedia Incubator contributors to {item["title"]}; attribution history at https://incubator.wikimedia.org/w/index.php?title={item["title"]}&action=history',
                info, title=item['title'], revision_id=revision['revid'],
                item_url=f'https://incubator.wikimedia.org/w/index.php?oldid={revision["revid"]}',
                script='Deva', genre='encyclopedia', text_format='wikitext',
                corpus_layer='extended_sa_raw'))
        if 'continue' not in payload:
            break
        params.update(payload['continue'])
        page += 1
    assert rows, 'Wikimedia parser produced no records'
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sources', nargs='+', choices=['asjp', 'tatoeba', 'wikimedia'],
                        default=['asjp', 'tatoeba', 'wikimedia'])
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    failures = {}
    for source in args.sources:
        try:
            rows = {'asjp': asjp, 'tatoeba': tatoeba, 'wikimedia': wiki}[source]()
            path = OUT / f'{source}.jsonl'
            temp = path.with_suffix('.tmp')
            temp.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
            temp.replace(path)
        except Exception as exc:
            failures[source] = str(exc)
    records = []
    for path in sorted(OUT.glob('*.jsonl')):
        records.extend(json.loads(line) for line in path.read_text().splitlines())
    ids = [r['record_id'] for r in records]
    assert len(ids) == len(set(ids)), 'Duplicate record IDs'
    for r in records:
        assert r['license_url'] and r['attribution'] and r['text_original']
    counts = {s: sum(r['source_id'] == s for r in records) for s in ['asjp', 'tatoeba', 'wikimedia']}
    report = dict(records=len(records), source_counts=counts,
                  unique_normalized_texts=len({r['text_sha256'] for r in records}),
                  native_reviewed=0, failures=failures)
    (OUT / 'ingestion-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return bool(failures)

if __name__ == '__main__':
    raise SystemExit(main())
