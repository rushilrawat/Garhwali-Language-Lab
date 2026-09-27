#!/usr/bin/env python3
"""Build normalized, content-free source tables for the public HF dataset."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL_DATA = ROOT / "data/huggingface/garhwali-language-lab-all-data"
PUBLIC_DATA = ROOT / "data/huggingface/garhwali-language-lab"
RELEASE_ID = "garhwali-language-lab-v0.1.1"

TABLES = {
    "record_index": PUBLIC_DATA / "data/record_index/train-00000.jsonl",
    "source_catalog": PUBLIC_DATA / "data/source_catalog/train-00000.jsonl",
    "record_sources": PUBLIC_DATA / "data/record_sources/train-00000.jsonl",
}
SOURCE_FIELDS = (
    "source_id", "source_title", "source_url", "source_authority", "attribution",
    "source_kind", "license_id", "license_url", "rights_status", "genre",
    "modality", "iso_639_3",
)
METADATA_FIELDS = {
    "geography": ("name", "name_local", "place_type", "division", "districts", "wikipedia_title"),
    "historical_terms": ("term", "term_local", "term_type", "period", "name_variants"),
    "literary_people": ("canonical_name", "aliases", "roles", "associated_works", "verification_status"),
    "literary_works": ("title", "title_variants", "creators", "date_or_period", "work_type", "language_scope", "ingestion_status"),
    "popular_songs": ("title", "artists", "album", "genre", "release_year", "caption_status", "popularity_basis"),
    "university_research": ("title", "creators", "institution", "resource_type", "topics", "language_scope", "year", "source_authority", "ingestion_status", "access_level", "visibility"),
    "instructions": ("task", "semantic_domains"),
}
PUBLIC_KEY_FIELDS = {
    "asr": "audio_sha256",
    "catalog": "id",
    "instructions": "instruction_sha256",
    "lexicon": "form_sha256",
    "sravaani_drafts": "audio_sha256",
    "text": "id",
}
FORBIDDEN_OUTPUT_KEYS = {
    "text", "transcript", "lyrics", "audio", "audio_sha256", "speaker_id",
    "text_sha256", "source_text_sha256", "local_path", "source_pdf",
}


def json_value(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def read_rows(directory: Path):
    for path in sorted(directory.glob("*.jsonl")):
        split = path.stem.split("-", 1)[0]
        with path.open(encoding="utf-8") as stream:
            for ordinal, line in enumerate(stream, 1):
                if line.strip():
                    yield split, path.stem, ordinal, json.loads(line)


def public_content_keys(public_root: Path) -> dict[str, dict[str, bool]]:
    result = {}
    for config, key_field in PUBLIC_KEY_FIELDS.items():
        keys = {}
        for _, _, _, row in read_rows(public_root / "data" / config):
            key = row.get(key_field)
            if key is not None:
                # The public catalog keeps every record, but many values are redacted.
                keys[str(key)] = bool(row.get("text_publicly_available", True))
        result[config] = keys
    return result


def source_objects(row: dict) -> list[dict]:
    candidates = []
    for field in ("provenance", "sources", "public_rights_basis"):
        values = row.get(field) or []
        if isinstance(values, dict):
            values = [values]
        if isinstance(values, list):
            candidates.extend(item for item in values if isinstance(item, dict))

    refs = []
    for item in candidates:
        ref = {key: item[key] for key in SOURCE_FIELDS if item.get(key) not in (None, "")}
        if ref:
            refs.append(ref)

    for field in ("source_url", "wikipedia_url", "osm_search_url", "youtube_url"):
        value = row.get(field)
        if isinstance(value, str) and value.startswith(("https://", "http://")):
            refs.append({"source_url": value})
    for field in ("lyrics_sources", "translation_sources"):
        for value in row.get(field) or []:
            if isinstance(value, str) and value.startswith(("https://", "http://")):
                refs.append({"source_url": value})
    if row.get("source") == "ARTPARK-IISc/Vaani":
        refs.append({
            "source_id": "ARTPARK-IISc/Vaani",
            "source_url": "https://huggingface.co/datasets/ARTPARK-IISc/Vaani",
            "license_id": "CC-BY-4.0",
        })

    unique = {}
    for ref in refs:
        unique[json_value(ref)] = ref
    return [unique[key] for key in sorted(unique)]


def source_reference_id(ref: dict) -> str:
    return hashlib.sha256(json_value(ref).encode("utf-8")).hexdigest()


def make_record_row(config: str, split: str, shard: str, ordinal: int, row: dict,
                    content_keys: dict, source_ids: list[str]) -> dict:
    key_field = PUBLIC_KEY_FIELDS.get(config)
    available = False
    if key_field and row.get(key_field) is not None:
        available = content_keys.get(config, {}).get(str(row[key_field]), False)
    row_rights = row.get("rights_status") or row.get("redistribution_status") or "not_recorded"
    metadata = {
        key: row[key]
        for key in METADATA_FIELDS.get(config, ())
        if key in row and row[key] not in (None, "", [], {})
    }
    quality = {}
    for field in ("quality_flags", "quality_tiers", "review_status", "verification_status", "ingestion_status"):
        if row.get(field):
            quality[field] = row[field]
    for field in ("quality_metadata", "language_quality", "dialect_quality"):
        value = row.get(field)
        if isinstance(value, dict):
            status = value.get("review_status") or value.get("status")
            if status:
                quality[field + "_status"] = status

    language = row.get("language")
    if not isinstance(language, str):
        language = row.get("iso_639_3") or (row.get("source_languages") or [None])[0]
    title = row.get("title") or row.get("canonical_name") or row.get("name") or row.get("term") or ""
    local = row.get("name_local") or row.get("term_local") or ""
    creators = row.get("creators") or row.get("artists") or row.get("aliases") or []
    record_type = row.get("resource_type") or row.get("place_type") or row.get("term_type") or row.get("work_type") or row.get("genre") or ""
    period = row.get("year") or row.get("release_year") or row.get("date_or_period") or row.get("period") or ""
    topics = row.get("topics") or row.get("subjects") or row.get("semantic_domains") or []
    language_scope = row.get("language_scope") or row.get("source_languages") or []
    return {
        "record_ref": f"{RELEASE_ID}:all-data:{config}:{split}:{shard}:{ordinal:06d}",
        "record_family": config,
        "source_split": split,
        "record_title_or_name": str(title),
        "local_name_or_term": str(local),
        "creators_json": json_value(creators),
        "record_type": str(record_type),
        "year_or_period": str(period),
        "topics_json": json_value(topics),
        "language_scope_json": json_value(language_scope),
        "language": language or "",
        "script": row.get("script") or "",
        "record_rights_status": str(row_rights),
        "public_profile_content_available": available,
        "source_ref_ids_json": json_value(source_ids),
        "quality_summary_json": json_value(quality),
        "bibliographic_metadata_json": json_value(metadata),
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def update_dataset_card(report: dict) -> None:
    path = PUBLIC_DATA / "README.md"
    text = path.read_text(encoding="utf-8")
    front, body = text.split("---\n", 2)[1:]
    config_blocks = "".join(
        f"- config_name: {name}\n  data_files:\n  - split: train\n    path: data/{name}/train-00000.jsonl\n"
        for name in TABLES
        if f"config_name: {name}" not in front
    )
    if config_blocks:
        marker = "- config_name: text\n"
        if marker not in front:
            raise ValueError("Cannot add reference-index tables to the dataset card config list")
        front = front.replace(marker, config_blocks + marker, 1)

    summary_heading = "## What this repository provides"
    summary_start = body.find(summary_heading)
    if summary_start >= 0:
        summary_end = body.find("\n## ", summary_start + len(summary_heading))
        if summary_end >= 0:
            body = body[:summary_start] + body[summary_end + 1:]
    summary = f"""## What this repository provides

