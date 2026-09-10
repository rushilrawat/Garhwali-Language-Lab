#!/usr/bin/env python3
"""Audit local PCM WAV files referenced by VAANI preparation manifests."""

from __future__ import annotations

import argparse
import json
import math
import sys
import wave
from array import array
from collections import Counter
from pathlib import Path


def audit_wav(path: Path, chunk_frames: int = 65_536) -> dict:
    """Return header and simple signal metrics without loading a file at once."""
    result = {"readable": False}
    try:
        with wave.open(str(path), "rb") as source:
            channels = source.getnchannels()
            sample_width = source.getsampwidth()
            sample_rate = source.getframerate()
            frames = source.getnframes()
            result.update(
                readable=True,
                channels=channels,
                sample_width_bytes=sample_width,
                sample_rate_hz=sample_rate,
                frames=frames,
                duration_seconds=frames / sample_rate if sample_rate else None,
                compression_type=source.getcomptype(),
            )
            if source.getcomptype() != "NONE" or sample_width != 2:
                result["signal_metrics_status"] = "unsupported_encoding"
                return result

            total = zeros = clipped = peak = sample_sum = square_sum = 0
            while True:
                payload = source.readframes(chunk_frames)
                if not payload:
                    break
                samples = array("h")
                samples.frombytes(payload)
                if sys.byteorder != "little":
                    samples.byteswap()
                total += len(samples)
                for sample in samples:
                    magnitude = abs(sample)
                    sample_sum += sample
                    square_sum += sample * sample
                    zeros += sample == 0
                    clipped += magnitude >= 32_767
                    if magnitude > peak:
                        peak = magnitude
            rms = math.sqrt(square_sum / total) if total else 0.0
            result.update(
                samples=total,
                peak_abs=peak,
                peak_dbfs=20 * math.log10(peak / 32768) if peak else None,
                rms_amplitude=rms,
                rms_dbfs=20 * math.log10(rms / 32768) if rms else None,
                dc_offset_normalized=sample_sum / total / 32768 if total else 0.0,
                zero_sample_share=zeros / total if total else 0.0,
                clipped_sample_share=clipped / total if total else 0.0,
                signal_metrics_status="complete",
            )
    except Exception as exc:  # A failure record is more useful than aborting a corpus run.
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def audit_manifests(manifests: list[tuple[str, Path]], output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "quality.jsonl"
    counts = Counter()
    duration = 0.0
    sample_rates = Counter()
    channels = Counter()
    sample_widths = Counter()
    with output_path.open("w", encoding="utf-8") as output:
        for subset, manifest in manifests:
            with manifest.open(encoding="utf-8") as source:
                for line_number, line in enumerate(source, 1):
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    audio_path = Path(record["local_audio_path"])
                    audit = audit_wav(audio_path)
                    audit.update(
                        subset=subset,
                        local_audio_path=str(audio_path),
                        audio_sha256=record.get("audio_sha256"),
                        manifest_duration_seconds=record.get("duration_seconds"),
                    )
                    output.write(json.dumps(audit, ensure_ascii=False, sort_keys=True) + "\n")
                    counts["rows"] += 1
                    counts[f"subset_{subset}"] += 1
                    if audit["readable"]:
                        counts["readable"] += 1
                        duration += audit.get("duration_seconds") or 0.0
                        sample_rates[str(audit["sample_rate_hz"])] += 1
                        channels[str(audit["channels"])] += 1
                        sample_widths[str(audit["sample_width_bytes"])] += 1
                        if audit.get("zero_sample_share", 0) >= 0.98:
                            counts["near_silent"] += 1
                        if audit.get("clipped_sample_share", 0) >= 0.01:
                            counts["high_clipping"] += 1
                    else:
                        counts["unreadable"] += 1

    report = {
        **dict(sorted(counts.items())),
        "decoded_duration_hours": duration / 3600,
        "sample_rate_distribution": dict(sample_rates),
        "channel_distribution": dict(channels),
        "sample_width_distribution": dict(sample_widths),
        "output": str(output_path),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--supervised", type=Path, default=Path("data/processed/vaani/supervised.jsonl"))
    parser.add_argument("--untranscribed", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/processed/audio"))
    args = parser.parse_args()
    manifests = [("supervised", args.supervised)]
    if args.untranscribed:
        manifests.append(("untranscribed", args.untranscribed))
    print(json.dumps(audit_manifests(manifests, args.output_dir), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
