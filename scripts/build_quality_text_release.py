#!/usr/bin/env python3
"""Build an additive, screened Garhwali text view for Hugging Face and Kaggle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from scripts.build_huggingface_dataset import (
    META_OMNILINGUAL_TRAINING_DECISION,
    build_quality_screened_meta_text,
    normalized_text_key,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "data/huggingface/garhwali-language-lab-v0.2.7-staging"
DEFAULT_BASE_CARD = ROOT / "data/huggingface/garhwali-language-lab-v0.2.7-upload/README.md"
DEFAULT_HF_OUTPUT = ROOT / "data/huggingface/garhwali-screened-text-v0.1-upload"
DEFAULT_KAGGLE_OUTPUT = ROOT / "data/kaggle/garhwali-screened-text-v0.1"
SOURCE_RELEASE_ID = "garhwali-language-lab-v0.2.7"
RELEASE_PATH = "releases/v0.2.8/data/screened_meta_gbm/train-00000.jsonl"
HF_CONFIG = "screened_meta_gbm"
SHORT_CONFIG = "short_utterances_meta_gbm"
KAGGLE_DATASET_ID = "rushilrawat1/garhwali-screened-text-candidates"

FIELDS = [
    "id", "text", "language", "script", "split", "source_config", "source_id",
    "source_record_ids", "source_dataset_url", "source_license_id", "license_url",
    "rights_status", "rights_evidence_url", "rights_evidence_snapshot_sha256",
    "attribution", "quality_status", "quality_tiers", "quality_flags",
    "source_split_overlap_status", "source_split_overlap_source_ids",
    "recommended_for_training", "project_recommendation_status", "native_reviewed",
    "training_profile", "training_eligibility_decision_id",
    "source_training_eligible_before_project_decision", "text_sha256", "word_count",
    "character_count",
]

FEATURES = [
    {"name": name, "dtype": dtype} for name, dtype in (
        ("id", "string"), ("text", "string"), ("language", "string"),
        ("script", "string"), ("split", "string"), ("source_config", "string"),
        ("source_id", "string"), ("source_dataset_url", "string"),
        ("source_license_id", "string"), ("license_url", "string"),
        ("rights_status", "string"), ("rights_evidence_url", "string"),
        ("rights_evidence_snapshot_sha256", "string"), ("attribution", "string"),
        ("quality_status", "string"), ("source_split_overlap_status", "string"),
        ("project_recommendation_status", "string"), ("training_profile", "string"),
        ("training_eligibility_decision_id", "string"), ("text_sha256", "string"),
        ("word_count", "int64"), ("character_count", "int64"),
    )
] + [
    {"name": name, "list": "string"} for name in (
        "source_record_ids", "quality_tiers", "quality_flags", "source_split_overlap_source_ids",
    )
] + [
    {"name": name, "dtype": "bool"} for name in (
        "recommended_for_training", "native_reviewed",
        "source_training_eligible_before_project_decision",
    )
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_source(source: Path) -> tuple[dict, dict, dict]:
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("release_id") != SOURCE_RELEASE_ID:
        raise ValueError(f"Expected pinned source {SOURCE_RELEASE_ID}, got {manifest.get('release_id')!r}")
    rows = {"text": [], "text_expansion": []}
    hashes = {"manifest.json": sha256_file(manifest_path)}
    for config in rows:
        paths = sorted((source / "data" / config).glob("train-*.jsonl"))
        if not paths:
            raise FileNotFoundError(f"No train JSONL shards for {config}")
        for path in paths:
            relative = path.relative_to(source).as_posix()
            hashes[relative] = sha256_file(path)
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.strip():
                    try:
                        value = json.loads(line)
                    except json.JSONDecodeError as error:
                        raise ValueError(f"Invalid JSON at {relative}:{line_number}") from error
                    if not isinstance(value, dict):
                        raise ValueError(f"Expected an object at {relative}:{line_number}")
                    rows[config].append(value)
    return manifest, rows, hashes


def project_row(row: dict) -> dict:
    provenance = row.get("provenance") or []
    rights_basis = row.get("public_rights_basis") or []
    if (
        len(provenance) != 1 or len(rights_basis) != 1
        or any(not isinstance(item, dict) or item.get("source_id") != "meta_omni"
               for item in [*provenance, *rights_basis])
    ):
        raise ValueError(f"Mixed or missing source-rights lineage for {row.get('id')}")
    source = provenance[0]
    rights = rights_basis[0]
    for item in (source, rights):
        if (
            item.get("source_url") != META_OMNILINGUAL_TRAINING_DECISION["source_url"]
            or item.get("license_id") != "CC-BY-4.0"
            or item.get("rights_status") != "upstream_meta_cc_by_4_0"
        ):
            raise ValueError(f"Source rights do not match the pinned Meta decision for {row.get('id')}")
    if source.get("record_id") != rights.get("record_id"):
        raise ValueError(f"Provenance and rights basis point to different records for {row.get('id')}")
    if not source.get("record_id"):
        raise ValueError(f"Expected one Meta provenance record for {row.get('id')}")
    text = row["text"]
    return {
        "id": str(row["id"]), "text": text, "language": row["language"],
        "script": row.get("script") or source.get("script") or "", "split": "train",
        "source_config": row["source_config"], "source_id": source["source_id"],
        "source_record_ids": [source["record_id"]], "source_dataset_url": source["source_url"],
        "source_license_id": source["license_id"], "license_url": source["license_url"],
        "rights_status": source["rights_status"],
        "rights_evidence_url": META_OMNILINGUAL_TRAINING_DECISION["evidence_urls"][0],
        "rights_evidence_snapshot_sha256": META_OMNILINGUAL_TRAINING_DECISION["rights_evidence_sha256"],
        "attribution": source["attribution"], "quality_status": row["quality_status"],
        "quality_tiers": list(row.get("quality_tiers") or []),
        "quality_flags": list(row.get("record_quality_flags") or []),
        "source_split_overlap_status": row["source_split_overlap_status"],
        "source_split_overlap_source_ids": list(row.get("source_split_overlap_source_ids") or []),
        "recommended_for_training": True,
        "project_recommendation_status": row["project_recommendation_status"],
        "native_reviewed": False, "training_profile": row["training_profile"],
        "training_eligibility_decision_id": row["training_eligibility_decision_id"],
        "source_training_eligible_before_project_decision": bool(
            source.get("training_eligible_before_project_decision")
        ),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "word_count": len(text.split()), "character_count": len(text),
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                key: json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                if isinstance(value, list) else value for key, value in row.items()
            })


def update_hf_card(card: str, manifest: dict) -> str:
    def replace_wrapped_text(value: str, old: str, new: str, error: str) -> str:
        # Dataset cards may wrap a paragraph differently in fixtures and in
        # the rendered release; preserve the prose while matching any wraps.
        pattern = re.compile(r"\s+".join(map(re.escape, old.split())))
        updated, count = pattern.subn(lambda _: new, value, count=1)
        if count != 1:
            raise ValueError(error)
        return updated

    if f"config_name: {HF_CONFIG}" in card or f"config_name: {SHORT_CONFIG}" in card:
        raise ValueError("Base card already contains a screened Garhwali text config")
    short_path = "releases/v0.2.8/data/short_utterances_meta_gbm/train-00000.jsonl"
    block = (
        f"- config_name: {HF_CONFIG}\n  data_files:\n  - split: train\n    path: {RELEASE_PATH}\n"
        f"- config_name: {SHORT_CONFIG}\n  data_files:\n  - split: train\n    path: {short_path}\n"
    )
    if "dataset_info:" not in card:
        raise ValueError("Base card is missing dataset_info")
    card = card.replace("dataset_info:", block + "dataset_info:", 1)
    pattern = re.compile(r"(?m)^dataset_info:\s*(\[.*\])\s*$")
    match = pattern.search(card)
    if not match:
        raise ValueError("Could not parse dataset_info JSON")
    info = json.loads(match.group(1))
    info.extend([
        {"config_name": HF_CONFIG, "features": FEATURES},
        {"config_name": SHORT_CONFIG, "features": FEATURES},
    ])
    card = card[:match.start(1)] + json.dumps(info, ensure_ascii=False, separators=(",", ":")) + card[match.end(1):]
    card = card.replace("Release: **garhwali-language-lab-v0.2.7**", "Release: **garhwali-language-lab-v0.2.8**", 1)
    for filename in (
        "DEVELOPER_QUICKSTART.md",
        "DATASET_SCHEMA.md",
        "search_garhwali_lexicon.py",
    ):
        card = card.replace(
            f"/releases/v0.2.7/{filename}",
            f"/releases/v0.2.8/{filename}",
        )
    section = f"""
