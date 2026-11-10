#!/usr/bin/env python3
"""Build a local, source-aware Garhwali text training candidate package.

This is an additive local profile. It does not alter published datasets or
change any source-level rights, quality, or training-eligibility flags.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from build_huggingface_dataset import normalized_text_key
from export_licensed_sources import build_benchmark_exports
from garhwali_lab.hashing import sha256_file
from garhwali_lab.io import read_jsonl


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data/training/garhwali-text-training-v0.2"
META_TRAIN = ROOT / "data/kaggle/garhwali-screened-text-v0.1/train.csv"
META_CONTEXT = ROOT / "data/kaggle/garhwali-screened-text-v0.1/short_utterances.csv"
BENCHMARK_DIR = ROOT / "data/processed/evaluation/garhwali_bench/v0.2-draft"
PDF_REPORT = ROOT / "research/incoming-pdf-ingestion-2026-09-16.json"
PDF_MODEL_REPORT = ROOT / "data/processed/model_ready/indicbert_pdf_domain/report.json"

MIN_WORDS = 5
PDF_SOURCE_SEGMENT_ROWS = {
    "incoming_english_hindi_garhwali_dictionary": 9214,
    "incoming_gadwali_sahitya": 555,
    "incoming_garhwali_bhasha_linguistic_grammatical_study": 1682,
    "incoming_garhwali_hindi_dictionary": 12453,
    "incoming_garhwali_language_and_culture": 3329,
    "incoming_chandola_syntactic_sketch": 720,
    "incoming_gadwali_lokgeet": 0,
}

FIELDS = [
    "id", "text", "language", "script", "split", "source_split",
    "source_id", "source_record_id", "source_document_id", "source_file",
    "source_title", "author", "publication_year", "source_url",
    "source_revision", "source_snapshot_sha256", "source_pdf_sha256",
    "source_printed_pages", "source_pdf_pages", "license_id", "license_url",
    "rights_status", "rights_evidence_url", "attribution", "modifications",
    "quality_status", "quality_flags", "native_reviewed",
    "source_training_eligible", "project_training_eligible",
    "source_public_release_cleared", "project_public_release_cleared",
    "training_eligibility_decision_id",
    "candidate_for_experimental_training", "benchmark_id", "benchmark_split",
    "benchmark_overlap_notice", "inclusion_reason", "text_sha256",
    "word_count", "character_count",
]


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def parse_json_cell(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"Expected a JSON-encoded CSV value, got {value!r}") from error


def record(
    *,
    identity: str,
    text: str,
    source_id: str,
    source_record_id: str,
    source_document_id: str,
    split: str,
    source_split: str,
    script: str,
    license_id: str,
    license_url: str,
    rights_status: str,
    rights_evidence_url: str,
    attribution: str,
    quality_status: str,
    quality_flags: list[str],
    native_reviewed: bool,
    source_training_eligible: bool,
    project_training_eligible: bool,
    source_public_release_cleared: bool | None,
    project_public_release_cleared: bool | None,
    training_eligibility_decision_id: str,
    candidate: bool,
    inclusion_reason: str,
    source_file: str = "",
    source_title: str = "",
    author: str = "",
    publication_year: str | int = "",
    source_url: str = "",
    source_revision: str = "",
    source_snapshot_sha256: str = "",
    source_pdf_sha256: str = "",
    source_printed_pages: str | int = "",
    source_pdf_pages: str | int = "",
    modifications: str = "",
    benchmark_id: str = "",
    benchmark_split: str = "",
    benchmark_overlap_notice: str = "",
) -> dict:
    text = str(text or "").strip()
    if not text:
        raise ValueError(f"Empty text for {identity}")
    if not source_id or not source_record_id:
        raise ValueError(f"Missing source identity for {identity}")
    if not license_id or not license_url or not rights_status:
        raise ValueError(f"Missing rights lineage for {identity}")
    return {
        "id": identity,
        "text": text,
        "language": "gbm",
        "script": script or "",
        "split": split,
        "source_split": source_split,
        "source_id": source_id,
        "source_record_id": source_record_id,
        "source_document_id": source_document_id or source_record_id,
        "source_file": source_file,
        "source_title": source_title,
        "author": author,
        "publication_year": publication_year,
        "source_url": source_url,
        "source_revision": source_revision,
        "source_snapshot_sha256": source_snapshot_sha256,
        "source_pdf_sha256": source_pdf_sha256,
        "source_printed_pages": source_printed_pages,
        "source_pdf_pages": source_pdf_pages,
        "license_id": license_id,
        "license_url": license_url,
        "rights_status": rights_status,
        "rights_evidence_url": rights_evidence_url,
        "attribution": attribution,
        "modifications": modifications,
        "quality_status": quality_status,
        "quality_flags": quality_flags,
        "native_reviewed": native_reviewed,
        "source_training_eligible": source_training_eligible,
        "project_training_eligible": project_training_eligible,
        "source_public_release_cleared": source_public_release_cleared,
        "project_public_release_cleared": project_public_release_cleared,
        "training_eligibility_decision_id": training_eligibility_decision_id,
        "candidate_for_experimental_training": candidate,
        "benchmark_id": benchmark_id,
        "benchmark_split": benchmark_split,
        "benchmark_overlap_notice": benchmark_overlap_notice,
        "inclusion_reason": inclusion_reason,
        "text_sha256": sha256_bytes(text.encode("utf-8")),
        "word_count": len(text.split()),
        "character_count": len(text),
    }


def meta_record(row: dict, *, context: bool = False, split_override: str | None = None) -> dict:
    record_ids = parse_json_cell(row.get("source_record_ids"), [])
    if len(record_ids) != 1:
        raise ValueError(f"Expected one Meta source record for {row.get('id')}")
    text = row.get("text") or ""
    words = len(text.split())
    if context and words >= MIN_WORDS:
        raise ValueError(f"Long text incorrectly routed to context: {row.get('id')}")
    if not context and words < MIN_WORDS:
        raise ValueError(f"Short text incorrectly routed to training: {row.get('id')}")
    decision_id = str(row.get("training_eligibility_decision_id") or "")
    exact_meta_decision = decision_id == "meta_omnilingual_cc_by_4_0_training_2026_10_06"
    project_training_eligible = (
        not context
        and str(row.get("recommended_for_training", "false")).lower() == "true"
        and exact_meta_decision
    )
    split = "context" if context else (split_override or "train")
    return record(
        identity=row["id"], text=text, source_id=row["source_id"],
        source_record_id=record_ids[0], source_document_id=record_ids[0],
        split=split, source_split=row.get("split", "train"),
        script=row.get("script", ""), license_id=row["source_license_id"],
        license_url=row["license_url"], rights_status=row["rights_status"],
        rights_evidence_url=row["rights_evidence_url"], attribution=row["attribution"],
        quality_status=row["quality_status"],
        quality_flags=parse_json_cell(row.get("quality_flags"), []),
        native_reviewed=str(row.get("native_reviewed", "false")).lower() == "true",
        source_training_eligible=str(row.get("source_training_eligible_before_project_decision", "false")).lower() == "true",
        project_training_eligible=project_training_eligible,
        source_public_release_cleared=True,
        project_public_release_cleared=exact_meta_decision,
        training_eligibility_decision_id=decision_id,
        candidate=project_training_eligible,
        inclusion_reason=(
            "Exact Meta CC BY 4.0 project decision; deterministic record-level 90/10 train/development split; automated screening only; not native-reviewed."
            if project_training_eligible else
            "Short context row; excluded from the default training split by the source profile."
        ),
        source_title="Meta Omnilingual ASR Corpus",
        source_url=row.get("source_dataset_url", ""),
    )


def source_record(row: dict) -> tuple[str, dict]:
    words = len(str(row.get("text_normalized") or "").split())
    source_split = str(row.get("benchmark_split") or "")
    if source_split in {"train", "validation", "test"}:
        split = "review_queue"
        candidate = source_split == "train" and words >= MIN_WORDS
        reason = (
            "Source train row with at least five whitespace tokens; rights/quality/release review is pending, so excluded from the model-ready train split."
            if candidate else
            "Preserved source row for audit only; excluded from model-ready train and evaluation splits."
        )
    else:
        raise ValueError(f"Unexpected source split {source_split!r} for {row.get('record_id')}")

    return split, record(
        identity=row["record_id"], text=row["text_normalized"],
        source_id=row["source_id"], source_record_id=row["source_record_id"],
        source_document_id=row["source_record_id"], split=split,
        source_split=source_split, script=row.get("script", "Deva"),
        license_id=row["license_id"], license_url=row["license_url"],
        rights_status=row["rights_status"],
        rights_evidence_url=row.get("rights_evidence_url") or "",
        attribution=row.get("attribution") or "", quality_status=row.get("quality_status") or "unreviewed",
        quality_flags=list(row.get("quality_flags") or []),
        native_reviewed=bool(row.get("native_reviewed", False)),
        source_training_eligible=bool(row.get("training_eligible", False)),
        project_training_eligible=bool(row.get("training_eligible", False)),
        source_public_release_cleared=bool(row.get("public_release_cleared", False)),
        project_public_release_cleared=bool(row.get("public_release_cleared", False)),
        training_eligibility_decision_id="",
        candidate=candidate, inclusion_reason=reason,
        source_file=row.get("source_file") or "", source_title=row.get("title") or "",
        author=row.get("author") or "", publication_year=row.get("publication_year") or "",
        source_url=row.get("source_url") or row.get("rights_evidence_url") or "",
        source_revision=row.get("source_revision") or row.get("source_version") or "",
        source_snapshot_sha256=row.get("source_snapshot_sha256") or "",
        source_pdf_sha256=row.get("source_pdf_sha256") or "",
        source_printed_pages=row.get("source_printed_pages") or "",
        source_pdf_pages=row.get("source_pdf_pages") or "",
        modifications=row.get("modifications") or "",
        benchmark_id=row.get("benchmark_id") or "",
        benchmark_split=source_split,
        benchmark_overlap_notice=row.get("benchmark_overlap_notice") or "",
    )


def csv_value(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if value is None:
        return ""
    return value


def write_jsonl(path: Path, rows: list[dict]) -> str:
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8", newline="\n")
    return sha256_bytes(payload.encode("utf-8"))


def write_csv(path: Path, rows: list[dict]) -> str:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: csv_value(row.get(key)) for key in FIELDS})
    return sha256_file(path)


def pdf_queue_rows() -> tuple[list[dict], dict]:
    report = read_json(PDF_REPORT)
    model_report = read_json(PDF_MODEL_REPORT)
    rows = []
    for item in report.get("documents", []):
        source_id = item.get("source_id", "")
        metadata = item.get("bibliographic_metadata") or {}
        duplicate = bool(item.get("exact_duplicate_of"))
        rows.append({
            "source_id": source_id,
            "title": item.get("title", ""),
            "author": item.get("author", ""),
            "publication_year": item.get("publication_year", ""),
            "pdf_path": item.get("file", ""),
            "pdf_sha256": item.get("sha256", ""),
            "pdf_pages": item.get("pages", 0),
            "extracted_page_records": item.get("extracted_records", 0),
            "source_associated_segments_in_all_data": PDF_SOURCE_SEGMENT_ROWS.get(source_id, 0),
            "rights_status": metadata.get("rights_status", "unknown"),
            "license_or_rights_statement": metadata.get("license_or_rights_statement", ""),
            "rights_evidence_url": metadata.get("rights_evidence_url", ""),
            "duplicate_of": item.get("exact_duplicate_of") or "",
            "training_release_disposition": (
                "duplicate_already_ingested; do not add a second copy" if duplicate else
                "excluded_from_this_candidate_until_reuse_scope_is_resolved"
            ),
        })
    model_splits = model_report.get("records", {})
    pdf_summary = {
        "supplied_pdf_files": report.get("input_pdfs"),
        "unique_pdfs_extracted": report.get("unique_pdfs_extracted"),
        "active_page_records": report.get("records"),
        "unique_text_segments_in_all_data": 27926,
        "source_associated_segment_rows_can_overlap": True,
        "previous_indicbert_pdf_domain_run": {
            "train_segments": model_splits.get("train", 0),
            "validation_segments": model_splits.get("validation", 0),
            "heldout_test_segments": model_splits.get("test", 0),
            "test_used_for_training_or_selection": model_report.get("test_used_for_training_or_selection"),
        },
        "pdf_model_output_report": "research/indicbert-pdf-domain-extended-2026-09-16.md",
        "note": "PDF-derived text is inventoried but excluded from the current combined candidate profile because the source rights metadata is unresolved, restricted, or limited-reproduction.",
    }
    return rows, pdf_summary


def build() -> dict:
    required = [META_TRAIN, META_CONTEXT, PDF_REPORT, PDF_MODEL_REPORT]
    required.extend(BENCHMARK_DIR / f"text_recommended__{split}.jsonl" for split in ("train", "validation", "test"))
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("Required local inputs are missing: " + ", ".join(missing))

    partitions: dict[str, list[dict]] = {name: [] for name in ("train", "validation", "context", "review_queue")}
    source_input_rows = []
    meta_rows = read_csv(META_TRAIN)
    ranked_meta_rows = sorted(
        meta_rows,
        key=lambda row: hashlib.sha256(
            (row["id"] + "|validation-v0.2").encode("utf-8")
        ).hexdigest(),
    )
    validation_count = round(len(ranked_meta_rows) * 0.10)
    validation_ids = {row["id"] for row in ranked_meta_rows[:validation_count]}
    for row in meta_rows:
        item = meta_record(row, split_override=("validation" if row["id"] in validation_ids else "train"))
        partitions[item["split"]].append(item)
    for row in read_csv(META_CONTEXT):
        item = meta_record(row, context=True)
        partitions[item["split"]].append(item)

    benchmark_rows = []
    for split in ("train", "validation", "test"):
        path = BENCHMARK_DIR / f"text_recommended__{split}.jsonl"
        for row in read_jsonl(path):
            if row.get("split") != split:
                raise ValueError(f"Split mismatch in {path}: {row.get('example_id')}")
            benchmark_rows.append(row)
    source_exports = build_benchmark_exports(benchmark_rows)
    selected_groups = (
        "obs_tlf_gbm_v1_cc_by_sa_4_0",
        "lsi_1916_public_domain",
    )
    source_group_counts = {}
    for group in selected_groups:
        rows = source_exports[group]
        source_group_counts[group] = len(rows)
        for row in rows:
            split, item = source_record(row)
            partitions[split].append(item)
            source_input_rows.append(row)

    for split in partitions:
        partitions[split].sort(key=lambda item: (item["source_id"], item["id"]))

    # Confirm that examples are unique across all partitions while preserving
    # Unicode combining marks in the duplicate key.
    duplicate_keys: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for split, rows in partitions.items():
        for item in rows:
            key = normalized_text_key(item["text"])
            if not key:
                raise ValueError(f"No normalized text key for {item['id']}")
            duplicate_keys[key].append((split, item["id"]))
    duplicate_groups = {key: values for key, values in duplicate_keys.items() if len(values) > 1}
    if duplicate_groups:
        examples = list(duplicate_groups.values())[:5]
        raise ValueError(f"Normalized duplicate text crosses rows or splits: {examples}")

    if any(row["word_count"] < MIN_WORDS for row in partitions["train"]):
        raise ValueError("A short row entered the training partition")
    for row in partitions["train"]:
        if row["project_training_eligible"] is not True or row["project_public_release_cleared"] is not True:
            raise ValueError(f"A row without project training/release clearance entered train: {row['id']}")
        if row["source_id"] != "meta_omni":
            raise ValueError(f"Unexpected source in model-ready train split: {row['source_id']}")
    if any(row["project_training_eligible"] for row in partitions["review_queue"]):
        raise ValueError("A review-queue row is marked eligible for model training")
    if any(row["language"] != "gbm" for rows in partitions.values() for row in rows):
        raise ValueError("Unexpected language in candidate package")

    pdf_rows, pdf_summary = pdf_queue_rows()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    artifact_hashes = {}
    for split, rows in partitions.items():
        jsonl_path = OUTPUT / f"{split}.jsonl"
        csv_path = OUTPUT / f"{split}.csv"
        artifact_hashes[jsonl_path.name] = write_jsonl(jsonl_path, rows)
        artifact_hashes[csv_path.name] = write_csv(csv_path, rows)

    pdf_path = OUTPUT / "pdf_rights_queue.csv"
    with pdf_path.open("w", encoding="utf-8", newline="") as stream:
        fields = list(pdf_rows[0]) if pdf_rows else []
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(pdf_rows)
    artifact_hashes[pdf_path.name] = sha256_file(pdf_path)

    # Retire filenames from the previous unsafe all-candidate profile so that
    # stale LSI examples cannot be mistaken for a model holdout.
    for stale_name in ("holdout.jsonl", "holdout.csv"):
        stale_path = OUTPUT / stale_name
        if stale_path.exists():
            stale_path.unlink()

    input_paths = [META_TRAIN, META_CONTEXT, PDF_REPORT, PDF_MODEL_REPORT]
    input_paths.extend(BENCHMARK_DIR / f"text_recommended__{split}.jsonl" for split in ("train", "validation", "test"))
    inputs = {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in input_paths}
    rows_by_split = {
        split: {
            "rows": len(rows),
            "words": sum(row["word_count"] for row in rows),
            "characters": sum(row["character_count"] for row in rows),
            "source_counts": dict(sorted(Counter(row["source_id"] for row in rows).items())),
            "license_counts": dict(sorted(Counter(row["license_id"] for row in rows).items())),
        }
        for split, rows in partitions.items()
    }
    manifest = {
        "schema_version": "garhwali-text-training-candidate-v0.2",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_status": "local_meta_subset_training_eligible_with_review_queue",
        "intended_use": "Experimental text-model fine-tuning or continued-pretraining data inspection; not an instruction dataset or benchmark.",
        "minimum_whitespace_tokens_for_train": MIN_WORDS,
        "rows_by_split": rows_by_split,
        "selected_source_export_rows": source_group_counts,
        "normalized_duplicate_groups_across_all_splits": len(duplicate_groups),
        "meta_record_level_validation_split": f"deterministic exact 10% ({validation_count} rows) selected by stable hash from upstream Meta train split; same speakers occur in both splits; development loss monitor only",
        "source_training_eligibility_flags_changed": False,
        "source_public_release_flags_changed": False,
        "pdf_inventory": pdf_summary,
        "inputs": inputs,
        "artifacts_sha256": artifact_hashes,
        "notes": [
            "Only exact Meta Omnilingual rows covered by the project CC BY 4.0 decision and training recommendation enter train/validation.",
            "The original source_training_eligible flag remains distinct from project_training_eligible; the project decision is recorded per row.",
            "Open Bible Stories and 1916 LSI rows stay in review_queue with their original source flags unchanged; they are excluded from optimizer and evaluation splits.",
            "The validation rows are a deterministic record-level slice from the upstream Meta train split; speaker overlap makes them a development loss monitor, not an independent benchmark.",
            "Short Meta rows stay in context. PDF-derived text is separately inventoried and excluded pending source-use resolution.",
            "The Meta values already exist in the current Hub corpus; this package adds a load-ready split view, not new unique text.",
            "No Hugging Face or Kaggle upload and no new model training job is performed by this builder.",
        ],
    }
    manifest_path = OUTPUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    readme = f"""# Garhwali text training profile v0.2

