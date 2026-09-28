#!/usr/bin/env python3
"""Attach reproducible manifests to existing mT0 validation predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evaluation_run_manifest import write_run_artifacts
from run_mt5_instruction_tuning import generation_diagnostics


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data/processed/model_ready/instructions_v0.2/validation.jsonl"
DEFAULT_PREDICTIONS = ROOT / (
    "data/processed/evaluation/controlled_modeling/"
    "mt0_instruction_32768_generation_analysis_v0_6/cloud_output/"
    "validation_predictions.jsonl"
)
DEFAULT_REPORT = ROOT / (
    "data/processed/evaluation/controlled_modeling/"
    "mt0_instruction_32768_generation_analysis_v0_6/cloud_output/report.json"
)
DEFAULT_OUTPUT = ROOT / (
    "data/processed/evaluation/generation/"
    "mt0_32768_validation_manifested_2026-09-27"
)


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected an object")
            rows.append(row)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _selected_rows_sha256(record_hashes: list[str]) -> str:
    payload = "\n".join(record_hashes).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_manifest_runs(
    validation_rows: list[dict],
    prediction_rows: list[dict],
    generation_report: dict,
    *,
    validation_sha256: str,
    prediction_sha256: str,
    generation_report_sha256: str,
) -> dict[str, dict]:
    """Join saved seed outputs to their exact source validation records."""
    if not validation_rows:
        raise ValueError("validation manifest is empty")
    if any(row.get("split") != "validation" for row in validation_rows):
        raise ValueError("input rows must all belong to the validation split")
    if generation_report.get("selection_split") != "validation":
        raise ValueError("generation report does not identify validation selection")
    if generation_report.get("fixed_test_opened") is not False:
        raise ValueError("generation report must confirm the fixed test was not opened")

    rows_by_hash = {}
    for row in validation_rows:
        record_hash = row.get("instruction_sha256")
        if not isinstance(record_hash, str) or not record_hash.strip():
            raise ValueError("selected validation row is missing instruction_sha256")
        record_hash = record_hash.strip().lower()
        if record_hash in rows_by_hash:
            raise ValueError(f"duplicate selected validation instruction hash: {record_hash}")
        rows_by_hash[record_hash] = row

    systems = generation_report.get("systems")
    if not isinstance(systems, dict) or not systems:
        raise ValueError("generation report has no per-seed systems")
    grouped: dict[str, dict[str, dict]] = {str(seed): {} for seed in systems}
    for prediction in prediction_rows:
        seed = str(prediction.get("system") or "")
        if seed not in grouped:
            raise ValueError(f"prediction has an unknown seed/system: {seed!r}")
        record_hash = prediction.get("instruction_sha256")
        record_hash = record_hash.strip().lower() if isinstance(record_hash, str) else ""
        if record_hash not in rows_by_hash:
            raise ValueError(f"prediction is outside the selected validation rows: {record_hash!r}")
        if record_hash in grouped[seed]:
            raise ValueError(f"duplicate validation prediction for {seed}/{record_hash}")
        source_row = rows_by_hash[record_hash]
        if prediction.get("task") != source_row.get("task"):
            raise ValueError(f"prediction task differs from validation row for {seed}/{record_hash}")
        if prediction.get("reference") != source_row.get("response"):
            raise ValueError(f"prediction reference differs from validation row for {seed}/{record_hash}")
        if not isinstance(prediction.get("hypothesis"), str):
            raise ValueError(f"prediction hypothesis is missing for {seed}/{record_hash}")
        grouped[seed][record_hash] = prediction

    observed_sets = {seed: set(rows) for seed, rows in grouped.items()}
    if not observed_sets or len({frozenset(ids) for ids in observed_sets.values()}) != 1:
        raise ValueError("seed predictions do not share one validation record set")
    expected_count = generation_report.get("validation_records")
    if expected_count != len(next(iter(observed_sets.values()))):
        raise ValueError("generation report row count differs from reconciled validation predictions")

    result = {}
    for seed in sorted(systems):
        observed = grouped[seed]
        ordered_hashes = list(observed)
        source_rows = [rows_by_hash[record_hash] for record_hash in ordered_hashes]
        seed_predictions = [observed[record_hash] for record_hash in ordered_hashes]
        selected_ids = [f"instruction:{record_hash}" for record_hash in observed]
        hypotheses = [prediction["hypothesis"] for prediction in seed_predictions]
        primary_reference_rows = [
            row | {"acceptable_responses": [prediction["reference"]]}
            for row, prediction in zip(source_rows, seed_predictions)
        ]
        primary_diagnostics, recomputed_details = generation_diagnostics(
            primary_reference_rows, hypotheses,
        )
        source_metrics = systems[seed]
        if source_metrics.get("diagnostics") != primary_diagnostics:
            raise ValueError(f"primary-reference generation metrics differ from saved report for {seed}")
        for metric in ("exact_match", "corpus_chrf2"):
            if source_metrics.get(metric) != primary_diagnostics["overall"].get(metric):
                raise ValueError(f"primary-reference generation metrics differ from saved report for {seed}")

        current_reference_diagnostics, _ = generation_diagnostics(source_rows, hypotheses)
        current_sensitivity = {
            "overall": {
                metric: current_reference_diagnostics["overall"][metric]
                for metric in ("records", "exact_match", "corpus_chrf2")
            },
            "by_task": {
                task: {
                    metric: values[metric]
                    for metric in ("records", "exact_match", "corpus_chrf2")
                }
                for task, values in current_reference_diagnostics["by_task"].items()
            },
            "chrf2_delta_vs_primary": round(
                current_reference_diagnostics["overall"]["corpus_chrf2"]
                - primary_diagnostics["overall"]["corpus_chrf2"],
                8,
            ),
            "interpretation": "Unreviewed alternative-reference sensitivity; not an accuracy improvement claim.",
        }
        report = {
            "schema_version": 1,
            "run_id": f"{generation_report.get('run_id')}:{seed}",
            "task": "multitask_text_generation",
            "evaluation_split": "instructions_v0.2/validation",
            "claim_limit": "development_diagnostic_only",
            "evaluation_records": len(observed),
            "selected_record_ids": selected_ids,
            "selected_rows_sha256": _selected_rows_sha256(ordered_hashes),
            "input_sha256": validation_sha256,
            "prediction_input_sha256": prediction_sha256,
            "generation_report_sha256": generation_report_sha256,
            "selected_id_source": "joined from saved prediction instruction hashes",
            "original_selection_parameters": "not recorded in the synced generation-analysis artifact",
            "metrics": systems[seed],
            "metric_reconciliation": {
                "source_report_generation_score_basis": "saved primary reference only",
                "recomputed_primary_reference_diagnostics": primary_diagnostics,
                "current_validation_alternative_reference_sensitivity": current_sensitivity,
            },
            "test_rows_scored": False,
            "limitations": [
                "These are saved development predictions; no new inference was run.",
                "The source references and generated Garhwali text have not been native-adjudicated.",
                "Saved predictions contain only the primary reference; alternate-reference results are a sensitivity analysis using current unreviewed candidates.",
                "The saved analysis artifact does not contain a per-seed checkpoint hash.",
            ],
        }
        predictions = []
        for record_hash, row, saved, detail in zip(
            ordered_hashes, source_rows, seed_predictions, recomputed_details,
        ):
            for detail_field, saved_field in (
                ("empty", "empty"),
                ("copies_instruction", "copies_instruction"),
                ("has_control_token", "has_control_token"),
                ("adjacent_repetition_rate", "adjacent_repetition_rate"),
            ):
                if saved_field in saved and saved[saved_field] != detail[detail_field]:
                    raise ValueError(f"saved generation diagnostic differs for {seed}/{record_hash}/{saved_field}")
            predictions.append({
                "record_id": f"instruction:{record_hash}",
                "instruction_sha256": record_hash,
                "task": row["task"],
                "reference": saved["reference"],
                "acceptable_responses": row.get("acceptable_responses") or [row["response"]],
                "hypothesis": saved["hypothesis"],
                "empty": saved.get("empty"),
                "copies_instruction": saved.get("copies_instruction"),
                "has_control_token": saved.get("has_control_token"),
                "adjacent_repetition_rate": saved.get("adjacent_repetition_rate"),
            })
        result[seed] = {
            "report": report,
            "predictions": predictions,
            "model": {
                "kind": "saved_mT0_LoRA_validation_predictions",
                "seed": seed,
                "checkpoint_hash": None,
                "checkpoint_identity_status": "not_recorded_in_saved_generation_analysis",
            },
            "config": {
                "task": "multitask_text_generation",
                "evaluation_split": "instructions_v0.2/validation",
            "selection_method": "join saved prediction hashes to frozen validation records",
            "original_selection_parameters": "unavailable",
            "test_rows_scored": False,
            "saved_predictions_only": True,
            "source_validation_manifest_sha256": validation_sha256,
            "source_predictions_sha256": prediction_sha256,
            "source_report_sha256": generation_report_sha256,
        },
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    validation_sha256 = sha256_file(args.data)
    prediction_sha256 = sha256_file(args.predictions)
    generation_report_sha256 = sha256_file(args.report)
    runs = build_manifest_runs(
        read_jsonl(args.data),
        read_jsonl(args.predictions),
        json.loads(args.report.read_text(encoding="utf-8")),
        validation_sha256=validation_sha256,
        prediction_sha256=prediction_sha256,
        generation_report_sha256=generation_report_sha256,
    )
    for seed, run in sorted(runs.items()):
        output_dir = args.output_dir / seed
        manifest = write_run_artifacts(
            output_dir,
            run["predictions"],
            run["report"],
            config=run["config"],
            model=run["model"],
            runtime={"inference": "not_run; saved validation predictions were reconciled"},
            device="saved_output_audit",
            seed=int(seed.removeprefix("seed-")),
            code_paths=[Path(__file__), ROOT / "scripts/run_mt5_instruction_tuning.py"],
            git_root=ROOT,
        )
        print(json.dumps({
            "seed": seed,
            "selected_records": manifest["selected_record_count"],
            "run_manifest": str(output_dir / "run_manifest.json"),
            "outputs": manifest["outputs"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
