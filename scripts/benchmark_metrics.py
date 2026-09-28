"""Dependency-free, versioned metrics for GarhwaliBench QA and summaries."""

from __future__ import annotations

import unicodedata
from collections import Counter


NORMALIZER_ID = 'garhwali-benchmark-nfc-casefold-punctuation-space-v1'
TOKENIZER_ID = 'unicode-whitespace-tokens-v1'


def normalize_metric_text(value: object) -> str:
    """Normalize spelling surface for scoring without transliteration or stemming."""
    text = unicodedata.normalize('NFC', '' if value is None else str(value)).casefold()
    text = ''.join(
        ' ' if unicodedata.category(char)[0] in {'P', 'S'} else char
        for char in text
    )
    return ' '.join(text.split())


def _inputs(predictions, reference_sets):
    predictions = list(predictions)
    reference_sets = list(reference_sets)
    if not predictions:
        raise ValueError('at least one record is required')
    if len(predictions) != len(reference_sets):
        raise ValueError('predictions and references must contain the same number of records')

    prepared = []
    empty_reference_alternatives = 0
    reference_count = 0
    multi_reference_records = 0
    for index, references in enumerate(reference_sets):
        alternatives = [references] if isinstance(references, str) else list(references)
        normalized = [normalize_metric_text(item) for item in alternatives]
        valid = [item for item in normalized if item]
        empty_reference_alternatives += len(normalized) - len(valid)
        if not valid:
            raise ValueError(f'record {index} requires a non-empty reference')
        reference_count += len(valid)
        multi_reference_records += int(len(valid) > 1)
        prepared.append((normalize_metric_text(predictions[index]), valid))
    return prepared, reference_count, multi_reference_records, empty_reference_alternatives


def _token_f1(prediction: str, reference: str) -> float:
    predicted_tokens = prediction.split()
    reference_tokens = reference.split()
    if not predicted_tokens or not reference_tokens:
        return 0.0
    overlap = sum((Counter(predicted_tokens) & Counter(reference_tokens)).values())
    if not overlap:
        return 0.0
    precision = overlap / len(predicted_tokens)
    recall = overlap / len(reference_tokens)
    return 2 * precision * recall / (precision + recall)


def _base_result(metric_id, prepared, reference_count, multi_reference_records,
                 empty_reference_alternatives):
    return {
        'metric_id': metric_id,
        'normalizer_id': NORMALIZER_ID,
        'tokenizer_id': TOKENIZER_ID,
        'aggregation': 'macro_mean_of_per_record_max_over_references',
        'empty_reference_policy': 'reject_record_without_nonempty_reference',
        'empty_prediction_policy': 'score_zero_and_include_in_denominator',
        'requested_records': len(prepared),
        'scored_records': len(prepared),
        'reference_count': reference_count,
        'multi_reference_records': multi_reference_records,
        'empty_reference_alternatives': empty_reference_alternatives,
        'empty_prediction_records': sum(not prediction for prediction, _ in prepared),
    }


def score_qa_answers(predictions, references) -> dict:
    """Return macro exact match and whitespace-token F1, max over references."""
    prepared, reference_count, multi_count, empty_count = _inputs(predictions, references)
    exact = []
    f1 = []
    for prediction, alternatives in prepared:
        exact.append(float(any(prediction == reference for reference in alternatives)))
        f1.append(max(_token_f1(prediction, reference) for reference in alternatives))
    result = _base_result(
        'garhwali-qa-em-token-f1-v1', prepared, reference_count, multi_count, empty_count,
    )
    result.update({
        'exact_match': round(sum(exact) / len(exact), 8),
        'token_f1': round(sum(f1) / len(f1), 8),
    })
    return result


def _lcs_length(left: list[str], right: list[str]) -> int:
    if len(left) > len(right):
        left, right = right, left
    previous = [0] * (len(left) + 1)
    for right_token in right:
        current = [0]
        for index, left_token in enumerate(left, start=1):
            current.append(
                previous[index - 1] + 1
                if left_token == right_token
                else max(previous[index], current[-1])
            )
        previous = current
    return previous[-1]


def _rouge_l_f1(prediction: str, reference: str) -> float:
    predicted_tokens = prediction.split()
    reference_tokens = reference.split()
    if not predicted_tokens or not reference_tokens:
        return 0.0
    common = _lcs_length(predicted_tokens, reference_tokens)
    if not common:
        return 0.0
    precision = common / len(predicted_tokens)
    recall = common / len(reference_tokens)
    return 2 * precision * recall / (precision + recall)


def score_rouge_l(predictions, references) -> dict:
    """Return macro ROUGE-L F1, with the best reference chosen per record."""
    prepared, reference_count, multi_count, empty_count = _inputs(predictions, references)
    scores = [
        max(_rouge_l_f1(prediction, reference) for reference in alternatives)
        for prediction, alternatives in prepared
    ]
    result = _base_result(
        'garhwali-rouge-l-f1-v1', prepared, reference_count, multi_count, empty_count,
    )
    result['rouge_l_f1'] = round(sum(scores) / len(scores), 8)
    return result
