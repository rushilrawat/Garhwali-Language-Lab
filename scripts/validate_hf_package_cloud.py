#!/usr/bin/env python3
"""Independent full-package validation for the Hugging Face all-data export."""

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from pathlib import Path

from build_huggingface_dataset import (
    is_public_factual_metadata_row,
    is_publishable_provenance,
    recommended_text_training_row,
    source_record_ids,
    upstream_split_overlap_ids,
)
from garhwali_lab.hashing import sha256_file as sha256


KNOWLEDGE_CONFIGS = {
    'geography', 'historical_terms', 'literary_people',
    'literary_works', 'popular_songs', 'university_research',
}
RECORD_SCHEMA_VERSION = '1.0.0'
VALIDATION_CONTRACT_VERSION = '1.0.0'
RECORD_ENVELOPE_STRING_FIELDS = (
    'rights_status', 'reuse_scope', 'quality_status',
)
RECORD_ENVELOPE_LIST_FIELDS = (
    'license_labels', 'record_quality_flags',
)
QUALITY_DETAIL_FIELDS = (
    'quality_flags', 'machine_transcript_quality', 'quality_v2',
    'language_quality', 'surface_quality', 'quality_metadata',
)


def script_profile(text):
    counts = Counter()
    for char in str(text or ""):
        code = ord(char)
        if 0x0900 <= code <= 0x097F:
            counts["Deva"] += 1
        elif 0x0980 <= code <= 0x09FF:
            counts["Beng"] += 1
        elif char.isascii() and char.isalpha():
            counts["Latn"] += 1
        elif char.isalpha():
            counts[unicodedata.name(char, "OTHER").split()[0]] += 1
    return counts.most_common(1)[0][0] if counts else "none"


def identity(config, row):
    if config == "record_index":
        return row.get("record_ref")
    if config == "source_catalog":
        return row.get("source_ref_id")
    if config == "record_sources":
        record_ref = row.get("record_ref")
        source_ref_id = row.get("source_ref_id")
        return f"{record_ref}\0{source_ref_id}" if record_ref and source_ref_id else None
    if config == "asr" or config == "sravaani_drafts":
        return row.get("audio_sha256")
    if config == "instructions":
        return row.get("instruction_sha256")
    return row.get("id") or row.get("text_sha256") or row.get("record_id")


