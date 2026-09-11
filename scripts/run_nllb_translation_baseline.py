#!/usr/bin/env python3
"""Evaluate official NLLB with an explicit Hindi source-token proxy for Garhwali."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from run_translation_baseline import metric_summary


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'facebook/nllb-200-distilled-600M'
REVISION = 'f8d333a098d19b4fd9a8b18f94170487ad3f821d'
MODEL = ROOT / '.cache/huggingface/hub/models--facebook--nllb-200-distilled-600M/snapshots' / REVISION
INPUT = ROOT / 'benchmarks/indicgenbench_flores.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/translation/nllb_hindi_proxy'
ADAPTER_ID = 'Gaurav17/garhwali-nllb-v12'
ADAPTER_REVISION = 'c17ad35a9fc522aae5da231adb5a0ecf1258e4a3'


def select_test_rows(rows, limit):
    selected = sorted(
        (row for row in rows if row.get('split') == 'test'),
        key=lambda row: row.get('record_id', ''),
    )
    return selected[:limit] if limit else selected


def run(
    input_path=INPUT,
    output_dir=OUTPUT,
    model_path=MODEL,
    adapter_path=None,
    max_records=32,
    max_source_tokens=256,
    max_new_tokens=128,
    device='auto',
):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = select_test_rows(rows, max_records)
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        src_lang='hin_Deva',
        tgt_lang='eng_Latn',
        local_files_only=True,
        fix_mistral_regex=True,
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True)
    if adapter_path:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter_path, local_files_only=True)
    model = model.to(device)
    model.eval()
    target_token = tokenizer.convert_tokens_to_ids('eng_Latn')
    predictions = []
    start = time.monotonic()
    with torch.no_grad():
        for row in rows:
            example = row['source_example']
            encoded = tokenizer(
                example['source'],
                return_tensors='pt',
                truncation=True,
                max_length=max_source_tokens,
            )
            encoded = {name: value.to(device) for name, value in encoded.items()}
            generated = model.generate(
                **encoded,
                forced_bos_token_id=target_token,
                max_length=max_new_tokens,
                num_beams=1,
                do_sample=False,
            )
            hypothesis = tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()
            predictions.append({
                'record_id': row.get('record_id'),
                'source': example['source'],
                'reference': example['target'],
                'hypothesis': hypothesis,
            })
    metrics = metric_summary(
        [row['reference'] for row in predictions],
        [row['hypothesis'] for row in predictions],
    )
    report = {
        'run_id': (
            'garhwali-nllb-v12-hindi-proxy-v0.1'
            if adapter_path else 'nllb-200-distilled-600m-garhwali-hindi-proxy-v0.1'
        ),
        'model_id': MODEL_ID,
        'revision': REVISION,
        'adapter_id': ADAPTER_ID if adapter_path else None,
        'adapter_revision': ADAPTER_REVISION if adapter_path else None,
        'adapter_language_token_mapping': 'undocumented' if adapter_path else None,
        'source_language_token': 'hin_Deva',
        'source_language_token_status': 'explicit_proxy_because_nllb_has_no_garhwali_token',
        'target_language_token': 'eng_Latn',
        'evaluation_records': len(predictions),
        'max_source_tokens': max_source_tokens,
        'max_target_tokens': max_new_tokens,
        'device': device,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        **metrics,
    }
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'predictions.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in predictions),
        encoding='utf-8',
    )
    (output_dir / 'report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + '\n',
        encoding='utf-8',
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--adapter', type=Path)
    parser.add_argument('--max-records', type=int, default=32)
    parser.add_argument('--max-source-tokens', type=int, default=256)
    parser.add_argument('--max-new-tokens', type=int, default=128)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        args.input,
        args.output,
        adapter_path=args.adapter,
        max_records=args.max_records,
        max_source_tokens=args.max_source_tokens,
        max_new_tokens=args.max_new_tokens,
        device=args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
