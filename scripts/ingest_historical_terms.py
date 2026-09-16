#!/usr/bin/env python3
"""Materialize the Garhwali historical-term metadata catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/garhwali-historical-terms.json"
OUTPUT = ROOT / "data/extracted/historical_terms"
FORBIDDEN = {"text", "text_normalized", "lyrics_text", "transcript", "audio_path"}
REQUIRED = {
    "term_id", "term", "term_local", "term_type", "period", "context_en",
    "name_variants", "source_refs",
}


def validate_term(row: dict, source_ids: set[str]) -> dict:
    missing = sorted(REQUIRED - row.keys())
    if missing:
        raise ValueError(f"{row.get('term_id', 'unknown')} missing {missing}")
    if not row["term"].strip() or not row["context_en"].strip():
        raise ValueError(f"Empty historical term or context: {row.get('term_id')}")
    unknown_sources = sorted(set(row["source_refs"]) - source_ids)
    if unknown_sources:
        raise ValueError(f"Unknown source references for {row['term_id']}: {unknown_sources}")
    forbidden = sorted(FORBIDDEN & row.keys())
    if forbidden:
        raise ValueError(f"Historical catalog cannot carry corpus payload fields: {forbidden}")
    return row


def run(catalog_path: Path = CATALOG, output: Path = OUTPUT) -> dict:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    source_ids = {source["source_id"] for source in catalog["sources"]}
    rows = [validate_term(row, source_ids) for row in catalog["terms"]]
    ids = [row["term_id"] for row in rows]
    terms = [row["term"].casefold() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate historical term IDs")
    if len(terms) != len(set(terms)):
        raise ValueError("Duplicate historical terms")

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = {
        "catalog_id": catalog["catalog_id"],
        "records": len(rows),
        "term_types": dict(sorted(Counter(row["term_type"] for row in rows).items())),
        "periods": dict(sorted(Counter(row["period"] for row in rows).items())),
        "source_refs": dict(sorted(Counter(
            source for row in rows for source in row["source_refs"]
        ).items())),
        "payload_fields_present": sorted(set().union(*(row.keys() for row in rows)) & FORBIDDEN),
        "status": "historical_term_metadata_layer_ready",
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
