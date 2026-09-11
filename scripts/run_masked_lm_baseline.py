#!/usr/bin/env python3
"""Run a deterministic masked-token pilot on held-out Garhwali text."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'ai4bharat/IndicBERTv2-MLM-only'
REVISION = '8598f13fe52443bc3fc054fcd665944560145b5c'
MODEL = ROOT / '.cache/huggingface/hub/models--ai4bharat--IndicBERTv2-MLM-only/snapshots' / REVISION
INPUT = ROOT / 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/model_audit/indicbertv2_masked_lm.json'


def select_mask_positions(token_ids, attention_mask, special_ids, record_key, rate, seed):
    candidates = [
        index for index, (token_id, attended) in enumerate(zip(token_ids, attention_mask))
        if attended and token_id not in special_ids
    ]
    if not candidates:
        return []
    scored = []
    for index in candidates:
        digest = hashlib.sha256(f'{seed}:{record_key}:{index}'.encode()).digest()
        score = int.from_bytes(digest[:8], 'big') / 2**64
        scored.append((score, index))
    selected = [index for score, index in scored if score < rate]
    return sorted(selected or [min(scored)[1]])


def read_rows(path, limit):
    rows = sorted(
        (json.loads(line) for line in Path(path).open(encoding='utf-8') if line.strip()),
        key=lambda row: row.get('segment_sha256', ''),
    )
    return rows[:limit] if limit else rows


def run_baseline(
    input_path=INPUT,
    output_path=OUTPUT,
    model_path=MODEL,
    max_records=128,
    max_length=256,
    mask_rate=0.15,
    seed=17,
    device='auto',
):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    import torch.nn.functional as functional
    from transformers import AutoModelForMaskedLM, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    rows = read_rows(input_path, max_records)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        local_files_only=True,
        fix_mistral_regex=True,
    )
    model = AutoModelForMaskedLM.from_pretrained(model_path, local_files_only=True).to(device)
    model.eval()
    if not hasattr(model, 'bert') or not hasattr(model, 'cls'):
        raise TypeError('baseline requires a BERT masked-language model')

    loss_sum = 0.0
    correct = 0
    masked_tokens = 0
    truncated_records = 0
    start = time.monotonic()
    special_ids = set(tokenizer.all_special_ids)
    with torch.no_grad():
        for row in rows:
            full_ids = tokenizer(row.get('text', ''), add_special_tokens=True)['input_ids']
            truncated_records += len(full_ids) > max_length
            encoded = tokenizer(
                row.get('text', ''),
                add_special_tokens=True,
                max_length=max_length,
                truncation=True,
                return_tensors='pt',
            )
            positions = select_mask_positions(
                encoded['input_ids'][0].tolist(),
                encoded['attention_mask'][0].tolist(),
                special_ids,
                row.get('segment_sha256', ''),
                mask_rate,
                seed,
            )
            if not positions:
                continue
            labels = encoded['input_ids'][0, positions].to(device)
            encoded['input_ids'][0, positions] = tokenizer.mask_token_id
            model_inputs = {name: value.to(device) for name, value in encoded.items()}
            hidden = model.bert(**model_inputs).last_hidden_state[0, positions]
            logits = model.cls(hidden)
            loss_sum += float(functional.cross_entropy(logits, labels, reduction='sum').cpu())
            correct += int((logits.argmax(dim=-1) == labels).sum().cpu())
            masked_tokens += len(positions)

    mean_loss = loss_sum / max(1, masked_tokens)
    report = {
        'run_id': 'indicbertv2-garhwali-masked-lm-v0.1',
        'model_id': MODEL_ID,
        'revision': REVISION,
        'evaluation_records': len(rows),
        'masked_tokens': masked_tokens,
        'mask_rate': mask_rate,
        'seed': seed,
        'max_length': max_length,
        'truncated_records': truncated_records,
        'masked_token_cross_entropy': round(mean_loss, 6),
        'masked_token_perplexity': round(math.exp(mean_loss), 6),
        'masked_token_accuracy': round(correct / max(1, masked_tokens), 8),
        'device': device,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        'scope': 'deterministic held-out pilot; masked positions selected by record hash',
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
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--max-records', type=int, default=128)
    parser.add_argument('--max-length', type=int, default=256)
    parser.add_argument('--mask-rate', type=float, default=0.15)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run_baseline(
        args.input,
        args.output,
        max_records=args.max_records,
        max_length=args.max_length,
        mask_rate=args.mask_rate,
        seed=args.seed,
        device=args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
