#!/usr/bin/env python3
"""Build the v0.2 ASR label index over the existing public speech audio."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
REPO = "rushilrawat/garhwali-speech"
SPEECH = ROOT / "data/huggingface/garhwali-language-lab-speech-v2.2.0-staging"
ASR = ROOT / "data/processed/model_ready/splits/asr_speaker_recovered_v0.1"
OLD_VIEW = ROOT / "data/huggingface/garhwali-speech-training-views-v0.1-upload"
OUTPUT = ROOT / "data/huggingface/garhwali-speech-training-views-v0.2-upload"
PREFIX = "training_views/v0.2/data/asr_reference"


def read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_parquet(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(sorted(rows, key=lambda row: row["audio_sha256"]))
    pq.write_table(table, path, compression="zstd")
    return sha256_file(path)


def load_public_speech_index() -> dict[str, dict]:
    selected_hashes = {
        row["audio_sha256"]
        for split in ("train", "validation", "test")
        for row in read_jsonl(ASR / f"{split}.jsonl")
    }
    manifest = {}
    for row in read_jsonl(SPEECH / "manifest.jsonl"):
        audio_hash = row.get("audio_sha256")
        if not audio_hash or audio_hash not in selected_hashes:
            continue
        if audio_hash in manifest:
            raise ValueError(f"duplicate selected audio hash in public speech manifest: {audio_hash}")
        manifest[audio_hash] = row
    if set(manifest) != selected_hashes:
        raise ValueError("a selected ASR audio hash is missing from the public speech manifest")
    return manifest


def build_rows(public_by_hash: dict[str, dict]) -> dict[str, list[dict]]:
    views = {split: [] for split in ("train", "validation", "test")}
    seen_hashes = set()
    for split in views:
        for source in read_jsonl(ASR / f"{split}.jsonl"):
            audio_hash = source["audio_sha256"]
            target = str(source.get("asr_target_clean") or "").strip()
            published = public_by_hash.get(audio_hash)
            if (
                published is None
                or published.get("split") != split
                or not target
                or audio_hash in seen_hashes
            ):
                raise ValueError(f"invalid or duplicate v0.2 reference row: {audio_hash}")
            seen_hashes.add(audio_hash)
            resolution = source.get("speaker_id_resolution") or "source_speakerID"
            if resolution not in {"source_speakerID", "exact_speakerImageHash_join"}:
                raise ValueError(f"unexpected speaker identity resolution: {resolution}")
            views[split].append({
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
                "split_policy": "project_vaani_speaker_disjoint_asr_v0.2",
                "speaker_identity_resolution": resolution,
                "source_license": published["source_license"],
                "duration_seconds": source["duration_seconds"],
            })
    return views


def updated_readme(old_readme: str, counts: dict[str, int]) -> str:
    readme = old_readme
    for split in ("train", "validation", "test"):
        old_path = f"training_views/v0.1/data/asr_reference/{split}.parquet"
        new_path = f"training_views/v0.2/data/asr_reference/{split}.parquet"
        if old_path not in readme:
            raise ValueError(f"missing expected v0.1 card path: {old_path}")
        readme = readme.replace(old_path, new_path)

    readme = readme.replace(
        "## Closeout snapshot — 6 October 2026",
        "## Training-view update — 7 October 2026",
    )
    readme = re.sub(
        r"strict\s+speaker-disjoint ASR view contains [\d,]+ unreviewed rows\.",
        f"strict\nspeaker-disjoint ASR view contains {sum(counts.values()):,} unreviewed rows.",
        readme,
    )
    readme = re.sub(
        r"A separate strict speaker-disjoint ASR view(?: in the linked corpus)? has [\d,]+\s+rows \(train [\d,]+, validation [\d,]+, test [\d,]+\); none has native-speaker\s+adjudication\.",
        f"A separate strict speaker-disjoint ASR view has {sum(counts.values()):,}\n  rows (train {counts['train']:,}, validation {counts['validation']:,}, test\n  {counts['test']:,}); none has native-speaker adjudication.",
        readme,
    )
    readme = re.sub(
        r"It has [\d,]+ train, [\d,]+\s+validation, and [\d,]+ test rows from the existing speaker-disjoint\s+VAANI ASR profile\.",
        f"It has {counts['train']:,} train, {counts['validation']:,}\nvalidation, and {counts['test']:,} test rows from the versioned speaker-disjoint\nVAANI ASR profile.",
        readme,
    )
    readme = re.sub(
        r"`reference_quality_flags`: [\d,]+ train,\s*[\d,]+ validation, and [\d,]+ test",
        "`reference_quality_flags`: 365 train,\n71 validation, and 11 test",
        readme,
    )
    readme = re.sub(
        r"validation is all Tehri Garhwal\s*\(\d+/\d+\), while test is mostly\s*Uttarkashi \(\d+/\d+\)",
        "validation is all Tehri Garhwal (373/373), while test is mostly\nUttarkashi (132/143)",
        readme,
    )
    readme = readme.replace(
        "`training_views/v0.1/TRAINING_GUIDE.md`.",
        "`training_views/v0.2/TRAINING_GUIDE.md`.",
    )
    readme = re.sub(
        r"No\s+speech payload changed in this project closeout\.",
        "The audio payload is unchanged; v0.2 updates only the text-only training index and its documentation.",
        readme,
    )
    addition = (
        "\n\nThe v0.2 view makes 716 already-present VAANI provider references newly\n"
        "eligible for this speaker-disjoint label index. Their missing source\n"
        "speaker IDs were recovered only through an exact, unambiguous join from\n"
        "the existing `speakerImageHash` field to one known source `speakerID`;\n"
        "the image hashes and speaker IDs are not included in the label index.\n"
        "Two exact matches remain excluded because they carry transcript-review\n"
        "flags. No new audio or transcript was created; v0.2 indexes these\n"
        "already-present provider labels for training.\n"
    )
    marker = "Neither view contains SraVaani or Whisper pseudo-labels."
    if marker not in readme:
        raise ValueError("could not locate the training-view documentation section")
    readme = readme.replace(marker, addition + "\n" + marker)
    return readme


def training_guide(counts: dict[str, int]) -> str:
    return f"""# Garhwali speech training views v0.2