def has_nonempty_value(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, dict):
        return any(has_nonempty_value(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(has_nonempty_value(item) for item in value)
    return True


def has_source_traceability(config, row):
    """Return whether a row has the minimum source locator for its config.

    This is an evidence-presence check only. It does not establish rights,
    source accuracy, or linguistic correctness.
    """
    if config in {'asr', 'sravaani_drafts'}:
        audio_hash = str(row.get('audio_sha256') or '')
        return (
            bool(str(row.get('source') or '').strip())
            and len(audio_hash) == 64
            and all(char in '0123456789abcdefABCDEF' for char in audio_hash)
            and int(row.get('source_audio_records') or 0) > 0
        )
    if config == 'record_index':
        try:
            references = json.loads(row.get('source_ref_ids_json') or '[]')
        except (TypeError, json.JSONDecodeError):
            return False
        return isinstance(references, list) and bool(references) and all(
            isinstance(reference, str) and reference.strip()
            for reference in references
        )
    if config == 'record_sources':
        return bool(
            str(row.get('record_ref') or '').strip()
            and str(row.get('source_ref_id') or '').strip()
        )
    if config == 'source_catalog':
        locator_fields = (
            'source_url', 'source_snapshot_sha256', 'source_capture_path',
        )
        attribution = str(row.get('attribution') or '')
        attribution_has_url = bool(re.search(r'https?://\S+', attribution))
        tatoeba_sentence_ref = (
            str(row.get('source_id') or '').casefold() == 'tatoeba'
            and bool(re.search(r'tatoeba sentence\s+\d+', attribution, re.IGNORECASE))
        )
        return bool(
            str(row.get('source_ref_id') or '').strip()
            and (
                any(str(row.get(field) or '').strip() for field in locator_fields)
                or attribution_has_url
                or tatoeba_sentence_ref
            )
        )

    sources = row.get('provenance') or row.get('sources') or []
    if not isinstance(sources, list):
        return False
    for source in sources:
        if not isinstance(source, dict):
            continue
        has_identifier = any(
            str(source.get(field) or '').strip()
            for field in ('source_id', 'source_ref_id', 'record_id', 'source_url')
        )
        has_locator = any(
            str(source.get(field) or '').strip()
            for field in (
                'source_url', 'source_snapshot_sha256', 'source_capture_path',
                'record_id',
            )
        ) or bool(
            str(source.get('file') or '').strip()
            and source.get('line') is not None
        )
        if has_identifier and has_locator:
            return True
    return False


def source_split_overlap_evidence(row, direct_eval_record_ids, aggregate_eval_record_ids):
    """Return the upstream held-out evidence label used by the exporter."""
    row_source_ids = source_record_ids(row)
    direct_matches = row_source_ids & direct_eval_record_ids
    aggregate_matches = row_source_ids & aggregate_eval_record_ids
    provenance = row.get('provenance') or row.get('sources') or []
    if isinstance(provenance, dict):
        provenance = provenance.get('provenance') or []
    vaani_test_matches = {
        str(item.get('record_id'))
        for item in provenance if isinstance(item, dict)
        and (
            item.get('source_id') in {
                'vaani-official-test-remainder',
                'vaani-transcription-part',
            }
            or item.get('canonical_transcript_source')
            == 'ARTPARK-IISc/Vaani-transcription-part'
        )
        and item.get('transcription_split') == 'test'
        and item.get('record_id')
    }
    if direct_matches and aggregate_matches:
        status = 'upstream_record_and_transcript_match'
    elif direct_matches:
        status = 'upstream_eval_record_id_match'
    elif aggregate_matches:
        status = 'upstream_eval_transcript_match'
    elif vaani_test_matches:
        status = 'upstream_vaani_test_source_record_match'
    else:
        status = 'no_upstream_eval_match_detected'
    return status, sorted(direct_matches | aggregate_matches | vaani_test_matches)


UPSTREAM_AUDIT_JSON = 'research/huggingface-upstream-split-overlap-2026-10-05.json'
UPSTREAM_AUDIT_MD = 'research/huggingface-upstream-split-overlap-2026-10-05.md'
TEXT_LIKE_CONFIGS = {'text', 'text_expansion', 'text_resources'}
PER_CONFIG_ERROR_FIELDS = (
    'unsupported_garhwali_label', 'missing_admission_metadata',
    'invalid_training_recommendation',
    'source_split_evidence_mismatch', 'upstream_eval_overlap_left_in_train',
    'source_overlap_split_without_evidence',
    'missing_acceptable_responses', 'knowledge_missing_source_provenance',
    'knowledge_untraceable_source_provenance',
    'knowledge_missing_quality_metadata', 'knowledge_missing_rights_status',
    'knowledge_missing_public_rights',
    *(f'record_envelope_missing_{field}' for field in RECORD_ENVELOPE_STRING_FIELDS),
    *(f'record_envelope_invalid_{field}' for field in RECORD_ENVELOPE_LIST_FIELDS),
)
METRIC_DEFINITIONS = {
    "rows_with_quality_status": (
        "Rows with a non-empty quality_status label; this does not certify quality."
    ),
    "rows_with_quality_evidence_fields_present": (
        "Rows containing at least one key from the validator's configured quality-detail fields; key presence only."
    ),
    "rows_with_nonempty_quality_evidence": (
        "Rows with a non-empty value in at least one configured quality-detail field; not a human-review or correctness measure."
    ),
    "rows_with_quality_metadata": (
        "Deprecated compatibility alias for rows_with_quality_evidence_fields_present."
    ),
    "rows_with_provenance_array": (
        "Rows with a non-empty provenance or sources array; config-specific source pointers are not included."
    ),
    "rows_with_provenance": (
        "Deprecated compatibility alias for rows_with_provenance_array."
    ),
    "rows_with_source_traceability": (
        "Rows with the minimum config-specific source identifier and locator: text-like/knowledge configs need one provenance item with an identifier and URL, snapshot hash, capture path, record_id, or file+line; ASR/draft configs need an upstream source, valid audio SHA-256, and a positive source-row count; source_catalog needs a source_ref_id and a locator (including an explicit URL or item reference in attribution); record_index needs source_ref_ids_json; record_sources needs both join identifiers. This does not establish reuse rights or correctness."
    ),
    "rows_without_source_traceability": (
        "Rows that do not meet the config-specific minimum source-locator rule. Reference-table rows are counted separately from content rows."
    ),
    "rights_status_counts": (
        "Per-config counts of the first recorded value among redistribution_status, rights_status, or record_rights_status; values are counted as-is, not interpreted as legal clearance."
    ),
    "reuse_scope_counts": (
        "Per-config counts of non-empty recorded reuse_scope strings; the validator does not infer scope from a source URL or license label."
    ),
    "license_label_counts": (
        "Per-config counts of non-empty license_labels entries; recorded labels are not independently verified by this metric."
    ),
    "rows_with_public_rights_basis": (
        "Rows with a non-empty public_rights_basis field; presence alone does not validate scope or evidence."
    ),
    "rows_with_noncommercial_rights_basis": (
        "Rows with a non-empty noncommercial_rights_basis field; presence alone does not validate scope or evidence."
    ),
    "rows_with_factual_publication_basis": (
        "Rows with a non-empty factual_publication_basis field; this is not a training or commercial-use license."
    ),
}


@dataclass
class _ValidationContext:
    """Package-wide inputs and accumulators shared by every config."""

    package: Path
    manifest: dict
    schema_version: object
    overlap_audit_manifest: dict
    direct_eval_record_ids: set = field(default_factory=set)
    aggregate_eval_record_ids: set = field(default_factory=set)
    errors: list = field(default_factory=list)
    split_ids: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    instruction_prompts: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(set)))
    source_ids: Counter = field(default_factory=Counter)
    file_hashes: list = field(default_factory=list)


