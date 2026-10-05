#!/usr/bin/env python3
"""Find released text rows whose source identities touch upstream eval splits.

The generated artifact contains source IDs and split evidence, not transcript
content. Matching a community-aggregated transcript to an upstream split is
reported as text-level evidence; it is not treated as proof of audio identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
META_PATH = ROOT / "corpus/meta_omni.jsonl"
VAANI_PATH = ROOT / "data/vaani/canonical-supervised-manifest.jsonl"
AGGREGATE_PATH = (
    ROOT / "sources/online/indic_dialect_asr/98b706985ac2935c-transcripts.json"
)
EXPERIMENTAL_PATH = ROOT / "experimental/indic_dialect_asr_gbm.jsonl"
DEFAULT_OUTPUT = ROOT / "research/huggingface-upstream-split-overlap-2026-10-05.json"
EVAL_SPLITS = {"dev", "validation", "test"}


def normalized_key(text: str | None) -> str:
    value = unicodedata.normalize("NFKC", str(text or "")).casefold()
    return "".join(character for character in value if character.isalnum())


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_match_index(rows: list[dict], family: str) -> dict[str, dict]:
    matches: dict[str, dict[str, str]] = defaultdict(dict)
    for row in rows:
        if family == "meta_omni":
            identity = str(row.get("record_id") or "")
            values = {row.get("text_original") or row.get("text_normalized") or ""}
        else:
            identity = f"{row.get('split')}:{row.get('row_idx')}"
            values = {
                row.get("canonical_transcript") or "",
                row.get("transcript") or "",
            }
        for value in values:
            key = normalized_key(value)
            if key:
                matches[key][identity] = str(row.get("split") or "<missing>")
    return {
        key: {
            "candidate_source_records": len(identities),
            "candidate_splits": sorted(set(identities.values())),
        }
        for key, identities in matches.items()
    }


def build_report(
    meta_rows: list[dict],
    vaani_rows: list[dict],
    aggregate_rows: list[dict],
    *,
    input_files: dict[str, dict] | None = None,
) -> dict:
    meta_eval_ids = sorted(
        str(row["record_id"])
        for row in meta_rows
        if row.get("record_id") and row.get("split") in EVAL_SPLITS
    )
    meta_matches = source_match_index(meta_rows, "meta_omni")
    vaani_matches = source_match_index(vaani_rows, "vaani")
    aggregates_by_source = Counter(str(row.get("source") or "not_reported") for row in aggregate_rows)
    split_counts = Counter(str(row.get("split") or "<missing>") for row in meta_rows)
    split_counts.update(
        {f"vaani:{split}": count for split, count in Counter(
            str(row.get("split") or "<missing>") for row in vaani_rows
        ).items()}
    )

    overlapping = []
    aggregate_counts = Counter()
    for index, row in enumerate(aggregate_rows):
        source = str(row.get("source") or "not_reported")
        if source == "facebook/omnilingual-asr-corpus":
            family, lookup = "meta_omni", meta_matches
        elif source.startswith("Vaani/"):
            family, lookup = "vaani", vaani_matches
        else:
            continue
        match = lookup.get(normalized_key(row.get("sentence")))
        if not match:
            aggregate_counts[f"{family}:unmatched"] += 1
            continue
        candidate_splits = match["candidate_splits"]
        if not set(candidate_splits) & EVAL_SPLITS:
            aggregate_counts[f"{family}:train_only_match"] += 1
            continue
        record_id = f"indic_dialect_asr_gbm:{index}"
        resolution = (
            "unique_source_record_text_match"
            if match["candidate_source_records"] == 1
            else "ambiguous_repeated_text_match"
        )
        overlapping.append({
            "record_id": record_id,
            "upstream_family": family,
            "candidate_splits": candidate_splits,
            "candidate_source_record_count": match["candidate_source_records"],
            "match_resolution": resolution,
        })
        aggregate_counts[f"{family}:matches_eval_split"] += 1
        aggregate_counts[f"{family}:{resolution}"] += 1

    overlap_split_combinations = Counter(
        f"{row['upstream_family']}:{'+'.join(row['candidate_splits'])}"
        for row in overlapping
    )

    return {
        "schema_version": "garhwali-upstream-split-overlap-v1",
        "generated_on": date.today().isoformat(),
        "matching_method": (
            "NFKC normalization, case-folding, and retaining alphanumeric codepoints; "
            "community transcript matches are candidate source lineage, not audio identity"
        ),
        "input_files": input_files or {},
        "meta_upstream_eval_record_ids": meta_eval_ids,
        "community_rows_with_eval_split_text_matches": overlapping,
        "source_row_counts": {
            "meta_omni": len(meta_rows),
            "vaani_canonical_supervised": len(vaani_rows),
            "indic_dialect_asr_gbm": len(aggregate_rows),
            "indic_dialect_asr_by_declared_source": dict(sorted(aggregates_by_source.items())),
            "upstream_split_counts": dict(sorted(split_counts.items())),
        },
        "community_match_counts": dict(sorted(aggregate_counts.items())),
        "community_match_split_combinations": dict(
            sorted(overlap_split_combinations.items())
        ),
        "training_split_policy": (
            "Keep every source text in the dataset. Rows with a direct Meta dev/test "
            "record ID or a community transcript match to an upstream dev/test split "
            "belong in source_overlap, not the default train split."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inputs = {
        "meta_omni": META_PATH,
        "vaani": VAANI_PATH,
        "indic_dialect_asr_transcripts": AGGREGATE_PATH,
        "indic_dialect_asr_records": EXPERIMENTAL_PATH,
    }
    absent = [str(path) for path in inputs.values() if not path.is_file()]
    if absent:
        raise FileNotFoundError("Missing audit inputs: " + ", ".join(absent))

    meta_rows = read_jsonl(META_PATH)
    vaani_rows = read_jsonl(VAANI_PATH)
    aggregate_snapshot = json.loads(
        AGGREGATE_PATH.read_text(encoding="utf-8")
    )
    aggregate_rows = aggregate_snapshot["rows"]
    experimental_rows = read_jsonl(EXPERIMENTAL_PATH)
    if len(aggregate_rows) != len(experimental_rows):
        raise ValueError("Aggregate transcript and ingested-record counts differ")
    for index, (source_row, ingested_row) in enumerate(zip(aggregate_rows, experimental_rows)):
        if ingested_row.get("record_id") != f"indic_dialect_asr_gbm:{index}":
            raise ValueError(f"Unexpected aggregate record order at row {index}")
        if ingested_row.get("text_original") != source_row.get("sentence"):
            raise ValueError(f"Source text mismatch at aggregate row {index}")

    input_manifest = {
        label: {
            "path": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for label, path in inputs.items()
    }
    report = build_report(meta_rows, vaani_rows, aggregate_rows, input_files=input_manifest)
    vaani_revisions = sorted({
        str(row.get("revision")) for row in vaani_rows if row.get("revision")
    })
    report["upstream_revisions"] = {
        "facebook/omnilingual-asr-corpus": (
            "No single upstream commit is recorded in the local transcript manifest; "
            "the local manifest SHA-256 is included in input_files.meta_omni."
        ),
        "ARTPARK-IISc/Vaani": vaani_revisions,
        "grushaaaaa/indic-dialect-asr": {
            "dataset": aggregate_snapshot.get("dataset"),
            "revision": aggregate_snapshot.get("revision"),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "meta_upstream_eval_ids": len(report["meta_upstream_eval_record_ids"]),
        "community_transcript_matches_to_eval": len(
            report["community_rows_with_eval_split_text_matches"]
        ),
        "match_counts": report["community_match_counts"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
