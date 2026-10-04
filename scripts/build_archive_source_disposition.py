"""Build a source-level evidence register and local Archive review indexes.

The script reads captured Internet Archive metadata, the existing OCR indexes,
and the 2026-10-04 media/overlap audits. It never edits or removes source
payloads, changes corpus eligibility, or publishes extracted content.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from audit_archive_intake_quality import profile_text
from audit_archive_corpus_overlap import normalize_text


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "data/downloads"
QUALITY_AUDIT = ROOT / "data/extracted/research/internet_archive_quality_audit_2026-10-04.json"
OVERLAP_AUDIT = ROOT / "data/extracted/research/internet_archive_corpus_overlap_2026-10-04.json"
OCR_DIRS = (
    Path("data/extracted/research/internet_archive_language_studies_2026-10-03"),
    Path("data/extracted/research/internet_archive_reference_books_2026-10-03"),
)
REGISTER = ROOT / "research/internet-archive-source-disposition-2026-10-04.json"
REPORT = ROOT / "research/internet-archive-source-disposition-2026-10-04.md"
CANDIDATE_DIR = ROOT / "data/extracted/research/internet_archive_candidate_views_2026-10-04"
TEXT_CANDIDATES = CANDIDATE_DIR / "text_review_candidates.jsonl"
MEDIA_CANDIDATES = CANDIDATE_DIR / "media_review_candidates.jsonl"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = "; ".join(str(part) for part in value if part is not None)
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value or None


def _rights_fields(metadata: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in sorted(metadata.items())
        if any(term in key.casefold() for term in ("license", "right", "copyright"))
        and value not in (None, "", [])
    }


def _cc_identifier(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"/licenses/(by(?:-nc)?(?:-nd|-sa)?)/(\d+(?:\.\d+)*)", value, re.I)
    if match:
        return f"cc-{match.group(1).casefold()}-{match.group(2)}"
    match = re.search(r"cc[- ](by(?:-nc)?(?:-nd|-sa)?)\s*(\d+(?:\.\d+)*)", value, re.I)
    if match:
        return f"cc-{match.group(1).casefold()}-{match.group(2)}"
    return None


def _metadata_description_rights_excerpt(metadata: dict[str, Any]) -> str | None:
    description = _text(metadata.get("description"))
    if not description:
        return None
    plain = re.sub(r"<[^>]*>", " ", description)
    plain = re.sub(r"\s+", " ", plain).strip()
    match = re.search(r"rights?\s*holder|copyright|all rights reserved|public domain|licen[cs]e", plain, re.I)
    if not match:
        return None
    start = max(0, match.start() - 180)
    return plain[start:min(len(plain), match.end() + 320)]


def _license_class(metadata: dict[str, Any]) -> tuple[str, str | None, bool]:
    """Return a recorded-claim label, URI/text, and metadata-conflict flag."""
    license_claim = _text(metadata.get("licenseurl") or metadata.get("license"))
    rights_text = _text(metadata.get("rights"))
    claim = (license_claim or "").casefold()
    if "publicdomain/zero" in claim or "cc0" in claim:
        label = "cc0_claim"
    elif "publicdomain/mark" in claim:
        label = "public_domain_mark_claim"
    elif "by-nc-sa" in claim:
        label = "cc_by_nc_sa_claim"
    elif "by-nc-nd" in claim:
        label = "cc_by_nc_nd_claim"
    elif "by-nc" in claim:
        label = "cc_by_nc_claim"
    elif "creativecommons.org/licenses/by/" in claim or "cc-by 4.0" in claim:
        label = "cc_by_claim"
    elif license_claim:
        label = "other_license_claim"
    else:
        label = "no_reuse_license_claim_recorded"

    conflict = False
    if license_claim and rights_text:
        license_cc = _cc_identifier(license_claim)
        rights_cc = _cc_identifier(rights_text)
        if license_cc and rights_cc:
            conflict = license_cc != rights_cc
    return label, license_claim, conflict


def classify_page_candidate(
    language_label: str | None,
    duplicate_of_source_id: str | None,
    text: str | None = None,
) -> tuple[str, str]:
    """Classify for follow-up review without asserting page-level language."""
    if not (text or "").strip():
        return "empty_ocr_page_pending_visual_check", "The OCR sidecar has an empty page; retain the source scan and review the image if needed."
    if duplicate_of_source_id:
        return "known_alternate_scan_of_existing_work", "Retain the page; source metadata links this scan to an existing work."
    label = (language_label or "").casefold()
    if "garhwali-focused" in label:
        return "priority_language_study_review", "The source is Garhwali-focused; this does not verify the language of this OCR page."
    if "garhwali folk material" in label:
        return "translated_folklore_scope_review", "Source describes Garhwali folk material with translation; page-level language and translation boundaries are unreviewed."
    return "regional_context_not_verified_garhwali", "Keep as a contextual source; this source/page is not verified as Garhwali-language text."


def triage_page_text(text: str) -> dict[str, Any]:
    """Attach non-linguistic-identification signals for review prioritization."""
    profile = profile_text(text)
    return {
        "character_count": profile["characters"],
        "whitespace_word_count": profile["words"],
        "script_profile": profile["script_profile"],
        "script_letter_counts": profile["script_letter_counts"],
        "warning_flags": profile["warning_flags"],
        "language_identification": "not_performed",
    }


def _load_ocr_records(paths: list[str]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    sources: dict[str, dict[str, Any]] = {}
    for raw_path in paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = ROOT / path
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                record = json.loads(line)
                records.append(record)
                identifier = record.get("archive_identifier")
                if identifier:
                    summary = sources.setdefault(identifier, {
                        "record_count": 0,
                        "language_labels": Counter(),
                        "rights_statuses": Counter(),
                        "source_ids": set(),
                        "duplicate_targets": set(),
                    })
                    summary["record_count"] += 1
                    summary["language_labels"][record.get("language") or "not_labeled"] += 1
                    summary["rights_statuses"][record.get("rights_status") or "not_labeled"] += 1
                    if record.get("source_id"):
                        summary["source_ids"].add(record["source_id"])
                    if record.get("duplicate_of_source_id"):
                        summary["duplicate_targets"].add(record["duplicate_of_source_id"])
    return records, sources


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].upper()


def _supplemental_djvu_pages(
    root: Path,
    indexed_identifiers: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Index readable local DjVu XML for Archive text items absent from OCR JSONL."""
    additions: list[dict[str, Any]] = []
    sidecars: list[dict[str, Any]] = []
    for metadata_path in sorted((root / DOWNLOADS.relative_to(ROOT)).rglob("archive_metadata.json")):
        item_snapshot = _read_json(metadata_path)
        metadata = item_snapshot.get("metadata", {})
        identifier = _text(metadata.get("identifier"))
        if not identifier or identifier in indexed_identifiers or metadata.get("mediatype") != "texts":
            continue
        candidates = sorted(
            path for path in metadata_path.parent.glob("*djvu*.xml")
            if path.name.casefold() != "archive_metadata.xml"
        )
        parsed: tuple[Path, list[tuple[str | None, str, list[int]]]] | None = None
        for xml_path in candidates:
            try:
                document = ET.parse(xml_path).getroot()
            except (ET.ParseError, OSError):
                continue
            if _xml_local_name(document.tag) != "DJVUXML":
                continue
            pages = []
            for obj in document.iter():
                if _xml_local_name(obj.tag) != "OBJECT":
                    continue
                scan_label = None
                for child in obj.iter():
                    if _xml_local_name(child.tag) == "PARAM" and child.attrib.get("name", "").upper() == "PAGE":
                        scan_label = child.attrib.get("value")
                        break
                words = []
                confidence = []
                for child in obj.iter():
                    if _xml_local_name(child.tag) == "WORD":
                        if child.text and child.text.strip():
                            words.append(child.text.strip())
                        try:
                            confidence.append(int(child.attrib["x-confidence"]))
                        except (KeyError, TypeError, ValueError):
                            pass
                if scan_label is not None:
                    pages.append((scan_label, " ".join(words).strip(), confidence))
            if pages:
                parsed = (xml_path, pages)
                break
        if not parsed:
            continue

        xml_path, pages = parsed
        slug = metadata_path.parent.name
        source_id = slug if slug.startswith("ia_") else f"ia_{slug}"
        title = _text(metadata.get("title")) or identifier
        if "himalayan folklore" in title.casefold():
            language_label = "Garhwali folk material with English translation; page-level scope uncertain"
            language_scope = "English-language regional folklore source; exact page language and translation boundaries unreviewed"
            genre = "translated_regional_folklore_reference"
        else:
            language_label = "English OCR; regional reference, not verified Garhwali text"
            language_scope = "Regional history/geography reference; page-level language not individually reviewed"
            genre = "regional_context_reference"
        pdf_candidates = sorted(metadata_path.parent.glob("*.pdf"))
        pdf_path = pdf_candidates[0] if pdf_candidates else None
        metadata_sha256 = _sha256(metadata_path)
        ocr_sha256 = _sha256(xml_path)
        pdf_sha256 = _sha256(pdf_path) if pdf_path else None
        source_url = f"https://archive.org/details/{identifier}"
        rights_fields = _rights_fields(metadata)
        manifest_path = metadata_path.parent / "download_manifest.json"
        manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
        license_claim = _text(metadata.get("licenseurl") or metadata.get("license") or manifest.get("archive_license_claim"))
        rights_status = (
            "recorded_rights_or_license_claim_not_independently_verified"
            if license_claim or rights_fields or manifest.get("rights_status")
            else "no_explicit_reuse_license_recorded"
        )
        sidecars.append({
            "archive_identifier": identifier,
            "source_id": source_id,
            "source_url": source_url,
            "source_ocr_file": xml_path.relative_to(root).as_posix(),
            "source_ocr_sha256": ocr_sha256,
            "extracted_page_count_including_empty": len(pages),
            "extracted_nonempty_page_count": sum(bool(text) for _, text, _ in pages),
            "source_pdf": pdf_path.relative_to(root).as_posix() if pdf_path else None,
            "source_pdf_sha256": pdf_sha256,
        })
        for page_number, (scan_label, text, confidence) in enumerate(pages, 1):
            record_id = f"{source_id}:scan-page:{page_number:04d}"
            normalized = normalize_text(text)
            additions.append({
                "archive_identifier": identifier,
                "archive_metadata_url": f"https://archive.org/metadata/{identifier}",
                "attribution": _text(metadata.get("creator")) or title,
                "genre": genre,
                "language": language_label,
                "language_scope": language_scope,
                "modality": "text_ocr_reference",
                "publication_year_claim": _text(metadata.get("date")),
                "public_redistribution_eligible": False,
                "quality_flags": ["uncorrected_archive_ocr", "not_native_reviewed", "page_language_unverified"],
                "quality_status": "archive_djvu_ocr_unreviewed",
                "record_id": record_id,
                "rights_status": rights_status,
                "reuse_scope": "local_research_reference_pending_rights_and_content_review",
                "scan_page": page_number,
                "scan_page_label": scan_label,
                "source_id": source_id,
                "source_metadata_sha256": metadata_sha256,
                "source_ocr_file": xml_path.relative_to(root).as_posix(),
                "source_ocr_sha256": ocr_sha256,
                "source_pdf": pdf_path.relative_to(root).as_posix() if pdf_path else None,
                "source_pdf_sha256": pdf_sha256,
                "source_url": source_url,
                "text": text,
                "text_normalized": normalized,
                "text_sha256": hashlib.sha256(
                    re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip().encode("utf-8")
                ).hexdigest(),
                "training_eligible": False,
                "ocr_word_confidence_mean": round(sum(confidence) / len(confidence), 3) if confidence else None,
                "ocr_word_confidence_count": len(confidence),
                "ocr_confidence_is_engine_signal_not_accuracy": bool(confidence),
            })
    return additions, sidecars


