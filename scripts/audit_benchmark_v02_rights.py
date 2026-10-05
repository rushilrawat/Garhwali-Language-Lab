#!/usr/bin/env python3
"""Audit rights, provenance coverage, and upload gates in the local v0.2 draft."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DRAFT = ROOT / 'data/processed/evaluation/garhwali_bench/v0.2-draft'


def _read_jsonl(path: Path):
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{line_number}: expected a JSON object')
            yield row


def _basis_status(basis: list[dict]) -> str:
    statuses = [item.get('rights_status', 'missing') for item in basis]
    if not statuses:
        return 'missing_basis'
    if all(status == 'rights_assessed_compatible' for status in statuses):
        return 'all_components_compatible'
    if all(status == 'not_recorded' for status in statuses):
        return 'all_components_not_recorded'
    return 'mixed_or_other'


def audit(draft_dir: Path = DEFAULT_DRAFT) -> dict:
    draft_dir = Path(draft_dir)
    manifest_path = draft_dir / 'manifest.json'
    if not manifest_path.is_file():
        raise FileNotFoundError(f'benchmark draft manifest not found: {manifest_path}')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))

    rows_by_view = Counter()
    public_upload_values = Counter()
    release_clearance_values = Counter()
    external_licenses = Counter()
    asr_licenses = Counter()
    asr_privacy_flags = Counter()
    external_rights_statuses = defaultdict(Counter)
    recommended_statuses = Counter()
    recommended_sources = Counter()
    recommended_basis_components = Counter()
    recommended_rows_by_source = Counter()
    recommended_evidence_coverage = defaultdict(Counter)
    external_provenance_coverage = defaultdict(Counter)
    external_training_eligibility = defaultdict(Counter)
    internal_component_statuses = Counter()
    total_rows = 0

    for path in sorted(draft_dir.glob('*.jsonl')):
        for row in _read_jsonl(path):
            total_rows += 1
            view = row.get('view') or path.stem.replace('__', '/')
            rows_by_view[view] += 1
            rights = row.get('rights') or {}
            privacy = row.get('privacy') or {}
            public_upload_values[str(privacy.get('public_upload_allowed', 'missing'))] += 1
            release_clearance_values[str(rights.get('public_release_cleared', 'missing'))] += 1

            if view.startswith('external/'):
                external_licenses[rights.get('declared_license_id', 'missing')] += 1
                for field in ('rights_status', 'component_rights_status', 'redistribution_status'):
                    external_rights_statuses[view][
                        f'{field}={rights.get(field, "missing")}'
                    ] += 1
                provenance = row.get('provenance') or {}
                snapshot = provenance.get('provenance') or {}
                source_example = (row.get('payload') or {}).get('source_example') or {}
                provenance_fields = {
                    'attribution_present': provenance.get('attribution'),
                    'source_id_present': provenance.get('source_id'),
                    'source_snapshot_url_present': snapshot.get('url'),
                    'source_snapshot_sha256_present': snapshot.get('sha256'),
                    'source_snapshot_retrieved_at_present': snapshot.get('retrieved_at'),
                    'source_example_present': source_example,
                    'source_example_source_url_present': (
                        source_example.get('source_url') or source_example.get('url')
                    ),
                    'source_example_target_url_present': source_example.get('target_url'),
                }
                for field, value in provenance_fields.items():
                    external_provenance_coverage[view][field] += bool(value)
                external_training_eligibility[view][
                    str((row.get('usage') or {}).get('training_eligibility_as_recorded', 'missing'))
                ] += 1
            elif view == 'internal/asr':
                asr_licenses[rights.get('license_declaration', 'missing')] += 1
                for flag in ('contains_local_audio_locator', 'contains_local_identifiers'):
                    asr_privacy_flags[f'{flag}={privacy.get(flag, "missing")}'] += 1
            elif view.startswith('text_recommended/'):
                basis = rights.get('public_rights_basis_as_recorded') or []
                recommended_statuses[_basis_status(basis)] += 1
                source_ids = sorted({item.get('source_id', 'missing') for item in basis})
                recommended_sources['+'.join(source_ids) if source_ids else 'missing_basis'] += 1
                for source_id in source_ids:
                    recommended_rows_by_source[source_id] += 1
                for item in basis:
                    source_id = item.get('source_id', 'missing')
                    recommended_basis_components[source_id] += 1
                    for field in (
                        'attribution', 'author', 'license_url', 'source_url',
                        'rights_evidence', 'source_snapshot_sha256', 'source_pdf_sha256',
                    ):
                        recommended_evidence_coverage[source_id][
                            f'{field}_present'
                        ] += bool(item.get(field))
            elif view == 'internal/text':
                for item in rights.get('component_rights') or []:
                    internal_component_statuses[item.get('rights_status', 'missing')] += 1

    if total_rows != manifest.get('total_records'):
        raise ValueError(
            f'row count {total_rows} does not match manifest total_records '
            f'{manifest.get("total_records")}'
        )

    return {
        'manifest_public_upload_allowed': manifest.get('public_upload_allowed'),
        'view_rows': total_rows,
        'rows_by_view': dict(sorted(rows_by_view.items())),
        'public_upload_allowed_by_value': dict(sorted(public_upload_values.items())),
        'public_release_cleared_by_value': dict(sorted(release_clearance_values.items())),
        'external_declared_license_rows': dict(sorted(external_licenses.items())),
        'external_rights_statuses_by_view': {
            view: dict(sorted(counts.items()))
            for view, counts in sorted(external_rights_statuses.items())
        },
        'asr_license_declaration_rows': dict(sorted(asr_licenses.items())),
        'asr_local_field_flags': dict(sorted(asr_privacy_flags.items())),
        'recommended_text_rights_rows': dict(sorted(recommended_statuses.items())),
        'recommended_text_rows_by_source_family': dict(sorted(recommended_sources.items())),
        'recommended_text_rows_with_basis_by_source': dict(
            sorted(recommended_rows_by_source.items())
        ),
        'recommended_text_basis_components_by_source': dict(
            sorted(recommended_basis_components.items())
        ),
        'recommended_text_rights_evidence_coverage_by_source': {
            source_id: dict(sorted(counts.items()))
            for source_id, counts in sorted(recommended_evidence_coverage.items())
        },
        'external_provenance_coverage_by_view': {
            view: dict(sorted(counts.items()))
            for view, counts in sorted(external_provenance_coverage.items())
        },
        'external_training_eligibility_by_view': {
            view: dict(sorted(counts.items()))
            for view, counts in sorted(external_training_eligibility.items())
        },
        'internal_text_component_rights_statuses': dict(sorted(internal_component_statuses.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--draft', type=Path, default=DEFAULT_DRAFT)
    args = parser.parse_args()
    print(json.dumps(audit(args.draft), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
