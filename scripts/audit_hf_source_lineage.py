#!/usr/bin/env python3
"""Compare upstream source records with source-linked Hugging Face text rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_ID = "indic_dialect_asr_gbm"
DEFAULT_SOURCE_FILE = ROOT / "experimental/indic_dialect_asr_gbm.jsonl"
DEFAULT_TEXT_DIR = (
    ROOT
    / "data/huggingface/garhwali-language-lab-v0.2.5-staging/data/text"
)


def read_jsonl(path: Path):
    with Path(path).open(encoding="utf-8") as handle:
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


def source_components(row):
    values = row.get("provenance") or row.get("sources") or []
    if isinstance(values, dict):
        values = values.get("provenance") or []
    return values if isinstance(values, list) else []


def build_report(source_id, source_rows, view_rows):
    source_records = {}
    upstream_sources = Counter()
    licenses = Counter()
    rights_statuses = Counter()
    for row in source_rows:
        if row.get("source_id") != source_id:
            continue
        record_id = row.get("record_id")
        if not record_id:
            raise ValueError(f"{source_id}: upstream record is missing record_id")
        if record_id in source_records:
            raise ValueError(f"{source_id}: duplicate upstream record_id {record_id}")
        source_records[record_id] = row
        upstream_sources[str(row.get("upstream_source") or "not_recorded")] += 1
        licenses[str(row.get("license_id") or "not_recorded")] += 1
        rights_statuses[str(row.get("rights_status") or "not_recorded")] += 1

    linked_rows = 0
    rows_by_split = Counter()
    record_to_rows = defaultdict(set)
    view_to_records = defaultdict(set)
    unknown_records = set()
    seen_view_ids = set()

    for row in view_rows:
        components = [
            item
            for item in source_components(row)
            if isinstance(item, dict) and item.get("source_id") == source_id
        ]
        if not components:
            continue
        view_id = (
            row.get("id")
            or row.get("segment_sha256")
            or row.get("text_sha256")
        )
        if not view_id:
            raise ValueError(f"{source_id}: linked view row is missing id")
        if view_id in seen_view_ids:
            raise ValueError(f"{source_id}: duplicate view row id {view_id}")
        seen_view_ids.add(view_id)
        linked_rows += 1
        rows_by_split[str(row.get("split") or "not_recorded")] += 1
        for item in components:
            record_id = item.get("record_id")
            if not record_id:
                raise ValueError(f"{source_id}: linked view row has a source without record_id")
            view_to_records[view_id].add(record_id)
            if record_id not in source_records:
                unknown_records.add(record_id)
            else:
                record_to_rows[record_id].add(view_id)

    fanout_histogram = Counter(
        len(record_to_rows.get(record_id, set())) for record_id in source_records
    )
    unlinked = sorted(set(source_records) - set(record_to_rows))
    return {
        "schema_version": "hf-source-lineage-audit-v1",
        "source_id": source_id,
        "upstream_source_rows": len(source_records),
        "upstream_source_rows_by_origin": dict(sorted(upstream_sources.items())),
        "upstream_source_rows_by_license": dict(sorted(licenses.items())),
        "upstream_source_rows_by_rights_status": dict(sorted(rights_statuses.items())),
        "view_rows_with_source": linked_rows,
        "view_rows_by_split": dict(sorted(rows_by_split.items())),
        "distinct_source_record_ids_linked": len(record_to_rows),
        "distinct_source_record_links": sum(
            len(rows) for rows in record_to_rows.values()
        ),
        "source_records_with_fanout": sum(
            len(rows) > 1 for rows in record_to_rows.values()
        ),
        "source_record_fanout_histogram": {
            str(count): fanout_histogram.get(count, 0)
            for count in range(max(fanout_histogram, default=0) + 1)
        },
        "view_rows_with_multiple_source_records": sum(
            len(records) > 1 for records in view_to_records.values()
        ),
        "unlinked_source_record_count": len(unlinked),
        "unlinked_source_record_ids": unlinked,
        "unknown_view_source_record_ids": sorted(unknown_records),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-id", default=DEFAULT_SOURCE_ID)
    parser.add_argument("--source-file", type=Path, default=DEFAULT_SOURCE_FILE)
    parser.add_argument("--text-dir", type=Path, default=DEFAULT_TEXT_DIR)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    source_rows = list(read_jsonl(args.source_file))
    view_rows = (
        row
        for path in sorted(args.text_dir.glob("*.jsonl"))
        for row in read_jsonl(path)
    )
    report = build_report(args.source_id, source_rows, view_rows)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