## Clean screened text config

The v0.2.8 addition exposes two purpose-labeled configs. `{HF_CONFIG}` contains
**{manifest['training_records']:,}** non-empty, normalized-deduplicated
Garhwali transcript texts suited to sentence-level experimental LM training
({manifest['training_words']:,} whitespace-separated words). `{SHORT_CONFIG}`
preserves **{manifest['short_utterance_records']:,}** short, nonblank
utterances for context; they are not recommended for general LM training.
All 1,951 selected text values were found verbatim in the earlier v0.2.7
`text`/`text_expansion` configs. This release adds a source-decided,
quality-filtered training surface, not new unique transcript content.
Blank values, normalized duplicates, reference tables, machine ASR drafts,
and very short utterances are not in the training config. Each row keeps source
record IDs, attribution, rights evidence, and quality fields. This is automated
screening, **not native-speaker review** or verified linguistic ground truth.

| Configuration | Rows | Use |
| --- | ---: | --- |
| `{HF_CONFIG}` | {manifest['training_records']:,} | Experimental sentence-level text training candidates |
| `{SHORT_CONFIG}` | {manifest['short_utterance_records']:,} | Short-utterance context; not general LM training |

```python
from datasets import load_dataset
data = load_dataset("rushilrawat/garhwali-corpus", "{HF_CONFIG}", split="train")
print(data[0]["text"])
```
"""
    anchor = "\n## Developer quick start"
    if anchor in card:
        card = card.replace(anchor, "\n" + section + anchor, 1)
    else:
        card += "\n" + section

    # Keep the prominent release totals and configuration table in step with
    # the additive v0.2.8 views. The 7.57 GB figure is the verified rounded Hub
    # size after adding the two JSONL shards.
    added_config_rows = (
        manifest['training_records'] + manifest['short_utterance_records']
    )
    displayed_rows = 961_533 + added_config_rows
    content_config_rows = 183_376 + added_config_rows
    content_config_count = 15 + 2
    content_config_split_views = 26 + 2
    named_config_count = 18 + 2
    total_config_split_views = 29 + 2
    reference_share = 778_157 / displayed_rows * 100
    expected_replacements = {
        "**961,533 rows** and **7.56 GB**":
            f"**{displayed_rows:,} rows** and **7.57 GB**",
        "**778,157 rows (80.9%)**":
            f"**778,157 rows ({reference_share:.1f}%)**",
        "**183,376** are overlapping config":
            f"**{content_config_rows:,}** are overlapping config",
    }
    for old, new in expected_replacements.items():
        if old not in card:
            raise ValueError(f"Pinned v0.2.7 card is missing expected metric: {old}")
        card = card.replace(old, new, 1)

    legacy_training_pattern = re.compile(
        r"Across `text`, `text_expansion`\s+\(1,737 rows\), and `text_resources` "
        r"\(475 rows\), \*\*zero rows are currently marked\s+recommended for "
        r"general text-model training\*\*\."
    )
    legacy_training_summary = (
        "Across the historical v0.2.7 `text`, `text_expansion` (1,737 rows), and "
        "`text_resources` (475 rows) configs, **zero rows are marked recommended "
        "for general text-model training**. The separate v0.2.8 `screened_meta_gbm` "
        f"config adds {manifest['training_records']:,} experimental training "
        "candidates; see its quality fields and review limitations below."
    )
    card, summary_count = legacy_training_pattern.subn(
        legacy_training_summary, card, count=1
    )
    if summary_count != 1:
        raise ValueError("Could not update the v0.2.7 text-readiness summary")

    config_row_pattern = re.compile(
        r"(?m)^(\| `record_sources` \| 412,740 \| record-to-source join table \|)$"
    )
    config_table_addition = (
        f"| `{HF_CONFIG}` | {manifest['training_records']:,} | "
        "experimental sentence-level text training candidates |\n"
        f"| `{SHORT_CONFIG}` | {manifest['short_utterance_records']:,} | "
        "short-utterance context; not general LM training |"
    )
    card, table_count = config_row_pattern.subn(
        rf"\1\n{config_table_addition}", card, count=1
    )
    if table_count != 1:
        raise ValueError("Could not add v0.2.8 configs to the configuration table")

    prior_content_total = "The current public package has **183,376 rows** across its content configurations;"
    current_content_total = (
        "The v0.2.7 baseline had **183,376 rows** across its content configurations; "
        f"v0.2.8 adds {added_config_rows:,} quality-screened text rows, bringing the "
        f"displayed content configuration total to **{content_config_rows:,}**;"
    )
    card = replace_wrapped_text(
        card,
        prior_content_total,
        current_content_total,
        "Could not update the content-view total in the v0.2.7 card",
    )

    old_scope_summary = (
        "The content views contain **183,376 overlapping rows** across 15 named "
        "content configurations and 26 content config/split views. With three "
        "reference configurations, the full dataset has 18 named configurations "
        "and 29 config/split views."
    )
    new_scope_summary = (
        f"The content views contain **{content_config_rows:,} overlapping rows** "
        f"across {content_config_count} named content configurations and "
        f"{content_config_split_views} content config/split views. With three "
        f"reference configurations, the full dataset has {named_config_count} "
        f"named configurations and {total_config_split_views} config/split views."
    )
    card = replace_wrapped_text(
        card,
        old_scope_summary,
        new_scope_summary,
        "Could not update the v0.2.7 repository-scope summary",
    )

    old_history = "The figures below describe the current v0.2.7 package, not a cumulative sum of"
    card = replace_wrapped_text(
        card,
        old_history,
        "The figures below describe the current v0.2.8 package, not a cumulative sum of",
        "Could not update the release-history summary",
    )

    old_package_summary = (
        "This public-profile package contains **183,376 overlapping content-view "
        "rows** across 15 content configs. The three reference-table configs add "
        "778,157 overlapping-view rows, for 18 named configs and 29 config/split "
        "views total."
    )
    new_package_summary = (
        f"This public-profile package contains **{content_config_rows:,} "
        f"overlapping content-view rows** across {content_config_count} content "
        f"configs. The three reference-table configs add 778,157 overlapping-view "
        f"rows, for {named_config_count} named configs and "
        f"{total_config_split_views} config/split views total."
    )
    card = replace_wrapped_text(
        card,
        old_package_summary,
        new_package_summary,
        "Could not update the public-profile package summary",
    )
    return card


def _safe_output(path: Path) -> None:
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"Refusing to overwrite non-empty output: {path}")
    path.mkdir(parents=True, exist_ok=True)


def build_quality_text_release(
    source_root: Path,
    hf_output: Path,
    kaggle_output: Path,
    base_card_path: Path | None = None,
) -> dict:
    """Generate matching packages without mutating the pinned source release."""
    source_root, hf_output, kaggle_output = map(
        lambda value: Path(value).resolve(), (source_root, hf_output, kaggle_output)
    )
    _safe_output(hf_output)
    _safe_output(kaggle_output)
    source_manifest, rows_by_config, input_hashes = load_source(source_root)
    selected, metrics = build_quality_screened_meta_text(rows_by_config)
    rows = [project_row(row) for row in selected]
    if not rows:
        raise ValueError("The screened text view is empty")
    ids = [row["id"] for row in rows]
    text_keys = [normalized_text_key(row["text"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate IDs in final release")
    if len(text_keys) != len(set(text_keys)):
        raise ValueError("Normalized duplicate text in final release")
    for row in rows:
        if not row["text"].strip():
            raise ValueError(f"Blank text in final release: {row['id']}")
        if (
            row["language"] != "gbm" or row["source_id"] != "meta_omni"
            or row["source_license_id"] != "CC-BY-4.0" or row["split"] != "train"
            or not row["recommended_for_training"] or row["native_reviewed"]
            or row["source_split_overlap_status"] != "no_upstream_eval_match_detected"
        ):
            raise ValueError(f"Record violates release scope: {row['id']}")

    words = sum(row["word_count"] for row in rows)
    characters = sum(row["character_count"] for row in rows)
    manifest = {
        "release_id": "garhwali-screened-text-v0.1",
        "source_release_id": source_manifest["release_id"],
        "source_release_manifest_sha256": input_hashes["manifest.json"],
        "source_input_sha256": input_hashes,
        "dataset_config": HF_CONFIG,
        "license_id": "CC-BY-4.0",
        "source_id": "meta_omni",
        "source_dataset_url": META_OMNILINGUAL_TRAINING_DECISION["source_url"],
        "rights_decision": META_OMNILINGUAL_TRAINING_DECISION,
        "selected_records": len(rows),
        "selected_by_source_config": dict(Counter(row["source_config"] for row in rows)),
        "blank_excluded": metrics["blank_excluded"],
        "eligibility_excluded": metrics["eligibility_excluded"],
        "normalized_duplicate_excluded": metrics["normalized_duplicate_excluded"],
        "training_records": 0,
        "short_utterance_records": 0,
        "training_words": 0,
        "short_utterance_word_count": 0,
        "whitespace_words": words,
        "characters": characters,
        "blank_rows_in_release": 0,
        "normalized_duplicate_rows_in_release": 0,
        "native_reviewed": False,
        "upstream_split": "train",
        "source_split_overlap_status": "no_upstream_eval_match_detected",
        "exclusions": {
            "duplicate_text": metrics["duplicate_exclusions"],
            "selection_counts": {
                "candidate_rows_evaluated": metrics["candidate_rows_evaluated"],
                "eligibility_excluded": metrics["eligibility_excluded"],
                "blank_excluded": metrics["blank_excluded"],
                "normalized_duplicate_excluded": metrics["normalized_duplicate_excluded"],
            },
            "deduplication_rule": (
                "NFKC + casefold + remove non-alphanumeric characters; retain first "
                "stable order (text before text_expansion; shard paths sorted)."
            ),
        },
        "files": {},
    }

    training_rows = [row for row in rows if row["word_count"] >= 5]
    short_rows = [dict(row) for row in rows if row["word_count"] < 5]
    if not training_rows:
        raise ValueError("No sentence-length rows remain for the main training view")
    for row in short_rows:
        row["recommended_for_training"] = False
        row["project_recommendation_status"] = "short_utterance_context_only_under_5_whitespace_tokens"
        row["training_profile"] = "short_utterance_context_only_v1"
    manifest["training_records"] = len(training_rows)
    manifest["short_utterance_records"] = len(short_rows)
    manifest["training_words"] = sum(row["word_count"] for row in training_rows)
    manifest["short_utterance_word_count"] = sum(row["word_count"] for row in short_rows)
    write_jsonl(hf_output / RELEASE_PATH, training_rows)
    write_jsonl(
        hf_output / "releases/v0.2.8/data/short_utterances_meta_gbm/train-00000.jsonl",
        short_rows,
    )
    hf_exclusions = hf_output / "releases/v0.2.8/quality-screened-exclusions.json"
    hf_exclusions.parent.mkdir(parents=True, exist_ok=True)
    hf_exclusions.write_text(json.dumps(manifest["exclusions"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    base_card_path = Path(base_card_path) if base_card_path else DEFAULT_BASE_CARD
    if base_card_path.is_file():
        card = update_hf_card(base_card_path.read_text(encoding="utf-8"), manifest)
    else:
        card = f"""---
