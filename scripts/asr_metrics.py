#!/usr/bin/env python3
"""Dependency-free normalization and WER/CER metrics for ASR evaluation."""
import re
import unicodedata
from collections import defaultdict


def normalize(text):
    value = unicodedata.normalize('NFC', text).casefold()
    value = ''.join(' ' if unicodedata.category(char).startswith(('P', 'S')) else char for char in value)
    return re.sub(r'\s+', ' ', value).strip()


def edit_distance(reference, hypothesis):
    previous = list(range(len(hypothesis) + 1))
    for index, left in enumerate(reference, 1):
        current = [index]
        for other, right in enumerate(hypothesis, 1):
            current.append(min(current[-1] + 1, previous[other] + 1,
                               previous[other - 1] + (left != right)))
        previous = current
    return previous[-1]


def score(reference, hypothesis):
    ref = normalize(reference); hyp = normalize(hypothesis)
    ref_words, hyp_words = ref.split(), hyp.split()
    word_errors = edit_distance(ref_words, hyp_words)
    character_errors = edit_distance(list(ref.replace(' ', '')), list(hyp.replace(' ', '')))
    reference_characters = len(ref.replace(' ', ''))
    return {
        'word_errors': word_errors, 'reference_words': len(ref_words),
        'wer': word_errors / max(1, len(ref_words)),
        'character_errors': character_errors, 'reference_characters': reference_characters,
        'cer': character_errors / max(1, reference_characters),
    }


def score_corpus(references, hypotheses, record_ids=None):
    """Compute corpus WER/CER from summed edits and explicit reference coverage.

    Empty hypotheses remain scored as deletions. References that normalize to
    no words or characters are listed as excluded because they have no valid
    error-rate denominator.
    """
    references = list(references)
    hypotheses = list(hypotheses)
    if not references:
        raise ValueError('at least one record is required')
    if len(references) != len(hypotheses):
        raise ValueError('references and hypotheses must contain the same number of records')
    if record_ids is None:
        record_ids = [str(index) for index in range(len(references))]
    else:
        record_ids = [str(record_id) for record_id in record_ids]
    if len(record_ids) != len(references):
        raise ValueError('record_ids must contain one ID per record')

    totals = {
        'word_errors': 0,
        'reference_words': 0,
        'character_errors': 0,
        'reference_characters': 0,
    }
    excluded = []
    empty_hypotheses = 0
    per_record_scores = []
    for record_id, reference, hypothesis in zip(record_ids, references, hypotheses):
        result = score(reference, hypothesis)
        if result['reference_words'] == 0 or result['reference_characters'] == 0:
            excluded.append({
                'record_id': record_id,
                'reason': 'empty_reference_after_normalization',
            })
            continue
        for key in totals:
            totals[key] += result[key]
        empty_hypotheses += not normalize(hypothesis)
        per_record_scores.append({
            'record_id': record_id,
            **result,
        })

    if not totals['reference_words'] or not totals['reference_characters']:
        raise ValueError('no records with non-empty normalized references to score')
    return {
        'metric_ids': ['garhwali-asr-corpus-wer-v1', 'garhwali-asr-corpus-cer-v1'],
        'normalizer_id': 'asr-nfc-casefold-punctuation-symbol-space-v1',
        'tokenizer_id': 'unicode-whitespace-words-and-codepoints-no-space-v1',
        'aggregation': 'micro_from_summed_edit_counts_and_reference_units',
        'empty_reference_policy': 'exclude_and_list_record_id',
        'empty_hypothesis_policy': 'include_as_deletions',
        'requested_records': len(references),
        'scored_records': len(references) - len(excluded),
        'empty_hypothesis_records': empty_hypotheses,
        'excluded_records': excluded,
        'per_record_scores': per_record_scores,
        **totals,
        'wer': totals['word_errors'] / totals['reference_words'],
        'cer': totals['character_errors'] / totals['reference_characters'],
    }


def summarize_slices(rows, scores):
    """Report micro WER/CER for metadata slices, without inventing labels."""
    rows = list(rows)
    scores = list(scores)
    if len(rows) != len(scores):
        raise ValueError('rows and scores must contain the same number of records')

    grouped = {
        'duration_seconds': defaultdict(list),
        'reference_word_count': defaultdict(list),
        'speaker_id': defaultdict(list),
    }
    has_speaker_ids = False
    has_audio_quality = all(
        'audio_quality_status' in row or 'audio_quality_flag' in row for row in rows
    ) if rows else False
    for row, score_row in zip(rows, scores):
        duration = float(row.get('duration_seconds', 0))
        duration_label = '<3s' if duration < 3 else '3-8s' if duration < 8 else '8-15s' if duration < 15 else '15s+'
        words = len(normalize(row['asr_target_clean']).split())
        word_label = '1-10' if words <= 10 else '11-25' if words <= 25 else '26+'
        grouped['duration_seconds'][duration_label].append(score_row)
        grouped['reference_word_count'][word_label].append(score_row)
        speaker = row.get('speaker_id')
        if speaker and str(speaker).strip().casefold() not in {'na', 'unknown', 'null'}:
            has_speaker_ids = True
            grouped['speaker_id'][str(speaker)].append(score_row)

    def summarize(groups):
        result = {}
        for label in sorted(groups):
            values = groups[label]
            word_errors = sum(row['word_errors'] for row in values)
            reference_words = sum(row['reference_words'] for row in values)
            character_errors = sum(row['character_errors'] for row in values)
            reference_characters = sum(row['reference_characters'] for row in values)
            result[label] = {
                'records': len(values),
                'word_errors': word_errors,
                'reference_words': reference_words,
                'wer': word_errors / max(1, reference_words),
                'character_errors': character_errors,
                'reference_characters': reference_characters,
                'cer': character_errors / max(1, reference_characters),
            }
        return result

    slices = {
        'duration_seconds': summarize(grouped['duration_seconds']),
        'reference_word_count': summarize(grouped['reference_word_count']),
        'speaker_id': summarize(grouped['speaker_id']) if has_speaker_ids else None,
        'district': None,
        'audio_quality': {
            'available': has_audio_quality,
            'field': 'audio_quality_status or audio_quality_flag' if has_audio_quality else None,
            'note': None if has_audio_quality else 'No per-record audio-quality annotation is present in this manifest.',
        },
    }
    if rows and all('district' in row for row in rows):
        district_groups = defaultdict(list)
        for row, score_row in zip(rows, scores):
            district_groups[str(row['district'])].append(score_row)
        slices['district'] = summarize(district_groups)
    if has_audio_quality:
        quality_groups = defaultdict(list)
        for row, score_row in zip(rows, scores):
            quality = row.get('audio_quality_status', row.get('audio_quality_flag'))
            quality_groups[str(quality)].append(score_row)
        slices['audio_quality'] = {
            'available': True,
            'field': 'audio_quality_status' if any('audio_quality_status' in row for row in rows) else 'audio_quality_flag',
            'groups': summarize(quality_groups),
            'note': 'Slices describe the supplied field; they do not establish acoustic or linguistic validity.',
        }
    return slices
