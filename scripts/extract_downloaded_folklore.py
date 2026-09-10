#!/usr/bin/env python3
"""Convert archived Internet Archive DjVu OCR into page-level JSONL."""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "downloads" / "folklore" / "internet_archive"
OUT = ROOT / "data" / "extracted" / "folklore"
SOURCES = [
    {
        "slug": "govind_chatak_gadwali_lokgeet_1956",
        "xml": "govind_chatak_gadwali_lokgeet_1956_djvu.xml",
        "title": "Gadwali Lokgeet",
        "creator": "Govind Chatak",
        "year": 1956,
        "url": "https://archive.org/details/in.ernet.dli.2015.404620",
        "archive_identifier": "in.ernet.dli.2015.404620",
    },
    {
        "slug": "shanti_chaudhary_garhwali_lokkala_loksahitya_1994",
        "xml": "shanti_chaudhary_garhwali_lokkala_loksahitya_1994_djvu.xml",
        "title": "Garhwali Lokkala Aur Loksahitya Ka Tulnatmak Anusilan",
        "creator": "Shanti Chaudhary",
        "year": 1994,
        "url": "https://archive.org/details/in.ernet.dli.2015.481134",
        "archive_identifier": "in.ernet.dli.2015.481134",
    },
]


def page_text(page: ET.Element) -> str:
    lines = []
    for line in page.iter("LINE"):
        text = " ".join((word.text or "").strip() for word in line.iter("WORD"))
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            lines.append(text)
    return "\n".join(lines)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = []
    for source in SOURCES:
        pages = ET.parse(RAW / source["xml"]).getroot().iter("OBJECT")
        records = []
        for page_number, page in enumerate(pages, start=1):
            text = page_text(page)
            if not text:
                continue
            records.append(
                {
                    "id": f"{source['archive_identifier']}:page:{page_number:04d}",
                    "text": text,
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "page": page_number,
                    "title": source["title"],
                    "creator": source["creator"],
                    "year": source["year"],
                    "source_url": source["url"],
                    "archive_identifier": source["archive_identifier"],
                    "language_scope": "Garhwali and Hindi; OCR language review required",
                    "genre": "folk_literature",
                    "rights_status": "publicly_downloadable_no_open_license_recorded",
                    "training_eligible": False,
                    "quality_flags": ["uncorrected_ocr", "language_mixed"],
                }
            )
        path = OUT / f"{source['slug']}.jsonl"
        path.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
            encoding="utf-8",
        )
        summary.append({"source": source["slug"], "records": len(records), "path": str(path.relative_to(ROOT))})
    (OUT / "manifest.json").write_text(
        json.dumps({"sources": summary}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