Status: local training profile. This folder has not been published to Hugging Face or Kaggle.

## Load it

The model text is in the text column. The package is plain-text data suitable for causal-language-model experiments or continued pretraining. It is not chat instruction data.

    from datasets import load_dataset

    data = load_dataset(
        "json",
        data_files={{
            "train": "data/training/garhwali-text-training-v0.2/train.jsonl",
            "validation": "data/training/garhwali-text-training-v0.2/validation.jsonl",
        }},
    )

Use only train for optimizer updates and validation for loss monitoring. The validation set is a deterministic record-level slice from the upstream Meta training split; speakers overlap, so it is not an independent benchmark. context.jsonl and review_queue.jsonl must stay out of the default training and evaluation splits.

## Current candidate counts

| Partition | Rows | Intended use |
| --- | ---: | --- |
| train | {rows_by_split['train']['rows']:,} | Meta rows cleared by the project training decision, each at least {MIN_WORDS} whitespace tokens |
| validation | {rows_by_split['validation']['rows']:,} | Record-level Meta development monitor; speaker overlap remains |
| context | {rows_by_split['context']['rows']:,} | Short Meta rows kept separate from default LM training |
| review_queue | {rows_by_split['review_queue']['rows']:,} | OBS and LSI candidates with training/public-release flags false |

