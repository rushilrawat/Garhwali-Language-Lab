#!/usr/bin/env python3
"""Validate and materialize the Garhwali literary-people catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/garhwali-literary-people-catalog.json"
OUTPUT = ROOT / "data/extracted/literary_people"
FORBIDDEN = {"text", "text_normalized", "lyrics_text", "transcript", "audio_path"}
REQUIRED = {
    "person_id", "canonical_name", "aliases", "roles", "associated_works",
    "source_ids", "verification_status", "notes",
}


def validate_person(row: dict, source_ids: set[str]) -> dict:
    missing = sorted(REQUIRED - row.keys())
    if missing:
        raise ValueError(f"{row.get('person_id', 'unknown')} missing {missing}")
    if not row["person_id"].startswith("literary-person:") or not row["canonical_name"].strip():
        raise ValueError(f"Invalid literary person: {row.get('person_id')}")
    if not row["roles"] or not row["source_ids"] or not set(row["source_ids"]) <= source_ids:
        raise ValueError(f"Invalid roles or sources: {row['person_id']}")
    if FORBIDDEN & row.keys():
        raise ValueError(f"Literary people catalog contains corpus payload: {row['person_id']}")
    return row


def run(catalog_path: Path = CATALOG, output: Path = OUTPUT) -> dict:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    source_ids = {source["source_id"] for source in catalog["sources"]}
    rows = [validate_person(row, source_ids) for row in catalog["people"]]
    ids = [row["person_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate literary person IDs")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8"
    )
    report = {
        "catalog_id": catalog["catalog_id"],
        "records": len(rows),
        "verification_statuses": dict(sorted(Counter(row["verification_status"] for row in rows).items())),
        "roles": dict(sorted(Counter(role for row in rows for role in row["roles"]).items())),
        "hidden_records": 0,
        "status": "literary_people_catalog_ready",
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
