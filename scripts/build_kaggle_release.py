#!/usr/bin/env python3
"""Build small, reproducible Kaggle exports from the verified HF packages.

The speech export intentionally contains metadata and transcripts only; audio
remains available from the linked Hugging Face dataset. The corpus export
omits PahariLI sentence text because its repository license does not establish
redistribution rights for the underlying sentences. A content-free hash/source
index keeps those records discoverable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


CORPUS_CONFIGS = (
    "asr",
    "catalog",
    "geography",
    "historical_terms",
    "instructions",
    "lexicon",
    "literary_people",
    "literary_works",
    "popular_songs",
    "record_index",
    "record_sources",
    "source_catalog",
    "sravaani_drafts",
    "text",
    "text_expansion",
    "text_resources",
    "university_research",
)
SPEECH_REPO_URL = "https://huggingface.co/datasets/rushilrawat/garhwali-speech"
PAHARILI_SOURCE_URL = "https://github.com/rachanagusain/PahariLI"


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _jsonl_files(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.jsonl"))


def _jsonl_records(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def _write_csv(path: Path, columns: list[str], rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="raise")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in columns})
            count += 1
    return count


def _split_name(path: Path) -> str:
    return path.stem.rsplit("-", 1)[0]


def _copy_release_docs(source: Path, destination: Path) -> None:
    for name in ("ATTRIBUTION.md", "LICENSE_POLICY.md", "DATASET_SCHEMA.md"):
        path = source / name
        if path.exists():
            (destination / name).write_bytes(path.read_bytes())


def build_corpus(corpus_root: Path, output: Path) -> dict[str, Any]:
    data_root = corpus_root / "data"
    output.mkdir(parents=True, exist_ok=True)
    if "paharili_gbm" in CORPUS_CONFIGS:
        raise ValueError("PahariLI text must remain excluded from the Kaggle text export")

    config_counts: dict[str, int] = {}
    data_files: list[dict[str, Any]] = []
    text_training_metrics = {
        "rows": 0,
        "whitespace_words": 0,
        "characters": 0,
        "recommended_rows": 0,
    }
    for config in CORPUS_CONFIGS:
        source_files = _jsonl_files(data_root / config)
        if not source_files:
            raise FileNotFoundError(f"No JSONL shards found for corpus config {config!r}")
        columns = {"dataset_config", "dataset_split"}
        for shard in source_files:
            for record in _jsonl_records(shard):
                columns.update(record)
        ordered_columns = ["dataset_config", "dataset_split"] + sorted(columns - {"dataset_config", "dataset_split"})

        def rows() -> Iterable[dict[str, Any]]:
            for shard in source_files:
                for record in _jsonl_records(shard):
                    if config in {"text", "text_expansion", "text_resources"}:
                        text = record.get("text")
                        if isinstance(text, str):
                            text_training_metrics["rows"] += 1
                            text_training_metrics["whitespace_words"] += len(text.split())
                            text_training_metrics["characters"] += len(text)
                            if record.get("recommended_for_training") is True:
                                text_training_metrics["recommended_rows"] += 1
                    yield {**record, "dataset_config": config, "dataset_split": _split_name(shard)}

        destination = output / f"{config}.csv"
        count = _write_csv(destination, ordered_columns, rows())
        config_counts[config] = count
        data_files.append({"path": destination.name, "records": count, "sha256": _sha256(destination)})

    # Publish a source/hash index, never sentence text, for the unresolved
    # PahariLI component. This preserves record-level discoverability.
    paharili_rows = []
    for shard in _jsonl_files(data_root / "paharili_gbm"):
        for record in _jsonl_records(shard):
            paharili_rows.append({
                "id": record.get("id"),
                "text_sha256": record.get("text_sha256"),
                "normalized_text_key_sha256": record.get("normalized_text_key_sha256"),
                "source_record_ids": record.get("source_record_ids"),
                "upstream_splits": record.get("upstream_splits"),
                "dataset_split": _split_name(shard),
                "language": record.get("language"),
                "language_name": record.get("language_name"),
                "license_id": record.get("license_id"),
                "license_url": record.get("license_url"),
                "rights_status": record.get("rights_status"),
                "reuse_scope": record.get("reuse_scope"),
                "quality_status": record.get("quality_status"),
                "source_repository": PAHARILI_SOURCE_URL,
                "content_omitted_reason": "Underlying sentence rights and Garhwali labels are unverified; repository license does not establish sentence-level reuse rights.",
            })
    index_path = output / "paharili_source_index.csv"
    index_columns = list(paharili_rows[0]) if paharili_rows else [
        "id", "text_sha256", "normalized_text_key_sha256", "source_record_ids",
        "upstream_splits", "dataset_split", "language", "language_name", "license_id",
        "license_url", "rights_status", "reuse_scope", "quality_status", "source_repository",
        "content_omitted_reason",
    ]
    index_count = _write_csv(index_path, index_columns, paharili_rows)
    data_files.append({"path": index_path.name, "records": index_count, "sha256": _sha256(index_path), "content_free": True})
    _copy_release_docs(corpus_root, output)

    total_rows = sum(config_counts.values())
    manifest = {
        "dataset_id": "rushilrawat1/garhwali-language-corpus",
        "title": "Garhwali Language Corpus v0.2.7",
        "release": "v0.2.7-kaggle.1",
        "upstream_dataset": "https://huggingface.co/datasets/rushilrawat/garhwali-corpus",
        "upstream_release_commit": "1f7b2ceed1b743412b75d6288757e1d2cadac9c4",
        "global_kaggle_license": "other",
        "row_level_license_policy": "Each record's source-specific license, attribution, rights_status, and reuse_scope controls its use; no corpus-wide permission is asserted.",
        "configuration_counts": config_counts,
        "configuration_view_rows": total_rows,
        "text_training_metrics": text_training_metrics,
        "paharili_text_rows_omitted": index_count,
        "paharili_text_omission_index": index_path.name,
        "data_files": data_files,
        "counts_are_overlapping_views": True,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kaggle_metadata = {
        "title": "Garhwali Language Corpus v0.2.7",
        "id": "rushilrawat1/garhwali-language-corpus",
        "subtitle": "Source-linked Garhwali text, vocabulary, and metadata",
        "description": "A versioned, source-linked Garhwali resource with text, lexicon, transcripts, literary and historical metadata, and reference indexes. Records retain their own source-specific rights, reuse scope, quality, and provenance; Kaggle's 'other' label does not grant blanket rights. See LICENSE_POLICY.md and each row's rights fields. The 8,444 full texts whose item-level reuse rights remain unresolved are absent from the content tables; catalog records retain source locators. PahariLI sentence text is also omitted because the upstream repository license does not establish rights for the sentences; paharili_source_index.csv keeps content-free identifiers and hashes. Speech audio is in the linked Hugging Face speech dataset.",
        "licenses": [{"name": "other"}],
    }
    (output / "dataset-metadata.json").write_text(json.dumps(kaggle_metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text(_corpus_readme(manifest), encoding="utf-8")
    return manifest


def _corpus_readme(manifest: dict[str, Any]) -> str:
    counts = manifest["configuration_counts"]
    references = sum(counts.get(name, 0) for name in ("record_index", "source_catalog", "record_sources"))
    combined_rows = manifest["configuration_view_rows"] + manifest["paharili_text_rows_omitted"]
    metrics = manifest["text_training_metrics"]
    return f"""# {manifest['title']}\n\nA Kaggle-friendly export of the public [Hugging Face corpus]({manifest['upstream_dataset']}) at commit `{manifest['upstream_release_commit']}`.\n\nThis export has {len(counts)} configurations and {manifest['configuration_view_rows']:,} CSV configuration-view rows, plus {manifest['paharili_text_rows_omitted']:,} content-free PahariLI ID/hash rows. Together they make {combined_rows:,} displayed rows, not unique examples. The three source-reference tables contribute {references:,} rows; the other views overlap and include several different data types. The main text-oriented configs contain {metrics['rows']:,} rows, {metrics['whitespace_words']:,} whitespace-separated words, and {metrics['characters']:,} characters. **{metrics['recommended_rows']:,} of those rows are currently marked recommended for general text-model training.** Use per-record `recommended_for_training`, rights, and quality fields; row totals alone do not indicate usability.\n\nEach configuration CSV contains one config, with nested values serialized as JSON strings. `dataset_config` and `dataset_split` identify the originating view.\n\n## Start quickly\n\n```python\nimport pandas as pd\n\ntext = pd.read_csv('/kaggle/input/garhwali-language-corpus/text.csv')\nprint(text[['text', 'language', 'quality_status', 'rights_status']].head())\n```\n\n## Rights and quality\n\nThis dataset uses Kaggle's `other` label because source terms differ. It is not a blanket license or permission. Check `license_labels`, `rights_status`, `reuse_scope`, `provenance`, and attribution for every record before reuse. Machine-generated SraVaani drafts are explicitly marked as unreviewed, and metadata-only records do not license the underlying work. The 8,444 full texts whose item-level reuse rights remain unresolved are absent from the content tables; catalog rows retain source locators. PahariLI sentence text is omitted: its upstream repository declares Apache-2.0, but sentence-level origins and rights are unresolved. The content-free `paharili_source_index.csv` retains {manifest['paharili_text_rows_omitted']:,} row identifiers and hashes.\n\n## Linked speech data\n\nThe speech metadata companion is packaged separately; audio remains in the [Hugging Face speech dataset]({SPEECH_REPO_URL}).\n\nSee `DATASET_SCHEMA.md`, `ATTRIBUTION.md`, and `LICENSE_POLICY.md` for the schema, attribution, and reuse rules. File counts and checksums are in `manifest.json`.\n"""


