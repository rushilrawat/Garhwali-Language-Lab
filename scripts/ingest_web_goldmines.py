#!/usr/bin/env python3
"""Collect robots-allowed Garhwali web leads into a local experimental layer."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.robotparser import RobotFileParser


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/downloads/web_goldmines"
OUTPUT = ROOT / "experimental/garhwali_web_goldmines.jsonl"
REPORT = ROOT / "data/extracted/web_goldmines/report.json"
USER_AGENT = "GarhwaliLanguageLab/0.2 research corpus"
PAGE_SIZE = 20
REQUEST_DELAY_SECONDS = 1.25
VERSION = "web-goldmines-0.1"
BLOG = "https://e-magazineofuttarakhand.blogspot.com"
BLOG_FEED = BLOG + "/feeds/posts/default"
KHABAR_STORIES = (
    "https://uttarakhandkhabarsaar.in/jani-mayedi-tani-jayedi-a-garhwali-short-story/",
    "https://uttarakhandkhabarsaar.in/khuded-bhajed-a-garhwali-short-story/",
)
LANGUAGE_RELEVANCE = re.compile(
    r"garhwali|garh wali|gharwali|gadhwali|garwali|gadwali|gbm|"
    r"गढ़वाली|गढवाली|गढ़वळी|गढ़वाळी",
    re.IGNORECASE,
)
REGIONAL_LANGUAGE_CONTEXT = re.compile(
    r"garhwal|गढ़वाल|गढवाल", re.IGNORECASE
)
LANGUAGE_CONTEXT_TERMS = re.compile(
    r"\b(?:language|dialect|stories?|tales?|poems?|folk|songs?|literature|idioms?|proverbs?)\b|"
    r"लोक|गीत|कथा|कहानी|कविता|नाटक|साहित्य|भाषा|बोली|मुहावरा|कहावत",
    re.IGNORECASE,
)
BLOCK_TAGS = {"script", "style", "noscript", "svg"}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def text_hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


class VisibleTextParser(HTMLParser):
    """Extract visible text, optionally restricting it to an article container."""

    def __init__(self, target_class: str | None = None, target_tag: str | None = None):
        super().__init__(convert_charrefs=True)
        self.target_class = target_class
        self.target_tag = target_tag
        self.depth = 0
        self.target_depth: int | None = None
        self.hidden_depth = 0
        self.values: list[str] = []
        self.found_target = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        matches = ((self.target_class and self.target_class in classes) or
                   (self.target_tag and tag == self.target_tag))
        if self.target_depth is None and matches:
            self.target_depth = self.depth
            self.found_target = True
        if tag in BLOCK_TAGS and (self.target_depth is None or self.depth >= self.target_depth):
            self.hidden_depth += 1
        self.depth += 1

    def handle_endtag(self, tag):
        self.depth = max(0, self.depth - 1)
        if tag in BLOCK_TAGS and self.hidden_depth:
            self.hidden_depth -= 1
        if self.target_depth is not None and self.depth == self.target_depth:
            self.target_depth = None

    def handle_data(self, data):
        inside = self.target_class is None and self.target_tag is None or self.target_depth is not None
        if inside and not self.hidden_depth:
            value = data.strip()
            if value:
                self.values.append(value)

    def text(self) -> str:
        return normalize_text(" ".join(self.values))


class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.values: list[str] = []

    def handle_starttag(self, tag, _attrs):
        if tag == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title and data.strip():
            self.values.append(data.strip())


def html_to_text(markup: str, target_class: str | None = None,
                 target_tag: str | None = None) -> tuple[str, bool]:
    parser = VisibleTextParser(target_class=target_class, target_tag=target_tag)
    parser.feed(markup)
    return parser.text(), parser.found_target


def robots_allows(robots_text: str, url: str, user_agent: str = USER_AGENT) -> bool:
    parser = RobotFileParser()
    parser.set_url(f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt")
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(user_agent, url)


def is_garhwali_candidate(title: str, url: str) -> bool:
    value = f"{title} {url}"
    return bool(LANGUAGE_RELEVANCE.search(value) or
                (REGIONAL_LANGUAGE_CONTEXT.search(value) and LANGUAGE_CONTEXT_TERMS.search(value)))


def fetch_bytes(url: str) -> bytes:
    try:
        result = subprocess.run(
            ["curl", "--proto", "=https", "--proto-redir", "=https", "--fail",
             "--location", "--silent", "--show-error", "--max-time", "90",
             "--retry", "1", "--retry-delay", "1", "--max-filesize", "20000000",
             "--user-agent", USER_AGENT, url],
            check=True, capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(detail or f"curl failed with status {error.returncode}: {url}") from error
    return result.stdout


def _pointer(source: str, name: str) -> Path:
    path = RAW / source / f"{name}.metadata.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_snapshot(source: str, name: str, url: str, data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    folder = RAW / source
    folder.mkdir(parents=True, exist_ok=True)
    suffix = Path(urlparse(url).path).suffix or ".json"
    path = folder / f"{name}-{digest[:16]}{suffix}"
    if not path.exists():
        path.write_bytes(data)
    info = {
        "url": url,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
        "raw_path": str(path.relative_to(ROOT)),
        "bytes": len(data),
    }
    _pointer(source, name).write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return info


def cached_snapshot(source: str, name: str, url: str) -> tuple[bytes, dict] | None:
    pointer = _pointer(source, name)
    if not pointer.exists():
        return None
    info = json.loads(pointer.read_text(encoding="utf-8"))
    path = ROOT / info["raw_path"]
    if info.get("url") != url or not path.is_file():
        return None
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != info.get("sha256"):
        raise ValueError(f"Cached web-source hash mismatch: {pointer}")
    return data, info


def fetch_snapshot(source: str, name: str, url: str, fetcher=fetch_bytes) -> tuple[bytes, dict]:
    data = fetcher(url)
    return data, save_snapshot(source, name, url, data)


def _feed_url(start: int, count: int = PAGE_SIZE) -> str:
    return f"{BLOG_FEED}?alt=json&start-index={start}&max-results={count}"


def _feed_name(start: int, count: int) -> str:
    return f"feed-{start:05d}" if count == PAGE_SIZE else f"feed-{start:05d}-n{count:02d}"


def _feed_count(payload: dict) -> int:
    value = payload.get("feed", {}).get("openSearch$totalResults", {}).get("$t", 0)
    return int(value)


def _read_acquisition_state() -> dict:
    path = RAW / "blogger_state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def _write_acquisition_state(state: dict) -> None:
    path = RAW / "blogger_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _acquire_feed_span(start: int, count: int, *, blog_rules: str, changed: bool,
                       fetcher, sleeper, preloaded=None) -> list[tuple[int, int, bytes, dict]]:
    name = _feed_name(start, count)
    url = _feed_url(start, count)
    if not robots_allows(blog_rules, url):
        raise RuntimeError(f"Blogger robots.txt disallows feed: {url}")
    if preloaded is not None:
        data, info = preloaded
    else:
        cached = None if changed else cached_snapshot("blogger", name, url)
        if cached:
            data, info = cached
        else:
            sleeper(REQUEST_DELAY_SECONDS)
            data, info = fetch_snapshot("blogger", name, url, fetcher)
    payload = json.loads(data)
    entries = payload.get("feed", {}).get("entry", [])
    if len(entries) == count:
        return [(start, count, data, info)]
    if len(entries) > count or count <= 1:
        raise RuntimeError(
            f"Blogger feed page {start} returned {len(entries)} entries for a span of {count}"
        )

    # Oversized post bodies can truncate Blogger's larger responses. Bisect only
    # the incomplete range, retaining completed snapshots for future resumes.
    left_count = count // 2
    right_count = count - left_count
    return (
        _acquire_feed_span(start, left_count, blog_rules=blog_rules, changed=changed,
                           fetcher=fetcher, sleeper=sleeper) +
        _acquire_feed_span(start + left_count, right_count, blog_rules=blog_rules,
                           changed=changed, fetcher=fetcher, sleeper=sleeper)
    )


def acquire(fetcher=fetch_bytes, sleeper=time.sleep) -> dict:
    """Snapshot all Garhwali-named Blogger posts plus two explicit short stories."""
    blog_robots_url = BLOG + "/robots.txt"
    khabar_robots_url = "https://uttarakhandkhabarsaar.in/robots.txt"
    blog_robots, _ = fetch_snapshot("blogger", "robots", blog_robots_url, fetcher)
    khabar_robots, _ = fetch_snapshot("khabarsaar", "robots", khabar_robots_url, fetcher)
    blog_rules = blog_robots.decode("utf-8", "replace")
    khabar_rules = khabar_robots.decode("utf-8", "replace")

    first_url = _feed_url(1, PAGE_SIZE)
    if not robots_allows(blog_rules, first_url):
        raise RuntimeError(f"Blogger robots.txt disallows feed: {first_url}")
    first_data, first_info = fetch_snapshot("blogger", "feed-00001", first_url, fetcher)
    first_payload = json.loads(first_data)
    total = _feed_count(first_payload)
    if total <= 0:
        raise RuntimeError("Blogger feed returned no posts")
    starts = list(range(1, total + 1, PAGE_SIZE))
    state = _read_acquisition_state()
    changed = (state.get("first_sha256") != first_info["sha256"] or
               state.get("total_posts") != total)
    _write_acquisition_state({
        "first_sha256": first_info["sha256"], "total_posts": total,
        "incomplete_refresh": bool(changed),
    })

    pages = []
    for start in starts:
        count = min(PAGE_SIZE, total - start + 1)
        preloaded = (first_data, first_info) if start == 1 else None
        pages.extend(_acquire_feed_span(
            start, count, blog_rules=blog_rules, changed=changed,
            fetcher=fetcher, sleeper=sleeper, preloaded=preloaded,
        ))
        if (start - 1) % (PAGE_SIZE * 50) == 0:
            print(f"Blogger feed snapshots: {start}/{total}", flush=True)

    for index, url in enumerate(KHABAR_STORIES, 1):
        if not robots_allows(khabar_rules, url):
            raise RuntimeError(f"Khabar Saar robots.txt disallows page: {url}")
        sleeper(REQUEST_DELAY_SECONDS)
        fetch_snapshot("khabarsaar", f"story-{index}", url, fetcher)

    verify_feed_complete([json.loads(data) for _start, _count, data, _info in pages], total)

    index_data = {
        "source": "e-Magazine of Uttarakhand public Blogger feed",
        "feed_total_posts": total,
        "feed_pages": [
            {"start_index": start, "max_results": count, "url": _feed_url(start, count),
             "sha256": info["sha256"], "raw_path": info["raw_path"], "bytes": info["bytes"]}
            for start, count, _data, info in pages
        ],
        "khabarsaar_story_urls": list(KHABAR_STORIES),
        "robots_checked": [blog_robots_url, khabar_robots_url],
        "rights_note": "Rights not stated as an open license; contents stay local experimental.",
    }
    index_path = RAW / "acquisition-index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_acquisition_state({
        "first_sha256": first_info["sha256"], "total_posts": total,
        "incomplete_refresh": False,
    })
    report = {"blogger_posts": total, "feed_snapshots": len(pages),
              "khabarsaar_story_pages": len(KHABAR_STORIES)}
    print(json.dumps(report, indent=2), flush=True)
    return report


def _entry_value(entry: dict, key: str, default="") -> str:
    value = entry.get(key, {})
    return str(value.get("$t", default)) if isinstance(value, dict) else default


def _alternate_link(entry: dict) -> str:
    for link in entry.get("link", []):
        if link.get("rel") == "alternate" and link.get("href"):
            return link["href"]
    return ""


def _author(entry: dict) -> str:
    authors = entry.get("author", [])
    return "; ".join(a.get("name", {}).get("$t", "") for a in authors if a.get("name", {}).get("$t"))


def verify_feed_complete(payloads: list[dict], expected_total: int) -> None:
    entry_ids = [
        _entry_value(entry, "id")
        for payload in payloads
        for entry in payload.get("feed", {}).get("entry", [])
    ]
    unique_ids = set(entry_ids)
    if len(entry_ids) != expected_total or len(unique_ids) != expected_total:
        raise RuntimeError(
            f"Blogger pagination incomplete or overlapping: {len(entry_ids)} entries, "
            f"{len(unique_ids)} unique IDs, expected {expected_total}"
        )


def _record(source: str, url: str, title: str, author: str, text: str,
            retrieved_at: str, provenance: dict, language_scope: str) -> dict:
    normalized = normalize_text(text)
    digest = text_hash(normalized)
    devanagari = sum("\u0900" <= char <= "\u097f" for char in normalized)
    latin = sum("LATIN" in unicodedata.name(char, "") for char in normalized)
    script = "Mixed-Deva-Latn" if devanagari and latin else "Deva" if devanagari else "Latn" if latin else "Other"
    return {
        "record_id": f"{source}:{hashlib.sha256(url.encode()).hexdigest()[:20]}",
        "source_id": source,
        "source_url": url,
        "title": title,
        "author": author or source,
        "text_original": text,
        "text_normalized": normalized,
        "text_sha256": digest,
        "language_candidates": ["gbm"],
        "language_scope": language_scope,
        "script": script,
        "genre": "folk_literature" if re.search(
            r"\b(?:stories?|tales?|lokgeet)\b|लोकगीत|कथा|कहानी", title, re.I
        )
                 else "regional_cultural_text",
        "modality": "text",
        "license_id": "LicenseRef-Rights-Unassessed",
        "rights_status": "rights_unassessed",
        "rights_evidence": url,
        "attribution": author or source,
        "retrieved_at": retrieved_at,
        "provenance": provenance,
        "extractor_version": VERSION,
        "quality_status": "unreviewed",
        "corpus_layer": "experimental",
        "training_eligible": False,
        "experimental_training_eligible": True,
        "usage": "all_data_experimental_user_approved",
        "native_reviewed": False,
        "quality_flags": [
            "garhwali_language_candidate_not_confirmed",
            "rights_unassessed_local_only",
            "web_text_unreviewed",
            "source_attribution_preserved",
        ],
    }


def records_from_blogger_feed(payload: dict, feed_url: str, feed_sha256: str,
                              raw_path: str = "") -> list[dict]:
    records = []
    for entry in payload.get("feed", {}).get("entry", []):
        title = normalize_text(_entry_value(entry, "title"))
        url = _alternate_link(entry)
        if not url or not is_garhwali_candidate(title, url):
            continue
        markup = _entry_value(entry, "content") or _entry_value(entry, "summary")
        text, _found = html_to_text(markup)
        if len(text) < 40:
            continue
        author = _author(entry) or "e-Magazine of Uttarakhand / credited contributor"
        records.append(_record(
            "emagazineofuttarakhand", url, title, author, text,
            _entry_value(entry, "updated") or _entry_value(entry, "published"),
            {"feed_url": feed_url, "feed_sha256": feed_sha256, "feed_snapshot": raw_path,
             "source_entry_id": _entry_value(entry, "id")},
            "Source title or URL is a regional-language relevance candidate; article language is unverified.",
        ))
    return records


def record_from_khabarsaar_page(url: str, data: bytes, info: dict) -> dict | None:
    markup = data.decode("utf-8", "replace")
    text, found = html_to_text(markup, target_class="entry-content")
    if not found:
        text, found = html_to_text(markup, target_tag="article")
    if not found or len(text) < 40:
        return None
    title_parser = TitleParser()
    title_parser.feed(markup)
    title = normalize_text(" ".join(title_parser.values)) or urlparse(url).path.rsplit("/", 2)[-2]
    source = "uttarakhandkhabarsaar"
    return _record(
        source, url, title, "Uttarakhand Khabar Saar; article-level byline retained in source page",
        text, info.get("retrieved_at", ""),
        {"raw_path": info["raw_path"], "source_snapshot_sha256": info["sha256"],
         "bytes": info["bytes"]},
        "Article URL labels a regional-language short story; text language remains unreviewed.",
    )


def deduplicate_records(records: list[dict], existing_hashes: set[str]) -> tuple[list[dict], list[str]]:
    seen = set(existing_hashes)
    unique = []
    duplicate_hashes = []
    duplicate_seen = set()
    for row in records:
        digest = text_hash(row["text_normalized"])
        row["text_sha256"] = digest
        if digest in seen:
            if digest not in duplicate_seen:
                duplicate_hashes.append(digest)
                duplicate_seen.add(digest)
            continue
        seen.add(digest)
        unique.append(row)
    return unique, duplicate_hashes


def _existing_hashes() -> set[str]:
    hashes = set()
    folders = ("corpus", "restricted", "experimental", "extracted", "data/extracted")
    for folder_name in folders:
        folder = ROOT / folder_name
        if not folder.exists():
            continue
        for path in folder.rglob("*.jsonl"):
            if path.resolve() == OUTPUT.resolve():
                continue
            with path.open(encoding="utf-8", errors="replace") as source:
                for line in source:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    text = next((row.get(key) for key in
                                 ("text_normalized", "text", "source_text", "transcript")
                                 if isinstance(row.get(key), str) and row[key].strip()), "")
                    if text:
                        hashes.add(text_hash(text))
    return hashes


def extract() -> dict:
    index_path = RAW / "acquisition-index.json"
    if not index_path.exists():
        raise FileNotFoundError("Run web goldmine acquisition before extraction")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    blog_candidates = []
    pages_seen = 0
    for page in index["feed_pages"]:
        path = ROOT / page["raw_path"]
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != page["sha256"]:
            raise ValueError(f"Feed snapshot hash mismatch: {path}")
        payload = json.loads(data)
        pages_seen += len(payload.get("feed", {}).get("entry", []))
        blog_candidates.extend(records_from_blogger_feed(
            payload, page["url"], digest, page["raw_path"]
        ))

    khabar_candidates = []
    for index_number, url in enumerate(KHABAR_STORIES, 1):
        cached = cached_snapshot("khabarsaar", f"story-{index_number}", url)
        if not cached:
            raise FileNotFoundError(f"Missing Khabar Saar snapshot: {url}")
        data, info = cached
        row = record_from_khabarsaar_page(url, data, info)
        if row:
            khabar_candidates.append(row)

    candidates = blog_candidates + khabar_candidates
    known = _existing_hashes()
    unique, duplicate_hashes = deduplicate_records(candidates, known)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
    temp.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                                    for row in unique), encoding="utf-8")
    temp.replace(OUTPUT)
    report = {
        "pipeline": VERSION,
        "source_pages_scanned": pages_seen,
        "garhwali_language_or_folk_named_blogger_candidates": len(blog_candidates),
        "khabarsaar_pages_scanned": len(KHABAR_STORIES),
        "khabarsaar_candidate_records": len(khabar_candidates),
        "candidate_records_before_dedup": len(candidates),
        "exact_duplicate_text_groups_against_existing_or_within_wave": len(duplicate_hashes),
        "exact_duplicate_records_against_existing_or_within_wave": len(candidates) - len(unique),
        "exact_new_unique_records": len(unique),
        "exact_new_unique_characters": sum(len(row["text_normalized"]) for row in unique),
        "source_record_counts": dict(sorted(
            __import__("collections").Counter(row["source_id"] for row in unique).items()
        )),
        "rights_status": "rights_unassessed_local_experimental_only",
        "public_huggingface_rows_added": 0,
        "output": str(OUTPUT.relative_to(ROOT)),
        "duplicate_text_sha256": duplicate_hashes,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items()
                      if key != "duplicate_text_sha256"}, ensure_ascii=False, indent=2), flush=True)
    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("acquire", "extract", "run"), default="run", nargs="?")
    args = parser.parse_args()
    if args.action in {"acquire", "run"}:
        acquire()
    if args.action in {"extract", "run"}:
        extract()


if __name__ == "__main__":
    main()
