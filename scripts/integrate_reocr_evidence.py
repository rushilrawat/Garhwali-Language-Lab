#!/usr/bin/env python3
"""Apply strong multi-layout OCR consensus while preserving original OCR text."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experimental/incoming_pdfs.jsonl"
CANDIDATES = ROOT / "data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/candidates.jsonl"
REPORT = ROOT / "data/processed/evaluation/data_quality/incoming_pdf_reocr_full_v0_1/integration_report.json"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def accepted_candidate(evidence: dict) -> dict | None:
    index = evidence.get("selected_candidate_index")
    if index is None or evidence.get("exact_variant_agreement", 0) < 2:
        return None
    candidate = evidence["candidates"][index]
    text = candidate.get("text", "").strip()
    original = evidence.get("original_text", "").strip()
    confidence = candidate.get("mean_word_confidence") or 0
    ratio = len(text) / max(1, len(original))
    if confidence < 80 or not 0.5 <= ratio <= 2.0 or text == original:
        return None
    return candidate


def run(source: Path, candidates: Path, report_path: Path) -> dict:
    evidence = {row["record_id"]: row for row in read_jsonl(candidates)}
    rows = []
    promoted = 0
    for row in read_jsonl(source):
        current = dict(row)
        if row.get("reocr_evidence"):
            rows.append(current)
            promoted += 1
            continue
        item = evidence.get(row["record_id"])
        candidate = accepted_candidate(item) if item else None
        if candidate:
            original = row["text"]
            current["original_ocr_text"] = original
            current["original_ocr_text_sha256"] = row["text_sha256"]
            current["text"] = candidate["text"]
            current["text_sha256"] = hashlib.sha256(candidate["text"].encode()).hexdigest()
            current["reocr_evidence"] = {
                "dpi": item["dpi"],
                "psm": candidate["psm"],
                "mean_word_confidence": candidate["mean_word_confidence"],
                "exact_variant_agreement": item["exact_variant_agreement"],
                "original_preserved": True,
            }
            current["modifications"] = row.get("modifications", "") + "; multi-layout OCR consensus applied"
            current["quality_flags"] = sorted(set(row.get("quality_flags", [])) | {"reocr_consensus_applied"})
            promoted += 1
        rows.append(current)
    temporary = source.with_suffix(source.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    temporary.replace(source)
    report = {
        "run_id": "incoming-pdf-reocr-integration-v0.1",
        "source_records": len(rows),
        "candidate_records": len(evidence),
        "promoted_consensus_records": promoted,
        "original_ocr_preserved": True,
        "minimum_exact_layout_agreement": 2,
        "minimum_mean_word_confidence": 80,
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--candidates", type=Path, default=CANDIDATES)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.candidates, args.report), indent=2))


if __name__ == "__main__":
    main()
