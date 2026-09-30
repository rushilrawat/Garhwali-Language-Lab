#!/usr/bin/env python3
"""Ingest the CC BY 4.0 Garhwali word forms exposed by Jambu."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://neojambu.herokuapp.com/languages/Garh"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"
RAW_DIR = Path("data/downloads/jambu_garhwali")
PAGES_DIR = RAW_DIR / "pages"
SNAPSHOT_MANIFEST = RAW_DIR / "web-snapshot-manifest.json"
OUTPUT = Path("corpus/jambu_garhwali.jsonl")
OUTPUT_MANIFEST = Path("corpus/jambu_garhwali_manifest.json")
PAGE_COUNT = 16
PAGE_SIZE = 50
REQUEST_DELAY_SECONDS = 1.25
USER_AGENT = "GarhwaliLanguageLab/2.0 (research corpus)"


def sha256(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


class ReflexTableParser(HTMLParser):
    """Extract only data rows from Jambu's Garhwali reflex table."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_results = False
        self.row: list[dict] | None = None
        self.cell: dict | None = None
        self.link: dict | None = None
        self.rows: list[list[dict]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "tbody" and "results" in classes:
            self.in_results = True
        if self.in_results and tag == "tr" and "lang-row" in classes:
            self.row = []
            self.rows.append(self.row)
        if self.row is not None and tag == "td":
            self.cell = {"text": [], "links": []}
            self.row.append(self.cell)
        if self.cell is not None and tag == "a":
            self.link = {"href": attributes.get("href"), "text": []}
            self.cell["links"].append(self.link)

    def handle_data(self, data: str) -> None:
        if self.cell is not None and data.strip():
            self.cell["text"].append(data.strip())
        if self.link is not None and data.strip():
            self.link["text"].append(data.strip())

    def handle_endtag(self, tag: str) -> None:
        if tag == "a":
            self.link = None
        elif tag == "td":
            self.cell = None
        elif tag == "tr":
            self.row = None
        elif tag == "tbody":
            self.in_results = False

    def parsed_rows(self) -> list[list[dict]]:
        return [
            [
                {
                    "text": " ".join(cell["text"]).strip(),
                    "links": [
                        {"href": link["href"], "text": " ".join(link["text"]).strip()}
                        for link in cell["links"]
                    ],
                }
                for cell in row
            ]
            for row in self.rows
            if row
        ]


def parse_page(html: str, page: int) -> tuple[dict, list[list[dict]]]:
    match = re.search(
        r"Showing\s+(\d+)&mdash;(\d+)\s+of\s+(\d+)\s+reflexes", html
    )
    if not match:
        raise ValueError(f"Jambu page {page} is missing its advertised row range")
    first, last, total = map(int, match.groups())
    parser = ReflexTableParser()
    parser.feed(html)
    rows = parser.parsed_rows()
    expected = last - first + 1
    if len(rows) != expected:
        raise ValueError(
            f"Jambu page {page} advertises {expected} rows but contains {len(rows)}"
        )
    if first != (page - 1) * PAGE_SIZE + 1:
        raise ValueError(f"Jambu page {page} starts at unexpected row {first}")
    return {"page": page, "first": first, "last": last, "total": total}, rows


def _page_url(page: int) -> str:
    return SOURCE_URL if page == 1 else f"{SOURCE_URL}?page={page}"


def _download_page(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Jambu returned HTTP {response.status} for {url}")
            return response.read()
    except URLError as error:
        raise RuntimeError(f"Unable to fetch public Jambu page {url}: {error}") from error


def acquire_snapshot(
    root: Path = ROOT,
    refresh: bool = False,
    offline: bool = False,
    fetcher=_download_page,
    sleeper=time.sleep,
) -> tuple[list[list[dict]], dict]:
    raw_dir = root / RAW_DIR
    pages_dir = root / PAGES_DIR
    manifest_path = root / SNAPSHOT_MANIFEST
    pages_dir.mkdir(parents=True, exist_ok=True)
    old_manifest = {}
    if manifest_path.exists():
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest = {
        "source": "Jambu Garhwali [Garh] reflex listing",
        "url": SOURCE_URL,
        "license_id": "CC-BY-4.0",
        "license_url": LICENSE_URL,
        "rights_evidence_url": SOURCE_URL,
        "retrieved_at": old_manifest.get("retrieved_at")
        or datetime.now(timezone.utc).isoformat(),
        "pages": [],
        "advertised_total": None,
    }
    all_rows: list[list[dict]] = []
    for page in range(1, PAGE_COUNT + 1):
        path = pages_dir / f"page-{page:02d}.html"
        cached_metadata = next(
            (item for item in old_manifest.get("pages", []) if item.get("page") == page),
            None,
        )
        if path.is_file() and cached_metadata and not refresh:
            data = path.read_bytes()
            if sha256(data) != cached_metadata.get("sha256"):
                raise ValueError(f"Jambu source snapshot checksum mismatch: {path}")
        elif offline:
            raise FileNotFoundError(f"Offline Jambu snapshot is missing page {page}")
        else:
            if page > 1:
                sleeper(REQUEST_DELAY_SECONDS)
            data = fetcher(_page_url(page))
            path.write_bytes(data)

        html = data.decode("utf-8", "replace")
        page_info, rows = parse_page(html, page)
        if manifest["advertised_total"] not in (None, page_info["total"]):
            raise ValueError("Jambu page totals changed during one ingestion run")
        manifest["advertised_total"] = page_info["total"]
        manifest["pages"].append(
            {
                **page_info,
                "url": _page_url(page),
                "bytes": len(data),
                "sha256": sha256(data),
                "raw_path": str(path.relative_to(root)),
            }
        )
        all_rows.extend(rows)

    upstream_ids = [
        _upstream_id(row) for row in all_rows
    ]
    if None in upstream_ids or len(set(upstream_ids)) != len(upstream_ids):
        raise ValueError("Jambu Garhwali table has duplicate or missing record IDs")
    if len(all_rows) != manifest["advertised_total"]:
        raise ValueError(
            f"Jambu advertised {manifest['advertised_total']} rows but yielded {len(all_rows)}"
        )
    manifest["parsed_rows"] = len(all_rows)
    return all_rows, manifest


def _upstream_id(row: list[dict]) -> str | None:
    if len(row) < 6:
        return None
    href = next(
        (link["href"] for link in row[1]["links"] if "/reflexes/" in (link["href"] or "")),
        None,
    )
    if not href:
        return None
    return href.rstrip("/").rsplit("/", 1)[-1]


def records_from_rows(rows: list[list[dict]], manifest: dict) -> list[dict]:
    pages_by_number = {page["page"]: page for page in manifest["pages"]}
    records = []
    for number, row in enumerate(rows, start=1):
        if len(row) < 6:
            raise ValueError(f"Jambu row {number} has fewer than six columns")
        upstream_id = _upstream_id(row)
        form = normalize(row[1]["text"])
        if not upstream_id or not form:
            raise ValueError(f"Jambu row {number} lacks a stable ID or Garhwali form")
        page_number = (number - 1) // PAGE_SIZE + 1
        page = pages_by_number[page_number]
        origin_link = next(
            (link for link in row[2]["links"] if link.get("href")), {}
        )
        reflex_url = urljoin(SOURCE_URL, row[1]["links"][0]["href"])
        origin_url = urljoin(SOURCE_URL, origin_link["href"]) if origin_link else None
        attribution = (
            "Jambu contributors; Garhwali forms and glosses from the Jambu dataset, "
            "with the source citation preserved per entry."
        )
        records.append(
            {
                "record_id": f"jambu-garhwali:{upstream_id}",
                "source_id": "jambu-garhwali",
                "text_original": row[1]["text"],
                "text_normalized": form,
                "text_sha256": sha256(form),
                "iso_639_3": "gbm",
                "language": "Garhwali",
                "license_id": "CC-BY-4.0",
                "license_url": LICENSE_URL,
                "attribution": attribution,
                "rights_status": "licensed",
                "rights_evidence": SOURCE_URL,
                "quality_status": "source-labeled_unreviewed",
                "native_reviewed": False,
                "training_eligible": False,
                "experimental_training_eligible": True,
                "recommended_use": "lexicon and vocabulary tasks; not conversational prose",
                "source_url": reflex_url,
                "provenance": {
                    "url": reflex_url,
                    "dataset_url": SOURCE_URL,
                    "page_url": page["url"],
                    "retrieved_at": manifest["retrieved_at"],
                    "page_sha256": page["sha256"],
                    "raw_path": page["raw_path"],
                    "upstream_record_id": upstream_id,
                },
                "form": form,
                "origin_form": row[2]["text"],
                "origin_entry_url": origin_url,
                "grammatical_note": row[4]["text"],
                "source_citation": row[5]["text"],
                "english_gloss": row[3]["text"],
                "script": "Latn_transcription",
                "genre": "lexicon",
                "corpus_layer": "core_open",
                "quality_flags": [
                    "historical_lexical_reflex",
                    "native_review_deferred",
                    "source_spelling_preserved",
                ],
            }
        )
    return records


def write_records(root: Path, records: list[dict], manifest: dict) -> dict:
    output = root / OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    unique_hashes = {record["text_sha256"] for record in records}
    existing_hashes = set()
    all_existing_hashes = set()
    canonical = root / "data/processed/text/canonical.jsonl"
    if canonical.exists():
        with canonical.open(encoding="utf-8") as stream:
            for line in stream:
                if not line.strip():
                    continue
                row = json.loads(line)
                all_existing_hashes.add(row["text_sha256"])
                if any(
                    item.get("source_id") != "jambu-garhwali"
                    for item in row.get("provenance", [])
                ):
                    existing_hashes.add(row["text_sha256"])
    overlap = unique_hashes & existing_hashes
    summary = {
        "source": manifest["source"],
        "source_url": SOURCE_URL,
        "license_id": "CC-BY-4.0",
        "license_url": LICENSE_URL,
        "rights_evidence_url": SOURCE_URL,
        "retrieved_at": manifest["retrieved_at"],
        "records": len(records),
        "unique_forms": len({record["text_normalized"] for record in records}),
        "duplicate_source_rows": len(records) - len(unique_hashes),
        "exact_overlap_with_existing_unique_forms": len(overlap),
        "exact_new_unique_forms": len(unique_hashes) - len(overlap),
        "already_in_current_corpus_unique_forms": len(unique_hashes & all_existing_hashes),
        "source_citation_counts": {},
        "rows_with_english_gloss": sum(bool(record["english_gloss"]) for record in records),
        "native_reviewed_records": 0,
        "training_eligible_records": sum(bool(record["training_eligible"]) for record in records),
        "pages": manifest["pages"],
        "source_file": str(OUTPUT),
        "source_file_sha256": sha256((root / OUTPUT).read_bytes()),
    }
    from collections import Counter

    summary["source_citation_counts"] = dict(
        Counter(record["source_citation"] for record in records)
    )
    manifest_path = root / OUTPUT_MANIFEST
    manifest_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def ingest(
    root: Path = ROOT,
    refresh: bool = False,
    offline: bool = False,
    fetcher=_download_page,
    sleeper=time.sleep,
) -> dict:
    rows, manifest = acquire_snapshot(
        root, refresh=refresh, offline=offline, fetcher=fetcher, sleeper=sleeper
    )
    records = records_from_rows(rows, manifest)
    summary = write_records(root, records, manifest)
    manifest_path = root / SNAPSHOT_MANIFEST
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="refetch all 16 public pages")
    parser.add_argument("--offline", action="store_true", help="rebuild only from saved pages")
    args = parser.parse_args()
    print(json.dumps(ingest(refresh=args.refresh, offline=args.offline), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
