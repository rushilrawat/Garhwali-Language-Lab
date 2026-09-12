#!/usr/bin/env python3
"""Create resumable SraVaani drafts for untranscribed VAANI Garhwali audio."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from run_sravaani_comparison import MODEL, MODEL_ID, REVISION, ROOT, validate_model_dir


DEFAULT_INPUT = ROOT / 'data/processed/model_ready/transcripts/untranscribed_queue.jsonl'
DEFAULT_OUTPUT = ROOT / 'data/processed/model_ready/transcripts/machine_drafts_sravaani.jsonl'


def read_jsonl(path):
    path = Path(path)
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as handle:
        return [json.loads(line) for line in handle if line.strip()]


def pending_rows(rows, output_path):
    completed = {row['audio_sha256'] for row in read_jsonl(output_path)}
    return sorted(
        (row for row in rows if row['audio_sha256'] not in completed),
        key=lambda row: (row.get('transcription_priority', 999), row['audio_sha256']),
    )


def build_draft_record(row, transcript):
    return {
        **row,
        'machine_transcript': transcript,
        'machine_transcript_model': MODEL_ID,
        'machine_transcript_model_revision': REVISION,
        'confidence_is_available': False,
        'training_eligible': False,
        'experimental_training_eligible': True,
        'review_status': 'machine_draft_noisy_experimental',
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--max-records', type=int, default=100)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--device', choices=('auto', 'mps', 'cuda', 'cpu'), default='auto')
    args = parser.parse_args()

    cache = ROOT / '.cache/huggingface'
    os.environ.setdefault('HF_HOME', str(cache))
    os.environ.setdefault('HF_MODULES_CACHE', str(cache / 'modules'))
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import AutoModel

    if args.device == 'auto':
        if torch.cuda.is_available():
            args.device = 'cuda'
        elif torch.backends.mps.is_available():
            args.device = 'mps'
        else:
            args.device = 'cpu'
    model_path = validate_model_dir(args.model)
    model = AutoModel.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    if args.device in ('mps', 'cuda'):
        model = model.half()
    model = model.to(args.device).eval()

    rows = pending_rows(read_jsonl(args.input), args.output)
    if args.max_records:
        rows = rows[:args.max_records]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('a', encoding='utf-8') as output, torch.no_grad():
        for offset in range(0, len(rows), args.batch_size):
            batch = rows[offset:offset + args.batch_size]
            paths = [str(ROOT / row['local_audio_path']) for row in batch]
            hypotheses = model.transcribe(paths, batch_size=args.batch_size)
            for row, hypothesis in zip(batch, hypotheses):
                output.write(json.dumps(
                    build_draft_record(row, hypothesis),
                    ensure_ascii=False,
                    sort_keys=True,
                ) + '\n')
            output.flush()
            print(f'draft={min(offset + len(batch), len(rows))}/{len(rows)}', flush=True)


if __name__ == '__main__':
    main()
