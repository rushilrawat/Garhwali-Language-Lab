"""Package the published ASR v0.2 view as a private Kaggle training input."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
from garhwali_lab.hashing import sha256_file as file_sha256


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "validation", "test")
LOCAL = ROOT / "data/processed/model_ready/splits/asr_speaker_recovered_v0.1"
HF = ROOT / "data/huggingface/garhwali-speech-training-views-v0.2-upload/training_views/v0.2"
OLD_ZIP = ROOT / "data/kaggle/garhwali-asr-reference-v0.1.zip"
OUT = ROOT / "data/kaggle/garhwali-asr-reference-v0.2.zip"
FIELDS = (
    "split", "audio_file", "audio_sha256", "transcript", "duration_seconds",
    "source_record_id", "target_kind", "review_status", "native_speaker_reviewed",
    "reference_quality_flags", "district", "speaker_identity_resolution",
    "source_license",
)


def main() -> None:
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite {OUT}")
    release = json.loads((HF / "manifest.json").read_text(encoding="utf-8"))
    if release["total"] != 2718 or release["view_release"] != "asr_reference_v0.2":
        raise ValueError("unexpected Hugging Face release manifest")

    old_rows = {}
    with zipfile.ZipFile(OLD_ZIP) as archive:
        old_manifest = io.TextIOWrapper(archive.open("manifest.csv"), encoding="utf-8")
        for row in csv.DictReader(old_manifest):
            old_rows[row["audio_sha256"]] = row
    if len(old_rows) != 2002:
        raise ValueError("unexpected Kaggle v0.1 manifest")

    rows = []
    audio_paths = {}
    counts = Counter()
    for split in SPLITS:
        parquet_path = HF / "data/asr_reference" / f"{split}.parquet"
        rel = f"training_views/v0.2/data/asr_reference/{split}.parquet"
        if file_sha256(parquet_path) != release["files"][rel]:
            raise ValueError(f"Hugging Face Parquet hash changed: {split}")
        hf_rows = {row["audio_sha256"]: row for row in pq.read_table(parquet_path).to_pylist()}
        if len(hf_rows) != release["rows"][split]:
            raise ValueError(f"unexpected Hugging Face {split} count")
        with (LOCAL / f"{split}.jsonl").open(encoding="utf-8") as handle:
            local_rows = [json.loads(line) for line in handle if line.strip()]
        if {row["audio_sha256"] for row in local_rows} != set(hf_rows):
            raise ValueError(f"local audio and Hugging Face labels differ: {split}")

        for source in local_rows:
            digest = source["audio_sha256"]
            label = hf_rows[digest]
            if label["split"] != split or label["target_text"] != source["asr_target_clean"]:
                raise ValueError(f"split or reference mismatch: {digest}")
            if label["target_kind"] != "provider_reference" or label["native_speaker_reviewed"]:
                raise ValueError(f"unexpected label provenance: {digest}")
            path = ROOT / source["local_audio_path"]
            if not path.is_file() or file_sha256(path) != digest:
                raise ValueError(f"missing or altered source audio: {digest}")
            row = {
                "split": split,
                "audio_file": f"audio/{digest}.wav",
                "audio_sha256": digest,
                "transcript": label["target_text"],
                "duration_seconds": label["duration_seconds"],
                "source_record_id": label["source_record_id"],
                "target_kind": label["target_kind"],
                "review_status": label["review_status"],
                "native_speaker_reviewed": str(label["native_speaker_reviewed"]).lower(),
                "reference_quality_flags": json.dumps(label["reference_quality_flags"], ensure_ascii=False),
                "district": label["district"],
                "speaker_identity_resolution": label["speaker_identity_resolution"],
                "source_license": label["source_license"],
            }
            if digest in old_rows and any(
                row[key] != old_rows[digest][key]
                for key in ("split", "audio_file", "audio_sha256", "transcript")
            ):
                raise ValueError(f"existing Kaggle row changed: {digest}")
            rows.append(row)
            audio_paths[digest] = path
            counts[split] += 1

    if len(rows) != 2718 or len(audio_paths) != 2718 or len(set(old_rows) & set(audio_paths)) != 2002:
        raise ValueError("Kaggle v0.2 is not an additive copy of v0.1")
    if dict(counts) != {"train": 2202, "validation": 373, "test": 143}:
        raise ValueError(f"unexpected split counts: {dict(counts)}")

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    readme = """# Garhwali ASR reference clips v0.2

Private Kaggle training input matching the public `asr_reference` v0.2 label
index in https://huggingface.co/datasets/rushilrawat/garhwali-speech.
It contains 2,718 existing ARTPARK-IISc/VAANI Garhwali provider-labeled WAV
clips: 2,202 train, 373 validation, and 143 test. It adds 716 existing
provider references to the previous Kaggle v0.1 selection; no new recording
or transcript was created. The 2,002 previous labels and splits are preserved.

Use `manifest.csv` to pair `audio_file` with `transcript`, and train only on
`split=train`. The `reference_quality_flags` field is a JSON array; a
`possibly_incomplete` flag is a review priority, not a confirmed error.
References have not been adjudicated by a native speaker. The split has no
repeated audio hash, known speaker ID, or normalized transcript across splits.
Validation is entirely Tehri Garhwal, while test is mostly Uttarkashi, so
report district-specific scores. The optional Meta train view from the
Hugging Face dataset is not included here.

Source: https://huggingface.co/datasets/ARTPARK-IISc/Vaani
License: CC BY 4.0; attribution required. This Kaggle copy is for computation.
"""
    attribution = (
        "Source: ARTPARK-IISc/Vaani, Garhwali provider-transcribed clips. "
        "License: CC BY 4.0. https://huggingface.co/datasets/ARTPARK-IISc/Vaani\n"
        "Training view: https://huggingface.co/datasets/rushilrawat/garhwali-speech\n"
    )
    package = {
        "dataset": "rushilrawat1/garhwali-asr-reference-clips-v0-1",
        "view_release": release["view_release"],
        "source_hf_parquet_sha256": release["files"],
        "split_counts": dict(counts),
        "existing_rows_preserved": len(old_rows),
        "existing_provider_references_added": len(rows) - len(old_rows),
        "new_recordings_or_transcripts_created": 0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        archive.writestr("manifest.csv", buffer.getvalue())
        archive.writestr("README.md", readme)
        archive.writestr("ATTRIBUTION.md", attribution)
        archive.writestr("release.json", json.dumps(package, indent=2, sort_keys=True) + "\n")
        for digest, path in sorted(audio_paths.items()):
            archive.write(path, f"audio/{digest}.wav")
    print(json.dumps({"output": str(OUT), "bytes": OUT.stat().st_size,
                      "sha256": file_sha256(OUT), **package}, indent=2))


if __name__ == "__main__":
    main()
