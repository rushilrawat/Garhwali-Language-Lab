"""Shared, non-destructive rights and quality envelope for released records."""

from __future__ import annotations

import json


COMMON_RECORD_FIELDS = (
    "rights_status",
    "reuse_scope",
    "license_labels",
    "quality_status",
    "record_quality_flags",
)

_RIGHTS_PLACEHOLDERS = {"", "not_assessed", "not_recorded", "unassessed"}


def _strings(value) -> list[str]:
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (TypeError, json.JSONDecodeError):
            return [value] if value else []
        return _strings(decoded)
    if isinstance(value, (list, tuple, set)):
        return [item for child in value for item in _strings(child)]
    return []


def _source_objects(row: dict) -> list[dict]:
    found = []
    for field in (
        "provenance", "sources", "public_rights_basis",
        "noncommercial_rights_basis", "rights_basis",
    ):
        values = row.get(field) or []
        if isinstance(values, dict):
            values = [values]
        if isinstance(values, list):
            found.extend(item for item in values if isinstance(item, dict))
    return found


def _license_labels(row: dict) -> list[str]:
    labels = _strings(row.get("license_labels"))
    objects = [row, *_source_objects(row)]
    for item in objects:
        for field in ("license_id", "license", "source_license"):
            value = item.get(field)
            if isinstance(value, str) and value.strip():
                labels.append(value.strip())
    return list(dict.fromkeys(labels))


def _rights_status(row: dict, family: str, labels: list[str]) -> str:
    status = row.get("rights_status")
    if status and str(status).strip().casefold() not in _RIGHTS_PLACEHOLDERS:
        return str(status)
    status = row.get("redistribution_status")
    if status:
        return str(status)
    status = row.get("record_rights_status")
    if status and str(status).strip().casefold() not in _RIGHTS_PLACEHOLDERS:
        return str(status)
    source_statuses = list(dict.fromkeys(
        str(item["rights_status"])
        for item in _source_objects(row)
        if item.get("rights_status")
        and str(item["rights_status"]).strip().casefold() not in _RIGHTS_PLACEHOLDERS
    ))
    if len(source_statuses) == 1:
        return source_statuses[0]
    if len(source_statuses) > 1:
        return "mixed_source_statuses; inspect provenance"
    if row.get("record_scope") == "factual_bibliographic_metadata_only":
        return "metadata_only; no license asserted for underlying work"
    if family == "record_sources":
        return "resolve_via_record_and_source_join"
    if family == "record_index":
        return "resolve_via_record_and_source_join"
    if row.get("text_publicly_available") is False:
        return "rights_pending"
    if row.get("public_rights_basis"):
        if labels:
            return "source_license_recorded; inspect provenance"
        return "public_basis_recorded; inspect provenance"
    if labels:
        return "source_terms_recorded; inspect provenance"
    return "not_assessed"


def _reuse_scope(row: dict, family: str, rights_status: str, labels: list[str]) -> str:
    scope = row.get("reuse_scope")
    if scope:
        return str(scope)
    if family in {"record_index", "record_sources"}:
        return "resolve_via_record_and_source_join"
    if row.get("record_scope") == "factual_bibliographic_metadata_only":
        return "metadata facts only; underlying-work rights are not asserted"
    if row.get("commercial_use_status"):
        scope = str(row["commercial_use_status"])
        if row.get("sharealike_required"):
            scope += "; share-alike required"
        return scope
    normalized = {label.upper().replace(" ", "-") for label in labels}
    if any(label.startswith("CC-BY-NC-SA-") for label in normalized):
        return "noncommercial use; attribution and share-alike required"
    if any(label.startswith("CC-BY-SA-") for label in normalized):
        return "attribution and share-alike required under source license"
    if any(label.startswith("CC-BY-NC-") for label in normalized):
        return "noncommercial use and attribution required under source license"
    if any(label.startswith("CC-BY-") for label in normalized):
        return "attribution required under source license"
    if "MIT" in normalized:
        return "MIT terms; preserve copyright and license notice"
    if "APACHE-2.0" in normalized:
        return "Apache-2.0 terms; preserve notices and review source scope"
    if "CC0-1.0" in normalized:
        return "CC0 dedication recorded; verify any third-party content"
    if "PDM-1.0" in normalized or any(
        label.startswith("PUBLIC-DOMAIN") for label in normalized
    ):
        return "public-domain mark or status recorded; verify source and jurisdiction"
    if rights_status == "rights_pending":
        return "not cleared for redistribution"
    if rights_status.startswith("metadata_only"):
        return "metadata only; underlying-work rights are not asserted"
    if row.get("public_rights_basis") or labels:
        return "source-specific terms; inspect provenance before reuse"
    return "not assessed"


def _quality_status(row: dict, family: str, flags: list[str]) -> str:
    status = row.get("quality_status")
    if status:
        return str(status)
    quality_metadata = row.get("quality_metadata")
    if not isinstance(quality_metadata, dict):
        quality_metadata = {}
    if row.get("native_reviewed") is True or quality_metadata.get("native_reviewed") is True:
        return "native_reviewed"
    for field in ("transcript_review_status", "review_status", "machine_draft_review_status"):
        if row.get(field):
            return str(row[field])
    if quality_metadata.get("review_status"):
        return str(quality_metadata["review_status"])
    if row.get("machine_transcript_model") or row.get("machine_draft_model"):
        return "machine_generated_unreviewed"
    if row.get("quality_v2") or row.get("quality_tiers"):
        return "automated_quality_assessed_unreviewed"
    if row.get("quality_summary_json"):
        try:
            summary = json.loads(row["quality_summary_json"])
        except (TypeError, json.JSONDecodeError):
            summary = {}
        if summary:
            return "automated_quality_assessed_unreviewed"
    if family in {"record_index", "source_catalog", "record_sources"}:
        return "provenance_metadata_only"
    if flags:
        return "automated_flags_present; not linguistically reviewed"
    return "not_reviewed"


def normalize_record(row: dict, family: str = "") -> dict:
    """Return a copy with common filter fields while preserving source detail.

    This envelope deliberately never promotes a public URL or an unknown license
    into permission. Source-specific fields remain authoritative for decisions.
    """
    result = dict(row)
    labels = _license_labels(result)
    flags = []
    for field in (
        "record_quality_flags", "quality_flags", "training_quality_flags",
        "proposed_machine_transcript_flags",
    ):
        flags.extend(_strings(result.get(field)))
    for item in _source_objects(result):
        flags.extend(_strings(item.get("quality_flags")))
    if result.get("quality_summary_json"):
        try:
            summary = json.loads(result["quality_summary_json"])
        except (TypeError, json.JSONDecodeError):
            summary = {}
        if isinstance(summary, dict):
            for key in ("quality_flags", "quality_tiers"):
                flags.extend(_strings(summary.get(key)))
    if result.get("text_publicly_available") is False:
        flags.append("source_text_not_publicly_redistributable")
    if result.get("machine_draft"):
        flags.append("machine_draft_present; not human ground truth")
    flags = list(dict.fromkeys(flag for flag in flags if flag))

    result["rights_status"] = _rights_status(result, family, labels)
    result["reuse_scope"] = _reuse_scope(
        result, family, result["rights_status"], labels
    )
    result["license_labels"] = labels
    result["quality_status"] = _quality_status(result, family, flags)
    result["record_quality_flags"] = flags
    return result
