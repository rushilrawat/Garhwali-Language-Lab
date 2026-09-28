# XORQA retrieval source-page-cluster uncertainty — 2026-09-28

## Purpose

The saved 500-query Garhwali BM25 development comparison had query-level metrics but no uncertainty interval accounting for multiple questions derived from the same Wikipedia page. This analysis resamples complete source-page families to avoid treating those related questions as independent observations. It uses the saved predictions only: no model inference, retraining, test scoring, Hub job, or paid compute was run.

## Lineage and preflight

The analysis matched all 500 saved prediction IDs exactly to the 500 XORQA `dev` IDs. All prediction rows were marked `dev`; every dev row had a parseable source-page title; all three retriever ranks were present or explicitly null. The saved BM25 report's benchmark-input SHA-256 matched the current benchmark file, and recomputed point metrics reproduced the saved report. No test predictions were used.

| Input | SHA-256 |
| --- | --- |
| `benchmarks/indicgenbench_xorqa.jsonl` | `e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6` |
| Saved BM25 dev `predictions.jsonl` | `3f7df640f9a27f4fc565a9f890eb87c20d14061f59e682bc818704bfb5eccd29` |
| Saved BM25 dev `report.json` | `dafb5582955de71b69cc0686104d3689eb976cc7c304d7a34c30b0128ac66fbf` |

The report pins a fixed candidate corpus of 1,059 documents with SHA-256 `9618e40f63f8e2744e8394b0d480f258a4730847b8399da7e644b45d27e7d9c0`.

## Clustered bootstrap

Source-page family IDs use the exact normalized page segment encoded by the upstream XORQA title locator: NFKC normalization, case folding, whitespace collapse, and the segment before `_parentSection:`. The title itself is not copied into the output. The 500 dev questions map to 461 source-page families: 427 singleton families and 34 multi-question families containing 73 rows (30 two-question, 3 three-question, and 1 four-question family).

For each of 2,000 replicates (seed 1729), the analysis samples 461 page families with replacement, retaining all questions from every selected family. Metrics remain query-weighted within each replicate. The confidence limits are 2.5th and 97.5th percentiles with linear interpolation. Character-versus-word deltas use the same resampled families in each paired replicate.

| Retriever | Recall@1 | Recall@5 | Recall@10 | MRR@10 |
| --- | ---: | ---: | ---: | ---: |
| Garhwali word BM25 | 0.0060 [0.0000, 0.0140] | 0.0080 [0.0020, 0.0163] | 0.0080 [0.0020, 0.0163] | 0.0064 [0.0004, 0.0144] |
| Garhwali character BM25 | 0.0080 [0.0020, 0.0163] | 0.0100 [0.0020, 0.0199] | 0.0100 [0.0020, 0.0199] | 0.0087 [0.0020, 0.0173] |
| English-query BM25 diagnostic | 0.5760 [0.5299, 0.6206] | 0.8100 [0.7758, 0.8433] | 0.8520 [0.8206, 0.8834] | 0.6772 [0.6404, 0.7127] |

Paired character-minus-word Garhwali BM25 differences are small: Recall@1 +0.0020 (95% interval [0.0000, 0.0061]), Recall@5/10 +0.0020 ([0.0000, 0.0061]), and MRR@10 +0.00226667 ([0.00000000, 0.00628684]). The intervals touch zero, so these saved dev results do not establish a reliable advantage for character BM25. The Garhwali-query recall is very low for both lexical baselines; the much higher English-query result is an upper-bound diagnostic that points to the cross-language retrieval gap, not a Garhwali model-quality score.

## Limits and reproducibility

The 1,059-document candidate corpus is fixed and contains documents derived from all original splits. The intervals therefore describe uncertainty among these dev queries conditional on that corpus; they are **not** a page-held-out generalization estimate and do not clear the known cross-split source-page overlap. They also do not validate the references or Garhwali language quality, which remain without native-speaker adjudication. This post-hoc analysis is uncertainty reporting, not a model improvement.

The script verifies prediction-ID equality, split labels, source-page lineage, parent-report input hash, and exact reproduction of saved dev metrics before writing its output. Re-run with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_retrieval_cluster_uncertainty.py
```

The hash-linked JSON and Markdown outputs are local-only under `data/processed/evaluation/retrieval/roadmap_2026-09-28/source_page_cluster_bootstrap/` and are excluded from Git.