This public dataset has two layers. Its rights-filtered content configurations contain **{report['public_profile_package_rows']:,} rows** across six named configurations and twelve config/split views. Separately, the metadata-only reference index covers every one of the **{report['records']:,} rows** in the complete all-data archive, including all 216 structured geography, history, literature, music, and research records.

The reference index includes **{report['source_catalog_records']:,} deduplicated source records** and **{report['record_source_links']:,} record-to-source links**. It exposes available names and titles, source URLs, attribution, rights status, and quality metadata. Record-level rights are marked `not_recorded` for **{report.get('record_rights_status_counts', {}).get('not_recorded', 0):,} rows**; other rows include rights-pending, reviewed-unresolved, metadata-only, or cleared statuses. `not_recorded` is not permission to reuse a record: inspect its linked source entry and terms. The index does not contain the referenced works' text, lyrics, transcripts, audio, speaker identifiers, local paths, or content hashes. These are archive-row counts with overlapping views, not unique-example counts; the reference rows themselves are not training examples. Links and bibliographic facts do not grant rights to copy or reuse source material.
"""
    release_marker = "Release: **" + str(report["release_id"]) + "**"
    if release_marker not in body:
        raise ValueError("Cannot add repository summary to the dataset card")
    body = body.replace(release_marker, release_marker + "\n\n" + summary, 1)

    legacy_start = body.find("Three normalized reference tables")
    if legacy_start >= 0:
        legacy_end = body.find("\n## ", legacy_start)
        if legacy_end >= 0:
            body = body[:legacy_start] + body[legacy_end:]

    section = f"""## Complete source reference index

The three metadata tables cover **{report['records']:,} records** from the complete local all-data archive. `record_index` has one row per archived record, `source_catalog` contains {report['source_catalog_records']:,} deduplicated source references, and `record_sources` contains {report['record_source_links']:,} join rows. The tables include source URLs, available attribution, rights and quality status, and factual catalog fields. They exclude source text, lyrics, transcripts, machine drafts, audio, speaker identifiers, local paths, and content hashes.

