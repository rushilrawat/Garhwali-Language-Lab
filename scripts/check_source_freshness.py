#!/usr/bin/env python3
"""Check catalogued source URLs for material HTTP metadata changes."""

import argparse
import json
import re
import ssl
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag

import certifi


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'sources/online/deep-search-catalog.md'
OUT = ROOT / 'data/cache/source-freshness.json'
FIELDS = ('status', 'etag', 'last_modified', 'content_length')
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def extract_urls(markdown):
    urls = {
        urldefrag(match).url
        for match in re.findall(r'\]\((https?://[^)]+)\)', markdown)
    }
    return sorted(urls)


def diff_records(previous, current):
    old = {row['url']: row for row in previous}
    changes = []
    for row in current:
        prior = old.get(row['url'])
        if not prior:
            changes.append({'url': row['url'], 'changes': {'source': {'before': None, 'after': 'added'}}})
            continue
        changed = {
            field: {'before': prior.get(field), 'after': row.get(field)}
            for field in FIELDS
            if prior.get(field) != row.get(field)
            and (prior.get(field) is not None or row.get(field) is not None)
        }
        if changed:
            changes.append({'url': row['url'], 'changes': changed})
    return changes


def inspect_url(url, timeout=20):
    headers = {'User-Agent': 'Mozilla/5.0 GarhwaliLanguageLab/0.1 source-audit'}
    request = urllib.request.Request(url, method='HEAD', headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=SSL_CONTEXT) as response:
            headers = response.headers
            return {
                'url': url,
                'status': response.status,
                'etag': headers.get('ETag'),
                'last_modified': headers.get('Last-Modified'),
                'content_length': headers.get('Content-Length'),
                'error': None,
            }
    except urllib.error.HTTPError as error:
        if error.code in (403, 405):
            bounded_get = urllib.request.Request(
                url,
                method='GET',
                headers={**headers, 'Range': 'bytes=0-0'},
            )
            try:
                with urllib.request.urlopen(bounded_get, timeout=timeout, context=SSL_CONTEXT) as response:
                    headers = response.headers
                    return {
                        'url': url,
                        'status': response.status,
                        'etag': headers.get('ETag'),
                        'last_modified': headers.get('Last-Modified'),
                        'content_length': headers.get('Content-Length'),
                        'error': None,
                    }
            except Exception:
                pass
        return {
            'url': url,
            'status': error.code,
            'etag': error.headers.get('ETag'),
            'last_modified': error.headers.get('Last-Modified'),
            'content_length': error.headers.get('Content-Length'),
            'error': str(error),
        }
    except Exception as error:
        return {'url': url, 'status': None, 'etag': None, 'last_modified': None, 'content_length': None, 'error': str(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--timeout', type=int, default=20)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()

    urls = extract_urls(args.catalog.read_text(encoding='utf-8'))
    if args.limit:
        urls = urls[:args.limit]
    records = []
    if args.live:
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = sorted(pool.map(lambda url: inspect_url(url, args.timeout), urls), key=lambda row: row['url'])
    previous = []
    if args.previous and args.previous.exists():
        previous = json.loads(args.previous.read_text(encoding='utf-8')).get('records', [])
    report = {
        'checked_at': datetime.now(timezone.utc).isoformat(),
        'catalog': str(args.catalog),
        'live': args.live,
        'source_urls': len(urls),
        'records': records,
        'changes': diff_records(previous, records) if args.live and previous else [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('live', 'source_urls', 'changes')}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
