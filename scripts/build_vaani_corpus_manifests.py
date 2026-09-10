#!/usr/bin/env python3
"""Build restricted metadata and canonical local VAANI Garhwali manifests."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "vaani"
SOURCE = DATA / "source" / "main" / "audio" / "Garhwali"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


def write_jsonl(path: Path, rows) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp.replace(path)


def normalized(value: str) -> str:
    return " ".join((value or "").split()).casefold()


def transcript_relation(main_text: str, transcription_text: str) -> str:
    if normalized(main_text) == normalized(transcription_text):
        return "exact-after-whitespace-case-normalization"
    strip_pause = lambda value: normalized(re.sub(r"</pause>", "", value or "", flags=re.I))
    if strip_pause(main_text) == strip_pause(transcription_text):
        return "closing-pause-tags-only"
    return "other-text-or-annotation-difference"


def quality_flags(transcript: str, relation: str) -> list[str]:
    flags = []
    if re.search(r"[\u0980-\u09FF]", transcript or ""):
        flags.append("bengali-script-in-garhwali-config")
    if relation == "other-text-or-annotation-difference":
        flags.append("manual-transcript-review")
    return flags


def apply_transcription_metadata(main_row: dict, transcription_row: dict) -> dict:
    """Merge a shared row while making the authoritative supervised split explicit."""
    record = dict(main_row)
    canonical = transcription_row["transcript"]
    relation = transcript_relation(main_row.get("transcript", ""), canonical)
    record["main_split"] = main_row.get("split")
    record["transcription_split"] = transcription_row.get("split")
    record["split"] = transcription_row.get("split")
    record["canonical_transcript"] = canonical
    record["canonical_transcript_source"] = "ARTPARK-IISc/Vaani-transcription-part"
    record["transcript_relation_to_main"] = relation
    record["quality_flags"] = quality_flags(canonical, relation)
    return record


def main() -> None:
    import pyarrow.parquet as pq

    restricted = []
    for shard in sorted(SOURCE.glob("train-*.parquet")):
        columns = ["audio.path", "pincode", "speakerImageHash"]
        for row in pq.ParquetFile(shard).read(columns=columns).to_pylist():
            restricted.append({
                "audio_path": Path(row["audio"]["path"]).name,
                "pincode": row.get("pincode"),
                "speaker_image_hash": row.get("speakerImageHash"),
                "access_class": "restricted-quasi-identifiers",
                "source": "ARTPARK-IISc/Vaani",
                "revision": "fe12c49bc61c083d5bb2092513fb6ec2e7ae72ee",
            })
    if len(restricted) != 110410:
        raise RuntimeError(f"Expected 110410 restricted rows, found {len(restricted)}")
    write_jsonl(DATA / "restricted-metadata.jsonl", restricted)

    main_rows = read_jsonl(DATA / "garhwali-main-metadata.jsonl")
    transcript_rows = read_jsonl(DATA / "garhwali-transcriptions.jsonl")
    local_audio = {row["audio_path"]: row for row in read_jsonl(DATA / "audio-local-manifest.jsonl")}
    extra_audio = {row["audio_path"]: row for row in read_jsonl(DATA / "transcription-only-audio-manifest.jsonl")}
    images = {row["image_path"]: row for row in read_jsonl(DATA / "reference-image-manifest.jsonl")}
    trans_by_audio = {row["audio_path"]: row for row in transcript_rows}

    full = []
    supervised = []
    for row in main_rows:
        audio_path = row["audio_path"]
        image_name = Path(row["reference_image"]).name
        record = dict(row)
        record["local_audio_path"] = local_audio[audio_path]["local_path"]
        record["audio_sha256"] = local_audio[audio_path]["sha256"]
        record["local_reference_image_path"] = images[image_name]["local_path"]
        record["reference_image_sha256"] = images[image_name]["sha256"]
        if audio_path in trans_by_audio:
            record = apply_transcription_metadata(record, trans_by_audio[audio_path])
            supervised.append(record)
        else:
            record["canonical_transcript"] = ""
            record["canonical_transcript_source"] = None
            record["transcript_relation_to_main"] = None
            record["quality_flags"] = []
        full.append(record)

    for row in transcript_rows:
        if row["audio_path"] not in extra_audio:
            continue
        audio = extra_audio[row["audio_path"]]
        image_name = Path(row["reference_image"]).name
        supervised.append({
            **row,
            "main_split": None,
            "transcription_split": row.get("split"),
            "duration_seconds": audio["duration_seconds"],
            "local_audio_path": audio["local_path"],
            "audio_sha256": audio["sha256"],
            "canonical_transcript": row["transcript"],
            "canonical_transcript_source": "ARTPARK-IISc/Vaani-transcription-part",
            "local_reference_image_path": images[image_name]["local_path"],
            "reference_image_sha256": images[image_name]["sha256"],
            "main_config_status": "absent-from-current-main-config",
            "transcript_relation_to_main": "absent-from-current-main-config",
            "quality_flags": quality_flags(row["transcript"], "absent-from-current-main-config"),
        })

    if len(full) != 110410 or len(supervised) != 5894:
        raise RuntimeError(f"Canonical row counts failed: full={len(full)}, supervised={len(supervised)}")
    write_jsonl(DATA / "canonical-full-manifest.jsonl", full)
    write_jsonl(DATA / "canonical-supervised-manifest.jsonl", supervised)

    report = {
        "restricted_metadata_rows": len(restricted),
        "unique_nonempty_pincodes": len({str(row["pincode"]) for row in restricted if row["pincode"] not in (None, "", "NA")}),
        "speaker_image_hash_values": dict(Counter("present" if row["speaker_image_hash"] not in (None, "", "NA") else "missing" for row in restricted)),
        "unique_nonempty_speaker_image_hashes": len({row["speaker_image_hash"] for row in restricted if row["speaker_image_hash"] not in (None, "", "NA")}),
        "canonical_full_rows": len(full),
        "canonical_supervised_rows": len(supervised),
        "canonical_untranscribed_rows": sum(not row["canonical_transcript"] for row in full),
        "supervised_duration_seconds": sum(float(row.get("duration_seconds") or 0) for row in supervised),
        "supervised_duration_hours": sum(float(row.get("duration_seconds") or 0) for row in supervised) / 3600,
        "supervised_rows_with_quality_flags": sum(bool(row["quality_flags"]) for row in supervised),
        "bengali_script_rows": sum("bengali-script-in-garhwali-config" in row["quality_flags"] for row in supervised),
        "note": "restricted-metadata.jsonl contains quasi-identifiers and must not be published with the normalized corpus",
    }
    (DATA / "canonical-manifest-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