The model-ready split is single-source and has one license:

- Meta Omnilingual: {rows_by_split['train']['rows'] + rows_by_split['validation']['rows']:,} rows across train/validation, CC BY 4.0; automated screen, not native-reviewed.

## Rights and review

Every row keeps its source, license, rights evidence, quality flags, review state, and original source split. The original source-level training flag is preserved separately from the exact project training decision that applies to the Meta rows. OBS and LSI records stay in review_queue; their source training and public-release flags remain false, and they overlap the local GarhwaliBench v0.2 draft.

The supplied PDFs are listed in pdf_rights_queue.csv and are not included as text here. Six unique PDFs produced 769 page records and were used in an earlier IndicBERT domain experiment ({pdf_summary['previous_indicbert_pdf_domain_run']['train_segments']:,} train segments); current rights metadata is copyrighted, unresolved, or limited-reproduction. Resolve exact source terms before adding more PDF text or publishing a model trained on it.

The Meta texts are already present in the current Hub corpus. This profile adds a ready-to-load train/development split, but does not add new unique passages. The separate speech Hub repository and the local ASR curriculum provide a larger model-training path (human/provider transcript rows plus optional confidence-weighted machine drafts); keep ASR audio/transcripts separate from this text LM profile.

## Rebuild

From the repository root, run:

    PYTHONPATH=scripts .venv/bin/python scripts/build_model_training_candidate.py

Build inputs and artifact hashes are recorded in manifest.json.
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    manifest["artifacts_sha256"]["README.md"] = sha256_file(OUTPUT / "README.md")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2, sort_keys=True))
