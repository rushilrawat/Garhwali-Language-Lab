"""Conservative plain-text rendering for locally preserved MediaWiki snapshots."""

import html
import re


def to_plain_text(source):
    text = source
    text = re.sub(r'<(?:inputbox|gallery)\b[^>]*>.*?</(?:inputbox|gallery)>', ' ', text,
                  flags=re.I | re.S)
    text = re.sub(r'<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>', ' ', text, flags=re.I | re.S)
    text = re.sub(r'\{\|.*?\|\}', ' ', text, flags=re.S)
    text = re.sub(r'\[\[(?:File|Image|Category):[^\]]+\]\]', ' ', text, flags=re.I)
    previous = None
    while text != previous:
        previous = text
        text = re.sub(r'\{\{[^{}]*\}\}', ' ', text)
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'\[\[(?:[^\]|]*\|)?([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[https?://[^\]]+\]', ' ', text)
    text = re.sub(r'(?m)^\s*=+\s*(.*?)\s*=+\s*$', r'\1', text)
    text = re.sub(r'__[A-Z]+__', ' ', text)
    text = text.replace("'''", '').replace("''", '')
    lines = []
    for line in html.unescape(text).splitlines():
        line = re.sub(r'^\s*[*#:;]+\s*', '', line)
        line = re.sub(r'\s+', ' ', line).strip()
        if line and not re.fullmatch(r'[|!{}=\-]+', line):
            lines.append(line)
    return '\n'.join(lines)
