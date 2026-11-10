"""Record construction and persistence shared by online source collectors."""

import csv
import hashlib
import io
import json
import unicodedata
from datetime import datetime, timezone


VERSION = 'online-0.1'


BY = 'https://creativecommons.org/licenses/by/4.0/'


SA = 'https://creativecommons.org/licenses/by-sa/4.0/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


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


def latin_record(source, key, text, info, attribution, **extra):
    record = make_record(source, key, text, info, 'CC-BY-4.0', BY, attribution, **extra)
    record['script'] = 'Latn'
    return record


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
