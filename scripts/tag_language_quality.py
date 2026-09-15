#!/usr/bin/env python3
"""Attach conservative language-quality labels to prepared Garhwali data."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/processed/model_ready/language_quality'
REVIEW = ROOT / 'data/processed/review'
LEXICON_GENRES = {'lexicon', 'thematic_lexicon', 'historical_lexicon', 'numeral_lexicon'}
GRAMMAR_SOURCE_GENRES = {
    'historical_linguistics', 'educational_material', 'educational_folk_literature',
    'historical_gazetteer_language_note', 'academic_thesis',
}
DIALECT_REVIEW_GENRES = LEXICON_GENRES | {
    'speech_transcript', 'prompted_speech', 'folk_text', 'folk_literature',
    'phrase_translation', 'sentence', 'idiom_or_proverb', 'social_media',
}
SOURCE_ATTESTED_TRANSCRIPTION_SOURCES = {
    'asjp', 'chan_numerals_garhwali', 'lsi_cldf_garhwali',
    'mamta_southasia_examples', 'mamta_southasia_values', 'sand_garhwali',
}


def script_profile(text):
    counts = {'devanagari': 0, 'latin': 0, 'bengali': 0, 'other_alphabetic': 0}
    for char in text:
        codepoint = ord(char)
        if 0x0900 <= codepoint <= 0x097F:
            counts['devanagari'] += 1
        elif 0x0980 <= codepoint <= 0x09FF:
            counts['bengali'] += 1
        elif 'LATIN' in unicodedata.name(char, ''):
            counts['latin'] += 1
        elif char.isalpha():
            counts['other_alphabetic'] += 1
    present = [name for name, count in counts.items() if count]
    names = {'devanagari': 'Deva', 'latin': 'Latn', 'bengali': 'Beng',
             'other_alphabetic': 'Other'}
    if set(present) == {'devanagari', 'latin'}:
        script = 'Mixed-Deva-Latn'
    elif len(present) > 1:
        script = 'Mixed'
    elif present:
        script = names[present[0]]
    else:
        script = 'Other'
    total = sum(counts.values())
    return {'script': script, 'counts': counts,
            'shares': {name: round(count / total, 6) if total else 0.0
                       for name, count in counts.items()}}


def _values(provenance, field):
    values = []
    for source in provenance:
        value = source.get(field)
        if isinstance(value, list): values.extend(value)
        elif value not in (None, ''): values.append(value)
    return values


def assess_language(text, provenance):
    profile = script_profile(text)
    iso_labels = {str(value).casefold() for value in _values(provenance, 'iso_639_3')}
    language_labels = [str(value).casefold() for value in _values(provenance, 'language')]
    scopes = [str(value).casefold() for value in _values(provenance, 'language_scope')]
    candidates = {str(value).casefold() for value in _values(provenance, 'language_candidates')}
    quality_flags = {str(value).casefold() for value in _values(provenance, 'quality_flags')}
    garhwali_label = ('gbm' in iso_labels or any('garhwali' in value or 'gadwali' in value
                                                for value in language_labels + scopes))
    source_ids = {str(value).casefold() for value in _values(provenance, 'source_id')}
    source_attested_transcription = bool(
        garhwali_label and source_ids & SOURCE_ATTESTED_TRANSCRIPTION_SOURCES
    )
    non_garhwali_label = bool(iso_labels - {'gbm', 'mul'} or any(
        'garhwali' not in value and 'gadwali' not in value for value in language_labels))
    mixed_declared = ('mul' in iso_labels or (garhwali_label and non_garhwali_label) or
                      len(candidates) > 1 or any(
        marker in value for value in scopes
        for marker in (' mixed ', ' and ', 'or_regional', 'does_not_separate')))
    mixed_flagged = any(marker in flag for flag in quality_flags for marker in (
        'language_mixed', 'mixed_languages', 'mixed_garhwali', 'predominantly_english'))
    mixed_scope = mixed_declared or mixed_flagged
    evidence = []
    if garhwali_label: evidence.append('source_garhwali_label')
    if mixed_scope: evidence.append('source_mixed_language_scope')
    reasons = []
    if non_garhwali_label and not garhwali_label:
        status = 'non_garhwali_source_language'; reasons.append('source_language_is_not_garhwali')
    elif mixed_scope:
        status = 'mixed_language_source'
        if mixed_declared: reasons.append('source_declares_mixed_language')
        if mixed_flagged: reasons.append('source_flags_language_mixing')
    elif profile['counts']['bengali']:
        status = 'language_review_required'; reasons.append('bengali_script_under_garhwali_scope')
    elif profile['script'].startswith('Mixed'):
        status = 'mixed_script_review'; reasons.append('multiple_scripts')
    elif profile['script'] == 'Latn' and source_attested_transcription:
        status = 'source_attested_garhwali_transcription'
        evidence.append('source_linguistic_transcription')
    elif profile['script'] == 'Latn':
        status = 'romanized_garhwali_candidate'
        reasons.append('romanized_spelling_unverified')
        if not garhwali_label: reasons.append('latin_text_without_explicit_garhwali_label')
    elif profile['script'] == 'Deva':
        status = 'garhwali_candidate' if garhwali_label else 'garhwali_scope_unverified'
        if not garhwali_label: reasons.append('no_explicit_garhwali_label')
    else:
        status = 'language_review_required'; reasons.append('no_supported_script')
    uncertainty_flags = {
        'source_lineage_missing', 'native_accuracy_unverified', 'language_identity_requires_native_review',
        'unlicensed', 'community_upload',
    }
    garhwali_sources = []
    for source in provenance:
        source_iso = str(source.get('iso_639_3') or '').casefold()
        source_language = str(source.get('language') or '').casefold()
        source_scope = str(source.get('language_scope') or '').casefold()
        if (source_iso == 'gbm' or 'garhwali' in source_language
                or 'gadwali' in source_language or 'garhwali' in source_scope
                or 'gadwali' in source_scope):
            garhwali_sources.append(source)
    clean_garhwali_source = any(
        not ({str(flag).casefold() for flag in source.get('quality_flags') or []}
             & uncertainty_flags)
        for source in garhwali_sources
    )
    uncertain_source = bool(garhwali_sources) and not clean_garhwali_source
    if status in {'garhwali_candidate', 'source_attested_garhwali_transcription'}:
        confidence = 'medium' if uncertain_source else 'high'
    elif status == 'romanized_garhwali_candidate' and garhwali_label:
        confidence = 'medium'
    else:
        confidence = 'low'
    return {'status': status, 'review_required': bool(reasons), 'review_reasons': reasons,
            'confidence': confidence, 'evidence': evidence, 'script_profile': profile}


def language_bucket(language_quality):
    status = language_quality.get('status')
    if status in {
        'garhwali_candidate', 'romanized_garhwali_candidate',
        'source_attested_garhwali_transcription',
    }:
        return 'garhwali_candidate'
    if status == 'mixed_language_source':
        return 'mixed_language'
    if status == 'non_garhwali_source_language':
        return 'non_garhwali_context'
    return 'review'


def infer_genres(provenance):
    explicit = sorted({str(value) for value in _values(provenance, 'genre')})
    subgenres = _metadata_values(provenance, ('cultural_genres',))
    if explicit:
        return {'tags': explicit, 'primary': explicit[0] if len(explicit) == 1 else 'multi_genre',
                'subgenres': subgenres, 'evidence': 'explicit_source_metadata'}
    text = ' '.join(str(source.get('file', '')) + ' ' + str(source.get('source_id', ''))
                    for source in provenance).casefold()
    rules = (
        ('data/extracted/folklore', 'folk_literature'),
        ('garhwali_idioms', 'idiom_or_proverb'),
        ('social_garhwali', 'social_media'),
        ('web_learning', 'language_learning_example'),
        ('cultural_references', 'cultural_reference'),
    )
    tags = sorted({tag for marker, tag in rules if marker in text})
    return {'tags': tags or ['unclassified'], 'primary': tags[0] if len(tags) == 1 else
            ('multi_genre' if tags else 'unclassified'),
            'subgenres': subgenres,
            'evidence': 'inferred_source_rule' if tags else 'unclassified'}


def dialect_evidence(provenance):
    labels = sorted({str(value) for value in _values(provenance, 'dialect')})
    districts = sorted({str(value) for value in _values(provenance, 'district')})
    return {'status': 'explicit_label' if labels else 'unlabeled',
            'dialect_labels': labels, 'geographic_hints': districts,
            'note': 'District is retained as geography and is not treated as a dialect label.'}


def tag_audio_record(row):
    text = row.get('asr_target_clean') or row.get('selected_transcript') or ''
    provenance = [{name: row.get(name) for name in
                   ('language', 'iso_639_3', 'dialect', 'district', 'language_scope')
                   if row.get(name) not in (None, '', [])}]
    speaker_id = str(row.get('speaker_id') or '').strip()
    identified = speaker_id.casefold() not in {'', 'na', 'n/a', 'none', 'unknown'}
    result = dict(row)
    assessment = assess_language(text, provenance)
    if not text and 'source_garhwali_label' in assessment['evidence']:
        assessment.update(status='source_labeled_garhwali_audio', review_required=False,
                          review_reasons=[], confidence='medium')
    result['language_quality'] = assessment
    result['dialect_quality'] = dialect_evidence(provenance)
    result['speaker_metadata'] = {
        'status': 'identified' if identified else 'unidentified',
        'speaker_id': speaker_id if identified else None,
        'gender': row.get('gender'),
        'languages_known': row.get('languages_known') or [],
    }
    return result


def tag_text_record(row):
    result = dict(row)
    provenance = row.get('provenance', [])
    text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    result['language_quality'] = assess_language(text, provenance)
    result['language_bucket'] = language_bucket(result['language_quality'])
    result['genre_quality'] = infer_genres(provenance)
    result['dialect_quality'] = dialect_evidence(provenance)
    return result


def needs_confidence_review(language_quality):
    return language_quality.get('confidence') != 'high'


def needs_dialect_review(row):
    return (row.get('dialect_quality', {}).get('status') != 'explicit_label' and
            bool(set(row.get('genre_quality', {}).get('tags', [])).intersection(DIALECT_REVIEW_GENRES)))


def _metadata_values(provenance, fields):
    values = []
    for source in provenance:
        metadata = source.get('linguistic_metadata') or {}
        for field in fields:
            value = metadata.get(field)
            if isinstance(value, list): values.extend(value)
            elif value not in (None, ''): values.append(value)
    return sorted({str(value) for value in values})


def lexicon_candidate(row):
    genres = set(row.get('genre_quality', {}).get('tags', []))
    if not genres.intersection(LEXICON_GENRES):
        return None
    return {
        'text_sha256': row['text_sha256'],
        'form': row.get('text_model') or row.get('text_clean') or row.get('text'),
        'genres': sorted(genres),
        'glosses': {
            'english': _metadata_values(row.get('provenance', []), ('english_gloss', 'gloss_en')),
            'hindi': _metadata_values(row.get('provenance', []), ('gloss_hi',)),
            'other': _metadata_values(row.get('provenance', []), ('gloss',)),
        },
        'semantic_domains': _metadata_values(row.get('provenance', []), ('semantic_domain',)),
        'dialect_quality': row.get('dialect_quality'),
        'language_quality': row.get('language_quality'),
        'provenance': row.get('provenance', []),
    }


def parallel_entries(row):
    entries = []; seen = set()
    garhwali = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
    for source in row.get('provenance', []):
        metadata = source.get('linguistic_metadata') or {}
        english_values = []
        for field in ('parallel_english', 'english_prompt', 'translation', 'english_alignments'):
            value = metadata.get(field)
            if isinstance(value, list): english_values.extend(value)
            elif value not in (None, ''): english_values.append(value)
        for english in english_values:
            english = ' '.join(str(english).split())
            key = (garhwali, english)
            if not english or key in seen: continue
            seen.add(key)
            digest = hashlib.sha256((garhwali + '\0' + english).encode()).hexdigest()
            entries.append({
                'pair_sha256': digest, 'garhwali': garhwali, 'english': english,
                'text_sha256': row['text_sha256'], 'source_id': source.get('source_id'),
                'source_record_id': source.get('record_id'), 'source_url': source.get('source_url'),
                'rights_status': source.get('rights_status'), 'license_url': source.get('license_url'),
            })
    return entries


def grammar_source_candidate(row):
    genres = set(row.get('genre_quality', {}).get('tags', []))
    if not genres.intersection(GRAMMAR_SOURCE_GENRES):
        return None
    return {
        'text_sha256': row['text_sha256'],
        'text': row.get('text_model') or row.get('text_clean') or row.get('text'),
        'genres': sorted(genres), 'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'), 'provenance': row.get('provenance', []),
    }


def read_jsonl(path):
    with path.open(encoding='utf-8') as source:
        for line in source:
            if line.strip(): yield json.loads(line)


def write_row(handle, row):
    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True); REVIEW.mkdir(parents=True, exist_ok=True)
    text_counts = Counter(); audio_counts = Counter(); pair_keys = set(); identified_speakers = set()
    with (
        (OUT/'text.jsonl').open('w', encoding='utf-8') as text_output,
        (OUT/'text_garhwali_candidates.jsonl').open('w', encoding='utf-8') as garhwali_output,
        (OUT/'text_mixed_language.jsonl').open('w', encoding='utf-8') as mixed_output,
        (OUT/'text_non_garhwali_context.jsonl').open('w', encoding='utf-8') as context_output,
        (OUT/'text_language_review.jsonl').open('w', encoding='utf-8') as unresolved_output,
        (OUT/'lexicon_candidates.jsonl').open('w', encoding='utf-8') as lexicon_output,
        (OUT/'parallel_examples.jsonl').open('w', encoding='utf-8') as parallel_output,
        (OUT/'grammar_source_candidates.jsonl').open('w', encoding='utf-8') as grammar_output,
        (REVIEW/'language_identity_review.jsonl').open('w', encoding='utf-8') as language_review,
        (REVIEW/'language_confidence_review.jsonl').open('w', encoding='utf-8') as confidence_review,
        (REVIEW/'dialect_review.jsonl').open('w', encoding='utf-8') as dialect_review,
        (REVIEW/'genre_review.jsonl').open('w', encoding='utf-8') as genre_review,
    ):
        for row in read_jsonl(ROOT/'data/processed/model_ready/cleaned/text.jsonl'):
            tagged = tag_text_record(row); write_row(text_output, tagged)
            language = tagged['language_quality']; genre = tagged['genre_quality']; dialect = tagged['dialect_quality']
            bucket = tagged['language_bucket']
            bucket_outputs = {'garhwali_candidate': garhwali_output, 'mixed_language': mixed_output,
                              'non_garhwali_context': context_output, 'review': unresolved_output}
            write_row(bucket_outputs[bucket], tagged)
            text_counts['records'] += 1
            text_counts[f'language_bucket:{bucket}'] += 1
            text_counts[f"language:{language['status']}"] += 1
            text_counts[f"language_confidence:{language['confidence']}"] += 1
            text_counts[f"script:{language['script_profile']['script']}"] += 1
            text_counts[f"genre:{genre['primary']}"] += 1
            text_counts[f"dialect:{dialect['status']}"] += 1
            if language['review_required']:
                write_row(language_review, tagged); text_counts['language_review_records'] += 1
            if needs_confidence_review(language):
                write_row(confidence_review, tagged); text_counts['language_confidence_review_records'] += 1
            if needs_dialect_review(tagged):
                write_row(dialect_review, tagged); text_counts['dialect_review_records'] += 1
            if genre['primary'] == 'unclassified':
                write_row(genre_review, tagged); text_counts['genre_review_records'] += 1
            lexicon = lexicon_candidate(tagged)
            if lexicon:
                write_row(lexicon_output, lexicon); text_counts['lexicon_candidates'] += 1
            grammar = grammar_source_candidate(tagged)
            if grammar:
                write_row(grammar_output, grammar); text_counts['grammar_source_candidates'] += 1
            for pair in parallel_entries(tagged):
                key = (pair['garhwali'], pair['english'])
                if key in pair_keys: continue
                pair_keys.add(key); write_row(parallel_output, pair); text_counts['parallel_examples'] += 1

    audio_sources = (
        ('supervised', ROOT/'data/processed/model_ready/cleaned/audio_transcripts.jsonl'),
        ('untranscribed', ROOT/'data/processed/model_ready/audio/untranscribed_all.jsonl'),
    )
    with (
        (OUT/'audio_supervised.jsonl').open('w', encoding='utf-8') as supervised_output,
        (OUT/'audio_untranscribed.jsonl').open('w', encoding='utf-8') as untranscribed_output,
        (REVIEW/'audio_language_review.jsonl').open('w', encoding='utf-8') as audio_review,
    ):
        outputs = {'supervised': supervised_output, 'untranscribed': untranscribed_output}
        for subset, path in audio_sources:
            for row in read_jsonl(path):
                tagged = tag_audio_record(row); write_row(outputs[subset], tagged)
                quality = tagged['language_quality']; speaker = tagged['speaker_metadata']
                audio_counts[f'{subset}_records'] += 1
                audio_counts[f"language:{quality['status']}"] += 1
                audio_counts[f"language_confidence:{quality['confidence']}"] += 1
                audio_counts[f"speaker:{speaker['status']}"] += 1
                if speaker['status'] == 'identified': identified_speakers.add(speaker['speaker_id'])
                audio_counts[f"district:{row.get('district') or 'unknown'}"] += 1
                audio_counts[f"gender:{row.get('gender') or 'unknown'}"] += 1
                if quality['review_required']:
                    write_row(audio_review, tagged); audio_counts['language_review_records'] += 1

    audio_counts['unique_identified_speakers'] = len(identified_speakers)

    report = {'text': dict(sorted(text_counts.items())),
              'audio': dict(sorted(audio_counts.items())),
              'method_notes': {
                  'language': 'Source labels and Unicode scripts only; Hindi/Garhwali separation is not guessed from shared Devanagari vocabulary.',
                  'dialect': 'Only explicit dialect labels are accepted; district is retained separately as a geographic hint.',
                  'genre': 'Explicit source metadata is preferred, with narrow path-based fallbacks for older extracted files.',
              }}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__': main()