def _speech_metadata_rows(speech_root: Path) -> tuple[list[str], Iterable[dict[str, Any]], dict[str, int]]:
    try:
        import pyarrow.parquet as parquet
    except ImportError as exc:  # pragma: no cover - exercised by CLI environment check
        raise RuntimeError("Install requirements-hf-release.txt to export speech metadata") from exc

    data_root = speech_root / "data"
    paths = sorted(data_root.rglob("*.parquet"))
    if not paths:
        raise FileNotFoundError(f"No Parquet files found under {data_root}")
    columns = {"dataset_config", "dataset_split", "audio_included", "audio_dataset_url"}
    for path in paths:
        schema = parquet.ParquetFile(path).schema_arrow
        columns.update(field.name for field in schema if field.name != "audio")
    output_columns = ["dataset_config", "dataset_split", "audio_included", "audio_dataset_url"] + sorted(columns - {"dataset_config", "dataset_split", "audio_included", "audio_dataset_url"})
    config_counts: dict[str, int] = {}

    def rows() -> Iterable[dict[str, Any]]:
        for path in paths:
            config = "meta_omnilingual" if "meta_omnilingual" in path.parts else "garhwali_speech"
            split = path.name.split("-", 1)[0]
            fields = [field.name for field in parquet.ParquetFile(path).schema_arrow if field.name != "audio"]
            reader = parquet.ParquetFile(path)
            for batch in reader.iter_batches(batch_size=512, columns=fields):
                for record in batch.to_pylist():
                    config_counts[config] = config_counts.get(config, 0) + 1
                    yield {
                        **record,
                        "dataset_config": config,
                        "dataset_split": split,
                        "audio_included": False,
                        "audio_dataset_url": SPEECH_REPO_URL,
                    }
    return output_columns, rows(), config_counts


