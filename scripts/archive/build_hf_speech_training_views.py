#!/usr/bin/env python3
"""Build additive, text-only training indexes for the published speech audio."""

from __future__ import annotations

import sys
from pathlib import Path as _Path

# Shared modules (garhwali_lab, metrics, manifests) live one level up in scripts/.
sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))


import json
from pathlib import Path
from garhwali_lab.hashing import sha256_file as file_sha256
from garhwali_lab.io import iter_jsonl as read_jsonl


ROOT = Path(__file__).resolve().parents[2]
SPEECH = ROOT / "data/huggingface/garhwali-language-lab-speech-v2.2.0-staging"
CARD = ROOT / "data/huggingface/garhwali-speech-training-views-v0.1-source/README.md"
ASR = ROOT / "data/processed/model_ready/splits/asr"
META = ROOT / "data/processed/model_ready/splits/meta_omnilingual_asr"
OUTPUT = ROOT / "data/huggingface/garhwali-speech-training-views-v0.1-upload"
REPO = "rushilrawat/garhwali-speech"
PREFIX = "training_views/v0.1/data"


def write_parquet(path: Path, rows: list[dict]) -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq

    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(sorted(rows, key=lambda item: item["audio_sha256"]))
    pq.write_table(table, path, compression="zstd")
    return {"path": str(path.relative_to(OUTPUT)), "rows": len(rows), "sha256": file_sha256(path)}


def source_lookup(path: Path, key: str, selected_keys: set[str] | None = None) -> dict[str, dict]:
    result = {}
    for row in read_jsonl(path):
        value = row[key]
        if selected_keys is not None and value not in selected_keys:
            continue
        if value in result:
            raise ValueError(f"duplicate source manifest key: {value}")
        result[value] = row
    return result


def reference_views(vaani: dict[str, dict]) -> dict[str, list[dict]]:
    views = {}
    seen_hashes = set()
    for split in ("train", "validation", "test"):
        rows = []
        for source in read_jsonl(ASR / f"{split}.jsonl"):
            audio_hash = source["audio_sha256"]
            published = vaani[audio_hash]
            target = source["asr_target_clean"].strip()
            if published["split"] != split or not target or audio_hash in seen_hashes:
                raise ValueError(f"invalid reference split or label for {audio_hash}")
            seen_hashes.add(audio_hash)
            rows.append({
                "source_config": "garhwali_speech",
                "source_record_id": published["record_id"],
                "audio_sha256": audio_hash,
                "target_text": target,
                "target_kind": "provider_reference",
                "target_source": "ARTPARK-IISc/Vaani-transcription-part",
                "target_normalization": "project_asr_target_clean",
                "review_status": "upstream_reference_unadjudicated",
                "native_speaker_reviewed": False,
                "reference_quality_flags": source.get("deep_cleanup_flags", []),
                "district": source["district"],
                "split": split,
                "split_policy": "project_vaani_speaker_disjoint_asr",
                "source_license": published["source_license"],
                "duration_seconds": source["duration_seconds"],
            })
        views[split] = rows
    return views


def meta_train_view(meta: dict[str, dict]) -> list[dict]:
    rows = []
    seen_hashes = set()
    for source in read_jsonl(META / "train.jsonl"):
        published = meta[source["record_id"]]
        audio_hash = source["audio_sha256"]
        target = source["asr_target_clean"].strip()
        if (
            published["split"] != "train"
            or published["audio_sha256"] != audio_hash
            or published["split_safe_for_training"] is not True
            or not target
            or audio_hash in seen_hashes
        ):
            raise ValueError(f"invalid optional Meta training row for {source['record_id']}")
        seen_hashes.add(audio_hash)
        rows.append({
            "source_config": "meta_omnilingual",
            "source_record_id": source["record_id"],
            "audio_sha256": audio_hash,
            "target_text": target,
            "target_kind": "upstream_reference",
            "target_source": "facebook/omnilingual-asr-corpus",
            "target_normalization": "project_asr_target_clean",
            "review_status": "upstream_reference_unadjudicated",
            "native_speaker_reviewed": False,
            "split": "train",
            "split_policy": "meta_upstream_train_overlap_screened",
            "source_license": published["source_license"],
            "duration_seconds": source["duration_seconds"],
        })
    return rows


