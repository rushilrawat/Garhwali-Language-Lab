#!/usr/bin/env python3
"""Summarize language-focused Internet Archive OCR candidates without exporting text."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_archive_corpus_overlap import normalize_text, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = Path(
    "data/extracted/research/internet_archive_candidate_views_2026-10-04/"
    "text_review_candidates.jsonl"
)
OUTPUT_PATH = Path(
    "data/extracted/research/internet_archive_priority_language_evidence_2026-10-04.json"
)

SOURCE_GROUPS = {
    "priority_language_study_review": {
        "ia_govind_chatak_gadwali_lok_gathayen_1958",
        "ia_gunanand_juyal_madhya_pahadi_1967",
        "ia_haridatta_bhatta_garhwali_bhasha_sahitya_1976",
    },
    "translated_folklore_scope_review": {
        "ia_himalayan_folklore_1935",
        "ia_ns_bhandari_snow_balls_garhwal_1946",
    },
}


def summarize_rows(rows: list[dict]) -> dict:
    """Return aggregate signals and duplicate IDs only; never return OCR text."""
    selected_ids = set().union(*SOURCE_GROUPS.values())
    selected = [row for row in rows if row.get("source_id") in selected_ids]
    per_source: dict[str, list[dict]] = defaultdict(list)
    for row in selected:
        per_source[str(row["source_id"])].append(row)

    source_summaries = {}
    group_rows: dict[str, list[dict]] = defaultdict(list)
    for source_id in sorted(selected_ids):
        source_rows = per_source.get(source_id, [])
        nonempty = [
            row for row in source_rows
            if str(row.get("text_normalized") or row.get("text") or "").strip()
        ]
        normalized_rows: dict[str, list[dict]] = defaultdict(list)
        normalization_empty_ids = []
        for row in nonempty:
            normalized = normalize_text(row.get("text_normalized") or row.get("text"))
            if normalized:
                normalized_rows[normalized].append(row)
            else:
                normalization_empty_ids.append(str(row.get("record_id") or ""))
        duplicates = [members for members in normalized_rows.values() if len(members) > 1]
        first = source_rows[0] if source_rows else {}
        source_summaries[source_id] = {
            "candidate_group": first.get("archive_review_candidate_group"),
            "archive_identifier": first.get("archive_identifier"),
            "source_url": first.get("source_url"),
            "page_objects": len(source_rows),
            "nonempty_ocr_rows": len(nonempty),
            "empty_ocr_rows": len(source_rows) - len(nonempty),
            "ocr_characters": sum(
                len(str(row.get("text_normalized") or row.get("text") or ""))
                for row in nonempty
            ),
            "script_profiles": dict(Counter(
                row.get("automated_page_triage", {}).get("script_profile", "missing")
                for row in nonempty
            )),
            "rows_with_ocr_warning": sum(bool(
                row.get("automated_page_triage", {}).get("warning_flags")
            ) for row in source_rows),
            "recorded_rights_statuses": dict(Counter(
                str(row.get("rights_status") or "unrecorded") for row in source_rows
            )),
            "recorded_license_claims": dict(Counter(
                str(row.get("archive_license_claim") or "none_recorded")
                for row in source_rows
            )),
            "normalized_unique_nonempty_values": len(normalized_rows),
            "rows_normalizing_to_empty": len(normalization_empty_ids),
            "normalization_empty_record_ids": sorted(normalization_empty_ids),
            "normalized_duplicate_groups": [
                sorted(str(member.get("record_id") or "") for member in members)
                for members in duplicates
            ],
            "training_eligible_rows": sum(bool(row.get("training_eligible")) for row in source_rows),
            "public_redistribution_eligible_rows": sum(
                bool(row.get("public_redistribution_eligible")) for row in source_rows
            ),
        }
        group = first.get("archive_review_candidate_group")
        if group in SOURCE_GROUPS:
            group_rows[str(group)].extend(source_rows)

    groups = {}
    for group, group_items in group_rows.items():
        nonempty = [
            row for row in group_items
            if str(row.get("text_normalized") or row.get("text") or "").strip()
        ]
        normalized_rows: dict[str, list[dict]] = defaultdict(list)
        normalization_empty_ids = []
        for row in nonempty:
            normalized = normalize_text(row.get("text_normalized") or row.get("text"))
            if normalized:
                normalized_rows[normalized].append(row)
            else:
                normalization_empty_ids.append(str(row.get("record_id") or ""))
        duplicate_groups = [members for members in normalized_rows.values() if len(members) > 1]
        groups[group] = {
            "page_objects": len(group_items),
            "nonempty_ocr_rows": len(nonempty),
            "empty_ocr_rows": len(group_items) - len(nonempty),
            "normalized_unique_nonempty_values": len(normalized_rows),
            "rows_normalizing_to_empty": len(normalization_empty_ids),
            "normalization_empty_record_ids": sorted(normalization_empty_ids),
            "normalized_duplicate_groups": [
                sorted(str(member.get("record_id") or "") for member in members)
                for members in duplicate_groups
            ],
        }

    return {
        "schema_version": "1.0.0",
        "audit_date": "2026-10-04",
        "purpose": "Source-scoped language/genre and text-integrity evidence; not a Garhwali classifier or rights clearance.",
        "input_rows": len(rows),
        "groups": groups,
        "sources": source_summaries,
        "limits": [
            "Unicode script composition does not distinguish Garhwali from Hindi or identify a page's language.",
            "OCR warning flags are heuristics, not measured OCR accuracy.",
            "Rights and license fields reproduce recorded claims; they do not establish authority or permission.",
            "No expressive OCR text is written to this audit output.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    source = args.root / args.input
    if not source.is_file():
        raise FileNotFoundError(f"Local candidate view is missing: {source}")
    result = summarize_rows(read_jsonl(source))
    output = args.root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "groups": result["groups"],
        "source_count": len(result["sources"]),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
