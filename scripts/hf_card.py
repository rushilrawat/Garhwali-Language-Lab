"""Hugging Face dataset card and feature metadata.

The card prose lives in ``templates/hf_dataset_card.md``; this module fills it in
and merges the per-config feature schemas declared in the card header.
"""

from __future__ import annotations

import copy
import json
import re
import tempfile
from functools import lru_cache
from pathlib import Path

from hf_rights import profile_includes_all_data


def _is_hf_null_feature(feature):
    return (
        isinstance(feature, dict)
        and feature.get('_type') == 'Value'
        and feature.get('dtype') == 'null'
    )


def _merge_hf_feature_nodes(left, right, path):
    if left == right:
        return copy.deepcopy(left)
    if _is_hf_null_feature(left):
        return copy.deepcopy(right)
    if _is_hf_null_feature(right):
        return copy.deepcopy(left)
    if isinstance(left, dict) and isinstance(right, dict):
        left_type = left.get('_type')
        right_type = right.get('_type')
        if left_type == right_type == 'List':
            return {
                **copy.deepcopy(left),
                'feature': _merge_hf_feature_nodes(
                    left['feature'], right['feature'], f'{path}[]'
                ),
            }
        if left_type or right_type:
            raise ValueError(
                f'incompatible Hugging Face feature at {path}: '
                f'{left!r} versus {right!r}'
            )
        merged = {}
        for key in sorted(set(left) | set(right)):
            if key in left and key in right:
                merged[key] = _merge_hf_feature_nodes(
                    left[key], right[key], f'{path}.{key}'
                )
            else:
                merged[key] = copy.deepcopy(
                    left[key] if key in left else right[key]
                )
        return merged
    raise ValueError(
        f'incompatible Hugging Face feature at {path}: '
        f'{left!r} versus {right!r}'
    )


def merge_hf_feature_schemas(schemas):
    """Union JSON shard schemas, promoting null-only fields to observed types."""
    merged = {}
    for schema in schemas:
        merged = _merge_hf_feature_nodes(merged, schema, 'root')
    return merged


def infer_hf_config_features(config_dir):
    """Infer one stable Hub schema across a config's independently written shards."""
    try:
        from datasets import Dataset, Features
    except ImportError as exc:
        raise RuntimeError(
            'Install requirements-hf-release.txt to infer Dataset Viewer feature metadata'
        ) from exc

    shard_paths = sorted(Path(config_dir).glob('*.jsonl'))
    if not shard_paths:
        raise ValueError(f'No JSONL shards found in {config_dir}')
    with tempfile.TemporaryDirectory(prefix='garhwali-hf-feature-schema-') as cache_dir:
        schemas = [
            Dataset.from_json(
                str(path), cache_dir=cache_dir, keep_in_memory=True,
                chunksize=path.stat().st_size + 1,
            ).features.to_dict()
            for path in shard_paths
        ]
    features = Features.from_dict(merge_hf_feature_schemas(schemas))
    return features._to_yaml_list()


def dataset_info_for_release(output, config_report):
    """Declare stable features for configs that the Hub cannot safely infer."""
    dataset_info = []
    for config_name in (
        'sravaani_drafts', 'text', 'text_expansion', 'text_resources',
        'paharili_gbm',
    ):
        if config_report.get(f'{config_name}/train', {}).get('records', 0):
            dataset_info.append({
                'config_name': config_name,
                'features': infer_hf_config_features(
                    Path(output) / 'data' / config_name
                ),
            })
    return dataset_info


CARD_TEMPLATE_PATH = Path(__file__).resolve().parent / 'templates/hf_dataset_card.md'
CARD_SECTION_MARKER = re.compile(r'^<!-- card:([\w.-]+) -->$', re.MULTILINE)
CONFIG_USES = {
    'asr': 'provider transcripts; not native-adjudicated',
    'catalog': 'unique text inventory with content and metadata-only entries',
    'geography': 'place facts and citations',
    'historical_terms': 'historical names and terms',
    'instructions': 'instruction/response examples',
    'lexicon': 'vocabulary and pronunciation candidates',
    'literary_people': 'writer and contributor metadata',
    'literary_works': 'work-level bibliography',
    'popular_songs': 'song-level metadata; no lyrics',
    'paharili_gbm': 'Garhwali-labeled PahariLI language-identification text; unreviewed and retains source-lineage and rights caveats',
    'record_index': 'archive references; not training examples',
    'record_sources': 'record-to-source links; not training examples',
    'source_catalog': 'deduplicated source and rights references',
    'sravaani_drafts': 'machine transcript drafts; not ground truth',
    'text': 'Garhwali text examples; source_overlap preserves rows linked to upstream dev/test content outside train',
    'text_expansion': 'strict-tier candidates; upstream dev/test overlaps are in source_overlap; not evaluation data',
    'text_resources': 'additional rights-cleared Garhwali resources; quality varies; upstream overlaps are separately split',
    'university_research': 'research bibliography',
}


