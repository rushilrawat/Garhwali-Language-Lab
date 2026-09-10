#!/usr/bin/env python3
"""Extract Garhwali idioms and proverbs from the archived Dhyani Google Site."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "downloads" / "garhwali_idioms_dhyani" / "page.html"
OUT = ROOT / "data" / "extracted" / "garhwali_idioms_dhyani"
URL = "https://sites.google.com/view/dhyani/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B3-%E0%A4%95%E0%A4%95%E0%A4%B7/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B2-%E0%A4%AE%E0%A4%B9%E0%A4%B5%E0%A4%B0-%E0%A4%94%E0%A4%B0-%E0%A4%95%E0%A4%B9%E0%A4%B5%E0%A4%A4"


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return re.sub(r"\s+", " ", text).strip()


def record(text: str, kind: str, position: int, context: list[str] | None = None) -> dict:
    normalized = normalize(text).lstrip("★").strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    row = {
        "id": f"dhyani-idioms:{kind}:{position:04d}",
        "text": normalized,
        "text_sha256": digest,
        "language": "Garhwali",
        "genre": "idiom_or_proverb",
        "source_title": "गढ़वाली मुहावरे और कहावतें",
        "source_author": "बालकृष्ण डी ध्यानी",
        "source_credit": "श्री प्रकाश भट (सेवानिवृत प्रधानाचार्य)",
        "source_url": URL,
        "source_section": kind,
        "rights_status": "publicly_accessible_no_open_license_recorded",
        "training_eligible": False,
        "quality_flags": ["community_web_source", "orthography_review_required"],
    }
    if context:
        row["translations_or_notes"] = context
    return row


def main() -> None:
    soup = BeautifulSoup(RAW.read_text(encoding="utf-8"), "html.parser")
    lines = [normalize(x) for x in soup.get_text("\n").splitlines() if normalize(x)]
    heading = next(
        i for i, x in enumerate(lines)
        if "मुहावरे और कहावतें -आभर श्री प्रकाश भट" in x
    )
    section = lines[heading + 1 :]

    rows: list[dict] = []
    for line in section:
        if line.startswith("★"):
            rows.append(record(line, "credited_list", len(rows) + 1))

    for i, line in enumerate(section):
        if line != "गढ़वाली" or i + 1 >= len(section):
            continue
        garhwali = section[i + 1]
        if garhwali in {"कुमाऊँनी", "Page updated", "Google Sites", "Report abuse"}:
            continue
        notes = []
        for candidate in section[i + 2 :]:
            if candidate in {"गढ़वाली", "कुमाऊँनी", "Page updated", "Google Sites", "Report abuse"}:
                break
            notes.append(candidate)
        rows.append(record(garhwali, "comparison_entry", len(rows) + 1, notes))

    unique = []
    seen = set()
    for row in rows:
        if row["text_sha256"] in seen:
            continue
        seen.add(row["text_sha256"])
        row["id"] = f"dhyani-idioms:{len(unique) + 1:04d}"
        unique.append(row)

    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / "idioms_proverbs.jsonl"
    output.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in unique),
        encoding="utf-8",
    )
    manifest = {
        "source_url": URL,
        "raw_file": str(RAW.relative_to(ROOT)),
        "raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "records_before_deduplication": len(rows),
        "records_after_deduplication": len(unique),
        "output": str(output.relative_to(ROOT)),
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == "__main__":
    main()
