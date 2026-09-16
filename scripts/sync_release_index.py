#!/usr/bin/env python3
"""Refresh dynamic counts in the tracked release index from built artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'release/v0.1.0-manifest.json'
DEFAULT_SPLITS = ROOT / 'data/processed/model_ready/splits/report.json'
DEFAULT_TEXT = ROOT / 'data/processed/text/report.json'
DEFAULT_PUBLIC = ROOT / 'data/huggingface/garhwali-language-lab/manifest.json'
DEFAULT_ALL_DATA = ROOT / 'data/huggingface/garhwali-language-lab-all-data/manifest.json'
KNOWLEDGE_CONFIGS = (
    'geography', 'historical_terms', 'literary_people',
    'literary_works', 'popular_songs', 'university_research',
)


def config_records(manifest, prefix):
    return sum(
        value['records'] for key, value in manifest['configs'].items()
        if key == prefix or key.startswith(prefix + '/')
    )


def package_records(manifest):
    return sum(value['records'] for value in manifest['configs'].values())


def refresh(index, splits, text, public, all_data):
    records = splits['text']['records']
    index['generated'] = date.today().isoformat()
    index['text'].update({
        'total': sum(records.values()),
        'splits': dict(records),
        'unique_parent_documents': text['unique_texts'],
    })

    index['all_data_package'].update({
        'profile': all_data.get('profile', 'all-data'),
        'transcript_only_package_rows': package_records(all_data),
        'full_text_segments': config_records(all_data, 'text'),
        'exact_unique_texts': all_data['catalog_records'],
        'redacted_text_values': all_data['catalog_redacted_text_records'],
        'human_vaani_transcript_rows': config_records(all_data, 'asr'),
        'lexicon_rows': config_records(all_data, 'lexicon'),
        'instruction_rows': config_records(all_data, 'instructions'),
        'all_collected_text_values_included': all_data['all_collected_text_values_included'],
    })

    index['public_text_release'].update({
        'exact_unique_with_public_rights_basis': (
            public['catalog_records'] - public['catalog_redacted_text_records']
        ),
        'rights_pending_catalog_records': public['catalog_redacted_text_records'],
        'transcript_only_package_rows': package_records(public),
    })
    index['evaluation_candidates']['text'] = splits['evaluation_candidates']['text_records']

    knowledge_counts = {
        family: config_records(all_data, family) for family in KNOWLEDGE_CONFIGS
    }
    index['structured_knowledge'] = {
        'records': sum(knowledge_counts.values()),
        'configs': knowledge_counts,
        'included_in_public_and_all_data_packages': True,
    }
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX)
    parser.add_argument('--splits', type=Path, default=DEFAULT_SPLITS)
    parser.add_argument('--text-report', type=Path, default=DEFAULT_TEXT)
    parser.add_argument('--public-manifest', type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument('--all-data-manifest', type=Path, default=DEFAULT_ALL_DATA)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding='utf-8'))
    refreshed = refresh(
        index,
        json.loads(args.splits.read_text(encoding='utf-8')),
        json.loads(args.text_report.read_text(encoding='utf-8')),
        json.loads(args.public_manifest.read_text(encoding='utf-8')),
        json.loads(args.all_data_manifest.read_text(encoding='utf-8')),
    )
    args.index.write_text(
        json.dumps(refreshed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps({
        'release_id': refreshed['release_id'],
        'text_records': refreshed['text']['total'],
        'unique_parent_documents': refreshed['text']['unique_parent_documents'],
        'structured_knowledge_records': refreshed['structured_knowledge']['records'],
        'public_package_rows': refreshed['public_text_release']['transcript_only_package_rows'],
        'all_data_package_rows': refreshed['all_data_package']['transcript_only_package_rows'],
    }, indent=2))


if __name__ == '__main__':
    main()
