#!/usr/bin/env python3
"""Build split-safe incoming-PDF train/validation manifests for domain adaptation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_indicbert_cloud_input import from_incoming_pdf, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/model_ready/splits/text"
OUTPUT = ROOT / "data/processed/model_ready/indicbert_pdf_domain"


def digest(rows: list[dict]) -> str:
    value = "\n".join(row["segment_sha256"] for row in rows).encode()
    return hashlib.sha256(value).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def run(input_dir: Path = INPUT, output_dir: Path = OUTPUT) -> dict:
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    selected = {
        split: [
            row for row in read_jsonl(input_dir / f"{split}.jsonl")
            if from_incoming_pdf(row)
        ]
        for split in ("train", "validation", "test")
    }
    hashes = {split: {row["segment_sha256"] for row in rows} for split, rows in selected.items()}
    overlap = {
        "train_validation": len(hashes["train"] & hashes["validation"]),
        "train_test": len(hashes["train"] & hashes["test"]),
        "validation_test": len(hashes["validation"] & hashes["test"]),
    }
    if any(overlap.values()):
        raise ValueError("Incoming-PDF domain splits overlap")
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "train.jsonl", selected["train"])
    write_jsonl(output_dir / "validation.jsonl", selected["validation"])
    report = {
        "run_id": "indicbert-pdf-domain-input-v0.1",
        "records": {split: len(rows) for split, rows in selected.items()},
        "digests": {split: digest(rows) for split, rows in selected.items()},
        "segment_hash_overlap": overlap,
        "test_records_written": 0,
        "test_used_for_training_or_selection": False,
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output), indent=2))


if __name__ == "__main__":
    main()