def card_with_views(source_card: str, counts: dict[str, int]) -> str:
    if "config_name: asr_reference" in source_card:
        raise ValueError("the source card already contains the training views")
    head, separator, body = source_card.partition("\n---\n")
    if not separator or not head.startswith("---\n"):
        raise ValueError("speech dataset card has no expected metadata block")
    configs = (
        "\n- config_name: asr_reference\n"
        "  data_files:\n"
        f"  - split: train\n    path: {PREFIX}/asr_reference/train.parquet\n"
        f"  - split: validation\n    path: {PREFIX}/asr_reference/validation.parquet\n"
        f"  - split: test\n    path: {PREFIX}/asr_reference/test.parquet\n"
        "- config_name: asr_meta_extra_train\n"
        "  data_files:\n"
        f"  - split: train\n    path: {PREFIX}/asr_meta_extra_train/train.parquet"
    )
    guide = f"""

## Training-ready label and split views

The `asr_reference` config is a small, text-only index into the audio in
`garhwali_speech`. It has {counts['train']:,} train, {counts['validation']:,}
validation, and {counts['test']:,} test rows from the existing speaker-disjoint
VAANI ASR profile. `target_text` is the project's cleaned version of an upstream
provider transcript. The references have not been adjudicated by native speakers.
Use `source_record_id` to join to the audio; no audio was copied for these views.

For evaluation, inspect `reference_quality_flags`: {counts['incomplete_train']:,} train,
{counts['incomplete_validation']:,} validation, and {counts['incomplete_test']:,} test
rows are marked `possibly_incomplete` in the source cleanup. Do not
assume those transcripts are wrong or silently rewrite them; review against the
audio before correcting labels. The strict split is speaker-disjoint, but its
district distribution is uneven: validation is all Tehri Garhwal
({counts['tehri_validation']:,}/{counts['validation']:,}), while test is mostly
Uttarkashi ({counts['uttarkashi_test']:,}/{counts['test']:,}). Report results by district and avoid
treating one aggregate score as broad Garhwali coverage.

`asr_meta_extra_train` adds {counts['meta_train']:,} optional Meta Omnilingual
training rows that passed the existing exact audio/text overlap screen. It is a
separate train-only view. Do not use it as an independent evaluation set.
Neither view contains SraVaani or Whisper pseudo-labels. Those remain separate
machine drafts in the source configs and are not reference targets.

```python
from datasets import Audio, load_dataset

repo = "{REPO}"
labels = load_dataset(repo, "asr_reference", split="train")
by_id = {{row["source_record_id"]: row for row in labels}}
audio = load_dataset(repo, "garhwali_speech", split="train", streaming=True)
audio = audio.cast_column("audio", Audio(decode=False))
joined = audio.filter(lambda row: row["record_id"] in by_id)
joined = joined.map(lambda row: {{"target_text": by_id[row["record_id"]]["target_text"]}})
joined = joined.cast_column("audio", Audio())
# Each joined row now has audio and a cleaned, unadjudicated reference target.
```

For validation or test, change both `split` arguments to the same split. To use
the optional Meta train rows, load `asr_meta_extra_train` and join them to
`meta_omnilingual/train` by `source_record_id`. The same procedure is also in
`training_views/v0.1/TRAINING_GUIDE.md`.
"""
    return head + configs + separator + body.rstrip() + "\n" + guide


