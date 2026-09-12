#!/usr/bin/env python3
"""Compare selected IndicBERTv2 transfer families on one frozen test subset."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import statistics
import time
import unicodedata
from pathlib import Path

import run_indicbert_adaptation as head
import run_indicbert_lora_adaptation as lora


ROOT = Path(__file__).resolve().parents[1]
TRAIN = head.TRAIN
TEST = ROOT / 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl'
HEAD_CHECKPOINTS = head.CHECKPOINTS
LORA_CHECKPOINTS = lora.CHECKPOINTS
OUTPUT = ROOT / 'data/processed/evaluation/controlled_modeling/indicbert_transfer_test.json'
SEEDS = (17, 29, 43)


def summarize_family(runs):
    losses = [run['cross_entropy'] for run in runs]
    accuracies = [run['accuracy'] for run in runs]
    return {
        'runs': len(runs),
        'mean_cross_entropy': round(statistics.mean(losses), 8),
        'std_cross_entropy': round(statistics.pstdev(losses), 8),
        'mean_accuracy': round(statistics.mean(accuracies), 8),
        'std_accuracy': round(statistics.pstdev(accuracies), 8),
    }


def select_family(families):
    return min(families, key=lambda name: families[name]['mean_cross_entropy'])


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def exact_overlap(train_rows, test_rows):
    training = {normalize(row.get('text', '')) for row in train_rows}
    return sum(normalize(row.get('text', '')) in training for row in test_rows)


def subset_sha256(rows):
    digest = hashlib.sha256()
    for row in rows:
        digest.update(head.row_key(row).encode())
        digest.update(b'\n')
    return digest.hexdigest()


def run(train_path=TRAIN, test_path=TEST, head_dir=HEAD_CHECKPOINTS,
        lora_dir=LORA_CHECKPOINTS, output_path=OUTPUT, test_records=256,
        max_length=128, mask_rate=0.15, subset_seed=211, device='auto'):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from peft import PeftModel
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    train_rows = head.read_jsonl(train_path)
    all_test_rows = head.read_jsonl(test_path)
    test_rows = head.select_rows(all_test_rows, test_records, subset_seed)
    tokenizer = AutoTokenizer.from_pretrained(
        head.MODEL, local_files_only=True, fix_mistral_regex=True,
    )
    started = time.monotonic()

    base = AutoModelForMaskedLM.from_pretrained(
        head.MODEL, local_files_only=True,
    ).to(device)
    base_score = lora.score_model(
        base, tokenizer, test_rows, max_length, mask_rate, subset_seed, device,
    )
    base_score['seed'] = None
    trainable = head.configure_head_only(base)
    initial = {name: parameter.detach().cpu().clone() for name, parameter in trainable}
    named_parameters = dict(base.named_parameters())
    head_runs = []
    for seed in SEEDS:
        checkpoint = Path(head_dir) / f'seed-{seed}.pt'
        payload = torch.load(checkpoint, map_location='cpu', weights_only=True)
        with torch.no_grad():
            for name, value in payload['trainable_state'].items():
                named_parameters[name].copy_(value.to(device))
        score = lora.score_model(
            base, tokenizer, test_rows, max_length, mask_rate, subset_seed, device,
        )
        score.update(seed=seed, checkpoint=head.display_path(checkpoint))
        head_runs.append(score)
        with torch.no_grad():
            for name, parameter in trainable:
                parameter.copy_(initial[name].to(device))
        print(f"head seed {seed}: test loss {score['cross_entropy']:.6f}", flush=True)
    del base
    gc.collect()

    lora_runs = []
    for seed in SEEDS:
        checkpoint = Path(lora_dir) / f'seed-{seed}'
        base = AutoModelForMaskedLM.from_pretrained(
            head.MODEL, local_files_only=True,
        )
        model = PeftModel.from_pretrained(base, checkpoint).to(device)
        score = lora.score_model(
            model, tokenizer, test_rows, max_length, mask_rate, subset_seed, device,
        )
        score.update(seed=seed, checkpoint=head.display_path(checkpoint))
        lora_runs.append(score)
        print(f"LoRA seed {seed}: test loss {score['cross_entropy']:.6f}", flush=True)
        del model, base
        gc.collect()

    families = {
        'base': summarize_family([base_score]),
        'head_only_64_steps': summarize_family(head_runs),
        'encoder_lora_256_steps': summarize_family(lora_runs),
    }
    for summary in families.values():
        summary['cross_entropy_delta_vs_base'] = round(
            summary['mean_cross_entropy'] - base_score['cross_entropy'], 8,
        )
        summary['accuracy_delta_vs_base'] = round(
            summary['mean_accuracy'] - base_score['accuracy'], 8,
        )
    selected = select_family(families)
    report = {
        'run_id': 'indicbertv2-garhwali-transfer-frozen-test-v0.1',
        'status': 'frozen_test_evaluation_complete',
        'model_id': head.MODEL_ID,
        'revision': head.REVISION,
        'test_subset': {
            'source_records': len(all_test_rows),
            'evaluated_records': len(test_rows),
            'selection_seed': subset_seed,
            'sha256': subset_sha256(test_rows),
            'masked_tokens': base_score['masked_tokens'],
        },
        'families': families,
        'runs': {
            'base': [base_score],
            'head_only_64_steps': head_runs,
            'encoder_lora_256_steps': lora_runs,
        },
        'selection': {
            'family': selected,
            'metric': 'mean_frozen_test_cross_entropy',
            'future_test_tuning_allowed': False,
        },
        'integrity': {
            'train_test_exact_text_overlap': exact_overlap(train_rows, test_rows),
            'validation_selected_hyperparameters': True,
            'test_used_for_further_tuning': False,
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
    parser.add_argument('--test', type=Path, default=TEST)
    parser.add_argument('--head-dir', type=Path, default=HEAD_CHECKPOINTS)
    parser.add_argument('--lora-dir', type=Path, default=LORA_CHECKPOINTS)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--test-records', type=int, default=256)
    parser.add_argument('--max-length', type=int, default=128)
    parser.add_argument('--mask-rate', type=float, default=0.15)
    parser.add_argument('--subset-seed', type=int, default=211)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        args.train, args.test, args.head_dir, args.lora_dir, args.output,
        args.test_records, args.max_length, args.mask_rate, args.subset_seed,
        args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
