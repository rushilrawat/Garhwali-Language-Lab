#!/usr/bin/env python3
"""Build normalized, content-free source tables for the public HF dataset."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from pathlib import Path

from record_schema import normalize_record
from hf_source_registry import SOURCE_URLS, source_record_locator

ROOT = Path(__file__).resolve().parents[1]
ALL_DATA = ROOT / os.environ.get(
    "GARHWALI_HF_ALL_DATA_OUTPUT", "data/huggingface/garhwali-language-lab-all-data"
)
PUBLIC_DATA = ROOT / os.environ.get(
    "GARHWALI_HF_PUBLIC_OUTPUT", "data/huggingface/garhwali-language-lab"
)
RELEASE_ID = f"garhwali-language-lab-v{os.environ.get('GARHWALI_RELEASE_VERSION', '2.2.0').removeprefix('v')}"

TABLES = {
    "record_index": PUBLIC_DATA / "data/record_index/train-00000.jsonl",
    "source_catalog": PUBLIC_DATA / "data/source_catalog/train-00000.jsonl",
    "record_sources": PUBLIC_DATA / "data/record_sources/train-00000.jsonl",
}
SOURCE_FIELDS = (
    "source_id", "source_title", "source_url", "source_authority", "attribution",
    "source_kind", "license_id", "license_url", "rights_status", "genre",
    "modality", "iso_639_3", "source_snapshot_sha256",
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
    "text_expansion": "id",
    "text_resources": "id",
}
FORBIDDEN_OUTPUT_KEYS = {
    "text", "transcript", "lyrics", "audio", "audio_sha256", "speaker_id",
    "text_sha256", "source_text_sha256", "local_path", "source_pdf",
}


def incoming_pdf_source_metadata(directory: Path | None = None) -> dict[str, dict]:
    """Load source-level bibliographic pointers from the tracked PDF sidecars."""
    directory = directory or ROOT / "incoming/pdfs"
    result = {}
    for path in sorted(Path(directory).glob("*.json")):
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        source_id = metadata.get("source_id")
        if not source_id:
            continue
        source = {}
        if metadata.get("title"):
            source["source_title"] = str(metadata["title"])
        landing_page = metadata.get("landing_page")
        if isinstance(landing_page, str) and landing_page.startswith(("https://", "http://")):
            source["source_url"] = landing_page
        attribution = metadata.get("author") or metadata.get("editor")
        if isinstance(attribution, list):
            attribution = "; ".join(str(item) for item in attribution if item)
        if attribution:
            source["attribution"] = str(attribution)
        if source:
            result[str(source_id)] = source
    return result


INCOMING_PDF_SOURCE_METADATA = incoming_pdf_source_metadata()


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
                # Every catalog record stays addressable; some expose metadata only.
                keys[str(key)] = bool(row.get("text_publicly_available", True))
        result[config] = keys
    return result


def source_objects(row: dict, incoming_metadata: dict[str, dict] | None = None) -> list[dict]:
    incoming_metadata = (
        INCOMING_PDF_SOURCE_METADATA if incoming_metadata is None else incoming_metadata
    )
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
        for key, value in source_record_locator(item).items():
            ref.setdefault(key, value)
        source_id = str(item.get("source_id") or "")
        for key, value in incoming_metadata.get(source_id, {}).items():
            ref.setdefault(key, value)
        if source_id in SOURCE_URLS:
            ref.setdefault("source_url", SOURCE_URLS[source_id])
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
    vaani_source = row.get("source")
    if vaani_source in {
        "ARTPARK-IISc/Vaani",
        "ARTPARK-IISc/Vaani-transcription-part",
    }:
        refs.append({
            "source_id": vaani_source,
            "source_url": f"https://huggingface.co/datasets/{vaani_source}",
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
    return normalize_record({
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
    }, family="record_index")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sync_quickstart_text(text: str, report: dict) -> str:
    """Keep the packaged quick-start's release counts aligned to its manifests."""
    release_id = str(report.get("release_id") or "")
    start = text.find("The dataset IDs are `rushilrawat/garhwali-corpus`")
    end = text.find("\n\n## Try three vocabulary rows", start)
    if start < 0 or end < 0:
        raise ValueError("Cannot find the developer quick-start release summary")
    intro = "\n".join((
        "The dataset IDs are `rushilrawat/garhwali-corpus` (text and reference tables)",
        "and `rushilrawat/garhwali-speech` (audio and speech metadata). Both repositories",
        "are public. The Hub cards link to the latest published revisions and preserve release history.",
        "This guide is bundled with `" + release_id + "`; its",
        "configuration counts match that package manifest. Use the Hub cards for current publication",
        "status and immutable revisions. The packages preserve a common rights/quality",
        "envelope, schema, and loading guidance. These examples stream the published",
        "configs. Pass a commit SHA as `revision=` when",
        "you need an immutable Hub snapshot.",
    ))
    text = text[:start] + intro + text[end:]

    counts = dict(report.get("content_config_counts") or {})
    reference_counts = {
        name: int(details.get("records", 0))
        for name, details in (report.get("tables") or {}).items()
    }
    counts.update(reference_counts)
    lines = text.splitlines()
    for index, line in enumerate(lines):
        for name, count in counts.items():
            if line.startswith(f"| `{name}` |"):
                cells = line.split("|")
                if len(cells) >= 4:
                    cells[2] = f" {count:,} "
                    lines[index] = "|".join(cells)
                break
    expansion_count = int(counts.get("text_expansion", 0))
    if expansion_count:
        expansion_row = (
            f"| `text_expansion` | {expansion_count:,} | Strict-tier Garhwali additions; "
            "train-only; machine-screened, not native-reviewed |"
        )
        if not any(line.startswith("| `text_expansion` |") for line in lines):
            insertion = next(
                (i + 1 for i, line in enumerate(lines) if line.startswith("| `text` |")),
                None,
            )
            if insertion is not None:
                lines.insert(insertion, expansion_row)
    resource_count = int(counts.get("text_resources", 0))
    if resource_count:
        resource_row = (
            f"| `text_resources` | {resource_count:,} | Supplementary rights-cleared resources; "
            "quality varies; not an evaluation set |"
        )
        if not any(line.startswith("| `text_resources` |") for line in lines):
            insertion = next(
                (i + 1 for i, line in enumerate(lines) if line.startswith("| `text_expansion` |")),
                next((i + 1 for i, line in enumerate(lines) if line.startswith("| `text` |")), None),
            )
            if insertion is not None:
                lines.insert(insertion, resource_row)
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

    content_rows = int(report.get("public_profile_package_rows", 0))
    reference_rows = sum(reference_counts.values())
    total_rows = content_rows + reference_rows
    summary = (
        f"The `{release_id}` package manifest reports **{total_rows:,} total view rows**: "
        f"{content_rows:,} content/config rows plus {reference_rows:,} reference rows. "
        "This is not a unique-example count."
    )
    text, replacements = re.subn(
        r"The (?:release|`[^`]+` package manifest) reports \*\*[\d,]+ total view rows\*\*:.*?(?:This is not [^.]+ unique examples\.|This is not a unique-example count\.)",
        summary,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if replacements != 1:
        raise ValueError("Cannot synchronize the developer quick-start package total")
    expansion_heading = "## Load the fast-tracked text view"
    start = text.find(expansion_heading)
    if start >= 0:
        next_heading = text.find("\n## ", start + 1)
        text = text[:start] + (text[next_heading + 1:] if next_heading >= 0 else "")
    expansion_count = int(counts.get("text_expansion", 0))
    if expansion_count:
        section = f'''## Load the fast-tracked text view

The `text_expansion` config contains **{expansion_count:,}** train-split Garhwali
candidates already present in the catalog. It is not new source ingestion or an
independent evaluation set. Currently zero rows meet the conservative training-
recommendation rule because source-level eligibility or quality evidence
remains unresolved. Rows retain their rights and quality fields; review each
row before downstream reuse.

```python
from datasets import load_dataset

extra_text = load_dataset(
    "rushilrawat/garhwali-corpus", "text_expansion", split="train", streaming=True
)
for row in extra_text.take(3):
    print(row["text"], row["rights_status"], row["quality_status"])
```

'''
        marker = "## Configurations and exact release counts"
        position = text.find(marker)
        if position >= 0:
            text = text[:position] + section + text[position:]
    resource_count = int(counts.get("text_resources", 0))
    if resource_count:
        section = f'''## Load supplementary text resources

The `text_resources` config exposes **{resource_count:,}** additional unique
Garhwali records already present in the source catalog. This is a lookup and
research view with varied quality; it is not an evaluation set or uniformly
training-ready. Check record-level rights and quality fields before reuse.

```python
from datasets import load_dataset

resources = load_dataset(
    "rushilrawat/garhwali-corpus", "text_resources", split="train", streaming=True
)
for row in resources.take(3):
    print(row["text"], row["redistribution_status"], row["quality_status"])
```

'''
        marker = "## Configurations and exact release counts"
        position = text.find(marker)
        if position >= 0:
            text = text[:position] + section + text[position:]
    return text


def update_dataset_card(report: dict) -> None:
    path = PUBLIC_DATA / "README.md"
    text = path.read_text(encoding="utf-8")
    front, body = text.split("---\n", 2)[1:]
    quick_heading = "## Developer quick start"
    quick_start_at = body.find(quick_heading)
    if quick_start_at >= 0:
        summary_at = body.find("\n## What this repository provides", quick_start_at)
        if summary_at >= 0:
            body = body[:quick_start_at] + body[summary_at + 1:]
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
    config_rows = []
    descriptions = {
        "text": "Garhwali text examples",
        "text_expansion": "strict-tier train-split candidates; zero currently meet training recommendation; not evaluation data",
        "text_resources": "rights-cleared supplementary text; varied quality, not for evaluation",
        "lexicon": "vocabulary and pronunciation candidates",
        "asr": "provider/human transcripts (unadjudicated)",
        "sravaani_drafts": "machine transcript drafts; not ground truth",
        "catalog": "unique text inventory with content and metadata-only entries",
        "instructions": "instruction/response examples",
        "geography": "place facts and citations",
        "historical_terms": "historical names and terms",
        "literary_people": "writer and contributor metadata",
        "literary_works": "work-level bibliography",
        "popular_songs": "song-level metadata, no lyrics",
        "university_research": "research bibliography",
    }
    for name, count in report.get("content_config_counts", {}).items():
        config_rows.append(
            f"| `{name}` | {count:,} | {descriptions.get(name, 'content view; inspect row metadata')} |"
        )
    for name in ("record_index", "source_catalog", "record_sources"):
        details = report.get("tables", {}).get(name, {})
        if details:
            purpose = {
                "record_index": "one metadata reference per archived row; not training data",
                "source_catalog": "deduplicated source and rights references",
                "record_sources": "record-to-source join table",
            }[name]
            config_rows.append(f"| `{name}` | {details['records']:,} | {purpose} |")
    config_table = "\n".join(config_rows)
    quick_start = f"""## Developer quick start

Install the small tabular-data stack with `pip install datasets pandas duckdb`, then stream a tiny vocabulary sample:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "rushilrawat/garhwali-corpus", "lexicon", split="train", streaming=True
)
for row in lexicon.take(3):
    print(row["form"], row.get("glosses"), row["rights_status"], row["quality_status"])
```

The common record envelope is `rights_status`, `reuse_scope`, `license_labels`,
`quality_status`, and `record_quality_flags`; source-specific provenance and
review fields remain alongside it. Dataset cards and schema guide explain how
to filter these fields and how to read each configuration.

## Configurations and current row counts

Counts are rows in this release's views, not unique examples. Configurations can
overlap, and reference-index rows are not training examples.

| Configuration | Rows | Use |
| --- | ---: | --- |
{config_table}

Pandas and DuckDB recipes, the full schema, searchable lexicon example, and
speech loading instructions are in the [developer quick start](DEVELOPER_QUICKSTART.md)
and [schema guide](DATASET_SCHEMA.md). A minimal [lexicon search script](search_garhwali_lexicon.py)
is shipped at the release root.

"""
    summary = f"""## What this repository provides

This public dataset has rights-filtered content configurations containing **{report['public_profile_package_rows']:,} rows** across {report.get('public_content_config_count', 0)} named configurations and {report.get('public_content_config_split_views', 0)} config/split views. Separately, the metadata-only reference index covers every one of the **{report['records']:,} rows** in the complete all-data archive, including all 216 structured geography, history, literature, music, and research records.

The reference index includes **{report['source_catalog_records']:,} deduplicated source records** and **{report['record_source_links']:,} record-to-source links**. It exposes available names and titles, source URLs, attribution, rights status, and quality metadata. Record-level rights are marked `not_recorded` for **{report.get('record_rights_status_counts', {}).get('not_recorded', 0):,} rows**; other rows include rights-pending, reviewed-unresolved, metadata-only, or cleared statuses. `not_recorded` is not permission to reuse a record: inspect its linked source entry and terms. The index does not contain the referenced works' text, lyrics, transcripts, audio, speaker identifiers, local paths, or content hashes. These are archive-row counts with overlapping views, not unique-example counts; the reference rows themselves are not training examples. Links and bibliographic facts do not grant rights to copy or reuse source material.
"""
    package_manifest = json.loads(
        (PUBLIC_DATA / "manifest.json").read_text(encoding="utf-8")
    )
    package_release_id = package_manifest.get('release_id') or report['release_id']
    release_marker = "Release: **" + str(package_release_id) + "**"
    if release_marker not in body:
        raise ValueError("Cannot add repository summary to the dataset card")
    body = body.replace(release_marker, release_marker + "\n\n" + quick_start + summary, 1)

    legacy_start = body.find("Three normalized reference tables")
    if legacy_start >= 0:
        legacy_end = body.find("\n## ", legacy_start)
        if legacy_end >= 0:
            body = body[:legacy_start] + body[legacy_end:]

    section = f"""## Complete source reference index

The three metadata tables cover **{report['records']:,} records** from the complete local all-data archive. `record_index` has one row per archived record, `source_catalog` contains {report['source_catalog_records']:,} deduplicated source references, and `record_sources` contains {report['record_source_links']:,} join rows. The tables include source URLs, available attribution, rights and quality status, and factual catalog fields. They exclude source text, lyrics, transcripts, machine drafts, audio, speaker identifiers, local paths, and content hashes.

The current public package has **{report['public_profile_package_rows']:,} rows** across its content configurations; **{report['records_with_content_in_public_profile']:,}** indexed records have a corresponding public content value. Other catalog entries retain identifiers and source/rights metadata while their full text remains outside public content. Reference-index rows are not training examples and must not be added to corpus sample counts. Source links point to original material and do not grant reuse rights.

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
    quickstart_path = PUBLIC_DATA / "DEVELOPER_QUICKSTART.md"
    quickstart_path.write_text(
        sync_quickstart_text(
            quickstart_path.read_text(encoding="utf-8"),
            {**report, "release_id": package_release_id},
        ),
        encoding="utf-8",
    )


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
            sources_file.write(json_value(
                normalize_record(sources[source_id], family="source_catalog")
            ) + "\n")
    with TABLES["record_sources"].open("w", encoding="utf-8") as links_file:
        for link in links:
            links_file.write(json_value(
                normalize_record(link, family="record_sources")
            ) + "\n")

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
    content_config_counts = {}
    for config_split, details in package_manifest.get("configs", {}).items():
        config = config_split.split("/", 1)[0]
        if config not in reference_config_names | {"source_index"}:
            content_config_counts[config] = (
                content_config_counts.get(config, 0) + details["records"]
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
        "record_schema_version": "1.0.0",
        "profile": "metadata_only_complete_reference_index",
        "records": sum(counts.values()),
        "records_by_family": dict(sorted(counts.items())),
        "records_with_content_in_public_profile": sum(public_counts.values()),
        "public_profile_package_rows": public_profile_rows,
        "content_config_counts": dict(sorted(content_config_counts.items())),
        "public_content_config_count": len(content_config_counts),
        "public_content_config_split_views": sum(
            1 for key in package_manifest.get("configs", {})
            if key.split("/", 1)[0] not in reference_config_names | {"source_index"}
        ),
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
