#!/usr/bin/env python3
"""Score existing GarhwaliBench predictions and write hash-linked run artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections import Counter
from pathlib import Path

from benchmark_metrics import normalize_metric_text, score_qa_answers, score_rouge_l
from asr_metrics import normalize as normalize_asr_text, score_corpus as score_asr_corpus
from evaluation_run_manifest import write_run_artifacts
from run_translation_baseline import corpus_chrf, metric_summary as translation_metric_summary
from run_translation_baseline import normalize as normalize_translation_text
from run_mt5_instruction_tuning import generation_diagnostics


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
        'limitations': [
            'Metric scores do not validate Garhwali spelling, meaning, or reference quality.',
            'Development metrics are for selection/diagnostics, not independent final accuracy.',
            'Historical public test metrics are not blind and must not select a model.',
            'Source-family clustered uncertainty is not computed by this scorer.',
        ],
    }
    return report, ordered_predictions


def run(
    *,
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
    )
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
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
