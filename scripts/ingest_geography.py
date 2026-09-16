#!/usr/bin/env python3
"""Materialize the Garhwali geographic place-name catalog."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "research/garhwali-geography-catalog.json"
OUTPUT = ROOT / "data/extracted/geography"
DISTRICTS = {
    "Chamoli", "Dehradun", "Haridwar", "Pauri Garhwal",
    "Rudraprayag", "Tehri Garhwal", "Uttarkashi",
}
FORBIDDEN = {"text", "text_normalized", "lyrics_text", "transcript", "audio_path"}


def validate_place(row: dict) -> dict:
    required = {
        "record_id", "name", "name_local", "place_type", "districts",
        "language_relevance", "wikipedia_title", "osm_query", "evidence",
    }
    missing = sorted(required - row.keys())
    if missing:
        raise ValueError(f"{row.get('record_id', 'unknown')} missing {missing}")
    if not row["districts"] or not set(row["districts"]).issubset(DISTRICTS):
        raise ValueError(f"Unknown Garhwal district in {row['record_id']}")
    present = sorted(FORBIDDEN & row.keys())
    if present:
        raise ValueError(f"Geography metadata cannot carry corpus payload fields: {present}")
    return {
        **row,
        "division": "Garhwal",
        "wikipedia_url": "https://en.wikipedia.org/wiki/" + quote_plus(
            row["wikipedia_title"].replace(" ", "_")
        ),
        "osm_search_url": "https://www.openstreetmap.org/search?query=" + quote_plus(
            row["osm_query"]
        ),
        "coordinates": None,
        "coordinates_status": "not_added_authoritative_gazetteer_needed",
    }


def run(catalog_path: Path = CATALOG, output: Path = OUTPUT) -> dict:
    catalog = json.loads(Path(catalog_path).read_text(encoding="utf-8"))
    rows = [validate_place(row) for row in catalog["places"]]
    ids = [row["record_id"] for row in rows]
    names = [row["name"].casefold() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate geography record IDs")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate geography place names")

    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "records.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    report = {
        "catalog_id": catalog["catalog_id"],
        "records": len(rows),
        "settlements": sum(
            row["place_type"] not in {"river", "mountain_peak", "national_park", "protected_area", "reservoir", "pilgrimage_site"}
            for row in rows
        ),
        "natural_and_cultural_features": sum(
            row["place_type"] in {"river", "mountain_peak", "national_park", "protected_area", "reservoir", "pilgrimage_site"}
            for row in rows
        ),
        "districts": dict(sorted(Counter(
            district for row in rows for district in row["districts"]
        ).items())),
        "place_types": dict(sorted(Counter(row["place_type"] for row in rows).items())),
        "coordinates_present": sum(row["coordinates"] is not None for row in rows),
        "status": "place_name_and_geographic_context_layer_ready",
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
