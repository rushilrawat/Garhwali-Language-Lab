#!/usr/bin/env python3
"""Index OCR pages mentioning Garhwal in the 1905 Holy Himalaya scan."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "ia_e_sherman_oakley_holy_himalaya_1905"
ARCHIVE_ID = "holyhimalayareli00oaklrich"
SOURCE_DIR = ROOT / "data/downloads/geography/internet_archive/holy_himalaya_1905"
OUTPUT_DIR = ROOT / "data/extracted/research/internet_archive_reference_books_2026-10-03"
OUTPUT_JSONL = OUTPUT_DIR / f"{SOURCE_ID}.jsonl"
OUTPUT_MANIFEST = OUTPUT_DIR / f"{SOURCE_ID}_manifest.json"
GARHWAL = re.compile(r"garhwal|garwhal|gharwal|garhwali", re.IGNORECASE)


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(block)
    return sha.hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def page_text(page: ET.Element) -> str:
    lines = []
    for line in page.iter("LINE"):
        value = " ".join((word.text or "").strip() for word in line.iter("WORD"))
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            lines.append(value)
    return "\n".join(lines)


def main() -> None:
    pdf = SOURCE_DIR / "source.pdf"
    ocr = SOURCE_DIR / "source_djvu.xml"
    source_manifest = json.loads((SOURCE_DIR / "download_manifest.json").read_text(encoding="utf-8"))
    files = {item["path"]: item for item in source_manifest["payloads"]}
    if hashlib.sha1(pdf.read_bytes()).hexdigest() != files["source.pdf"]["sha1"]:
        raise ValueError("PDF no longer matches its Archive-verified manifest")
    pdf_hash, ocr_hash = digest(pdf), digest(ocr)
    metadata_hash = digest(SOURCE_DIR / "archive_metadata.json")
    rows = []
    pages = list(ET.parse(ocr).getroot().iter("OBJECT"))
    for page_number, page in enumerate(pages, 1):
        text = page_text(page)
        if not GARHWAL.search(text):
            continue
        normalized = normalize(text)
        matches = sorted({m.group(0) for m in GARHWAL.finditer(text)}, key=str.casefold)
        text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        rows.append({
            "record_id": f"{SOURCE_ID}:scan-page:{page_number:04d}",
            "source_id": SOURCE_ID,
            "archive_identifier": ARCHIVE_ID,
            "title": "Holy Himalaya: The Religion, Traditions and Scenery of a Himalayan Province",
            "author": "E. Sherman Oakley",
            "publication_year": 1905,
            "scan_page": page_number,
            "text": text,
            "text_normalized": normalized,
            "text_sha256": text_hash,
            "language": "English",
            "language_scope": "English historical reference; page explicitly mentions Garhwal/Garhwali",
            "genre": "historical_geography_and_ethnographic_reference",
            "modality": "text_ocr_reference",
            "matched_region_terms": matches,
            "source_url": f"https://archive.org/details/{ARCHIVE_ID}",
            "source_pdf": str(pdf.relative_to(ROOT)),
            "source_pdf_sha256": pdf_hash,
            "source_ocr_file": str(ocr.relative_to(ROOT)),
            "source_ocr_sha256": ocr_hash,
            "source_metadata_sha256": metadata_hash,
            "archive_possible_copyright_status": "NOT_IN_COPYRIGHT",
            "rights_status": "archive_not_in_copyright_claim_recorded",
            "reuse_scope": "local_research_reference_pending_project_rights_review",
            "quality_status": "archive_djvu_ocr_unreviewed",
            "quality_flags": ["uncorrected_ocr", "historical_English_not_Garhwali_text", "regional_context_not_language_training_data"],
            "training_eligible": False,
            "public_redistribution_eligible": False,
            "attribution": "E. Sherman Oakley, Holy Himalaya (1905), scan page noted; Internet Archive item holyhimalayareli00oaklrich.",
        })

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    hashes = [row["text_sha256"] for row in rows]
    manifest = {
        "source_id": SOURCE_ID,
        "archive_identifier": ARCHIVE_ID,
        "source_url": f"https://archive.org/details/{ARCHIVE_ID}",
        "selection_rule": "Keep scanned OCR pages containing an explicit Garhwal, Garhwali, Garwhal, or Gharwal spelling; this is a regional reference index, not a Garhwali-language corpus extract.",
        "scan_page_count": len(pages),
        "selected_page_records": len(rows),
        "exact_unique_selected_pages": len(set(hashes)),
        "archive_scan_status": "NOT_IN_COPYRIGHT",
        "reuse_scope": "local_research_reference_pending_project_rights_review",
        "training_eligible": False,
        "public_redistribution_eligible": False,
        "output_jsonl": str(OUTPUT_JSONL.relative_to(ROOT)),
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
