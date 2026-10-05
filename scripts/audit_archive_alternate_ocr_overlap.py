#!/usr/bin/env python3
"""Compare local alternate Archive OCR against the canonical cleaned text view."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_archive_corpus_overlap import audit_overlap, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
ALTERNATE_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_alternate_ocr_2026-10-04.jsonl"
)
CORPUS_PATH = Path("data/processed/model_ready/cleaned/text.jsonl")
OUTPUT_PATH = Path(
    "data/extracted/research/archive_chatak_shailesh_alternate_ocr_overlap_2026-10-04.json"
)


def audit_alternates(alternate_rows: list[dict], corpus_rows: list[dict]) -> dict:
    archive_rows = [
        {
            "record_id": f"{row['source_id']}:page:{int(row['pdf_page']):04d}:tesseract-hin-eng",
            "source_id": row["source_id"],
            "text": row.get("alternate_ocr_text", ""),
        }
        for row in alternate_rows
    ]
    return audit_overlap(archive_rows, corpus_rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--alternate", type=Path, default=ALTERNATE_PATH)
    parser.add_argument("--corpus", type=Path, default=CORPUS_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    root = args.root.resolve()
    alternate_path = args.alternate if args.alternate.is_absolute() else root / args.alternate
    corpus_path = args.corpus if args.corpus.is_absolute() else root / args.corpus
    output_path = args.output if args.output.is_absolute() else root / args.output

    alternate_rows = read_jsonl(alternate_path)
    corpus_rows = read_jsonl(corpus_path)
    report = audit_alternates(alternate_rows, corpus_rows)
    report["input_hashes"] = {
        "alternate_ocr_sha256": hashlib.sha256(alternate_path.read_bytes()).hexdigest(),
        "canonical_cleaned_text_sha256": hashlib.sha256(corpus_path.read_bytes()).hexdigest(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(output_path),
        "archive_rows": report["archive_rows"],
        "canonical_corpus_rows": report["canonical_corpus_rows"],
        "exact_match_rows": report["exact"]["normalized_match_rows"],
        "within_archive_duplicate_groups": report["exact"]["within_archive_duplicate_groups"],
        "near_duplicate_threshold_pairs": report["near_duplicate"]["threshold_pairs"],
        "near_duplicate_pairs_scored": report["near_duplicate"]["candidate_pairs_scored"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
