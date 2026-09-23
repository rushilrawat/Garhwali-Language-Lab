#!/usr/bin/env python3
"""Archive and extract attributed Garhwali learning-page text."""
import hashlib
import json
import re
import unicodedata
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT/'data/downloads/web_learning'
OUT = ROOT/'experimental/web_learning_garhwali.jsonl'
URLS = {
 'euttaranchal_1':'https://www.euttaranchal.com/culture/learn-garhwali.php',
 'euttaranchal_2':'https://www.euttaranchal.com/culture/learn-garhwali-lesson-2.php',
 'euttaranchal_3':'https://www.euttaranchal.com/culture/learn-garhwali-lesson-3.php',
 'languageshome':'https://www.languageshome.com/English-Garhwali.htm',
 'omniglot':'https://omniglot.com/writing/garhwali.htm',
}


class TextParser(HTMLParser):
    def __init__(self): super().__init__(); self.nodes=[]; self.hidden=0
    def handle_starttag(self, tag, attrs):
        if tag in {'script','style','noscript'}: self.hidden+=1
    def handle_endtag(self, tag):
        if tag in {'script','style','noscript'} and self.hidden: self.hidden-=1
    def handle_data(self, data):
        value=re.sub(r'\s+',' ',data).strip()
        if value and not self.hidden: self.nodes.append(value)


def normalize(text): return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text)).strip()


def labeled_pairs(text):
    text = re.split(r'\s+(?:Continue to Lesson \d+|Posted by:)\s*', text, maxsplit=1, flags=re.I)[0]
    pattern=r'English\s*:\s*(.*?)\s+Garhwali\s*:\s*(.*?)(?=\s+English\s*:|$)'
    return [(normalize(a),normalize(b)) for a,b in re.findall(pattern,text,flags=re.I|re.S)]


def pairwise(values): return list(zip(values[0::2],values[1::2]))


def fetch(url):
    request=urllib.request.Request(url,headers={'User-Agent':'GarhwaliLanguageLab/0.1 research corpus'})
    with urllib.request.urlopen(request,timeout=60) as response: return response.read()


def nodes(data):
    parser=TextParser(); parser.feed(data.decode('utf-8',errors='replace')); return parser.nodes


def collect_records(fetcher=None):
    fetcher = fetch if fetcher is None else fetcher
    RAW.mkdir(parents=True,exist_ok=True); records=[]; source_counts={}; failures=[]
    for source,url in URLS.items():
        try: data=fetcher(url)
        except Exception as error:
            failures.append({'source': source, 'url': url, 'error': str(error)})
            continue
        digest=hashlib.sha256(data).hexdigest(); raw=RAW/f'{source}-{digest[:12]}.html'; raw.write_bytes(data)
        values=nodes(data); pairs=[]
        if source.startswith('euttaranchal'):
            pairs=labeled_pairs(' '.join(values))
        elif source=='languageshome':
            start=next((i for i,v in enumerate(values) if v.lower()=='english to garhwali'),None)
            end=next((i for i,v in enumerate(values[start+1:],start+1) if v=='HOME'),len(values)) if start is not None else 0
            body=[v for v in values[start+1:end] if not v.lower().startswith('listen audio')] if start is not None else []
            pairs=pairwise(body)
        else:
            start=next((i for i,v in enumerate(values) if v=='Sample text'),None)
            end=next((i for i,v in enumerate(values[start+1:],start+1) if v=='IPA transcription'),len(values)) if start is not None else 0
            pairs=[(None,v) for v in values[start+1:end] if re.search(r'[\u0900-\u097f]',v)] if start is not None else []
        for index,(english,garhwali) in enumerate(pairs):
            text=normalize(garhwali)
            if not text: continue
            records.append({'record_id':f'{source}:{index}','source_id':source,'source_url':url,
                'text_original':text,'text_normalized':text,'parallel_english':english,
                'iso_639_3':'gbm','script':'Deva' if re.search(r'[\u0900-\u097f]',text) else 'Latn',
                'license_id':'not_stated','rights_status':'public_webpage_no_open_license_stated',
                'attribution':'Page author/publisher named at source URL','corpus_layer':'experimental',
                'training_eligible':True,'usage':'all_data_experimental_user_approved',
                'quality_flags':['native_accuracy_unverified','web_source'],
                'provenance':{'raw_path':str(raw.relative_to(ROOT)),'sha256':digest}})
        source_counts[source]=len(pairs)
    missing = sorted(set(URLS) - set(source_counts))
    empty = sorted(source for source, count in source_counts.items() if count == 0)
    if failures or missing or empty or not records:
        raise RuntimeError(
            f'web learning ingestion incomplete: failures={failures}, '
            f'missing={missing}, empty={empty}, records={len(records)}'
        )
    return records, source_counts


def main():
    records, source_counts = collect_records()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(f'{OUT.suffix}.tmp')
    temporary.write_text(
        ''.join(json.dumps(r,ensure_ascii=False,sort_keys=True)+'\n' for r in records),
        encoding='utf-8',
    )
    temporary.replace(OUT)
    report={'records':len(records),'source_counts':source_counts,'output':str(OUT.relative_to(ROOT))}
    (RAW/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
