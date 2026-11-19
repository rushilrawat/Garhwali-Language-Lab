#!/usr/bin/env python3
"""Extract VAANI WAV bytes from local Parquet shards without audio decoding."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data" / "vaani" / "source" / "main" / "audio" / "Garhwali"
DEFAULT_OUTPUT = ROOT / "data" / "vaani" / "audio" / "main"
DEFAULT_MANIFEST = ROOT / "data" / "vaani" / "audio-local-manifest.jsonl"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_audio(path: Path, payload: bytes) -> tuple[str, bool]:
    expected_hash = hashlib.sha256(payload).hexdigest()
    if path.exists() and path.stat().st_size == len(payload) and file_hash(path) == expected_hash:
        return expected_hash, False
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(payload)
    temp.replace(path)
    return expected_hash, True


def extract(source: Path, output: Path, manifest: Path) -> None:
    shards = sorted(source.glob("train-*.parquet"))
    if len(shards) != 56:
        raise SystemExit(f"Expected 56 Parquet shards in {source}, found {len(shards)}")
    output.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    temp_manifest = manifest.with_suffix(manifest.suffix + ".tmp")
    seen = set()
    total_rows = total_bytes = invalid_wav_headers = written = 0

    with temp_manifest.open("w", encoding="utf-8") as handle:
        for shard_number, shard in enumerate(shards):
            shard_dir = output / f"{shard_number:05d}"
            shard_dir.mkdir(parents=True, exist_ok=True)
            shard_rows = 0
            parquet = pq.ParquetFile(shard)
            for batch in parquet.iter_batches(batch_size=256, columns=["audio.path", "audio.bytes"]):
                for item in batch.to_pylist():
                    audio = item["audio"]
                    name = Path(audio["path"]).name
                    payload = audio["bytes"]
                    if not name or payload is None:
                        raise RuntimeError(f"Missing audio path or bytes in {shard}")
                    if name in seen:
                        raise RuntimeError(f"Duplicate WAV path: {name}")
                    seen.add(name)
                    local_path = shard_dir / name
                    sha256, changed = write_audio(local_path, payload)
                    written += int(changed)
                    valid_header = payload[:4] == b"RIFF" and payload[8:12] == b"WAVE"
                    invalid_wav_headers += int(not valid_header)
                    total_rows += 1
                    shard_rows += 1
                    total_bytes += len(payload)
                    record = {
                        "audio_path": name,
                        "local_path": str(local_path.relative_to(ROOT)),
                        "source_shard": shard.name,
                        "bytes": len(payload),
                        "sha256": sha256,
                        "riff_wave_header": valid_header,
                    }
                    handle.write(json.dumps(record, separators=(",", ":")) + "\n")
            print(f"{shard_number + 1}/{len(shards)} {shard.name}: {shard_rows} WAVs", flush=True)

    if total_rows != 110410:
        raise RuntimeError(f"Expected 110410 WAVs, extracted {total_rows}")
    if invalid_wav_headers:
        raise RuntimeError(f"Found {invalid_wav_headers} files without RIFF/WAVE headers")
    temp_manifest.replace(manifest)
    report = {
        "source": str(source.relative_to(ROOT)),
        "output": str(output.relative_to(ROOT)),
        "shards": len(shards),
        "wav_files": total_rows,
        "unique_audio_paths": len(seen),
        "audio_payload_bytes": total_bytes,
        "written_or_replaced": written,
        "invalid_riff_wave_headers": invalid_wav_headers,
        "manifest": str(manifest.relative_to(ROOT)),
    }
    (manifest.parent / "audio-extraction-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    extract(args.source, args.output, args.manifest)
