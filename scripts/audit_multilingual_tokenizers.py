#!/usr/bin/env python3
"""Measure Garhwali tokenization for pinned multilingual model candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.cache/huggingface/hub'
INPUT = ROOT / 'data/processed/model_ready/splits/evaluation/text_candidate.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/model_audit/tokenizer_report.json'
MODELS = (
    {
        'repo_id': 'google/muril-base-cased',
        'revision': 'afd9f36c7923d54e97903922ff1b260d091d202f',
        'family': 'Indic encoder',
    },
    {
        'repo_id': 'google/mt5-small',
        'revision': '73fb5dbe4756edadc8fbe8c769b0a109493acf7a',
        'family': 'multilingual encoder-decoder',
    },
    {
        'repo_id': 'FacebookAI/xlm-roberta-base',
        'revision': 'e73636d4f797dec63c3081bb6ed5c7b0bb3f2089',
        'family': 'multilingual encoder',
    },
    {
        'repo_id': 'ai4bharat/IndicBERTv2-MLM-only',
        'revision': '8598f13fe52443bc3fc054fcd665944560145b5c',
        'family': 'Indic encoder',
    },
    {
        'repo_id': 'hikinegi/UK-Garhwali-Language',
        'revision': '3c714bfcf195f5917cd2b3a78d4fe5b436645f35',
        'family': 'Garhwali OpenLLaMA LoRA tokenizer',
        'base_model': 'openlm-research/open_llama_3b_v2',
        'declared_max_length': 2048,
    },
)


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', str(text))).strip()


def score_tokenizer(tokenizer, texts, max_length=None):
    tokens = 0
    words = 0
    characters = 0
    unknowns = 0
    empty = 0
    over_context = 0
    unknown_id = getattr(tokenizer, 'unk_token_id', None)
    for raw_text in texts:
        text = normalize(raw_text)
        token_ids = tokenizer(text, add_special_tokens=False)['input_ids']
        tokens += len(token_ids)
        words += len(text.split())
        characters += len(text)
        empty += not token_ids
        if unknown_id is not None:
            unknowns += sum(token_id == unknown_id for token_id in token_ids)
        if max_length:
            over_context += len(token_ids) > max_length
    return {
        'records': len(texts),
        'characters': characters,
        'whitespace_words': words,
        'tokens': tokens,
        'fertility_tokens_per_word': round(tokens / max(1, words), 6),
        'characters_per_token': round(characters / max(1, tokens), 6),
        'unknown_tokens': unknowns,
        'unknown_token_rate': round(unknowns / max(1, tokens), 8),
        'empty_encodings': empty,
        'max_context_tokens': max_length,
        'sequences_over_context': over_context,
        'tokenizer_vocabulary_size': getattr(tokenizer, 'vocab_size', None),
    }


def snapshot_path(model, cache=CACHE):
    directory = 'models--' + model['repo_id'].replace('/', '--')
    return Path(cache) / directory / 'snapshots' / model['revision']


def tokenizer_files_sha256(path):
    digest = hashlib.sha256()
    names = ('config.json', 'adapter_config.json', 'special_tokens_map.json',
             'spiece.model', 'sentencepiece.bpe.model', 'tokenizer.json',
             'tokenizer.model', 'tokenizer_config.json', 'vocab.txt')
    for name in names:
        candidate = Path(path) / name
        if candidate.exists():
            digest.update(name.encode())
            digest.update(candidate.read_bytes())
    return digest.hexdigest()


def model_max_length(model, path, tokenizer):
    if model.get('declared_max_length'):
        return model['declared_max_length']
    config_path = path / 'config.json'
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    value = config.get('max_position_embeddings') or config.get('n_positions')
    if isinstance(value, int) and 0 < value < 1_000_000:
        return value
    value = getattr(tokenizer, 'model_max_length', None)
    return value if isinstance(value, int) and 0 < value < 1_000_000 else None


def audit(input_path=INPUT, output_path=OUTPUT, cache=CACHE):
    from transformers import AutoTokenizer

    texts = [
        json.loads(line).get('text', '')
        for line in Path(input_path).open(encoding='utf-8')
        if line.strip()
    ]
    results = []
    for model in MODELS:
        path = snapshot_path(model, cache)
        if not path.exists():
            raise FileNotFoundError(f"missing pinned tokenizer snapshot: {path}")
        tokenizer = AutoTokenizer.from_pretrained(
            path,
            local_files_only=True,
            fix_mistral_regex=True,
        )
        result = score_tokenizer(tokenizer, texts, model_max_length(model, path, tokenizer))
        results.append({
            **model,
            'tokenizer_files_sha256': tokenizer_files_sha256(path),
            'weights_downloaded': any(path.glob('*.bin')) or any(path.glob('*.safetensors')),
            **result,
        })
    report = {
        'audit_id': 'garhwali-multilingual-tokenizers-v0.1',
        'input': str(Path(input_path).relative_to(ROOT)),
        'records': len(texts),
        'scope': 'tokenizer_and_declared_architecture_only',
        'models': sorted(results, key=lambda row: row['fertility_tokens_per_word']),
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
    args = parser.parse_args()
    print(json.dumps(audit(args.input, args.output), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