@dataclass
class _ConfigTally:
    """Counters for one config/split."""

    stats: Counter = field(default_factory=Counter)
    seen: set = field(default_factory=set)
    scripts: Counter = field(default_factory=Counter)
    rights_statuses: Counter = field(default_factory=Counter)
    reuse_scopes: Counter = field(default_factory=Counter)
    license_labels: Counter = field(default_factory=Counter)


def _check_upstream_split_audit(ctx):
    if not ctx.overlap_audit_manifest:
        return
    try:
        ctx.direct_eval_record_ids, ctx.aggregate_eval_record_ids = upstream_split_overlap_ids()
    except (FileNotFoundError, ValueError, KeyError, json.JSONDecodeError) as exc:
        ctx.errors.append(f'upstream_split_audit_unavailable:{exc}')
    audit_json_path = ctx.package / UPSTREAM_AUDIT_JSON
    audit_md_path = ctx.package / UPSTREAM_AUDIT_MD
    if not audit_json_path.is_file():
        ctx.errors.append(f'missing_file:{UPSTREAM_AUDIT_JSON}')
    elif sha256(audit_json_path) != ctx.overlap_audit_manifest.get('sha256'):
        ctx.errors.append('upstream_split_audit_hash_mismatch')
    if not audit_md_path.is_file():
        ctx.errors.append(f'missing_file:{UPSTREAM_AUDIT_MD}')


def _check_record_envelope(stats, row):
    for field_name in RECORD_ENVELOPE_STRING_FIELDS:
        if not isinstance(row.get(field_name), str) or not row[field_name].strip():
            stats[f'record_envelope_missing_{field_name}'] += 1
    for field_name in RECORD_ENVELOPE_LIST_FIELDS:
        value = row.get(field_name)
        if not isinstance(value, list) or any(
            not isinstance(item, str) for item in value
        ):
            stats[f'record_envelope_invalid_{field_name}'] += 1


def _tally_identity_and_hashes(ctx, tally, config, split, row):
    stats = tally.stats
    rid = identity(config, row)
    if not rid:
        stats["missing_identity"] += 1
    elif rid in tally.seen:
        stats["duplicate_identity"] += 1
    else:
        tally.seen.add(rid)
        ctx.split_ids[config][split].add(rid)
    if config == 'text' and row.get('id') != hashlib.sha256(
        str(row.get('text') or '').encode('utf-8')
    ).hexdigest():
        stats['text_id_hash_mismatch'] += 1
    if config == 'catalog' and row.get('id') != row.get('text_sha256'):
        stats['catalog_id_hash_mismatch'] += 1
    text = row.get("text") if "text" in row else row.get("transcript")
    if text is not None:
        stats["empty_content"] += int(not str(text).strip())
        tally.scripts[script_profile(text)] += 1


