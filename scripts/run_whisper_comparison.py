#!/usr/bin/env python3
"""Evaluate a pinned Whisper checkpoint on the speaker-safe Garhwali test set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/splits/asr/test.jsonl'
TINY_REVISION = '169d4a4341b33bc18d8881c4b69c2e104e1cc0af'
TINY_MODEL = ROOT / '.cache/huggingface/hub/models--openai--whisper-tiny/snapshots' / TINY_REVISION
OUTPUT = ROOT / 'data/processed/evaluation/asr/whisper_tiny_zero_shot'


def select_rows(rows, limit):
    selected = sorted(rows, key=lambda row: row['audio_sha256'])
    return selected[:limit] if limit else selected


def summarize_scores(scores):
    totals = {
        key: sum(row[key] for row in scores)
        for key in ('word_errors', 'reference_words', 'character_errors', 'reference_characters')
    }
    totals['wer'] = totals['word_errors'] / max(1, totals['reference_words'])
    totals['cer'] = totals['character_errors'] / max(1, totals['reference_characters'])
    return totals


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    model_path=TINY_MODEL,
    model_id='openai/whisper-tiny',
    revision=TINY_REVISION,
    input_path=INPUT,
    output_dir=OUTPUT,
    max_records=0,
    max_new_tokens=128,
    language_prompt='hi',
    device='auto',
):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from asr_metrics import score
    from run_asr_baseline import read_audio

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    input_path = Path(input_path)
    with input_path.open(encoding='utf-8') as handle:
        rows = select_rows([json.loads(line) for line in handle if line.strip()], max_records)
    processor = WhisperProcessor.from_pretrained(model_path, local_files_only=True)
    model = WhisperForConditionalGeneration.from_pretrained(
        model_path,
        local_files_only=True,
    ).to(device)
    model.eval()
    predictions = []
    scores = []
    start = time.monotonic()
    with torch.no_grad():
        for index, row in enumerate(rows, 1):
            audio = read_audio(ROOT / row['local_audio_path'])
            features = processor(
                audio,
                sampling_rate=16000,
                return_tensors='pt',
            ).input_features.to(device)
            generated = model.generate(
                features,
                language=language_prompt,
                task='transcribe',
                max_length=max_new_tokens,
                do_sample=False,
            )
            hypothesis = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
            metrics = score(row['asr_target_clean'], hypothesis)
            scores.append(metrics)
            predictions.append({
                'audio_sha256': row['audio_sha256'],
                'reference': row['asr_target_clean'],
                'hypothesis': hypothesis,
                **metrics,
            })
            if index == 1 or index % 10 == 0 or index == len(rows):
                current = summarize_scores(scores)
                print(f'{index}/{len(rows)} WER={current["wer"]:.4f} CER={current["cer"]:.4f}', flush=True)
    report = {
        'run_id': f'{model_id.replace("/", "--")}-garhwali-speaker-safe-v0.1',
        'model_id': model_id,
        'revision': revision,
        'language_prompt': language_prompt,
        'evaluation_manifest': str(input_path.relative_to(ROOT)),
        'evaluation_manifest_sha256': sha256_file(input_path),
        'evaluation_records': len(rows),
        'device': device,
        'max_target_tokens': max_new_tokens,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        **summarize_scores(scores),
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                for row in predictions),
        encoding='utf-8',
    )
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=Path, default=TINY_MODEL)
    parser.add_argument('--model-id', default='openai/whisper-tiny')
    parser.add_argument('--revision', default=TINY_REVISION)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--max-records', type=int, default=0)
    parser.add_argument('--max-new-tokens', type=int, default=128)
    parser.add_argument('--language-prompt', default='hi')
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        model_path=args.model,
        model_id=args.model_id,
        revision=args.revision,
        input_path=args.input,
        output_dir=args.output,
        max_records=args.max_records,
        max_new_tokens=args.max_new_tokens,
        language_prompt=args.language_prompt,
        device=args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
