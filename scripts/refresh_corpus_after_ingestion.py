#!/usr/bin/env python3
"""Rebuild corpus-derived local views, package previews, and README figures."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
START_MARKER = "<!-- AUTO-CORPUS-METRICS:START -->"
END_MARKER = "<!-- AUTO-CORPUS-METRICS:END -->"
PIPELINE_COMMANDS = (
    ("ingest_jambu_garhwali.py", ("--offline",)),
    ("ingest_garhwali_language_library.py", ()),
    ("verify_ingestion.py", ()),
    ("dedup_report.py", ()),
    ("prepare_text_corpus.py", ()),
    ("build_all_data_view.py", ()),
    ("clean_text_corpus.py", ()),
    ("deep_cleanup.py", ()),
    ("tag_language_quality.py", ()),
    ("segment_text_corpus.py", ()),
    ("build_dataset_splits.py", ()),
    ("build_language_resources.py", ()),
    ("build_garhwali_benchmark.py", ()),
    ("build_instruction_dataset.py", ()),
    ("build_instruction_accuracy_split.py", ()),
    ("build_quality_tiers.py", ()),
    ("build_recommended_text_view.py", ()),
    ("build_huggingface_dataset.py", (
        "--profile", "all-data",
    )),
    ("build_huggingface_dataset.py", (
        "--profile", "public",
    )),
    ("build_hf_reference_index.py", ()),
    ("generate_project_file_map.py", ()),
)


def replace_metrics_block(readme: str, table: str) -> str:
    if readme.count(START_MARKER) != 1 or readme.count(END_MARKER) != 1:
        raise ValueError("README must contain exactly one auto-corpus-metrics marker pair")
    start = readme.index(START_MARKER) + len(START_MARKER)
    end = readme.index(END_MARKER)
    if end < start:
        raise ValueError("README corpus-metrics markers are out of order")
    return readme[:start] + "\n" + table.rstrip() + "\n" + readme[end:]


def configure_environment(environment: dict[str, str]) -> dict[str, str]:
    version = environment.setdefault("GARHWALI_RELEASE_VERSION", "0.2.1").removeprefix("v")
    environment.setdefault(
        "GARHWALI_HF_ALL_DATA_OUTPUT",
        f"data/huggingface/garhwali-language-lab-all-data-v{version}-local",
    )
    environment.setdefault(
        "GARHWALI_HF_PUBLIC_OUTPUT",
        f"data/huggingface/garhwali-language-lab-v{version}-staging",
    )
    return environment


def run_pipeline(root: Path = ROOT, runner=subprocess.run,
                 environment: dict[str, str] | None = None) -> None:
    environment = configure_environment(dict(os.environ) if environment is None else environment)
    for script, arguments in PIPELINE_COMMANDS:
        arguments = list(arguments)
        if script == "build_huggingface_dataset.py":
            output = (
                environment["GARHWALI_HF_ALL_DATA_OUTPUT"]
                if "all-data" in arguments else environment["GARHWALI_HF_PUBLIC_OUTPUT"]
            )
            arguments.extend(("--output", output))
        command = [sys.executable, str(root / "scripts" / script), *arguments]
        runner(command, cwd=root, check=True, env=environment)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_metrics(root: Path = ROOT, environment: dict[str, str] | None = None) -> dict:
    environment = configure_environment(dict(os.environ) if environment is None else environment)
    text_report = read_json(root / "data/processed/text/report.json")
    segment_report = read_json(root / "data/processed/model_ready/segments/report.json")
    quality_report = read_json(root / "data/processed/model_ready/quality_v2/report.json")
    all_manifest = read_json(
        root / environment["GARHWALI_HF_ALL_DATA_OUTPUT"] / "manifest.json"
    )
    reference_index = read_json(
        root / environment["GARHWALI_HF_PUBLIC_OUTPUT"] / "reference_index_manifest.json"
    )
    wave = read_json(root / "data/extracted/web_goldmines/report.json")
    jambu = read_json(root / "corpus/jambu_garhwali_manifest.json")
    language_library = read_json(root / "corpus/garhwali_language_library_manifest.json")

    tokens = 0
    with (root / "data/processed/text/canonical.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                tokens += len(json.loads(line)["text"].split())

    all_package_rows = sum(
        details["records"] for details in all_manifest.get("configs", {}).values()
    )
    return {
        "source_files": text_report["source_files"],
        "source_records": text_report["source_records"],
        "exact_unique_parent_texts": text_report["unique_texts"],
        "duplicate_parent_rows": text_report["duplicate_rows"],
        "empty_records": text_report["empty_records"],
        "text_characters": text_report["characters"],
        "whitespace_tokens": tokens,
        "source_segments": segment_report["source_segments"],
        "exact_unique_segments": segment_report["unique_segments"],
        "cross_split_segment_leakage": segment_report["remaining_cross_split_segments"],
        "quality_tiers": quality_report["datasets"]["text"]["tiers"],
        "all_data_package_rows_overlapping_views": all_package_rows,
        "public_profile_package_rows_overlapping_views": reference_index["public_profile_package_rows"],
        "public_profile_rows_with_content": reference_index["records_with_content_in_public_profile"],
        "reference_index_rows": reference_index["records"],
        "reference_sources": reference_index["source_catalog_records"],
        "reference_source_links": reference_index["record_source_links"],
        "web_goldmine_candidates_before_dedup": wave["candidate_records_before_dedup"],
        "web_goldmine_exact_duplicates_skipped": wave["exact_duplicate_records_against_existing_or_within_wave"],
        "web_goldmine_exact_new_records": wave["exact_new_unique_records"],
        "web_goldmine_source_characters": wave["exact_new_unique_characters"],
        "web_goldmine_rights_status": wave["rights_status"],
        "web_goldmine_public_rows_added": wave["public_huggingface_rows_added"],
        "jambu_source_records": jambu.get("records", 0),
        "jambu_unique_forms": jambu.get("unique_forms", 0),
        "jambu_exact_overlaps": jambu.get("exact_overlap_with_existing_unique_forms", 0),
        "jambu_historically_new_vs_other_sources": jambu.get("exact_new_unique_forms", 0),
        "jambu_already_in_current_corpus": jambu.get("already_in_current_corpus_unique_forms", 0),
        "jambu_net_new_this_refresh": max(
            0, jambu.get("unique_forms", 0) - jambu.get("already_in_current_corpus_unique_forms", 0)
        ),
        "language_library_source_records": language_library.get("source_records", 0),
        "language_library_unique_strings": language_library.get("unique_surface_forms", 0),
        "language_library_exact_overlaps": language_library.get("exact_overlap_with_existing_unique_forms", 0),
        "language_library_exact_new_strings": language_library.get("exact_new_unique_forms", 0),
        "language_library_records_by_type": language_library.get("records_by_type", {}),
        "public_huggingface_remote_changed": False,
    }


def render_metrics_table(metrics: dict) -> str:
    rows = (
        ("Canonical source records before exact deduplication", metrics["source_records"]),
        ("Exact-unique parent texts", metrics["exact_unique_parent_texts"]),
        ("Parent text characters", metrics["text_characters"]),
        ("Whitespace tokens (engineering count)", metrics["whitespace_tokens"]),
        ("Exact-unique prepared segments", metrics["exact_unique_segments"]),
        ("Segment occurrences before exact deduplication", metrics["source_segments"]),
        ("Text quality tiers (strict / experimental / rights-pending)", "/".join(
            f"{metrics['quality_tiers'].get(key, 0):,}"
            for key in ("strict_gold_candidate", "experimental_review", "high_quality_rights_pending")
        )),
        ("All-data local package rows (overlapping views)", metrics["all_data_package_rows_overlapping_views"]),
        ("Public-profile package rows, including redacted catalog (overlapping views)", metrics["public_profile_package_rows_overlapping_views"]),
        ("Public-profile rows with content (overlapping views)", metrics["public_profile_rows_with_content"]),
        ("Metadata-only reference-index rows", metrics["reference_index_rows"]),
        ("Reference sources / record-source links", f"{metrics['reference_sources']:,} / {metrics['reference_source_links']:,}"),
        ("New web candidates before deduplication", metrics["web_goldmine_candidates_before_dedup"]),
        ("Exact duplicate web records skipped", metrics["web_goldmine_exact_duplicates_skipped"]),
        ("Exact-new web records (rights-unassessed; local experimental)", metrics["web_goldmine_exact_new_records"]),
        ("New web-source characters before package normalization", metrics["web_goldmine_source_characters"]),
        ("New web rows in public Hugging Face profile", metrics["web_goldmine_public_rows_added"]),
        ("Jambu source rows / distinct Garhwali forms", f"{metrics['jambu_source_records']:,} / {metrics['jambu_unique_forms']:,}"),
        ("Jambu forms already present in the pre-refresh corpus", metrics["jambu_already_in_current_corpus"]),
        ("Jambu net-new forms this refresh", metrics["jambu_net_new_this_refresh"]),
        ("Jambu historically new forms versus non-Jambu sources", metrics["jambu_historically_new_vs_other_sources"]),
        ("Language Library static rows / distinct strings", f"{metrics['language_library_source_records']:,} / {metrics['language_library_unique_strings']:,}"),
        ("Language Library exact-new strings after cross-corpus deduplication", metrics["language_library_exact_new_strings"]),
        ("Language Library source rows by type", ", ".join(
            f"{kind} {count:,}" for kind, count in sorted(metrics["language_library_records_by_type"].items())
        )),
    )
    return "\n".join(
        ["| Metric | Current local working tree |", "| --- | ---: |"]
        + [f"| {label} | {value:,} |" if isinstance(value, int) else f"| {label} | {value} |"
           for label, value in rows]
    )


def refresh(root: Path = ROOT, runner=subprocess.run,
            environment: dict[str, str] | None = None) -> dict:
    environment = configure_environment(dict(os.environ) if environment is None else environment)
    run_pipeline(root, runner=runner, environment=environment)
    metrics = collect_metrics(root, environment=environment)
    metrics_path = root / "data/extracted/current_corpus_metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    readme_path = root / "README.md"
    readme_path.write_text(
        replace_metrics_block(readme_path.read_text(encoding="utf-8"), render_metrics_table(metrics)),
        encoding="utf-8",
    )
    return metrics


if __name__ == "__main__":
    print(json.dumps(refresh(), ensure_ascii=False, indent=2, sort_keys=True))