Use `asr_reference` for the default supervised ASR baseline. It has {counts['train']:,}
train, {counts['validation']:,} validation, and {counts['test']:,} test rows. The split
view combines the previous identified-speaker profile with 716 existing VAANI
provider references whose missing speaker IDs were recovered by an exact,
unambiguous `speakerImageHash` to `speakerID` source join. No image hashes or
speaker IDs are published in this label index. Two additional source matches
remain excluded because transcript quality flags require review.

The labels are cleaned upstream provider transcripts, not native-adjudicated
gold text. The view contains no machine-generated drafts and no duplicated
audio payload. Join it to the already published audio using the stable
`source_record_id` / `record_id` pair:

```python
from datasets import Audio, load_dataset

repo = "rushilrawat/garhwali-speech"
split = "train"  # use "validation" or "test" for the matching held-out split
labels = load_dataset(repo, "asr_reference", split=split)
targets = {{row["source_record_id"]: row for row in labels}}

# The labeled audio is already partitioned under the corresponding split.
# Streaming avoids loading unrelated recordings into memory.
audio = load_dataset(repo, "garhwali_speech", split=split, streaming=True)
audio = audio.cast_column("audio", Audio(decode=False))
joined = audio.filter(lambda row: row["record_id"] in targets)
joined = joined.map(lambda row: {{
    "target_text": targets[row["record_id"]]["target_text"],
    "speaker_identity_resolution": targets[row["record_id"]]["speaker_identity_resolution"],
}})
joined = joined.cast_column("audio", Audio())
```

`reference_quality_flags` preserves the existing source cleanup flags, including
`possibly_incomplete`; this flag signals review priority, not a proven error.
Validation is entirely Tehri Garhwal and test remains mostly Uttarkashi
(132/143), so report district-specific results. The splits have no repeated
audio hashes, speaker IDs, or normalized transcript strings across partitions.

The optional `asr_meta_extra_train` config remains the same train-only Meta
Omnilingual view. Its upstream references are unadjudicated and it has no
validation/test split. Do not use it as a benchmark.
"""


def build() -> dict:
    if OUTPUT.exists():
        raise FileExistsError(f"refusing to overwrite versioned output: {OUTPUT}")
    if not (OLD_VIEW / "README.md").is_file():
        raise FileNotFoundError("v0.1 training-view package is missing")
    public_by_hash = load_public_speech_index()
    views = build_rows(public_by_hash)
    counts = {split: len(rows) for split, rows in views.items()}
    expected = {"train": 2202, "validation": 373, "test": 143}
    if counts != expected:
        raise ValueError(f"unexpected recovered reference counts: {counts}")

    OUTPUT.mkdir(parents=True)
    file_hashes = {}
    for split, rows in views.items():
        path = OUTPUT / "training_views/v0.2/data/asr_reference" / f"{split}.parquet"
        file_hashes[str(path.relative_to(OUTPUT))] = write_parquet(path, rows)

    old_readme = (OLD_VIEW / "README.md").read_text(encoding="utf-8")
    (OUTPUT / "README.md").write_text(
        updated_readme(old_readme, counts), encoding="utf-8"
    )
    guide_path = OUTPUT / "training_views/v0.2/TRAINING_GUIDE.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(training_guide(counts), encoding="utf-8")
    view_manifest = {
        "view_release": "asr_reference_v0.2",
        "parent_view": "asr_reference_v0.1",
        "dataset": REPO,
        "source_splits": {
            split: json.loads((ASR / "report.json").read_text(encoding="utf-8"))["output_sha256"][f"{split}.jsonl"]
            for split in ("train", "validation", "test")
        },
        "rows": counts,
        "total": sum(counts.values()),
        "added_existing_provider_references": {"train": 581, "validation": 104, "test": 31},
        "speaker_identity_resolution": {
            "method": "exact_speakerImageHash_join_to_unique_existing_speakerID",
            "resolved_rows_before_quality_filter": 718,
            "rows_excluded_by_existing_transcript_quality_filter": 2,
            "rows_added": 716,
            "speaker_image_hashes_published": False,
            "speaker_IDs_published": False,
        },
        "audio_payloads_added": 0,
        "new_transcripts_created": 0,
        "files": file_hashes,
    }
    (OUTPUT / "training_views/v0.2/manifest.json").write_text(
        json.dumps(view_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return view_manifest


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
