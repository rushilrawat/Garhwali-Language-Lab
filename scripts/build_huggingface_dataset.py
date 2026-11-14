#!/usr/bin/env python3
"""Build deterministic Hugging Face upload folders from prepared Garhwali views."""

from __future__ import annotations

import argparse
import errno
import json
import os
import shutil
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from hf_card import dataset_card, dataset_info_for_release
from hf_rights import asr_split_directory, is_public_garhwali_text_row, is_public_text_row, profile_includes_all_data
from hf_rows import (
    KNOWLEDGE_CONFIGS,
    PAHARILI_GBM_ROWS_PATH,
    PAHARILI_LICENSE_PATH,
    UPSTREAM_SPLIT_OVERLAP_PATH,
    attach_audio_grounded_review,
    attach_recovery_adjudication,
    attach_recovery_third_checkpoint,
    audio_row,
    build_catalog_text_expansion,
    build_catalog_text_resources,
    build_paharili_gbm_rows,
    catalog_row,
    comparable_text_rows,
    content_audio_path,
    deduplicate_audio_rows,
    drafts_cover_queue,
    knowledge_row,
    lexicon_row,
    public_factual_metadata_row,
    refresh_acceptable_responses,
    route_upstream_split_overlap,
    source_catalog_for_family,
    text_row,
    upstream_split_overlap_ids,
    with_public_rights_basis,
)
from record_schema import normalize_record

from garhwali_lab.hashing import sha256_file
from garhwali_lab.io import iter_jsonl as read_jsonl
from garhwali_lab.version import corpus_release_version, ensure_unpublished_corpus_version

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab'
ALL_DATA_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-all-data'
# Preserve these earlier local output paths in the overwrite guard. Their names
# are historical storage paths, not semantic project release versions.
LEGACY_PUBLIC_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-v2.0.0-staging'
LEGACY_ALL_DATA_OUTPUT = ROOT / 'data/huggingface/garhwali-language-lab-all-data-v2.0.0-local'
RELEASE_VERSION = corpus_release_version()
RELEASE_PUBLIC_OUTPUT = ROOT / f'data/huggingface/garhwali-language-lab-v{RELEASE_VERSION}-staging'
RELEASE_ALL_DATA_OUTPUT = ROOT / f'data/huggingface/garhwali-language-lab-all-data-v{RELEASE_VERSION}-local'
MANAGED_OUTPUTS = {
    DEFAULT_OUTPUT.resolve(), ALL_DATA_OUTPUT.resolve(),
    LEGACY_PUBLIC_OUTPUT.resolve(), LEGACY_ALL_DATA_OUTPUT.resolve(),
    RELEASE_PUBLIC_OUTPUT.resolve(), RELEASE_ALL_DATA_OUTPUT.resolve(),
}
RELEASE_ID = f"garhwali-language-lab-v{RELEASE_VERSION}"


def prepare_package_output(output):
    output = Path(output)
    resolved = output.resolve()
    if output.exists() and resolved not in MANAGED_OUTPUTS:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    return output


def write_shards(rows, directory, split, shard_rows=10_000):
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.glob(f'{split}-*.jsonl'):
        old.unlink()
    count = 0
    shard = -1
    handle = None
    paths = []
    try:
        family = directory.name
        for row in rows:
            if count % shard_rows == 0:
                if handle:
                    handle.close()
                shard += 1
                path = directory / f'{split}-{shard:05d}.jsonl'
                paths.append(path)
                handle = path.open('w', encoding='utf-8')
            row = normalize_record(row, family=family)
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
            count += 1
    finally:
        if handle:
            handle.close()
    files = [str(path.name) for path in paths]
    return {
        'records': count,
        'shards': len(paths),
        'files': files,
        'file_sha256': {path.name: sha256_file(path) for path in paths},
    }