def _tally_rights(tally, row):
    stats = tally.stats
    rights_status = (
        row.get('redistribution_status')
        or row.get('rights_status')
        or row.get('record_rights_status')
    )
    tally.rights_statuses[str(rights_status or 'missing')] += 1
    stats['rows_with_rights_status'] += int(bool(rights_status))
    reuse_scope = row.get('reuse_scope')
    if isinstance(reuse_scope, str) and reuse_scope.strip():
        tally.reuse_scopes[reuse_scope] += 1
        stats['rows_with_reuse_scope'] += 1
    for label in row.get('license_labels') or []:
        if isinstance(label, str) and label.strip():
            tally.license_labels[label] += 1
    stats['rows_with_license_label'] += int(
        bool(row.get('license_labels'))
    )
    for basis_field in (
        'public_rights_basis', 'noncommercial_rights_basis',
        'factual_publication_basis',
    ):
        stats[f'rows_with_{basis_field}'] += int(
            bool(row.get(basis_field))
        )


def _tally_provenance_and_quality(stats, config, row, provenance):
    has_provenance_array = bool(provenance)
    stats["rows_with_provenance"] += int(has_provenance_array)
    stats["rows_with_provenance_array"] += int(has_provenance_array)
    traceable = has_source_traceability(config, row)
    stats['rows_with_source_traceability'] += int(traceable)
    stats['rows_without_source_traceability'] += int(not traceable)
    has_quality_detail_field = any(
        field_name in row for field_name in QUALITY_DETAIL_FIELDS
    )
    has_quality_evidence = any(
        has_nonempty_value(row.get(field_name))
        for field_name in QUALITY_DETAIL_FIELDS
    )
    stats["rows_with_quality_status"] += int(
        bool(str(row.get('quality_status') or '').strip())
    )
    stats["rows_with_quality_evidence_fields_present"] += int(
        has_quality_detail_field
    )
    stats["rows_with_nonempty_quality_evidence"] += int(
        has_quality_evidence
    )
    # Keep the historical key stable for existing report readers.
    stats["rows_with_quality_metadata"] += int(
        has_quality_detail_field
    )


def _tally_knowledge_row(stats, manifest, config, row, provenance):
    if not provenance or any(
        not (item.get('source_id') or item.get('source_url'))
        for item in provenance
    ):
        stats['knowledge_missing_source_provenance'] += 1
    if not provenance or any(
        not (
            item.get('source_url')
            or item.get('source_snapshot_sha256')
            or item.get('source_capture_path')
        )
        for item in provenance
    ):
        stats['knowledge_untraceable_source_provenance'] += 1
    metadata = row.get('quality_metadata')
    if not isinstance(metadata, dict) or not metadata.get('review_status'):
        stats['knowledge_missing_quality_metadata'] += 1
    if not row.get('rights_status'):
        stats['knowledge_missing_rights_status'] += 1
    if manifest.get('profile') == 'public' and not is_public_factual_metadata_row(row, config):
        rights_basis = row.get('public_rights_basis') or []
        if not rights_basis or not all(
            is_publishable_provenance(item)
            and item.get('attribution')
            and (item.get('source_url') or item.get('source_snapshot_sha256'))
            for item in rights_basis
        ):
            stats['knowledge_missing_public_rights'] += 1


def _tally_text_row(stats, row):
    source_languages = set(row.get('source_languages') or [])
    if row.get('language') == 'gbm' and source_languages & {'eng', 'hin', 'mul'}:
        stats['unsupported_garhwali_label'] += 1
    if row.get('recommended_for_training') is not recommended_text_training_row(row):
        stats['invalid_training_recommendation'] += 1
    if any(
        field_name not in row for field_name in (
            'language_buckets', 'quality_tiers',
            'recommended_for_training',
        )
    ):
        stats['missing_admission_metadata'] += 1