def build_speech(speech_root: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    columns, rows, config_counts = _speech_metadata_rows(speech_root)
    csv_path = output / "speech_records.csv"
    row_count = _write_csv(csv_path, columns, rows)
    _copy_release_docs(speech_root, output)
    manifest = {
        "dataset_id": "rushilrawat1/garhwali-speech-metadata",
        "title": "Garhwali Speech Metadata v0.2.1",
        "release": "v0.2.1-kaggle.1",
        "upstream_dataset": SPEECH_REPO_URL,
        "global_kaggle_license": "CC-BY-4.0",
        "configuration_counts": config_counts,
        "metadata_rows": row_count,
        "audio_payload_included": False,
        "audio_reason": "Avoid duplicating the large audio package; audio remains available in the linked Hugging Face release.",
        "csv_sha256": _sha256(csv_path),
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    metadata = {
        "title": manifest["title"],
        "id": manifest["dataset_id"],
        "subtitle": "Garhwali transcript and quality metadata; audio linked",
        "description": f"A metadata-only companion to {SPEECH_REPO_URL}. It contains source/provider transcripts, experimental SraVaani drafts, hashes, split and quality fields; it contains no audio bytes. Machine drafts are not ground truth. All rows retain CC BY 4.0 attribution and source fields. Join/download audio from the linked Hugging Face dataset using record_id/audio_sha256.",
        "licenses": [{"name": "CC-BY-4.0"}],
    }
    (output / "dataset-metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "README.md").write_text(f"""# {manifest['title']}\n\nThis is the transcript and metadata companion for the [Hugging Face speech dataset]({SPEECH_REPO_URL}). It contains **{row_count:,}** rows across `{', '.join(f'{name}={count:,}' for name, count in sorted(config_counts.items()))}`. Rows are config/split views and may overlap.\n\n## Audio\n\nThis Kaggle package contains no audio bytes. Use `record_id` or `audio_sha256` to join these rows to the linked Hugging Face dataset when audio is needed.\n\n## Quality and use\n\nProvider transcripts and SraVaani machine drafts are separate fields. The drafts are unreviewed experimental hypotheses, not ground truth. Inspect `transcript_review_status`, `machine_draft_review_status`, `quality_status`, `rights_status`, `reuse_scope`, and `license_labels` before using any row. The exported CSV serializes nested lists as JSON strings.\n\n## Quick start\n\n```python\nimport pandas as pd\n\ndf = pd.read_csv('/kaggle/input/garhwali-speech-metadata/speech_records.csv')\nprint(df[['record_id', 'transcript', 'transcript_source', 'quality_status']].head())\n```\n\nSee `DATASET_SCHEMA.md`, `ATTRIBUTION.md`, and `manifest.json` for field definitions, attribution, row counts, and checksums.\n""", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("data/huggingface/garhwali-language-lab-v0.2.7-staging"))
    parser.add_argument("--speech", type=Path, default=Path("data/huggingface/garhwali-language-lab-speech-v2.2.0-staging"))
    parser.add_argument("--output", type=Path, default=Path("data/kaggle"))
    args = parser.parse_args()
    corpus = build_corpus(args.corpus, args.output / "garhwali-language-corpus-v0.2.7")
    speech = build_speech(args.speech, args.output / "garhwali-speech-metadata-v0.2.1")
    print(json.dumps({"corpus": corpus, "speech": speech}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
