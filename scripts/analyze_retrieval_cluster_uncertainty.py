#!/usr/bin/env python3
"""Estimate dev retrieval uncertainty by resampling XORQA source-page families."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import random
from collections import Counter, defaultdict
from pathlib import Path

from audit_xorqa_source_page_families import source_page_hashes


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
DEFAULT_PREDICTIONS = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/predictions.jsonl'
DEFAULT_RETRIEVAL_REPORT = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/report.json'
DEFAULT_OUTPUT = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-28/source_page_cluster_bootstrap'
RETRIEVERS = (
    'garhwali_word_bm25',
    'garhwali_character_bm25',
    'oracle_english_word_bm25',
)
METRICS = ('recall_at_1', 'recall_at_5', 'recall_at_10', 'mrr_at_10')


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with Path(path).open(encoding='utf-8') as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f'{path}:{line_number}: invalid JSON') from error
            if not isinstance(row, dict):
                raise ValueError(f'{path}:{line_number}: expected a JSON object')
            rows.append(row)
    return rows


def validate_inputs(
    benchmark_rows: list[dict], prediction_rows: list[dict], retrieval_report: dict,
) -> tuple[list[dict], dict[str, dict]]:
    """Check row identity, dev-only scope, and source-page lineage."""
    benchmark_by_id = {}
    for index, row in enumerate(benchmark_rows):
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError(f'benchmark row {index} is missing record_id')
        if record_id in benchmark_by_id:
            raise ValueError(f'duplicate benchmark record_id: {record_id}')
        benchmark_by_id[record_id] = row
    dev_rows = [row for row in benchmark_rows if row.get('split') == 'dev']
    dev_by_id = {row['record_id']: row for row in dev_rows}
    if not dev_rows:
        raise ValueError('benchmark has no dev rows')

    predictions_by_id = {}
    for index, row in enumerate(prediction_rows):
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError(f'prediction row {index} is missing record_id')
        if record_id in predictions_by_id:
            raise ValueError(f'duplicate prediction record_id: {record_id}')
        if row.get('split') != 'dev':
            raise ValueError(f'{record_id}: only dev predictions may be analyzed')
        predictions_by_id[record_id] = row
    if set(predictions_by_id) != set(dev_by_id):
        missing = sorted(set(dev_by_id) - set(predictions_by_id))
        unexpected = sorted(set(predictions_by_id) - set(dev_by_id))
        raise ValueError(
            'prediction IDs must exactly match benchmark dev IDs '
            f'(missing={len(missing)}, unexpected={len(unexpected)})')
    if retrieval_report.get('evaluation_queries') != len(dev_rows):
        raise ValueError('retrieval report query count does not match benchmark dev rows')

    for row in dev_rows:
        if source_page_hashes(row) is None:
            raise ValueError(f"{row['record_id']}: missing or invalid source-page title")
        prediction = predictions_by_id[row['record_id']]
        for retriever in RETRIEVERS:
            item = prediction.get(retriever)
            if not isinstance(item, dict):
                raise ValueError(f"{row['record_id']}: missing {retriever} prediction")
            if 'rank' not in item:
                raise ValueError(f"{row['record_id']}: {retriever} prediction is missing rank")
            rank = item.get('rank')
            if rank is not None and (isinstance(rank, bool) or not isinstance(rank, int) or rank < 1):
                raise ValueError(f"{row['record_id']}: invalid {retriever} rank")
    return dev_rows, predictions_by_id


def _outcome(rank: int | None, metric: str) -> float:
    if metric.startswith('recall_at_'):
        cutoff = int(metric.rsplit('_', 1)[1])
        return float(rank is not None and rank <= cutoff)
    if metric == 'mrr_at_10':
        return 1.0 / rank if rank is not None and rank <= 10 else 0.0
    raise ValueError(f'unsupported metric: {metric}')


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def _family_values(rows: list[dict], metric: str) -> dict[str, list[float]]:
    groups: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        family = row.get('source_page_family_sha256')
        if not isinstance(family, str) or not family:
            raise ValueError('each row requires a source_page_family_sha256')
        groups[family].append(_outcome(row.get('rank'), metric))
    if not groups:
        raise ValueError('at least one source-page family is required')
    return dict(sorted(groups.items()))


def cluster_bootstrap_metric(
    rows: list[dict], *, metric: str, replicates: int = 2000, seed: int = 1729,
    confidence_level: float = 0.95,
) -> dict:
    """Resample source-page groups, retaining every query from each sampled group."""
    if replicates < 1:
        raise ValueError('replicates must be positive')
    if not 0 < confidence_level < 1:
        raise ValueError('confidence_level must be between zero and one')
    groups = _family_values(rows, metric)
    family_ids = list(groups)
    point = sum(sum(values) for values in groups.values()) / sum(map(len, groups.values()))
    rng = random.Random(seed)
    sampled_metrics = []
    for _ in range(replicates):
        total = sampled_rows = 0
        for _ in family_ids:
            values = groups[rng.choice(family_ids)]
            total += sum(values)
            sampled_rows += len(values)
        sampled_metrics.append(total / sampled_rows)
    alpha = (1 - confidence_level) / 2
    return {
        'point_estimate': point,
        'confidence_interval': [
            _percentile(sampled_metrics, alpha),
            _percentile(sampled_metrics, 1 - alpha),
        ],
        'bootstrap_values': sampled_metrics,
    }


def _prediction_rows(
    dev_rows: list[dict], predictions_by_id: dict[str, dict],
) -> dict[str, list[dict]]:
    prepared = {name: [] for name in RETRIEVERS}
    for source_row in dev_rows:
        family_hash = source_page_hashes(source_row)[1]
        prediction = predictions_by_id[source_row['record_id']]
        for name in RETRIEVERS:
            prepared[name].append({
                'record_id': source_row['record_id'],
                'source_page_family_sha256': family_hash,
                'rank': prediction[name]['rank'],
            })
    return prepared


def _family_summary(rows: list[dict]) -> dict:
    sizes = Counter()
    for row in rows:
        sizes[source_page_hashes(row)[1]] += 1
    size_counts = Counter(sizes.values())
    return {
        'source_page_family_count': len(sizes),
        'singleton_family_count': size_counts.get(1, 0),
        'multiquery_family_count': sum(size > 1 for size in sizes.values()),
        'rows_in_multiquery_families': sum(size for size in sizes.values() if size > 1),
        'family_size_distribution': {
            str(size): count for size, count in sorted(size_counts.items())
        },
    }


def _rounded_interval(result: dict) -> dict:
    return {
        'point_estimate': round(result['point_estimate'], 8),
        'confidence_interval_95': [round(value, 8) for value in result['confidence_interval']],
    }


def run(
    benchmark_path: Path = DEFAULT_BENCHMARK,
    predictions_path: Path = DEFAULT_PREDICTIONS,
    retrieval_report_path: Path = DEFAULT_RETRIEVAL_REPORT,
    output_dir: Path = DEFAULT_OUTPUT,
    *, replicates: int = 2000, seed: int = 1729,
) -> dict:
    benchmark_path = Path(benchmark_path)
    predictions_path = Path(predictions_path)
    retrieval_report_path = Path(retrieval_report_path)
    output_dir = Path(output_dir)
    benchmark_sha = sha256_file(benchmark_path)
    predictions_sha = sha256_file(predictions_path)
    retrieval_report_sha = sha256_file(retrieval_report_path)
    retrieval_report = json.loads(retrieval_report_path.read_text(encoding='utf-8'))
    if retrieval_report.get('input_manifest_sha256') != benchmark_sha:
        raise ValueError('saved retrieval report does not pin the supplied benchmark file')
    if retrieval_report.get('test_scored') is not False:
        raise ValueError('saved retrieval run is not verified as dev-only')
    benchmark_rows = read_jsonl(benchmark_path)
    prediction_rows = read_jsonl(predictions_path)
    dev_rows, predictions_by_id = validate_inputs(
        benchmark_rows, prediction_rows, retrieval_report)
    prepared = _prediction_rows(dev_rows, predictions_by_id)

    retrievers = {}
    raw_results = {}
    for name, rows in prepared.items():
        raw_results[name] = {}
        retrievers[name] = {}
        for metric in METRICS:
            result = cluster_bootstrap_metric(
                rows, metric=metric, replicates=replicates, seed=seed)
            raw_results[name][metric] = result
            retrievers[name][metric] = _rounded_interval(result)
            parent_metric_name = {
                'recall_at_1': 'recall_at_1',
                'recall_at_5': 'recall_at_5',
                'recall_at_10': 'recall_at_10',
                'mrr_at_10': 'mrr_at_10',
            }[metric]
            expected = retrieval_report['baselines'][name]['dev'][parent_metric_name]
            if abs(result['point_estimate'] - expected) > 1e-7:
                raise ValueError(f'{name} {metric} does not reproduce the saved dev report')

    paired_deltas = {}
    for metric in METRICS:
        base = raw_results['garhwali_word_bm25'][metric]
        candidate = raw_results['garhwali_character_bm25'][metric]
        # Equal seeds and sorted family keys produce identical paired family draws.
        sampled_deltas = [
            char_value - word_value
            for char_value, word_value in zip(
                candidate['bootstrap_values'], base['bootstrap_values'])
        ]
        paired_deltas[metric] = {
            'comparison': 'garhwali_character_bm25_minus_garhwali_word_bm25',
            'point_estimate': round(candidate['point_estimate'] - base['point_estimate'], 8),
            'confidence_interval_95': [
                round(_percentile(sampled_deltas, 0.025), 8),
                round(_percentile(sampled_deltas, 0.975), 8),
            ],
        }

    families = _family_summary(dev_rows)
    report = {
        'schema_version': 1,
        'analysis': 'xorqa_bm25_source_page_cluster_bootstrap_v1',
        'evaluation_split': 'dev',
        'evaluation_record_count': len(dev_rows),
        **families,
        'retrievers': retrievers,
        'paired_deltas': paired_deltas,
        'bootstrap': {
            'method': 'source_page_cluster_resampling_with_replacement',
            'replicates': replicates,
            'seed': seed,
            'confidence_level': 0.95,
            'quantile_method': 'linear_interpolation_on_sorted_bootstrap_values',
            'cluster_unit': 'NFKC + casefold + whitespace-collapsed upstream Wikipedia title page segment',
        },
        'lineage': {
            'benchmark_path': str(benchmark_path),
            'benchmark_sha256': benchmark_sha,
            'predictions_path': str(predictions_path),
            'predictions_sha256': predictions_sha,
            'retrieval_report_path': str(retrieval_report_path),
            'retrieval_report_sha256': retrieval_report_sha,
            'retrieval_report_benchmark_sha256_verified': True,
            'candidate_corpus_sha256': retrieval_report.get('passage_corpus_sha256'),
            'candidate_corpus_documents': retrieval_report.get('corpus_documents'),
            'test_rows_scored': 0,
            'generator_sha256': sha256_file(Path(__file__)),
            'python_version': platform.python_version(),
        },
        'limitations': [
            'This is source-page-clustered uncertainty for saved development predictions, not an evaluation on held-out pages.',
            'The retrieval candidate corpus is fixed and includes documents derived from all original splits; intervals are conditional on that corpus.',
            'The English-query retriever is a diagnostic upper bound, not a Garhwali model-quality score.',
            'References and language labels have not received native-speaker adjudication.',
            'Bootstrap intervals do not establish independent accuracy or statistical significance for model selection.',
        ],
        'outputs': {
            'json': str(output_dir / 'report.json'),
            'markdown': str(output_dir / 'report.md'),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (output_dir / 'report.md').write_text(_markdown(report), encoding='utf-8')
    return report


def _markdown(report: dict) -> str:
    lines = [
        '# XORQA retrieval source-page-cluster uncertainty', '',
        'This analysis resamples complete source-page families among the saved 500-query development predictions. It adds uncertainty estimates; it does not retrain a model, evaluate held-out pages, or score the test split.', '',
        f"- Dev queries: {report['evaluation_record_count']}",
        f"- Source-page families: {report['source_page_family_count']}",
        f"- Families with multiple queries: {report['multiquery_family_count']} ({report['rows_in_multiquery_families']} rows)",
        f"- Bootstrap: {report['bootstrap']['replicates']:,} replicates, seed {report['bootstrap']['seed']}", '',
        '| Retriever | R@1 | R@5 | R@10 | MRR@10 |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for name, metrics in report['retrievers'].items():
        cells = []
        for metric in METRICS:
            item = metrics[metric]
            lo, hi = item['confidence_interval_95']
            cells.append(f"{item['point_estimate']:.4f} [{lo:.4f}, {hi:.4f}]")
        lines.append(f"| `{name}` | " + ' | '.join(cells) + ' |')
    lines.extend([
        '', 'Paired character-minus-word Garhwali BM25 deltas:', '',
        '| Metric | Difference | 95% clustered interval |', '| --- | ---: | ---: |',
    ])
    for metric, result in report['paired_deltas'].items():
        lo, hi = result['confidence_interval_95']
        lines.append(f"| {metric} | {result['point_estimate']:.4f} | [{lo:.4f}, {hi:.4f}] |")
    lines.extend([
        '', 'The candidate corpus is fixed and contains documents derived from train, dev, and test, so these intervals are conditional on that all-split retrieval corpus. They estimate query uncertainty within the existing dev set; they do not demonstrate generalization to unseen Wikipedia pages. The English-query result is only an upper-bound diagnostic. References remain unreviewed.', '',
        f"Benchmark SHA-256: `{report['lineage']['benchmark_sha256']}`  ",
        f"Predictions SHA-256: `{report['lineage']['predictions_sha256']}`  ",
        f"Parent report SHA-256: `{report['lineage']['retrieval_report_sha256']}`", '',
    ])
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument('--predictions', type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument('--retrieval-report', type=Path, default=DEFAULT_RETRIEVAL_REPORT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--replicates', type=int, default=2000)
    parser.add_argument('--seed', type=int, default=1729)
    args = parser.parse_args()
    report = run(
        args.benchmark, args.predictions, args.retrieval_report, args.output_dir,
        replicates=args.replicates, seed=args.seed)
    print(json.dumps({
        'evaluation_record_count': report['evaluation_record_count'],
        'source_page_family_count': report['source_page_family_count'],
        'outputs': report['outputs'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
