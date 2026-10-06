#!/usr/bin/env python3
"""Check that prior public text remains available in a candidate HF package."""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import defaultdict
from pathlib import Path


TEXT_FIELDS = ("text", "release_text", "text_clean", "text_model")


def read_rows(folder: Path):
    for path in sorted(folder.glob("*.jsonl")):
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from error
                if not isinstance(row, dict):
                    raise ValueError(f"{path}:{line_number}: expected a JSON object")
                yield row


def normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def digest(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()


def text_values(row: dict) -> list[str]:
    return [
        row[field]
        for field in TEXT_FIELDS
        if isinstance(row.get(field), str) and row[field].strip()
    ]


def source_components(row: dict) -> list[dict]:
    components = row.get("provenance") or row.get("sources") or []
    if isinstance(components, dict):
        components = components.get("provenance") or []
    return [item for item in components if isinstance(item, dict)] if isinstance(components, list) else []


def audit_packages(old_package: Path, new_package: Path) -> dict:
    old_text_rows = list(read_rows(old_package / "data" / "text"))
    new_text_ids = {
        str(row["id"]) for row in read_rows(new_package / "data" / "text") if row.get("id")
    }

    new_value_hashes = set()
    catalog_values_by_source = defaultdict(set)
    for path in sorted((new_package / "data").rglob("*.jsonl")):
        family = path.relative_to(new_package / "data").parts[0]
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{line_number}: invalid JSON") from error
                for value in text_values(row):
                    normalized = normalize(value)
                    if normalized:
                        new_value_hashes.add(hashlib.sha256(normalized.encode("utf-8")).hexdigest())
                if (
                    family == "catalog"
                    and row.get("content_included") is True
                    and row.get("text_publicly_available") is True
                    and isinstance(row.get("text"), str)
                    and row["text"].strip()
                ):
                    parent_text = normalize(row["text"])
                    for component in source_components(row):
                        source_id = component.get("source_id")
                        record_id = component.get("record_id")
                        if source_id and record_id:
                            catalog_values_by_source[(str(source_id), str(record_id))].add(parent_text)

    values_with_sources = defaultdict(set)
    values_by_hash = {}
    for row in old_text_rows:
        value = row.get("text")
        if not isinstance(value, str) or not value.strip():
            continue
        value_hash = digest(value)
        values_by_hash[value_hash] = normalize(value)
        for component in source_components(row):
            source_id = component.get("source_id")
            record_id = component.get("record_id")
            if source_id and record_id:
                values_with_sources[value_hash].add((str(source_id), str(record_id)))

    exact = {
        value_hash for value_hash in values_by_hash if value_hash in new_value_hashes
    }
    contained = set()
    for value_hash, value in values_by_hash.items():
        if value_hash in exact:
            continue
        for source in values_with_sources.get(value_hash, ()):
            if any(value in parent for parent in catalog_values_by_source.get(source, ())):
                contained.add(value_hash)
                break

    unrepresented = set(values_by_hash) - exact - contained
    old_ids = {str(row["id"]) for row in old_text_rows if row.get("id")}
    try:
        old_release = json.loads((old_package / "manifest.json").read_text(encoding="utf-8")).get("release_id")
    except FileNotFoundError:
        old_release = None
    try:
        new_release = json.loads((new_package / "manifest.json").read_text(encoding="utf-8")).get("release_id")
    except FileNotFoundError:
        new_release = None

    return {
        "schema_version": "hf-release-continuity-audit-v1",
        "old_release_id": old_release,
        "new_release_id": new_release,
        "normalization": "NFKC, casefold, and whitespace collapse; content values themselves are never emitted",
        "old_text_rows": len(old_text_rows),
        "new_text_rows": len(new_text_ids),
        "old_text_rows_without_same_id_in_new_text": sum(
            1 for row in old_text_rows if row.get("id") and str(row["id"]) not in new_text_ids
        ),
        "old_unique_normalized_values": len(values_by_hash),
        "old_unique_values_exactly_present_in_new_package": len(exact),
        "old_unique_values_in_linked_public_catalog_parent": len(contained),
        "old_unique_values_unrepresented": len(unrepresented),
        "unrepresented_value_sha256": sorted(unrepresented),
        "all_old_text_values_represented": not unrepresented,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old-package", type=Path, required=True)
    parser.add_argument("--new-package", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    report = audit_packages(args.old_package, args.new_package)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
