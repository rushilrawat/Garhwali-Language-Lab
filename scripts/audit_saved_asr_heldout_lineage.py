#!/usr/bin/env python3
"""Reconcile historical ASR test outputs to the fixed local audio manifest.

This is a provenance audit only. It does not run inference or select a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ASR_ROOT = ROOT / 'data/processed/evaluation/asr'
DEFAULT_MANIFEST = ASR_ROOT / 'audio_score_calibration_manifest.jsonl'
DEFAULT_OUTPUT = ASR_ROOT / 'heldout_lineage_audit_2026-09-28'
HEX_256 = re.compile(r'^[0-9a-f]{64}$')
AGGREGATE_FIELDS = (
    'word_errors', 'reference_words', 'character_errors', 'reference_characters',
    'wer', 'cer',
)

RUNS = (
    {
        'name': 'SraVaani 1.0 base',
        'report': ASR_ROOT / 'sravaani_1_0/report.json',
        'predictions': ASR_ROOT / 'sravaani_1_0/predictions.jsonl',
        'aggregate_key': None,
    },
    {
        'name': 'Six-configuration decoder sweep, selected configuration',
        'report': ASR_ROOT / 'sravaani_decoding_sweep/cloud_output/report.json',
        'predictions': ASR_ROOT / 'sravaani_decoding_sweep/cloud_output/selected-test-predictions.json',
        'aggregate_key': 'selected_test',
    },
    {
        'name': '61-trial decoder/joint fine-tune',
        'report': ASR_ROOT / 'sravaani_refined_61/cloud_output/report.json',
        'predictions': ASR_ROOT / 'sravaani_refined_61/cloud_output/held-out-test-predictions.json',
        'aggregate_key': 'held_out_test',
    },
    {
        'name': 'Expanded-human-transcript fine-tune',
        'report': ASR_ROOT / 'sravaani_expanded_human/cloud_output/report.json',
        'predictions': ASR_ROOT / 'sravaani_expanded_human/cloud_output/held-out-test-predictions.json',
        'aggregate_key': 'held_out_test',
    },
    {
        'name': 'Original 102-step human-reference adaptation',
        'report': ASR_ROOT / 'sravaani_finetune/cloud_output/held_out_evaluation/report.json',
        'predictions': ASR_ROOT / 'sravaani_finetune/cloud_output/held_out_evaluation/predictions.jsonl',
        'aggregate_key': None,
    },
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
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


def read_records(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    if path.suffix == '.jsonl':
        return read_jsonl(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise ValueError(f'{path}: expected a JSON array of objects')
    return value


def _audio_id(row: dict[str, Any], *, row_number: int, source: str) -> str:
    filepath = row.get('audio_filepath')
    audio_id = row.get('audio_sha256')
    if isinstance(filepath, str) and filepath:
        basename = Path(filepath).name
        path_id = basename.rsplit('.', 1)[0] if '.' in basename else basename
        if not HEX_256.fullmatch(path_id):
            raise ValueError(f'{source} row {row_number}: audio filename is not a SHA-256 ID')
        if audio_id is not None and audio_id != path_id:
            raise ValueError(f'{source} row {row_number}: audio hash disagrees with filename')
        audio_id = path_id
    if not isinstance(audio_id, str) or not HEX_256.fullmatch(audio_id):
        raise ValueError(f'{source} row {row_number}: missing valid audio SHA-256 ID')
    return audio_id


def _counter(row: dict[str, Any], key: str, *, row_number: int) -> int:
    value = row.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f'prediction row {row_number}: {key} must be a nonnegative integer')
    return value


def reconcile_prediction_rows(
    manifest_rows: list[dict[str, Any]],
    prediction_rows: list[dict[str, Any]],
    expected_aggregate: dict[str, Any],
) -> dict[str, Any]:
    """Verify exact audio/reference identity and the saved aggregate counters."""
    manifest_by_id: dict[str, dict[str, Any]] = {}
    manifest_order = []
    for index, row in enumerate(manifest_rows, start=1):
        audio_id = row.get('audio_sha256')
        if not isinstance(audio_id, str) or not HEX_256.fullmatch(audio_id):
            raise ValueError(f'manifest row {index}: invalid audio_sha256')
        if audio_id in manifest_by_id:
            raise ValueError(f'duplicate manifest audio hash: {audio_id}')
        reference = row.get('asr_target_clean')
        if not isinstance(reference, str):
            raise ValueError(f'manifest row {index}: missing cleaned ASR reference')
        manifest_by_id[audio_id] = row
        manifest_order.append(audio_id)
    if not manifest_by_id:
        raise ValueError('manifest has no rows')

    predictions_by_id: dict[str, dict[str, Any]] = {}
    prediction_order = []
    sums = {key: 0 for key in AGGREGATE_FIELDS[:4]}
    for index, row in enumerate(prediction_rows, start=1):
        audio_id = _audio_id(row, row_number=index, source='prediction')
        if audio_id in predictions_by_id:
            raise ValueError(f'duplicate prediction audio hash: {audio_id}')
        predictions_by_id[audio_id] = row
        prediction_order.append(audio_id)
        for key in sums:
            sums[key] += _counter(row, key, row_number=index)

    if set(predictions_by_id) != set(manifest_by_id):
        missing = len(set(manifest_by_id) - set(predictions_by_id))
        unexpected = len(set(predictions_by_id) - set(manifest_by_id))
        raise ValueError(
            'prediction audio IDs must exactly match manifest IDs '
            f'(missing={missing}, unexpected={unexpected})')

    reference_digest_rows = []
    for audio_id in sorted(manifest_by_id):
        prediction = predictions_by_id[audio_id]
        if prediction.get('reference') != manifest_by_id[audio_id]['asr_target_clean']:
            raise ValueError(f'{audio_id}: clean reference mismatch')
        reference_digest_rows.append(
            f"{audio_id}\t{manifest_by_id[audio_id]['asr_target_clean']}")

    if sums['reference_words'] <= 0 or sums['reference_characters'] <= 0:
        raise ValueError('reference denominators must be positive')
    sums['wer'] = sums['word_errors'] / sums['reference_words']
    sums['cer'] = sums['character_errors'] / sums['reference_characters']
    for key in AGGREGATE_FIELDS:
        expected = expected_aggregate.get(key)
        observed = sums[key]
        if isinstance(observed, float):
            if isinstance(expected, bool) or not isinstance(expected, (int, float)) or not math.isclose(
                observed, float(expected), rel_tol=1e-12, abs_tol=1e-12,
            ):
                raise ValueError(f'reported aggregate {key} does not reconcile')
        elif isinstance(expected, bool) or not isinstance(expected, int) or expected != observed:
            raise ValueError(f'reported aggregate {key} does not reconcile')

    ordered_digest = sha256_bytes('\n'.join(manifest_order).encode('ascii'))
    reference_digest = sha256_bytes('\n'.join(reference_digest_rows).encode('utf-8'))
    return {
        'record_count': len(manifest_by_id),
        'audio_ids_match': len(predictions_by_id),
        'clean_references_match': len(reference_digest_rows),
        'ordered_audio_ids_match': prediction_order == manifest_order,
        'audio_id_set_sha256': sha256_bytes('\n'.join(sorted(manifest_by_id)).encode('ascii')),
        'manifest_ordered_audio_ids_sha256': ordered_digest,
        'reference_id_pairs_sha256': reference_digest,
        **sums,
    }


def _percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def paired_speaker_bootstrap(
    manifest_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    *, replicates: int = 10_000, seed: int = 1729,
) -> dict[str, Any]:
    """Compare saved per-row WER/CER by paired speaker-cluster bootstrap."""
    import random

    if replicates < 1:
        raise ValueError('replicates must be positive')
    manifest_by_id = {row['audio_sha256']: row for row in manifest_rows}
    if len(manifest_by_id) != len(manifest_rows) or not manifest_by_id:
        raise ValueError('manifest audio hashes must be nonempty and unique')

    def index(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
        indexed = {}
        for row_number, row in enumerate(rows, start=1):
            audio_id = _audio_id(row, row_number=row_number, source=label)
            if audio_id in indexed:
                raise ValueError(f'{label}: duplicate prediction audio hash')
            indexed[audio_id] = row
        if set(indexed) != set(manifest_by_id):
            raise ValueError(f'{label}: prediction IDs do not match fixed manifest')
        return indexed

    baseline = index(baseline_rows, 'baseline')
    candidate = index(candidate_rows, 'candidate')
    grouped: dict[str, list[tuple[int, int, int, int, int, int]]] = {}
    for audio_id, source in manifest_by_id.items():
        speaker_id = source.get('speaker_id')
        if not isinstance(speaker_id, str) or not speaker_id.strip():
            raise ValueError(f'{audio_id}: missing speaker identity for clustered resampling')
        if speaker_id.strip().lower() in {
            'unknown', 'unidentified', 'none', 'null', 'n/a', 'na', '0', 'speaker_unknown',
        }:
            raise ValueError(f'{audio_id}: placeholder speaker identity cannot define a cluster')
        base_row = baseline[audio_id]
        candidate_row = candidate[audio_id]
        reference = source['asr_target_clean']
        if base_row.get('reference') != reference or candidate_row.get('reference') != reference:
            raise ValueError(f'{audio_id}: paired runs do not share the fixed cleaned reference')
        for key in ('reference_words', 'reference_characters'):
            base_denominator = _counter(base_row, key, row_number=1)
            candidate_denominator = _counter(candidate_row, key, row_number=1)
            if base_denominator <= 0:
                raise ValueError(f'{audio_id}: paired reference denominator is not positive for {key}')
            if base_denominator != candidate_denominator:
                raise ValueError(f'{audio_id}: paired reference denominator differs for {key}')
        grouped.setdefault(speaker_id, []).append((
            _counter(base_row, 'word_errors', row_number=1),
            _counter(candidate_row, 'word_errors', row_number=1),
            _counter(base_row, 'reference_words', row_number=1),
            _counter(base_row, 'character_errors', row_number=1),
            _counter(candidate_row, 'character_errors', row_number=1),
            _counter(base_row, 'reference_characters', row_number=1),
        ))
    if not grouped:
        raise ValueError('no speaker groups available for paired bootstrap')

    def deltas(clusters: list[list[tuple[int, int, int, int, int, int]]]) -> tuple[float, float]:
        base_words = candidate_words = word_count = 0
        base_chars = candidate_chars = char_count = 0
        for cluster in clusters:
            for base_word, candidate_word, words, base_char, candidate_char, chars in cluster:
                base_words += base_word
                candidate_words += candidate_word
                word_count += words
                base_chars += base_char
                candidate_chars += candidate_char
                char_count += chars
        return (
            candidate_words / word_count - base_words / word_count,
            candidate_chars / char_count - base_chars / char_count,
        )

    clusters = [grouped[key] for key in sorted(grouped)]
    word_delta, char_delta = deltas(clusters)
    rng = random.Random(seed)
    word_samples, char_samples = [], []
    for _ in range(replicates):
        sample = [clusters[rng.randrange(len(clusters))] for _ in clusters]
        word_value, char_value = deltas(sample)
        word_samples.append(word_value)
        char_samples.append(char_value)
    return {
        'record_count': len(manifest_by_id),
        'speaker_cluster_count': len(clusters),
        'bootstrap_replicates': replicates,
        'seed': seed,
        'wer_delta_candidate_minus_base': word_delta,
        'wer_delta_ci95': [_percentile(word_samples, 0.025), _percentile(word_samples, 0.975)],
        'cer_delta_candidate_minus_base': char_delta,
        'cer_delta_ci95': [_percentile(char_samples, 0.025), _percentile(char_samples, 0.975)],
    }


def _aggregate(report: dict[str, Any], aggregate_key: str | None) -> dict[str, Any]:
    if aggregate_key is None:
        value = report
    else:
        value = report.get(aggregate_key)
    if not isinstance(value, dict):
        raise ValueError(f'missing aggregate report section: {aggregate_key}')
    return {key: value.get(key) for key in AGGREGATE_FIELDS}


def _declared_manifest_sha(report: dict[str, Any]) -> str | None:
    for key in ('evaluation_manifest_sha256', 'test_manifest_sha256', 'manifest_sha256'):
        value = report.get(key)
        if isinstance(value, str):
            return value
    return None


def _test_use_flag(report: dict[str, Any]) -> bool | None:
    for key in ('selection_used_test_split', 'test_used_for_training_or_selection'):
        value = report.get(key)
        if isinstance(value, bool):
            return value
    return None


def run(manifest_path: Path = DEFAULT_MANIFEST, output_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    manifest_rows = read_jsonl(manifest_path)
    manifest_sha = sha256_file(manifest_path)
    ids = [row.get('audio_sha256') for row in manifest_rows]
    if len(ids) != len(set(ids)):
        raise ValueError('fixed manifest contains duplicate audio hashes')

    run_results = []
    prediction_rows_by_name = {}
    for profile in RUNS:
        report_path = Path(profile['report'])
        report = json.loads(report_path.read_text(encoding='utf-8'))
        if not isinstance(report, dict):
            raise ValueError(f'{report_path}: expected a JSON object')
        aggregate = _aggregate(report, profile['aggregate_key'])
        if profile['name'] == RUNS[0]['name']:
            if _declared_manifest_sha(report) != manifest_sha:
                raise ValueError('base model report does not pin the fixed manifest bytes')
            if report.get('evaluation_records') != len(manifest_rows):
                raise ValueError('base model report row count does not match the fixed manifest')
        prediction_path = profile['predictions']
        if prediction_path is None:
            if _declared_manifest_sha(report) != manifest_sha:
                raise ValueError(f"{profile['name']}: base report does not pin fixed manifest")
            if report.get('evaluation_records') != len(manifest_rows):
                raise ValueError(f"{profile['name']}: base report row count does not match")
            prediction_result = None
        else:
            prediction_path = Path(prediction_path)
            prediction_rows = read_records(prediction_path)
            prediction_result = reconcile_prediction_rows(
                manifest_rows, prediction_rows, aggregate)
            prediction_rows_by_name[profile['name']] = prediction_rows

        run_results.append({
            'name': profile['name'],
            'report_path': report_path.relative_to(ROOT).as_posix(),
            'report_sha256': sha256_file(report_path),
            'predictions_path': (
                Path(prediction_path).relative_to(ROOT).as_posix()
                if prediction_path is not None else None),
            'predictions_sha256': sha256_file(Path(prediction_path)) if prediction_path else None,
            'checkpoint_sha256': report.get('best_checkpoint_sha256') or report.get('checkpoint_sha256'),
            'declared_manifest_sha256': _declared_manifest_sha(report),
            'declared_manifest_matches_current_bytes': (
                _declared_manifest_sha(report) == manifest_sha),
            'test_used_for_training_or_selection': _test_use_flag(report),
            'aggregate': aggregate,
            'row_reconciliation': prediction_result,
        })

    base_name = RUNS[0]['name']
    paired_comparisons = {}
    for profile in RUNS[1:]:
        candidate_name = profile['name']
        paired_comparisons[candidate_name] = paired_speaker_bootstrap(
            manifest_rows,
            prediction_rows_by_name[base_name],
            prediction_rows_by_name[candidate_name],
        )

    output = {
        'schema_version': 1,
        'audit_type': 'posthoc_saved_asr_test_lineage',
        'inference_run': False,
        'model_selection_run': False,
        'fixed_manifest': {
            'path': manifest_path.relative_to(ROOT).as_posix(),
            'sha256': manifest_sha,
            'record_count': len(manifest_rows),
            'unique_audio_hashes': len(ids),
            'reference_field': 'asr_target_clean',
        },
        'runs': run_results,
        'paired_speaker_bootstrap_vs_base': paired_comparisons,
        'conclusion': {
            'same_fixed_test_ids_and_clean_references': True,
            'runs_with_row_level_prediction_reconciliation': sum(
                item['row_reconciliation'] is not None for item in run_results),
            'run_count': len(run_results),
            'historical_only': True,
            'limitations': [
                'These test rows and aggregate metrics were used previously; this audit does not establish independent accuracy.',
                'SraVaani upstream exposure and native-speaker reference correctness remain unresolved.',
                'The original 102-step run declares a different input-manifest byte hash; its saved per-row audio hashes and cleaned references nevertheless reconcile exactly to the fixed current manifest.',
            ],
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / 'report.json'
    md_path = output_dir / 'report.md'
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    md_path.write_text(render_markdown(output), encoding='utf-8')
    return output


def render_markdown(report: dict[str, Any]) -> str:
    manifest = report['fixed_manifest']
    lines = [
        '# Post-hoc ASR held-out lineage audit (2026-09-28)',
        '',
        'This audit verifies saved output identity, aggregate arithmetic, and retrospective paired uncertainty. It ran no inference and did not select a model.',
        '',
        f"Fixed manifest: `{manifest['record_count']}` rows; SHA-256 `{manifest['sha256']}`.",
        '',
        '| Run | Audio IDs | Clean references | WER | CER | Original manifest hash matches current bytes |',
        '| --- | ---: | ---: | ---: | ---: | --- |',
    ]
    for item in report['runs']:
        row = item['row_reconciliation']
        ids = str(row['audio_ids_match']) if row else 'n/a'
        refs = str(row['clean_references_match']) if row else 'n/a'
        values = item['aggregate']
        matches = 'yes' if item['declared_manifest_matches_current_bytes'] else (
            'not recorded' if item['declared_manifest_sha256'] is None else 'no; post-hoc rows match')
        lines.append(
            f"| {item['name']} | {ids} | {refs} | {float(values['wer']):.4%} | "
            f"{float(values['cer']):.4%} | {matches} |")
    lines.extend([
        '',
        'All five runs identify the same fixed 112-row evaluation set. Every saved prediction file matches all 112 audio hashes and all 112 cleaned references; the row counters reproduce each aggregate WER/CER report. The base report directly records the fixed manifest hash and row count.',
        '',
        '| Candidate vs base | WER delta, percentage points (95% speaker-cluster interval) | CER delta, percentage points (95% speaker-cluster interval) | Speaker clusters |',
        '| --- | ---: | ---: | ---: |',
    ])
    for name, comparison in report['paired_speaker_bootstrap_vs_base'].items():
        wer_ci = comparison['wer_delta_ci95']
        cer_ci = comparison['cer_delta_ci95']
        lines.append(
            f"| {name} | {comparison['wer_delta_candidate_minus_base'] * 100:+.3f} "
            f"[{wer_ci[0] * 100:+.3f}, {wer_ci[1] * 100:+.3f}] | "
            f"{comparison['cer_delta_candidate_minus_base'] * 100:+.3f} "
            f"[{cer_ci[0] * 100:+.3f}, {cer_ci[1] * 100:+.3f}] | "
            f"{comparison['speaker_cluster_count']} |")
    lines.extend([
        '',
        'Positive deltas mean higher error than the base. These paired intervals are retrospective descriptions of a previously scored public test; they were not used to select or promote a model. They do not establish independent generalization, upstream SraVaani exposure is unresolved, and references have not been native-adjudicated.',
        '',
        'The 102-step run’s recorded manifest byte hash differs from the current manifest hash, but its saved predictions reconcile by all audio-hash IDs and cleaned references. This verifies example identity; it does not explain the historical serialization difference.',
        '',
        'No fresh inference or model selection occurred.',
        '',
        'Machine-readable report: `report.json` (written beside this Markdown file).',
        '',
    ])
    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    report = run(args.manifest, args.output_dir)
    print(json.dumps({
        'fixed_rows': report['fixed_manifest']['record_count'],
        'runs_reconciled': report['conclusion']['run_count'],
        'prediction_files_reconciled': report['conclusion']['runs_with_row_level_prediction_reconciliation'],
        'output': str(args.output_dir),
    }, indent=2))


if __name__ == '__main__':
    main()