language:
- gbm
license: other
configs:
- config_name: {HF_CONFIG}
  data_files:
  - split: train
    path: {RELEASE_PATH}
---
# Garhwali Language Lab

The `{HF_CONFIG}` config has {len(rows):,} automated-screened rows. Not native-reviewed.
"""
    (hf_output / "README.md").write_text(card, encoding="utf-8")

    kaggle_output.mkdir(parents=True, exist_ok=True)
    write_csv(kaggle_output / "train.csv", training_rows)
    write_csv(kaggle_output / "short_utterances.csv", short_rows)
    (kaggle_output / "dataset-metadata.json").write_text(json.dumps({
        "title": "Garhwali Screened Text Candidates",
        "id": KAGGLE_DATASET_ID,
        "licenses": [{"name": "CC-BY-4.0"}],
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (kaggle_output / "README.md").write_text(f"""# Garhwali Screened Text Candidates

This focused dataset contains **{len(training_rows):,}** sentence-length,
automatically screened Garhwali
(`gbm`) transcript texts from the Meta Omnilingual ASR Corpus. It is a small
experimental text resource, not a complete corpus, native-reviewed reference
set, or independent benchmark.

An additional **{len(short_rows):,}** nonblank short utterances are preserved in
`short_utterances.csv` for context. They are not recommended for general
language-model training because they contain fewer than five whitespace tokens.

