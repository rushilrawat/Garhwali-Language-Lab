#!/usr/bin/env python3
"""Evaluate zero-shot IndicBERTv2 mean-pooled retrieval on Garhwali XORQA."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from run_retrieval_baseline import build_documents, context_id, metric_summary


ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = 'ai4bharat/IndicBERTv2-MLM-only'
REVISION = '8598f13fe52443bc3fc054fcd665944560145b5c'
MODEL = ROOT / '.cache/huggingface/hub/models--ai4bharat--IndicBERTv2-MLM-only/snapshots' / REVISION
INPUT = ROOT / 'benchmarks/indicgenbench_xorqa.jsonl'
OUTPUT = ROOT / 'data/processed/evaluation/retrieval/indicbertv2'


def select_evaluation_rows(rows, limit):
    selected = sorted(
        (row for row in rows if row.get('split') == 'test'),
        key=lambda row: row.get('record_id', ''),
    )
    return selected[:limit] if limit else selected


def rank_scores(document_ids, scores, relevant_id, top_k=10):
    ranked = sorted(
        zip(document_ids, scores),
        key=lambda item: (-item[1], item[0]),
    )
    rank = next(index for index, (document_id, _) in enumerate(ranked, 1)
                if document_id == relevant_id)
    return {
        'rank': rank,
        'relevant_score': round(ranked[rank - 1][1], 8),
        'top': [
            {'document_id': document_id, 'score': round(score, 8)}
            for document_id, score in ranked[:top_k]
        ],
    }


def encode_texts(texts, tokenizer, model, torch, device, batch_size, max_tokens):
    batches = []
    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            encoded = tokenizer(
                texts[start:start + batch_size],
                padding=True,
                truncation=True,
                max_length=max_tokens,
                return_tensors='pt',
            )
            encoded = {name: value.to(device) for name, value in encoded.items()}
            hidden = model(**encoded).last_hidden_state
            mask = encoded['attention_mask'].unsqueeze(-1)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            batches.append(pooled.cpu())
    return torch.cat(batches)


def run(
    input_path=INPUT,
    output_dir=OUTPUT,
    model_path=MODEL,
    max_records=128,
    batch_size=8,
    max_document_tokens=192,
    max_query_tokens=64,
    device='auto',
):
    os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
    import torch
    from transformers import AutoModel, AutoTokenizer

    if device == 'auto':
        device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    with Path(input_path).open(encoding='utf-8') as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    documents, _ = build_documents(rows)
    evaluation_rows = select_evaluation_rows(rows, max_records)
    document_ids = [row['document_id'] for row in documents]
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    model = AutoModel.from_pretrained(model_path, local_files_only=True).to(device)
    model.eval()
    start = time.monotonic()
    document_embeddings = encode_texts(
        [row['text'] for row in documents], tokenizer, model, torch, device,
        batch_size, max_document_tokens,
    )
    query_embeddings = encode_texts(
        [row['source_example']['question'] for row in evaluation_rows],
        tokenizer, model, torch, device, batch_size, max_query_tokens,
    )
    similarities = torch.matmul(query_embeddings, document_embeddings.T)
    results = []
    predictions = []
    for row, scores in zip(evaluation_rows, similarities.tolist()):
        relevant_id = context_id(row['source_example']['context'])
        ranking = rank_scores(document_ids, scores, relevant_id)
        results.append({
            'rank': ranking['rank'],
            'relevant_score': ranking['relevant_score'],
        })
        predictions.append({
            'record_id': row.get('record_id'),
            'split': row['split'],
            'rank': ranking['rank'],
            'relevant_score': ranking['relevant_score'],
            'top_10': ranking['top'],
        })
    report = {
        'run_id': 'indicbertv2-garhwali-xorqa-retrieval-v0.1',
        'model_id': MODEL_ID,
        'revision': REVISION,
        'pooling': 'attention_mask_mean_pooling_l2_normalized',
        'training': 'zero_shot; no retrieval fine-tuning',
        'corpus_documents': len(documents),
        'evaluation_split': 'test',
        'evaluation_queries': len(evaluation_rows),
        'max_document_tokens': max_document_tokens,
        'max_query_tokens': max_query_tokens,
        'batch_size': batch_size,
        'device': device,
        'elapsed_seconds': round(time.monotonic() - start, 3),
        **metric_summary(results),
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
    parser.add_argument('--input', type=Path, default=INPUT)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--max-records', type=int, default=128)
    parser.add_argument('--batch-size', type=int, default=8)
    parser.add_argument('--max-document-tokens', type=int, default=192)
    parser.add_argument('--max-query-tokens', type=int, default=64)
    parser.add_argument('--device', choices=('auto', 'mps', 'cpu'), default='auto')
    args = parser.parse_args()
    print(json.dumps(run(
        args.input,
        args.output,
        max_records=args.max_records,
        batch_size=args.batch_size,
        max_document_tokens=args.max_document_tokens,
        max_query_tokens=args.max_query_tokens,
        device=args.device,
    ), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