@lru_cache(maxsize=1)
def card_sections():
    """Read the card template into ``{section name: text}``."""
    parts = CARD_SECTION_MARKER.split(CARD_TEMPLATE_PATH.read_text(encoding='utf-8'))
    return {name: body.strip('\n') for name, body in zip(parts[1::2], parts[2::2], strict=True)}


def _card_config_yaml_and_table(configs):
    by_config = {}
    for key, value in configs.items():
        if value.get('records', 0) > 0:
            config, split = key.split('/', 1)
            by_config.setdefault(config, {})[split] = value['records']
    # Dataset metadata accepts one declaration per split. A shard glob keeps
    # multiple JSONL shards from becoming duplicate split names.
    yaml_blocks = [
        f'- config_name: {name}\n  data_files:\n' + '\n'.join(
            f'  - split: {split}\n    path: data/{name}/{split}-*.jsonl'
            for split in sorted(by_config[name])
        )
        for name in sorted(by_config)
    ]
    table_rows = [
        f'| `{name}` | {sum(by_config[name].values()):,} | '
        f'{CONFIG_USES.get(name, "source-specific records; inspect the schema")} |'
        for name in sorted(by_config)
    ]
    entries = sum(len(splits) for splits in by_config.values())
    return '\n'.join(yaml_blocks), '\n'.join(table_rows), len(by_config), entries