## Quality and use

- Blank text values excluded: {metrics['blank_excluded']:,}.
- Normalized duplicate text excluded and documented: {metrics['normalized_duplicate_excluded']:,}.
- Included records have source IDs, provenance, CC BY 4.0 attribution, quality
  fields, and text SHA-256 values.
- All records come from the upstream training split; upstream evaluation overlap
  was not detected.
- **No native-speaker review has been performed.** Automated screening cannot
  certify spelling, meaning, or dialect accuracy.

The included texts are released under CC BY 4.0 subject to its attribution
terms. See `ATTRIBUTION.md`, `LICENSE_POLICY.md`, and `DATASET_SCHEMA.md`.

```python
import pandas as pd
df = pd.read_csv("train.csv")
print(df[["text", "language", "quality_status"]].head())
```

| Measure | Value |
|---|---:|
| Training rows | {len(training_rows):,} |
| Short context rows | {len(short_rows):,} |
| All words | {words:,} |
| Training words | {manifest['training_words']:,} |
| Characters | {characters:,} |
| Blank rows / normalized duplicates | 0 / 0 |
| Native-reviewed | No |

Source release: `{source_manifest['release_id']}`. Build and input hashes are in
`manifest.json`; normalized duplicate exclusions are in
`quality-screened-exclusions.json`.
""", encoding="utf-8")
    (kaggle_output / "DATASET_SCHEMA.md").write_text("""# Dataset schema

