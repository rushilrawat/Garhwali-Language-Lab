#!/usr/bin/env python3
"""Audit the current split-safe IndicBERT continuation input."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data/processed/model_ready/splits/text"
OUTPUT = ROOT / "data/processed/evaluation/controlled_modeling/indicbert_cloud_input.json"
SPLITS = ("train", "validation", "test")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def from_incoming_pdf(row: dict) -> bool:
    return any(
        provenance.get("source_pdf", "").startswith("incoming/pdfs/")
        for parent in row.get("parents", [])
        for provenance in parent.get("provenance", [])
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def run(input_dir: Path = INPUT, output: Path = OUTPUT, expected_pdf_segments: int = 27926) -> dict:
    input_dir = Path(input_dir)
    rows = {split: read_jsonl(input_dir / f"{split}.jsonl") for split in SPLITS}
    hashes = {
        split: {row["segment_sha256"] for row in values}
        for split, values in rows.items()
    }
    overlaps = {
        f"{left}_{right}": len(hashes[left] & hashes[right])
        for index, left in enumerate(SPLITS)
        for right in SPLITS[index + 1:]
    }
    pdf_counts = {
        split: sum(from_incoming_pdf(row) for row in values)
        for split, values in rows.items()
    }
    if any(overlaps.values()):
        raise ValueError("IndicBERT text splits overlap by segment hash")
    if sum(pdf_counts.values()) != expected_pdf_segments:
        raise ValueError(
            f"Expected {expected_pdf_segments} incoming-PDF segments; "
            f"found {sum(pdf_counts.values())}"
        )
    report = {
        "run_id": "indicbertv2-cloud-continuation-input-v0.3",
        "splits": {split: len(values) for split, values in rows.items()},
        "incoming_pdf_segments": pdf_counts,
        "incoming_pdf_segments_total": sum(pdf_counts.values()),
        "incoming_pdf_test_segments_excluded_from_training": pdf_counts["test"],
        "segment_hash_overlap": overlaps,
        "manifests": {
            split: {
                "path": display_path(input_dir / f"{split}.jsonl"),
                "sha256": sha256_file(input_dir / f"{split}.jsonl"),
            }
            for split in SPLITS
        },
        "selection_split": "validation",
        "test_used_for_training_or_selection": False,
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--expected-pdf-segments", type=int, default=27926)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output, args.expected_pdf_segments), indent=2))


if __name__ == "__main__":
    main()
