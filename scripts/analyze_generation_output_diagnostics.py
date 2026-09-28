#!/usr/bin/env python3
"""Audit structural quality of saved mT0 validation generations only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VALIDATION = ROOT / "data/processed/model_ready/instructions_v0.2/validation.jsonl"
DEFAULT_MANIFESTED_DIR = ROOT / (
    "data/processed/evaluation/generation/"
    "mt0_32768_validation_manifested_2026-09-27"
)
DEFAULT_SOURCE_PREDICTIONS = ROOT / (
    "data/processed/evaluation/controlled_modeling/"
    "mt0_instruction_32768_generation_analysis_v0_6/cloud_output/"
    "validation_predictions.jsonl"
)
DEFAULT_SOURCE_REPORT = ROOT / (
    "data/processed/evaluation/controlled_modeling/"
    "mt0_instruction_32768_generation_analysis_v0_6/cloud_output/report.json"
)
DEFAULT_OUTPUT = ROOT / (
    "data/processed/evaluation/generation/"
    "mt0_32768_output_diagnostics_2026-09-28"
)
EXPECTED_SEEDS = {"seed-17", "seed-29", "seed-43"}
SUSPICIOUS_INVISIBLES = {
    "\u200b",  # zero-width space
    "\ufeff",  # byte-order mark / zero-width no-break space
    *map(chr, range(0x202A, 0x202F)),  # bidi embedding/override controls
    *map(chr, range(0x2066, 0x206A)),  # bidi isolate controls
}
CONTROL_TOKEN = re.compile(r"<extra_id_\d+>")


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


def _normalized_output(text: str) -> str:
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def _percentile(values: list[int], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)
    return round(value, 2)


def _max_run(values: list[str]) -> int:
    if not values:
        return 0
    longest = current = 1
    previous = values[0]
    for value in values[1:]:
        if value == previous:
            current += 1
            longest = max(longest, current)
        else:
            previous = value
            current = 1
    return longest


def _script_family(text: str) -> str:
    has_latin = False
    has_devanagari = False
    has_other = False
    for char in text:
        if not char.isalpha():
            continue
        name = unicodedata.name(char, "")
        if "LATIN" in name:
            has_latin = True
        elif "DEVANAGARI" in name:
            has_devanagari = True
        else:
            has_other = True
    if not (has_latin or has_devanagari or has_other):
        return "no_letters"
    if has_latin and has_devanagari and not has_other:
        return "mixed_latin_devanagari"
    if has_latin and not has_devanagari and not has_other:
        return "latin_only"
    if has_devanagari and not has_latin and not has_other:
        return "devanagari_only"
    return "other_or_mixed"


SCRIPT_PROFILE_KEYS = (
    "latin_only",
    "devanagari_only",
    "mixed_latin_devanagari",
    "other_or_mixed",
    "no_letters",
)


def _summarize_group(rows: list[dict], *, include_mode_diagnostics: bool = True) -> dict:
    outputs = [unicodedata.normalize("NFC", row["hypothesis"]) for row in rows]
    references = [unicodedata.normalize("NFC", row["reference"]) for row in rows]
    normalized_counts = Counter(_normalized_output(text) for text in outputs)
    repeated_groups = [count for count in normalized_counts.values() if count > 1]
    char_runs = [_max_run(list(text)) for text in outputs]
    token_runs = [
        _max_run(_normalized_output(text).split())
        for text in outputs
    ]
    script_outputs = Counter(_script_family(text) for text in outputs)
    script_references = Counter(_script_family(text) for text in references)

    def count_rows(predicate) -> int:
        return sum(bool(predicate(text)) for text in outputs)

    result = {
        "records": len(rows),
        "empty_outputs": count_rows(lambda text: not text.strip()),
        "instruction_copy_outputs": sum(bool(row.get("copies_instruction")) for row in rows),
        "control_token_outputs": count_rows(lambda text: bool(CONTROL_TOKEN.search(text))),
        "length_characters": {
            "p10": _percentile([len(text) for text in outputs], 0.10),
            "p50": _percentile([len(text) for text in outputs], 0.50),
            "p90": _percentile([len(text) for text in outputs], 0.90),
            "max": max((len(text) for text in outputs), default=0),
        },
        "length_whitespace_tokens": {
            "p10": _percentile([len(text.split()) for text in outputs], 0.10),
            "p50": _percentile([len(text.split()) for text in outputs], 0.50),
            "p90": _percentile([len(text.split()) for text in outputs], 0.90),
            "max": max((len(text.split()) for text in outputs), default=0),
        },
        "max_adjacent_token_run": max(token_runs, default=0),
        "outputs_with_token_run_at_least_3": sum(run >= 3 for run in token_runs),
        "max_repeated_character_run": max(char_runs, default=0),
        "outputs_with_character_run_at_least_6": sum(run >= 6 for run in char_runs),
        "unicode_replacement_character_outputs": count_rows(lambda text: "\ufffd" in text),
        "surrogate_code_point_outputs": count_rows(
            lambda text: any(unicodedata.category(char) == "Cs" for char in text)
        ),
        "control_character_outputs": count_rows(
            lambda text: any(
                unicodedata.category(char) == "Cc" and char not in "\t\n\r"
                for char in text
            )
        ),
        "suspicious_invisible_character_outputs": count_rows(
            lambda text: any(char in SUSPICIOUS_INVISIBLES for char in text)
        ),
        "output_script_profile": {
            key: script_outputs.get(key, 0) for key in SCRIPT_PROFILE_KEYS
        },
        "reference_script_profile": {
            key: script_references.get(key, 0) for key in SCRIPT_PROFILE_KEYS
        },
    }
    if include_mode_diagnostics:
        result.update({
            "unique_normalized_outputs": len(normalized_counts),
            "repeated_output_groups": len(repeated_groups),
            "rows_in_repeated_output_groups": sum(repeated_groups),
            "largest_mode_count": max(normalized_counts.values(), default=0),
            "largest_mode_share": round(max(normalized_counts.values(), default=0) / len(rows), 4)
            if rows else 0,
        })
    return result


def summarize_predictions(validation_rows: list[dict], predictions_by_seed: dict[str, list[dict]]) -> dict:
    """Summarize saved validation predictions without retaining generated text."""
    if not validation_rows:
        raise ValueError("validation input is empty")
    if any(row.get("split") != "validation" for row in validation_rows):
        raise ValueError("all source rows must belong to validation")
    if not predictions_by_seed:
        raise ValueError("no seed predictions were supplied")

    validation_by_hash = {}
    for row in validation_rows:
        record_hash = row.get("instruction_sha256")
        if not isinstance(record_hash, str) or not record_hash:
            raise ValueError("validation row is missing instruction_sha256")
        if record_hash in validation_by_hash:
            raise ValueError(f"duplicate validation instruction hash: {record_hash}")
        validation_by_hash[record_hash] = row

    normalized_predictions = {}
    for seed, rows in predictions_by_seed.items():
        by_hash = {}
        for prediction in rows:
            record_hash = prediction.get("instruction_sha256")
            source = validation_by_hash.get(record_hash)
            if source is None:
                raise ValueError(f"{seed} prediction is not in validation: {record_hash!r}")
            if record_hash in by_hash:
                raise ValueError(f"duplicate prediction for {seed}/{record_hash}")
            if prediction.get("record_id") != f"instruction:{record_hash}":
                raise ValueError(f"record ID/hash mismatch for {seed}/{record_hash}")
            if prediction.get("task") != source.get("task"):
                raise ValueError(f"task mismatch for {seed}/{record_hash}")
            if prediction.get("reference") != source.get("response"):
                raise ValueError(f"reference mismatch for {seed}/{record_hash}")
            if not isinstance(prediction.get("hypothesis"), str):
                raise ValueError(f"hypothesis is missing for {seed}/{record_hash}")
            by_hash[record_hash] = prediction
        if not by_hash:
            raise ValueError(f"{seed} has no validation predictions")
        normalized_predictions[seed] = by_hash

    record_sets = {frozenset(rows) for rows in normalized_predictions.values()}
    if len(record_sets) != 1:
        raise ValueError("seed predictions do not share the same validation records")

    seed_reports = {}
    for seed, by_hash in sorted(normalized_predictions.items()):
        rows = list(by_hash.values())
        by_task = defaultdict(list)
        for row in rows:
            by_task[row["task"]].append(row)
        seed_reports[seed] = {
            "records": len(rows),
            "overall": _summarize_group(rows, include_mode_diagnostics=False),
            "by_task": {
                task: _summarize_group(task_rows)
                for task, task_rows in sorted(by_task.items())
            },
        }

    return {
        "schema_version": 1,
        "evaluation_split": "instructions_v0.2/validation",
        "claim_limit": "descriptive_validation_diagnostics_only",
        "test_rows_scored": False,
        "records_per_seed": len(next(iter(record_sets))),
        "seeds": seed_reports,
        "interpretation_limits": [
            "Length, repetition, script, and Unicode checks are structural heuristics, not measures of Garhwali correctness.",
            "Latin and Devanagari are both observed in the task outputs; script profiles are descriptive and do not flag either as wrong.",
            "Output character lengths count Unicode code points, not grapheme clusters; token lengths use whitespace splitting.",
            "Predictions and references are not native-adjudicated; results apply only to this saved validation subset.",
        ],
    }


def load_manifested_predictions(validation_path: Path, manifested_dir: Path,
                                source_predictions_path: Path,
                                source_report_path: Path) -> tuple[dict, dict]:
    validation_sha = sha256_file(validation_path)
    source_predictions_sha = sha256_file(source_predictions_path)
    source_report_sha = sha256_file(source_report_path)
    validation_rows = read_jsonl(validation_path)
    source_report = json.loads(source_report_path.read_text(encoding="utf-8"))
    if source_report.get("selection_split") != "validation":
        raise ValueError("source generation report is not validation-selected")
    if source_report.get("fixed_test_opened") is not False:
        raise ValueError("source generation report does not confirm test isolation")
    if set(source_report.get("systems", {})) != EXPECTED_SEEDS:
        raise ValueError("source generation report does not contain exactly seeds 17, 29, and 43")
    source_predictions = read_jsonl(source_predictions_path)
    source_by_seed = defaultdict(dict)
    for row in source_predictions:
        seed = str(row.get("system") or "")
        record_hash = row.get("instruction_sha256")
        if not seed or not record_hash or record_hash in source_by_seed[seed]:
            raise ValueError("source prediction rows have missing or duplicate seed/hash")
        source_by_seed[seed][record_hash] = row
    if set(source_by_seed) != EXPECTED_SEEDS:
        raise ValueError("source predictions do not contain exactly seeds 17, 29, and 43")

    predictions_by_seed = {}
    lineage_by_seed = {}
    run_dirs = sorted(path for path in manifested_dir.glob("seed-*") if path.is_dir())
    if {path.name for path in run_dirs} != EXPECTED_SEEDS:
        raise ValueError("manifested output does not contain exactly seeds 17, 29, and 43")

    for run_dir in run_dirs:
        seed = run_dir.name
        manifest_path = run_dir / "run_manifest.json"
        predictions_path = run_dir / "predictions.jsonl"
        report_path = run_dir / "report.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        config = manifest.get("config", {})
        outputs = manifest.get("outputs", {})
        if manifest.get("evaluation_split") != "instructions_v0.2/validation":
            raise ValueError(f"{seed} run manifest is not validation-scoped")
        if config.get("test_rows_scored") is not False:
            raise ValueError(f"{seed} run manifest does not confirm test isolation")
        if manifest.get("benchmark_input_sha256") != validation_sha:
            raise ValueError(f"{seed} validation input hash differs from its manifest")
        if config.get("source_validation_manifest_sha256") != validation_sha:
            raise ValueError(f"{seed} source validation hash differs from its manifest")
        if config.get("source_predictions_sha256") != source_predictions_sha:
            raise ValueError(f"{seed} source predictions hash differs from its manifest")
        if config.get("source_report_sha256") != source_report_sha:
            raise ValueError(f"{seed} source report hash differs from its manifest")
        predictions_sha = sha256_file(predictions_path)
        if outputs.get("predictions.jsonl") != predictions_sha:
            raise ValueError(f"{seed} packaged predictions hash differs from its manifest")
        report_sha = sha256_file(report_path)
        if outputs.get("report.json") != report_sha:
            raise ValueError(f"{seed} packaged report hash differs from its manifest")
        saved_report = json.loads(report_path.read_text(encoding="utf-8"))
        if (
            saved_report.get("evaluation_split") != manifest.get("evaluation_split")
            or saved_report.get("evaluation_records") != manifest.get("selected_record_count")
            or saved_report.get("selected_record_ids") != manifest.get("selected_record_ids")
            or saved_report.get("input_sha256") != validation_sha
            or saved_report.get("prediction_input_sha256") != source_predictions_sha
            or saved_report.get("generation_report_sha256") != source_report_sha
            or saved_report.get("test_rows_scored") is not False
        ):
            raise ValueError(f"{seed} saved report does not reconcile with its run manifest")
        rows = read_jsonl(predictions_path)
        selected_ids = set(manifest.get("selected_record_ids", []))
        actual_ids = {row.get("record_id") for row in rows}
        if manifest.get("selected_record_count") != len(rows) or actual_ids != selected_ids:
            raise ValueError(f"{seed} prediction IDs/count differ from its run manifest")
        expected_source_rows = source_by_seed.get(seed, {})
        packaged_by_hash = {row.get("instruction_sha256"): row for row in rows}
        if set(packaged_by_hash) != set(expected_source_rows):
            raise ValueError(f"{seed} packaged predictions differ from the source prediction coverage")
        if len(expected_source_rows) != source_report.get("validation_records"):
            raise ValueError(f"{seed} source prediction count differs from the source report")
        for record_hash, packaged in packaged_by_hash.items():
            source = expected_source_rows[record_hash]
            for field in (
                "task", "reference", "hypothesis", "empty", "copies_instruction",
                "has_control_token", "adjacent_repetition_rate",
            ):
                if field not in source or field not in packaged:
                    continue
                if packaged.get(field) != source.get(field):
                    raise ValueError(f"{seed} {field} differs from source prediction for {record_hash}")
        predictions_by_seed[seed] = rows
        lineage_by_seed[seed] = {
            "run_manifest_sha256": sha256_file(manifest_path),
            "predictions_sha256": predictions_sha,
            "saved_report_sha256": report_sha,
            "records": len(rows),
        }

    return (
        {
            "validation_sha256": validation_sha,
            "source_predictions_sha256": source_predictions_sha,
            "source_report_sha256": source_report_sha,
            "manifested_runs": lineage_by_seed,
        },
        {"validation_rows": validation_rows, "predictions_by_seed": predictions_by_seed},
    )


def run(validation_path: Path = DEFAULT_VALIDATION,
        manifested_dir: Path = DEFAULT_MANIFESTED_DIR,
        source_predictions_path: Path = DEFAULT_SOURCE_PREDICTIONS,
        source_report_path: Path = DEFAULT_SOURCE_REPORT,
        output_dir: Path = DEFAULT_OUTPUT) -> dict:
    lineage, inputs = load_manifested_predictions(
        validation_path, manifested_dir, source_predictions_path, source_report_path,
    )
    report = summarize_predictions(inputs["validation_rows"], inputs["predictions_by_seed"])
    report["lineage"] = lineage
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "diagnostics.json"
    output_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return {"report": report, "output_path": output_path}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--manifested-dir", type=Path, default=DEFAULT_MANIFESTED_DIR)
    parser.add_argument("--source-predictions", type=Path, default=DEFAULT_SOURCE_PREDICTIONS)
    parser.add_argument("--source-report", type=Path, default=DEFAULT_SOURCE_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = run(
        args.validation, args.manifested_dir, args.source_predictions,
        args.source_report, args.output_dir,
    )
    summary = result["report"]
    print(json.dumps({
        "output": str(result["output_path"]),
        "records_per_seed": summary["records_per_seed"],
        "seeds": sorted(summary["seeds"]),
        "test_rows_scored": summary["test_rows_scored"],
        "validation_sha256": summary["lineage"]["validation_sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
