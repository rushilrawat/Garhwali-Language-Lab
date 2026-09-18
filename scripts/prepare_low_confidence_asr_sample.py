#!/usr/bin/env python3
"""Build a deterministic audio sample for independent ASR agreement evidence."""

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def priority(row):
    quality = row.get("machine_transcript_quality") or {}
    flags = set(quality.get("flags") or [])
    score = 2 * len(flags)
    score += 10 if not str(row.get("machine_transcript") or "").strip() else 0
    score += 8 if quality.get("level") == "high_risk" else 0
    score += 5 if "bengali_script" in flags else 0
    score += 4 if "no_devanagari_letters" in flags else 0
    score += 3 if "implausibly_long_for_duration" in flags else 0
    return score


def build(input_path, excluded_path, output_dir, limit, offset=0):
    excluded = {
        row["audio_sha256"] for row in read_jsonl(excluded_path)
    } if Path(excluded_path).exists() else set()
    unique = {}
    for row in read_jsonl(input_path):
        digest = row["audio_sha256"]
        if digest not in excluded and digest not in unique:
            unique[digest] = row
    rows = list(unique.values())
    rows.sort(key=lambda row: (-priority(row), row["audio_sha256"]))
    selected = rows[offset:offset + limit]
    output_dir = Path(output_dir)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for row in selected:
        source = ROOT / row["local_audio_path"]
        target = audio_dir / f'{row["audio_sha256"]}.wav'
        if not target.exists():
            os.link(source, target)
        exported.append({
            "audio_sha256": row["audio_sha256"],
            "audio_path": f'audio/{target.name}',
            "duration_seconds": row.get("duration_seconds"),
            "sravaani_transcript": row.get("machine_transcript", ""),
            "sravaani_quality": row.get("machine_transcript_quality"),
            "selection_priority": priority(row),
            "district": row.get("district"),
            "gender": row.get("gender"),
        })
    selected_names = {f'{row["audio_sha256"]}.wav' for row in selected}
    for stale in audio_dir.glob("*.wav"):
        if stale.name not in selected_names:
            stale.unlink()
    (output_dir / "manifest.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in exported),
        encoding="utf-8",
    )
    report = {
        "records": len(exported),
        "selection_offset": offset,
        "excluded_existing_third_checkpoint": len(excluded),
        "selection": "lowest-confidence-first, deterministic hash tie-break",
        "total_duration_seconds": round(sum(row.get("duration_seconds") or 0 for row in exported), 3),
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--excluded", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()
    print(json.dumps(build(
        args.input, args.excluded, args.output, args.limit, args.offset
    ), indent=2))


if __name__ == "__main__":
    main()