def link_audio(rows, output):
    linked = 0
    seen = set()
    for row in rows:
        digest = row['audio_sha256']
        if digest in seen:
            continue
        seen.add(digest)
        source = (ROOT / row['local_audio_path']).resolve()
        audio_root = (ROOT / 'data/vaani/audio').resolve()
        if source.is_symlink() or not source.is_file() or not source.is_relative_to(audio_root):
            raise ValueError(f'unsafe audio source path: {row["local_audio_path"]}')
        if sha256_file(source) != digest:
            raise ValueError(f'audio SHA-256 mismatch: {row["local_audio_path"]}')
        target = output / content_audio_path(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            try:
                os.link(source, target)
            except OSError as error:
                if error.errno != errno.EXDEV:
                    raise
                shutil.copy2(source, target)
            linked += 1
    return {'new': linked, 'total': len(seen)}


def remove_packaged_audio(output):
    directory = Path(output) / 'audio'
    count = sum(1 for _ in directory.rglob('*.wav')) if directory.exists() else 0
    if directory.exists():
        shutil.rmtree(directory)
    return count


def source_expansion_metrics():
    """Read the pinned-source intake manifests for the current major release."""
    jambu_path = ROOT / 'corpus/jambu_garhwali_manifest.json'
    library_path = ROOT / 'corpus/garhwali_language_library_manifest.json'
    jambu = json.loads(jambu_path.read_text(encoding='utf-8'))
    library = json.loads(library_path.read_text(encoding='utf-8'))
    return {
        'jambu': {
            'source_records': jambu.get('records', 0),
            'unique_forms': jambu.get('unique_forms', 0),
            'cross_source_overlap': jambu.get('exact_overlap_with_existing_unique_forms', 0),
            'new_vs_other_sources': jambu.get('exact_new_unique_forms', 0),
            'already_in_current_corpus': jambu.get('already_in_current_corpus_unique_forms', 0),
        },
        'language_library': {
            'source_records': library.get('source_records', 0),
            'unique_strings': library.get('unique_surface_forms', 0),
            'cross_source_overlap': library.get('exact_overlap_with_existing_unique_forms', 0),
            'new_vs_current_corpus': library.get('exact_new_unique_forms', 0),
            'records_by_type': library.get('records_by_type', {}),
        },
    }


@dataclass
class _PackageBuild:
    """Inputs and the growing manifest for one package build."""

    output: Path
    profile: str
    include_audio: bool
    shard_rows: int
    direct_eval_record_ids: set
    aggregate_eval_record_ids: set
    report: dict

    def write(self, config, rows, directory, split):
        self.report['configs'][f'{config}/{split}'] = write_shards(
            rows, self.output / directory, split, self.shard_rows
        )

    def route(self, rows):
        return [
            route_upstream_split_overlap(
                row, self.direct_eval_record_ids, self.aggregate_eval_record_ids
            )
            for row in rows
        ]


SRAVAANI_DRAFT_PREFERENCE = (
    'machine_drafts_sravaani_verified.jsonl',
    'machine_drafts_sravaani_confidence_aware.jsonl',
    'machine_drafts_sravaani_quality.jsonl',
    'machine_drafts_sravaani.jsonl',
)
TRANSCRIPTS_DIR = ROOT / 'data/processed/model_ready/transcripts'
LEXICON_PATH = ROOT / 'data/processed/model_ready/language_resources/pronunciation/lexicon.jsonl'
INSTRUCTIONS_DIR = ROOT / 'data/processed/model_ready/instructions_v0.2'


def _new_package_build(output, profile, include_audio, shard_rows):
    direct_eval_record_ids, aggregate_eval_record_ids = upstream_split_overlap_ids()
    overlap_audit = json.loads(
        UPSTREAM_SPLIT_OVERLAP_PATH.read_text(encoding='utf-8')
    )
    report = {
        'release_id': RELEASE_ID,
        'record_schema_version': '1.0.0',
        'profile': profile,
        'include_audio': include_audio,
        'upstream_split_overlap_audit': {
            'schema_version': overlap_audit['schema_version'],
            'sha256': sha256_file(UPSTREAM_SPLIT_OVERLAP_PATH),
            'direct_upstream_eval_record_ids': len(direct_eval_record_ids),
            'community_transcript_overlap_record_ids': len(aggregate_eval_record_ids),
        },
        'configs': {},
        'structured_knowledge_excluded_for_rights': {},
        'structured_knowledge_metadata_only': {},
    }
    if RELEASE_ID.endswith('v0.2.1'):
        report['source_expansion'] = source_expansion_metrics()
    return _PackageBuild(
        output, profile, include_audio, shard_rows,
        direct_eval_record_ids, aggregate_eval_record_ids, report,
    )


def _first_existing_draft_file():
    return next(
        path for path in (TRANSCRIPTS_DIR / name for name in SRAVAANI_DRAFT_PREFERENCE)
        if path.exists()
    )


def _write_text_splits(pkg, parent_quality):
    text_dir = ROOT / 'data/processed/model_ready/splits/text'
    for split in ('train', 'validation', 'test'):
        rows = read_jsonl(text_dir / f'{split}.jsonl')
        exported_rows = [text_row(row, parent_quality) for row in rows]
        if pkg.profile == 'public':
            exported_rows = (
                exported
                for exported in exported_rows
                if exported['language'] == 'gbm'
                and is_public_garhwali_text_row(exported)
            )
        exported_rows = pkg.route(exported_rows)
        if split == 'train':
            train_rows = [row for row in exported_rows if row['split'] == 'train']
            overlap_rows = [
                row for row in exported_rows if row['split'] == 'source_overlap'
            ]
            pkg.report['text_source_overlap_records'] = len(overlap_rows)
            pkg.write('text', train_rows, 'data/text', 'train')
            if overlap_rows:
                pkg.write('text', overlap_rows, 'data/text', 'source_overlap')
        else:
            pkg.write('text', exported_rows, 'data/text', split)


def _existing_text_rows(pkg):
    """Collect text values already exported or present in other text-bearing configs."""
    existing_text_rows = []
    for path in sorted((pkg.output / 'data/text').glob('*.jsonl')):
        existing_text_rows.extend(read_jsonl(path))
    # Deduplicate across text-bearing configs, not only the main text split.
    asr_source_dir = (
        ROOT / 'data/processed/model_ready/splits' / asr_split_directory(pkg.profile)
    )
    for split in ('train', 'validation', 'test'):
        asr_rows = list(read_jsonl(asr_source_dir / f'{split}.jsonl'))
        existing_text_rows.extend(comparable_text_rows(asr_rows, 'asr_target_clean'))
    existing_text_rows.extend(comparable_text_rows(
        read_jsonl(_first_existing_draft_file()), 'machine_transcript'
    ))
    existing_text_rows.extend(comparable_text_rows(
        read_jsonl(LEXICON_PATH), 'form'
    ))
    for split in ('train', 'validation', 'test'):
        instruction_rows = list(read_jsonl(INSTRUCTIONS_DIR / f'{split}.jsonl'))
        existing_text_rows.extend(comparable_text_rows(instruction_rows, 'instruction'))
        existing_text_rows.extend(comparable_text_rows(instruction_rows, 'response'))
    return existing_text_rows


def _write_catalog(pkg, quality_catalog):
    report = pkg.report
    refinement_path = ROOT / 'data/processed/model_ready/text_quality_v2/priority_text.jsonl'
    refinements = {
        row['text_sha256']: row for row in read_jsonl(refinement_path)
    } if refinement_path.exists() else {}
    catalog_rows = [
        catalog_row(
            row,
            include_all_text=profile_includes_all_data(pkg.profile),
            refinement=refinements.get(row['text_sha256']),
        )
        for row in quality_catalog
    ]
    status_counts = Counter(row['redistribution_status'] for row in catalog_rows)
    report['catalog_refined_text_records'] = sum(
        'text_refinement' in row for row in catalog_rows
    )
    report['catalog_records'] = len(catalog_rows)
    report['catalog_redacted_text_records'] = sum(
        row['text'] is None for row in catalog_rows
    )
    report['catalog_rights_cleared_records'] = status_counts['rights_cleared']
    report['catalog_noncommercial_records'] = status_counts[
        'rights_cleared_noncommercial_sharealike'
    ]
    report['catalog_source_policy_records'] = status_counts['reproduced_under_source_policy']
    report['catalog_factual_word_records'] = status_counts['individual_word_fact']
    report['catalog_sharealike_records'] = sum(
        any(
            item.get('license_id') in {'CC-BY-SA-4.0', 'CC-BY-NC-SA-4.0'}
            for item in row.get('public_rights_basis', [])
            + row.get('noncommercial_rights_basis', [])
        )
        for row in catalog_rows
    )
    report['all_collected_text_values_included'] = (
        report['catalog_redacted_text_records'] == 0
    )
    if profile_includes_all_data(pkg.profile) and not report['all_collected_text_values_included']:
        raise RuntimeError('All-data profile omitted one or more collected text values')
    pkg.write('catalog', catalog_rows, 'data/catalog', 'train')
    return catalog_rows


def _benchmark_eval_rows():
    benchmark_eval_dir = (
        ROOT / 'data/processed/evaluation/garhwali_bench_parent_safe_v0.2_2026-09-28'
        / 'v0.2-frozen-candidate'
    )
    rows = []
    for split in ('validation', 'test'):
        path = benchmark_eval_dir / f'text_recommended__{split}.jsonl'
        if path.exists():
            rows.extend(read_jsonl(path))
    return rows


def _write_routed_catalog_view(pkg, config, rows, metrics, metrics_key):
    """Route a catalog-derived view by upstream overlap and write train/overlap splits."""
    rows = pkg.route(rows)
    overlap_rows = [row for row in rows if row['split'] == 'source_overlap']
    train_rows = [row for row in rows if row['split'] == 'train']
    metrics['source_split_overlap_records'] = len(overlap_rows)
    metrics['train_records'] = len(train_rows)
    pkg.report[metrics_key] = metrics
    pkg.write(config, train_rows, f'data/{config}', 'train')
    if overlap_rows:
        pkg.write(config, overlap_rows, f'data/{config}', 'source_overlap')
    return rows


def _write_catalog_views(pkg, catalog_rows, existing_text_rows):
    benchmark_eval_rows = _benchmark_eval_rows()
    expansion_rows, expansion_metrics = build_catalog_text_expansion(
        catalog_rows, existing_text_rows, benchmark_eval_rows
    )
    expansion_rows = _write_routed_catalog_view(
        pkg, 'text_expansion', expansion_rows, expansion_metrics, 'text_expansion_metrics'
    )
    resource_rows, resource_metrics = build_catalog_text_resources(
        catalog_rows, [*existing_text_rows, *expansion_rows], benchmark_eval_rows
    )
    resource_rows = _write_routed_catalog_view(
        pkg, 'text_resources', resource_rows, resource_metrics, 'text_resource_metrics'
    )
    return expansion_rows, resource_rows


def _write_paharili(pkg, existing_rows):
    if not PAHARILI_GBM_ROWS_PATH.is_file():
        raise FileNotFoundError(
            f'Missing prepared PahariLI Garhwali rows: {PAHARILI_GBM_ROWS_PATH}'
        )
    paharili_rows, paharili_metrics = build_paharili_gbm_rows(
        read_jsonl(PAHARILI_GBM_ROWS_PATH), existing_rows
    )
    pkg.report['paharili_gbm_metrics'] = paharili_metrics
    for split in ('train', 'test', 'source_overlap'):
        split_rows = [row for row in paharili_rows if row['split'] == split]
        if split_rows:
            pkg.write('paharili_gbm', split_rows, 'data/paharili_gbm', split)


def _write_knowledge(pkg):
    for family, path in KNOWLEDGE_CONFIGS.items():
        if not path.exists():
            raise FileNotFoundError(f'Missing structured knowledge catalog: {path}')
        source_catalog = source_catalog_for_family(family)
        rows = [
            knowledge_row(row, family, source_catalog)
            for row in read_jsonl(path)
        ]
        ids = [row['id'] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f'Duplicate stable IDs in {family}')
        if pkg.profile == 'public':
            pkg.report['structured_knowledge_excluded_for_rights'][family] = 0
            pkg.report['structured_knowledge_metadata_only'][family] = len(rows)
            rows = [public_factual_metadata_row(row, family) for row in rows]
        pkg.write(family, rows, f'data/{family}', 'train')


def _write_asr(pkg):
    audio_sources = []
    asr_dir = ROOT / 'data/processed/model_ready/splits' / asr_split_directory(pkg.profile)
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(asr_dir / f'{split}.jsonl'))
        audio_sources.extend(rows)
        pkg.write(
            'asr',
            (audio_row(row, 'asr_target_clean', pkg.include_audio) for row in rows),
            'data/asr', split,
        )
    return audio_sources


