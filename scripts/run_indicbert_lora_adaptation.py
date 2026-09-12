#!/usr/bin/env python3
"""Run a validation-only, multi-seed IndicBERTv2 encoder-LoRA pilot."""

from __future__ import annotations

import argparse
import gc
import json
import os
import statistics
import time
from pathlib import Path

import run_indicbert_adaptation as head


ROOT = Path(__file__).resolve().parents[1]
TRAIN = head.TRAIN
VALIDATION = head.VALIDATION
OUTPUT = ROOT / 'data/processed/evaluation/controlled_modeling/indicbert_lora_adaptation.json'
CHECKPOINTS = ROOT / 'models/controlled_modeling/indicbert_lora_v0.1'
LORA_TARGET_MODULES = ('query', 'value')
DEFAULT_SEEDS = (17, 29, 43)


def summarize_lora(baseline, runs):
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
            'advance_to_longer_continued_pretraining'
            if mean_loss < baseline['cross_entropy'] else 'not_advanced'
        ),
    }


def core_model(model):
    candidate = getattr(getattr(model, 'base_model', None), 'model', None)
    return candidate if candidate is not None and hasattr(candidate, 'bert') else model


def score_model(model, tokenizer, rows, max_length, mask_rate, mask_seed, device):
    import torch
    import torch.nn.functional as functional

    model.eval()
    core = core_model(model)
    special_ids = set(tokenizer.all_special_ids)
    loss_sum = 0.0
    correct = 0
    masked_tokens = 0
    with torch.no_grad():
        for row in rows:
            item = head.encode_masked(
                tokenizer, row, special_ids, max_length, mask_rate, mask_seed, device,
            )
            if item is None:
                continue
            inputs, positions, labels = item
            hidden = core.bert(**inputs).last_hidden_state[0, positions]
            logits = core.cls(hidden)
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


def train_seed(model, tokenizer, rows, seed, steps, learning_rate, max_length,
               mask_rate, device):
    import torch
    import torch.nn.functional as functional

    torch.manual_seed(seed)
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=learning_rate, weight_decay=0.01)
    special_ids = set(tokenizer.all_special_ids)
    core = core_model(model)
    losses = []
    masked_tokens = 0
    model.train()
    for step in range(steps):
        row = rows[step % len(rows)]
        item = head.encode_masked(
            tokenizer, row, special_ids, max_length, mask_rate, seed, device,
        )
        if item is None:
            continue
        inputs, positions, labels = item
        hidden = core.bert(**inputs).last_hidden_state[0, positions]
        logits = core.cls(hidden)
        loss = functional.cross_entropy(logits, labels)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, 1.0)
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
        masked_tokens += len(positions)
    return {
        'steps': steps,
        'unique_training_records': min(len(rows), steps),
        'masked_tokens': masked_tokens,
        'mean_training_loss': round(statistics.mean(losses), 8) if losses else None,
        'final_training_loss': round(losses[-1], 8) if losses else None,
    }


def run(train_path=TRAIN, validation_path=VALIDATION, output_path=OUTPUT,
        checkpoint_dir=CHECKPOINTS, seeds=DEFAULT_SEEDS, steps=32,
        training_records=256, evaluation_records=128, learning_rate=1e-4,
        max_length=128, mask_rate=0.15, rank=4, alpha=8, device='auto'):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    train_rows = head.read_jsonl(train_path)
    validation_rows = head.select_rows(
        head.read_jsonl(validation_path), evaluation_records, 101,
    )
    tokenizer = AutoTokenizer.from_pretrained(
        head.MODEL, local_files_only=True, fix_mistral_regex=True,
    )
    base = AutoModelForMaskedLM.from_pretrained(
        head.MODEL, local_files_only=True,
    ).to(device)
    baseline = score_model(
        base, tokenizer, validation_rows, max_length, mask_rate, 101, device,
    )
    total_parameters = sum(parameter.numel() for parameter in base.parameters())
    del base
    gc.collect()

    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    trainable_parameters = None
    started = time.monotonic()
    for seed in seeds:
        torch.manual_seed(seed)
        base = AutoModelForMaskedLM.from_pretrained(
            head.MODEL, local_files_only=True,
        )
        config = LoraConfig(
            r=rank,
            lora_alpha=alpha,
            lora_dropout=0.0,
            bias='none',
            target_modules=list(LORA_TARGET_MODULES),
        )
        model = get_peft_model(base, config).to(device)
        current_trainable = sum(
            parameter.numel() for parameter in model.parameters() if parameter.requires_grad
        )
        trainable_parameters = trainable_parameters or current_trainable
        pool = head.select_rows(train_rows, training_records, seed)
        print(f'training LoRA seed {seed} ({steps} steps)', flush=True)
        training = train_seed(
            model, tokenizer, pool, seed, steps, learning_rate,
            max_length, mask_rate, device,
        )
        validation = score_model(
            model, tokenizer, validation_rows, max_length, mask_rate, 101, device,
        )
        checkpoint = checkpoint_dir / f'seed-{seed}'
        model.save_pretrained(checkpoint, safe_serialization=True)
        runs.append({
            'seed': seed,
            'training': training,
            'validation': validation,
            'checkpoint': head.display_path(checkpoint),
        })
        print(
            f"seed {seed}: validation loss {validation['cross_entropy']:.6f} "
            f"(baseline {baseline['cross_entropy']:.6f})",
            flush=True,
        )
        del model, base
        gc.collect()

    report = {
        'run_id': 'indicbertv2-garhwali-encoder-lora-v0.1',
        'status': 'validation_only_encoder_adaptation_pilot',
        'model_id': head.MODEL_ID,
        'revision': head.REVISION,
        'adaptation_scope': 'LoRA on encoder attention query/value projections; MLM head frozen',
        'total_parameters': total_parameters,
        'trainable_parameters': trainable_parameters,
        'configuration': {
            'seeds': list(seeds),
            'steps_per_seed': steps,
            'training_pool_records_per_seed': min(training_records, len(train_rows)),
            'validation_records': len(validation_rows),
            'learning_rate': learning_rate,
            'max_length': max_length,
            'mask_rate': mask_rate,
            'evaluation_mask_seed': 101,
            'lora_rank': rank,
            'lora_alpha': alpha,
            'lora_dropout': 0.0,
            'target_modules': list(LORA_TARGET_MODULES),
            'device': device,
        },
        'baseline_validation': baseline,
        'runs': runs,
        'summary': summarize_lora(baseline, runs),
        'integrity': {
            'training_split_only': True,
            'selection_split': 'validation',
            'frozen_test_records_used': 0,
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', type=Path, default=TRAIN)
    parser.add_argument('--validation', type=Path, default=VALIDATION)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--checkpoint-dir', type=Path, default=CHECKPOINTS)
    parser.add_argument('--seeds', default=','.join(map(str, DEFAULT_SEEDS)))
    parser.add_argument('--steps', type=int, default=32)
    parser.add_argument('--training-records', type=int, default=256)
    parser.add_argument('--evaluation-records', type=int, default=128)
    parser.add_argument('--learning-rate', type=float, default=1e-4)
    parser.add_argument('--max-length', type=int, default=128)
    parser.add_argument('--mask-rate', type=float, default=0.15)
    parser.add_argument('--rank', type=int, default=4)
    parser.add_argument('--alpha', type=int, default=8)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        args.train, args.validation, args.output, args.checkpoint_dir,
        head.parse_ints(args.seeds), args.steps, args.training_records,
        args.evaluation_records, args.learning_rate, args.max_length,
        args.mask_rate, args.rank, args.alpha, args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
