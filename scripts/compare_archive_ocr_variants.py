#!/usr/bin/env python3
"""Compare original and alternate OCR pages without exporting either text."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_PATH = Path(
    "data/extracted/research/internet_archive_candidate_views_2026-10-04/"
    "text_review_candidates.jsonl"
)
ALTERNATE_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_alternate_ocr_2026-10-04.jsonl"
)
PAGE_MAP_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_page_section_map_2026-10-04.jsonl"
)
OUTPUT_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_ocr_comparison_2026-10-04.json"
)
SOURCE_IDS = {
    "ia_govind_chatak_gadwali_lok_gathayen_1958",
    "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976",
}


def _read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def _script_counts(text: str) -> dict[str, int]:
    counts = Counter()
    for char in text:
        if char.isalpha():
            name = unicodedata.name(char, "")
            if "DEVANAGARI" in name:
                counts["devanagari_letters"] += 1
            elif "LATIN" in name:
                counts["latin_letters"] += 1
            else:
                counts["other_letters"] += 1
        elif char.isdigit():
            counts["digits"] += 1
    return dict(counts)


def _char_ngram_jaccard(left: str, right: str, size: int = 3) -> float | None:
    left_grams = {left[i:i + size] for i in range(max(0, len(left) - size + 1))}
    right_grams = {right[i:i + size] for i in range(max(0, len(right) - size + 1))}
    if not left_grams and not right_grams:
        return None
    if not left_grams or not right_grams:
        return 0.0
    return round(len(left_grams & right_grams) / len(left_grams | right_grams), 4)


def _priority(original: str, alternate: str, ratio: float | None) -> tuple[str, str]:
    if not original and alternate:
        return "high", "alternate recovers text from an empty original OCR page"
    if not original and not alternate:
        return "high", "both OCR versions are empty; inspect scan and extraction"
    if original and not alternate:
        return "high", "alternate OCR is empty while original OCR has text"
    if ratio is not None and ratio < 0.50:
        return "high", "substantial character-sequence disagreement between OCR versions"
    if ratio is not None and ratio < 0.80:
        return "medium", "moderate character-sequence disagreement between OCR versions"
    return "low", "OCR versions are broadly similar; other warning flags may still matter"


def compare_pages(original_rows: list[dict], alternate_rows: list[dict], page_map_rows: list[dict]) -> dict:
    originals = {
        (row["source_id"], int(row["pdf_page"])): row
        for row in original_rows
        if row.get("source_id") in SOURCE_IDS and row.get("pdf_page") is not None
    }
    page_map = {
        (row["source_id"], int(row["pdf_page"])): row
        for row in page_map_rows
        if row.get("source_id") in SOURCE_IDS
    }

    comparisons = []
    for alternate_row in sorted(
        (row for row in alternate_rows if row.get("source_id") in SOURCE_IDS),
        key=lambda row: (row["source_id"], int(row["pdf_page"])),
    ):
        key = (alternate_row["source_id"], int(alternate_row["pdf_page"]))
        original_row = originals.get(key)
        original = _normalize(str(original_row.get("text_normalized") or "")) if original_row else ""
        alternate = _normalize(str(alternate_row.get("alternate_ocr_text") or ""))
        ratio = round(difflib.SequenceMatcher(None, original, alternate, autojunk=False).ratio(), 4) \
            if original and alternate else None
        priority, reason = _priority(original, alternate, ratio)
        map_row = page_map.get(key, {})
        comparisons.append({
            "source_id": key[0],
            "pdf_page": key[1],
            "candidate_record_id": alternate_row.get("candidate_record_id"),
            "original_record_present": original_row is not None,
            "section_id": map_row.get("section_id"),
            "section_assignment": map_row.get("section_assignment"),
            "printed_page_number": map_row.get("printed_page_number"),
            "original_characters": len(original),
            "alternate_characters": len(alternate),
            "character_delta_alternate_minus_original": len(alternate) - len(original),
            "normalized_sequence_similarity": ratio,
            "character_trigram_jaccard": _char_ngram_jaccard(original, alternate),
            "exact_normalized_match": bool(original and original == alternate),
            "original_script_counts": _script_counts(original),
            "alternate_script_counts": _script_counts(alternate),
            "alternate_mean_word_confidence": alternate_row.get("mean_word_confidence"),
            "original_warning_flags": alternate_row.get("existing_ocr_warning_flags", []),
            "alternate_empty": not alternate,
            "manual_inspection_priority": priority,
            "manual_inspection_reason": reason,
            "text_included": False,
        })

    by_source: dict[str, dict] = {}
    for source_id in sorted(SOURCE_IDS):
        rows = [row for row in comparisons if row["source_id"] == source_id]
        priorities = Counter(row["manual_inspection_priority"] for row in rows)
        by_source[source_id] = {
            "pages_compared": len(rows),
            "original_characters": sum(row["original_characters"] for row in rows),
            "alternate_characters": sum(row["alternate_characters"] for row in rows),
            "pages_with_alternate_text": sum(not row["alternate_empty"] for row in rows),
            "exact_normalized_matches": sum(row["exact_normalized_match"] for row in rows),
            "manual_inspection_priority_counts": dict(priorities),
        }

    return {
        "schema_version": "1.0.0",
        "method": {
            "normalization": "Unicode NFKC, casefold, and whitespace collapse",
            "similarity": "character-sequence ratio and character-trigram Jaccard",
            "interpretation": "comparison signals only; neither OCR output is treated as truth",
            "text_included": False,
        },
        "summary": {
            "pages_compared": len(comparisons),
            "original_records_missing": sum(not row["original_record_present"] for row in comparisons),
            "alternate_empty_pages": sum(row["alternate_empty"] for row in comparisons),
            "exact_normalized_matches": sum(row["exact_normalized_match"] for row in comparisons),
            "manual_inspection_priority_counts": dict(Counter(
                row["manual_inspection_priority"] for row in comparisons
            )),
            "by_source": by_source,
        },
        "pages": comparisons,
    }


def run(original_path: Path, alternate_path: Path, page_map_path: Path, output_path: Path) -> dict:
    report = compare_pages(
        _read_jsonl(original_path),
        _read_jsonl(alternate_path),
        _read_jsonl(page_map_path),
    )
    report["inputs"] = {
        "original_candidates_sha256": hashlib.sha256(original_path.read_bytes()).hexdigest(),
        "alternate_ocr_sha256": hashlib.sha256(alternate_path.read_bytes()).hexdigest(),
        "page_map_sha256": hashlib.sha256(page_map_path.read_bytes()).hexdigest(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--original", type=Path, default=ORIGINAL_PATH)
    parser.add_argument("--alternate", type=Path, default=ALTERNATE_PATH)
    parser.add_argument("--page-map", type=Path, default=PAGE_MAP_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    root = args.root.resolve()

    def resolve(path: Path) -> Path:
        return path if path.is_absolute() else root / path

    report = run(*(resolve(path) for path in (
        args.original, args.alternate, args.page_map, args.output
    )))
    print(json.dumps({"output": str(resolve(args.output)), **report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
