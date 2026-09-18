#!/usr/bin/env python3
"""Create reversible, model-assisted text-cleanup proposals.

Original and current text are retained. Suggestions are never applied by this
script, and every source record stays active in the complete experimental view.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/language_quality/text.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/text_cleanup'
MODEL_ID = 'ai4bharat/IndicBERTv2-MLM-only'
MODEL_REVISION = '8598f13fe52443bc3fc054fcd665944560145b5c'
MODEL_PATH = (
    ROOT / '.cache/huggingface/hub/models--ai4bharat--IndicBERTv2-MLM-only'
    / 'snapshots' / MODEL_REVISION
)
INVISIBLE = dict.fromkeys(map(ord, '\u200b\u200c\u200d\u2060\ufeff'), None)
DEVANAGARI_TOKEN = re.compile(r'[\u0900-\u097F]+')
REPEATED_PUNCTUATION = re.compile(r'([^\w\s])\1{3,}', re.UNICODE)
DIALECT_PRIORITY_GENRES = {
    'folk_text', 'folk_literature', 'idiom_or_proverb', 'lexicon',
    'thematic_lexicon', 'historical_lexicon', 'social_media',
    'speech_transcript', 'prompted_speech', 'sentence',
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        for line in source:
            if line.strip():
                yield json.loads(line)


def mechanical_cleanup(text):
    """Return a conservative proposal plus a complete change trace."""
    proposed = text
    changes = []
    normalized = unicodedata.normalize('NFC', proposed)
    if normalized != proposed:
        proposed = normalized
        changes.append('normalized_unicode_nfc')
    without_invisible = proposed.translate(INVISIBLE)
    if without_invisible != proposed:
        proposed = without_invisible
        changes.append('removed_invisible_characters')
    collapsed = ' '.join(proposed.split())
    if collapsed != proposed:
        proposed = collapsed
        changes.append('collapsed_whitespace')
    limited = REPEATED_PUNCTUATION.sub(lambda match: match.group(1) * 3, proposed)
    if limited != proposed:
        proposed = limited
        changes.append('limited_repeated_punctuation')
    return {'proposed_text': proposed, 'changes': changes}


def devanagari_tokens(text):
    return DEVANAGARI_TOKEN.findall(unicodedata.normalize('NFC', text))


def build_token_frequencies(rows):
    frequencies = Counter()
    for row in rows:
        language = row.get('language_quality', {})
        if (row.get('split') in {None, 'train'}
                and row.get('language_bucket') == 'garhwali_candidate'
                and language.get('confidence') in {'high', 'medium'}):
            frequencies.update(devanagari_tokens(row.get('text_model') or row.get('text_clean')
                                                 or row.get('text') or ''))
    return dict(frequencies)


def deletion_variants(token):
    return {token[:index] + token[index + 1:] for index in range(len(token))}


def build_deletion_index(frequencies, minimum_frequency=20):
    index = defaultdict(set)
    for token, frequency in frequencies.items():
        if frequency < minimum_frequency or len(token) < 3:
            continue
        for variant in deletion_variants(token) | {token}:
            index[variant].add(token)
    return {variant: tuple(sorted(tokens)) for variant, tokens in index.items()}


def edit_distance(left, right):
    previous = list(range(len(right) + 1))
    for row_index, left_char in enumerate(left, 1):
        current = [row_index]
        for column_index, right_char in enumerate(right, 1):
            current.append(min(
                current[-1] + 1,
                previous[column_index] + 1,
                previous[column_index - 1] + (left_char != right_char),
            ))
        previous = current
    return previous[-1]


def spelling_candidates(text, frequencies, deletion_index, max_candidates=20):
    proposals = []
    seen = set()
    for observed in devanagari_tokens(text):
        observed_frequency = frequencies.get(observed, 0)
        if observed in seen or observed_frequency > 2 or len(observed) < 3:
            continue
        seen.add(observed)
        possible = set(deletion_index.get(observed, ()))
        for variant in deletion_variants(observed):
            possible.update(deletion_index.get(variant, ()))
        ranked = sorted(
            (
                (edit_distance(observed, candidate), -frequencies[candidate], candidate)
                for candidate in possible if candidate != observed
            ),
        )
        if not ranked:
            continue
        distance, negative_frequency, candidate = ranked[0]
        candidate_frequency = -negative_frequency
        if distance != 1 or candidate_frequency < max(5, 10 * max(1, observed_frequency)):
            continue
        proposals.append({
            'observed': observed,
            'candidate': candidate,
            'edit_distance': distance,
            'observed_corpus_frequency': observed_frequency,
            'candidate_corpus_frequency': candidate_frequency,
            'evidence': 'one_edit_from_high_frequency_garhwali_corpus_form',
            'confidence': 'low',
            'status': 'proposal_only',
        })
        if len(proposals) >= max_candidates:
            break
    return proposals


def language_signal(row, model_loss=None, high_loss_threshold=None):
    bucket = row.get('language_bucket', 'review')
    source_confidence = row.get('language_quality', {}).get('confidence', 'low')
    result = {
        'source_bucket': bucket,
        'source_confidence': source_confidence,
        'model_metric': 'deterministic_masked_token_cross_entropy',
        'model_loss': model_loss,
        'high_loss_threshold': high_loss_threshold,
        'decision': 'retain_source_label',
    }
    if model_loss is None:
        result['status'] = 'not_model_scored'
    elif high_loss_threshold is not None and model_loss >= high_loss_threshold:
        result['status'] = 'model_source_disagreement'
    else:
        result['status'] = 'no_model_disagreement'
    if bucket in {'mixed_language', 'review'} and source_confidence == 'low':
        result['hindi_garhwali_status'] = 'ambiguity_priority'
    else:
        result['hindi_garhwali_status'] = 'no_automatic_language_correction'
    return result


def needs_dialect_priority(row):
    genres = set(row.get('genre_quality', {}).get('tags', []))
    return (row.get('dialect_quality', {}).get('status') != 'explicit_label'
            and bool(genres & DIALECT_PRIORITY_GENRES))


def source_quality_flags(row):
    flags = set(row.get('cleanup_review_flags', [])) | set(row.get('deep_cleanup_flags', []))
    for source in row.get('provenance', []):
        flags.update(source.get('quality_flags') or [])
    return sorted(flags)


def build_proposal(row, frequencies, deletion_index, model_loss=None,
                   high_loss_threshold=None):
    original = row.get('text') or ''
    current = row.get('text_model') or row.get('text_clean') or original
    mechanical = mechanical_cleanup(current)
    spellings = spelling_candidates(current, frequencies, deletion_index)
    language = language_signal(row, model_loss, high_loss_threshold)
    flags = source_quality_flags(row)
    types = []
    if mechanical['changes']:
        types.append('mechanical_cleanup')
    if spellings:
        types.append('spelling_candidates')
    if language['status'] == 'model_source_disagreement':
        types.append('language_model_disagreement')
    if language['hindi_garhwali_status'] == 'ambiguity_priority':
        types.append('hindi_garhwali_ambiguity')
    dialect_priority = needs_dialect_priority(row)
    if dialect_priority:
        types.append('dialect_evidence_priority')
    if any('ocr' in flag.casefold() for flag in flags):
        types.append('ocr_source_priority')
    return {
        'text_sha256': row.get('text_sha256'),
        'split': row.get('split'),
        'text_original': original,
        'text_current': current,
        'proposed_text': mechanical['proposed_text'],
        'mechanical_changes': mechanical['changes'],
        'spelling_candidates': spellings,
        'language_signal': language,
        'dialect_priority': dialect_priority,
        'proposal_types': sorted(set(types)),
        'source_quality_flags': flags,
        'language_bucket': row.get('language_bucket'),
        'language_quality': row.get('language_quality'),
        'dialect_quality': row.get('dialect_quality'),
        'genre_quality': row.get('genre_quality'),
        'provenance': row.get('provenance', []),
        'application_status': 'proposal_only',
        'active_for_experiment': True,
        'original_preserved': True,
    }


def select_model_rows(rows, preliminary, limit):
    if limit <= 0:
        return []
    ranked = []
    for row, proposal in zip(rows, preliminary):
        language = row.get('language_quality', {})
        score = (
            4 * bool(proposal['mechanical_changes'])
            + 4 * bool(proposal['spelling_candidates'])
            + 3 * (language.get('confidence') == 'low')
            + 2 * (row.get('language_bucket') in {'mixed_language', 'review'})
            + bool(proposal['dialect_priority'])
        )
        digest = hashlib.sha256(str(row.get('text_sha256', '')).encode()).hexdigest()
        ranked.append((-score, digest, row))
    return [item[2] for item in sorted(ranked)[:limit]]


def select_mask_positions(token_ids, attention_mask, special_ids, record_key, rate, seed):
    candidates = [
        index for index, (token_id, attended) in enumerate(zip(token_ids, attention_mask))
        if attended and token_id not in special_ids
    ]
    if not candidates:
        return []
    scored = []
    for index in candidates:
        digest = hashlib.sha256(f'{seed}:{record_key}:{index}'.encode()).digest()
        score = int.from_bytes(digest[:8], 'big') / 2**64
        scored.append((score, index))
    return sorted([index for score, index in scored if score < rate] or [min(scored)[1]])


def score_with_masked_lm(rows, model_path=MODEL_PATH, max_length=256, mask_rate=0.15,
                         seed=29, device='auto', adapter_path=None):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    import torch.nn.functional as functional
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    if not rows:
        return {}, {'scored_records': 0}
    if device == 'auto':
        if torch.cuda.is_available():
            device = 'cuda'
        else:
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    tokenizer = AutoTokenizer.from_pretrained(
        model_path, local_files_only=True, fix_mistral_regex=True,
    )
    model = AutoModelForMaskedLM.from_pretrained(model_path, local_files_only=True).to(device)
    if adapter_path:
        from peft import PeftModel
        model = PeftModel.from_pretrained(
            model, adapter_path, local_files_only=True,
        ).to(device)
    model.eval()
    special_ids = set(tokenizer.all_special_ids)
    scores = {}
    masked_tokens = 0
    truncated = 0
    started = time.monotonic()
    with torch.no_grad():
        for row in rows:
            text = row.get('text_model') or row.get('text_clean') or row.get('text') or ''
            full_ids = tokenizer(text, add_special_tokens=True)['input_ids']
            truncated += len(full_ids) > max_length
            encoded = tokenizer(text, add_special_tokens=True, max_length=max_length,
                                truncation=True, return_tensors='pt')
            positions = select_mask_positions(
                encoded['input_ids'][0].tolist(), encoded['attention_mask'][0].tolist(),
                special_ids, row.get('text_sha256', ''), mask_rate, seed,
            )
            if not positions:
                continue
            labels = encoded['input_ids'][0, positions].to(device)
            encoded['input_ids'][0, positions] = tokenizer.mask_token_id
            inputs = {name: value.to(device) for name, value in encoded.items()}
            hidden = model.bert(**inputs).last_hidden_state[0, positions]
            logits = model.cls(hidden)
            loss = functional.cross_entropy(logits, labels, reduction='mean')
            scores[row.get('text_sha256')] = round(float(loss.cpu()), 6)
            masked_tokens += len(positions)
    metadata = {
        'model_id': MODEL_ID,
        'revision': MODEL_REVISION,
        'scored_records': len(scores),
        'masked_tokens': masked_tokens,
        'mask_rate': mask_rate,
        'seed': seed,
        'max_length': max_length,
        'truncated_records': truncated,
        'device': device,
        'adapter_path': str(adapter_path) if adapter_path else None,
        'elapsed_seconds': round(time.monotonic() - started, 3),
    }
    return scores, metadata


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def run(input_path=INPUT, output_dir=OUTPUT, model_scores=None, model_records=0,
        device='auto', model_path=MODEL_PATH):
    rows = list(read_jsonl(input_path))
    frequencies = build_token_frequencies(rows)
    deletion_index = build_deletion_index(frequencies)
    preliminary = [build_proposal(row, frequencies, deletion_index) for row in rows]
    model_metadata = {'scored_records': len(model_scores or {}), 'source': 'provided'}
    if model_scores is None:
        selected = select_model_rows(rows, preliminary, min(model_records, len(rows)))
        model_scores, model_metadata = score_with_masked_lm(
            selected, model_path=model_path, device=device,
        )
    threshold = percentile(list(model_scores.values()), 0.9)
    proposals = [
        build_proposal(row, frequencies, deletion_index, model_scores.get(row.get('text_sha256')),
                       threshold)
        for row in rows
    ]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    proposal_path = output_dir / 'proposals.jsonl'
    priority_path = output_dir / 'priority.jsonl'
    counts = Counter()
    with proposal_path.open('w', encoding='utf-8') as all_output, \
            priority_path.open('w', encoding='utf-8') as priority_output:
        for proposal in proposals:
            line = json.dumps(proposal, ensure_ascii=False, sort_keys=True) + '\n'
            all_output.write(line)
            counts['total'] += 1
            counts['active_for_experiment'] += bool(proposal['active_for_experiment'])
            counts['with_any_proposal'] += bool(proposal['proposal_types'])
            counts['with_mechanical_change'] += bool(proposal['mechanical_changes'])
            counts['with_spelling_candidates'] += bool(proposal['spelling_candidates'])
            counts['spelling_candidate_pairs'] += len(proposal['spelling_candidates'])
            counts['model_scored'] += proposal['language_signal']['model_loss'] is not None
            counts['model_source_disagreement'] += (
                proposal['language_signal']['status'] == 'model_source_disagreement')
            counts['hindi_garhwali_ambiguity'] += (
                proposal['language_signal']['hindi_garhwali_status'] == 'ambiguity_priority')
            counts['dialect_priority'] += proposal['dialect_priority']
            counts['ocr_source_priority'] += 'ocr_source_priority' in proposal['proposal_types']
            if proposal['proposal_types']:
                priority_output.write(line)
    counts['excluded'] = counts['total'] - counts['active_for_experiment']
    report = {
        'run_id': 'garhwali-model-assisted-text-cleanup-v0.1',
        'records': dict(sorted(counts.items())),
        'vocabulary': {
            'trusted_devanagari_types': len(frequencies),
            'high_frequency_candidate_types': sum(value >= 20 for value in frequencies.values()),
        },
        'model': model_metadata,
        'model_high_loss_threshold_p90': threshold,
        'policy': {
            'application': 'proposal_only',
            'originals_preserved': True,
            'all_records_active_for_experiment': True,
            'automatic_hindi_garhwali_relabeling': False,
            'automatic_dialect_inference': False,
            'spelling_variants_preserved': True,
        },
        'artifacts': {
            'all_proposals': str(proposal_path.relative_to(ROOT)) if proposal_path.is_relative_to(ROOT) else str(proposal_path),
            'priority_proposals': str(priority_path.relative_to(ROOT)) if priority_path.is_relative_to(ROOT) else str(priority_path),
        },
    }
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    parser.add_argument('--model-records', type=int, default=4096)
    parser.add_argument('--device', choices=('auto', 'cuda', 'mps', 'cpu'), default='auto')
    parser.add_argument('--model-path', type=Path, default=MODEL_PATH)
    args = parser.parse_args()
    print(json.dumps(run(args.input, args.output_dir, model_records=args.model_records,
                         device=args.device, model_path=args.model_path),
                     ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
