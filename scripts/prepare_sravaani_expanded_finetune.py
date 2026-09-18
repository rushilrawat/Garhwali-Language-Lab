#!/usr/bin/env python3
"""Build the experimental all-human SraVaani package against the fixed benchmark."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import prepare_sravaani_finetune as package_builder


ROOT = Path(__file__).resolve().parents[1]
STRICT = ROOT / "data/processed/model_ready/splits/asr"
EXPERIMENTAL = ROOT / "data/processed/model_ready/splits/asr_experimental"
SPLITS = ROOT / "data/processed/model_ready/splits/asr_expanded_human"
OUTPUT = ROOT / "data/processed/model_ready/sravaani_expanded_human_finetune"


def read_jsonl(path: Path) -> list[dict]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def identified_speakers(rows: list[dict]) -> set[str]:
    return {
        row["speaker_id"]
        for row in rows
        if row.get("speaker_id")
        and row.get("speaker_metadata", {}).get("status", "identified")
        == "identified"
    }


def build_rows(strict_dir: Path, experimental_dir: Path) -> tuple[dict[str, list[dict]], dict]:
    fixed = {
        split: read_jsonl(strict_dir / f"{split}.jsonl")
        for split in ("validation", "test")
    }
    candidates = [
        row
        for split in ("train", "validation", "test")
        for row in read_jsonl(experimental_dir / f"{split}.jsonl")
    ]
    by_hash: dict[str, dict] = {}
    for row in candidates:
        audio_hash = row["audio_sha256"]
        if audio_hash in by_hash:
            raise ValueError(f"Duplicate experimental audio hash: {audio_hash}")
        by_hash[audio_hash] = row

    fixed_rows = fixed["validation"] + fixed["test"]
    fixed_hashes = {row["audio_sha256"] for row in fixed_rows}
    fixed_speakers = identified_speakers(fixed_rows)
    after_hash = [row for key, row in by_hash.items() if key not in fixed_hashes]
    excluded_speakers = [
        row for row in after_hash if row.get("speaker_id") in fixed_speakers
    ]
    train = [
        row for row in after_hash if row.get("speaker_id") not in fixed_speakers
    ]
    train.sort(key=lambda row: row["audio_sha256"])

    split_rows = {"train": train, **fixed}
    package_builder.audit_split_leakage(split_rows)
    audit = {
        "candidate_rows": len(candidates),
        "candidate_unique_audio_hashes": len(by_hash),
        "fixed_validation_audio_hashes": len(fixed["validation"]),
        "fixed_test_audio_hashes": len(fixed["test"]),
        "excluded_fixed_audio_hashes": len(fixed_hashes),
        "excluded_identified_speaker_rows": len(excluded_speakers),
        "training_rows": len(train),
        "training_duration_seconds": round(
            sum(row["duration_seconds"] for row in train), 6
        ),
        "training_identified_speakers": len(identified_speakers(train)),
        "training_rows_with_incomplete_speaker_identity": sum(
            row.get("speaker_metadata", {}).get("status", "identified")
            != "identified"
            for row in train
        ),
        "fixed_audio_hash_overlap": 0,
        "identified_speaker_overlap": 0,
        "experimental_reason": "speaker identity is incomplete for added rows",
    }
    return split_rows, audit


def run(
    strict: Path = STRICT,
    experimental: Path = EXPERIMENTAL,
    splits: Path = SPLITS,
    output: Path = OUTPUT,
) -> dict:
    split_rows, audit = build_rows(Path(strict), Path(experimental))
    for split, rows in split_rows.items():
        write_jsonl(Path(splits) / f"{split}.jsonl", rows)
    package = package_builder.run(Path(splits), Path(output), ROOT)
    package["run_id"] = "garhwali-sravaani-expanded-human-package-v0.1"
    package["experimental_training"] = audit
    package["benchmark_policy"] = (
        "fixed strict validation/test hashes excluded from training; known "
        "speaker overlap excluded; unknown speaker identities remain"
    )
    (Path(output) / "report.json").write_text(
        json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return package


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", type=Path, default=STRICT)
    parser.add_argument("--experimental", type=Path, default=EXPERIMENTAL)
    parser.add_argument("--splits", type=Path, default=SPLITS)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    print(json.dumps(run(**vars(args)), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
