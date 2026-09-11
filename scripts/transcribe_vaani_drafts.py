#!/usr/bin/env python3
"""Create resumable, review-only machine transcript drafts for unlabelled VAANI audio."""

import argparse
import json
import math
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
DEFAULT_OUTPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts.jsonl'
DEFAULT_MODEL = ROOT / 'models/whisper-tiny-garhwali-v0.2'


def read_jsonl(path):
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def pending_rows(rows, output_path):
    completed = {row['audio_sha256'] for row in read_jsonl(Path(output_path))}
    return sorted(
        (row for row in rows if row['audio_sha256'] not in completed),
        key=lambda row: (row.get('transcription_priority', 999), row['audio_sha256']),
    )


def build_draft_record(row, transcript, mean_token_log_probability, model_name):
    confidence = math.exp(mean_token_log_probability) if math.isfinite(mean_token_log_probability) else 0.0
    return {
        **row,
        'machine_transcript': transcript,
        'machine_transcript_model': str(model_name),
        'mean_token_log_probability': mean_token_log_probability,
        'token_confidence_uncalibrated': round(confidence, 8),
        'confidence_is_calibrated': False,
        'training_eligible': False,
        'review_status': 'machine_draft_needs_native_review',
    }


def generate_transcript_and_score(model, processor, features):
    """Generate normally, then score that fixed sequence in a separate forward pass."""
    generated = model.generate(
        features,
        language='hi',
        task='transcribe',
        max_new_tokens=128,
    )
    scored = model(input_features=features, labels=generated)
    mean_log_probability = float((-scored.loss).detach().cpu())
    transcript = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
    return transcript, mean_log_probability


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--model', default=str(DEFAULT_MODEL))
    parser.add_argument('--max-records', type=int, default=100)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--local-files-only', action='store_true')
    args = parser.parse_args()

    os.environ.setdefault('HF_HOME', str(ROOT / '.cache/huggingface'))
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from run_asr_baseline import read_audio

    device = 'mps' if args.device == 'auto' and torch.backends.mps.is_available() else args.device
    if device == 'auto':
        device = 'cpu'
    processor = WhisperProcessor.from_pretrained(
        args.model,
        cache_dir=ROOT / '.cache/huggingface/hub',
        local_files_only=args.local_files_only,
    )
    model = WhisperForConditionalGeneration.from_pretrained(
        args.model,
        cache_dir=ROOT / '.cache/huggingface/hub',
        local_files_only=args.local_files_only,
    ).to(device)
    model.eval()

    rows = pending_rows(read_jsonl(args.input), args.output)
    if args.max_records:
        rows = rows[:args.max_records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('a', encoding='utf-8') as output:
        with torch.no_grad():
            for index, row in enumerate(rows, start=1):
                audio = read_audio(ROOT / row['local_audio_path'])
                features = processor(audio, sampling_rate=16000, return_tensors='pt').input_features.to(device)
                transcript, mean_log_probability = generate_transcript_and_score(
                    model, processor, features
                )
                draft = build_draft_record(row, transcript, mean_log_probability, args.model)
                output.write(json.dumps(draft, ensure_ascii=False, sort_keys=True) + '\n')
                output.flush()
                print(f"draft={index}/{len(rows)} audio_sha256={row['audio_sha256']}", flush=True)


if __name__ == '__main__':
    main()