def _optional_jsonl(path):
    return list(read_jsonl(path)) if path.exists() else []


def _write_drafts(pkg, allow_partial_drafts):
    report = pkg.report
    queue = list(read_jsonl(TRANSCRIPTS_DIR / 'untranscribed_queue.jsonl'))
    queue_count = len(queue)
    drafts_path = _first_existing_draft_file()
    drafts = list(read_jsonl(drafts_path))
    unique_drafts = list(deduplicate_audio_rows(drafts, 'machine_transcript'))
    unique_drafts = attach_recovery_third_checkpoint(
        unique_drafts, _optional_jsonl(TRANSCRIPTS_DIR / 'sravaani_recovery_whisper_v0.1.jsonl')
    )
    unique_drafts = attach_recovery_adjudication(
        unique_drafts, _optional_jsonl(TRANSCRIPTS_DIR / 'sravaani_recovery_adjudication.jsonl')
    )
    unique_drafts = attach_audio_grounded_review(
        unique_drafts,
        _optional_jsonl(TRANSCRIPTS_DIR / 'sravaani_recovery_audio_grounded_review.jsonl'),
    )
    report['draft_queue_records'] = queue_count
    report['draft_source'] = str(drafts_path.relative_to(ROOT))
    report['draft_records'] = len(drafts)
    report['draft_unique_audio'] = len(unique_drafts)
    report['draft_unique_nonempty_audio'] = sum(
        bool(str(row.get('machine_transcript') or '').strip())
        for row in unique_drafts
    )
    report['draft_empty_audio'] = (
        report['draft_unique_audio'] - report['draft_unique_nonempty_audio']
    )
    report['draft_source_label_conflicts'] = sum(
        row.get('language_scope_status') == 'source_label_conflict'
        for row in unique_drafts
    )
    report['draft_three_checkpoint_review_records'] = sum(
        bool(row.get('recovery_adjudication')) for row in unique_drafts
    )
    report['draft_third_checkpoint_records'] = sum(
        bool(row.get('recovery_third_checkpoint')) for row in unique_drafts
    )
    report['draft_audio_grounded_review_records'] = sum(
        bool(row.get('audio_grounded_review')) for row in unique_drafts
    )
    report['draft_inherited_duplicate_rows'] = len(drafts) - len(unique_drafts)
    report['drafts_complete'] = drafts_cover_queue(queue, drafts)
    if not report['drafts_complete'] and not allow_partial_drafts:
        raise RuntimeError(
            f'SraVaani drafts incomplete: {len(drafts)}/{queue_count}; '
            'use --allow-partial-drafts only for a preview'
        )
    pkg.write(
        'sravaani_drafts',
        (audio_row(row, 'machine_transcript', pkg.include_audio,
                   serialize_evidence=True) for row in unique_drafts),
        'data/sravaani_drafts', 'train',
    )
    return unique_drafts


