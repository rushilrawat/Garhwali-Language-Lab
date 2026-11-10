#!/usr/bin/env python3
"""Score existing GarhwaliBench predictions and write hash-linked run artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
from collections import Counter
from pathlib import Path

from benchmark_metrics import normalize_metric_text, score_qa_answers, score_rouge_l
from asr_metrics import normalize as normalize_asr_text, score_corpus as score_asr_corpus
from evaluation_run_manifest import write_run_artifacts
from run_translation_baseline import corpus_chrf, metric_summary as translation_metric_summary
from run_translation_baseline import normalize as normalize_translation_text
from run_mt5_instruction_tuning import generation_diagnostics
from garhwali_lab.io import read_json, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
TASKS = {
    'translation': {
        'reference_field': 'source_example.target',
        'metric_ids': ['garhwali-custom-add1-bleu-v1', 'garhwali-custom-chrf2-v1'],
    },
    'summarization': {
        'reference_field': 'source_example.summary',
        'metric_ids': ['garhwali-rouge-l-f1-v1', 'garhwali-custom-chrf2-v1'],
    },
    'question_answering': {
        'reference_field': 'source_example.translated_answers[*].text',
        'metric_ids': ['garhwali-qa-em-token-f1-v1'],
    },
    'asr': {
        'reference_field': 'text.text_scoring',
        'metric_ids': ['garhwali-asr-corpus-wer-v1', 'garhwali-asr-corpus-cer-v1'],
    },
    'generation': {
        'reference_field': 'acceptable_responses[*] (fallback: response)',
        'metric_ids': [
            'garhwali-generation-em-multi-ref-v1',
            'garhwali-generation-chrf2-multi-ref-v1',
        ],
    },
}


# Headline metrics re-estimated by the bootstrap, per task.
HEADLINE_METRICS = {
    'asr': ('wer', 'cer'),
    'translation': ('corpus_chrf2', 'corpus_bleu_smoothed', 'exact_match'),
    'summarization': ('rouge_l_f1', 'corpus_chrf2'),
    'question_answering': ('exact_match', 'token_f1'),
}
# Most specific shared-source key first; records with none of these are their
# own cluster. Resampling whole clusters keeps related records together, so
# intervals are not narrowed by near-duplicates or shared source pages.
CLUSTER_FIELDS = (
    'source_page_family_sha256',
    'overlay_source_page_family_sha256',
    'source_context_group_sha256',
    'overlay_source_family_sha256',
    'duplicate_component_id',
    'speaker_id',
)


def cluster_keys(rows: list[dict], record_ids: list[str]) -> tuple[list[str], Counter]:
    """Return one cluster key per row and how many rows each field supplied."""
    keys = []
    used = Counter()
    for row, record_id in zip(rows, record_ids, strict=True):
        lineage = row.get('lineage') or {}
        for field in CLUSTER_FIELDS:
            value = lineage.get(field) or row.get(field)
            if value:
                keys.append(f'{field}:{value}')
                used[field] += 1
                break
        else:
            keys.append(f'record:{record_id}')
            used['record_id'] += 1
    return keys, used


def bootstrap_intervals(score, indices, clusters, metric_names, *,
                        replicates: int, seed: int, confidence: float = 0.95) -> dict:
    """Percentile intervals from a cluster bootstrap over the given record indices."""
    if replicates < 1:
        raise ValueError('bootstrap replicates must be positive')
    groups: dict[str, list[int]] = {}
    for index in indices:
        groups.setdefault(clusters[index], []).append(index)
    names = list(groups)
    rng = random.Random(seed)
    samples = {name: [] for name in metric_names}
    for _ in range(replicates):
        chosen = [index for _ in names for index in groups[rng.choice(names)]]
        metrics = score(chosen)
        for name in metric_names:
            value = metrics.get(name)
            if isinstance(value, (int, float)):
                samples[name].append(float(value))
    alpha = (1 - confidence) / 2

    def percentile(values, q):
        ordered = sorted(values)
        position = q * (len(ordered) - 1)
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)

    return {
        'method': 'cluster_percentile_bootstrap',
        'replicates': replicates,
        'seed': seed,
        'confidence': confidence,
        'clusters': len(names),
        'records': len(indices),
        'intervals': {
            name: [round(percentile(values, alpha), 8), round(percentile(values, 1 - alpha), 8)]
            for name, values in samples.items() if values
        },
    }



def _references(task: str, row: dict) -> list[str]:
    example = row.get('source_example') or {}
    if task == 'translation':
        target = example.get('target')
        return [target] if isinstance(target, str) else []
    if task == 'summarization':
        summary = example.get('summary')
        return [summary] if isinstance(summary, str) else []
    if task == 'question_answering':
        answers = example.get('translated_answers')
        if not isinstance(answers, list):
            return []
        return [
            answer.get('text', '') if isinstance(answer, dict) else str(answer)
            for answer in answers
        ]
    if task == 'asr':
        text = row.get('text') or {}
        reference = text.get('text_scoring')
        return [reference if isinstance(reference, str) else '']
    if task == 'generation':
        alternatives = row.get('acceptable_responses')
        if isinstance(alternatives, list) and alternatives:
            return [reference for reference in alternatives if isinstance(reference, str)]
        reference = row.get('response')
        return [reference] if isinstance(reference, str) else []
    raise ValueError(f'unsupported task: {task}')


def _record_id(task: str, row: dict) -> str:
    record_id = row.get('record_id')
    if task == 'generation' and not record_id:
        instruction_hash = row.get('instruction_sha256')
        if isinstance(instruction_hash, str) and instruction_hash.strip():
            record_id = f'instruction:{instruction_hash.strip().lower()}'
    return str(record_id or '')


def _canonical_jsonl(rows: list[dict]) -> bytes:
    return ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in rows
    ).encode('utf-8')


def evaluate_rows(
    *,
    task: str,
    benchmark_rows: list[dict],
    prediction_rows: list[dict],
    prediction_field: str = 'hypothesis',
    split: str = 'dev',
    allow_historical_test: bool = False,
    input_sha256: str | None = None,
    prediction_input_sha256: str | None = None,
    bootstrap_replicates: int = 0,
    bootstrap_seed: int = 17,
) -> tuple[dict, list[dict]]:
    """Score one explicit split after exact prediction-ID reconciliation."""
    if task not in TASKS:
        raise ValueError(f'unsupported task: {task}')
    if split not in {'dev', 'validation', 'test'}:
        raise ValueError('scoring supports only dev, validation, or historical test')
    if split == 'test' and not allow_historical_test:
        raise ValueError('test scoring requires --allow-historical-test')
    if not prediction_field:
        raise ValueError('prediction_field must be explicit')

    selected = [row for row in benchmark_rows if row.get('split') == split]
    if not selected:
        raise ValueError(f'benchmark has no rows in requested split: {split}')
    selected_ids = [_record_id(task, row) for row in selected]
    if any(not record_id for record_id in selected_ids):
        raise ValueError('selected benchmark rows require record_id')
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError('selected benchmark rows contain duplicate record_id values')

    prediction_map = {}
    for row in prediction_rows:
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError('prediction rows require record_id')
        if record_id in prediction_map:
            raise ValueError(f'duplicate prediction record_id: {record_id}')
        if prediction_field not in row or not isinstance(row[prediction_field], str):
            raise ValueError(f'{record_id}: prediction field {prediction_field!r} must be a string')
        prediction_map[record_id] = row[prediction_field]

    expected_ids = set(selected_ids)
    observed_ids = set(prediction_map)
    missing = sorted(expected_ids - observed_ids)
    unexpected = sorted(observed_ids - expected_ids)
    if missing:
        raise ValueError(f'missing prediction IDs: {missing[:5]}')
    if unexpected:
        raise ValueError(f'unexpected prediction IDs: {unexpected[:5]}')

    references = [_references(task, row) for row in selected]
    hypotheses = [prediction_map[record_id] for record_id in selected_ids]
    reference_is_nonempty = (
        (lambda reference: bool(normalize_translation_text(reference)))
        if task == 'translation'
        else (lambda reference: bool(normalize_asr_text(reference)))
        if task == 'asr'
        else (lambda reference: bool(normalize_metric_text(reference)))
    )
    metric_indices = [
        index for index, alternatives in enumerate(references)
        if any(reference_is_nonempty(reference) for reference in alternatives)
    ]
    excluded_indices = [
        index for index, alternatives in enumerate(references)
        if not any(reference_is_nonempty(reference) for reference in alternatives)
    ]
    if not metric_indices:
        raise ValueError('no selected records have a non-empty reference for this task')
    if task == 'asr':
        metrics = score_asr_corpus(
            [alternatives[0] for alternatives in references],
            hypotheses,
            record_ids=selected_ids,
        )
    elif task == 'translation':
        metrics = translation_metric_summary(
            [references[index][0] for index in metric_indices],
            [hypotheses[index] for index in metric_indices],
        )
    elif task == 'summarization':
        metrics = score_rouge_l(
            [hypotheses[index] for index in metric_indices],
            [references[index] for index in metric_indices],
        )
    elif task == 'generation':
        metric_rows = []
        for index in metric_indices:
            row = dict(selected[index])
            row['acceptable_responses'] = references[index]
            row['response'] = references[index][0]
            metric_rows.append(row)
        metrics, generation_details = generation_diagnostics(
            metric_rows,
            [hypotheses[index] for index in metric_indices],
        )
        metrics.update({
            'metric_ids': TASKS[task]['metric_ids'],
            'normalizer_id': 'mt0-generation-nfc-casefold-whitespace-v1',
            'tokenizer_id': 'whitespace-tokens-and-codepoint-ngrams-v1',
            'aggregation': 'exact_match_any_valid_reference_and_chrf2_best_reference_per_record',
        })
    else:
        metrics = score_qa_answers(
            [hypotheses[index] for index in metric_indices],
            [references[index] for index in metric_indices],
        )
    if task == 'translation':
        metrics.update({
            'metric_ids': TASKS[task]['metric_ids'],
            'normalizer_id': 'garhwali-translation-nfc-casefold-whitespace-v1',
            'tokenizer_id': 'unicode-whitespace-tokens-v1',
            'aggregation': 'corpus',
        })
    elif task == 'summarization':
        metrics['corpus_chrf2'] = corpus_chrf(
            [references[index][0] for index in metric_indices],
            [hypotheses[index] for index in metric_indices],
        )
        metrics['metric_ids'] = TASKS[task]['metric_ids']
    elif task == 'question_answering':
        metrics['metric_ids'] = TASKS[task]['metric_ids']
    clusters, cluster_fields_used = cluster_keys(selected, selected_ids)
    if bootstrap_replicates and task in HEADLINE_METRICS:
        if task == 'asr':
            def score(chosen):
                return score_asr_corpus(
                    [references[index][0] for index in chosen],
                    [hypotheses[index] for index in chosen],
                    record_ids=[f'{selected_ids[index]}#{n}' for n, index in enumerate(chosen)],
                )
            bootstrap_indices = list(range(len(selected)))
        elif task == 'translation':
            def score(chosen):
                return translation_metric_summary(
                    [references[index][0] for index in chosen],
                    [hypotheses[index] for index in chosen],
                )
            bootstrap_indices = metric_indices
        elif task == 'summarization':
            def score(chosen):
                result = score_rouge_l(
                    [hypotheses[index] for index in chosen],
                    [references[index] for index in chosen],
                )
                result['corpus_chrf2'] = corpus_chrf(
                    [references[index][0] for index in chosen],
                    [hypotheses[index] for index in chosen],
                )
                return result
            bootstrap_indices = metric_indices
        else:
            def score(chosen):
                return score_qa_answers(
                    [hypotheses[index] for index in chosen],
                    [references[index] for index in chosen],
                )
            bootstrap_indices = metric_indices
        uncertainty = bootstrap_intervals(
            score, bootstrap_indices, clusters, HEADLINE_METRICS[task],
            replicates=bootstrap_replicates, seed=bootstrap_seed,
        )
    else:
        uncertainty = {
            'method': 'not_computed',
            'reason': (
                'bootstrap not requested' if task in HEADLINE_METRICS
                else f'no bootstrap defined for task {task}'
            ),
        }
    uncertainty['cluster_fields_used'] = dict(sorted(cluster_fields_used.items()))
    selected_hash = hashlib.sha256(_canonical_jsonl(selected)).hexdigest()
    ordered_predictions = [
        dict({
            'record_id': record_id,
            'hypothesis': prediction_map[record_id],
            'metric_included': index in metric_indices,
            'metric_exclusion_reason': (
                None if index in metric_indices else 'missing_nonempty_target_reference'
            ),
        }, **({
            'generation_diagnostics': generation_details[
                metric_indices.index(index)
            ] | {'acceptable_responses': references[index]}
        } if task == 'generation' and index in metric_indices else {}))
        for index, record_id in enumerate(selected_ids)
    ]
    source_split_counts = (
        dict(sorted(Counter(
            str((row.get('source_example') or {}).get('split') or 'unspecified')
            for row in selected
        ).items()))
        if task != 'generation'
        else {}
    )
    report = {
        'schema_version': 1,
        'run_id': None,
        'task': task,
        'evaluation_split': split,
        'claim_limit': (
            'historical_open_test_only' if split == 'test'
            else 'development_metrics_not_final_accuracy'
        ),
        'evaluation_records': len(selected),
        'selected_record_ids': selected_ids,
        'input_sha256': input_sha256,
        'prediction_input_sha256': prediction_input_sha256,
        'selected_rows_sha256': selected_hash,
        'reference_field': TASKS[task]['reference_field'],
        'prediction_field': prediction_field,
        'coverage': {
            'requested': len(selected),
            'predicted': len(ordered_predictions),
            'metric_scored_records': len(metric_indices),
            'excluded_missing_reference_records': len(excluded_indices),
            'missing': 0,
            'unexpected': 0,
        },
        'metric_scored_record_ids': [selected_ids[index] for index in metric_indices],
        'excluded_record_ids': [selected_ids[index] for index in excluded_indices],
        'source_split_counts': source_split_counts,
        'metrics': metrics,
        'uncertainty': uncertainty,
        'benchmark_snapshot': None,
        'limitations': [
            'Metric scores do not validate Garhwali spelling, meaning, or reference quality.',
            'Development metrics are for selection/diagnostics, not independent final accuracy.',
            'Historical public test metrics are not blind and must not select a model.',
            (
                'Uncertainty intervals resample source-family clusters; they do not cover reference errors or model exposure.'
                if uncertainty['method'] != 'not_computed'
                else 'Source-family clustered uncertainty was not computed for this run.'
            ),
        ],
    }
    return report, ordered_predictions


def snapshot_reference(snapshot_path: Path, benchmark_sha256: str) -> dict:
    """Tie a run to a pinned benchmark snapshot; the input file must be in it."""
    snapshot = read_json(snapshot_path)
    matches = [
        entry['path'] for entry in snapshot.get('files', [])
        if entry.get('sha256') == benchmark_sha256
    ]
    if not matches:
        raise ValueError(
            f'benchmark input is not part of snapshot {snapshot_path} '
            f'(sha256 {benchmark_sha256[:12]}...); re-pin the benchmark or score the pinned file'
        )
    return {
        'snapshot_file': snapshot_path.name,
        'schema': snapshot.get('schema'),
        'combined_sha256': snapshot.get('combined_sha256'),
        'benchmark_file': matches[0],
        'benchmark_id': (snapshot.get('benchmark') or {}).get('benchmark_id'),
    }


def run(    *,
    task: str,
    benchmark_path: Path,
    predictions_path: Path,
    output_dir: Path,
    prediction_field: str,
    model: dict,
    split: str = 'dev',
    allow_historical_test: bool = False,
    device: str = 'cpu',
    seed: int | None = None,
    git_root: Path | None = ROOT,
    snapshot_path: Path | None = None,
    bootstrap_replicates: int = 0,
    bootstrap_seed: int = 17,
) -> dict:
    benchmark_path = Path(benchmark_path)
    predictions_path = Path(predictions_path)
    benchmark_bytes = benchmark_path.read_bytes()
    prediction_bytes = predictions_path.read_bytes()
    benchmark_hash = hashlib.sha256(benchmark_bytes).hexdigest()
    prediction_hash = hashlib.sha256(prediction_bytes).hexdigest()
    report, predictions = evaluate_rows(
        task=task,
        benchmark_rows=read_jsonl(benchmark_path),
        prediction_rows=read_jsonl(predictions_path),
        prediction_field=prediction_field,
        split=split,
        allow_historical_test=allow_historical_test,
        input_sha256=benchmark_hash,
        prediction_input_sha256=prediction_hash,
        bootstrap_replicates=bootstrap_replicates,
        bootstrap_seed=bootstrap_seed,
    )
    if snapshot_path is not None:
        report['benchmark_snapshot'] = snapshot_reference(Path(snapshot_path), benchmark_hash)
    report['run_id'] = f"garhwali-{task}-{split}-{prediction_hash[:12]}"
    config = {
        'task': task,
        'split': split,
        'prediction_field': prediction_field,
        'reference_field': TASKS[task]['reference_field'],
        'metric_ids': TASKS[task]['metric_ids'],
        'normalizer_id': report['metrics']['normalizer_id'],
        'tokenizer_id': report['metrics']['tokenizer_id'],
        'allow_historical_test': allow_historical_test,
        'bootstrap_replicates': bootstrap_replicates,
        'bootstrap_seed': bootstrap_seed if bootstrap_replicates else None,
    }
    write_run_artifacts(
        output_dir,
        predictions,
        report,
        config=config,
        model=model,
        runtime={
            'python': platform.python_version(),
            'implementation': platform.python_implementation(),
            'platform': platform.platform(),
        },
        device=device,
        seed=seed,
        code_paths=(
            __file__,
            Path(__file__).with_name('asr_metrics.py'),
            Path(__file__).with_name('benchmark_metrics.py'),
            Path(__file__).with_name('evaluation_run_manifest.py'),
            Path(__file__).with_name('freeze_benchmark.py'),
            Path(__file__).with_name('run_mt5_instruction_tuning.py'),
            Path(__file__).with_name('run_translation_baseline.py'),
        ),
        git_root=git_root,
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', choices=sorted(TASKS), required=True)
    parser.add_argument('--benchmark', type=Path, required=True)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--prediction-field', required=True)
    parser.add_argument('--model-id', required=True)
    parser.add_argument('--model-revision', required=True)
    parser.add_argument('--checkpoint-sha256')
    parser.add_argument('--split', choices=('dev', 'validation', 'test'), default='dev')
    parser.add_argument('--allow-historical-test', action='store_true')
    parser.add_argument('--device', default='cpu')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--snapshot', type=Path,
                        help='benchmark snapshot JSON (release/*_snapshot.json) the input must belong to')
    parser.add_argument('--bootstrap', type=int, default=0, metavar='N',
                        help='cluster-bootstrap replicates for uncertainty intervals (0 = off)')
    parser.add_argument('--bootstrap-seed', type=int, default=17)
    args = parser.parse_args()
    report = run(
        task=args.task,
        benchmark_path=args.benchmark,
        predictions_path=args.predictions,
        output_dir=args.output_dir,
        prediction_field=args.prediction_field,
        model={
            'id': args.model_id,
            'revision': args.model_revision,
            'checkpoint_sha256': args.checkpoint_sha256,
        },
        split=args.split,
        allow_historical_test=args.allow_historical_test,
        device=args.device,
        seed=args.seed,
        snapshot_path=args.snapshot,
        bootstrap_replicates=args.bootstrap,
        bootstrap_seed=args.bootstrap_seed,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
