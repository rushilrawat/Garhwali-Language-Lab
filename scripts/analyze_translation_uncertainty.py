#!/usr/bin/env python3
"""Paired record-bootstrap uncertainty for saved Garhwali translation predictions."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
import math
from collections import Counter
from pathlib import Path

from evaluation_run_manifest import write_run_artifacts
from run_translation_baseline import (
    character_ngrams,
    metric_summary,
    normalize,
    word_ngrams,
)


ROOT = Path(__file__).resolve().parents[1]


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _record_components(reference: str, hypothesis: str) -> dict:
    reference_words = normalize(reference).split()
    hypothesis_words = normalize(hypothesis).split()
    bleu_matches = []
    bleu_possible = []
    for order in range(1, 5):
        reference_counts = word_ngrams(reference, order)
        hypothesis_counts = word_ngrams(hypothesis, order)
        bleu_matches.append(sum(
            min(count, reference_counts[gram])
            for gram, count in hypothesis_counts.items()
        ))
        bleu_possible.append(sum(hypothesis_counts.values()))

    chrf_matches = []
    chrf_reference = []
    chrf_hypothesis = []
    for order in range(1, 7):
        reference_counts = character_ngrams(reference, order)
        hypothesis_counts = character_ngrams(hypothesis, order)
        chrf_matches.append(sum(
            min(count, reference_counts[gram])
            for gram, count in hypothesis_counts.items()
        ))
        chrf_reference.append(sum(reference_counts.values()))
        chrf_hypothesis.append(sum(hypothesis_counts.values()))
    return {
        'bleu_matches': bleu_matches,
        'bleu_possible': bleu_possible,
        'reference_words': len(reference_words),
        'hypothesis_words': len(hypothesis_words),
        'chrf_matches': chrf_matches,
        'chrf_reference': chrf_reference,
        'chrf_hypothesis': chrf_hypothesis,
        'exact_match': normalize(reference) == normalize(hypothesis),
    }


def _score_resample(indices, components: list[dict]) -> dict:
    sampled_counts = Counter(indices)
    count = len(indices)
    bleu_matches = [0] * 4
    bleu_possible = [0] * 4
    reference_words = hypothesis_words = 0
    chrf_matches = [0] * 6
    chrf_reference = [0] * 6
    chrf_hypothesis = [0] * 6
    exact_matches = 0
    for index, weight in sampled_counts.items():
        row = components[index]
        for order in range(4):
            bleu_matches[order] += weight * row['bleu_matches'][order]
            bleu_possible[order] += weight * row['bleu_possible'][order]
        reference_words += weight * row['reference_words']
        hypothesis_words += weight * row['hypothesis_words']
        for order in range(6):
            chrf_matches[order] += weight * row['chrf_matches'][order]
            chrf_reference[order] += weight * row['chrf_reference'][order]
            chrf_hypothesis[order] += weight * row['chrf_hypothesis'][order]
        exact_matches += weight * int(row['exact_match'])

    if reference_words == 0 or hypothesis_words == 0:
        bleu = 0.0
    else:
        precisions = [
            (matches + 1) / (possible + 1)
            for matches, possible in zip(bleu_matches, bleu_possible)
        ]
        geometric_mean = math.exp(sum(math.log(value) for value in precisions) / 4)
        brevity = 1.0 if hypothesis_words > reference_words else math.exp(
            1 - reference_words / hypothesis_words
        )
        bleu = round(brevity * geometric_mean, 8)
    chrf_scores = []
    for matches, ref_total, hyp_total in zip(chrf_matches, chrf_reference, chrf_hypothesis):
        precision = matches / max(1, hyp_total)
        recall = matches / max(1, ref_total)
        denominator = 4 * precision + recall
        chrf_scores.append(5 * precision * recall / denominator if denominator else 0.0)
    return {
        'corpus_bleu_smoothed': bleu,
        'corpus_chrf2': round(sum(chrf_scores) / 6, 8),
        'exact_match': round(exact_matches / count, 8),
    }


def analyze_rows(
    rows: list[dict],
    *,
    baseline_field: str,
    candidate_field: str,
    reference_field: str = 'reference',
    record_id_field: str = 'record_id',
    replicates: int = 2000,
    seed: int = 1729,
    confidence_level: float = 0.95,
) -> tuple[dict, list[dict]]:
    rows = list(rows)
    if not rows:
        raise ValueError('at least one paired prediction row is required')
    if replicates < 1:
        raise ValueError('replicates must be positive')
    if not 0 < confidence_level < 1:
        raise ValueError('confidence_level must be between zero and one')
    if not baseline_field or not candidate_field or not reference_field or not record_id_field:
        raise ValueError('field names must be non-empty')

    record_ids = []
    references = []
    baseline = []
    candidate = []
    paired = []
    for index, row in enumerate(rows):
        record_id = str(row.get(record_id_field) or '')
        if not record_id:
            raise ValueError(f'row {index} requires a non-empty {record_id_field}')
        if not isinstance(row.get(reference_field), str) or not normalize(row[reference_field]):
            raise ValueError(f'{record_id}: requires a non-empty reference')
        if not isinstance(row.get(baseline_field), str):
            raise ValueError(f'{record_id}: {baseline_field} must be a string')
        if not isinstance(row.get(candidate_field), str):
            raise ValueError(f'{record_id}: {candidate_field} must be a string')
        record_ids.append(record_id)
        references.append(row[reference_field])
        baseline.append(row[baseline_field])
        candidate.append(row[candidate_field])
        reference_normalized = normalize(row[reference_field])
        baseline_exact = normalize(row[baseline_field]) == reference_normalized
        candidate_exact = normalize(row[candidate_field]) == reference_normalized
        paired.append({
            'record_id': record_id,
            'baseline_exact_match': baseline_exact,
            'candidate_exact_match': candidate_exact,
            'candidate_minus_baseline_exact_match': int(candidate_exact) - int(baseline_exact),
        })
    if len(record_ids) != len(set(record_ids)):
        raise ValueError('duplicate record_id values in paired predictions')

    baseline_metrics = metric_summary(references, baseline)
    candidate_metrics = metric_summary(references, candidate)
    metric_names = ('corpus_bleu_smoothed', 'corpus_chrf2', 'exact_match')
    baseline_components = [
        _record_components(reference, hypothesis)
        for reference, hypothesis in zip(references, baseline)
    ]
    candidate_components = [
        _record_components(reference, hypothesis)
        for reference, hypothesis in zip(references, candidate)
    ]
    rng = random.Random(seed)
    deltas = {name: [] for name in metric_names}
    count = len(rows)
    for _ in range(replicates):
        sampled_indices = [rng.randrange(count) for _ in range(count)]
        base_scores = _score_resample(sampled_indices, baseline_components)
        candidate_scores = _score_resample(sampled_indices, candidate_components)
        for name in metric_names:
            deltas[name].append(candidate_scores[name] - base_scores[name])

    alpha = (1 - confidence_level) / 2
    paired_deltas = {
        name: {
            'baseline': baseline_metrics[name],
            'candidate': candidate_metrics[name],
            'candidate_minus_baseline': round(candidate_metrics[name] - baseline_metrics[name], 8),
            'confidence_interval': [
                round(_percentile(samples, alpha), 8),
                round(_percentile(samples, 1 - alpha), 8),
            ],
        }
        for name, samples in deltas.items()
    }
    exact_outcomes = [row['candidate_minus_baseline_exact_match'] for row in paired]
    report = {
        'schema_version': 1,
        'analysis': 'paired_translation_record_bootstrap_v1',
        'evaluation_records': count,
        'selected_record_ids': record_ids,
        'metric_ids': ['garhwali-custom-add1-bleu-v1', 'garhwali-custom-chrf2-v1'],
        'paired_deltas': paired_deltas,
        'exact_match_outcomes': {
            'candidate_better': sum(value > 0 for value in exact_outcomes),
            'tie': sum(value == 0 for value in exact_outcomes),
            'candidate_worse': sum(value < 0 for value in exact_outcomes),
        },
        'bootstrap': {
            'method': 'paired_record_resampling_with_replacement',
            'replicates': replicates,
            'seed': seed,
            'confidence_level': confidence_level,
            'quantile_method': 'linear_interpolation_on_sorted_bootstrap_deltas',
        },
        'limitations': [
            'Intervals resample records, not source-document clusters; source-group IDs are unavailable here.',
            'This is development-set uncertainty for diagnostics and does not establish independent accuracy.',
            'Metrics and references do not validate Garhwali linguistic correctness.',
        ],
    }
    return report, paired


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{line_number}: expected a JSON object')
            rows.append(row)
    return rows


def run(
    *,
    predictions_path: Path,
    output_dir: Path,
    baseline_field: str = 'copy_hypothesis',
    candidate_field: str = 'translation_memory_hypothesis',
    reference_field: str = 'reference',
    replicates: int = 2000,
    seed: int = 1729,
    confidence_level: float = 0.95,
    git_root: Path | None = ROOT,
) -> dict:
    predictions_path = Path(predictions_path)
    source_bytes = predictions_path.read_bytes()
    rows = read_jsonl(predictions_path)
    report, paired = analyze_rows(
        rows,
        baseline_field=baseline_field,
        candidate_field=candidate_field,
        reference_field=reference_field,
        replicates=replicates,
        seed=seed,
        confidence_level=confidence_level,
    )
    selected_bytes = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in rows
    ).encode('utf-8')
    report.update({
        'run_id': f"translation-bootstrap-{hashlib.sha256(source_bytes).hexdigest()[:12]}",
        'task': 'translation',
        'evaluation_split': 'dev',
        'claim_limit': 'development_metrics_not_final_accuracy',
        'input_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'selected_rows_sha256': hashlib.sha256(selected_bytes).hexdigest(),
    })
    config = {
        'task': 'translation',
        'split': 'dev',
        'baseline_field': baseline_field,
        'candidate_field': candidate_field,
        'reference_field': reference_field,
        'metric_ids': report['metric_ids'],
        'bootstrap': report['bootstrap'],
    }
    write_run_artifacts(
        output_dir,
        paired,
        report,
        config=config,
        model={'comparison': [baseline_field, candidate_field]},
        runtime={
            'python': platform.python_version(),
            'implementation': platform.python_implementation(),
            'platform': platform.platform(),
        },
        device='cpu',
        code_paths=(
            __file__,
            Path(__file__).with_name('run_translation_baseline.py'),
            Path(__file__).with_name('evaluation_run_manifest.py'),
        ),
        git_root=git_root,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--baseline-field', default='copy_hypothesis')
    parser.add_argument('--candidate-field', default='translation_memory_hypothesis')
    parser.add_argument('--reference-field', default='reference')
    parser.add_argument('--replicates', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=1729)
    parser.add_argument('--confidence-level', type=float, default=0.95)
    args = parser.parse_args()
    report = run(
        predictions_path=args.predictions,
        output_dir=args.output_dir,
        baseline_field=args.baseline_field,
        candidate_field=args.candidate_field,
        reference_field=args.reference_field,
        replicates=args.replicates,
        seed=args.seed,
        confidence_level=args.confidence_level,
    )
    print(json.dumps({
        'run_id': report['run_id'],
        'evaluation_records': report['evaluation_records'],
        'bootstrap': report['bootstrap'],
        'paired_deltas': report['paired_deltas'],
        'exact_match_outcomes': report['exact_match_outcomes'],
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
