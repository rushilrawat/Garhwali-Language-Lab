#!/usr/bin/env python3
"""Run a multi-seed, validation-only IndicBERTv2 MLM-head adaptation pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRAIN = ROOT / 'data/processed/model_ready/splits/text/train.jsonl'
VALIDATION = ROOT / 'data/processed/model_ready/splits/text/validation.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/controlled_modeling/indicbert_head_adaptation.json'
CHECKPOINTS = ROOT / 'models/controlled_modeling/indicbert_head_v0.1'
MODEL_ID = 'ai4bharat/IndicBERTv2-MLM-only'
REVISION = '8598f13fe52443bc3fc054fcd665944560145b5c'
MODEL = ROOT / '.cache/huggingface/hub/models--ai4bharat--IndicBERTv2-MLM-only/snapshots' / REVISION
DEFAULT_SEEDS = (17, 29, 43)


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def row_key(row):
    return str(row.get('segment_sha256') or row.get('text_sha256') or row.get('text') or '')


def select_rows(rows, count, seed):
    return sorted(
        rows,
        key=lambda row: hashlib.sha256(f'{seed}:{row_key(row)}'.encode()).digest(),
    )[:min(count, len(rows))]


def select_mask_positions(token_ids, attention_mask, special_ids, record_key, rate, seed):
    candidates = [
        index for index, (token_id, attended) in enumerate(zip(token_ids, attention_mask))
        if attended and token_id not in special_ids
    ]
    if not candidates:
        return []
    ranked = []
    for index in candidates:
        digest = hashlib.sha256(f'{seed}:{record_key}:{index}'.encode()).digest()
        ranked.append((int.from_bytes(digest[:8], 'big') / 2**64, index))
    selected = [index for score, index in ranked if score < rate]
    return sorted(selected or [min(ranked)[1]])


def summarize_runs(baseline, runs):
    losses = [run['validation']['cross_entropy'] for run in runs]
    accuracies = [run['validation']['accuracy'] for run in runs]
    mean_loss = statistics.mean(losses)
    mean_accuracy = statistics.mean(accuracies)
    return {
        'mean_cross_entropy': round(mean_loss, 8),
        'std_cross_entropy': round(statistics.pstdev(losses), 8),
        'mean_accuracy': round(mean_accuracy, 8),
        'std_accuracy': round(statistics.pstdev(accuracies), 8),
        'mean_cross_entropy_delta': round(mean_loss - baseline['cross_entropy'], 8),
        'mean_accuracy_delta': round(mean_accuracy - baseline['accuracy'], 8),
        'improved_seed_count': sum(
            run['validation']['cross_entropy'] < baseline['cross_entropy'] for run in runs
        ),
        'promotion_status': (
            'advance_to_encoder_adaptation'
            if mean_loss < baseline['cross_entropy'] else 'not_advanced'
        ),
    }


def configure_head_only(model):
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.cls.predictions.transform.parameters():
        parameter.requires_grad = True
    model.cls.predictions.bias.requires_grad = True
    return [
        (name, parameter) for name, parameter in model.named_parameters()
        if parameter.requires_grad
    ]


def encode_masked(tokenizer, row, special_ids, max_length, mask_rate, seed, device):
    text = row.get('text', '')
    encoded = tokenizer(
        text, add_special_tokens=True, max_length=max_length,
        truncation=True, return_tensors='pt',
    )
    positions = select_mask_positions(
        encoded['input_ids'][0].tolist(), encoded['attention_mask'][0].tolist(),
        special_ids, row_key(row), mask_rate, seed,
    )
    if not positions:
        return None
    labels = encoded['input_ids'][0, positions].to(device)
    encoded['input_ids'][0, positions] = tokenizer.mask_token_id
    inputs = {name: value.to(device) for name, value in encoded.items()}
    return inputs, positions, labels


def score_rows(model, tokenizer, rows, max_length, mask_rate, mask_seed, device):
    import torch
    import torch.nn.functional as functional

    model.eval()
    special_ids = set(tokenizer.all_special_ids)
    loss_sum = 0.0
    correct = 0
    masked_tokens = 0
    with torch.no_grad():
        for row in rows:
            item = encode_masked(
                tokenizer, row, special_ids, max_length, mask_rate, mask_seed, device,
            )
            if item is None:
                continue
            inputs, positions, labels = item
            hidden = model.bert(**inputs).last_hidden_state[0, positions]
            logits = model.cls(hidden)
            loss_sum += float(functional.cross_entropy(
                logits, labels, reduction='sum',
            ).cpu())
            correct += int((logits.argmax(dim=-1) == labels).sum().cpu())
            masked_tokens += len(positions)
    return {
        'records': len(rows),
        'masked_tokens': masked_tokens,
        'cross_entropy': round(loss_sum / max(1, masked_tokens), 8),
        'accuracy': round(correct / max(1, masked_tokens), 8),
    }


def train_seed(model, tokenizer, train_rows, seed, steps, learning_rate, max_length,
               mask_rate, device):
    import torch
    import torch.nn.functional as functional

    torch.manual_seed(seed)
    selected = select_rows(train_rows, max(steps, 1), seed)
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=learning_rate, weight_decay=0.01)
    special_ids = set(tokenizer.all_special_ids)
    losses = []
    masked_tokens = 0
    model.bert.eval()
    model.cls.train()
    for step in range(steps):
        row = selected[step % len(selected)]
        item = encode_masked(
            tokenizer, row, special_ids, max_length, mask_rate, seed, device,
        )
        if item is None:
            continue
        inputs, positions, labels = item
        with torch.no_grad():
            hidden = model.bert(**inputs).last_hidden_state[0, positions]
        logits = model.cls(hidden)
        loss = functional.cross_entropy(logits, labels)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        masked_tokens += len(positions)
    return {
        'steps': steps,
        'unique_training_records': len(selected),
        'masked_tokens': masked_tokens,
        'mean_training_loss': round(statistics.mean(losses), 8) if losses else None,
        'final_training_loss': round(losses[-1], 8) if losses else None,
    }


def display_path(path):
    try:
        return str(Path(path).relative_to(ROOT))
    except ValueError:
        return str(path)


def run(train_path=TRAIN, validation_path=VALIDATION, output_path=OUTPUT,
        checkpoint_dir=CHECKPOINTS, seeds=DEFAULT_SEEDS, steps=64,
        training_records=512, evaluation_records=128, learning_rate=5e-5,
        max_length=128, mask_rate=0.15, device='auto'):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    train_rows = read_jsonl(train_path)
    validation_rows = select_rows(read_jsonl(validation_path), evaluation_records, 101)
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL, local_files_only=True, fix_mistral_regex=True,
    )
    model = AutoModelForMaskedLM.from_pretrained(MODEL, local_files_only=True).to(device)
    trainable = configure_head_only(model)
    initial = {name: parameter.detach().cpu().clone() for name, parameter in trainable}
    evaluation_seed = 101
    baseline = score_rows(
        model, tokenizer, validation_rows, max_length, mask_rate, evaluation_seed, device,
    )
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    started = time.monotonic()
    for seed in seeds:
        with torch.no_grad():
            for name, parameter in trainable:
                parameter.copy_(initial[name].to(device))
        print(f'training seed {seed} ({steps} steps)', flush=True)
        training = train_seed(
            model, tokenizer, select_rows(train_rows, training_records, seed), seed,
            steps, learning_rate, max_length, mask_rate, device,
        )
        validation = score_rows(
            model, tokenizer, validation_rows, max_length, mask_rate,
            evaluation_seed, device,
        )
        checkpoint = checkpoint_dir / f'seed-{seed}.pt'
        torch.save({
            'model_id': MODEL_ID,
            'revision': REVISION,
            'seed': seed,
            'trainable_state': {
                name: parameter.detach().cpu() for name, parameter in trainable
            },
        }, checkpoint)
        runs.append({
            'seed': seed,
            'training': training,
            'validation': validation,
            'checkpoint': display_path(checkpoint),
        })
        print(
            f"seed {seed}: validation loss {validation['cross_entropy']:.6f} "
            f"(baseline {baseline['cross_entropy']:.6f})",
            flush=True,
        )
    summary = summarize_runs(baseline, runs)
    report = {
        'run_id': 'indicbertv2-garhwali-mlm-head-adaptation-v0.1',
        'status': 'validation_only_transfer_pilot',
        'model_id': MODEL_ID,
        'revision': REVISION,
        'adaptation_scope': 'MLM prediction transform and output bias; encoder frozen',
        'trainable_parameters': sum(parameter.numel() for _, parameter in trainable),
        'total_parameters': sum(parameter.numel() for parameter in model.parameters()),
        'configuration': {
            'seeds': list(seeds),
            'steps_per_seed': steps,
            'training_pool_records_per_seed': min(training_records, len(train_rows)),
            'validation_records': len(validation_rows),
            'learning_rate': learning_rate,
            'max_length': max_length,
            'mask_rate': mask_rate,
            'evaluation_mask_seed': evaluation_seed,
            'device': device,
        },
        'baseline_validation': baseline,
        'runs': runs,
        'summary': summary,
        'integrity': {
            'training_split_only': True,
            'selection_split': 'validation',
            'frozen_test_records_used': 0,
            'encoder_frozen': True,
            'source_text_mutated': False,
        },
        'elapsed_seconds': round(time.monotonic() - started, 3),
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def parse_ints(value):
    return tuple(int(item.strip()) for item in value.split(',') if item.strip())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=Path, default=TRAIN)
    parser.add_argument('--validation', type=Path, default=VALIDATION)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--checkpoint-dir', type=Path, default=CHECKPOINTS)
    parser.add_argument('--seeds', default=','.join(map(str, DEFAULT_SEEDS)))
    parser.add_argument('--steps', type=int, default=64)
    parser.add_argument('--training-records', type=int, default=512)
    parser.add_argument('--evaluation-records', type=int, default=128)
    parser.add_argument('--learning-rate', type=float, default=5e-5)
    parser.add_argument('--max-length', type=int, default=128)
    parser.add_argument('--mask-rate', type=float, default=0.15)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    report = run(
        args.train, args.validation, args.output, args.checkpoint_dir,
        parse_ints(args.seeds), args.steps, args.training_records,
        args.evaluation_records, args.learning_rate, args.max_length,
        args.mask_rate, args.device,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
