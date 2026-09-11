# Garhwali cross-lingual retrieval baseline

Generated on 2026-09-11 from the frozen IndicGenBench XORQA Garhwali asset in
`benchmarks/indicgenbench_xorqa.jsonl`. The audit asks a concrete question: can a
Garhwali query retrieve its associated English evidence passage?

## Evaluation design

The 1,139 source rows collapse to **1,059 normalized unique passages**. All
passages form one fixed index. Train-labelled questions are never scored; the
evaluation contains **500 dev** and **539 test** questions. Every evaluated row's
English answer text occurs in its associated passage.

Exact context duplicates share one passage identifier. Recall and reciprocal
rank credit the row-associated passage. Other passages that may also answer a
question are not labelled relevant, so the scores are conservative when several
passages contain valid evidence.

## Full test results

| Retriever | Queries | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Garhwali word BM25 | 539 | 0.001855 | 0.005566 | 0.016698 | 0.004263 |
| Garhwali character 3–5 gram BM25 | 539 | 0.005566 | 0.014842 | 0.024119 | 0.009168 |
| IndicBERTv2 mean-pooled cosine | 539 | **0.022263** | **0.081633** | **0.103896** | **0.046607** |

IndicBERTv2 improves Recall@10 by 4.31 times over character BM25. The absolute
result remains low: almost nine in ten questions still lack the associated
passage in the first ten results. This is a useful baseline for later retrieval
fine-tuning and translation-assisted retrieval, not a production RAG system.

## Diagnostic comparator

The upstream test rows contain empty `oracle_question` fields, so an English
oracle comparison is impossible on test. On the 500 dev rows where English
oracle questions exist, word BM25 reaches **0.576 Recall@1**, **0.810 Recall@5**,
**0.852 Recall@10**, and **0.677235 MRR@10**. This large cross-language gap shows
that passage indexing is viable while Garhwali-to-English query alignment is the
main baseline weakness.

## Model configuration

The semantic run uses pinned `ai4bharat/IndicBERTv2-MLM-only` revision
`8598f13fe52443bc3fc054fcd665944560145b5c`. It mean-pools attention-masked token
states, applies L2 normalization, and ranks passages by cosine similarity. It
uses no retrieval fine-tuning, 192-token passage truncation, and 64-token query
truncation. The model supports English and several related Devanagari languages,
but its model card does not list Garhwali.

## Reproduction

```bash
.venv/bin/python scripts/run_retrieval_baseline.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_indicbert_retrieval_baseline.py --max-records 0 --device cpu
```

Generated embeddings, rankings, and aggregate JSON reports remain ignored by
Git. Aggregate results are copied into the tracked candidate release manifest.