def _write_lexicon_and_instructions(pkg):
    lexicon = read_jsonl(LEXICON_PATH)
    if pkg.profile == 'public':
        lexicon = (row for row in lexicon if is_public_text_row(row))
    pkg.write('lexicon', (lexicon_row(row) for row in lexicon), 'data/lexicon', 'train')
    for split in ('train', 'validation', 'test'):
        rows = list(read_jsonl(INSTRUCTIONS_DIR / f'{split}.jsonl'))
        if pkg.profile == 'public':
            rows = [row for row in rows if is_public_text_row(row)]
        rows = refresh_acceptable_responses(rows)
        pkg.write(
            'instructions', (with_public_rights_basis(row) for row in rows),
            'data/instructions', split,
        )


def _copy_package_documents(output):
    for name in ('LICENSE_POLICY.md', 'ATTRIBUTION.md', 'REMOVAL_POLICY.md'):
        shutil.copy2(ROOT / name, output / name)
    for name in ('DEVELOPER_QUICKSTART.md', 'DATASET_SCHEMA.md'):
        shutil.copy2(ROOT / 'docs' / name, output / name)
    if not PAHARILI_LICENSE_PATH.is_file():
        raise FileNotFoundError(
            f'Missing PahariLI repository license: {PAHARILI_LICENSE_PATH}'
        )
    paharili_license_target = output / 'licenses' / 'PahariLI-Apache-2.0.txt'
    paharili_license_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PAHARILI_LICENSE_PATH, paharili_license_target)
    shutil.copy2(
        ROOT / 'examples' / 'search_garhwali_lexicon.py',
        output / 'search_garhwali_lexicon.py',
    )
    rights_report = ROOT / 'research/text-rights-resolution-2026-09-30.md'
    rights_report_target = output / 'research' / rights_report.name
    rights_report_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(rights_report, rights_report_target)
    for name in (
        'huggingface-upstream-split-overlap-2026-10-05.md',
        'huggingface-upstream-split-overlap-2026-10-05.json',
    ):
        shutil.copy2(ROOT / 'research' / name, output / 'research' / name)


