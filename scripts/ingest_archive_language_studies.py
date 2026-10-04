#!/usr/bin/env python3
"""Extract page-level Archive OCR for two Garhwali language studies."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    {
        "archive_id": "ycbf_madhya-pahadi-bhasha-garhwali-kumauni-ka-anushilan-aur-uska-hindi-se-samban",
        "source_id": "ia_gunanand_juyal_madhya_pahadi_1967",
        "directory": "data/downloads/linguistics/internet_archive/madhya_pahadi_1967",
        "title": "Madhya Pahadi Bhasha Garhwali Kumauni Ka Anushilan Aur Uska Hindi Se Sambandh",
        "author": "Gunanand Juyal",
        "year": 1967,
        "language_scope": "Hindi comparative study with Garhwali and Kumauni language material",
        "genre": "comparative_linguistics",
    },
    {
        "archive_id": "ezqp-garhwali-bhasha-aur-uska-sahitya-by-haridatta-bhat",
        "source_id": "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976",
        "directory": "data/downloads/linguistics/internet_archive/garhwali_bhasha_sahitya_1976",
        "title": "Garhwali Bhasha Aur Uska Sahitya",
        "author": "Haridatta Bhatta ‘Shailesh’",
        "year": 1976,
        "language_scope": "Hindi study of Garhwali language and literature with Garhwali examples",
        "genre": "language_and_literature_study",
    },
    {
        "archive_id": "dli.ernet.426855",
        "source_id": "ia_govind_chatak_gadwali_lok_gathayen_1958",
        "directory": "data/downloads/folklore/internet_archive/gadwali_lok_gathayen_1958",
        "title": "Gadwali Lok Gathayen",
        "author": "Govind Chatak",
        "year": 1958,
        "language_scope": "Garhwali folk-ballad collection; individual page language requires review",
        "genre": "folk_ballads",
    },
    {
        "archive_id": "in.ernet.dli.2015.347446",
        "source_id": "ia_govind_chatak_gadwali_bhasha_undated",
        "directory": "data/downloads/linguistics/internet_archive/gadwali_bhasha_undated",
        "title": "Gadwali Bhasha",
        "author": "Govind Chatak",
        "year": None,
        "language_scope": "Hindi language reference concerning Garhwali; page-level language requires review",
        "genre": "language_study",
        "source_novelty_status": "partial_or_alternate_scan_of_existing_work",
        "duplicate_of_source_id": "incoming_garhwali_bhasha_linguistic_grammatical_study",
        "dedupe_note": "The scanned title page identifies Govind Chatak, Garhwali Bhasha, Lok Bharati, and November 1959, matching the user-supplied 1959 grammar. Archive metadata describes a 68-page item while the supplied scan has 147 pages; this may be a partial or alternate scan, not a new work.",
    },
]
OUTPUT = ROOT / "data/extracted/research/internet_archive_language_studies_2026-10-03"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha1_file(path: Path) -> str:
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
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


def repository_text_hashes(excluded_paths: set[Path]) -> set[str]:
    hashes = set()
    for folder in ("corpus", "restricted", "experimental", "extracted", "data/extracted"):
        directory = ROOT / folder
        if not directory.exists():
            continue
        for path in directory.rglob("*.jsonl"):
            if path.resolve() in excluded_paths:
                continue
            with path.open(encoding="utf-8", errors="replace") as handle:
                for line in handle:
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


def extract(source: dict) -> tuple[list[dict], dict]:
    directory = ROOT / source["directory"]
    metadata_path = directory / "archive_metadata.json"
    xml_path = directory / "source_djvu.xml"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    archive_metadata = metadata.get("metadata", {})
    license_claim = archive_metadata.get("licenseurl")
    rights_status = (
        "unverified_uploader_license_claim"
        if license_claim
        else "no_explicit_reuse_license_recorded"
    )
    metadata_sha256 = sha256_file(metadata_path)
    ocr_sha256 = sha256_file(xml_path)
    download_manifest = json.loads((directory / "download_manifest.json").read_text(encoding="utf-8"))
    pdf_entry = next((file for file in download_manifest["files"] if file.get("path", "").endswith("source.pdf")), None)
    pdf_path = directory / "source.pdf"
    pdf_sha1_verified = bool(pdf_entry and sha1_file(pdf_path) == pdf_entry.get("sha1"))
    if not pdf_sha1_verified:
        raise ValueError(f"PDF checksum does not match the download manifest: {pdf_path}")
    rows = []
    page_count = 0

    for page_number, page in enumerate(ET.parse(xml_path).getroot().iter("OBJECT"), 1):
        page_count += 1
        text = page_text(page)
        if not text.strip():
            continue
        normalized = normalize(text)
        has_devanagari = any("\u0900" <= c <= "\u097f" for c in normalized)
        has_latin = any(c.isascii() and c.isalpha() for c in normalized)
        script = "Mixed" if has_devanagari and has_latin else "Deva" if has_devanagari else "Latn" if has_latin else "Other"
        rows.append(
            {
                "record_id": f"{source['source_id']}:page:{page_number:04d}",
                "source_id": source["source_id"],
                "archive_identifier": source["archive_id"],
                "title": source["title"],
                "author": source["author"],
                "publication_year": source["year"],
                "pdf_page": page_number,
                "text": text,
                "text_normalized": normalized,
                "text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
                "iso_639_3": "mul",
                "language": "multilingual Garhwali-focused research source",
                "language_scope": source["language_scope"],
                "script": script,
                "genre": source["genre"],
                "source_novelty_status": source.get("source_novelty_status", "new_archive_work_not_yet_work_level_reviewed"),
                "duplicate_of_source_id": source.get("duplicate_of_source_id"),
                "dedupe_note": source.get("dedupe_note"),
                "modality": "text",
                "source_url": f"https://archive.org/details/{source['archive_id']}",
                "archive_metadata_url": f"https://archive.org/metadata/{source['archive_id']}",
                "source_metadata_sha256": metadata_sha256,
                "source_ocr_file": str(xml_path.relative_to(ROOT)),
                "source_ocr_sha256": ocr_sha256,
                "archive_license_claim": license_claim,
                "rights_status": rights_status,
                "reuse_scope": "local_research_only_pending_rights_verification",
                "quality_status": "archive_djvu_ocr_unreviewed",
                "quality_flags": [
                    "uncorrected_archive_ocr",
                    "mixed_language",
                    "not_native_reviewed",
                    *(["probable_duplicate_scan_of_existing_work"] if source.get("duplicate_of_source_id") else []),
                ],
                "training_eligible": False,
                "attribution": f"{source['author']}, {source['title']} ({source['year'] or 'date unknown'}); Internet Archive item {source['archive_id']}.",
            }
        )

    report = {
        "source_id": source["source_id"],
        "archive_identifier": source["archive_id"],
        "title": source["title"],
        "archive_license_claim": license_claim,
        "rights_status": rights_status,
        "source_novelty_status": source.get("source_novelty_status", "new_archive_work_not_yet_work_level_reviewed"),
        "duplicate_of_source_id": source.get("duplicate_of_source_id"),
        "dedupe_note": source.get("dedupe_note"),
        "pdf_pages_in_ocr": page_count,
        "nonempty_page_records": len(rows),
        "characters": sum(len(row["text"]) for row in rows),
        "exact_unique_page_texts": len({row["text_sha256"] for row in rows}),
        "pdf_sha1_verified": pdf_sha1_verified,
        "output": "",
    }
    return rows, report


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    all_rows = []
    reports = []
    output_paths = {OUTPUT / f"{source['source_id']}.jsonl" for source in SOURCES}
    for source in SOURCES:
        rows, report = extract(source)
        report["output"] = str((OUTPUT / f"{source['source_id']}.jsonl").relative_to(ROOT))
        reports.append(report)
        all_rows.extend(rows)

    ids = [row["record_id"] for row in all_rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate record IDs in Archive language-study extraction")
    prior_hashes = repository_text_hashes({path.resolve() for path in output_paths})
    frequencies = Counter(row["text_sha256"] for row in all_rows)
    for row in all_rows:
        flags = set(row["quality_flags"])
        if frequencies[row["text_sha256"]] > 1:
            flags.add("exact_duplicate_within_intake")
        if row["text_sha256"] in prior_hashes:
            flags.add("exact_duplicate_in_existing_project_data")
        row["quality_flags"] = sorted(flags)
    for report in reports:
        source_rows = [row for row in all_rows if row["source_id"] == report["source_id"]]
        report["exact_page_text_overlaps_with_existing_project"] = sum(
            row["text_sha256"] in prior_hashes for row in source_rows
        )
        report["exact_unique_texts_new_to_existing_project"] = len(
            {row["text_sha256"] for row in source_rows if row["text_sha256"] not in prior_hashes}
        )
        (ROOT / report["output"]).write_text(
            "".join(
                json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                for row in source_rows
            ),
            encoding="utf-8",
        )
    report = {
        "retrieved_date": "2026-10-03",
        "policy": "Page-level reference extraction only; mixed-language OCR remains local and is not training-eligible pending rights and language review.",
        "sources": reports,
        "records": len(all_rows),
        "exact_unique_page_texts_across_sources": len({row["text_sha256"] for row in all_rows}),
        "exact_unique_page_texts_from_sources_not_already_identified_as_same_work": len(
            {row["text_sha256"] for row in all_rows if not row.get("duplicate_of_source_id")}
        ),
        "page_records_from_probable_duplicate_or_alternate_scans": sum(
            bool(row.get("duplicate_of_source_id")) for row in all_rows
        ),
        "exact_duplicate_rows_within_intake": len(all_rows) - len(frequencies),
        "exact_duplicate_groups_within_intake": sum(value > 1 for value in frequencies.values()),
        "exact_duplicate_rows_against_existing_project": sum(
            row["text_sha256"] in prior_hashes for row in all_rows
        ),
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
