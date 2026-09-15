#!/usr/bin/env python3
"""Attach local ASR evidence to ambiguous human-transcript review rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path

from run_asr_baseline import read_audio


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/cleaned/audio_transcripts.jsonl'
OUTPUT = ROOT / 'data/processed/model_ready/transcripts/supervised_review_model_evidence.jsonl'
REPORT = ROOT / 'data/processed/model_ready/transcripts/supervised_review_model_evidence_report.json'
MODELS = (
    ROOT / 'models/whisper-tiny-garhwali-v0.1',
    ROOT / 'models/whisper-tiny-garhwali-v0.2',
)
BENGALI_FLAGS = {
    'bengali_script',
    'bengali-script-in-garhwali-config',
    'bengali-script-under-garhwali-label',
}


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def normalize_for_comparison(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text or '')).strip()


def select_review_rows(rows):
    selected = []
    for row in rows:
        flags = set(row.get('transcript_review_flags') or [])
        if flags and not flags.intersection(BENGALI_FLAGS):
            selected.append(row)
    return sorted(selected, key=lambda row: row['audio_sha256'])


def clean_release_text(reference):
    changes = []
    signals = []
    release = reference
    if release.count('(') and not release.count(')'):
        release = re.sub(r'\s*\(\s*', ' ', release)
        release = normalize_for_comparison(release)
        changes.append('unmatched_open_parenthesis_removed')
    elif re.search(r'\([^()]+\)', release):
        signals.append('parenthetical_content_alignment_review')
    return release, changes, signals


def build_review_record(row, hypotheses):
    reference = row.get('asr_target_clean') or row.get('asr_target') or ''
    release, changes, signals = clean_release_text(reference)
    if 'possibly_incomplete' in (row.get('deep_cleanup_flags') or []):
        signals.append('possibly_incomplete_reference')
    normalized_reference = normalize_for_comparison(reference)
    normalized = {
        model: normalize_for_comparison(text)
        for model, text in sorted(hypotheses.items())
    }
    distinct = sorted(set(normalized.values()))
    models_agree = len(distinct) == 1
    all_match = bool(normalized) and all(
        text == normalized_reference for text in normalized.values()
    )
    status = (
        'model_supported_listening_review_pending'
        if all_match else 'listening_review_required'
    )
    return {
        'audio_sha256': row['audio_sha256'],
        'local_audio_path': row.get('local_audio_path'),
        'duration_seconds': row.get('duration_seconds'),
        'district': row.get('district'),
        'reference_text': reference,
        'reference_sha256': hashlib.sha256(reference.encode()).hexdigest(),
        'release_text': release,
        'release_text_sha256': hashlib.sha256(release.encode()).hexdigest(),
        'recommended_text': release,
        'reference_changed': False,
        'automatic_changes': changes,
        'review_signals': sorted(signals),
        'original_review_flags': row.get('transcript_review_flags') or [],
        'model_evidence': {
            'hypotheses': normalized,
            'models_agree': models_agree,
            'all_models_match_reference': all_match,
            'agreement_is_accuracy_proof': False,
        },
        'review_status': status,
    }


def model_hypotheses(rows, model_path, device):
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(
        model_path, local_files_only=True
    ).to(device).eval()
    audio = [read_audio(ROOT / row['local_audio_path']) for row in rows]
    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors='pt',
        return_attention_mask=True,
    )
    with torch.no_grad():
        generated = model.generate(
            inputs.input_features.to(device),
            attention_mask=inputs.attention_mask.to(device),
            language='hi',
            task='transcribe',
            max_new_tokens=128,
        )
    return processor.batch_decode(generated, skip_special_tokens=True)


def run(input_path=INPUT, output_path=OUTPUT, report_path=REPORT,
        model_paths=MODELS, device='auto'):
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    import torch

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    rows = select_review_rows(read_jsonl(input_path))
    evidence = {row['audio_sha256']: {} for row in rows}
    for model_path in model_paths:
        model_path = Path(model_path)
        hypotheses = model_hypotheses(rows, model_path, device)
        for row, hypothesis in zip(rows, hypotheses):
            evidence[row['audio_sha256']][model_path.name] = hypothesis
    results = [
        build_review_record(row, evidence[row['audio_sha256']]) for row in rows
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                for row in results),
        encoding='utf-8',
    )
    report = {
        'records': len(results),
        'models': [Path(path).name for path in model_paths],
        'device': device,
        'models_agree': sum(row['model_evidence']['models_agree'] for row in results),
        'all_models_match_reference': sum(
            row['model_evidence']['all_models_match_reference'] for row in results
        ),
        'references_changed': sum(row['reference_changed'] for row in results),
        'release_values_changed': sum(bool(row['automatic_changes']) for row in results),
        'listening_review_required': sum(
            row['review_status'] == 'listening_review_required' for row in results
        ),
        'policy': 'Model output is supporting evidence and never replaces a human reference automatically.',
    }
    Path(report_path).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--report', type=Path, default=REPORT)
    parser.add_argument('--models', type=Path, nargs='+', default=list(MODELS))
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        args.input, args.output, args.report, args.models, args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
