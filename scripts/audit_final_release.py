#!/usr/bin/env python3
"""Audit the tracked release index against the upload-ready dataset package."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from build_huggingface_dataset import is_publishable_provenance
from validate_release_index import validate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'release/v0.1.0-manifest.json'
DEFAULT_DATASET = ROOT / 'data/huggingface/garhwali-language-lab'
DEFAULT_OUTPUT = ROOT / 'release/final-audit.json'
REQUIRED_CONFIGS = {
    'text/train', 'text/validation', 'text/test',
    'asr/train', 'asr/validation', 'asr/test',
    'sravaani_drafts/train', 'lexicon/train',
    'instructions/train', 'instructions/validation', 'instructions/test',
    'catalog/train',
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def overlap_error(label, split_values):
    errors = []
    names = ('train', 'validation', 'test')
    for position, left in enumerate(names):
        for right in names[position + 1:]:
            if split_values.get(left, set()) & split_values.get(right, set()):
                errors.append(f'{label} overlap across {left} and {right}')
    return errors


def audit(index, dataset_root):
    dataset_root = Path(dataset_root)
    errors = list(validate(index))
    warnings = []
    manifest_path = dataset_root / 'manifest.json'
    if not manifest_path.exists():
        return {'status': 'failed', 'errors': errors + ['Hugging Face manifest is missing'], 'warnings': warnings}

    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('release_id') != index.get('release_id'):
        errors.append('Hugging Face release ID does not match release index')
    missing_configs = sorted(REQUIRED_CONFIGS - set(manifest.get('configs', {})))
    if missing_configs:
        errors.append(f'missing configs: {", ".join(missing_configs)}')

    actual_counts = {}
    text_ids = {}
    asr_hashes = {}
    asr_speakers = {}
    provenance_missing = 0
    rights_failures = 0
    language_scope_failures = 0
    asr_metadata_missing = 0
    expected_audio = set()
    draft_hashes = set()
    draft_rows = 0
    empty_drafts = 0
    draft_quality_missing = 0
    supervised_drafts = 0
    catalog_ids = set()
    catalog_redacted = 0
    catalog_missing_evidence = 0

    for key, config in sorted(manifest.get('configs', {}).items()):
        group, split = key.split('/', 1)
        rows = []
        for filename in config.get('files', []):
            path = dataset_root / 'data' / group / filename
            if not path.exists():
                errors.append(f'{key} shard is missing: {filename}')
                continue
            rows.extend(read_jsonl(path))
        actual_counts[key] = len(rows)
        if len(rows) != config.get('records'):
            errors.append(f'{key} has {len(rows)} rows, manifest declares {config.get("records")}')
        if len(config.get('files', [])) != config.get('shards'):
            errors.append(f'{key} shard count does not match its manifest')

        if group == 'text':
            text_ids[split] = {row.get('id') for row in rows}
            missing = sum(not row.get('provenance') for row in rows)
            rights = sum(
                bool(row.get('provenance')) and
                not all(is_publishable_provenance(item) for item in row['provenance'])
                for row in rows
            )
            language_scope = sum(
                row.get('language') != 'gbm' or any(
                    item.get('iso_639_3') != 'gbm'
                    for item in row.get('provenance') or []
                )
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows without provenance')
            if rights:
                errors.append(f'{key} has {rights} rows without compatible public rights')
            if language_scope:
                errors.append(f'{key} has {language_scope} rows outside explicit Garhwali scope')
            provenance_missing += missing
            rights_failures += rights
            language_scope_failures += language_scope
        elif group == 'asr':
            expected_audio.update(row.get('audio') for row in rows if row.get('audio'))
            asr_hashes[split] = {row.get('audio_sha256') for row in rows}
            asr_speakers[split] = {
                row.get('speaker_id') for row in rows
                if row.get('speaker_id') not in (None, '', 'NA')
            }
            missing = sum(
                not row.get('source') or not row.get('license') or not row.get('transcript')
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows missing transcript/source/license metadata')
            asr_metadata_missing += missing
        elif group in ('lexicon', 'instructions'):
            missing = sum(not row.get('provenance') for row in rows)
            rights = sum(
                bool(row.get('provenance')) and
                not all(is_publishable_provenance(item) for item in row['provenance'])
                for row in rows
            )
            if missing:
                errors.append(f'{key} has {missing} rows without provenance')
            if rights:
                errors.append(f'{key} has {rights} rows without compatible public rights')
            provenance_missing += missing
            rights_failures += rights
        elif group == 'sravaani_drafts':
            expected_audio.update(row.get('audio') for row in rows if row.get('audio'))
            draft_rows += len(rows)
            for row in rows:
                digest = row.get('audio_sha256')
                if digest in draft_hashes:
                    errors.append(f'sravaani_drafts contains duplicate audio hash {digest}')
                draft_hashes.add(digest)
                empty_drafts += not bool(row.get('transcript'))
                draft_quality_missing += not bool(row.get('machine_transcript_quality'))
                supervised_drafts += row.get('training_eligible') is True
        elif group == 'catalog':
            for row in rows:
                identity = row.get('id')
                if not identity or identity in catalog_ids:
                    errors.append('catalog contains a missing or duplicate stable ID')
                catalog_ids.add(identity)
                if row.get('text') is None:
                    catalog_redacted += 1
                    if not row.get('redaction_reason') or not row.get('sources'):
                        catalog_missing_evidence += 1

    errors.extend(overlap_error('text IDs', text_ids))
    errors.extend(overlap_error('ASR audio hashes', asr_hashes))
    errors.extend(overlap_error('ASR speakers', asr_speakers))
    if draft_quality_missing:
        errors.append(f'{draft_quality_missing} SraVaani drafts lack quality metadata')
    if supervised_drafts:
        errors.append(f'{supervised_drafts} machine drafts are marked supervised-training eligible')
    expected_catalog_records = index.get('text', {}).get(
        'unique_parent_documents', index.get('text', {}).get('total')
    )
    if len(catalog_ids) != expected_catalog_records:
        errors.append('catalog does not account for every exact-unique text record')
    if catalog_missing_evidence:
        errors.append(f'{catalog_missing_evidence} redacted catalog rows lack public evidence')

    asr_total = sum(actual_counts.get(f'asr/{split}', 0) for split in ('train', 'validation', 'test'))
    if asr_total != index.get('speech', {}).get('strict_comparison_rows'):
        errors.append('ASR export total does not match release strict comparison rows')
    comparison = index.get('speech_baseline_comparison', {})
    checks = {
        'draft_queue_records': manifest.get('draft_queue_records'),
        'draft_records': manifest.get('draft_records'),
        'draft_unique_audio': manifest.get('draft_unique_audio'),
        'draft_inherited_duplicate_rows': manifest.get('draft_inherited_duplicate_rows'),
    }
    expected = {
        'draft_records': comparison.get('sravaani_draft_rows'),
        'draft_unique_audio': comparison.get('sravaani_draft_unique_audio'),
        'draft_inherited_duplicate_rows': comparison.get('sravaani_draft_inherited_duplicate_rows'),
    }
    for name, value in expected.items():
        if checks[name] != value:
            errors.append(f'{name} does not match release index')
    if draft_rows != manifest.get('draft_unique_audio'):
        errors.append('exported draft rows do not match unique-audio count')
    if not manifest.get('drafts_complete'):
        errors.append('SraVaani draft coverage is incomplete')
    audio_files = set()
    if (dataset_root / 'audio').exists():
        audio_files = {
            path.relative_to(dataset_root).as_posix()
            for path in (dataset_root / 'audio').rglob('*.wav')
        }
    missing_audio = expected_audio - audio_files
    unexpected_audio = audio_files - expected_audio
    if manifest.get('include_audio'):
        if missing_audio:
            errors.append(f'{len(missing_audio)} referenced audio files are missing')
        if unexpected_audio:
            errors.append(f'{len(unexpected_audio)} unexpected audio files are present')
        if manifest.get('linked_audio_files') != len(expected_audio):
            errors.append('linked audio count does not match referenced unique audio')
    else:
        warnings.append('audio_not_included')
    if manifest.get('draft_inherited_duplicate_rows'):
        warnings.append('inherited_source_audio_duplicates_collapsed')
    if empty_drafts:
        warnings.append('empty_machine_drafts_retained_with_quality_flags')

    return {
        'audit_id': 'garhwali-final-release-audit-v0.1',
        'generated': date.today().isoformat(),
        'release_id': index.get('release_id'),
        'status': 'passed' if not errors else 'failed',
        'errors': errors,
        'warnings': warnings,
        'configs': actual_counts,
        'exported_rows': sum(actual_counts.values()),
        'audio': {
            'included': bool(manifest.get('include_audio')),
            'referenced_unique_files': len(expected_audio),
            'present_files': len(audio_files),
            'missing_files': len(missing_audio),
            'unexpected_files': len(unexpected_audio),
        },
        'provenance': {
            'missing_rows': provenance_missing,
            'public_rights_failures': rights_failures,
            'text_language_scope_failures': language_scope_failures,
            'asr_missing_transcript_source_or_license': asr_metadata_missing,
        },
        'leakage': {
            'text_id_cross_split': 0 if not overlap_error('text', text_ids) else 1,
            'asr_audio_cross_split': 0 if not overlap_error('asr', asr_hashes) else 1,
            'asr_speaker_cross_split': 0 if not overlap_error('speaker', asr_speakers) else 1,
        },
        'drafts': {
            **checks,
            'exported_unique_audio': len(draft_hashes),
            'empty_transcripts': empty_drafts,
            'quality_metadata_missing': draft_quality_missing,
            'supervised_training_eligible': supervised_drafts,
            'complete': bool(manifest.get('drafts_complete')),
        },
        'catalog': {
            'records': len(catalog_ids),
            'redacted_text_records': catalog_redacted,
            'missing_evidence': catalog_missing_evidence,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX)
    parser.add_argument('--dataset', type=Path, default=DEFAULT_DATASET)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    index = json.loads(args.index.read_text(encoding='utf-8'))
    report = audit(index, args.dataset)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