`train.csv` contains one screened transcript per row. List fields are JSON
arrays serialized inside CSV cells.

| Field | Meaning |
|---|---|
| `id`, `text` | Stable record ID and transcript value. |
| `language`, `script`, `split` | Garhwali label, script, and upstream train partition. |
| `source_config`, `source_id`, `source_record_ids`, `source_dataset_url` | Source lineage. |
| `source_license_id`, `license_url`, `rights_status` | Per-record rights basis. |
| `rights_evidence_url`, `rights_evidence_snapshot_sha256` | Evidence pointer and pinned card snapshot hash. |
| `attribution` | Required source attribution. |
| `quality_status`, `quality_tiers`, `quality_flags` | Automated quality evidence, not human validation. |
| `source_split_overlap_status`, `source_split_overlap_source_ids` | Evaluation-split overlap audit. |
| `recommended_for_training`, `project_recommendation_status`, `training_profile` | Experimental scope of the project recommendation. |
| `native_reviewed` | False for every record in this release. |
| `training_eligibility_decision_id`, `source_training_eligible_before_project_decision` | Rights decision lineage and original source flag. |
| `text_sha256`, `word_count`, `character_count` | Integrity and text size. |
""", encoding="utf-8")
    (kaggle_output / "ATTRIBUTION.md").write_text("""# Attribution

