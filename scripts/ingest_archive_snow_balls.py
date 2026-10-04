#!/usr/bin/env python3
"""Extract the Garhwal chapter from the 1946 Archive scan as local OCR records."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    "archive_id": "in.gov.ignca.12846",
    "source_id": "ia_ns_bhandari_snow_balls_garhwal_1946",
    "title": "Snow Balls of Garhwal",
    "author": "N. S. Bhandari",
    "year": 1946,
    "chapter_pages": [42, 110],
    "directory": ROOT / "data/downloads/folklore/internet_archive/snow_balls_garhwal_1946",
}
OUTPUT = ROOT / "data/extracted/research/internet_archive_reference_books_2026-10-03"
OUTPUT_JSONL = OUTPUT / f"{SOURCE['source_id']}.jsonl"
OUTPUT_MANIFEST = OUTPUT / f"{SOURCE['source_id']}_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def extract_page_text(page: ET.Element) -> str:
    lines = []
    for line in page.iter("LINE"):
        value = " ".join((word.text or "").strip() for word in line.iter("WORD"))
        value = re.sub(r"\s+", " ", value).strip()
        if value:
            lines.append(value)
    return "\n".join(lines)


def existing_text_hashes(output_path: Path) -> set[str]:
    hashes: set[str] = set()
    for folder in ("corpus", "restricted", "experimental", "extracted", "data/extracted"):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*.jsonl"):
            if path.resolve() == output_path.resolve():
                continue
            with path.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    for field in ("text_normalized", "text", "source_text", "transcript"):
                        value = row.get(field)
                        if isinstance(value, str) and value.strip():
                            hashes.add(hashlib.sha256(normalize(value).encode("utf-8")).hexdigest())
                            break
    return hashes


def main() -> None:
    directory: Path = SOURCE["directory"]
    pdf_path = directory / "source.pdf"
    ocr_path = directory / "source_djvu.xml"
    metadata_path = directory / "archive_metadata.json"
    download_manifest = json.loads((directory / "download_manifest.json").read_text(encoding="utf-8"))
    if not any(
        item.get("path", "").endswith("source.pdf")
        and item.get("sha1")
        and hashlib.sha1(pdf_path.read_bytes()).hexdigest() == item["sha1"]
        for item in download_manifest["files"]
    ):
        raise ValueError("Source PDF does not match its verified download manifest")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    archive_metadata = metadata.get("metadata", {})
    pdf_sha256 = sha256_file(pdf_path)
    ocr_sha256 = sha256_file(ocr_path)
    metadata_sha256 = sha256_file(metadata_path)
    first_page, last_page = SOURCE["chapter_pages"]
    pages = list(ET.parse(ocr_path).getroot().iter("OBJECT"))
    if last_page > len(pages):
        raise ValueError(f"Requested page {last_page}, but OCR has only {len(pages)} pages")

    rows = []
    for page_number in range(first_page, last_page + 1):
        text = extract_page_text(pages[page_number - 1])
        if not text:
            continue
        normalized = normalize(text)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        rows.append({
            "record_id": f"{SOURCE['source_id']}:page:{page_number:04d}",
            "source_id": SOURCE["source_id"],
            "archive_identifier": SOURCE["archive_id"],
            "title": SOURCE["title"],
            "author": SOURCE["author"],
            "publication_year": SOURCE["year"],
            "pdf_page": page_number,
            "text": text,
            "text_normalized": normalized,
            "text_sha256": digest,
            "language": "Garhwali folk material with English translation; page-level scope uncertain",
            "language_scope": "Garhwali oral-song chapter; Roman transliteration and English translation are both present",
            "script": "Latin_and_uncertain",
            "genre": "folk_songs_and_oral_traditions",
            "modality": "text_ocr_from_printed_book",
            "source_url": f"https://archive.org/details/{SOURCE['archive_id']}",
            "archive_metadata_url": f"https://archive.org/metadata/{SOURCE['archive_id']}",
            "source_pdf": str(pdf_path.relative_to(ROOT)),
            "source_pdf_sha256": pdf_sha256,
            "source_ocr_file": str(ocr_path.relative_to(ROOT)),
            "source_ocr_sha256": ocr_sha256,
            "source_metadata_sha256": metadata_sha256,
            "archive_license_claim": archive_metadata.get("licenseurl"),
            "printed_rights_notice": "All Rights Reserved",
            "rights_status": "printed_all_rights_reserved",
            "reuse_scope": "local_research_only_no_public_redistribution_or_training_use",
            "quality_status": "archive_djvu_ocr_unreviewed",
            "quality_flags": ["uncorrected_ocr", "native_review_needed", "translation_and_transliteration_mixed", "language_not_page_verified"],
            "training_eligible": False,
            "public_redistribution_eligible": False,
            "attribution": "N. S. Bhandari, Snow Balls of Garhwal (1946), chapter pages 42–110; Internet Archive item in.gov.ignca.12846.",
        })

    seen: set[str] = set()
    for row in rows:
        row["exact_duplicate_within_chapter"] = row["text_sha256"] in seen
        seen.add(row["text_sha256"])
    previous = existing_text_hashes(OUTPUT_JSONL)
    for row in rows:
        if row["text_sha256"] in previous:
            row["quality_flags"].append("exact_text_match_in_existing_project")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with OUTPUT_JSONL.open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    unique_hashes = {row["text_sha256"] for row in rows}
    manifest = {
        "source_id": SOURCE["source_id"],
        "archive_identifier": SOURCE["archive_id"],
        "source_url": f"https://archive.org/details/{SOURCE['archive_id']}",
        "title": SOURCE["title"],
        "author": SOURCE["author"],
        "publication_year": SOURCE["year"],
        "selected_pdf_pages_inclusive": SOURCE["chapter_pages"],
        "selection_basis": "OCR page 42 begins the titled Garhwal chapter; page 110 is its final song page; page 112 starts unrelated society matter.",
        "archive_pdf_sha256": pdf_sha256,
        "archive_ocr_sha256": ocr_sha256,
        "archive_metadata_sha256": metadata_sha256,
        "archive_license_claim": archive_metadata.get("licenseurl"),
        "printed_rights_notice": "All Rights Reserved",
        "rights_status": "printed_all_rights_reserved",
        "reuse_scope": "local_research_only_no_public_redistribution_or_training_use",
        "page_records": len(rows),
        "exact_unique_page_texts": len(unique_hashes),
        "exact_duplicates_within_chapter": sum(row["exact_duplicate_within_chapter"] for row in rows),
        "exact_overlaps_with_existing_project": sum("exact_text_match_in_existing_project" in row["quality_flags"] for row in rows),
        "characters": sum(len(row["text"]) for row in rows),
        "output_jsonl": str(OUTPUT_JSONL.relative_to(ROOT)),
        "training_eligible": False,
        "public_redistribution_eligible": False,
    }
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
