#!/usr/bin/env python3
"""Generate resumable Whisper alternatives for the SraVaani recovery queue."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path

from analyze_sravaani_drafts import analyze_row, normalize_hypothesis
from run_asr_baseline import read_audio


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_queue.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_report.json'
MODEL = ROOT / 'models/whisper-tiny-garhwali-v0.2'
MODEL_ID = 'whisper-tiny-garhwali-v0.2'
FLAG_WEIGHTS = {
    'empty_transcript': 100,
    'bengali_script': 80,
    'no_devanagari_letters': 80,
    'mixed_script': 50,
    'repeated_token_loop': 60,
    'implausibly_short_for_duration': 70,
    'implausibly_long_for_duration': 70,
    'frequent_identical_hypothesis': 20,
    'decoding_replacement_character': 50,
}


def read_rows(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def severity(flags):
    return sum(FLAG_WEIGHTS.get(flag, 10) for flag in set(flags))


def candidate_flags(text, duration, hypothesis_frequency=1):
    row = analyze_row(
        {'machine_transcript': text, 'duration_seconds': duration},
        hypothesis_frequency=hypothesis_frequency,
    )
    flags = list(row['machine_transcript_quality']['flags'])
    if '\ufffd' in text:
        flags.append('decoding_replacement_character')
    return sorted(set(flags))


def build_result(row, whisper_text, candidate_frequency=1):
    original = normalize_hypothesis(row.get('original_machine_transcript', ''))
    candidate = normalize_hypothesis(whisper_text)
    original_flags = sorted(set(row.get('quality_flags') or []))
    alternative_flags = candidate_flags(
        candidate, row.get('duration_seconds'), candidate_frequency
    )
    advantage = severity(original_flags) - severity(alternative_flags)
    preference = 'whisper_candidate' if candidate and advantage > 0 else 'sravaani_original'
    result = {
        **row,
        'original_machine_transcript': original,
        'whisper_candidate': candidate,
        'whisper_candidate_model': MODEL_ID,
        'whisper_candidate_frequency': candidate_frequency,
        'whisper_candidate_flags': alternative_flags,
        'original_quality_severity': severity(original_flags),
        'whisper_quality_severity': severity(alternative_flags),
        'quality_advantage': advantage,
        'structural_preference': preference,
        'automatic_promotion': False,
        'original_preserved': True,
        'active_for_experiment': True,
    }
    result.pop('review_preference', None)
    return result


def finalize_output(output_path):
    """Reassess candidates with corpus-level frequencies and atomically rewrite."""
    output_path = Path(output_path)
    rows = read_rows(output_path)
    frequencies = Counter(row['whisper_candidate'] for row in rows)
    finalized = [
        build_result(row, row['whisper_candidate'], frequencies[row['whisper_candidate']])
        for row in rows
    ]
    temporary = output_path.with_suffix(output_path.suffix + '.tmp')
    temporary.write_text(
        ''.join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
            for row in finalized
        ),
        encoding='utf-8',
    )
    temporary.replace(output_path)
    return finalized


def pending_rows(input_path, output_path, maximum):
    completed = {row['audio_sha256'] for row in read_rows(output_path)}
    rows = [row for row in read_rows(input_path) if row['audio_sha256'] not in completed]
    return rows[:maximum] if maximum else rows


def summarize(output_path, input_path=None):
    rows = read_rows(output_path)
    preferences = Counter(row['structural_preference'] for row in rows)
    source_flags = Counter(flag for row in rows for flag in row.get('quality_flags', []))
    candidate_flags_count = Counter(
        flag for row in rows for flag in row['whisper_candidate_flags']
    )
    summary = {
        'run_id': 'sravaani-recovery-whisper-v0.2',
        'model': MODEL_ID,
        'records': len(rows),
        'unique_audio_hashes': len({row['audio_sha256'] for row in rows}),
        'structural_preferences': dict(sorted(preferences.items())),
        'source_quality_flags': dict(sorted(source_flags.items())),
        'candidate_quality_flags': dict(sorted(candidate_flags_count.items())),
        'candidates_without_automated_flags': sum(
            not row['whisper_candidate_flags'] for row in rows
        ),
        'empty_candidates': sum(not row['whisper_candidate'] for row in rows),
        'candidates_with_replacement_character': sum(
            '\ufffd' in row['whisper_candidate'] for row in rows
        ),
        'candidates_with_frequency_gte_10': sum(
            row.get('whisper_candidate_frequency', 1) >= 10 for row in rows
        ),
        'exact_transcript_matches': sum(
            row['whisper_candidate'] == row['original_machine_transcript'] for row in rows
        ),
        'structurally_improved': sum(row['quality_advantage'] > 0 for row in rows),
        'structurally_equal': sum(row['quality_advantage'] == 0 for row in rows),
        'structurally_worse': sum(row['quality_advantage'] < 0 for row in rows),
        'automatic_promotions': sum(row['automatic_promotion'] for row in rows),
        'originals_preserved': all(row['original_preserved'] for row in rows),
    }
    if input_path is not None:
        expected = {row['audio_sha256'] for row in read_rows(input_path)}
        observed = {row['audio_sha256'] for row in rows}
        summary['coverage'] = {
            'expected_unique_audio_hashes': len(expected),
            'missing_audio_hashes': len(expected - observed),
            'unexpected_audio_hashes': len(observed - expected),
        }
    return summary


def write_report(summary, report_path):
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )


def run(input_path=INPUT, output_path=OUTPUT, report_path=REPORT, model_path=MODEL,
        maximum=0, batch_size=8, device='auto'):
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    rows = pending_rows(input_path, output_path, maximum)
    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(
        model_path, local_files_only=True
    ).to(device).eval()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('a', encoding='utf-8') as output, torch.no_grad():
        for offset in range(0, len(rows), batch_size):
            batch = rows[offset:offset + batch_size]
            audio = [read_audio(ROOT / row['local_audio_path']) for row in batch]
            inputs = processor(
                audio, sampling_rate=16000, return_tensors='pt',
                return_attention_mask=True,
            )
            features = inputs.input_features.to(device)
            attention_mask = inputs.attention_mask.to(device)
            generated = model.generate(
                features, attention_mask=attention_mask,
                language='hi', task='transcribe', max_new_tokens=128,
            )
            hypotheses = processor.batch_decode(generated, skip_special_tokens=True)
            for row, hypothesis in zip(batch, hypotheses):
                output.write(json.dumps(
                    build_result(row, hypothesis), ensure_ascii=False, sort_keys=True
                ) + '\n')
            output.flush()
            print(f'redecoded={offset + len(batch)}/{len(rows)}', flush=True)
    finalize_output(output_path)
    summary = summarize(output_path, input_path)
    if report_path:
        write_report(summary, report_path)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--max-records', type=int, default=0)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--summarize-only', action='store_true')
    args = parser.parse_args()
    if args.summarize_only:
        finalize_output(args.output)
        summary = summarize(args.output, args.input)
        write_report(summary, args.report)
        print(json.dumps(summary, indent=2, sort_keys=True))
        return
    print(json.dumps(run(
        args.input, args.output, args.report, args.model, args.max_records,
        args.batch_size, args.device,
    ), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
