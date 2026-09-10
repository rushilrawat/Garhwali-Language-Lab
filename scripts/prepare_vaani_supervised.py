#!/usr/bin/env python3
"""Create model-preparation views from the verified VAANI manifests."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VAANI = ROOT / "data" / "vaani"
OUT = ROOT / "data" / "processed" / "vaani"


def normalize_transcript(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def selected_transcript(row: dict) -> str:
    return normalize_transcript(row.get("canonical_transcript") or row.get("transcript") or "")


def has_bengali_script(text: str) -> bool:
    return any("\u0980" <= char <= "\u09ff" for char in text)


def quality_decision(row: dict, transcript: str) -> dict:
    flags = list(dict.fromkeys(row.get("quality_flags", [])))
    if has_bengali_script(transcript) and "bengali-script-under-garhwali-label" not in flags:
        flags.append("bengali-script-under-garhwali-label")
    if not transcript:
        flags.append("empty-transcript")
    return {
        "quality_flags": flags,
        "recommended_for_supervised_training": bool(transcript) and not flags,
    }


def supervised_split(row: dict, transcription_rows: dict[str, dict]) -> str:
    transcription = transcription_rows.get(row["audio_path"])
    if not transcription or not transcription.get("split"):
        raise KeyError(f"Missing transcription split for {row['audio_path']}")
    return transcription["split"]


def write_jsonl(path: Path, rows) -> int:
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def prepared_supervised(path: Path, transcription_rows: dict[str, dict]):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            transcript = selected_transcript(row)
            decision = quality_decision(row, transcript)
            authoritative_split = supervised_split(row, transcription_rows)
            yield {
                **row,
                "main_split": row.get("main_split", row.get("split") if row.get("main_config_status") != "absent-from-current-main-config" else None),
                "transcription_split": authoritative_split,
                "split": authoritative_split,
                "selected_transcript": transcript,
                "selected_transcript_sha256": hashlib.sha256(transcript.encode()).hexdigest(),
                **decision,
            }


def untranscribed(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if selected_transcript(row):
                continue
            yield {
                "audio_path": row["audio_path"],
                "local_audio_path": row["local_audio_path"],
                "audio_sha256": row["audio_sha256"],
                "duration_seconds": row["duration_seconds"],
                "district": row.get("district"),
                "gender": row.get("gender"),
                "speaker_id": row.get("speaker_id"),
                "license": row.get("license"),
                "language": row.get("language"),
                "languages_known": row.get("languages_known"),
                "state": row.get("state"),
                "stay_years": row.get("stay_years"),
                "source": row.get("source"),
                "config": row.get("config"),
                "utterance_sequence_id": row.get("utterance_sequence_id"),
                "transcript_status": "untranscribed",
            }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    transcription_rows = {
        row["audio_path"]: row
        for row in (json.loads(line) for line in (VAANI / "garhwali-transcriptions.jsonl").open())
    }
    supervised_rows = list(prepared_supervised(
        VAANI / "canonical-supervised-manifest.jsonl", transcription_rows
    ))
    supervised_count = write_jsonl(OUT / "supervised.jsonl", supervised_rows)
    quarantine = [row for row in supervised_rows if not row["recommended_for_supervised_training"]]
    quarantine_count = write_jsonl(OUT / "quarantine.jsonl", quarantine)
    untranscribed_count = write_jsonl(
        OUT / "untranscribed.jsonl", untranscribed(VAANI / "canonical-full-manifest.jsonl")
    )
    report = {
        "supervised_rows": supervised_count,
        "recommended_supervised_rows": supervised_count - quarantine_count,
        "quarantine_rows": quarantine_count,
        "untranscribed_rows": untranscribed_count,
        "bengali_script_rows": sum(has_bengali_script(row["selected_transcript"]) for row in supervised_rows),
        "quality_flags": dict(sorted(Counter(flag for row in supervised_rows for flag in row["quality_flags"]).items())),
        "split_rows": dict(sorted(Counter(row["split"] for row in supervised_rows).items())),
        "supervised_duration_hours": sum(row["duration_seconds"] for row in supervised_rows) / 3600,
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
