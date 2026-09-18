#!/usr/bin/env python3
"""Attach completed Whisper agreement evidence without changing transcripts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl"
OUTPUT = ROOT / "data/processed/model_ready/transcripts/machine_drafts_sravaani_verified.jsonl"
REPORT = OUTPUT.with_name("machine_drafts_sravaani_verified_report.json")
EVIDENCE_GLOB = "low_confidence_whisper_turbo*/cloud_output/predictions.jsonl"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def load_evidence(directory: Path) -> tuple[dict[str, dict], list[str]]:
    evidence = {}
    paths = sorted(directory.glob(EVIDENCE_GLOB))
    for path in paths:
        for row in read_jsonl(path):
            digest = row["audio_sha256"]
            if digest in evidence:
                raise ValueError(f"Duplicate Whisper evidence for {digest}")
            evidence[digest] = row
    labels = []
    for path in paths:
        try:
            labels.append(str(path.relative_to(ROOT)))
        except ValueError:
            labels.append(str(path))
    return evidence, labels


def evidence_view(row: dict) -> dict:
    return {
        "model_id": "openai/whisper-large-v3-turbo",
        "model_revision": "41f01f3fe87f28c78e2fbf8b568835947dd65ed9",
        "transcript": row["whisper_transcript"],
        "agreement_wer": row["agreement_wer"],
        "agreement_cer": row["agreement_cer"],
        "exact_agreement": row["agreement_cer"] == 0,
        "human_reference_available": False,
        "automatic_transcript_replacement": False,
    }


def run(base: Path, evidence_dir: Path, output: Path, report_path: Path) -> dict:
    evidence, paths = load_evidence(evidence_dir)
    matched = set()
    output.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    with output.open("w", encoding="utf-8") as handle:
        for row in read_jsonl(base):
            digest = row["audio_sha256"]
            enriched = dict(row)
            if digest in evidence:
                enriched["independent_asr_evidence"] = evidence_view(evidence[digest])
                matched.add(digest)
            handle.write(json.dumps(enriched, ensure_ascii=False, sort_keys=True) + "\n")
            records += 1
    missing = set(evidence) - matched
    if missing:
        raise ValueError(f"Whisper evidence missing from base corpus: {len(missing)}")
    report = {
        "run_id": "sravaani-whisper-turbo-evidence-integration-v0.1",
        "records": records,
        "evidence_records": len(evidence),
        "evidence_files": paths,
        "exact_agreement_records": sum(
            row["agreement_cer"] == 0 for row in evidence.values()
        ),
        "original_transcripts_changed": 0,
        "policy": "Independent ASR evidence only; source transcripts are preserved.",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--evidence-dir", type=Path,
                        default=ROOT / "data/processed/evaluation/asr")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(run(args.base, args.evidence_dir, args.output, args.report), indent=2))


if __name__ == "__main__":
    main()
