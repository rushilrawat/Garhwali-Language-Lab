#!/usr/bin/env python3
"""Run split-safe, multi-seed mT5 LoRA instruction tuning for Garhwali."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import random
import re
import statistics
import time
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/processed/model_ready/instructions'
OUTPUT = ROOT / 'data/processed/evaluation/controlled_modeling/mt5_instruction'
CHECKPOINTS = ROOT / 'models/controlled_modeling/mt5_instruction_v0.1'
MODEL_ID = 'google/mt5-small'
REVISION = '73fb5dbe4756edadc8fbe8c769b0a109493acf7a'
MODEL = (
    ROOT / '.cache/huggingface/hub/models--google--mt5-small'
    / 'snapshots' / REVISION
)
DEFAULT_SEEDS = (17, 29, 43)
TARGET_MODULES = ('q', 'v')


def read_jsonl(path):
    with Path(path).open(encoding='utf-8') as source:
        return [json.loads(line) for line in source if line.strip()]


def write_jsonl(path, rows):
    Path(path).write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in rows),
        encoding='utf-8',
    )


def select_rows(rows, limit, seed):
    """Select deterministically while cycling across instruction tasks."""
    if limit <= 0 or limit > len(rows):
        limit = len(rows)
    grouped = defaultdict(list)
    for row in rows:
        grouped[row.get('task', 'unknown')].append(row)
    rng = random.Random(seed)
    for task_rows in grouped.values():
        task_rows.sort(key=lambda row: row.get('instruction_sha256', ''))
        rng.shuffle(task_rows)
    tasks = sorted(grouped)
    rng.shuffle(tasks)
    selected = []
    while len(selected) < limit:
        added = False
        for task in tasks:
            if grouped[task]:
                selected.append(grouped[task].pop())
                added = True
                if len(selected) == limit:
                    break
        if not added:
            break
    rng.shuffle(selected)
    return selected


def mask_padding_labels(labels, pad_token_id):
    return [
        [-100 if token == pad_token_id else token for token in row]
        for row in labels
    ]


def normalize(text):
    value = unicodedata.normalize('NFC', str(text)).casefold()
    return re.sub(r'\s+', ' ', value).strip()


def clean_generated_text(text):
    value = re.sub(r'<extra_id_\d+>', ' ', str(text))
    return re.sub(r'\s+', ' ', value).strip()


def character_ngrams(text, size):
    value = ''.join(normalize(text).split())
    return Counter(value[index:index + size] for index in range(len(value) - size + 1))


def corpus_chrf(references, hypotheses, max_order=6, beta=2.0):
    scores = []
    for order in range(1, max_order + 1):
        matches = reference_total = hypothesis_total = 0
        for reference, hypothesis in zip(references, hypotheses):
            reference_counts = character_ngrams(reference, order)
            hypothesis_counts = character_ngrams(hypothesis, order)
            matches += sum(
                min(count, reference_counts[gram])
                for gram, count in hypothesis_counts.items()
            )
            reference_total += sum(reference_counts.values())
            hypothesis_total += sum(hypothesis_counts.values())
        if reference_total == 0 and hypothesis_total == 0:
            continue
        precision = matches / max(1, hypothesis_total)
        recall = matches / max(1, reference_total)
        denominator = beta**2 * precision + recall
        scores.append(
            (1 + beta**2) * precision * recall / denominator if denominator else 0.0
        )
    return round(statistics.mean(scores), 8) if scores else 0.0


def metric_summary(references, hypotheses):
    return {
        'exact_match': round(sum(
            normalize(reference) == normalize(hypothesis)
            for reference, hypothesis in zip(references, hypotheses)
        ) / max(1, len(references)), 8),
        'corpus_chrf2': corpus_chrf(references, hypotheses),
    }


def summarize_runs(baseline, runs):
    losses = [run['validation']['cross_entropy'] for run in runs]
    best = min(runs, key=lambda run: (run['validation']['cross_entropy'], run['seed']))
    return {
        'mean_cross_entropy': round(statistics.mean(losses), 8),
        'std_cross_entropy': round(statistics.pstdev(losses), 8),
        'mean_cross_entropy_delta': round(
            statistics.mean(losses) - baseline['cross_entropy'], 8,
        ),
        'improved_seed_count': sum(
            run['validation']['cross_entropy'] < baseline['cross_entropy'] for run in runs
        ),
        'best_seed': best['seed'],
        'best_validation_cross_entropy': best['validation']['cross_entropy'],
    }


def resolve_device(requested):
    import torch

    if requested != 'auto':
        return requested
    return 'mps' if torch.backends.mps.is_available() else 'cpu'


def load_tokenizer():
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(
        MODEL, local_files_only=True, fix_mistral_regex=True,
    )


def load_base_model(device):
    from transformers import AutoModelForSeq2SeqLM

    return AutoModelForSeq2SeqLM.from_pretrained(
        MODEL, local_files_only=True,
    ).to(device)


def encoded_batch(tokenizer, rows, max_input_length, max_target_length, device):
    import torch

    inputs = tokenizer(
        [row['instruction'] for row in rows],
        max_length=max_input_length,
        truncation=True,
        padding=True,
        return_tensors='pt',
    )
    targets = tokenizer(
        text_target=[row['response'] for row in rows],
        max_length=max_target_length,
        truncation=True,
        padding=True,
        return_tensors='pt',
    )
    labels = targets['input_ids']
    labels = labels.masked_fill(labels == tokenizer.pad_token_id, -100)
    return ({key: value.to(device) for key, value in inputs.items()}, labels.to(device))


def score_model(model, tokenizer, rows, max_input_length, max_target_length,
                batch_size, device):
    import torch

    model.eval()
    loss_sum = 0.0
    target_tokens = 0
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            inputs, labels = encoded_batch(
                tokenizer, batch, max_input_length, max_target_length, device,
            )
            output = model(**inputs, labels=labels)
            tokens = int((labels != -100).sum().cpu())
            loss_sum += float(output.loss.detach().cpu()) * tokens
            target_tokens += tokens
    return {
        'records': len(rows),
        'target_tokens': target_tokens,
        'cross_entropy': round(loss_sum / max(1, target_tokens), 8),
    }


def train_seed(model, tokenizer, rows, seed, steps, learning_rate,
               max_input_length, max_target_length, batch_size, device):
    import torch

    torch.manual_seed(seed)
    random.seed(seed)
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = torch.optim.AdamW(parameters, lr=learning_rate, weight_decay=0.01)
    losses = []
    target_tokens = 0
    model.train()
    for step in range(steps):
        offset = (step * batch_size) % len(rows)
        batch = [rows[(offset + index) % len(rows)] for index in range(batch_size)]
        inputs, labels = encoded_batch(
            tokenizer, batch, max_input_length, max_target_length, device,
        )
        output = model(**inputs, labels=labels)
        optimizer.zero_grad(set_to_none=True)
        output.loss.backward()
        torch.nn.utils.clip_grad_norm_(parameters, 1.0)
        optimizer.step()
        losses.append(float(output.loss.detach().cpu()))
        target_tokens += int((labels != -100).sum().cpu())
        if (step + 1) % max(1, min(32, steps)) == 0:
            print(
                f'  step {step + 1}/{steps}: loss {losses[-1]:.6f}',
                flush=True,
            )
    return {
        'steps': steps,
        'examples_seen': steps * batch_size,
        'unique_training_records': min(len(rows), steps * batch_size),
        'target_tokens': target_tokens,
        'mean_training_loss': round(statistics.mean(losses), 8),
        'final_training_loss': round(losses[-1], 8),
    }


def generate_predictions(model, tokenizer, rows, max_input_length,
                         max_new_tokens, batch_size, device):
    import torch

    model.eval()
    hypotheses = []
    with torch.no_grad():
        for start in range(0, len(rows), batch_size):
            batch = rows[start:start + batch_size]
            inputs = tokenizer(
                [row['instruction'] for row in batch],
                max_length=max_input_length,
                truncation=True,
                padding=True,
                return_tensors='pt',
            )
            inputs = {key: value.to(device) for key, value in inputs.items()}
            generated = model.generate(
                **inputs, max_new_tokens=max_new_tokens, num_beams=1, do_sample=False,
            )
            hypotheses.extend(
                clean_generated_text(text)
                for text in tokenizer.batch_decode(generated, skip_special_tokens=True)
            )
    references = [row['response'] for row in rows]
    return hypotheses, metric_summary(references, hypotheses)


def evaluate_test_model(model, tokenizer, rows, max_input_length,
                        max_target_length, max_new_tokens, batch_size, device):
    teacher_forced = score_model(
        model, tokenizer, rows, max_input_length, max_target_length,
        batch_size, device,
    )
    hypotheses, generation = generate_predictions(
        model, tokenizer, rows, max_input_length, max_new_tokens,
        batch_size, device,
    )
    return teacher_forced | generation, hypotheses


def dataset_digest(rows):
    payload = '\n'.join(row['instruction_sha256'] for row in rows).encode()
    return hashlib.sha256(payload).hexdigest()


def run(data_dir=DATA, output_dir=OUTPUT, checkpoint_dir=CHECKPOINTS,
        seeds=DEFAULT_SEEDS, steps=64, training_records=2304,
        validation_records=130, learning_rate=2e-4, batch_size=1,
        evaluation_batch_size=4, max_input_length=96, max_target_length=72,
        max_new_tokens=32, rank=4, alpha=8, device='auto'):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from peft import LoraConfig, PeftModel, TaskType, get_peft_model

    device = resolve_device(device)
    train_rows = read_jsonl(Path(data_dir) / 'train.jsonl')
    validation_all = read_jsonl(Path(data_dir) / 'validation.jsonl')
    test_rows = read_jsonl(Path(data_dir) / 'test.jsonl')
    validation_rows = select_rows(validation_all, validation_records, 101)
    tokenizer = load_tokenizer()
    started = time.monotonic()

    print(f'evaluating base mT5 on {len(validation_rows)} validation records', flush=True)
    base = load_base_model(device)
    total_parameters = sum(parameter.numel() for parameter in base.parameters())
    baseline_validation = score_model(
        base, tokenizer, validation_rows, max_input_length, max_target_length,
        evaluation_batch_size, device,
    )
    del base
    gc.collect()

    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    runs = []
    trainable_parameters = None
    for seed in seeds:
        torch.manual_seed(seed)
        base = load_base_model('cpu')
        config = LoraConfig(
            r=rank,
            lora_alpha=alpha,
            lora_dropout=0.0,
            bias='none',
            task_type=TaskType.SEQ_2_SEQ_LM,
            target_modules=list(TARGET_MODULES),
        )
        model = get_peft_model(base, config).to(device)
        trainable_parameters = trainable_parameters or sum(
            parameter.numel() for parameter in model.parameters()
            if parameter.requires_grad
        )
        pool = select_rows(train_rows, training_records, seed)
        print(f'training mT5 LoRA seed {seed} ({steps} steps)', flush=True)
        training = train_seed(
            model, tokenizer, pool, seed, steps, learning_rate,
            max_input_length, max_target_length, batch_size, device,
        )
        validation = score_model(
            model, tokenizer, validation_rows, max_input_length,
            max_target_length, evaluation_batch_size, device,
        )
        checkpoint = checkpoint_dir / f'seed-{seed}'
        model.save_pretrained(checkpoint, safe_serialization=True)
        runs.append({
            'seed': seed,
            'training': training,
            'validation': validation,
            'checkpoint': str(checkpoint.relative_to(ROOT)),
        })
        print(
            f"seed {seed}: validation loss {validation['cross_entropy']:.6f} "
            f"(base {baseline_validation['cross_entropy']:.6f})",
            flush=True,
        )
        del model, base
        gc.collect()

    summary = summarize_runs(baseline_validation, runs)
    print('opening fixed instruction test split for final evaluation', flush=True)
    base = load_base_model(device)
    base_test, base_hypotheses = evaluate_test_model(
        base, tokenizer, test_rows, max_input_length, max_target_length,
        max_new_tokens, evaluation_batch_size, device,
    )
    del base
    gc.collect()
    systems = {'base': {'test': base_test}}
    predictions = []
    for row, hypothesis in zip(test_rows, base_hypotheses):
        predictions.append({
            'instruction_sha256': row['instruction_sha256'],
            'task': row['task'],
            'reference': row['response'],
            'system': 'base',
            'hypothesis': hypothesis,
        })
    for run_record in runs:
        seed = run_record['seed']
        base = load_base_model('cpu')
        model = PeftModel.from_pretrained(
            base, checkpoint_dir / f'seed-{seed}', local_files_only=True,
        ).to(device)
        test_metrics, hypotheses = evaluate_test_model(
            model, tokenizer, test_rows, max_input_length, max_target_length,
            max_new_tokens, evaluation_batch_size, device,
        )
        run_record['test'] = test_metrics
        systems[f'seed-{seed}'] = {'test': test_metrics}
        for row, hypothesis in zip(test_rows, hypotheses):
            predictions.append({
                'instruction_sha256': row['instruction_sha256'],
                'task': row['task'],
                'reference': row['response'],
                'system': f'seed-{seed}',
                'hypothesis': hypothesis,
            })
        del model, base
        gc.collect()

    test_losses = [run['test']['cross_entropy'] for run in runs]
    selected_run = next(run for run in runs if run['seed'] == summary['best_seed'])
    selected_test = selected_run['test']
    report = {
        'run_id': 'garhwali-mt5-instruction-lora-v0.1',
        'status': 'completed_multi_seed_instruction_tuning',
        'model_id': MODEL_ID,
        'revision': REVISION,
        'adaptation_scope': 'LoRA on encoder and decoder attention q/v projections',
        'total_parameters': total_parameters,
        'trainable_parameters': trainable_parameters,
        'dataset': {
            'train_records': len(train_rows),
            'validation_records': len(validation_rows),
            'test_records': len(test_rows),
            'train_sha256': dataset_digest(train_rows),
            'validation_sha256': dataset_digest(validation_rows),
            'test_sha256': dataset_digest(test_rows),
            'tasks': dict(sorted(Counter(
                row['task'] for row in train_rows + validation_rows + test_rows
            ).items())),
        },
        'configuration': {
            'seeds': list(seeds),
            'steps_per_seed': steps,
            'training_pool_records_per_seed': min(training_records, len(train_rows)),
            'batch_size': batch_size,
            'learning_rate': learning_rate,
            'max_input_length': max_input_length,
            'max_target_length': max_target_length,
            'max_new_tokens': max_new_tokens,
            'generation_control_tokens_removed': True,
            'lora_rank': rank,
            'lora_alpha': alpha,
            'target_modules': list(TARGET_MODULES),
            'device': device,
        },
        'baseline_validation': baseline_validation,
        'runs': runs,
        'summary': summary | {
            'mean_test_cross_entropy': round(statistics.mean(test_losses), 8),
            'std_test_cross_entropy': round(statistics.pstdev(test_losses), 8),
            'selected_seed_test_cross_entropy': selected_test['cross_entropy'],
            'selected_seed_test_exact_match': selected_test['exact_match'],
            'selected_seed_test_corpus_chrf2': selected_test['corpus_chrf2'],
            'all_seed_test_cross_entropy_below_base': all(
                loss < base_test['cross_entropy'] for loss in test_losses
            ),
            'generation_promotion_status': (
                'candidate_for_extended_evaluation'
                if selected_test['exact_match'] > 0 else 'not_promoted_for_generation'
            ),
        },
        'test_systems': systems,
        'integrity': {
            'training_split_only': True,
            'selection_split': 'validation',
            'test_opened_after_training_and_selection': True,
            'test_records_used_for_training': 0,
            'source_text_mutated': False,
            'all_records_active_for_experiment': True,
        },
        'elapsed_seconds': round(time.monotonic() - started, 3),
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    write_jsonl(output_dir / 'test_predictions.jsonl', predictions)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=Path, default=DATA)
    parser.add_argument('--output-dir', type=Path, default=OUTPUT)
    parser.add_argument('--checkpoint-dir', type=Path, default=CHECKPOINTS)
    parser.add_argument('--seeds', default=','.join(map(str, DEFAULT_SEEDS)))
    parser.add_argument('--steps', type=int, default=64)
    parser.add_argument('--training-records', type=int, default=2304)
    parser.add_argument('--validation-records', type=int, default=130)
    parser.add_argument('--learning-rate', type=float, default=2e-4)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--evaluation-batch-size', type=int, default=4)
    parser.add_argument('--max-input-length', type=int, default=96)
    parser.add_argument('--max-target-length', type=int, default=72)
    parser.add_argument('--max-new-tokens', type=int, default=32)
    parser.add_argument('--rank', type=int, default=4)
    parser.add_argument('--alpha', type=int, default=8)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    report = run(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        checkpoint_dir=args.checkpoint_dir,
        seeds=tuple(int(seed) for seed in args.seeds.split(',')),
        steps=args.steps,
        training_records=args.training_records,
        validation_records=args.validation_records,
        learning_rate=args.learning_rate,
        batch_size=args.batch_size,
        evaluation_batch_size=args.evaluation_batch_size,
        max_input_length=args.max_input_length,
        max_target_length=args.max_target_length,
        max_new_tokens=args.max_new_tokens,
        rank=args.rank,
        alpha=args.alpha,
        device=args.device,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
