"""Make a local listening batch from VAANI clips without provider transcripts."""

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl"
OUTPUT = ROOT / "data/review/vaani-no-provider-100-v0.1"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()
    candidates = []
    seen = set()
    with SOURCE.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            digest = row.get("audio_sha256")
            if not digest or digest in seen:
                continue
            seen.add(digest)
            quality = row.get("machine_transcript_quality") or {}
            duration = row.get("duration_seconds") or 0
            draft = (row.get("machine_transcript") or "").strip()
            if not (3 <= duration <= 12 and draft and quality.get("level") == "standard"):
                continue
            if quality.get("script_profile", {}).get("script") != "Deva":
                continue
            if row.get("review_status") != "machine_draft_noisy_experimental":
                continue
            path = ROOT / row["local_audio_path"]
            if not path.is_file():
                continue
            candidates.append(row)
    # Stable pseudo-random ordering avoids selecting adjacent clips from a session.
    candidates.sort(key=lambda row: hashlib.sha256(("review-v0.1:" + row["audio_sha256"]).encode()).hexdigest())
    districts = sorted({row["district"] for row in candidates})
    quotas = {district: args.count // len(districts) for district in districts}
    for district in districts[: args.count % len(districts)]:
        quotas[district] += 1
    selected = []
    speakers = set()
    for row in candidates:
        district = row["district"]
        speaker = row.get("speaker_id")
        if quotas[district] <= 0 or (speaker and speaker in speakers):
            continue
        selected.append(row)
        quotas[district] -= 1
        if speaker:
            speakers.add(speaker)
    if any(quotas.values()):
        raise RuntimeError(f"Insufficient distinct speakers: {quotas}")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    audio_dir = OUTPUT / "audio"
    audio_dir.mkdir(exist_ok=True)
    manifest = []
    for number, row in enumerate(selected, 1):
        filename = f"{number:03d}-{row['audio_sha256'][:12]}.wav"
        source = ROOT / row["local_audio_path"]
        target = audio_dir / filename
        if not target.exists():
            shutil.copyfile(source, target)
        manifest.append({
            "item_id": f"review-{number:03d}",
            "audio_file": f"audio/{filename}",
            "audio_sha256": row["audio_sha256"],
            "district": row["district"],
            "duration_seconds": row["duration_seconds"],
            "machine_draft_unverified": row["machine_transcript"],
            "corrected_transcript": "",
            "language_heard": "",
            "review_status": "pending_listen",
            "reviewer": "",
            "notes": "",
        })
    with (OUTPUT / "review.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    (OUTPUT / "README.md").write_text(
        "# VAANI listening batch: 100 clips without provider transcripts\n\n"
        "These clips are existing CC BY 4.0 VAANI audio, selected by distinct audio hash "
        "and speaker, balanced across Tehri Garhwal and Uttarkashi. The draft text is "
        "machine generated and **not a reference transcript**. This folder adds zero "
        "new recordings and zero validated training labels.\n\n"
        "Listen to each audio file, enter the exact Devanagari words heard in "
        "`corrected_transcript`, and set `review_status` to `accepted`, `unclear`, "
        "`non_garhwali`, or `reject`. Fill `language_heard`, `reviewer`, and notes when "
        "useful. Keep rejected/unclear rows for audit. Only `accepted` rows with a "
        "nonempty corrected transcript should enter supervised training; never train "
        "on `machine_draft_unverified`. Retain the original VAANI attribution and "
        "CC BY 4.0 notice for any later release. This folder stays local.\n",
        encoding="utf-8",
    )
    print(json.dumps({"output": str(OUTPUT), "rows": len(manifest), "districts": {d: sum(r["district"] == d for r in manifest) for d in districts}, "duration_seconds": round(sum(r["duration_seconds"] for r in manifest), 2)}))


if __name__ == "__main__":
    main()