def _tally_split_evidence(ctx, stats, split, row):
    expected_status, expected_source_ids = (
        source_split_overlap_evidence(
            row, ctx.direct_eval_record_ids,
            ctx.aggregate_eval_record_ids,
        )
    )
    if row.get('source_split_overlap_status') != expected_status:
        stats['source_split_evidence_mismatch'] += 1
    if row.get('source_split_overlap_source_ids') != expected_source_ids:
        stats['source_split_evidence_mismatch'] += 1
    has_overlap = expected_status != 'no_upstream_eval_match_detected'
    if split == 'train' and has_overlap:
        stats['upstream_eval_overlap_left_in_train'] += 1
    if split == 'source_overlap' and not has_overlap:
        stats['source_overlap_split_without_evidence'] += 1
    if split == 'source_overlap' and has_overlap:
        stats['source_overlap_rows'] += 1


def _tally_row(ctx, tally, config, split, row):
    stats = tally.stats
    stats["records"] += 1
    if ctx.schema_version == RECORD_SCHEMA_VERSION:
        _check_record_envelope(stats, row)
    _tally_identity_and_hashes(ctx, tally, config, split, row)
    _tally_rights(tally, row)
    provenance = row.get("provenance") or row.get("sources") or []
    _tally_provenance_and_quality(stats, config, row, provenance)
    if config in KNOWLEDGE_CONFIGS:
        _tally_knowledge_row(stats, ctx.manifest, config, row, provenance)
    for item in provenance:
        source = item.get("source_id")
        if source:
            ctx.source_ids[source] += 1
    if config == 'text':
        _tally_text_row(stats, row)
    if ctx.overlap_audit_manifest and config in TEXT_LIKE_CONFIGS:
        _tally_split_evidence(ctx, stats, split, row)
    elif config == 'instructions':
        prompt = ' '.join(
            str(row.get('instruction') or '').casefold().split()
        )
        ctx.instruction_prompts[config][split].add(prompt)
        if not row.get('acceptable_responses'):
            stats['missing_acceptable_responses'] += 1


def _validate_config(ctx, key, expected):
    config, split = key.split("/", 1)
    tally = _ConfigTally()
    declared_hashes = expected.get('file_sha256') or {}
    if set(declared_hashes) != set(expected.get('files') or []):
        ctx.errors.append(f'file_hash_manifest_mismatch:{key}')
    for filename in expected["files"]:
        path = ctx.package / "data" / config / filename
        if not path.exists():
            ctx.errors.append(f"missing_file:{config}/{filename}")
            continue
        digest = sha256(path)
        ctx.file_hashes.append({"path": str(path.relative_to(ctx.package)), "sha256": digest})
        if declared_hashes.get(filename) != digest:
            ctx.errors.append(f'file_hash_mismatch:{key}:{filename}')
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                try:
                    row = json.loads(line)
                except Exception as exc:  # noqa: BLE001 - any parse failure is reported per line
                    ctx.errors.append(f"invalid_json:{config}/{filename}:{line_number}:{exc}")
                    continue
                _tally_row(ctx, tally, config, split, row)
    stats = tally.stats
    if stats["records"] != expected["records"]:
        ctx.errors.append(f"record_count:{key}:{stats['records']}!={expected['records']}")
    if stats["missing_identity"]:
        ctx.errors.append(f"missing_identity:{key}:{stats['missing_identity']}")
    if stats['duplicate_identity']:
        ctx.errors.append(f"duplicate_identity:{key}:{stats['duplicate_identity']}")
    for field_name in ('text_id_hash_mismatch', 'catalog_id_hash_mismatch'):
        if stats[field_name]:
            ctx.errors.append(f'{field_name}:{key}:{stats[field_name]}')
    for field_name in PER_CONFIG_ERROR_FIELDS:
        if stats[field_name]:
            ctx.errors.append(f'{field_name}:{key}:{stats[field_name]}')
    return stats, {
        **dict(stats),
        "scripts": dict(sorted(tally.scripts.items())),
        "rights_status_counts": dict(sorted(tally.rights_statuses.items())),
        "reuse_scope_counts": dict(sorted(tally.reuse_scopes.items())),
        "license_label_counts": dict(sorted(tally.license_labels.items())),
    }


def _cross_split_leakage(ctx):
    leakage = {}
    for config, splits in ctx.split_ids.items():
        names = sorted(splits)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                count = len(splits[left] & splits[right])
                leakage[f"{config}:{left}:{right}"] = count
                if count:
                    ctx.errors.append(f"cross_split_identity:{config}:{left}:{right}:{count}")
    for config, splits in ctx.instruction_prompts.items():
        names = sorted(splits)
        for index, left in enumerate(names):
            for right in names[index + 1:]:
                count = len(splits[left] & splits[right])
                leakage[f'{config}_prompt:{left}:{right}'] = count
                if count:
                    ctx.errors.append(
                        f'cross_split_instruction_prompt:{left}:{right}:{count}'
                    )
    return leakage


