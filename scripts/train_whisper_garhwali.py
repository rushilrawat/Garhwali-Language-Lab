#!/usr/bin/env python3
"""Fine-tune Whisper on the strict speaker-safe Garhwali ASR split."""

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPLITS = ROOT / 'data/processed/model_ready/splits/asr'
DEFAULT_OUTPUT = ROOT / 'models/whisper-tiny-garhwali-v0.1'


def load_rows(path, limit=0):
    with path.open(encoding='utf-8') as handle:
        rows = sorted(
            (json.loads(line) for line in handle if line.strip()),
            key=lambda row: row['audio_sha256'],
        )
    return rows[:limit] if limit else rows


def summarize_scores(scores):
    totals = {
        key: sum(row[key] for row in scores)
        for key in ('word_errors', 'reference_words', 'character_errors', 'reference_characters')
    }
    totals['wer'] = totals['word_errors'] / max(1, totals['reference_words'])
    totals['cer'] = totals['character_errors'] / max(1, totals['reference_characters'])
    return totals


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='openai/whisper-tiny')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--epochs', type=int, default=1)
    parser.add_argument('--learning-rate', type=float, default=1e-5)
    parser.add_argument('--max-train', type=int, default=0)
    parser.add_argument('--max-eval', type=int, default=112)
    parser.add_argument('--save-every', type=int, default=100)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    parser.add_argument('--local-files-only', action='store_true')
    args = parser.parse_args()

    os.environ.setdefault('HF_HOME', str(ROOT / '.cache/huggingface'))
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    from asr_metrics import score
    from run_asr_baseline import read_audio

    if args.device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    else:
        device = args.device
    train_rows = load_rows(SPLITS / 'train.jsonl', args.max_train)
    eval_rows = load_rows(SPLITS / 'test.jsonl', args.max_eval)
    args.output.mkdir(parents=True, exist_ok=True)

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
    model.config.use_cache = False
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)

    losses = []
    step = 0
    model.train()
    for epoch in range(args.epochs):
        for row in train_rows:
            audio = read_audio(ROOT / row['local_audio_path'])
            features = processor(audio, sampling_rate=16000, return_tensors='pt').input_features.to(device)
            labels = processor.tokenizer(row['asr_target_clean'], return_tensors='pt').input_ids.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = model(input_features=features, labels=labels).loss
            loss.backward()
            optimizer.step()
            step += 1
            losses.append(float(loss.detach().cpu()))
            state = {'epoch': epoch + 1, 'step': step, 'last_audio_sha256': row['audio_sha256'], 'device': device}
            (args.output / 'trainer_state.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
            if step == 1 or step % 25 == 0:
                print(f"step={step}/{len(train_rows) * args.epochs} loss={losses[-1]:.4f}", flush=True)
            if args.save_every and step % args.save_every == 0:
                model.save_pretrained(args.output)
                processor.save_pretrained(args.output)

    model.save_pretrained(args.output)
    processor.save_pretrained(args.output)
    model.eval()
    predictions = []
    scores = []
    with torch.no_grad():
        for row in eval_rows:
            audio = read_audio(ROOT / row['local_audio_path'])
            features = processor(audio, sampling_rate=16000, return_tensors='pt').input_features.to(device)
            generated = model.generate(features, language='hi', task='transcribe', max_new_tokens=128)
            prediction = processor.batch_decode(generated, skip_special_tokens=True)[0].strip()
            metrics = score(row['asr_target_clean'], prediction)
            scores.append(metrics)
            predictions.append({
                'audio_sha256': row['audio_sha256'],
                'reference': row['asr_target_clean'],
                'prediction': prediction,
                **metrics,
            })
    evaluation = summarize_scores(scores)
    (args.output / 'evaluation_predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in predictions), encoding='utf-8'
    )
    report = {
        'base_model': args.model,
        'device': device,
        'epochs': args.epochs,
        'train_records': len(train_rows),
        'training_steps': step,
        'mean_training_loss': sum(losses) / max(1, len(losses)),
        'evaluation_records': len(eval_rows),
        **evaluation,
    }
    (args.output / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