The current public package has **{report['public_profile_package_rows']:,} rows** across its content configurations; **{report['records_with_content_in_public_profile']:,}** indexed records have a corresponding public content value. The difference is metadata-only catalog rows whose values are redacted. Reference-index rows are not training examples and must not be added to corpus sample counts. Source links point to original material and do not grant reuse rights.

See [`reference_index_manifest.json`](reference_index_manifest.json) for counts by family and the three table checksums.
"""
    start = body.find("## Complete source reference index")
    if start >= 0:
        next_heading = body.find("\n## ", start + 1)
        end = next_heading if next_heading >= 0 else len(body)
        suffix = body[end:].lstrip("\n")
        body = body[:start] + section.rstrip() + "\n\n" + suffix
    else:
        marker = "\n## Linked speech dataset"
        position = body.find(marker)
        if position >= 0:
            suffix = body[position:].lstrip("\n")
            body = body[:position] + "\n\n" + section.rstrip() + "\n\n" + suffix
        else:
            body = body.rstrip() + "\n\n" + section
    path.write_text(f"---\n{front}---\n{body.lstrip()}", encoding="utf-8")


def build_index(all_data: Path = ALL_DATA, public_data: Path = PUBLIC_DATA) -> dict:
    manifest = json.loads((all_data / "manifest.json").read_text(encoding="utf-8"))
    content_keys = public_content_keys(public_data)
    for path in TABLES.values():
        path.parent.mkdir(parents=True, exist_ok=True)

    counts, public_counts, rights_counts = Counter(), Counter(), Counter()
    sources, links = {}, []
    with TABLES["record_index"].open("w", encoding="utf-8") as records_file:
        configs = sorted({item.split("/", 1)[0] for item in manifest["configs"]})
        for config in configs:
            for split, shard, ordinal, row in read_rows(all_data / "data" / config):
                refs = source_objects(row)
                source_ids = []
                for ref in refs:
                    source_id = source_reference_id(ref)
                    sources[source_id] = {"source_ref_id": source_id, **ref}
                    source_ids.append(source_id)
                record = make_record_row(config, split, shard, ordinal, row, content_keys, source_ids)
                records_file.write(json_value(record) + "\n")
                links.extend({"record_ref": record["record_ref"], "source_ref_id": source_id} for source_id in source_ids)
                counts[config] += 1
                if record["public_profile_content_available"]:
                    public_counts[config] += 1
                rights_counts[record["record_rights_status"]] += 1

    with TABLES["source_catalog"].open("w", encoding="utf-8") as sources_file:
        for source_id in sorted(sources):
            sources_file.write(json_value(sources[source_id]) + "\n")
    with TABLES["record_sources"].open("w", encoding="utf-8") as links_file:
        for link in links:
            links_file.write(json_value(link) + "\n")

    expected = Counter()
    for config_split, value in manifest["configs"].items():
        config = config_split.split("/", 1)[0]
        expected[config] += value["records"]
    if counts != expected:
        raise ValueError(f"All-data package counts changed: {dict(counts)} != {dict(expected)}")

    package_manifest_path = PUBLIC_DATA / "manifest.json"
    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    reference_config_names = set(TABLES)
    public_profile_rows = sum(
        details["records"]
        for key, details in package_manifest.get("configs", {}).items()
        if key.split("/", 1)[0] not in reference_config_names | {"source_index"}
    )

    file_details = {}
    for name, path in TABLES.items():
        row_count = sum(1 for line in path.open(encoding="utf-8") if line.strip())
        file_details[name] = {
            "file": str(path.relative_to(PUBLIC_DATA)),
            "records": row_count,
            "sha256": _sha256(path),
        }
    report = {
        "release_id": RELEASE_ID,
        "profile": "metadata_only_complete_reference_index",
        "records": sum(counts.values()),
        "records_by_family": dict(sorted(counts.items())),
        "records_with_content_in_public_profile": sum(public_counts.values()),
        "public_profile_package_rows": public_profile_rows,
        "public_content_records_by_family": dict(sorted(public_counts.items())),
        "record_rights_status_counts": dict(sorted(rights_counts.items())),
        "source_catalog_records": len(sources),
        "record_source_links": len(links),
        "tables": file_details,
        "payload_policy": "No corpus text, transcript, lyrics, audio, speaker identifier, text hash, local source path, or scan is included.",
        "reference_policy": "Source URLs and factual bibliographic metadata are pointers and do not grant redistribution rights to referenced works.",
    }
    (PUBLIC_DATA / "reference_index_manifest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    package_manifest.setdefault("configs", {}).pop("source_index/train", None)
    for name, details in file_details.items():
        package_manifest.setdefault("configs", {})[f"{name}/train"] = {
            "records": details["records"], "shards": 1,
            "files": [Path(details["file"]).name],
            "file_sha256": {Path(details["file"]).name: details["sha256"]},
        }
    package_manifest["reference_index"] = report
    package_manifest_path.write_text(
        json.dumps(package_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    update_dataset_card(report)
    return report


if __name__ == "__main__":
    print(json.dumps(build_index(), indent=2, ensure_ascii=False))