Derived from the Meta Omnilingual ASR Corpus contributors, CC BY 4.0:
<https://huggingface.co/datasets/facebook/omnilingual-asr-corpus>. This project
adds screening and release metadata; it has not natively reviewed the text.
""", encoding="utf-8")
    (kaggle_output / "LICENSE_POLICY.md").write_text("""# License policy

This focused package contains records mapped to the Meta Omnilingual ASR
Corpus CC BY 4.0 basis. Reuse is subject to attribution and other applicable
license terms. The release manifest pins the card snapshot used for this
decision. This notice does not relicense the larger mixed-source corpus.
""", encoding="utf-8")
    (kaggle_output / "quality-screened-exclusions.json").write_text(
        json.dumps(manifest["exclusions"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    manifest["files"] = {}
    for package, base in (("huggingface", hf_output), ("kaggle", kaggle_output)):
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.name not in {"quality-screened-text-manifest.json", "manifest.json"}:
                relative = path.relative_to(base).as_posix()
                manifest["files"][f"{package}/{relative}"] = {
                    "sha256": sha256_file(path), "bytes": path.stat().st_size,
                }
    manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    (hf_output / "releases/v0.2.8/quality-screened-text-manifest.json").write_text(manifest_text, encoding="utf-8")
    (kaggle_output / "manifest.json").write_text(manifest_text, encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--hf-output", type=Path, default=DEFAULT_HF_OUTPUT)
    parser.add_argument("--kaggle-output", type=Path, default=DEFAULT_KAGGLE_OUTPUT)
    parser.add_argument("--base-card", type=Path, default=DEFAULT_BASE_CARD)
    args = parser.parse_args()
    manifest = build_quality_text_release(args.source, args.hf_output, args.kaggle_output, args.base_card)
    print(json.dumps({key: manifest[key] for key in (
        "release_id", "source_release_id", "selected_records", "blank_excluded",
        "normalized_duplicate_excluded", "whitespace_words", "characters",
    )}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
