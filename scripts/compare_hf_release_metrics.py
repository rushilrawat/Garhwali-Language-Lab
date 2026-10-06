#!/usr/bin/env python3
"""Compare two passing Hugging Face package preflights under one metric contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


COUNT_DISTRIBUTIONS = (
    "scripts", "rights_status_counts", "reuse_scope_counts", "license_label_counts",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def numeric_fields(values: dict) -> dict[str, int | float]:
    return {
        key: value for key, value in values.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    }


def compare_numeric_fields(previous: dict, candidate: dict) -> tuple[dict, list[str]]:
    old = numeric_fields(previous)
    new = numeric_fields(candidate)
    shared = sorted(old.keys() & new.keys())
    deltas = {
        key: {
            "previous": old[key],
            "candidate": new[key],
            "delta": new[key] - old[key],
        }
        for key in shared
    }
    missing = sorted(old.keys() ^ new.keys())
    return deltas, missing


def compare_reports(
    previous: dict,
    candidate: dict,
    previous_report_sha256: str | None = None,
    candidate_report_sha256: str | None = None,
    comparison_script_sha256: str | None = None,
) -> dict:
    for label, report in (("previous", previous), ("candidate", candidate)):
        if report.get("status") != "passed" or report.get("errors"):
            raise ValueError(f"{label} preflight must have passed with no errors")
    if previous.get("release_id") == candidate.get("release_id"):
        raise ValueError("Preflight reports must identify different releases")
    for field in (
        "record_schema_version", "validation_contract_version", "validator_sha256",
    ):
        if not previous.get(field) or previous.get(field) != candidate.get(field):
            raise ValueError(f"Preflight reports use incompatible {field}")
    if previous.get("metric_definitions") != candidate.get("metric_definitions"):
        raise ValueError("Preflight reports use different metric definitions")

    previous_configs = previous.get("configs") or {}
    candidate_configs = candidate.get("configs") or {}
    previous_names = set(previous_configs)
    candidate_names = set(candidate_configs)
    common_names = sorted(previous_names & candidate_names)
    per_config = {}
    for name in common_names:
        old = previous_configs[name]
        new = candidate_configs[name]
        numeric_deltas, missing_numeric = compare_numeric_fields(old, new)
        distributions = {}
        for field in COUNT_DISTRIBUTIONS:
            old_counts = old.get(field)
            new_counts = new.get(field)
            if isinstance(old_counts, dict) and isinstance(new_counts, dict):
                distributions[field], _ = compare_numeric_fields(old_counts, new_counts)
        per_config[name] = {
            "previous_records": old.get("records"),
            "candidate_records": new.get("records"),
            "record_delta": (
                new["records"] - old["records"]
                if isinstance(old.get("records"), int)
                and isinstance(new.get("records"), int) else None
            ),
            "numeric_metric_deltas": numeric_deltas,
            "numeric_metrics_missing_on_one_side": missing_numeric,
            "count_distribution_deltas": distributions,
        }

    total_deltas, missing_total_metrics = compare_numeric_fields(
        previous.get("totals") or {}, candidate.get("totals") or {}
    )
    old_records = previous.get("totals", {}).get("records")
    new_records = candidate.get("totals", {}).get("records")
    return {
        "comparison_schema_version": 1,
        "comparison_script_sha256": comparison_script_sha256,
        "metric_contract": {
            "record_schema_version": previous["record_schema_version"],
            "validation_contract_version": previous["validation_contract_version"],
            "validator_sha256": previous["validator_sha256"],
            "metric_definitions_sha256": sha256_json(previous["metric_definitions"]),
            "same_contract_verified": True,
        },
        "input_reports": {
            "previous": {
                "release_id": previous.get("release_id"),
                "run_id": previous.get("run_id"),
                "sha256": previous_report_sha256,
            },
            "candidate": {
                "release_id": candidate.get("release_id"),
                "run_id": candidate.get("run_id"),
                "sha256": candidate_report_sha256,
            },
        },
        "summary": {
            "previous_config_split_count": len(previous_names),
            "candidate_config_split_count": len(candidate_names),
            "common_config_split_count": len(common_names),
            "added_config_splits": sorted(candidate_names - previous_names),
            "removed_config_splits": sorted(previous_names - candidate_names),
            "previous_overlapping_config_split_rows": old_records,
            "candidate_overlapping_config_split_rows": new_records,
            "overlapping_config_split_row_delta": (
                new_records - old_records
                if isinstance(old_records, int) and isinstance(new_records, int)
                else None
            ),
            "previous_records_deleted_or_mutated": previous.get("records_deleted_or_mutated"),
            "candidate_records_deleted_or_mutated": candidate.get("records_deleted_or_mutated"),
        },
        "config_split_record_counts": {
            "previous": {
                name: values.get("records") for name, values in previous_configs.items()
            },
            "candidate": {
                name: values.get("records") for name, values in candidate_configs.items()
            },
        },
        "total_metric_deltas": total_deltas,
        "total_metrics_missing_on_one_side": missing_total_metrics,
        "per_config_split": per_config,
    }


def render_markdown(comparison: dict) -> str:
    previous = comparison["input_reports"]["previous"]
    candidate = comparison["input_reports"]["candidate"]
    summary = comparison["summary"]
    lines = [
        f"# Hugging Face release metric comparison: {previous['release_id']} to {candidate['release_id']}",
        "",
        "Both package preflights passed under the same record schema, validator code, and metric definitions.",
        "",
        "| Measure | Previous | Candidate | Change |",
        "| --- | ---: | ---: | ---: |",
        (
            "| Config/split rows (overlapping views) | "
            f"{summary['previous_overlapping_config_split_rows']:,} | "
            f"{summary['candidate_overlapping_config_split_rows']:,} | "
            f"{summary['overlapping_config_split_row_delta']:+,} |"
        ),
        (
            "| Config/split views | "
            f"{summary['previous_config_split_count']} | "
            f"{summary['candidate_config_split_count']} | "
            f"{summary['candidate_config_split_count'] - summary['previous_config_split_count']:+} |"
        ),
        (
            "| Records deleted or mutated | "
            f"{summary['previous_records_deleted_or_mutated']} | "
            f"{summary['candidate_records_deleted_or_mutated']} | — |"
        ),
        "",
        "These config/split totals overlap and are not unique-record or newly acquired-text counts.",
        "",
        "## Per-view row counts",
        "",
        "| Config / split | Previous | Candidate | Change |",
        "| --- | ---: | ---: | ---: |",
    ]
    all_names = sorted(
        set(comparison["per_config_split"])
        | set(summary["added_config_splits"])
        | set(summary["removed_config_splits"])
    )
    for name in all_names:
        delta = comparison["per_config_split"].get(name)
        if delta:
            old = delta["previous_records"]
            new = delta["candidate_records"]
            change = f"{delta['record_delta']:+,}" if delta["record_delta"] is not None else "not comparable"
        elif name in summary["added_config_splits"]:
            old = "—"
            new = comparison["config_split_record_counts"]["candidate"].get(name, "—")
            change = f"+{new:,}" if isinstance(new, int) else "added"
        else:
            old = comparison["config_split_record_counts"]["previous"].get(name, "—")
            new, change = "—", "removed"
        old_value = f"{old:,}" if isinstance(old, int) else old
        new_value = f"{new:,}" if isinstance(new, int) else new
        lines.append(f"| `{name}` | {old_value} | {new_value} | {change} |")

    lines.extend([
        "",
        "## Aggregate metric deltas",
        "",
        "Counts below sum across config/split views. They are descriptive QA counts, not accuracy scores or unique records.",
        "",
        "| Metric | Previous | Candidate | Change |",
        "| --- | ---: | ---: | ---: |",
    ])
    for name, values in comparison["total_metric_deltas"].items():
        lines.append(
            f"| `{name}` | {values['previous']:,} | {values['candidate']:,} | {values['delta']:+,} |"
        )
    lines.extend([
        "",
        "## Reproducibility",
        "",
        f"- Validator SHA-256: `{comparison['metric_contract']['validator_sha256']}`",
        f"- Comparison script SHA-256: `{comparison.get('comparison_script_sha256') or 'not supplied'}`",
        f"- Metric-definition SHA-256: `{comparison['metric_contract']['metric_definitions_sha256']}`",
        f"- Previous preflight report SHA-256: `{previous.get('sha256') or 'not supplied'}`",
        f"- Candidate preflight report SHA-256: `{candidate.get('sha256') or 'not supplied'}`",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    previous = json.loads(args.previous.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    comparison = compare_reports(
        previous, candidate, sha256(args.previous), sha256(args.candidate),
        sha256(Path(__file__).resolve()),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(comparison), encoding="utf-8")
    print(json.dumps(comparison["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
