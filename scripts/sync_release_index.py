#!/usr/bin/env python3
"""Refresh dynamic counts in the tracked release index from built artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX = ROOT / 'release/v0.1.1-manifest.json'
DEFAULT_SPLITS = ROOT / 'data/processed/model_ready/splits/report.json'
DEFAULT_TEXT = ROOT / 'data/processed/text/report.json'
DEFAULT_PUBLIC = ROOT / 'data/huggingface/garhwali-language-lab/manifest.json'
DEFAULT_ALL_DATA = ROOT / 'data/huggingface/garhwali-language-lab-all-data/manifest.json'
DEFAULT_BENCHMARK = ROOT / 'data/processed/evaluation/garhwali_bench/manifest.json'
DEFAULT_RESOURCES = ROOT / 'data/processed/model_ready/language_resources/report.json'
DEFAULT_FINAL_AUDIT = ROOT / 'release/v0.1.1/final-audit.json'
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


def refresh(index, splits, text, public, all_data, benchmark=None, resources=None,
            final_audit=None):
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
    if benchmark:
        baseline = benchmark.get('baselines', {}).get('character_bigram', {})
        index['garhwali_bench'].update({
            'release_id': benchmark.get('release_id'),
            'held_out_text_records': benchmark['records']['text_evaluation'],
            'speaker_safe_asr_records': benchmark['records']['asr_evaluation'],
            'external_records': benchmark['records']['external_total'],
            'character_bigram_perplexity': baseline.get('perplexity'),
            'character_oov_rate': baseline.get('oov_character_rate'),
            'external_exact_train_text': benchmark['leakage']['external_exact_train_text'],
            'internal_exact_train_text': benchmark['leakage']['internal_text_exact_train_text'],
            'asr_speaker_overlap': benchmark['leakage']['asr_speaker_overlap'],
            'native_reviewed': bool(benchmark.get('native_reviewed')),
            'dialect_aware': bool(benchmark.get('dialect_aware')),
            'status': benchmark.get('status'),
        })
        index['evaluation_candidates'].update({
            'text': benchmark['records']['text_evaluation'],
            'speech': benchmark['records']['asr_evaluation'],
            'review_status': benchmark.get('status'),
            'native_review_deferred': True,
        })
    if resources:
        index['language_resources'].update({
            'tokenizer_type': resources['tokenizer_type'],
            'tokenizer_vocabulary_size': resources['tokenizer_vocabulary_size'],
            'tokenizer_training_texts': resources['tokenizer_training_texts'],
            'word_types': resources['word_types'],
            'pronunciation_candidates': resources['pronunciation_candidates'],
            'pronunciations_with_source_phonetics': resources[
                'pronunciation_with_source_phonetics'
            ],
            'tts_pairs': resources['tts_pairs'],
        })

    knowledge_counts = {
        family: config_records(all_data, family) for family in KNOWLEDGE_CONFIGS
    }
    public_knowledge_count = sum(
        config_records(public, family) for family in KNOWLEDGE_CONFIGS
    )
    all_knowledge_count = sum(knowledge_counts.values())
    index['structured_knowledge'] = {
        'records': all_knowledge_count,
        'configs': knowledge_counts,
        'all_data_records': all_knowledge_count,
        'public_records': public_knowledge_count,
        'public_excluded_for_rights': all_knowledge_count - public_knowledge_count,
        'included_in_all_data_package': True,
    }
    audit_status = (final_audit or {}).get('status', 'not_run')
    index['final_audit_status'] = audit_status
    index['status'] = (
        'release_ready_with_public_rights_filtered_export'
        if audit_status == 'passed'
        else 'blocked_final_audit'
    )
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--index', type=Path, default=DEFAULT_INDEX)
    parser.add_argument('--splits', type=Path, default=DEFAULT_SPLITS)
    parser.add_argument('--text-report', type=Path, default=DEFAULT_TEXT)
    parser.add_argument('--public-manifest', type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument('--all-data-manifest', type=Path, default=DEFAULT_ALL_DATA)
    parser.add_argument('--benchmark-manifest', type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument('--language-resources', type=Path, default=DEFAULT_RESOURCES)
    parser.add_argument('--final-audit', type=Path, default=DEFAULT_FINAL_AUDIT)
    args = parser.parse_args()

    index = json.loads(args.index.read_text(encoding='utf-8'))
    refreshed = refresh(
        index,
        json.loads(args.splits.read_text(encoding='utf-8')),
        json.loads(args.text_report.read_text(encoding='utf-8')),
        json.loads(args.public_manifest.read_text(encoding='utf-8')),
        json.loads(args.all_data_manifest.read_text(encoding='utf-8')),
        json.loads(args.benchmark_manifest.read_text(encoding='utf-8')),
        json.loads(args.language_resources.read_text(encoding='utf-8')),
        json.loads(args.final_audit.read_text(encoding='utf-8'))
        if args.final_audit.exists() else None,
    )
    args.index.write_text(
        json.dumps(refreshed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )
    print(json.dumps({
        'release_id': refreshed['release_id'],
        'status': refreshed['status'],
        'final_audit_status': refreshed['final_audit_status'],
        'text_records': refreshed['text']['total'],
        'unique_parent_documents': refreshed['text']['unique_parent_documents'],
        'structured_knowledge_records': refreshed['structured_knowledge']['records'],
        'public_package_rows': refreshed['public_text_release']['transcript_only_package_rows'],
        'all_data_package_rows': refreshed['all_data_package']['transcript_only_package_rows'],
    }, indent=2))


if __name__ == '__main__':
    main()
