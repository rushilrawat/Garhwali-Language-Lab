#!/usr/bin/env python3
"""Verify the complete local VAANI Garhwali collection."""

from __future__ import annotations

from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import wave

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vaani"


def rows(name: str):
    return [json.loads(line) for line in (DATA / name).open(encoding="utf-8")]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_audio(items):
    seconds = 0.0
    sample_rates = Counter()
    channels = Counter()
    sample_widths = Counter()
    total_bytes = 0
    for index, item in enumerate(items, 1):
        path = ROOT / item["local_path"]
        if path.stat().st_size != item["bytes"] or sha256(path) != item["sha256"]:
            raise RuntimeError(f"Audio integrity failure: {path}")
        with wave.open(str(path), "rb") as wav:
            seconds += wav.getnframes() / wav.getframerate()
            sample_rates[wav.getframerate()] += 1
            channels[wav.getnchannels()] += 1
            sample_widths[wav.getsampwidth()] += 1
        total_bytes += path.stat().st_size
        if index % 20000 == 0:
            print(f"verified {index}/{len(items)} WAVs", flush=True)
    return {
        "files": len(items), "bytes": total_bytes, "duration_seconds_from_wav_headers": seconds,
        "duration_hours_from_wav_headers": seconds / 3600,
        "sample_rates": dict(sorted(sample_rates.items())), "channels": dict(sorted(channels.items())),
        "sample_width_bytes": dict(sorted(sample_widths.items())),
    }


def verify_images(items):
    formats = Counter()
    total_bytes = 0
    for item in items:
        path = ROOT / item["local_path"]
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise RuntimeError(f"Image integrity failure: {path}")
        with Image.open(io.BytesIO(payload)) as image:
            image.verify()
            formats[image.format] += 1
        total_bytes += len(payload)
    return {"files": len(items), "bytes": total_bytes, "formats": dict(sorted(formats.items()))}


def main():
    main_audio = rows("audio-local-manifest.jsonl")
    extra_audio = rows("transcription-only-audio-manifest.jsonl")
    images = rows("reference-image-manifest.jsonl")
    full = rows("canonical-full-manifest.jsonl")
    supervised = rows("canonical-supervised-manifest.jsonl")
    if (len(main_audio), len(extra_audio), len(images), len(full), len(supervised)) != (110410, 26, 4506, 110410, 5894):
        raise RuntimeError("Manifest row-count verification failed")
    report = {
        "main_audio": verify_audio(main_audio),
        "transcription_only_audio": verify_audio(extra_audio),
        "reference_images": verify_images(images),
        "canonical_full_rows": len(full),
        "canonical_supervised_rows": len(supervised),
        "canonical_full_missing_local_audio": sum(not (ROOT / row["local_audio_path"]).is_file() for row in full),
        "canonical_full_missing_local_image": sum(not (ROOT / row["local_reference_image_path"]).is_file() for row in full),
        "canonical_supervised_missing_local_audio": sum(not (ROOT / row["local_audio_path"]).is_file() for row in supervised),
        "canonical_supervised_missing_local_image": sum(not (ROOT / row["local_reference_image_path"]).is_file() for row in supervised),
        "supervised_quality_flags": dict(Counter(flag for row in supervised for flag in row["quality_flags"])),
        "status": "complete",
    }
    (DATA / "collection-verification-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