def dataset_card(report, dataset_info=None):
    """Render the Hugging Face README from ``templates/hf_dataset_card.md``."""
    sections = card_sections()
    release_id = str(report.get('release_id', ''))
    release_version = release_id.rsplit('-v', 1)[-1]
    expansion = report.get('text_expansion_metrics') or {}
    resources = report.get('text_resource_metrics') or {}
    paharili = report.get('paharili_gbm_metrics') or {}
    paharili_splits = paharili.get('split_records') or {}
    source_expansion = report.get('source_expansion') or {}
    jambu = source_expansion.get('jambu') or {}
    library = source_expansion.get('language_library') or {}
    configs_yaml, config_table, config_count, entry_count = _card_config_yaml_and_table(report['configs'])

    draft_unique_audio = report.get('draft_unique_audio', 0)
    draft_nonempty_audio = report.get('draft_unique_nonempty_audio', draft_unique_audio)
    draft_empty_audio = report.get('draft_empty_audio', max(0, draft_unique_audio - draft_nonempty_audio))
    draft_source_rows = report.get('draft_records')
    exported_rows = sum(item['records'] for item in report['configs'].values())
    all_data = profile_includes_all_data(report['profile'])
    package_summary = (
        f"This {'complete all-data' if all_data else 'public-profile'} package contains "
        f"**{exported_rows:,} records** across {config_count} named "
        f"{'configuration' if config_count == 1 else 'configurations'} ({entry_count} config/split entries)"
    )

    values = {
        'release_id': report['release_id'],
        'release_version': release_version,
        'configs_yaml': configs_yaml,
        'config_table': config_table,
        'dataset_info_yaml': (
            # JSON flow collections are valid YAML and keep generated feature
            # metadata deterministic without adding a YAML dependency.
            'dataset_info: ' + json.dumps(dataset_info, ensure_ascii=False, separators=(',', ':')) + '\n'
            if dataset_info else ''
        ),
        'language_header': '- gbm\n- hi\n- en' if all_data else '- gbm',
        'draft_status': 'complete' if report['drafts_complete'] else 'partial',
        'draft_summary': (
            f'{package_summary}. The SraVaani draft config covers '
            f'**{draft_unique_audio:,} unique audio hashes**'
            f"{f' from {draft_source_rows:,} source rows' if draft_source_rows is not None else ''}: "
            f'**{draft_nonempty_audio:,}** have non-empty draft text and '
            f'**{draft_empty_audio:,}** are empty.'
        ),
        'audio_summary': (
            f"The package includes **{report['linked_audio_files']:,} content-addressed audio files**."
            if report['include_audio'] else
            'This transcript-only package does not include audio files or source filenames.'
        ),
        'draft_third_checkpoint_records': report['draft_third_checkpoint_records'],
        'draft_three_checkpoint_review_records': report['draft_three_checkpoint_review_records'],
        'draft_audio_grounded_review_records': report['draft_audio_grounded_review_records'],
        'draft_source_label_conflicts': report['draft_source_label_conflicts'],
        'catalog_records': report['catalog_records'],
        'catalog_noncommercial_records': report.get('catalog_noncommercial_records', 0),
        'catalog_sharealike_records': report.get('catalog_sharealike_records', 0),
        'catalog_source_policy_records': report.get('catalog_source_policy_records', 0),
        'catalog_factual_word_records': report.get('catalog_factual_word_records', 0),
        'metadata_only_records': sum(report.get('structured_knowledge_metadata_only', {}).values()),
        'text_source_overlap_records': report.get('text_source_overlap_records', 0),
        'overlap_audit_url': (
            'https://huggingface.co/datasets/rushilrawat/garhwali-corpus/blob/main/'
            f'releases/v{release_version}/research/huggingface-upstream-split-overlap-2026-10-05.md'
        ),
        'expansion_records': expansion.get('records', 0),
        'expansion_source_overlap_records': expansion.get('source_split_overlap_records', 0),
        'expansion_recommended': expansion.get('recommended_for_training', 0),
        'expansion_not_recommended': max(
            0, expansion.get('records', 0) - expansion.get('recommended_for_training', 0)
        ),
        'resource_records': resources.get('records', 0),
        'resource_words': resources.get('whitespace_words', 0),
        'resource_characters': resources.get('characters', 0),
        'resource_recommended': resources.get('recommended_for_training', 0),
        'paharili_new_records': paharili.get('new_records', 0),
        'paharili_source_records': paharili.get('garhwali_source_records', 0),
        'paharili_unique_texts': paharili.get('normalized_unique_source_texts', 0),
        'paharili_collapsed_records': paharili.get('collapsed_duplicate_source_records', 0),
        'paharili_new_source_ids': paharili.get('new_source_record_ids', 0),
        'paharili_existing_source_ids': paharili.get('source_record_ids_already_in_existing_configs', 0),
        'paharili_train': paharili_splits.get('train', 0),
        'paharili_test': paharili_splits.get('test', 0),
        'paharili_source_overlap': paharili_splits.get('source_overlap', 0),
        'jambu_source_records': jambu.get('source_records', 0),
        'jambu_unique_forms': jambu.get('unique_forms', 0),
        'jambu_new_forms': max(0, jambu.get('unique_forms', 0) - jambu.get('already_in_current_corpus', 0)),
        'jambu_already_in_corpus': jambu.get('already_in_current_corpus', 0),
        'jambu_cross_source_overlap': jambu.get('cross_source_overlap', 0),
        'jambu_new_vs_other_sources': jambu.get('new_vs_other_sources', 0),
        'library_source_records': library.get('source_records', 0),
        'library_unique_strings': library.get('unique_strings', 0),
        'library_cross_source_overlap': library.get('cross_source_overlap', 0),
        'library_new_vs_current_corpus': library.get('new_vs_current_corpus', 0),
        'library_type_counts': ', '.join(
            f'{kind} {count:,}' for kind, count in sorted((library.get('records_by_type') or {}).items())
        ),
    }

    def section(name):
        return sections[name].format_map(values)

    profile = 'all-data' if all_data else 'public'
    history = sections.get(f'history-{release_version}')
    if release_id.endswith('v0.2.1'):
        additions = '\n\n' + section('additions-0.2.1') + '\n'
    elif release_id.endswith('v0.2.0'):
        additions = '\n\n' + section('additions-0.2.0') + '\n'
    else:
        additions = ''
    values.update({
        'access_notice': section(f'{profile}-access'),
        'resource_summary': section(f'{profile}-resources'),
        'catalog_summary': section(f'{profile}-catalog'),
        'speech_companion': '' if all_data else '\n\n' + section('public-speech-companion'),
        'candidate_history': '\n' + history if history else '',
        'source_expansion': additions,
        'text_source_overlap_summary': section('source-overlap'),
        'text_expansion_summary': section('text-expansion'),
        'text_resources_summary': section('text-resources'),
        'paharili_summary': section('paharili') if paharili else '',
    })
    return section('main') + '\n'
