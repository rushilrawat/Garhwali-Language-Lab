#!/usr/bin/env python3
"""Download only transcription-part WAVs absent from the main VAANI config."""

from __future__ import annotations

import hashlib
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import time
import wave

import requests
from huggingface_hub import get_token


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vaani"
REPO = "ARTPARK-IISc/Vaani-transcription-part"
REVISION = "d2acadff1ccce766d127c11b1a157251460dd68a"
ROWS_URL = "https://datasets-server.huggingface.co/rows"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def fetch_one(record: dict, headers: dict[str, str], output: Path) -> dict:
    for attempt in range(6):
        try:
            response = requests.get(
                ROWS_URL,
                params={"dataset": REPO, "config": "Garhwali", "split": record["split"],
                        "offset": record["row_idx"], "length": 1},
                headers=headers,
                timeout=120,
            )
            response.raise_for_status()
            item = response.json()["rows"][0]["row"]
            audio_url = item["audio"][0]["src"]
            audio = requests.get(audio_url, timeout=120)
            audio.raise_for_status()
            payload = audio.content
            with wave.open(io.BytesIO(payload), "rb") as wav:
                frames, sample_rate = wav.getnframes(), wav.getframerate()
                duration = frames / sample_rate
                channels, sample_width = wav.getnchannels(), wav.getsampwidth()
            destination = output / record["split"] / record["audio_path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            temp = destination.with_suffix(destination.suffix + ".tmp")
            temp.write_bytes(payload)
            temp.replace(destination)
            return {
                "source": REPO,
                "revision": REVISION,
                "split": record["split"],
                "row_idx": record["row_idx"],
                "audio_path": record["audio_path"],
                "local_path": str(destination.relative_to(ROOT)),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "duration_seconds": duration,
                "sample_rate": sample_rate,
                "channels": channels,
                "sample_width_bytes": sample_width,
                "transcript": record["transcript"],
                "license": "CC-BY-4.0",
            }
        except Exception:
            if attempt == 5:
                raise
            time.sleep(2 ** attempt)


def main() -> None:
    token = get_token()
    if not token:
        raise SystemExit("No Hugging Face token found")
    main_paths = {row["audio_path"] for row in load_jsonl(DATA / "garhwali-main-metadata.jsonl")}
    transcription = load_jsonl(DATA / "garhwali-transcriptions.jsonl")
    missing = [row for row in transcription if row["audio_path"] not in main_paths]
    if len(missing) != 26:
        raise RuntimeError(f"Expected 26 transcription-only rows, found {len(missing)}")

    output = DATA / "audio" / "transcription-only"
    headers = {"Authorization": f"Bearer {token}"}
    results = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_one, row, headers, output): row for row in missing}
        for done, future in enumerate(as_completed(futures), 1):
            results.append(future.result())
            print(f"{done}/{len(missing)} transcription-only WAVs", flush=True)
    results.sort(key=lambda row: (row["split"], row["row_idx"]))
    manifest = DATA / "transcription-only-audio-manifest.jsonl"
    with manifest.open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    report = {
        "source": REPO,
        "revision": REVISION,
        "wav_files": len(results),
        "audio_payload_bytes": sum(row["bytes"] for row in results),
        "duration_seconds": sum(row["duration_seconds"] for row in results),
        "duration_hours": sum(row["duration_seconds"] for row in results) / 3600,
        "unique_audio_paths": len({row["audio_path"] for row in results}),
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (DATA / "transcription-only-audio-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
