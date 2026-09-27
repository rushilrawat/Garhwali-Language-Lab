# Garhwali retrieval baseline refresh

**Run date:** 2026-09-25

**Status:** development-only lexical baseline; no test queries scored
**Execution:** local CPU, dependency-free BM25; no Hugging Face job or download

## What ran

The XORQA retrieval runner was tightened so its evaluation and model-selection
path accepts only `dev`. Both the BM25 and IndicBERTv2 entry points default to
development rows and reject `test`; reports carry input and candidate-corpus
SHA-256 hashes, evaluated record IDs, passage-to-source-row mappings, duplicate
groups, and an explicit evaluation status. BM25 no longer treats a zero-score
passage as retrieved just because its stable ID happened to sort near the top.

The current XORQA manifest contains **1,139 rows**. The fixed candidate
collection contains **1,059 unique context passages**, with **65 exact duplicate
passage groups**. Duplicate source-row IDs are preserved in the generated JSON
report. The candidate collection intentionally includes contexts attached to
train, dev, and test rows; this is retrieval against the benchmark's known
passage collection, not an unseen-document or fully isolated-corpus test.

This run scored **500 development questions**. Every prediction is a dev row;
`test_scored` is `false`. The frozen input manifest SHA-256 is
`e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6`, and the
canonical deduplicated passage-corpus SHA-256 is
`9618e40f63f8e2744e8394b0d480f258a4730847b8399da7e644b45d27e7d9c0`.

## Development scores

| Query / retriever | Answer passage retrieved | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Garhwali query, word BM25 | 4 / 500 | 0.60% | 0.80% | 0.80% | 0.006400 |
| Garhwali query, character 3–5gram BM25 | 7 / 500 | 0.80% | 1.00% | 1.00% | 0.008667 |
| English oracle query, word BM25 | 499 / 500 | 57.60% | 81.00% | 85.20% | 0.677235 |

“Retrieved” means the gold context received a nonzero BM25 score. Zero-score
positives receive a null rank and do not count toward recall or MRR. Mean and
median rank summarize only queries whose relevant passage received a nonzero
score; the coverage column makes that denominator explicit.

The English oracle result is a diagnostic upper bound, not a Garhwali-quality
score: it uses the benchmark's paired English questions against English context
passages. Its large gap over Garhwali-query BM25 shows that lexical matching
does not bridge the query/context language difference. The lexical baseline is
therefore a low floor, not a usable Garhwali retrieval model and not evidence
that the underlying corpus is linguistically inaccurate.

## What remains blocked

The planned zero-shot IndicBERTv2 development run and dense-retriever experiment
were not run. The active local environment lacks PyTorch and Transformers, and
the pinned IndicBERTv2 weights are not cached. This roadmap is local-only; no
model packages or weights were downloaded and no paid Hugging Face compute was
started. The dense branch should proceed only if a compatible local runtime and
the exact checkpoint become available under the existing no-download policy.

The XORQA test split already has saved predictions for all 539 rows. It remains
historical and was not rescored. No independent final retrieval score is
established. Existing native-language and dialect-review deferrals remain in
force.

## Reproduction and artifacts

```bash
.venv/bin/python scripts/run_retrieval_baseline.py \
  --input benchmarks/indicgenbench_xorqa.jsonl \
  --output data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev \
  --selection-split dev

PYTHONPATH=scripts .venv/bin/python -m unittest \
  tests.test_run_retrieval_baseline \
  tests.test_run_indicbert_retrieval_baseline -v
```

The local generated `report.json` and `predictions.jsonl` are under
`data/processed/evaluation/retrieval/roadmap_2026-09-25/bm25_dev/`; generated
data remains excluded from Git. The complete project suite passed **470 tests**
after this change.
