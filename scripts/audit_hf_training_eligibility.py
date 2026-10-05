#!/usr/bin/env python3
"""Audit text-training gates in a prepared Hugging Face package.

The counterfactual in this report is diagnostic only: it temporarily resolves
explicit source-level ``training_eligible: false`` values to true in memory,
then reruns the existing recommendation rule. It does not change package rows,
licenses, rights decisions, or eligibility labels.
"""

from __future__ import annotations

import argparse
import copy
import json
from collections import Counter, defaultdict
from pathlib import Path

from build_huggingface_dataset import (
    is_publishable_provenance,
    recommended_text_training_row,
)


TEXT_CONFIGS = ("text", "text_expansion", "text_resources")
SOURCE_LIST_FIELDS = ("provenance", "sources", "public_rights_basis")


def read_rows(package: Path, config: str) -> list[dict]:
    rows = []
    for shard in sorted((package / "data" / config).glob("*.jsonl")):
        with shard.open(encoding="utf-8") as stream:
            rows.extend(json.loads(line) for line in stream if line.strip())
    return rows


def source_rows(row: dict) -> list[dict]:
    return [
        item
        for field in SOURCE_LIST_FIELDS
        for item in (row.get(field) or [])
        if isinstance(item, dict)
    ]


def source_ids(row: dict) -> set[str]:
    return {
        str(item.get("source_id") or "<missing-source-id>")
        for item in source_rows(row)
    }


def simulate_resolved_source_flags(row: dict) -> dict:
    """Copy a row and resolve only explicit source training=False flags."""
    simulated = copy.deepcopy(row)
    for field in SOURCE_LIST_FIELDS:
        for item in simulated.get(field) or []:
            if isinstance(item, dict) and item.get("training_eligible") is False:
                item["training_eligible"] = True
    return simulated


def summarize_config(rows: list[dict]) -> dict:
    counts = Counter()
    split_counts = Counter()
    source_stats = defaultdict(lambda: {
        "records": 0,
        "records_with_explicit_training_false": 0,
        "records_with_quality_flags": 0,
        "quality_flag_record_counts": Counter(),
    })

    for row in rows:
        split = str(row.get("split") or "<missing>")
        split_counts[split] += 1
        source_items = source_rows(row)
        source_training = [
            item["training_eligible"]
            for item in source_items
            if isinstance(item.get("training_eligible"), bool)
        ]
        source_flags = {
            str(flag)
            for item in source_items
            for flag in item.get("quality_flags") or []
            if isinstance(flag, str) and flag
        }
        record_flags = {
            str(flag)
            for field in ("quality_flags", "record_quality_flags")
            for flag in row.get(field) or []
            if isinstance(flag, str) and flag
        }
        rights_basis = row.get("public_rights_basis") or []

        counts["stored_recommended_for_training"] += bool(
            row.get("recommended_for_training")
        )
        counts["recomputed_recommended_for_training"] += bool(
            recommended_text_training_row(row)
        )
        counts["explicit_source_training_false"] += any(
            value is False for value in source_training
        )
        experimental_training = [
            item["experimental_training_eligible"]
            for item in source_items
            if isinstance(item.get("experimental_training_eligible"), bool)
        ]
        counts["explicit_source_experimental_training_true"] += any(
            value is True for value in experimental_training
        )
        counts["explicit_source_experimental_training_false"] += any(
            value is False for value in experimental_training
        )
        counts["mixed_source_training_true_and_false"] += (
            any(source_training) and not all(source_training)
        )
        counts["source_quality_flags_present"] += bool(source_flags)
        counts["record_quality_flags_present"] += bool(record_flags)
        counts["strict_gold_tier_present"] += (
            "strict_gold_candidate" in (row.get("quality_tiers") or [])
        )
        counts["missing_public_rights_basis"] += not bool(rights_basis)
        counts["public_rights_basis_with_nonpublishable_item"] += bool(
            rights_basis
            and any(not is_publishable_provenance(item) for item in rights_basis)
        )
        counts["not_gbm_only"] += not (
            row.get("language") == "gbm"
            and set(row.get("source_languages") or []) == {"gbm"}
        )

        simulated = simulate_resolved_source_flags(row)
        counts["diagnostic_recommended_if_false_source_flags_resolved"] += bool(
            recommended_text_training_row(simulated)
        )

        for source_id in source_ids(row):
            stats = source_stats[source_id]
            stats["records"] += 1
            source_items_for_id = [
                item for item in source_items
                if str(item.get("source_id") or "<missing-source-id>") == source_id
            ]
            has_false = any(item.get("training_eligible") is False for item in source_items_for_id)
            flags_for_id = {
                str(flag)
                for item in source_items_for_id
                for flag in item.get("quality_flags") or []
                if isinstance(flag, str) and flag
            }
            stats["records_with_explicit_training_false"] += has_false
            stats["records_with_quality_flags"] += bool(flags_for_id)
            for flag in flags_for_id:
                stats["quality_flag_record_counts"][flag] += 1

    counts["records"] = len(rows)
    counts["stored_recommendation_mismatches"] = sum(
        bool(row.get("recommended_for_training"))
        != recommended_text_training_row(row)
        for row in rows
    )
    return {
        **dict(counts),
        "split_counts": dict(sorted(split_counts.items())),
        "source_records": [
            {
                "source_id": source_id,
                "records": stats["records"],
                "records_with_explicit_training_false": stats[
                    "records_with_explicit_training_false"
                ],
                "records_with_quality_flags": stats["records_with_quality_flags"],
                "quality_flag_record_counts": dict(
                    sorted(stats["quality_flag_record_counts"].items())
                ),
            }
            for source_id, stats in sorted(
                source_stats.items(),
                key=lambda item: (-item[1]["records"], item[0]),
            )
        ],
    }


def build_report(package: Path) -> dict:
    manifest_path = package / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    configs = {
        config: summarize_config(read_rows(package, config))
        for config in TEXT_CONFIGS
    }
    return {
        "package": str(package),
        "release_id": manifest.get("release_id"),
        "manifest_profile": manifest.get("profile"),
        "record_schema_version": manifest.get("record_schema_version"),
        "diagnostic_only": True,
        "counterfactual_definition": (
            "In memory only, set every explicit source-level training_eligible=false "
            "in provenance, sources, and public_rights_basis to true, then rerun "
            "recommended_text_training_row. All rights, quality, split, language, "
            "and other fields remain unchanged. This does not grant permission or "
            "change any release record."
        ),
        "configs": configs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.package)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "release_id": report["release_id"],
        "profile": report["manifest_profile"],
        "configs": {
            name: {
                "records": values["records"],
                "recommended": values["recomputed_recommended_for_training"],
                "diagnostic_after_resolving_source_flags": values[
                    "diagnostic_recommended_if_false_source_flags_resolved"
                ],
            }
            for name, values in report["configs"].items()
        },
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
