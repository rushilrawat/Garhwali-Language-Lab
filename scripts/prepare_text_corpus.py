#!/usr/bin/env python3
"""Prepare a normalized, provenance-preserving view of every text layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUTS = ("corpus", "restricted", "experimental", "extracted", "data/extracted")
TEXT_FIELDS = ("text_normalized", "text", "source_text", "transcript")
ID_FIELDS = ("record_id", "id", "utterance_id", "audio_path")
QUALITY_METADATA_FIELDS = (
    "iso_639_3", "language", "language_scope", "language_candidates", "script",
    "genre", "modality", "dialect", "district", "speaker_id", "gender", "languages_known",
)
LINGUISTIC_METADATA_FIELDS = (
    "english_gloss", "gloss_en", "gloss_hi", "gloss", "translation", "parallel_english",
    "english_prompt", "english_alignments", "semantic_domain", "concept_id", "parameter_id",
    "segments", "value", "other_form", "cultural_genres",
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def split_for_hash(digest: str) -> str:
    bucket = int(digest[:8], 16) % 1000
    if bucket < 900:
        return "train"
    if bucket < 950:
        return "validation"
    return "test"


def quality_signals(text: str) -> dict:
    nonspace = [char for char in text if not char.isspace()]
    alphabetic = [char for char in nonspace if char.isalpha()]
    devanagari = [char for char in nonspace if "\u0900" <= char <= "\u097f"]
    replacement = text.count("\ufffd")
    return {
        "characters": len(text),
        "nonspace_characters": len(nonspace),
        "alphabetic_characters": len(alphabetic),
        "devanagari_characters": len(devanagari),
        "devanagari_share": round(len(devanagari) / len(nonspace), 6) if nonspace else 0.0,
        "replacement_characters": replacement,
        "quality_band": "low" if replacement or len(text) < 3 else "review",
    }


def text_from(row: dict) -> tuple[str, str | None]:
    for field in TEXT_FIELDS:
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return normalize_text(value), field
    return "", None


def record_id(row: dict, fallback: str) -> str:
    for field in ID_FIELDS:
        value = row.get(field)
        if value is not None and str(value).strip():
            return str(value)
    return fallback


def layer_for(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    parts = relative.parts
    return "/".join(parts[:2]) if parts[0] == "data" and len(parts) > 1 else parts[0]


def discover(root: Path = ROOT) -> list[Path]:
    paths = []
    for name in DEFAULT_INPUTS:
        folder = root / name
        if folder.exists():
            paths.extend(folder.rglob("*.jsonl"))
    return sorted(set(paths))


def prepare(paths: list[Path], output_dir: Path, root: Path = ROOT) -> dict:
    groups: dict[str, dict] = {}
    source_records = empty_records = invalid_json_records = 0
    layers = Counter()
    for path in sorted(paths):
        layer = layer_for(path, root)
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                source_records += 1
                layers[layer] += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    invalid_json_records += 1
                    continue
                text, field = text_from(row)
                if not text:
                    empty_records += 1
                    continue
                digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                provenance = {
                    "layer": layer,
                    "file": str(path.relative_to(root)),
                    "line": line_number,
                    "record_id": record_id(row, f"line:{line_number}"),
                    "text_field": field,
                    "source_id": row.get("source_id"),
                    "source_url": row.get("source_url"),
                    "license": row.get("license") or row.get("license_name"),
                    "license_url": row.get("license_url"),
                    "rights_status": row.get("rights_status"),
                    "training_eligible": bool(row.get("training_eligible", False)),
                    "experimental_training_eligible": bool(
                        row.get("experimental_training_eligible", True)
                    ),
                    "quality_flags": row.get("quality_flags", []),
                    **{name: row[name] for name in QUALITY_METADATA_FIELDS if row.get(name) not in (None, "", [])},
                    "linguistic_metadata": {
                        name: row[name] for name in LINGUISTIC_METADATA_FIELDS
                        if row.get(name) not in (None, "", [])
                    },
                }
                if digest not in groups:
                    groups[digest] = {
                        "text_sha256": digest,
                        "text": text,
                        "split": split_for_hash(digest),
                        "quality": quality_signals(text),
                        "provenance": [],
                    }
                groups[digest]["provenance"].append(provenance)

    canonical = sorted(groups.values(), key=lambda row: row["text_sha256"])
    duplicates = [row for row in canonical if len(row["provenance"]) > 1]
    for row in canonical:
        row["source_count"] = len(row["provenance"])
        row["any_training_eligible_source"] = any(p["training_eligible"] for p in row["provenance"])
        row["any_experimental_training_eligible_source"] = any(
            p["experimental_training_eligible"] for p in row["provenance"]
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "canonical.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in canonical), encoding="utf-8"
    )
    (output_dir / "duplicates.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in duplicates), encoding="utf-8"
    )
    report = {
        "source_files": len(paths),
        "source_records": source_records,
        "unique_texts": len(canonical),
        "duplicate_rows": sum(len(row["provenance"]) - 1 for row in duplicates),
        "duplicate_groups": len(duplicates),
        "empty_records": empty_records,
        "invalid_json_records": invalid_json_records,
        "characters": sum(len(row["text"]) for row in canonical),
        "layer_records": dict(sorted(layers.items())),
        "split_unique_texts": dict(sorted(Counter(row["split"] for row in canonical).items())),
        "quality_bands": dict(sorted(Counter(row["quality"]["quality_band"] for row in canonical).items())),
    }
    (output_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "processed" / "text")
    args = parser.parse_args()
    report = prepare(discover(), args.output)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