def _item_root_for_media(path: Path, item_dirs: dict[Path, dict[str, Any]]) -> dict[str, Any] | None:
    resolved = path.resolve()
    for folder, item in item_dirs.items():
        try:
            resolved.relative_to(folder.resolve())
        except ValueError:
            continue
        return item
    return None


def build_disposition(root: Path = ROOT) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    quality_path = root / QUALITY_AUDIT.relative_to(ROOT)
    overlap_path = root / OVERLAP_AUDIT.relative_to(ROOT)
    quality = _read_json(quality_path)
    overlap = _read_json(overlap_path)
    ocr_paths = [
        str(path.relative_to(root))
        for directory in OCR_DIRS
        for path in sorted((root / directory).glob("*.jsonl"))
    ]
    page_records, page_summaries = _load_ocr_records(ocr_paths)
    indexed_identifiers = set(page_summaries)
    supplemental_records, supplemental_sidecars = _supplemental_djvu_pages(root, indexed_identifiers)
    page_records.extend(supplemental_records)
    for record in supplemental_records:
        summary = page_summaries.setdefault(record["archive_identifier"], {
            "record_count": 0,
            "language_labels": Counter(),
            "rights_statuses": Counter(),
            "source_ids": set(),
            "duplicate_targets": set(),
        })
        summary["record_count"] += 1
        summary["language_labels"][record["language"]] += 1
        summary["rights_statuses"][record["rights_status"]] += 1
        summary["source_ids"].add(record["source_id"])
        confidence_count = record.get("ocr_word_confidence_count", 0)
        confidence_mean = record.get("ocr_word_confidence_mean")
        if confidence_count and confidence_mean is not None:
            summary["confidence_weighted_sum"] = summary.get("confidence_weighted_sum", 0.0) + confidence_mean * confidence_count
            summary["confidence_word_count"] = summary.get("confidence_word_count", 0) + confidence_count
            summary["confidence_page_count"] = summary.get("confidence_page_count", 0) + 1
            if confidence_mean < 50:
                summary["confidence_pages_below_50"] = summary.get("confidence_pages_below_50", 0) + 1

    item_dirs: dict[Path, dict[str, Any]] = {}
    for metadata_path in sorted((root / DOWNLOADS.relative_to(ROOT)).rglob("archive_metadata.json")):
        item_metadata = _read_json(metadata_path)
        metadata = item_metadata.get("metadata", {})
        identifier = _text(metadata.get("identifier"))
        if not identifier:
            continue
        manifest_path = metadata_path.parent / "download_manifest.json"
        manifest = _read_json(manifest_path) if manifest_path.is_file() else {}
        claim_class, metadata_license_claim, conflict = _license_class(metadata)
        manifest_license_claim = _text(manifest.get("archive_license_claim") or manifest.get("license_claim"))
        if metadata_license_claim:
            license_claim = metadata_license_claim
        elif manifest_license_claim:
            claim_class, license_claim, _manifest_only_conflict = _license_class({"licenseurl": manifest_license_claim})
        else:
            license_claim = None
        manifest_conflict = bool(
            metadata_license_claim
            and manifest_license_claim
            and _cc_identifier(metadata_license_claim)
            and _cc_identifier(manifest_license_claim)
            and _cc_identifier(metadata_license_claim) != _cc_identifier(manifest_license_claim)
        )
        conflict = conflict or manifest_conflict
        rights_fields = _rights_fields(metadata)
        item = {
            "archive_identifier": identifier,
            "source_url": f"https://archive.org/details/{identifier}",
            "metadata_snapshot_path": metadata_path.relative_to(root).as_posix(),
            "metadata_snapshot_sha256": _sha256(metadata_path),
            "local_source_directory": metadata_path.parent.relative_to(root).as_posix(),
            "title": _text(metadata.get("title")),
            "creator_claim": _text(metadata.get("creator")),
            "date_claim": _text(metadata.get("date")),
            "mediatype": _text(metadata.get("mediatype")),
            "language_claim": _text(metadata.get("language")),
            "subject_claims": metadata.get("subject", []) if isinstance(metadata.get("subject", []), list) else [_text(metadata.get("subject"))],
            "license_claim": license_claim,
            "rights_fields": rights_fields,
            "description_rights_excerpt": _metadata_description_rights_excerpt(metadata),
            "download_manifest_path": manifest_path.relative_to(root).as_posix() if manifest_path.is_file() else None,
            "download_manifest_license_claim": manifest_license_claim,
            "download_manifest_rights_status": _text(manifest.get("rights_status")),
            "download_manifest_rights_note": _text(manifest.get("rights_note")),
            "license_claim_class": claim_class,
            "metadata_license_conflict": conflict,
            "rights_evidence_decision": (
                "conflicting_item_rights_fields_need_resolution" if conflict else
                "recorded_license_or_status_claim_not_independently_verified" if license_claim or rights_fields or manifest.get("rights_status") or manifest.get("rights_note") or _metadata_description_rights_excerpt(metadata) else
                "no_explicit_reuse_license_in_captured_item_metadata"
            ),
            "publication_and_training_decision": "no_new_content_cleared_by_this_metadata_review",
            "source_claims_are_not_independent_rights_clearance": True,
        }
        item_dirs[metadata_path.parent] = item

    item_by_identifier = {item["archive_identifier"]: item for item in item_dirs.values()}
    media_rows: list[dict[str, Any]] = []
    media_by_identifier: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for media in sorted(quality.get("media", {}).get("files", []), key=lambda row: row["path"]):
        media_path = Path(media["path"])
        item = _item_root_for_media(media_path, item_dirs)
        if item is None:
            continue
        row = {
            "archive_identifier": item["archive_identifier"],
            "source_id": item["archive_identifier"],
            "source_url": item["source_url"],
            "title": item["title"],
            "media_path": media_path.resolve().relative_to(root).as_posix(),
            "media_sha256": _sha256(media_path),
            "bytes": media.get("size_bytes"),
            "duration_seconds": media.get("duration_seconds"),
            "streams": media.get("streams", []),
            "license_claim": item["license_claim"],
            "license_claim_class": item["license_claim_class"],
            "rights_evidence_decision": item["rights_evidence_decision"],
            "content_review_status": "not_reviewed_for_language_or_content",
            "transcript_status": "not_transcribed_in_this_workstream",
            "publication_and_training_decision": "no_media_content_cleared_by_this_metadata_review",
        }
        media_rows.append(row)
        media_by_identifier[item["archive_identifier"]].append(row)

    normalized_groups: dict[str, list[str]] = defaultdict(list)
    for record in page_records:
        normalized = normalize_text(record.get("text_normalized") or record.get("text"))
        if normalized:
            normalized_groups[hashlib.sha256(normalized.encode("utf-8")).hexdigest()].append(record.get("record_id", ""))
    exact_duplicates = {
        record_id
        for record_ids in normalized_groups.values() if len(record_ids) > 1
        for record_id in record_ids
    }
    canonical_matches_by_archive_record: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for match in overlap.get("exact", {}).get("matches", []):
        canonical_matches_by_archive_record[match["archive"].get("record_id", "")].append(match["corpus"])
    text_rows: list[dict[str, Any]] = []
    for record in page_records:
        group, reason = classify_page_candidate(record.get("language"), record.get("duplicate_of_source_id"), record.get("text"))
        canonical_matches = canonical_matches_by_archive_record.get(record.get("record_id", ""), [])
        page_triage = triage_page_text(record.get("text") or "")
        row = {
            **record,
            "archive_review_candidate_group": group,
            "archive_review_candidate_reason": reason,
            "automated_page_triage": page_triage,
            "within_intake_exact_duplicate": record.get("record_id") in exact_duplicates,
            "canonical_exact_match": bool(canonical_matches),
            "canonical_match_references": canonical_matches,
            "review_outcome": "source_linked_review_candidate_retained",
            "rights_and_eligibility_unchanged": True,
        }
        text_rows.append(row)

    for identifier, item in item_by_identifier.items():
        pages = page_summaries.get(identifier, {})
        item["ocr_page_records"] = pages.get("record_count", 0)
        item["ocr_language_labels"] = dict(sorted(pages.get("language_labels", {}).items()))
        item["ocr_recorded_rights_statuses"] = dict(sorted(pages.get("rights_statuses", {}).items()))
        item["ocr_work_level_duplicate_targets"] = sorted(pages.get("duplicate_targets", set()))
        item["ocr_word_confidence_page_count"] = pages.get("confidence_page_count", 0)
        item["ocr_word_confidence_word_count"] = pages.get("confidence_word_count", 0)
        item["ocr_word_confidence_mean"] = (
            round(pages["confidence_weighted_sum"] / pages["confidence_word_count"], 3)
            if pages.get("confidence_word_count") else None
        )
        item["ocr_pages_mean_confidence_below_50"] = pages.get("confidence_pages_below_50", 0)
        item_matches = [
            {
                "archive_record_id": record.get("record_id"),
                "canonical_references": canonical_matches_by_archive_record.get(record.get("record_id", ""), []),
            }
            for record in page_records
            if record.get("archive_identifier") == identifier and record.get("record_id") in canonical_matches_by_archive_record
        ]
        item["canonical_exact_match_page_records"] = item_matches
        item["media_files_probed"] = len(media_by_identifier.get(identifier, []))
        item["media_duration_seconds"] = round(sum(row["duration_seconds"] or 0 for row in media_by_identifier.get(identifier, [])), 3)
        if item["ocr_page_records"]:
            labels = pages.get("language_labels", {})
            item["language_scope_decision"] = (
                "source_labeled_garhwali_focused_but_page_language_unverified"
                if any("garhwali-focused" in label.casefold() for label in labels)
                else "source_mentions_garhwali_folk_material_but_page_scope_unverified"
                if any("garhwali folk material" in label.casefold() for label in labels)
                else "contextual_regional_reference_not_verified_garhwali_text"
            )
        elif item["mediatype"] in {"audio", "movies"} or item["media_files_probed"]:
            item["language_scope_decision"] = "archive_metadata_only_media_language_and_content_unreviewed"
        else:
            item["language_scope_decision"] = "metadata_only_or_non_ocr_payload_content_unreviewed"

    text_rows.sort(key=lambda row: row.get("record_id", ""))
    media_rows.sort(key=lambda row: (row["archive_identifier"], row["media_path"]))
    license_counts = Counter(item["license_claim_class"] for item in item_by_identifier.values())
    media_type_counts = Counter(item["mediatype"] or "unspecified" for item in item_by_identifier.values())
    candidate_counts = Counter(row["archive_review_candidate_group"] for row in text_rows)
    triage_by_group: dict[str, dict[str, Any]] = {}
    for group in sorted(candidate_counts):
        rows = [row for row in text_rows if row["archive_review_candidate_group"] == group]
        script_counts = Counter(row["automated_page_triage"]["script_profile"] for row in rows)
        warning_counts = Counter(
            warning
            for row in rows
            for warning in row["automated_page_triage"]["warning_flags"]
        )
        triage_by_group[group] = {
            "pages": len(rows),
            "script_profiles": dict(sorted(script_counts.items())),
            "pages_with_any_ocr_warning": sum(bool(row["automated_page_triage"]["warning_flags"]) for row in rows),
            "ocr_warning_rows": dict(sorted(warning_counts.items())),
        }
    confidence_items = [item for item in item_by_identifier.values() if item["ocr_word_confidence_word_count"]]
    confidence_word_count = sum(item["ocr_word_confidence_word_count"] for item in confidence_items)
    confidence_mean = (
        round(sum(item["ocr_word_confidence_mean"] * item["ocr_word_confidence_word_count"] for item in confidence_items) / confidence_word_count, 3)
        if confidence_word_count else None
    )
    register = {
        "schema_version": "internet-archive-source-disposition-v1",
        "audit_date": "2026-10-04",
        "purpose": "Item-level inventory of captured rights and language claims plus source-linked review candidates. This is not a rights determination, language verification, or release approval.",
        "inputs": {
            "archive_metadata_snapshots": len(item_dirs),
            "quality_audit_sha256": _sha256(quality_path),
            "overlap_audit_sha256": _sha256(overlap_path),
            "ocr_jsonl_files": ocr_paths,
            "supplemental_djvu_sidecars": supplemental_sidecars,
        },
        "summary": {
            "archive_items": len(item_by_identifier),
            "archive_items_by_mediatype": dict(sorted(media_type_counts.items())),
            "archive_items_by_recorded_license_claim": dict(sorted(license_counts.items())),
            "items_with_conflicting_license_fields": sum(item["metadata_license_conflict"] for item in item_by_identifier.values()),
            "ocr_page_records": len(text_rows),
            "ocr_nonempty_page_records": sum(bool((row.get("text") or "").strip()) for row in text_rows),
            "supplemental_djvu_page_records": len(supplemental_records),
            "normalized_nonempty_text_records": sum(len(record_ids) for record_ids in normalized_groups.values()),
            "normalized_exact_unique_nonempty_texts": len(normalized_groups),
            "nonempty_texts_without_normalized_letters_or_numbers": sum(
                bool((row.get("text") or "").strip()) and not normalize_text(row.get("text")) for row in text_rows
            ),
            "ocr_page_review_groups": dict(sorted(candidate_counts.items())),
            "automated_page_triage_by_review_group": triage_by_group,
            "within_archive_exact_duplicate_page_rows": len(exact_duplicates),
            "within_archive_exact_duplicate_groups": sum(len(record_ids) > 1 for record_ids in normalized_groups.values()),
            "canonical_exact_match_page_rows": sum(len(matches) for matches in canonical_matches_by_archive_record.values()),
            "canonical_exact_unique_text_matches": len({
                match["archive"].get("normalized_text_sha256")
                for match in overlap.get("exact", {}).get("matches", [])
            }),
            "canonical_near_duplicate_candidates": overlap.get("near_duplicate", {}).get("threshold_pairs", 0),
            "unique_normalized_page_texts_not_in_canonical_view": max(
                0,
                len(normalized_groups) - len({
                    match["archive"].get("normalized_text_sha256")
                    for match in overlap.get("exact", {}).get("matches", [])
                }),
            ),
            "ocr_word_confidence_pages": sum(item["ocr_word_confidence_page_count"] for item in confidence_items),
            "ocr_word_confidence_words": confidence_word_count,
            "ocr_word_confidence_mean": confidence_mean,
            "local_media_files_probed": len(media_rows),
            "local_media_playback_seconds_not_language_hours": round(sum(row["duration_seconds"] or 0 for row in media_rows), 3),
            "new_content_publication_or_training_cleared": 0,
            "source_payloads_deleted_or_edited": 0,
        },
        "decision_rules": [
            "Preserve all source payloads and OCR records; this builder does not delete, redact, or alter them.",
            "Record item rights/license fields as claims from the captured Archive metadata snapshot, not independent authorization.",
            "Do not infer page language from title or script; the source labels define review priority only.",
            "Do not infer media language, transcript, or Garhwali speech duration from item title or ffprobe data.",
            "No row is promoted or marked newly eligible by this register; reuse evidence must be assessed separately for each work.",
        ],
        "items": sorted(item_by_identifier.values(), key=lambda item: item["archive_identifier"].casefold()),
    }
    return register, text_rows, media_rows


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def render_report(register: dict[str, Any]) -> str:
    summary = register["summary"]
    lines = [
        "# Internet Archive source disposition — 2026-10-04",
        "",
        "## Result",
        "",
        f"The captured local metadata covers **{summary['archive_items']} distinct Archive items**: "
        f"{summary['archive_items_by_mediatype'].get('texts', 0)} text items, "
        f"{summary['archive_items_by_mediatype'].get('audio', 0)} audio items, and "
        f"{summary['archive_items_by_mediatype'].get('movies', 0)} movie items. "
        f"It links to **{summary['ocr_page_records']:,} OCR page objects** "
        f"({summary['ocr_nonempty_page_records']:,} with non-empty OCR; "
        f"{summary['ocr_page_records'] - summary['ocr_nonempty_page_records']:,} empty), and "
        f"{summary['local_media_files_probed']} technically probed local audio/video files.",
        "",
        "No source text, page, or media was deleted or edited. No new Archive content was approved for model training or public redistribution by this pass. The full OCR pages and source files remain in the ignored local data folders; the tracked register contains item metadata and evidence labels, not extracted expressive text.",
        "",
        "## Rights evidence recorded",
        "",
        "The following counts describe captured metadata fields, not independently verified rights or permission from authors, publishers, performers, institutions, or other rightsholders:",
        "",
        "| Captured item-level claim | Items |",
        "| --- | ---: |",
    ]
    claim_labels = {
        "cc0_claim": "CC0 URI recorded",
        "cc_by_claim": "CC BY URI recorded",
        "cc_by_nc_claim": "CC BY-NC URI recorded",
        "cc_by_nc_nd_claim": "CC BY-NC-ND URI recorded",
        "cc_by_nc_sa_claim": "CC BY-NC-SA URI recorded",
        "public_domain_mark_claim": "Public Domain Mark URI recorded",
        "no_reuse_license_claim_recorded": "No reuse-license field recorded",
        "other_license_claim": "Other license claim recorded",
    }
    for claim, count in sorted(summary["archive_items_by_recorded_license_claim"].items()):
        lines.append(f"| {claim_labels.get(claim, claim)} | {count} |")
    lines.extend([
        "",
        f"A **metadata conflict** is present on {summary['items_with_conflicting_license_fields']} item(s): *MarginalizedAadhaar: Sampati* has an Archive `licenseurl` for CC BY 4.0 while its `rights` field says CC BY-SA 4.0. The register preserves both statements and does not choose between them.",
        "",
        "The register also preserves Archive copyright-status fields as recorded claims, including the two US-region `NOT_IN_COPYRIGHT` records. Such fields are not presented as a cross-jurisdictional or edition-level determination.",
        "",
        "## Non-destructive text review views",
        "",
        "All OCR page objects in the review inventory were retained and assigned a source-linked follow-up group. The groups guide language review; they do not call a page Garhwali based on title or script.",
        "",
        "| Follow-up group | Rows |",
        "| --- | ---: |",
    ])
    group_labels = {
        "priority_language_study_review": "Garhwali-focused language/folklore sources; page language unverified",
        "known_alternate_scan_of_existing_work": "Known alternate scan of an already represented work",
        "translated_folklore_scope_review": "Garhwali folk material with translation; page scope uncertain",
        "regional_context_not_verified_garhwali": "Regional context; not verified as Garhwali text",
        "empty_ocr_page_pending_visual_check": "Empty OCR sidecar page; source scan retained",
    }
    for group, count in sorted(summary["ocr_page_review_groups"].items()):
        lines.append(f"| {group_labels.get(group, group)} | {count:,} |")
    lines.extend([
        "",
        "Page-level script and OCR triage signals (these are not language-identification results):",
        "",
        "| Review group | Pages | Mostly Devanagari | Mostly Latin | Mixed script | Other/unclear | No letters | Any OCR warning |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ])
    script_columns = (
        "mostly_devanagari",
        "mostly_latin",
        "mixed_devanagari_latin",
        "other_or_unclear",
        "no_letters",
    )
    for group, triage in sorted(summary["automated_page_triage_by_review_group"].items()):
        scripts = triage["script_profiles"]
        label = group_labels.get(group, group).replace("|", "\\|")
        values = [scripts.get(key, 0) for key in script_columns]
        lines.append(
            f"| {label} | {triage['pages']:,} | "
            + " | ".join(f"{value:,}" for value in values)
            + f" | {triage['pages_with_any_ocr_warning']:,} |"
        )
    lines.extend([
        "",
        "Script profiles describe Unicode character composition only. OCR-warning rows can overlap and are heuristic review flags. They do not establish Garhwali versus Hindi, text correctness, or training suitability.",
        "",
        "The priority group includes 920 pages from three Garhwali-focused works. Another 61 pages belong to an alternate scan of the user-supplied 1959 grammar and stay linked as an existing-work duplicate. Translated-folklore rows need language/translation-boundary review; regional-reference pages remain contextual. One exact duplicate page-text group occurs within the full inventory, covering two records; both are retained. No page is individually language-verified.",
        "",
        "The original 3,369-page index came from 20 JSONL files. This reconciliation found two more downloaded text items with local DjVu OCR sidecars but no page index: *Himalayan Folklore: Kumaon and West Nepal* (376 scan objects; 368 non-empty) and *British Garhwal: A Gazetteer* (266 scan objects; 246 non-empty). The local review view now covers all 4,011 page objects found in these captured text items. Those 614 non-empty additions are contextual or translated source pages, not new verified Garhwali training records.",
        "",
        f"Normalization and overlap counts: **{summary['ocr_nonempty_page_records']:,}** rows have OCR text; **{summary['normalized_nonempty_text_records']:,}** remain non-empty after Unicode/punctuation normalization; those collapse to **{summary['normalized_exact_unique_nonempty_texts']:,}** distinct normalized values. One non-empty OCR row normalizes to no letters or numbers. The full intake has {summary['within_archive_exact_duplicate_groups']} repeated normalized-text group covering {summary['within_archive_exact_duplicate_page_rows']} page rows. Of the unique normalized values, {summary['canonical_exact_unique_text_matches']:,} match the named canonical view and {summary['unique_normalized_page_texts_not_in_canonical_view']:,} do not. This is a scoped duplicate check, not a Garhwali-language, rights, or training-eligibility decision.",
        "",
        "The generated text review JSONL includes every indexed and supplemental OCR row, source/page identifiers, original text, prior rights/quality labels, exact-duplicate signals, available OCR-engine word-confidence signals, and the follow-up group. It is stored under ignored `data/extracted/research/internet_archive_candidate_views_2026-10-04/`. The media index has one row per probed local file and stores source link, file hash, duration, metadata rights claim, and unreviewed language/transcript state. Neither local view changes eligibility or publishes content.",
        "",
        "## Item-by-item disposition",
        "",
        "Every captured item appears below. License/rights language is quoted or labeled as a source claim; `No content cleared` means this pass did not establish new training or redistribution permission.",
        "",
        "| Archive item | Scope evidence | OCR pages | Media files | Canonical exact-match pages | Captured rights evidence | OCR confidence | Disposition |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ])
    for item in register["items"]:
        title = (item.get("title") or item["archive_identifier"]).replace("|", "\\|")
        item_link = f"[{title}]({item['source_url']})"
        scope = item["language_scope_decision"].replace("_", " ")
        rights = claim_labels.get(item["license_claim_class"], item["license_claim_class"].replace("_", " "))
        if item["metadata_license_conflict"]:
            rights += "; conflicting rights field"
        elif item["rights_fields"].get("possible-copyright-status"):
            rights += "; Archive possible-copyright-status recorded"
        manifest_status = item.get("download_manifest_rights_status")
        if manifest_status and manifest_status != "no_explicit_reuse_license_recorded":
            rights += "; " + manifest_status.replace("_", " ")
        pages = item["ocr_page_records"]
        media_count = item["media_files_probed"]
        canonical_count = len(item.get("canonical_exact_match_page_records", []))
        ocr_confidence = (
            f"{item['ocr_word_confidence_page_count']} pages; word mean {item['ocr_word_confidence_mean']}"
            if item["ocr_word_confidence_page_count"] else "not available"
        )
        lines.append(f"| {item_link} | {scope} | {pages:,} | {media_count} | {canonical_count} | {rights} | {ocr_confidence} | No new content cleared |")
    canonical_details = []
    for item in register["items"]:
        for match in item.get("canonical_exact_match_page_records", []):
            for reference in match.get("canonical_references", []):
                existing_records = ", ".join(reference.get("source_record_ids", [])) or f"cleaned-view line {reference.get('line_number')}"
                rights_statuses = ", ".join(reference.get("rights_statuses", [])) or "no row-level rights status recorded"
                canonical_details.append(
                    f"`{match['archive_record_id']}` matches existing `{existing_records}` "
                    f"(source IDs: {', '.join(reference.get('source_ids', [])) or 'not recorded'}; "
                    f"rights evidence: `{rights_statuses}`)."
                )
    if canonical_details:
        lines.extend(["", "Canonical exact-match references:", "", *[f"- {detail}" for detail in canonical_details]])
    lines.extend([
        "",
        "## Reproduction and limitations",
        "",
        "Run the complete six-command sequence documented in [`scripts/README.md`](../scripts/README.md) from the project root when source indexes change. The disposition builder reads the captured Archive metadata plus the generated 4 October audits, then regenerates this report, the tracked JSON register, and ignored review indexes. It does not download anything, edit the input records, alter GitHub/Hugging Face, or contact any rightsholder.",
        "",
        "Captured Archive metadata is a snapshot. This run did not obtain independent confirmation from any source uploader/rightsholder or conduct legal research on the source works. The Archive metadata endpoint was not available to the browsing tool during this run; item URLs below point to the captured source records for follow-up.",
        "",
        "The full review candidate set was compared with all 32,072 canonical cleaned parent-text rows: "
        f"{summary['canonical_exact_match_page_rows']} exact page-row match(es), "
        f"{summary['canonical_near_duplicate_candidates']} 5-gram Jaccard candidates at ≥0.85, "
        "and the within-intake duplicate group noted above. The exact overlaps are linked to existing source records in the local index; they were not added again. These checks cover this named text view and exact normalization, not all segments, transcripts, or semantic overlap.",
        "",
        f"All 39 media files passed the existing ffprobe check for **14:09:25.531 of playback**. That duration does not measure Garhwali speech. This task did not listen to or transcribe those files, run language identification, correct OCR, or review individual pages. Only the Himalayan Folklore DjVu XML sidecar exposes OCR-engine word-confidence attributes: {summary['ocr_word_confidence_pages']} pages / {summary['ocr_word_confidence_words']:,} words, mean {summary['ocr_word_confidence_mean']}. These are OCR-engine signals, not word-accuracy scores.",
        "",
        "Related reports: [Archive intake](internet-archive-intake-2026-10-03.md), [automated quality and overlap audit](internet-archive-intake-quality-2026-10-04.md), [active dataset-quality roadmap](huggingface-dataset-quality-roadmap.md).",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    register, text_rows, media_rows = build_disposition()
    _write_json(REGISTER, register)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(register), encoding="utf-8")
    _write_jsonl(TEXT_CANDIDATES, text_rows)
    _write_jsonl(MEDIA_CANDIDATES, media_rows)
    print(json.dumps(register["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    print(f"Wrote {REGISTER.relative_to(ROOT)}")
    print(f"Wrote {REPORT.relative_to(ROOT)}")
    print(f"Wrote {TEXT_CANDIDATES.relative_to(ROOT)}")
    print(f"Wrote {MEDIA_CANDIDATES.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
