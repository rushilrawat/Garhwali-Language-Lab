#!/usr/bin/env python3
"""Evaluate official NLLB with an explicit Hindi source-token proxy for Garhwali."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from evaluation_run_manifest import utc_now, write_run_artifacts
from run_translation_baseline import metric_summary


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'facebook/nllb-200-distilled-600M'
REVISION = 'f8d333a098d19b4fd9a8b18f94170487ad3f821d'
MODEL = ROOT / '.cache/huggingface/hub/models--facebook--nllb-200-distilled-600M/snapshots' / REVISION
INPUT = ROOT / 'benchmarks/indicgenbench_flores.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/translation'
ADAPTER_ID = 'Gaurav17/garhwali-nllb-v12'
ADAPTER_REVISION = 'c17ad35a9fc522aae5da231adb5a0ecf1258e4a3'


def select_rows(rows, split='dev', limit=None):
    if split not in {'dev', 'test'}:
        raise ValueError("split must be 'dev' or 'test'")
    if limit is not None and limit < 0:
        raise ValueError('limit must be zero or greater')
    selected = sorted(
        (row for row in rows if row.get('split') == split),
        key=lambda row: row.get('record_id', ''),
    )
    return selected[:limit] if limit else selected


def selected_rows_sha256(rows):
    payload = ''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        for row in rows
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def run(
    input_path=INPUT,
    output_dir=None,
    model_path=MODEL,
    adapter_path=None,
    max_records=32,
    max_source_tokens=256,
    max_new_tokens=128,
    device='auto',
    split='dev',
    allow_historical_test=False,
):
    started_at_utc = utc_now()
    if split not in {'dev', 'test'}:
        raise ValueError("split must be 'dev' or 'test'")
    if split == 'test' and not allow_historical_test:
        raise ValueError('test scoring requires allow_historical_test=True')
    if device not in {'auto', 'mps', 'cpu'}:
        raise ValueError("device must be 'auto', 'mps', or 'cpu'")
    if max_source_tokens <= 0 or max_new_tokens <= 0:
        raise ValueError('token limits must be greater than zero')
    if max_records is not None and max_records < 0:
        raise ValueError('max_records must be zero or greater')

    input_path = Path(input_path)
    if not input_path.is_file():
        raise FileNotFoundError(f'evaluation input does not exist: {input_path}')
    with input_path.open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    rows = select_rows(rows, split, max_records)
    if not rows:
        raise ValueError(f'no records found for split: {split}')
    if any(
        not isinstance(row.get('source_example'), dict)
        or row['source_example'].get('translation_direction') != 'xxen'
        or not isinstance(row['source_example'].get('source'), str)
        or not isinstance(row['source_example'].get('target'), str)
        or not isinstance(row.get('record_id'), str)
        for row in rows
    ):
        raise ValueError('expected identified FLORES rows with Garhwali-to-English text')
    record_ids = [row['record_id'] for row in rows]
    if len(record_ids) != len(set(record_ids)):
        raise ValueError('selected evaluation rows contain duplicate record_id values')

    model_path = Path(model_path)
    if not model_path.is_dir():
        raise FileNotFoundError(f'local model checkpoint does not exist: {model_path}')
    model_config_path = model_path / 'config.json'
    if not model_config_path.is_file():
        raise ValueError(f'local model checkpoint is missing config.json: {model_path}')
    adapter_config_path = None
    if adapter_path is not None:
        adapter_path = Path(adapter_path)
        if not adapter_path.is_dir():
            raise FileNotFoundError(f'local adapter checkpoint does not exist: {adapter_path}')
        adapter_config_path = adapter_path / 'adapter_config.json'
        if not adapter_config_path.is_file():
            raise ValueError(f'local adapter checkpoint is missing adapter_config.json: {adapter_path}')

    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    import transformers
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    mps_available = bool(getattr(
        getattr(getattr(torch, 'backends', None), 'mps', None),
        'is_available',
        lambda: False,
    )())
    if device == 'auto':
        device = 'mps' if mps_available else 'cpu'
    elif device == 'mps' and not mps_available:
        raise ValueError('MPS device was requested but is not available')
    tokenizer = AutoTokenizer.from_pretrained(
        model_path,
        src_lang='hin_Deva',
        tgt_lang='eng_Latn',
        local_files_only=True,
        fix_mistral_regex=True,
    )
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path, local_files_only=True)
    if adapter_path is not None:
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
        'evaluation_split': split,
        'evaluation_status': 'historical_already_scored' if split == 'test' else 'development_only',
        'input_name': Path(input_path).name,
        'script_sha256': file_sha256(__file__),
        'python_version': sys.version.split()[0],
        'max_records': max_records,
        'decoding': {
            'num_beams': 1,
            'do_sample': False,
            'max_source_tokens': max_source_tokens,
            'max_new_tokens': max_new_tokens,
        },
        'evaluation_records': len(predictions),
        'selected_record_ids': [row['record_id'] for row in rows],
        'input_sha256': file_sha256(input_path),
        'selected_rows_sha256': selected_rows_sha256(rows),
        'max_source_tokens': max_source_tokens,
        'max_target_tokens': max_new_tokens,
        'device': device,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        **metrics,
    }
    if output_dir is None:
        model_name = 'nllb_garhwali_adapter_hindi_proxy' if adapter_path else 'nllb_hindi_proxy'
        output_dir = OUTPUT / f'accuracy_{split}' / model_name
    output_dir = Path(output_dir)
    write_run_artifacts(
        output_dir,
        predictions,
        report,
        config={
            'split': split,
            'max_records': max_records,
            'source_language_token': 'hin_Deva',
            'target_language_token': 'eng_Latn',
            'decoding': report['decoding'],
            'metric': {
                'implementation': 'run_translation_baseline.metric_summary',
                'normalizer': 'NFC, case-fold, collapse whitespace, trim',
            },
        },
        model={
            'id': MODEL_ID,
            'revision': REVISION,
            'config_sha256': file_sha256(model_config_path),
            'adapter_id': ADAPTER_ID if adapter_path is not None else None,
            'adapter_revision': ADAPTER_REVISION if adapter_path is not None else None,
            'adapter_config_sha256': (
                file_sha256(adapter_config_path) if adapter_config_path is not None else None
            ),
        },
        runtime={
            'python': sys.version.split()[0],
            'torch': torch.__version__,
            'transformers': transformers.__version__,
        },
        device=device,
        code_paths=(
            __file__,
            Path(__file__).with_name('run_translation_baseline.py'),
            Path(__file__).with_name('evaluation_run_manifest.py'),
        ),
        git_root=ROOT,
        started_at_utc=started_at_utc,
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--split', choices=('dev', 'test'), default='dev')
    parser.add_argument('--allow-historical-test', action='store_true')
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
        split=args.split,
        allow_historical_test=args.allow_historical_test,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
