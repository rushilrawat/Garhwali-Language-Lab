#!/usr/bin/env python3
"""Build provenance-complete, source-license-specific Garhwali text exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".cache/license_exports/2026-10-05"
DEFAULT_ATTRIBUTION_OVERLAY = ROOT / "research/source-attribution-overlays-2026-10-05.json"
SWADESH_TITLE = "Appendix:Garhwali Swadesh list"
LICENSES = {
    "tatoeba_cc_by_2_0_fr": ("CC-BY-2.0-FR", "https://creativecommons.org/licenses/by/2.0/fr/"),
    "wikimedia_cc_by_sa_4_0": ("CC-BY-SA-4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    "wiktionary_cc_by_sa_4_0": ("CC-BY-SA-4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    "obs_tlf_gbm_v1_cc_by_sa_4_0": ("CC-BY-SA-4.0", "https://creativecommons.org/licenses/by-sa/4.0/"),
    "lsi_1916_public_domain": ("PDM-1.0", "https://creativecommons.org/publicdomain/mark/1.0/"),
}
HISTORY_RE = re.compile(r"https?://[^\s;]+action=history[^\s;]*")
ATTRIBUTION_OVERLAY_GROUPS = {
    "tatoeba_cc_by_2_0_fr",
    "wikimedia_cc_by_sa_4_0",
    "wiktionary_cc_by_sa_4_0",
}
ATTRIBUTION_OVERLAY_FIELDS = (
    "attribution_name", "attribution", "source_url", "source_history_url",
    "source_title", "source_revision", "source_snapshot_sha256", "license_id",
    "license_url", "rights_status", "quality_flags", "modifications",
    "upstream_owner", "upstream_orphaned", "upstream_unapproved",
    "source_api_url", "api_retrieved_at", "attribution_profile_url",
    "contributor_added_date", "attribution_status", "attribution_evidence_url",
    "attribution_evidence_sha256", "attribution_evidence_retrieved_at",
)


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def _title_from_history(history_url: str) -> str | None:
    values = parse_qs(urlparse(history_url).query).get("title")
    return values[0] if values else None


def _wiki_urls(row: dict, source_id: str) -> tuple[str, str, int | None, str | None]:
    revision = row.get("revision_id") or row.get("source_revision")
    if revision is not None:
        revision = int(revision)

    if source_id == "wiktionary_swadesh_thematic":
        domain, title = "en.wiktionary.org", SWADESH_TITLE
    else:
        history = HISTORY_RE.search(str(row.get("attribution") or ""))
        existing = history.group(0).replace("&amp;", "&") if history else ""
        parsed = urlparse(existing)
        domain = parsed.netloc or ("en.wiktionary.org" if source_id == "wiktionary_en" else "incubator.wikimedia.org")
        title = row.get("title") or _title_from_history(existing)
        if not title and row.get("source_url"):
            title = _title_from_history(str(row["source_url"]))
        if not title:
            raise ValueError(f"Missing source page title for {row.get('record_id')}")

    if revision is None:
        raise ValueError(f"Missing source revision for {row.get('record_id')}")

    source_url = f"https://{domain}/w/index.php?{urlencode({'title': title, 'oldid': revision})}"
    history_url = f"https://{domain}/w/index.php?{urlencode({'title': title, 'action': 'history'})}"
    return source_url, history_url, revision, title


def _project_record(row: dict, source_group: str, metadata: dict | None = None) -> dict:
    source_id = row.get("source_id")
    license_id, license_url = LICENSES[source_group]
    if row.get("license_id") != license_id:
        raise ValueError(f"Unexpected license for {row.get('record_id')}: {row.get('license_id')}")
    if row.get("iso_639_3") != "gbm":
        raise ValueError(f"Non-Garhwali row in source export: {row.get('record_id')}")

    record = {
        "schema_version": "garhwali-source-license-export-v1",
        "record_id": row["record_id"],
        "source_id": source_id,
        "language": "gbm",
        "script": row.get("script"),
        "text_original": row.get("text_original", row.get("text_normalized")),
        "text_normalized": row.get("text_normalized", row.get("text_original")),
        "english_gloss": row.get("english_gloss", row.get("gloss_en")),
        "semantic_domain": row.get("semantic_domain"),
        "license_id": license_id,
        "license_url": license_url,
        "quality_status": row.get("quality_status", "unreviewed"),
        "quality_flags": list(row.get("quality_flags") or []),
        "native_reviewed": bool(row.get("native_reviewed", False)),
        "training_eligible": bool(row.get("training_eligible", False)),
        "genre": row.get("genre"),
        "modifications": row.get("modifications") or "Text value preserved from the local source record; provenance fields standardized for this export.",
        "source_snapshot_sha256": (row.get("provenance") or {}).get("sha256"),
        "source_retrieved_at": (row.get("provenance") or {}).get("retrieved_at"),
        "benchmark_overlap_notice": "May overlap open GarhwaliBench v0.2 draft examples; do not treat as an independent evaluation set.",
    }

    if source_id == "tatoeba":
        if metadata is None:
            raise ValueError(f"Missing Tatoeba attribution for {row.get('record_id')}")
        sentence_id = str(row["record_id"]).split(":", 1)[1]
        if str(metadata.get("sentence_id")) != sentence_id:
            raise ValueError(f"Tatoeba attribution ID mismatch for {row.get('record_id')}")
        contributor = metadata.get("contributor_username")
        if not contributor or not metadata.get("page_has_sentence_id"):
            raise ValueError(f"Tatoeba creator attribution evidence incomplete for {sentence_id}")
        if metadata.get("license") != "CC BY 2.0 FR" or metadata.get("lang") != "gbm":
            raise ValueError(f"Unexpected Tatoeba license/language for {sentence_id}")
        item_url = str(metadata.get("item_url") or row.get("item_url"))
        record.update({
            "attribution_name": contributor,
            "attribution": f"Sentence #{sentence_id} contributed by {contributor} to Tatoeba; {item_url}; CC BY 2.0 FR.",
            "source_url": item_url,
            "source_history_url": None,
            "source_revision": None,
            "upstream_owner": metadata.get("owner"),
            "upstream_orphaned": metadata.get("owner") is None,
            "upstream_unapproved": bool(metadata.get("is_unapproved")),
            "source_api_url": metadata.get("api_url"),
            "api_retrieved_at": metadata.get("retrieved_at"),
            "attribution_profile_url": metadata.get("contributor_profile_url"),
            "contributor_added_date": metadata.get("added_date_label"),
            "attribution_status": metadata.get("attribution_status"),
            "attribution_evidence_url": item_url,
            "attribution_evidence_sha256": metadata.get("sentence_page_sha256"),
            "attribution_evidence_retrieved_at": metadata.get("sentence_page_retrieved_at"),
        })
        record["quality_flags"] = [flag for flag in record["quality_flags"] if flag != "missing_contributor"]
        if record["upstream_orphaned"]:
            record["quality_flags"].append("upstream_sentence_orphaned")
        record["quality_flags"].append("creator_attribution_recovered_from_sentence_page")
        record["rights_status"] = "sentence_license_declared_by_api; creator attributed from sentence page; sentence is orphaned in API"
        return record

    source_url, history_url, revision, title = _wiki_urls(row, source_id)
    record.update({
        "attribution_name": "English Wiktionary contributors" if source_id.startswith("wiktionary") else "Wikimedia Incubator contributors",
        "attribution": f"{ 'English Wiktionary' if source_id.startswith('wiktionary') else 'Wikimedia Incubator' } contributors; page {title}; revision {revision}; {source_url}; CC BY-SA 4.0; see history for authorship.",
        "source_title": title,
        "source_url": source_url,
        "source_history_url": history_url,
        "source_revision": revision,
        "rights_status": "source project declares CC BY-SA 4.0; revision and history linked; item-specific third-party-material exceptions not independently audited",
    })
    return record


def build_exports(
    tatoeba_rows: list[dict],
    wikimedia_rows: list[dict],
    wiktionary_rows: list[dict],
    swadesh_rows: list[dict],
    tatoeba_evidence: dict,
) -> dict[str, list[dict]]:
    evidence = {str(row["sentence_id"]): row for row in tatoeba_evidence.get("records", [])}
    if len(evidence) != len(tatoeba_evidence.get("records", [])):
        raise ValueError("Duplicate Tatoeba sentence IDs in attribution evidence")
    tatoeba_ids = {str(row["record_id"]).split(":", 1)[1] for row in tatoeba_rows}
    if tatoeba_ids != set(evidence):
        raise ValueError("Tatoeba source rows and attribution evidence IDs do not match exactly")

    exports = {
        "tatoeba_cc_by_2_0_fr": [
            _project_record(row, "tatoeba_cc_by_2_0_fr", evidence[str(row["record_id"]).split(":", 1)[1]])
            for row in tatoeba_rows
        ],
        "wikimedia_cc_by_sa_4_0": [
            _project_record(row, "wikimedia_cc_by_sa_4_0") for row in wikimedia_rows
        ],
        "wiktionary_cc_by_sa_4_0": [
            _project_record(row, "wiktionary_cc_by_sa_4_0")
            for row in [*wiktionary_rows, *swadesh_rows]
        ],
    }

    all_ids = [row["record_id"] for rows in exports.values() for row in rows]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("Duplicate record IDs across license exports")
    return {name: sorted(rows, key=lambda row: row["record_id"]) for name, rows in exports.items()}


def build_attribution_overlays(exports: dict[str, list[dict]]) -> dict:
    """Create content-free source metadata overlays keyed by stable record ID."""
    records = {}
    for group in sorted(ATTRIBUTION_OVERLAY_GROUPS):
        for row in exports.get(group, []):
            record_id = row.get("record_id")
            source_id = row.get("source_id")
            if not record_id or not source_id:
                raise ValueError(f"Missing source identity in attribution overlay: {row}")
            if record_id in records:
                raise ValueError(f"duplicate attribution overlay record ID: {record_id}")
            overlay = {
                key: row[key] for key in ATTRIBUTION_OVERLAY_FIELDS
                if row.get(key) not in (None, "", [])
            }
            overlay["source_id"] = source_id
            if source_id == "tatoeba":
                overlay["contributor"] = row.get("attribution_name")
                overlay["contributor_profile_url"] = row.get("attribution_profile_url")
                overlay["item_url"] = row.get("source_url")
            records[record_id] = overlay
    return {
        "schema_version": "garhwali-source-attribution-overlay-v1",
        "audit_date": "2026-10-05",
        "records": records,
    }


def build_benchmark_exports(benchmark_rows: list[dict]) -> dict[str, list[dict]]:
    source_groups = {
        "obs_tlf_gbm_v1": "obs_tlf_gbm_v1_cc_by_sa_4_0",
        "lsi_1916_grierson_garhwali_specimens": "lsi_1916_public_domain",
    }
    exports = {group: [] for group in source_groups.values()}
    for row in benchmark_rows:
        bases = row.get("rights", {}).get("public_rights_basis_as_recorded", [])
        for basis in bases:
            source_id = basis.get("source_id")
            if source_id not in source_groups or basis.get("rights_status") != "rights_assessed_compatible":
                continue
            group = source_groups[source_id]
            expected_license, expected_url = LICENSES[group]
            if basis.get("license_id") != expected_license or basis.get("license_url") != expected_url:
                raise ValueError(f"Unexpected rights metadata for {basis.get('record_id')}")
            source_record = next((
                item for item in row.get("legacy_record", {}).get("provenance", [])
                if item.get("source_id") == source_id and item.get("record_id") == basis.get("record_id")
            ), {})
            export_record = {
                "schema_version": "garhwali-source-license-export-v1",
                "record_id": f"{basis.get('record_id')}#{row.get('example_id')}",
                "source_record_id": basis.get("record_id"),
                "example_id": row.get("example_id"),
                "benchmark_id": row.get("benchmark_id"),
                "benchmark_split": row.get("split"),
                "benchmark_task": row.get("task"),
                "source_id": source_id,
                "language": basis.get("iso_639_3", row.get("language")),
                "script": basis.get("script", row.get("declared_script")),
                "text_original": row.get("payload", {}).get("text"),
                "text_normalized": row.get("payload", {}).get("text"),
                "license_id": expected_license,
                "license_url": expected_url,
                "rights_status": basis.get("rights_status"),
                "rights_evidence_url": basis.get("rights_evidence"),
                "attribution": basis.get("attribution"),
                "author": basis.get("author"),
                "title": basis.get("title"),
                "source_url": basis.get("source_url"),
                "source_revision": source_record.get("source_revision", basis.get("source_revision")),
                "source_version": source_record.get("source_version"),
                "source_file": source_record.get("source_file"),
                "source_snapshot_sha256": basis.get("source_snapshot_sha256", source_record.get("source_snapshot_sha256")),
                "source_pdf_sha256": basis.get("source_pdf_sha256", source_record.get("source_pdf_sha256")),
                "source_pdf_pages": source_record.get("source_pdf_pages"),
                "source_printed_pages": source_record.get("source_printed_pages"),
                "source_citation": source_record.get("source_citation"),
                "publication_year": basis.get("publication_year"),
                "modifications": basis.get("modifications"),
                "quality_status": "unreviewed",
                "quality_flags": basis.get("quality_flags", []),
                "native_reviewed": False,
                "training_eligible": False,
                "public_release_cleared": False,
                "benchmark_overlap_notice": "This record is part of the open v0.2 draft and is not independent evaluation evidence.",
            }
            if not export_record["record_id"] or not export_record["text_normalized"]:
                raise ValueError(f"Missing source record ID or text for {row.get('example_id')}")
            exports[group].append(export_record)

    for group, records in exports.items():
        record_ids = [row["record_id"] for row in records]
        if len(record_ids) != len(set(record_ids)):
            raise ValueError(f"Duplicate benchmark source record IDs in {group}")
        exports[group] = sorted(records, key=lambda row: row["record_id"])
    return exports


def _write_exports(
    exports: dict[str, list[dict]],
    output_dir: Path,
    attribution_overlay_path: Path = DEFAULT_ATTRIBUTION_OVERLAY,
) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    attribution_overlay = build_attribution_overlays(exports)
    attribution_overlay_path.parent.mkdir(parents=True, exist_ok=True)
    attribution_overlay_path.write_text(
        json.dumps(attribution_overlay, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    try:
        attribution_overlay_name = attribution_overlay_path.resolve().relative_to(ROOT)
    except ValueError:
        attribution_overlay_name = attribution_overlay_path
    manifest = {
        "schema_version": "garhwali-source-license-export-manifest-v1",
        "built_from_local_corpus": True,
        "public_release_cleared": False,
        "exports": {},
        "attribution_overlay": {
            "path": attribution_overlay_name.as_posix(),
            "records": len(attribution_overlay["records"]),
            "sha256": hashlib.sha256(
                attribution_overlay_path.read_bytes()
            ).hexdigest(),
        },
        "notes": [
            "These source-specific candidates preserve row quality and training-eligibility flags; an open license does not establish linguistic quality.",
            "Wikimedia/Wiktionary rows retain page revision/history links, but page-specific third-party material and reuse terms have not been audited record by record.",
            "Tatoeba records are owner-null/orphaned upstream; their original creator is credited from the sentence page. All remain unreviewed and excluded from training-ready claims.",
            "Some texts overlap the open GarhwaliBench v0.2 draft and must not be used to claim independent model evaluation.",
            "The export layer does not set the final Hugging Face repository license or publish any files.",
        ],
    }
    for name, rows in sorted(exports.items()):
        path = output_dir / f"{name}.jsonl"
        contents = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        path.write_text(contents, encoding="utf-8")
        texts = Counter(row["text_normalized"] for row in rows)
        license_id, license_url = LICENSES[name]
        manifest["exports"][name] = {
            "path": path.name,
            "records": len(rows),
            "source_ids": dict(sorted(Counter(row["source_id"] for row in rows).items())),
            "unique_normalized_texts": len(texts),
            "repeated_text_rows": sum(count - 1 for count in texts.values() if count > 1),
            "license_id": license_id,
            "license_url": license_url,
            "sha256": hashlib.sha256(contents.encode("utf-8")).hexdigest(),
        }
    flattened = [row for rows in exports.values() for row in rows]
    all_texts = Counter(row.get("text_normalized") for row in flattened)
    manifest["total_records"] = len(flattened)
    manifest["unique_record_ids"] = len({row["record_id"] for row in flattened})
    manifest["unique_normalized_texts_across_exports"] = len(all_texts)
    manifest["repeated_text_rows_across_exports"] = sum(count - 1 for count in all_texts.values() if count > 1)
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--attribution-overlay", type=Path, default=DEFAULT_ATTRIBUTION_OVERLAY)
    parser.add_argument("--tatoeba-evidence", type=Path, default=ROOT / "research/tatoeba-attribution-audit-2026-10-05.json")
    args = parser.parse_args()
    corpus = ROOT / "corpus"
    restricted = ROOT / "restricted/thematic_web_lexicon.jsonl"
    inputs = [corpus / "tatoeba.jsonl", corpus / "wikimedia.jsonl", corpus / "incubator_wt.jsonl", corpus / "wiktionary_en.jsonl", restricted, args.tatoeba_evidence]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        parser.error("required local source files are missing: " + ", ".join(missing))
    exports = build_exports(
        read_jsonl(inputs[0]),
        [*read_jsonl(inputs[1]), *read_jsonl(inputs[2])],
        read_jsonl(inputs[3]),
        [row for row in read_jsonl(inputs[4]) if row.get("source_id") == "wiktionary_swadesh_thematic" and row.get("license_id") == "CC-BY-SA-4.0"],
        json.loads(inputs[5].read_text(encoding="utf-8")),
    )
    benchmark_dir = ROOT / "data/processed/evaluation/garhwali_bench/v0.2-draft"
    benchmark_rows = []
    for split in ("train", "validation", "test"):
        benchmark_rows.extend(read_jsonl(benchmark_dir / f"text_recommended__{split}.jsonl"))
    exports.update(build_benchmark_exports(benchmark_rows))
    manifest = _write_exports(exports, args.output_dir, args.attribution_overlay)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