def _finalize_package(pkg, audio_sources):
    output, report = pkg.output, pkg.report
    removed_audio_files = 0 if pkg.include_audio else remove_packaged_audio(output)
    link_report = (
        link_audio(audio_sources, output) if pkg.include_audio else {'new': 0, 'total': 0}
    )
    report['linked_audio_files'] = link_report['total']
    report['newly_linked_audio_files'] = link_report['new']
    report['removed_audio_files'] = removed_audio_files
    output.mkdir(parents=True, exist_ok=True)
    dataset_info = dataset_info_for_release(output, report['configs'])
    (output / 'README.md').write_text(
        dataset_card(report, dataset_info=dataset_info), encoding='utf-8'
    )
    _copy_package_documents(output)
    (output / 'manifest.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    report['manifest_sha256'] = sha256_file(output / 'manifest.json')
    return report


def _build_at(output, profile='public', include_audio=False,
              allow_partial_drafts=False, shard_rows=10_000):
    output = prepare_package_output(output)
    pkg = _new_package_build(output, profile, include_audio, shard_rows)
    quality_catalog = list(read_jsonl(
        ROOT / 'data/processed/model_ready/quality_v2/text.jsonl'
    ))
    parent_quality = {row['text_sha256']: row for row in quality_catalog}
    _write_text_splits(pkg, parent_quality)
    existing_text_rows = _existing_text_rows(pkg)
    catalog_rows = _write_catalog(pkg, quality_catalog)
    expansion_rows, resource_rows = _write_catalog_views(pkg, catalog_rows, existing_text_rows)
    _write_paharili(pkg, [*existing_text_rows, *expansion_rows, *resource_rows])
    _write_knowledge(pkg)
    audio_sources = _write_asr(pkg)
    audio_sources.extend(_write_drafts(pkg, allow_partial_drafts))
    _write_lexicon_and_instructions(pkg)
    return _finalize_package(pkg, audio_sources)


def build(output, profile='public', include_audio=False, allow_partial_drafts=False,
          shard_rows=10_000):
    """Build in a sibling staging directory, then replace the managed package."""
    output = Path(output)
    if output.exists() and output.resolve() not in MANAGED_OUTPUTS:
        raise ValueError(
            'refusing to replace an existing custom output directory; use a new '
            'path or one of the managed Hugging Face package paths'
        )
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise ValueError(f'package output must be a regular directory: {output}')
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.building-'
    ))
    staging.rmdir()
    backup = Path(tempfile.mkdtemp(
        dir=output.parent, prefix=f'.{output.name}.previous-'
    ))
    backup.rmdir()
    try:
        report = _build_at(
            staging, profile=profile, include_audio=include_audio,
            allow_partial_drafts=allow_partial_drafts, shard_rows=shard_rows,
        )
        if output.exists():
            output.rename(backup)
        staging.rename(output)
        if backup.exists():
            shutil.rmtree(backup)
        return report
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if backup.exists() and not output.exists():
            backup.rename(output)
        elif backup.exists():
            shutil.rmtree(backup)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument(
        '--profile', choices=('public', 'all-data'),
        default='public',
    )
    parser.add_argument('--include-audio', action='store_true')
    parser.add_argument('--allow-partial-drafts', action='store_true')
    parser.add_argument('--shard-rows', type=int, default=10_000)
    args = parser.parse_args()
    output = args.output or (
        ALL_DATA_OUTPUT if profile_includes_all_data(args.profile) else DEFAULT_OUTPUT
    )
    if output.resolve() in {RELEASE_PUBLIC_OUTPUT.resolve(), RELEASE_ALL_DATA_OUTPUT.resolve()}:
        ensure_unpublished_corpus_version(RELEASE_VERSION)
    print(json.dumps(build(
        output,
        profile=args.profile,
        include_audio=args.include_audio,
        allow_partial_drafts=args.allow_partial_drafts,
        shard_rows=args.shard_rows,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
