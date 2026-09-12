#!/usr/bin/env python3
"""Evaluate pinned SraVaani 1.0 on the speaker-safe Garhwali test set."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'data/processed/model_ready/splits/asr/test.jsonl'
MODEL_ID = 'ARTPARK-IISc/SraVaani-1.0'
REVISION = 'f5dd5358325a5208775b91dad98918e079ea2b27'
MODEL = ROOT / '.cache/huggingface/hub/models--ARTPARK-IISc--SraVaani-1.0/snapshots' / REVISION
OUTPUT = ROOT / 'data/processed/evaluation/asr/sravaani_1_0'
REQUIRED_ARTIFACTS = (
    'config.json',
    'configuration_sravaani.py',
    'model-asr.fp16.ts',
    'modeling_sravaani.py',
    'preproc.pt',
    'tokenizer.model',
)


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


def validate_model_dir(model_dir):
    model_dir = Path(model_dir)
    missing = [name for name in REQUIRED_ARTIFACTS if not (model_dir / name).is_file()]
    if missing:
        raise FileNotFoundError(f'missing SraVaani artifact: {missing[0]}')
    return model_dir


def run(
    model_path=MODEL,
    input_path=INPUT,
    output_dir=OUTPUT,
    max_records=0,
    batch_size=4,
    device='auto',
):
    cache = ROOT / '.cache/huggingface'
    os.environ.setdefault('HF_HOME', str(cache))
    os.environ.setdefault('HF_MODULES_CACHE', str(cache / 'modules'))
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import AutoModel
    from asr_metrics import score

    model_path = validate_model_dir(model_path)
    if device == 'auto':
        if torch.cuda.is_available():
            device = 'cuda'
        elif torch.backends.mps.is_available():
            device = 'mps'
        else:
            device = 'cpu'
    input_path = Path(input_path)
    with input_path.open(encoding='utf-8') as handle:
        rows = select_rows([json.loads(line) for line in handle if line.strip()], max_records)

    model = AutoModel.from_pretrained(
        model_path,
        trust_remote_code=True,
        local_files_only=True,
    )
    if device in ('cuda', 'mps'):
        model = model.half()
    model = model.to(device).eval()

    predictions = []
    scores = []
    start = time.monotonic()
    with torch.no_grad():
        for offset in range(0, len(rows), batch_size):
            batch = rows[offset:offset + batch_size]
            paths = [str(ROOT / row['local_audio_path']) for row in batch]
            hypotheses = model.transcribe(paths, batch_size=batch_size)
            for row, hypothesis in zip(batch, hypotheses):
                metrics = score(row['asr_target_clean'], hypothesis)
                scores.append(metrics)
                predictions.append({
                    'audio_sha256': row['audio_sha256'],
                    'reference': row['asr_target_clean'],
                    'hypothesis': hypothesis,
                    **metrics,
                })
            completed = min(offset + len(batch), len(rows))
            current = summarize_scores(scores)
            print(f'{completed}/{len(rows)} WER={current["wer"]:.4f} CER={current["cer"]:.4f}', flush=True)

    report = {
        'run_id': 'ARTPARK-IISc--SraVaani-1.0-garhwali-speaker-safe-v0.1',
        'model_id': MODEL_ID,
        'revision': REVISION,
        'model_artifact_sha256': sha256_file(model_path / 'model-asr.fp16.ts'),
        'evaluation_manifest': str(input_path.relative_to(ROOT)),
        'evaluation_manifest_sha256': sha256_file(input_path),
        'evaluation_records': len(rows),
        'device': device,
        'batch_size': batch_size,
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
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--max-records', type=int, default=0)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--device', choices=('auto', 'mps', 'cuda', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        model_path=args.model,
        input_path=args.input,
        output_dir=args.output,
        max_records=args.max_records,
        batch_size=args.batch_size,
        device=args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
