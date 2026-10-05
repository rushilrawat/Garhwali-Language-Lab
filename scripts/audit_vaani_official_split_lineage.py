#!/usr/bin/env python3
"""Reconcile local ASR views against VAANI's official transcript split."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "data/processed/model_ready/language_quality/audio_supervised.jsonl"
PROJECT_SPLITS = {
    f"asr_{split}": f"data/processed/model_ready/splits/asr/{split}.jsonl"
    for split in ("train", "validation", "test")
}
TRAINING_VIEWS = {
    "strict_asr_train": "data/processed/model_ready/splits/asr/train.jsonl",
    "expanded_human_train": "data/processed/model_ready/splits/asr_expanded_human/train.jsonl",
    "whisper_curriculum_train": "data/processed/model_ready/asr_curriculum/train.jsonl",
}
OFFICIAL_SPLITS = ("train", "validation", "test")
UNKNOWN_SPEAKERS = {"", "na", "n/a", "unknown", "none", "null", "unidentified"}


def read_jsonl(path: str | Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: malformed JSON") from error
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(row)
    return rows


def _audio_hash(row: dict) -> str | None:
    value = row.get("audio_sha256")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().lower()


def _speaker_id(row: dict) -> str | None:
    value = row.get("speaker_id")
    if value is None:
        return None
    value = str(value).strip()
    return None if value.casefold() in UNKNOWN_SPEAKERS else value


def _view_summary(rows: list[dict]) -> dict:
    hashes = [_audio_hash(row) for row in rows]
    valid_hashes = [value for value in hashes if value is not None]
    speakers = {_speaker_id(row) for row in rows}
    speakers.discard(None)
    return {
        "records": len(rows),
        "rows_with_audio_hash": len(valid_hashes),
        "unique_audio_hashes": len(set(valid_hashes)),
        "identified_speakers": len(speakers),
    }


def build_report(
    source_rows: list[dict],
    project_splits: dict[str, list[dict]],
    training_views: dict[str, list[dict]],
) -> dict:
    """Return aggregate-only overlap counts; never emit IDs, hashes, or text."""
    if not source_rows:
        raise ValueError("official source manifest is empty")

    official_rows: dict[str, list[dict]] = {split: [] for split in OFFICIAL_SPLITS}
    hash_to_splits: dict[str, set[str]] = defaultdict(set)
    for row in source_rows:
        audio_hash = _audio_hash(row)
        if audio_hash is None:
            raise ValueError("official source manifest has a row without audio_sha256")
        split = row.get("transcription_split")
        if split not in official_rows:
            raise ValueError(f"unsupported transcription_split: {split!r}")
        official_rows[split].append(row)
        hash_to_splits[audio_hash].add(split)

    cross_split_hashes = sum(len(splits) > 1 for splits in hash_to_splits.values())
    if cross_split_hashes:
        raise ValueError(
            f"official source manifest has {cross_split_hashes} audio hashes across splits"
        )

    source_counts = Counter(row["transcription_split"] for row in source_rows)
    project_coverage = {}
    for name, rows in project_splits.items():
        matched = Counter()
        missing_hash_rows = 0
        unmatched_hash_rows = 0
        for row in rows:
            audio_hash = _audio_hash(row)
            if audio_hash is None:
                missing_hash_rows += 1
            elif audio_hash in hash_to_splits:
                matched[next(iter(hash_to_splits[audio_hash]))] += 1
            else:
                unmatched_hash_rows += 1
        project_coverage[name] = {
            **_view_summary(rows),
            "official_split_counts": {
                split: matched[split] for split in OFFICIAL_SPLITS
            },
            "rows_without_audio_hash": missing_hash_rows,
            "audio_hashes_not_in_official_source": unmatched_hash_rows,
        }

    view_hashes = {}
    view_speakers = {}
    training_summary = {}
    for name, rows in training_views.items():
        hashes = {_audio_hash(row) for row in rows}
        hashes.discard(None)
        speakers = {_speaker_id(row) for row in rows}
        speakers.discard(None)
        view_hashes[name] = hashes
        view_speakers[name] = speakers

        official_audio_counts = Counter()
        official_speaker_counts = Counter()
        for split, split_rows in official_rows.items():
            for row in split_rows:
                audio_hash = _audio_hash(row)
                if audio_hash in hashes:
                    official_audio_counts[split] += 1
                speaker = _speaker_id(row)
                if speaker and speaker in speakers:
                    official_speaker_counts[split] += 1
        training_summary[name] = {
            **_view_summary(rows),
            "official_audio_hash_overlap_rows": {
                split: official_audio_counts[split] for split in OFFICIAL_SPLITS
            },
            "official_speaker_overlap_rows": {
                split: official_speaker_counts[split] for split in OFFICIAL_SPLITS
            },
        }

    remainder = build_official_test_remainder(
        source_rows, project_splits.get("asr_test", [])
    )
    remainder_speakers = {_speaker_id(row) for row in remainder}
    remainder_speakers.discard(None)
    remainder_known_speaker_rows = sum(bool(_speaker_id(row)) for row in remainder)
    training_overlap = {}
    for name in training_views:
        training_overlap[name] = {
            "audio_hash_rows": sum(
                _audio_hash(row) in view_hashes[name] for row in remainder
            ),
            "speaker_rows": sum(
                bool(_speaker_id(row) and _speaker_id(row) in view_speakers[name])
                for row in remainder
            ),
            "rows_with_identified_speaker": remainder_known_speaker_rows,
            "identified_speakers": len(remainder_speakers),
            "overlapping_identified_speakers": len(
                remainder_speakers & view_speakers[name]
            ),
        }

    remainder_hours = sum(
        float(row.get("duration_seconds") or 0) for row in remainder
    ) / 3600
    return {
        "official_split_counts": {
            split: source_counts[split] for split in OFFICIAL_SPLITS
        },
        "official_unique_audio_hashes": len(hash_to_splits),
        "official_cross_split_audio_hashes": cross_split_hashes,
        "project_split_coverage": project_coverage,
        "training_views": training_summary,
        "official_test_remainder": {
            "records": len(remainder),
            "duration_hours": round(remainder_hours, 6),
            "rows_with_identified_speaker": remainder_known_speaker_rows,
            "identified_speakers": len(remainder_speakers),
            "training_view_overlap": training_overlap,
            "designation": "open_utterance_split_diagnostic_only",
            "independent_speaker_evaluation": False,
            "selection_use_prohibited": True,
        },
    }


def build_official_test_remainder(
    source_rows: list[dict], fixed_test_rows: list[dict]
) -> list[dict]:
    """Return official test rows outside the existing fixed test audio hashes."""
    fixed_test_hashes = {_audio_hash(row) for row in fixed_test_rows}
    fixed_test_hashes.discard(None)
    return [
        row
        for row in source_rows
        if row.get("transcription_split") == "test"
        and _audio_hash(row) not in fixed_test_hashes
    ]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(root: Path, output: Path, remainder_manifest: Path | None = None) -> dict:
    source_path = root / SOURCE
    source_rows = read_jsonl(source_path)
    project_paths = {name: root / path for name, path in PROJECT_SPLITS.items()}
    training_paths = {name: root / path for name, path in TRAINING_VIEWS.items()}
    report = build_report(
        source_rows,
        {name: read_jsonl(path) for name, path in project_paths.items()},
        {name: read_jsonl(path) for name, path in training_paths.items()},
    )
    report["inputs_sha256"] = {
        "official_source": sha256_file(source_path),
        **{name: sha256_file(path) for name, path in project_paths.items()},
        **{name: sha256_file(path) for name, path in training_paths.items()},
    }
    output = output if output.is_absolute() else root / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if remainder_manifest is not None:
        rows = build_official_test_remainder(
            source_rows, read_jsonl(project_paths["asr_test"])
        )
        manifest_path = (
            remainder_manifest
            if remainder_manifest.is_absolute()
            else root / remainder_manifest
        )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
            encoding="utf-8",
        )
        report["official_test_remainder"]["manifest_records"] = len(rows)
        report["official_test_remainder"]["manifest_sha256"] = sha256_file(manifest_path)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/extracted/research/vaani-official-split-lineage.json"),
    )
    parser.add_argument(
        "--remainder-manifest",
        type=Path,
        help="optionally write the local-only official-test remainder JSONL",
    )
    args = parser.parse_args()
    report = run(args.root, args.output, args.remainder_manifest)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