def _check_package_files(ctx):
    package, manifest = ctx.package, ctx.manifest
    expected_files = {
        'README.md', 'manifest.json', 'LICENSE_POLICY.md',
        'ATTRIBUTION.md', 'REMOVAL_POLICY.md',
        'research/text-rights-resolution-2026-09-30.md',
    }
    if ctx.overlap_audit_manifest:
        expected_files.update({UPSTREAM_AUDIT_MD, UPSTREAM_AUDIT_JSON})
    if ctx.schema_version == RECORD_SCHEMA_VERSION:
        schema_docs = (
            'DEVELOPER_QUICKSTART.md', 'DATASET_SCHEMA.md',
            'search_garhwali_lexicon.py',
        )
        expected_files.update(schema_docs)
        for filename in schema_docs:
            if not (package / filename).is_file():
                ctx.errors.append(f'missing_file:{filename}')
    if manifest.get('reference_index'):
        expected_files.add('reference_index_manifest.json')
    if any(
        key.split('/', 1)[0] == 'paharili_gbm'
        for key in manifest['configs']
    ):
        paharili_license = 'licenses/PahariLI-Apache-2.0.txt'
        expected_files.add(paharili_license)
        if not (package / paharili_license).is_file():
            ctx.errors.append(f'missing_file:{paharili_license}')
    for key, config in manifest['configs'].items():
        group, _ = key.split('/', 1)
        expected_files.update(
            f'data/{group}/{filename}' for filename in config.get('files', [])
        )
    actual_files = {
        path.relative_to(package).as_posix()
        for path in package.rglob('*') if path.is_file() or path.is_symlink()
    }
    for path in sorted(actual_files - expected_files):
        if not (manifest.get('include_audio') and path.startswith('audio/')):
            ctx.errors.append(f'unexpected_file:{path}')
    for path in sorted(path for path in package.rglob('*') if path.is_symlink()):
        ctx.errors.append(f'symlink:{path.relative_to(package).as_posix()}')


def validate_package(package):
    """Validate a package directory and return the report dictionary."""
    manifest = json.loads((package / "manifest.json").read_text())
    ctx = _ValidationContext(
        package=package,
        manifest=manifest,
        schema_version=manifest.get('record_schema_version'),
        overlap_audit_manifest=manifest.get('upstream_split_overlap_audit') or {},
    )
    _check_upstream_split_audit(ctx)
    if ctx.schema_version is not None and ctx.schema_version != RECORD_SCHEMA_VERSION:
        ctx.errors.append(f'unsupported_record_schema_version:{ctx.schema_version}')
    configs = {}
    global_stats = Counter()
    for key, expected in sorted(manifest["configs"].items()):
        stats, configs[key] = _validate_config(ctx, key, expected)
        global_stats.update(stats)
    leakage = _cross_split_leakage(ctx)
    _check_package_files(ctx)
    release_suffix = str(manifest.get('release_id') or '').rsplit('-v', 1)
    release_version = release_suffix[-1] if len(release_suffix) == 2 else '0.1'
    return {
        "run_id": f"garhwali-hf-{manifest['profile']}-cloud-validation-v{release_version}",
        "release_id": manifest["release_id"],
        "status": "passed" if not ctx.errors else "failed",
        "manifest_profile": manifest["profile"],
        "record_schema_version": ctx.schema_version,
        "validation_contract_version": VALIDATION_CONTRACT_VERSION,
        "validator_sha256": sha256(Path(__file__).resolve()),
        "metric_definitions": METRIC_DEFINITIONS,
        "configs": configs,
        "totals": dict(global_stats),
        "cross_split_identity_overlap": leakage,
        "distinct_provenance_sources": len(ctx.source_ids),
        "top_provenance_sources": ctx.source_ids.most_common(50),
        "file_hashes": ctx.file_hashes,
        "errors": ctx.errors,
        "records_deleted_or_mutated": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate_package(args.package)
    output_path = (
        args.output if args.output.suffix == '.json' else args.output / 'report.json'
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
