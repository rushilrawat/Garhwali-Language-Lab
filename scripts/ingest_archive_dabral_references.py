#!/usr/bin/env python3
"""Create a checksum-verified, page-level regional reference index for Dabral books."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/extracted/research/internet_archive_reference_books_2026-10-03"
TERMS = re.compile(
    r"गढ़वाल|गढवाल|गढ़वाली|गढवाली|गढ़वाळ|गढ़वालि|गढ़राज्य|गढ़पति|"
    r"अलकनन्दा|अलकनंदा|अलखनन्दा|भोटिया|भोटांतिक|पशुचारक|"
    r"टिहरी|चमोली|पौड़ी|देहरादून|श्रीनगर|केदारनाथ|बदरीनाथ|"
    r"Garhwal|Garhwali|Alaknanda|Uttarakhand",
    re.IGNORECASE,
)
SOURCES = [
    {
        "source_id": "ia_shiv_prasad_dabral_uttarakhand_history_vol1_1965",
        "archive_id": "ozkb_uttarakhand-ka-itihas-katyuri-yug-tak-bhag-1-sakshya-sankalan-by-shiv-prasa",
        "directory": "data/downloads/history/internet_archive/dabral_uttarakhand_history_vol1_katyuri_1965",
        "title": "Uttarakhand Ka Itihas: Katyuri Yug Tak, Bhag 1 (Sakshya Sankalan)",
        "author": "Shiv Prasad Dabral ‘Charan’ (Archive title-page attribution)",
        "year_claim": 1965,
        "genre": "regional_history_reference",
    },
    {
        "source_id": "ia_shiv_prasad_dabral_uttarakhand_history_vol3",
        "archive_id": "cylk_uttarakhand-ka-itihas-bhag-3-rajnaitik-tatha-sanskritik-itihas-by-shiv-pras",
        "directory": "data/downloads/history/internet_archive/dabral_uttarakhand_history_political_cultural_vol3",
        "title": "Uttarakhand Ka Itihas, Bhag 3: Rajnaitik Tatha Sanskritik Itihas",
        "author": "Shiv Prasad Dabral ‘Charan’ (Archive title-page attribution)",
        "year_claim": None,
        "genre": "regional_history_reference",
    },
    {
        "source_id": "ia_shiv_prasad_dabral_alaknanda_pravas_vol1",
        "archive_id": "wsxq_alakananda-upatyaka-mein-pravas-bhag-1-alakananda-upatyaka-by-shiva-prasad-",
        "directory": "data/downloads/geography/internet_archive/dabral_alaknanda_pravas_vol1",
        "title": "Alakananda Upatyaka Mein Pravas, Bhag 1",
        "author": "Shiv Prasad Dabral (Archive title-page attribution)",
        "year_claim": None,
        "genre": "regional_geography_and_transhumance_reference",
    },
    {
        "source_id": "ia_shiv_prasad_dabral_alaknanda_ethnography_vol2_1964",
        "archive_id": "xhed_uttarakhand-ke-bhotantik-alaknanda-upatyaka-mein-pravas-bhag-2-by-shivapras",
        "directory": "data/downloads/geography/internet_archive/dabral_alaknanda_ethnography_vol2_1964",
        "title": "Uttarakhand Ke Bhotantik Alaknanda Upatyaka Mein Pravas, Bhag 2",
        "author": "Shiv Prasad Dabral (Archive title-page attribution)",
        "year_claim": 1964,
        "genre": "regional_ethnography_and_transhumance_reference",
    },
    {
        "source_id": "ia_shiv_prasad_dabral_uttarakhand_yatra_darshan",
        "archive_id": "in.ernet.dli.2015.309034",
        "directory": "data/downloads/geography/internet_archive/dabral_uttarakhand_yatra_darshan_dli_scan",
        "title": "Shri Uttarakhand Yatra Darshan",
        "author": "Shiv Prasad Dabral (DLI/Archive attribution)",
        "year_claim": None,
        "genre": "regional_pilgrimage_geography_reference",
    },
]


def sha1(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def existing_text_hashes(excluded: set[Path]) -> set[str]:
    hashes = set()
    for folder in ("corpus", "restricted", "experimental", "extracted", "data/extracted"):
        base = ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*.jsonl"):
            if path.resolve() in excluded:
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
                            normalized = normalize(value)
                            hashes.add(hashlib.sha256(normalized.encode("utf-8")).hexdigest())
                            break
    return hashes


def source_pages(source: dict) -> tuple[list[dict], dict]:
    folder = ROOT / source["directory"]
    metadata_path = folder / "archive_metadata.json"
    manifest_path = folder / "download_manifest.json"
    pdf_path = folder / "source.pdf"
    ocr_path = folder / "source_djvu.xml"
    download = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = {entry["path"]: entry for entry in download["files"]}
    if sha1(pdf_path) != files["source.pdf"]["sha1"]:
        raise ValueError(f"PDF checksum mismatch: {pdf_path}")
    if sha1(ocr_path) != files["source_djvu.xml"]["sha1"]:
        raise ValueError(f"OCR checksum mismatch: {ocr_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    license_claim = metadata.get("metadata", {}).get("licenseurl") or download.get("archive_license_claim")
    rights = source.get("rights_status") or (
        "unverified_uploader_license_claim" if license_claim else "no_explicit_reuse_license_recorded"
    )
    pdf_hash, ocr_hash, metadata_hash = sha256(pdf_path), sha256(ocr_path), sha256(metadata_path)
    rows = []
    pages = list(ET.parse(ocr_path).getroot().iter("OBJECT"))
    for page_number, page in enumerate(pages, 1):
        text = page_text(page)
        term_pattern = source.get("terms", TERMS)
        matches = sorted({match.group(0) for match in term_pattern.finditer(text)}, key=str.casefold)
        if not text.strip() or not matches:
            continue
        normalized = normalize(text)
        text_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        has_deva = any("\u0900" <= char <= "\u097f" for char in normalized)
        has_latin = any(char.isascii() and char.isalpha() for char in normalized)
        script = "Mixed" if has_deva and has_latin else "Deva" if has_deva else "Latn" if has_latin else "Other"
        rows.append({
            "record_id": f"{source['source_id']}:scan-page:{page_number:04d}",
            "source_id": source["source_id"],
            "archive_identifier": source["archive_id"],
            "title": source["title"],
            "author": source["author"],
            "publication_year_claim": source["year_claim"],
            "scan_page": page_number,
            "text": text,
            "text_normalized": normalized,
            "text_sha256": text_hash,
            "language": source.get("language", "Hindi/regional historical OCR; Garhwali not individually confirmed"),
            "script": script,
            "genre": source["genre"],
            "matched_region_terms": matches,
            "modality": "text_ocr_reference",
            "source_url": f"https://archive.org/details/{source['archive_id']}",
            "source_pdf": str(pdf_path.relative_to(ROOT)),
            "source_pdf_sha256": pdf_hash,
            "source_ocr_file": str(ocr_path.relative_to(ROOT)),
            "source_ocr_sha256": ocr_hash,
            "source_metadata_sha256": metadata_hash,
            "archive_license_claim": license_claim,
            "rights_status": rights,
            "reuse_scope": source.get("reuse_scope", "local_research_reference_pending_rights_and_content_review"),
            "quality_status": "archive_djvu_ocr_unreviewed",
            "quality_flags": ["uncorrected_ocr", "regional_reference_not_verified_Garhwali_text", "not_native_reviewed"],
            "training_eligible": False,
            "public_redistribution_eligible": False,
            "attribution": f"{source['author']}, {source['title']}; Internet Archive item {source['archive_id']}, scan page {page_number}.",
        })
    return rows, {
        "source_id": source["source_id"],
        "archive_identifier": source["archive_id"],
        "title": source["title"],
        "archive_license_claim": license_claim,
        "rights_status": rights,
        "scan_pages": len(pages),
        "selected_page_records": len(rows),
        "exact_unique_selected_pages": len({row["text_sha256"] for row in rows}),
        "characters": sum(len(row["text"]) for row in rows),
        "pdf_bytes": pdf_path.stat().st_size,
        "pdf_sha1_verified": True,
        "ocr_sha1_verified": True,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_paths = {OUTPUT / f"{source['source_id']}.jsonl" for source in SOURCES}
    all_rows = []
    reports = []
    for source in SOURCES:
        rows, report = source_pages(source)
        all_rows.extend(rows)
        reports.append((source, rows, report))
    prior_hashes = existing_text_hashes({path.resolve() for path in output_paths})
    intake_counts = Counter(row["text_sha256"] for row in all_rows)
    for source, rows, report in reports:
        for row in rows:
            flags = set(row["quality_flags"])
            if intake_counts[row["text_sha256"]] > 1:
                flags.add("exact_duplicate_within_intake")
            if row["text_sha256"] in prior_hashes:
                flags.add("exact_duplicate_in_existing_project_data")
            row["quality_flags"] = sorted(flags)
        path = OUTPUT / f"{source['source_id']}.jsonl"
        path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        report["exact_page_overlaps_with_existing_project"] = sum(row["text_sha256"] in prior_hashes for row in rows)
        report["exact_unique_pages_new_to_existing_project"] = len({row["text_sha256"] for row in rows if row["text_sha256"] not in prior_hashes})
        report["output_jsonl"] = str(path.relative_to(ROOT))
    manifest = {
        "retrieved_date": "2026-10-03",
        "selection_rule": "Index only Archive OCR scan pages containing an explicit Garhwal/Garhwali, Alaknanda, named Garhwal district/pilgrimage-place or related regional term. This is a regional reference index, not a Garhwali-language extraction.",
        "all_records_training_eligible": False,
        "all_records_public_redistribution_eligible": False,
        "records": len(all_rows),
        "exact_unique_page_texts": len({row["text_sha256"] for row in all_rows}),
        "exact_duplicate_rows_within_intake": len(all_rows) - len(intake_counts),
        "exact_page_text_overlaps_with_existing_project": sum(row["text_sha256"] in prior_hashes for row in all_rows),
        "sources": [report for _, _, report in reports],
    }
    (OUTPUT / "ia_dabral_regional_reference_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
