#!/usr/bin/env python3
"""Evaluate a pinned Whisper checkpoint on a local Garhwali ASR manifest."""

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


def resolve_input_path(path):
    path = Path(path)
    return path if path.is_absolute() else ROOT / path


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


def make_prediction_row(row, hypothesis, metrics):
    """Keep stable manifest identity beside every ASR result."""
    prediction = {
        'audio_sha256': row['audio_sha256'],
        'reference': row['asr_target_clean'],
        'hypothesis': hypothesis,
        **metrics,
    }
    for field in (
        'record_id', 'source_split', 'split', 'text_sha256', 'source_file',
        'source_file_sha256', 'source', 'source_url', 'source_revision',
        'source_license', 'source_license_url', 'duplicate_audio_count',
        'duplicate_text_count', 'cross_split_audio_overlap',
        'cross_corpus_audio_overlap', 'cross_split_text_overlap',
        'cross_corpus_text_overlap', 'cross_corpus_train_text_overlap',
        'cross_corpus_evaluation_text_overlap', 'transcript_conflict_for_audio',
        'split_safe_for_training', 'split_safe_for_evaluation',
    ):
        if row.get(field) is not None:
            prediction[field] = row[field]
    return prediction


def generation_kwargs(max_new_tokens=128, language_prompt='hi', num_beams=1):
    if max_new_tokens < 1 or num_beams < 1:
        raise ValueError('max_new_tokens and num_beams must be positive integers')
    return {
        'language': language_prompt,
        'task': 'transcribe',
        'max_length': max_new_tokens,
        'do_sample': False,
        'num_beams': num_beams,
    }


def resolve_run_id(model_id, run_id=None):
    return run_id or f'{model_id.replace("/", "--")}-garhwali-speaker-safe-v0.1'


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def model_weight_sha256(model_path):
    """Fingerprint local model weight files without hashing training metadata."""
    model_path = Path(model_path)
    if model_path.is_file():
        return sha256_file(model_path)
    if not model_path.is_dir():
        return None
    weights = sorted(
        path for pattern in ('*.safetensors', 'pytorch_model*.bin')
        for path in model_path.glob(pattern)
        if path.is_file()
    )
    if not weights:
        return None
    if len(weights) == 1:
        return sha256_file(weights[0])
    digest = hashlib.sha256()
    for path in weights:
        digest.update(path.name.encode('utf-8'))
        digest.update(bytes.fromhex(sha256_file(path)))
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
    run_id=None,
    num_beams=1,
):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from asr_metrics import score, summarize_slices
    from run_asr_baseline import read_audio

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    input_path = resolve_input_path(input_path)
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
                **generation_kwargs(max_new_tokens, language_prompt, num_beams),
            )
            hypothesis = processor.batch_decode(
                generated,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0].strip()
            metrics = score(row['asr_target_clean'], hypothesis)
            scores.append(metrics)
            predictions.append(make_prediction_row(row, hypothesis, metrics))
            if index == 1 or index % 10 == 0 or index == len(rows):
                current = summarize_scores(scores)
                print(f'{index}/{len(rows)} WER={current["wer"]:.4f} CER={current["cer"]:.4f}', flush=True)
    report = {
        'run_id': resolve_run_id(model_id, run_id),
        'model_id': model_id,
        'revision': revision,
        'model_weight_sha256': model_weight_sha256(model_path),
        'language_prompt': language_prompt,
        'evaluation_manifest': str(input_path.relative_to(ROOT)),
        'evaluation_manifest_sha256': sha256_file(input_path),
        'evaluation_records': len(rows),
        'device': device,
        'max_target_tokens': max_new_tokens,
        'num_beams': num_beams,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'error_slices': summarize_slices(rows, scores),
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
    parser.add_argument('--num-beams', type=int, default=1)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--run-id')
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
        run_id=args.run_id,
        num_beams=args.num_beams,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
