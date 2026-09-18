#!/usr/bin/env python3
"""Build a deterministic 50/50 incoming-PDF and general Garhwali train view."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_indicbert_cloud_input import from_incoming_pdf, read_jsonl

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/model_ready/splits/text"
OUTPUT = ROOT / "data/processed/model_ready/indicbert_balanced_domain"


def stable_order(row: dict) -> str:
    return hashlib.sha256(("balanced-v0.1\0" + row["segment_sha256"]).encode()).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows))


def run(input_dir: Path = INPUT, output_dir: Path = OUTPUT) -> dict:
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    train = read_jsonl(input_dir / "train.jsonl")
    pdf = [row for row in train if from_incoming_pdf(row)]
    general = sorted((row for row in train if not from_incoming_pdf(row)), key=stable_order)[:len(pdf)]
    balanced = sorted(pdf + general, key=stable_order)
    validation = read_jsonl(input_dir / "validation.jsonl")
    pdf_validation = [row for row in validation if from_incoming_pdf(row)]
    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "train.jsonl", balanced)
    write_jsonl(output_dir / "validation_general.jsonl", validation)
    write_jsonl(output_dir / "validation_pdf.jsonl", pdf_validation)
    report = {
        "run_id": "indicbert-balanced-domain-input-v0.1",
        "train_records": len(balanced), "train_pdf_records": len(pdf),
        "train_general_records": len(general),
        "general_validation_records": len(validation),
        "pdf_validation_records": len(pdf_validation),
        "test_records_written": 0, "test_used_for_training_or_selection": False,
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
