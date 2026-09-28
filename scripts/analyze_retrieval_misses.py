#!/usr/bin/env python3
"""Diagnose saved XORQA BM25 dev misses and gold-passage availability."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_xorqa_source_page_families import source_page_hashes
from run_retrieval_baseline import (
    build_documents,
    character_ngrams,
    context_id,
    metric_summary,
    word_tokens,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
DEFAULT_PREDICTIONS = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/predictions.jsonl'
DEFAULT_RETRIEVAL_REPORT = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/report.json'
DEFAULT_OUTPUT = ROOT / 'data/processed/evaluation/retrieval/roadmap_2026-09-28/miss_analysis'
RETRIEVER_QUERIES = {
    'garhwali_word_bm25': ('question', word_tokens),
    'garhwali_character_bm25': ('question', character_ngrams),
    'oracle_english_word_bm25': ('oracle_question', word_tokens),
}
STATUS_ORDER = ('rank_1', 'rank_2_5', 'rank_6_10', 'rank_11_plus', 'zero_score')


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


def corpus_sha256(documents: list[dict]) -> str:
    payload = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in documents
    ).encode('utf-8')
    return sha256_bytes(payload)


def _status(rank: int | None) -> str:
    if rank is None:
        return 'zero_score'
    if rank == 1:
        return 'rank_1'
    if rank <= 5:
        return 'rank_2_5'
    if rank <= 10:
        return 'rank_6_10'
    return 'rank_11_plus'


def _validate_inputs(
    benchmark_rows: list[dict], prediction_rows: list[dict], retrieval_report: dict,
) -> tuple[list[dict], dict[str, dict], list[dict], dict[str, list[str]]]:
    benchmark_by_id = {}
    for index, row in enumerate(benchmark_rows):
        record_id = str(row.get('record_id') or '')
        if not record_id:
            raise ValueError(f'benchmark row {index} is missing record_id')
        if record_id in benchmark_by_id:
            raise ValueError(f'duplicate benchmark record_id: {record_id}')
        example = row.get('source_example')
        if not isinstance(example, dict) or not isinstance(example.get('context'), str):
            raise ValueError(f'{record_id}: requires a string gold context')
        benchmark_by_id[record_id] = row
    dev_rows = [row for row in benchmark_rows if row.get('split') == 'dev']
    if not dev_rows:
        raise ValueError('benchmark has no dev rows')
    dev_by_id = {row['record_id']: row for row in dev_rows}

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
    if sorted(retrieval_report.get('evaluated_record_ids', [])) != sorted(dev_by_id):
        raise ValueError('retrieval report evaluated IDs do not match benchmark dev IDs')
    if retrieval_report.get('test_scored') is not False:
        raise ValueError('saved retrieval run is not verified as dev-only')
    if retrieval_report.get('retrieval_scope') != 'all_unique_xorqa_contexts':
        raise ValueError('unexpected saved retrieval candidate-corpus scope')

    documents, relevant_ids, source_ids = build_documents(benchmark_rows)
    if retrieval_report.get('corpus_documents') != len(documents):
        raise ValueError('candidate corpus document count does not match saved report')
    if retrieval_report.get('passage_corpus_sha256') != corpus_sha256(documents):
        raise ValueError('candidate corpus hash does not match saved retrieval report')
    if retrieval_report.get('passage_source_record_ids') != source_ids:
        raise ValueError('candidate passage source mapping does not match saved report')

    document_ids = {row['document_id'] for row in documents}
    for row in dev_rows:
        record_id = row['record_id']
        example = row['source_example']
        if source_page_hashes(row) is None:
            raise ValueError(f'{record_id}: missing source-page family metadata')
        for system, (query_field, analyzer) in RETRIEVER_QUERIES.items():
            query = example.get(query_field)
            if not isinstance(query, str) or not query.strip():
                raise ValueError(f'{record_id}: missing query field {query_field}')
            item = predictions_by_id[record_id].get(system)
            if not isinstance(item, dict) or 'rank' not in item:
                raise ValueError(f'{record_id}: missing {system} rank')
            rank = item['rank']
            if rank is not None and (
                isinstance(rank, bool) or not isinstance(rank, int)
                or rank < 1 or rank > len(documents)
            ):
                raise ValueError(f'{record_id}: invalid {system} rank')
            score = item.get('relevant_score')
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                raise ValueError(f'{record_id}: invalid {system} relevant score')
            if (rank is None) != (score == 0):
                raise ValueError(f'{record_id}: rank and relevant score disagree for {system}')
            top_10 = item.get('top_10')
            if not isinstance(top_10, list):
                raise ValueError(f'{record_id}: invalid {system} top_10 list')
            gold_id = context_id(example['context'])
            seen_candidates = set()
            for candidate in top_10:
                if not isinstance(candidate, dict):
                    raise ValueError(f'{record_id}: malformed {system} top_10 item')
                candidate_id = candidate.get('document_id')
                if candidate_id not in document_ids or candidate_id in seen_candidates:
                    raise ValueError(f'{record_id}: invalid or duplicate {system} candidate ID')
                if candidate.get('score', 0) <= 0:
                    raise ValueError(f'{record_id}: top_10 contains a nonpositive score')
                seen_candidates.add(candidate_id)
            if rank is not None and rank <= 10:
                if rank > len(top_10) or top_10[rank - 1]['document_id'] != gold_id:
                    raise ValueError(f'{record_id}: rank does not point to gold passage in top_10')
                if top_10[rank - 1]['score'] != score:
                    raise ValueError(f'{record_id}: top_10 gold score disagrees with relevant score')
            elif any(candidate['document_id'] == gold_id for candidate in top_10):
                raise ValueError(f'{record_id}: top_10 contains gold passage at inconsistent rank')
            overlaps = set(analyzer(query)) & set(analyzer(example['context']))
            if (rank is None) != (not overlaps):
                raise ValueError(
                    f'{record_id}: saved {system} rank disagrees with gold lexical overlap')
            if gold_id not in document_ids:
                raise ValueError(f'{record_id}: gold context is missing from candidate corpus')

    return dev_rows, predictions_by_id, documents, source_ids


def _gold_candidate_splits(dev_rows, source_ids, benchmark_by_id):
    by_document = defaultdict(set)
    for document_id, source_record_ids in source_ids.items():
        by_document[document_id].update(
            benchmark_by_id[record_id]['split']
            for record_id in source_record_ids if record_id in benchmark_by_id
        )
    gold_documents = {context_id(row['source_example']['context']) for row in dev_rows}
    counts = Counter()
    for document_id in gold_documents:
        counts.update(by_document[document_id])
    return gold_documents, by_document, counts


def _query_record(row, prediction, candidate_page_families, candidate_splits):
    example = row['source_example']
    gold_id = context_id(example['context'])
    family_hash = source_page_hashes(row)[1]
    gold_splits = candidate_splits[gold_id]
    retrievers = {}
    for system, (query_field, analyzer) in RETRIEVER_QUERIES.items():
        item = prediction[system]
        rank = item['rank']
        top_10 = item['top_10']
        query = example[query_field]
        unique_query_units = set(analyzer(query))
        shared_units = unique_query_units & set(analyzer(example['context']))
        same_page_alternative = any(
            candidate['document_id'] != gold_id
            and family_hash in candidate_page_families.get(candidate['document_id'], set())
            for candidate in top_10
        )
        retrievers[system] = {
            'rank': rank,
            'status': _status(rank),
            'relevant_score': item['relevant_score'],
            'query_analyzer_unit_count': len(unique_query_units),
            'shared_gold_analyzer_unit_count': len(shared_units),
            'query_unit_coverage_of_gold': round(
                len(shared_units) / len(unique_query_units), 8) if unique_query_units else 0.0,
            'top_10_candidate_count': len(top_10),
            'same_page_non_gold_passage_in_top_10': same_page_alternative,
        }
    return {
        'record_id': row['record_id'],
        'source_page_family_sha256': family_hash,
        'gold_context_sha256': gold_id,
        'gold_context_available': True,
        'gold_context_source_splits': sorted(gold_splits),
        'gold_context_is_cross_split_duplicate': len(gold_splits) > 1,
        'retrievers': retrievers,
    }


def _summarize(per_query):
    retrievers = {}
    for system in RETRIEVER_QUERIES:
        rows = [item['retrievers'][system] for item in per_query]
        status_counts = Counter(row['status'] for row in rows)
        grouped = {}
        for status in STATUS_ORDER:
            group = [row for row in rows if row['status'] == status]
            if not group:
                continue
            grouped[status] = {
                'queries': len(group),
                'mean_shared_gold_analyzer_units': round(
                    sum(row['shared_gold_analyzer_unit_count'] for row in group) / len(group), 6),
                'mean_query_unit_coverage': round(
                    sum(row['query_unit_coverage_of_gold'] for row in group) / len(group), 6),
                'same_page_non_gold_passages_in_top_10': sum(
                    row['same_page_non_gold_passage_in_top_10'] for row in group),
            }
        ranks = [{'rank': row['rank'], 'relevant_score': row['relevant_score']}
                 for row in rows]
        metrics = metric_summary(ranks)
        retrievers[system] = {
            'metrics_reproduced': {
                key: metrics[key]
                for key in ('recall_at_1', 'recall_at_5', 'recall_at_10', 'mrr_at_10')
            },
            'status_counts': {status: status_counts.get(status, 0) for status in STATUS_ORDER},
            'misses_at_10': sum(status_counts.get(status, 0)
                                for status in ('rank_11_plus', 'zero_score')),
            'miss_rate_at_10': round(
                sum(status_counts.get(status, 0)
                    for status in ('rank_11_plus', 'zero_score')) / len(rows), 8),
            'zero_score_count': status_counts.get('zero_score', 0),
            'ranked_beyond_10_count': status_counts.get('rank_11_plus', 0),
            'gold_overlap_by_result_status': grouped,
        }
    return retrievers


def analyze_rows(benchmark_rows, prediction_rows, retrieval_report):
    dev_rows, predictions_by_id, documents, source_ids = _validate_inputs(
        benchmark_rows, prediction_rows, retrieval_report)
    benchmark_by_id = {row['record_id']: row for row in benchmark_rows}
    gold_documents, candidate_splits, gold_split_counts = _gold_candidate_splits(
        dev_rows, source_ids, benchmark_by_id)
    candidate_page_families = defaultdict(set)
    for document_id, record_ids in source_ids.items():
        for record_id in record_ids:
            row = benchmark_by_id.get(record_id)
            hashes = source_page_hashes(row) if row else None
            if hashes:
                candidate_page_families[document_id].add(hashes[1])

    per_query = [
        _query_record(row, predictions_by_id[row['record_id']],
                      candidate_page_families, candidate_splits)
        for row in dev_rows
    ]
    candidate_source_rows = sum(len(record_ids) for record_ids in source_ids.values())
    candidate_duplicate_context_groups = sum(
        len(record_ids) > 1 for record_ids in source_ids.values())
    duplicate_gold_documents = sum(
        len(source_ids[document_id]) > 1 for document_id in gold_documents)
    cross_split_gold_documents = sum(
        len(candidate_splits[document_id]) > 1 for document_id in gold_documents)
    retrievers = _summarize(per_query)
    saved_baselines = retrieval_report.get('baselines')
    if not isinstance(saved_baselines, dict):
        raise ValueError('saved retrieval report is missing baselines')
    for system, result in retrievers.items():
        saved_system = saved_baselines.get(system)
        saved_dev_metrics = saved_system.get('dev') if isinstance(saved_system, dict) else None
        if not isinstance(saved_dev_metrics, dict):
            raise ValueError(f'{system}: saved retrieval report is missing dev metrics')
        for metric_name, reproduced_value in result['metrics_reproduced'].items():
            saved_value = saved_dev_metrics.get(metric_name)
            if (isinstance(saved_value, bool) or not isinstance(saved_value, (int, float))
                    or abs(reproduced_value - saved_value) > 1e-7):
                raise ValueError(f'{system} {metric_name} does not reproduce saved dev report')
    report = {
        'schema_version': 1,
        'analysis': 'xorqa_saved_bm25_dev_miss_diagnosis_v1',
        'evaluation_split': 'dev',
        'evaluation_record_count': len(dev_rows),
        'candidate_corpus_document_count': len(documents),
        'candidate_coverage': {
            'gold_records': len(dev_rows),
            'available_gold_records': sum(row['gold_context_available'] for row in per_query),
            'missing_gold_records': sum(not row['gold_context_available'] for row in per_query),
            'unique_gold_contexts': len(gold_documents),
            'unique_gold_contexts_with_duplicate_source_rows': duplicate_gold_documents,
            'unique_gold_contexts_with_sources_in_multiple_splits': cross_split_gold_documents,
            'unique_gold_contexts_by_source_split': dict(sorted(gold_split_counts.items())),
            'candidate_corpus_source_rows': candidate_source_rows,
            'candidate_corpus_duplicate_context_groups': candidate_duplicate_context_groups,
        },
        'retrievers': retrievers,
        'interpretation': [
            'Every dev gold context is included in the fixed candidate corpus; misses are not caused by absent gold documents.',
            'A zero-score rank means the saved BM25 analyzer had no shared query unit with the gold passage; ranks above 10 had lexical overlap but were below the retrieval cutoff.',
            'A same-page alternative in top 10 is a page-lineage signal only; it does not establish that the retrieved passage supports the answer.',
            'The English-query retriever is an upper-bound diagnostic and is not a Garhwali model-quality score.',
        ],
        'limitations': [
            'The fixed candidate corpus is built from train, dev, and test contexts. This is conditional-corpus miss analysis, not unseen-page generalization.',
            'No test predictions or references were analyzed; test contexts remain in the fixed corpus exactly as in the saved dev run.',
            'The diagnostics contain hashes and counts, not copied query, answer, page-title, or passage text.',
            'The analysis does not judge whether a retrieved passage semantically answers a question.',
        ],
        'per_query': per_query,
    }
    return report


def _markdown(report):
    coverage = report['candidate_coverage']
    lines = [
        '# XORQA BM25 dev retrieval miss analysis — 2026-09-28', '',
        'This analysis checks whether each saved dev query’s gold passage exists in the fixed candidate corpus, then separates no lexical score from poor rank placement. It reads saved predictions only and does not copy query, answer, title, or passage text.', '',
        f"- Dev queries: {report['evaluation_record_count']}",
        f"- Candidate passages: {report['candidate_corpus_document_count']}",
        f"- Gold context available: {coverage['available_gold_records']}/{coverage['gold_records']}",
        f"- Unique dev gold contexts: {coverage['unique_gold_contexts']}",
        f"- Unique gold contexts also sourced from multiple splits: {coverage['unique_gold_contexts_with_sources_in_multiple_splits']}", '',
        '| Retriever | Rank 1 | Rank 2–5 | Rank 6–10 | Rank >10 | Zero score | Misses at 10 | Same-page alternatives among misses |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
    ]
    for name, result in report['retrievers'].items():
        c = result['status_counts']
        same_page_misses = sum(
            group['same_page_non_gold_passages_in_top_10']
            for status, group in result['gold_overlap_by_result_status'].items()
            if status in ('rank_11_plus', 'zero_score')
        )
        lines.append(
            f"| `{name}` | {c['rank_1']} | {c['rank_2_5']} | {c['rank_6_10']} | "
            f"{c['rank_11_plus']} | {c['zero_score']} | {result['misses_at_10']} | "
            f"{same_page_misses} |"
        )
    lines.extend([
        '', '## Gold-passage lexical overlap by outcome', '',
        'Mean shared analyzer units and mean query-unit coverage are computed between each query and its own gold context. Zero-score rows should have no shared unit for the corresponding saved BM25 analyzer; rank >10 rows do share terms but miss the top-10 cutoff.', '',
        '| Retriever | Outcome | Queries | Mean shared units | Mean query-unit coverage | Same-page alternatives in top 10 |',
        '| --- | --- | ---: | ---: | ---: | ---: |',
    ])
    for name, result in report['retrievers'].items():
        for status in STATUS_ORDER:
            group = result['gold_overlap_by_result_status'].get(status)
            if group:
                lines.append(
                    f"| `{name}` | {status} | {group['queries']} | "
                    f"{group['mean_shared_gold_analyzer_units']:.3f} | "
                    f"{group['mean_query_unit_coverage']:.3f} | "
                    f"{group['same_page_non_gold_passages_in_top_10']} |"
                )
    lines.extend([
        '', 'All dev gold contexts are available in the fixed candidate set, so the measured misses arise from lexical matching or rank placement in this setup, not missing gold passages. The corpus includes contexts from every original split; these results are not a page-held-out evaluation. Same-page alternatives are lineage signals, not proof of supporting evidence.', '',
        f"Benchmark SHA-256: `{report['lineage']['benchmark_sha256']}`  ",
        f"Predictions SHA-256: `{report['lineage']['predictions_sha256']}`  ",
        f"Parent retrieval report SHA-256: `{report['lineage']['retrieval_report_sha256']}`", '',
    ])
    return '\n'.join(lines)


def run(
    benchmark_path=DEFAULT_BENCHMARK,
    predictions_path=DEFAULT_PREDICTIONS,
    retrieval_report_path=DEFAULT_RETRIEVAL_REPORT,
    output_dir=DEFAULT_OUTPUT,
):
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
    benchmark_rows = read_jsonl(benchmark_path)
    prediction_rows = read_jsonl(predictions_path)
    report = analyze_rows(benchmark_rows, prediction_rows, retrieval_report)
    report['lineage'] = {
        'benchmark_path': str(benchmark_path),
        'benchmark_sha256': benchmark_sha,
        'predictions_path': str(predictions_path),
        'predictions_sha256': predictions_sha,
        'retrieval_report_path': str(retrieval_report_path),
        'retrieval_report_sha256': retrieval_report_sha,
        'retrieval_report_benchmark_sha256_verified': True,
        'candidate_corpus_sha256': retrieval_report['passage_corpus_sha256'],
        'test_rows_scored': 0,
        'generator_sha256': sha256_file(Path(__file__)),
    }
    report['outputs'] = {
        'json': str(output_dir / 'report.json'),
        'markdown': str(output_dir / 'report.md'),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    (output_dir / 'report.md').write_text(_markdown(report), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument('--predictions', type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument('--retrieval-report', type=Path, default=DEFAULT_RETRIEVAL_REPORT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.benchmark, args.predictions, args.retrieval_report, args.output_dir)
    print(json.dumps({
        'evaluation_record_count': report['evaluation_record_count'],
        'candidate_coverage': report['candidate_coverage'],
        'miss_counts_at_10': {
            name: data['misses_at_10'] for name, data in report['retrievers'].items()
        },
        'outputs': report['outputs'],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
