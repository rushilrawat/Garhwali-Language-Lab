#!/usr/bin/env python3
"""Validate and materialize the Garhwali literary-works catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/garhwali-literary-works-catalog.json"
OUTPUT = ROOT / "data/extracted/literary_works"

REQUIRED_FIELDS = {
    "record_id",
    "title",
    "title_variants",
    "creators",
    "work_type",
    "date_or_period",
    "language_scope",
    "ingestion_status",
    "source_ids",
    "notes",
}
FORBIDDEN_PAYLOAD_FIELDS = {
    "audio_path",
    "full_text",
    "lyrics_text",
    "text",
    "text_normalized",
    "transcript",
}
VALID_STATUSES = {
    "bibliographic_metadata",
    "existing_extracted_evidence",
    "source_catalogued_no_payload",
}


def validate_work(row: dict, source_ids: set[str]) -> dict:
    missing = sorted(REQUIRED_FIELDS - row.keys())
    if missing:
        raise ValueError(f"{row.get('record_id', 'unknown')} missing {missing}")
    forbidden = sorted(FORBIDDEN_PAYLOAD_FIELDS & row.keys())
    if forbidden:
        raise ValueError(
            f"{row['record_id']} contains unverified payload fields: {forbidden}"
        )
    if not row["record_id"].startswith("literary-work:"):
        raise ValueError(f"Invalid record ID: {row['record_id']}")
    if not row["title"].strip():
        raise ValueError(f"Blank title: {row['record_id']}")
    if row["ingestion_status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid ingestion status: {row['record_id']}")
    if not row["source_ids"] or not set(row["source_ids"]) <= source_ids:
        raise ValueError(f"Unknown or missing source: {row['record_id']}")
    return row


def run(catalog_path: Path = CATALOG, output: Path = OUTPUT) -> dict:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    sources = catalog["sources"]
    source_ids = {source["source_id"] for source in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Duplicate source IDs")

    rows = [validate_work(row, source_ids) for row in catalog["works"]]
    record_ids = [row["record_id"] for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("Duplicate literary-work record IDs")

    title_creator_keys = [
        (
            row["title"].casefold().strip(),
            tuple(creator.casefold().strip() for creator in row["creators"]),
        )
        for row in rows
    ]
    if len(title_creator_keys) != len(set(title_creator_keys)):
        raise ValueError("Duplicate literary-work title/creator keys")

    covered_ids = set(catalog["capture_coverage"]["resolved_work_ids"])
    if covered_ids != set(record_ids):
        missing = sorted(set(record_ids) - covered_ids)
        extra = sorted(covered_ids - set(record_ids))
        raise ValueError(f"Capture coverage mismatch; missing={missing}, extra={extra}")

    unresolved = catalog["capture_coverage"]["unresolved_mentions"]
    unresolved_ids = [row["mention_id"] for row in unresolved]
    if len(unresolved_ids) != len(set(unresolved_ids)):
        raise ValueError("Duplicate unresolved mention IDs")

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = {
        "catalog_id": catalog["catalog_id"],
        "records": len(rows),
        "work_types": dict(sorted(Counter(row["work_type"] for row in rows).items())),
        "ingestion_statuses": dict(
            sorted(Counter(row["ingestion_status"] for row in rows).items())
        ),
        "named_genres": len(catalog["capture_coverage"]["named_genres"]),
        "unresolved_mentions": len(unresolved),
        "unresolved_details": unresolved,
        "payload_records_added": 0,
        "status": "all_named_works_in_capture_catalogued",
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.catalog, args.output), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
