#!/usr/bin/env python3
"""Create an inspectable release-quality profile for split text segments."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/model_ready/splits/text"
JSON_OUT = ROOT / "research/text-release-quality-2026-09-16.json"
MD_OUT = ROOT / "research/text-release-quality-2026-09-16.md"


def read(path):
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def provenance(row):
    return [p for parent in row.get("parents", []) for p in parent.get("provenance", [])]


def percentile(values, fraction):
    values = sorted(values)
    return values[round((len(values) - 1) * fraction)] if values else 0


def run(input_dir=INPUT, json_out=JSON_OUT, md_out=MD_OUT):
    split_rows = {split: read(Path(input_dir) / f"{split}.jsonl") for split in ("train", "validation", "test")}
    sets = {split: {row["segment_sha256"] for row in rows} for split, rows in split_rows.items()}
    all_rows = [row for rows in split_rows.values() for row in rows]
    lengths = [len(row.get("text", "")) for row in all_rows]
    sources = Counter()
    missing_source = missing_rights = pdf_rows = 0
    for row in all_rows:
        records = provenance(row)
        ids = {item.get("source_id") or "unknown" for item in records}
        sources.update(ids)
        missing_source += not records or all(not item.get("source_id") for item in records)
        missing_rights += not records or all(not item.get("rights_status") for item in records)
        pdf_rows += any(str(item.get("source_pdf", "")).startswith("incoming/pdfs/") for item in records)
    checks = {
        "empty_text": sum(not row.get("text", "").strip() for row in all_rows),
        "duplicate_segment_ids_within_splits": sum(len(rows) - len(sets[split]) for split, rows in split_rows.items()),
        "train_validation_overlap": len(sets["train"] & sets["validation"]),
        "train_test_overlap": len(sets["train"] & sets["test"]),
        "validation_test_overlap": len(sets["validation"] & sets["test"]),
        "missing_source_id": missing_source,
        "missing_rights_status": missing_rights,
    }
    findings = []
    for key in ("empty_text", "duplicate_segment_ids_within_splits", "train_validation_overlap", "train_test_overlap", "validation_test_overlap"):
        findings.append({"check": key, "count": checks[key], "severity": "critical" if checks[key] else "pass"})
    findings.extend([
        {"check": "missing_source_id", "count": missing_source, "rate": missing_source / len(all_rows), "severity": "high" if missing_source else "pass"},
        {"check": "missing_rights_status", "count": missing_rights, "rate": missing_rights / len(all_rows), "severity": "medium" if missing_rights else "pass"},
    ])
    report = {
        "run_id": "garhwali-text-release-quality-v0.1",
        "grain": "one exact-unique text segment per split row",
        "records": len(all_rows),
        "splits": {split: len(rows) for split, rows in split_rows.items()},
        "incoming_pdf_records": pdf_rows,
        "length_characters": {"min": min(lengths), "median": statistics.median(lengths), "p95": percentile(lengths, .95), "max": max(lengths)},
        "distinct_sources": len(sources),
        "largest_sources": sources.most_common(20),
        "checks": checks,
        "findings": findings,
        "policy": {"records_mutated": 0, "records_deleted": 0},
    }
    Path(json_out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = ["# Text release quality audit", "", f"**Grain:** {report['grain']}", "", f"**Records:** {len(all_rows):,}", "", "## Split and integrity checks", "", "| Check | Count | Status |", "| --- | ---: | --- |"]
    for finding in findings:
        lines.append(f"| {finding['check']} | {finding['count']:,} | {finding['severity']} |")
    lines += ["", "## Coverage", "", f"- Incoming-PDF segments: **{pdf_rows:,}**", f"- Distinct source identifiers: **{len(sources):,}**", f"- Character length: median **{statistics.median(lengths):,.0f}**, p95 **{percentile(lengths, .95):,}**, maximum **{max(lengths):,}**", "", "No record was changed or removed. Model-backed semantic and language/noise audits remain additive review evidence.", ""]
    Path(md_out).write_text("\n".join(lines), encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
