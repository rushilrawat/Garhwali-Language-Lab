#!/usr/bin/env python3
"""Validate and materialize university and scholarly Garhwali resources."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/garhwali-university-research-catalog.json"
OUTPUT = ROOT / "data/extracted/university_research"
VALID_STATUSES = {"bibliographic_metadata", "research_context_extracted", "already_ingested"}
REQUIRED = {
    "record_id", "title", "creators", "institution", "year", "resource_type",
    "topics", "language_scope", "source_url", "source_authority", "access_level",
    "ingestion_status", "already_covered_by", "visibility", "notes",
}


def validate_record(row: dict) -> dict:
    missing = sorted(REQUIRED - row.keys())
    if missing:
        raise ValueError(f"{row.get('record_id', 'unknown')} missing {missing}")
    if not row["record_id"].startswith("university-research:"):
        raise ValueError(f"Invalid research record ID: {row['record_id']}")
    if not row["title"].strip() or not row["institution"].strip():
        raise ValueError(f"Blank title or institution: {row['record_id']}")
    if row["ingestion_status"] not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {row['record_id']}")
    if row["visibility"] != "catalogued" or not row["source_url"].startswith("https://"):
        raise ValueError(f"Research source must be visible and HTTPS: {row['record_id']}")
    if row["ingestion_status"] == "already_ingested" and not row["already_covered_by"]:
        raise ValueError(f"Missing deduplication pointer: {row['record_id']}")
    return row


def run(catalog_path: Path = CATALOG, output: Path = OUTPUT) -> dict:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rows = [validate_record(row) for row in catalog["records"]]
    ids = [row["record_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate university/research record IDs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    report = {
        "catalog_id": catalog["catalog_id"],
        "records": len(rows),
        "institutions": len({row["institution"] for row in rows}),
        "resource_types": dict(sorted(Counter(row["resource_type"] for row in rows).items())),
        "access_levels": dict(sorted(Counter(row["access_level"] for row in rows).items())),
        "already_covered_records": sum(row["ingestion_status"] == "already_ingested" for row in rows),
        "hidden_records": 0,
        "status": "university_research_catalog_ready",
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