def build() -> dict:
    strict_hashes = {
        row["audio_sha256"]
        for split in ("train", "validation", "test")
        for row in read_jsonl(ASR / f"{split}.jsonl")
    }
    vaani = source_lookup(SPEECH / "manifest.jsonl", "audio_sha256", strict_hashes)
    meta = source_lookup(SPEECH / "meta_omnilingual-manifest.jsonl", "record_id")
    reference = reference_views(vaani)
    extra = meta_train_view(meta)
    reference_hashes = {r["audio_sha256"] for rows in reference.values() for r in rows}
    if reference_hashes & {r["audio_sha256"] for r in extra}:
        raise ValueError("reference and optional Meta train audio overlap")
    counts = {split: len(rows) for split, rows in reference.items()}
    counts["meta_train"] = len(extra)
    for split, rows in reference.items():
        counts[f"incomplete_{split}"] = sum("possibly_incomplete" in row["reference_quality_flags"] for row in rows)
    counts["tehri_validation"] = sum(row["district"] == "TehriGarhwal" for row in reference["validation"])
    counts["uttarkashi_test"] = sum(row["district"] == "Uttarkashi" for row in reference["test"])
    files = []
    for split, rows in reference.items():
        files.append(write_parquet(OUTPUT / PREFIX / "asr_reference" / f"{split}.parquet", rows))
    files.append(write_parquet(OUTPUT / PREFIX / "asr_meta_extra_train" / "train.parquet", extra))
    for obsolete in (OUTPUT / PREFIX).glob("**/*.jsonl"):
        obsolete.unlink()
    card = card_with_views(CARD.read_text(encoding="utf-8"), counts)
    (OUTPUT / "README.md").write_text(card, encoding="utf-8")
    guide = (
        "# Garhwali speech training views\n\n"
        "Use `asr_reference` for the default supervised ASR baseline. Its "
        "train/validation/test partitions come from the existing strict "
        "speaker-disjoint VAANI profile. The labels are cleaned upstream "
        "provider transcripts, not native-adjudicated gold text.\n\n"
        "Use `asr_meta_extra_train` only as additional training material. "
        "It contains overlap-screened Meta upstream references and has no "
        "validation or test split. Machine drafts are absent from both views.\n\n"
        "Each row points to the existing audio by `source_config` and "
        "`source_record_id`. The dataset card gives a streaming join example. "
        "No audio or new transcript was generated by these views.\n\n"
        "The `reference_quality_flags` column exposes existing source cleanup "
        f"flags; `possibly_incomplete` occurs in {counts['incomplete_train']:,} train, "
        f"{counts['incomplete_validation']:,} validation, and {counts['incomplete_test']:,} test rows. "
        f"The speaker-disjoint validation split has {counts['tehri_validation']:,} of {counts['validation']:,} "
        f"Tehri Garhwal rows, while {counts['uttarkashi_test']:,} of {counts['test']:,} test rows are Uttarkashi. Review flagged "
        "references against audio and report district-specific metrics.\n"
    )
    guide_path = OUTPUT / "training_views/v0.1/TRAINING_GUIDE.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(guide, encoding="utf-8")
    manifest = {
        "version": "0.1",
        "destination": REPO,
        "purpose": "Additive training label and split views; no new audio or transcripts",
        "counts": counts,
        "source_files_sha256": {
            str(path.relative_to(ROOT)): file_sha256(path)
            for path in [
                CARD,
                SPEECH / "manifest.jsonl",
                SPEECH / "meta_omnilingual-manifest.jsonl",
                *[ASR / f"{split}.jsonl" for split in ("train", "validation", "test")],
                META / "train.jsonl",
            ]
        },
        "data_files": files,
        "card_sha256": file_sha256(OUTPUT / "README.md"),
        "guide_sha256": file_sha256(guide_path),
    }
    manifest_path = OUTPUT / "training_views/v0.1/manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    obsolete_uppercase_manifest = manifest_path.with_name("MANIFEST.json")
    if obsolete_uppercase_manifest.exists():
        obsolete_uppercase_manifest.unlink()
    return manifest


if __name__ == "__main__":
    print(json.dumps(build()["counts"], sort_keys=True))
