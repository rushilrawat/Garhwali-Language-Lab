#!/usr/bin/env python3
"""Build a versioned ASR view using exact VAANI speaker-image-hash links.

The source manifests are never modified. A missing speakerID is recovered only
when the transcript record uniquely matches one source row and that row's exact
speakerImageHash maps to exactly one non-empty speakerID elsewhere in the
pinned VAANI Garhwali source. Unresolved and ambiguous rows stay excluded.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/processed/model_ready/language_quality/audio_supervised.jsonl"
PARQUET_DIR = ROOT / "data/vaani/source/main/audio/Garhwali"
PARQUET_INDEX = ROOT / "data/vaani/source-shards-manifest.json"
BASE_SPLITS = ROOT / "data/processed/model_ready/splits/asr"
PUBLIC_SPEECH_MANIFEST = ROOT / (
    "data/huggingface/garhwali-language-lab-speech-v2.2.0-staging/manifest.jsonl"
)
OUT = ROOT / "data/processed/model_ready/splits/asr_speaker_recovered_v0.1"
PLACEHOLDERS = {"", "na", "n/a", "none", "unknown", "null", "unidentified"}
SPLITS = ("train", "validation", "test")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def is_identified(value: object) -> bool:
    return str(value or "").strip().casefold() not in PLACEHOLDERS


def normalized_source_text(value: object) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    return re.sub(r"\s+", " ", text)


def exact_source_key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("referenceImage") or ""),
        str(row.get("district") or ""),
        normalized_source_text(row.get("transcript")),
    )


def prepared_source_key(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("reference_image") or ""),
        str(row.get("district") or ""),
        normalized_source_text(row.get("transcript")),
    )


def exclusion_reason(row: dict) -> str | None:
    if not is_identified(row.get("speaker_id")):
        return "unidentified_speaker"
    language = row.get("language_quality", {})
    if (
        language.get("status") != "garhwali_candidate"
        or language.get("review_required")
        or row.get("transcript_review_flags")
        or not str(row.get("asr_target_clean") or "").strip()
    ):
        return "transcript_or_language_review"
    if (
        not row.get("recommended_for_supervised_training", False)
        or not row.get("audio_quality", {}).get("readable", False)
        or row.get("training_quality_flags")
    ):
        return "audio_quality_review"
    return None


def normalized_target_key(row: dict) -> str:
    value = unicodedata.normalize(
        "NFKC", str(row.get("asr_target_clean") or "")
    ).casefold()
    return "".join(char for char in value if char.isalnum())


def build() -> dict:
    if OUT.exists():
        raise FileExistsError(f"refusing to overwrite versioned output: {OUT}")
    if (
        not SOURCE.is_file()
        or not PARQUET_DIR.is_dir()
        or not BASE_SPLITS.is_dir()
        or not PUBLIC_SPEECH_MANIFEST.is_file()
    ):
        raise FileNotFoundError("a required pinned source or split manifest is missing")

    prepared = read_jsonl(SOURCE)
    source_by_key: dict[tuple[str, str, str], set[tuple[str, str]]] = defaultdict(set)
    speaker_ids_by_image_hash: dict[str, set[str]] = defaultdict(set)
    source_rows = 0
    for path in sorted(PARQUET_DIR.glob("*.parquet")):
        parquet = pq.ParquetFile(path)
        for batch in parquet.iter_batches(
            columns=["speakerID", "speakerImageHash", "referenceImage", "district", "transcript"],
            batch_size=1024,
        ):
            for source_row in batch.to_pylist():
                source_rows += 1
                speaker_id = str(source_row.get("speakerID") or "").strip()
                image_hash = str(source_row.get("speakerImageHash") or "").strip()
                source_by_key[exact_source_key(source_row)].add((speaker_id, image_hash))
                if is_identified(speaker_id) and image_hash:
                    speaker_ids_by_image_hash[image_hash].add(speaker_id)

    recovery_counts = Counter()
    unresolved_reasons = Counter()
    recovered_rows = []
    for row in prepared:
        if is_identified(row.get("speaker_id")):
            continue
        recovery_counts["prepared_rows_without_speaker_id"] += 1
        source_matches = source_by_key.get(prepared_source_key(row), set())
        if len(source_matches) != 1:
            unresolved_reasons["no_unique_exact_source_record_match"] += 1
            continue
        source_speaker_id, image_hash = next(iter(source_matches))
        if is_identified(source_speaker_id):
            unresolved_reasons["source_record_already_has_direct_speaker_id"] += 1
            continue
        candidate_ids = speaker_ids_by_image_hash.get(image_hash, set())
        if len(candidate_ids) != 1:
            unresolved_reasons[
                "image_hash_has_no_unique_known_speaker_id"
            ] += 1
            continue

        resolved_id = next(iter(candidate_ids))
        recovered = dict(row)
        recovered["speaker_id"] = resolved_id
        recovered["speaker_metadata"] = {
            **(row.get("speaker_metadata") or {}),
            "status": "identified",
            "speaker_id": resolved_id,
            "identity_resolution": "exact_speakerImageHash_join",
        }
        recovered["speaker_id_resolution"] = "exact_speakerImageHash_join"
        recovered["speaker_id_resolution_evidence"] = (
            "one_exact_source_record_match_and_one_known_source_speakerID"
        )
        recovered_rows.append(recovered)
        recovery_counts["unique_exact_image_hash_matches"] += 1

    eligible_recovered = []
    excluded_recovered = Counter()
    for row in recovered_rows:
        reason = exclusion_reason(row)
        if reason:
            excluded_recovered[reason] += 1
        else:
            eligible_recovered.append(row)

    rows_by_split = {split: read_jsonl(BASE_SPLITS / f"{split}.jsonl") for split in SPLITS}
    base_counts = {split: len(rows) for split, rows in rows_by_split.items()}
    for row in eligible_recovered:
        split = row.get("split")
        if split not in rows_by_split or row.get("transcription_split") != split:
            raise ValueError("recovered source split differs from preserved split")
        rows_by_split[split].append(row)

    all_rows = [row for split in SPLITS for row in rows_by_split[split]]
    audio_hashes = [str(row.get("audio_sha256") or "") for row in all_rows]
    if not all(audio_hashes) or len(audio_hashes) != len(set(audio_hashes)):
        raise ValueError("versioned ASR view has missing or duplicate audio hashes")

    speaker_splits: dict[str, set[str]] = defaultdict(set)
    text_splits: dict[str, set[str]] = defaultdict(set)
    for split, rows in rows_by_split.items():
        for row in rows:
            speaker_id = str(row.get("speaker_id") or "").strip()
            if not is_identified(speaker_id):
                raise ValueError("versioned ASR view contains an unidentified speaker")
            speaker_splits[speaker_id].add(split)
            target_key = normalized_target_key(row)
            if target_key:
                text_splits[target_key].add(split)
    speaker_cross_split = sum(len(splits) > 1 for splits in speaker_splits.values())
    text_cross_split = sum(len(splits) > 1 for splits in text_splits.values())
    if speaker_cross_split or text_cross_split:
        raise ValueError(
            "recovered split view has a speaker or normalized transcript crossing splits"
        )

    OUT.mkdir(parents=True)
    output_hashes = {}
    counts = {}
    district_counts = {}
    quality_flag_counts = {}
    for split, rows in rows_by_split.items():
        ordered = sorted(rows, key=lambda row: row["audio_sha256"])
        output_hashes[f"{split}.jsonl"] = write_jsonl(OUT / f"{split}.jsonl", ordered)
        counts[split] = len(ordered)
        district_counts[split] = dict(sorted(Counter(
            str(row.get("district") or "unknown") for row in ordered
        ).items()))
        quality_flag_counts[split] = dict(sorted(Counter(
            flag for row in ordered for flag in row.get("deep_cleanup_flags", [])
        ).items()))

    recovered_ids = {row["speaker_id"] for row in eligible_recovered}
    public_by_hash = {
        row["audio_sha256"]: row
        for row in read_jsonl(PUBLIC_SPEECH_MANIFEST)
        if row.get("audio_sha256")
    }
    added_rows_missing_public_audio = 0
    added_rows_wrong_public_split = 0
    for row in eligible_recovered:
        published = public_by_hash.get(row["audio_sha256"])
        if published is None:
            added_rows_missing_public_audio += 1
        elif published.get("split") != row["split"]:
            added_rows_wrong_public_split += 1
    if added_rows_missing_public_audio or added_rows_wrong_public_split:
        raise ValueError("a recovered reference does not join its existing public audio split")
    report = {
        "release_id": "vaani-asr-speaker-recovered-v0.1",
        "status": "source_linked_candidate",
        "policy": "exact source-record match plus unique exact speakerImageHash-to-speakerID match; no filename inference",
        "source_rows_scanned": source_rows,
        "source_shard_manifest_sha256": sha256_file(PARQUET_INDEX),
        "prepared_audio_supervised_sha256": sha256_file(SOURCE),
        "existing_strict_split_hashes": {
            split: sha256_file(BASE_SPLITS / f"{split}.jsonl") for split in SPLITS
        },
        "recovery": {
            "prepared_rows_without_speaker_id": recovery_counts[
                "prepared_rows_without_speaker_id"
            ],
            "uniquely_recovered_rows": recovery_counts[
                "unique_exact_image_hash_matches"
            ],
            "eligible_for_speaker_disjoint_view": len(eligible_recovered),
            "excluded_after_existing_quality_filters": dict(sorted(excluded_recovered.items())),
            "unresolved_rows": dict(sorted(unresolved_reasons.items())),
            "new_speaker_ids_not_in_previous_strict_view": len(
                recovered_ids - {row["speaker_id"] for row in all_rows if row not in eligible_recovered}
            ),
            "image_hashes_or_speaker_images_published": False,
        },
        "rows": {
            "existing_strict": base_counts,
            "added_existing_references": dict(sorted(Counter(
                row["split"] for row in eligible_recovered
            ).items())),
            "combined_versioned_view": counts,
            "districts": district_counts,
            "deep_cleanup_flags": quality_flag_counts,
            "total": sum(counts.values()),
            "added_audio_hours": round(
                sum(float(row.get("duration_seconds") or 0) for row in eligible_recovered) / 3600,
                6,
            ),
        },
        "integrity": {
            "unique_audio_hashes": len(set(audio_hashes)),
            "speaker_cross_split_ids": speaker_cross_split,
            "normalized_transcript_cross_split_keys": text_cross_split,
            "all_added_audio_hashes_already_in_public_speech_manifest": True,
            "all_added_audio_hashes_match_public_split": True,
            "public_manifest_audio_hash_rows": len(public_by_hash),
        },
        "output_sha256": output_hashes,
        "note": "Only training-view membership and source-linked speaker metadata change. No new recording or transcript was created.",
    }
    (OUT / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
