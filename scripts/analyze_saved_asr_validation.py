"""Compare saved ASR outputs on the frozen validation split only."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from asr_metrics import normalize, score
from evaluation_run_manifest import write_run_artifacts


def _row_set_sha256(rows: list[dict]) -> str:
    identities = [
        {
            "row_idx": row.get("row_idx"),
            "audio_sha256": row["audio_sha256"].strip().lower(),
            "asr_target_sha256": row.get("asr_target_sha256"),
        }
        for row in rows
    ]
    payload = json.dumps(identities, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_report(
    manifest_rows: list[dict],
    predictions_by_model: dict[str, list[dict]],
    input_sha256: dict[str, str] | None = None,
) -> dict:
    """Score paired model predictions using only rows in the validation manifest."""
    if not manifest_rows:
        raise ValueError("validation manifest is empty")
    if any(row.get("split") != "validation" for row in manifest_rows):
        raise ValueError("manifest must contain validation rows only")

    wanted = {}
    for row in manifest_rows:
        audio_hash = row.get("audio_sha256")
        target = row.get("asr_target_clean")
        if not isinstance(audio_hash, str) or not audio_hash.strip():
            raise ValueError("validation row is missing audio_sha256")
        key = audio_hash.strip().lower()
        if key in wanted:
            raise ValueError(f"duplicate validation audio hash: {key}")
        if not isinstance(target, str) or not target.strip():
            raise ValueError(f"validation row {row.get('row_idx')} is missing asr_target_clean")
        wanted[key] = row

    model_rows = {}
    ignored = {}
    for model, predictions in sorted(predictions_by_model.items()):
        indexed = {}
        ignored[model] = 0
        for prediction in predictions:
            audio_hash = prediction.get("audio_sha256")
            key = audio_hash.strip().lower() if isinstance(audio_hash, str) else ""
            if key not in wanted:
                ignored[model] += 1
                continue
            if key in indexed:
                raise ValueError(f"duplicate validation prediction for {model}: {key}")
            reference = prediction.get("reference")
            hypothesis = prediction.get("hypothesis")
            if not isinstance(reference, str) or not isinstance(hypothesis, str):
                raise ValueError(f"prediction for {model}/{key} needs reference and hypothesis text")
            target = wanted[key]["asr_target_clean"]
            if normalize(reference) != normalize(target):
                raise ValueError(f"reference does not match frozen validation target for {model}/{key}")
            indexed[key] = prediction
        missing = sorted(set(wanted) - set(indexed))
        if missing:
            raise ValueError(f"missing validation prediction for {model}: {len(missing)} rows")
        model_rows[model] = indexed

    if len(model_rows) < 2:
        raise ValueError("at least two paired model prediction sets are required")

    rows = []
    totals = {model: {"word_errors": 0, "character_errors": 0} for model in model_rows}
    comparison = {
        model: {"lower_wer_rows": 0, "lower_cer_rows": 0}
        for model in model_rows
    }
    names = sorted(model_rows)
    for audio_hash, manifest_row in sorted(wanted.items(), key=lambda item: str(item[1].get("row_idx"))):
        reference = manifest_row["asr_target_clean"]
        per_model = {}
        for model in names:
            prediction = model_rows[model][audio_hash]
            metrics = score(reference, prediction["hypothesis"])
            per_model[model] = {
                "word_errors": metrics["word_errors"],
                "character_errors": metrics["character_errors"],
            }
            totals[model]["word_errors"] += metrics["word_errors"]
            totals[model]["character_errors"] += metrics["character_errors"]
        for left_index, left in enumerate(names):
            for right in names[left_index + 1:]:
                for error_key, metric_key in (
                    ("word_errors", "lower_wer_rows"),
                    ("character_errors", "lower_cer_rows"),
                ):
                    left_errors = per_model[left][error_key]
                    right_errors = per_model[right][error_key]
                    if left_errors < right_errors:
                        comparison[left][metric_key] += 1
                    elif right_errors < left_errors:
                        comparison[right][metric_key] += 1
        rows.append(
            {
                "record_id": f"asr:validation:{audio_hash}",
                "row_idx": manifest_row.get("row_idx"),
                "audio_sha256": audio_hash,
                "reference_words": len(normalize(reference).split()),
                "reference_characters": len(normalize(reference).replace(" ", "")),
                "models": per_model,
            }
        )

    reference_words = sum(row["reference_words"] for row in rows)
    reference_characters = sum(row["reference_characters"] for row in rows)
    summaries = {}
    for model, counts in totals.items():
        summaries[model] = {
            **counts,
            "reference_words": reference_words,
            "reference_characters": reference_characters,
            "wer": counts["word_errors"] / max(1, reference_words),
            "cer": counts["character_errors"] / max(1, reference_characters),
        }

    return {
        "status": "development_only",
        "evaluation_split": "asr/validation",
        "record_count": len(rows),
        "row_set_sha256": _row_set_sha256(manifest_rows),
        "metric_normalizer": "scripts/asr_metrics.py: NFC, casefold, punctuation/symbol to space, whitespace collapse",
        "previously_inspected": True,
        "models": summaries,
        "paired_comparison": comparison,
        "ignored_prediction_rows": ignored,
        "input_sha256": input_sha256 or {},
        "rows": rows,
        "limitation": "Automated-reference comparison only; this validation split has prior evaluation history and does not establish native-speaker correctness or blind generalization.",
    }


def write_analysis_artifacts(
    report: dict,
    output_dir: str | Path,
    *,
    model_metadata: dict | None = None,
    code_paths=(),
    git_root: str | Path | None = None,
) -> dict:
    """Write a post-hoc ASR comparison with a shared hash-linked manifest."""
    report = dict(report)
    rows = list(report.get("rows") or [])
    record_ids = [str(row.get("record_id") or "") for row in rows]
    if any(not record_id for record_id in record_ids):
        raise ValueError("ASR validation comparison row is missing a stable record ID")
    report["evaluation_records"] = len(rows)
    report["selected_record_ids"] = record_ids
    report["selected_rows_sha256"] = report.get("row_set_sha256")
    report["run_id"] = "asr-validation-paired-posthoc"
    predictions = [
        {
            "record_id": row["record_id"],
            "audio_sha256": row["audio_sha256"],
            "models": row["models"],
        }
        for row in rows
    ]
    return write_run_artifacts(
        output_dir,
        predictions,
        report,
        config={
            "task": "automatic_speech_recognition",
            "evaluation_split": "asr/validation",
            "purpose": "posthoc_scoring_of_saved_model_predictions",
            "metric_normalizer": report.get("metric_normalizer"),
            "uses_only_frozen_validation_audio_hashes": True,
            "test_rows_scored": False,
            "input_sha256": report.get("input_sha256", {}),
        },
        model={
            "kind": "paired_saved_prediction_comparison",
            "models": model_metadata or {},
        },
        runtime={"inference": "not_run; existing predictions rescored locally"},
        device="cpu_posthoc_scoring",
        code_paths=code_paths,
        git_root=git_root,
    )


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected an object")
            rows.append(row)
    return rows


def _read_matching_predictions(path: Path, wanted: set[str]) -> list[dict]:
    """Parse only prediction lines whose audio hash belongs to validation."""
    rows = []
    hash_pattern = re.compile(r'"audio_sha256"\s*:\s*"([0-9a-fA-F]{64})"')
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            match = hash_pattern.search(line)
            if not match or match.group(1).lower() not in wanted:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: malformed validation prediction") from error
            if not isinstance(row, dict):
                raise ValueError(f"{path}:{line_number}: expected a prediction object")
            rows.append(row)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def render_markdown(report: dict) -> str:
    lines = [
        "# Saved ASR validation comparison",
        "",
        "This is a validation-only reanalysis of existing prediction files. The test rows in those combined files were not parsed or scored.",
        "",
        f"- Status: `{report['status']}`",
        f"- Rows: {report['record_count']}",
        f"- Exact row-set SHA-256: `{report['row_set_sha256']}`",
        f"- Normalization: {report['metric_normalizer']}",
        "",
        "| Model | WER | CER | Word errors | Character errors |",
        "|---|---:|---:|---:|---:|",
    ]
    for model, metrics in sorted(report["models"].items()):
        lines.append(
            f"| {model} | {metrics['wer']:.4f} | {metrics['cer']:.4f} | "
            f"{metrics['word_errors']} | {metrics['character_errors']} |"
        )
    lines.extend(["", "## Paired record comparison", "", "| Model | Rows with lower WER | Rows with lower CER |", "|---|---:|---:|"])
    for model, values in sorted(report["paired_comparison"].items()):
        lines.append(f"| {model} | {values['lower_wer_rows']} | {values['lower_cer_rows']} |")
    lines.extend(["", "## Limits", "", report["limitation"], "", "Prediction and manifest SHA-256 values are in the JSON report.", ""])
    return "\n".join(lines)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=root / "data/processed/evaluation/asr/validation_comparison_manifested_2026-09-27",
    )
    args = parser.parse_args()
    manifest = root / "data/processed/model_ready/splits/asr/validation.jsonl"
    prediction_paths = {
        "sravaani": root / "data/processed/evaluation/asr/confidence_calibration/sravaani/predictions.jsonl",
        "whisper_v0.2": root / "data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/predictions.jsonl",
    }
    manifest_rows = _read_jsonl(manifest)
    wanted = {row["audio_sha256"].strip().lower() for row in manifest_rows}
    predictions = {
        name: _read_matching_predictions(path, wanted)
        for name, path in prediction_paths.items()
    }
    inputs = {"validation_manifest": _sha256_file(manifest)}
    inputs.update({name: _sha256_file(path) for name, path in prediction_paths.items()})
    report = build_report(manifest_rows, predictions, inputs)
    model_metadata = {}
    for name, path in prediction_paths.items():
        metadata_path = path.with_name("report.json")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        model_metadata[name] = {
            key: metadata.get(key)
            for key in ("model_id", "revision", "model_artifact_sha256", "run_id")
            if metadata.get(key) is not None
        }
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    manifest = write_analysis_artifacts(
        report,
        output_dir,
        model_metadata=model_metadata,
        code_paths=(Path(__file__), Path(__file__).with_name("asr_metrics.py"),
                    Path(__file__).with_name("evaluation_run_manifest.py")),
        git_root=root,
    )
    print(json.dumps({
        "output_dir": str(output_dir),
        "records": report["record_count"],
        "models": report["models"],
        "manifest": manifest,
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
