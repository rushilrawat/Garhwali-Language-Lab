#!/usr/bin/env python3
"""Refine the highest-value text queue without guessing linguistic corrections."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from build_huggingface_dataset import is_public_garhwali_text_row, provenance_items


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed/model_ready/language_quality/text.jsonl'
OUT = ROOT / 'data/processed/model_ready/text_quality_v2'
PHONE = re.compile(r'(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)')
EDITORIAL_NASAL = re.compile(r'\([nm]\)', re.IGNORECASE)
EXACT_DOUBLE_PERIOD = re.compile(r'(?<!\.)\.\.(?!\.)')
REPEATED_PUNCTUATION = re.compile(r'([!?,;:])\1+')
URL = re.compile(r'https?://|www\.', re.IGNORECASE)
WIKI_MARKUP = re.compile(r"'''|''|[=\[\]{}*#|]")
REGIONAL_IDENTITY = re.compile(
    r'\b(kumaon|kumaoni|lohaghat|champawat|nainital)\b', re.IGNORECASE
)
LEXICON_GENRES = {'lexicon', 'thematic_lexicon', 'historical_lexicon', 'numeral_lexicon'}
TRANSLATION_GENRES = {'software_localization', 'translated_example'}
NATIVE_ACCURACY_FLAGS = {'native_accuracy_unverified', 'needs_native_review', 'community_edited'}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def text_digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def clean_wiki_markup(text):
    text = re.sub(r"'''|''", '', text)
    text = re.sub(r'[=\[\]{}*#|]+', ' ', text)
    return ' '.join(text.split())


def build_quality_dimensions(row, release, changes, signals, remaining_flags):
    language = row.get('language_quality') or {}
    script = (language.get('script_profile') or {}).get('script') or 'unknown'
    genres = set((row.get('genre_quality') or {}).get('tags') or [])
    items = provenance_items(row)
    source_ids = sorted({item.get('source_id') for item in items if item.get('source_id')})
    source_flags = sorted({
        flag for item in items for flag in item.get('quality_flags') or []
    })
    iso_codes = sorted({item.get('iso_639_3') for item in items if item.get('iso_639_3')})
    language_needs_review = (
        language.get('confidence') != 'high' or bool(language.get('review_required'))
    )
    source_attested_transcription = (
        'source_linguistic_transcription' in (language.get('evidence') or [])
    )
    language_status = (
        'source_declared_garhwali_pending_native_validation'
        if language_needs_review else 'existing_high_confidence_evidence'
    )

    if script == 'Latn' and source_attested_transcription:
        orthography_status = 'source_attested_linguistic_notation'
    elif script == 'Latn':
        orthography_status = 'romanized_source_form_pending_native_review'
    elif 'double_period_normalized' in changes or 'wiki_markup_removed' in changes:
        orthography_status = 'mechanically_normalized'
    elif signals or remaining_flags:
        orthography_status = 'source_form_with_surface_review_pending'
    else:
        orthography_status = 'source_form_preserved'

    if genres & TRANSLATION_GENRES and source_attested_transcription:
        semantic_status = 'source_attested_parallel_alignment'
    elif genres & TRANSLATION_GENRES or 'native_accuracy_unverified' in source_flags:
        semantic_status = 'translation_or_alignment_pending_native_validation'
    else:
        semantic_status = 'not_applicable_or_not_available'

    if 'may_contain_scaffolding' in source_flags:
        source_status = 'source_scaffolding_review_required'
    elif set(source_flags) & NATIVE_ACCURACY_FLAGS:
        source_status = 'native_accuracy_unverified'
    elif 'structured_derivative_of_existing_lsi_ocr' in source_flags:
        source_status = 'structured_historical_derivative'
    elif len(source_ids) > 1:
        source_status = 'multiple_source_records_observed'
    else:
        source_status = 'single_source_record'

    surface_status = (
        'review_required' if signals or remaining_flags else
        'mechanically_normalized' if changes else 'no_detected_surface_issue'
    )
    return {
        'language_identity': {
            'status': language_status,
            'source_confidence_label': language.get('confidence'),
            'evidence': language.get('evidence') or [],
            'iso_639_3_codes': iso_codes,
            'native_validation_required': language_needs_review,
        },
        'orthography': {
            'status': orthography_status,
            'script': script,
            'native_validation_required': script == 'Latn' and not source_attested_transcription,
        },
        'semantic_alignment': {
            'status': semantic_status,
            'native_validation_required': semantic_status.endswith('native_validation'),
        },
        'source_evidence': {
            'status': source_status,
            'source_ids': source_ids,
            'distinct_source_count': len(source_ids),
            'quality_flags': source_flags,
            'corroboration_is_accuracy_proof': False,
        },
        'surface_form': {
            'status': surface_status,
            'release_value_changed': release != (
                row.get('text_model') or row.get('text_clean') or row.get('text') or ''
            ),
        },
    }


def build_review_priority(dimensions, signals, remaining_flags):
    source_flags = set(dimensions['source_evidence']['quality_flags'])
    substantive_signals = set(signals) - {'romanized_text_requires_native_review'}
    if remaining_flags or substantive_signals or 'may_contain_scaffolding' in source_flags:
        return {'rank': 1, 'label': 'surface_or_scaffolding', 'reasons': sorted(
            set(remaining_flags) | substantive_signals | (source_flags & {'may_contain_scaffolding'})
        )}
    if source_flags & NATIVE_ACCURACY_FLAGS:
        return {'rank': 2, 'label': 'source_accuracy', 'reasons': sorted(
            source_flags & NATIVE_ACCURACY_FLAGS
        )}
    if dimensions['semantic_alignment']['native_validation_required']:
        return {'rank': 3, 'label': 'semantic_alignment', 'reasons': [
            'translation_or_alignment_pending_native_validation'
        ]}
    if dimensions['orthography']['native_validation_required']:
        return {'rank': 4, 'label': 'romanized_orthography', 'reasons': [
            'romanized_source_form_pending_native_review'
        ]}
    return {'rank': 5, 'label': 'language_identity', 'reasons': [
        'source_declared_garhwali_pending_native_validation'
    ]}


def build_review_queue(rows):
    unique = {}
    for row in rows:
        dimensions = row['quality_dimensions']
        unresolved = (
            row['manual_review_required']
            or dimensions['language_identity']['native_validation_required']
        )
        if unresolved:
            unique[row['text_sha256']] = row
    return sorted(
        unique.values(),
        key=lambda row: (
            row['review_priority']['rank'],
            row['quality_dimensions']['source_evidence']['source_ids'],
            row['text_sha256'],
        ),
    )


def refine_row(row):
    original = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    genres = set((row.get('genre_quality') or {}).get('tags') or [])
    release = original
    signals = []
    changes = []
    cleanup_flags = set(row.get('cleanup_review_flags') or []) | set(
        row.get('deep_cleanup_flags') or []
    )
    source_attested_transcription = 'source_linguistic_transcription' in (
        (row.get('language_quality') or {}).get('evidence') or []
    )

    if PHONE.search(original):
        signals.append('contains_phone_number')
        release = PHONE.sub('<PHONE_NUMBER>', release)
        changes.append('phone_number_redacted')
    if 'html_markup' in cleanup_flags and WIKI_MARKUP.search(release):
        release = clean_wiki_markup(release)
        changes.append('wiki_markup_removed')
    if EXACT_DOUBLE_PERIOD.search(release):
        release = EXACT_DOUBLE_PERIOD.sub('…', release)
        changes.append('double_period_normalized')
    script = (row.get('language_quality') or {}).get('script_profile', {}).get('script')
    if script == 'Latn' and not source_attested_transcription:
        signals.append('romanized_text_requires_native_review')
    if '/' in original and (
        len(original.split()) <= 6 or genres.intersection(LEXICON_GENRES)
    ) and not source_attested_transcription:
        signals.append('slash_separated_variants')
    if EDITORIAL_NASAL.search(original):
        signals.append('editorial_nasal_notation')
    if REPEATED_PUNCTUATION.search(original):
        signals.append('repeated_punctuation')
    if REGIONAL_IDENTITY.search(original):
        signals.append('regional_identity_review')
    semantic_characters = sum(
        unicodedata.category(character)[0] in {'L', 'M', 'N'} for character in original
    )
    if semantic_characters <= 2 and not genres.intersection(LEXICON_GENRES):
        signals.append('very_short_fragment')

    resolved_flags = set()
    if 'html_markup' in cleanup_flags and not WIKI_MARKUP.search(release):
        resolved_flags.add('html_markup')
    if 'mixed_latin_devanagari' in cleanup_flags and script not in {'Mixed', 'Mixed-Deva-Latn'}:
        resolved_flags.add('mixed_latin_devanagari')
    if (
        'no_devanagari' in cleanup_flags
        and script == 'Latn'
        and 'source_garhwali_label' in ((row.get('language_quality') or {}).get('evidence') or [])
    ):
        resolved_flags.add('no_devanagari')
    if 'very_short' in cleanup_flags and genres.intersection(LEXICON_GENRES):
        resolved_flags.add('very_short')
    if 'url' in cleanup_flags and not URL.search(release):
        resolved_flags.add('url')
    remaining_flags = sorted(cleanup_flags - resolved_flags)

    manual_review_required = bool(signals or remaining_flags)
    if 'phone_number_redacted' in changes:
        refinement_status = 'privacy_redacted_review_required' if manual_review_required else 'privacy_redacted'
    elif changes:
        refinement_status = 'mechanically_cleaned_review_required' if manual_review_required else 'mechanically_cleaned'
    elif manual_review_required:
        refinement_status = 'review_required'
    else:
        refinement_status = 'no_additional_issue'

    dimensions = build_quality_dimensions(
        row, release, changes, sorted(set(signals)), remaining_flags
    )
    priority = build_review_priority(dimensions, signals, remaining_flags)
    result = dict(row)
    result.update({
        'original_text': original,
        'original_text_sha256': text_digest(original),
        'release_text': release,
        'release_text_sha256': text_digest(release),
        'automatic_changes': changes,
        'resolved_cleanup_flags': sorted(resolved_flags),
        'remaining_cleanup_flags': remaining_flags,
        'review_signals': sorted(set(signals)),
        'manual_review_required': manual_review_required,
        'language_decision': 'unchanged_pending_native_review' if signals or remaining_flags else 'unchanged',
        'quality_refinement_status': refinement_status,
        'quality_dimensions': dimensions,
        'review_priority': priority,
    })
    return result


def main():
    rows = [
        refine_row(row) for row in read_jsonl(SOURCE)
        if is_public_garhwali_text_row(row)
        and row.get('language_bucket') == 'garhwali_candidate'
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    output = OUT / 'priority_text.jsonl'
    with output.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')

    review_queue = build_review_queue(rows)
    with (OUT / 'review_queue.jsonl').open('w', encoding='utf-8') as handle:
        for row in review_queue:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')

    signals = Counter(
        signal for row in rows for signal in row['review_signals']
    )
    resolved = Counter(
        flag for row in rows for flag in row['resolved_cleanup_flags']
    )
    remaining = Counter(
        flag for row in rows for flag in row['remaining_cleanup_flags']
    )
    changes = Counter(
        change for row in rows for change in row['automatic_changes']
    )
    sources = Counter(
        source.get('source_id') or 'unknown'
        for row in rows for source in row.get('provenance') or []
    )
    priority_counts = Counter(row['review_priority']['label'] for row in review_queue)
    dimension_status_counts = {
        dimension: dict(sorted(Counter(
            row['quality_dimensions'][dimension]['status'] for row in rows
        ).items()))
        for dimension in (
            'language_identity', 'orthography', 'semantic_alignment',
            'source_evidence', 'surface_form',
        )
    }
    report = {
        'records': len(rows),
        'values_automatically_changed': sum(bool(row['automatic_changes']) for row in rows),
        'manual_review_required': sum(row['manual_review_required'] for row in rows),
        'no_additional_issue': sum(not row['manual_review_required'] for row in rows),
        'review_queue_records': len(review_queue),
        'review_priority_counts': dict(sorted(priority_counts.items())),
        'quality_dimension_status_counts': dimension_status_counts,
        'review_signal_counts': dict(sorted(signals.items(), key=lambda item: (-item[1], item[0]))),
        'resolved_cleanup_flag_counts': dict(sorted(resolved.items(), key=lambda item: (-item[1], item[0]))),
        'remaining_cleanup_flag_counts': dict(sorted(remaining.items(), key=lambda item: (-item[1], item[0]))),
        'automatic_change_counts': dict(sorted(changes.items(), key=lambda item: (-item[1], item[0]))),
        'source_record_counts': dict(sorted(sources.items(), key=lambda item: (-item[1], item[0]))),
        'policy': {
            'linguistic_values': 'No automatic spelling, transliteration, language, or dialect correction.',
            'privacy': 'High-confidence Indian phone-number patterns are redacted in release_text; original_text remains preserved locally.',
            'regional_terms': 'Regional place/language mentions trigger review but never automatic relabeling.',
            'confidence': 'Dimensions report evidence and review state; they are not accuracy probabilities.',
        },
    }
    (OUT / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
