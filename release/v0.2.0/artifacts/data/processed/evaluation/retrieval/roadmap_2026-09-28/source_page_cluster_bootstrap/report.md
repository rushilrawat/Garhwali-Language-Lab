# XORQA retrieval source-page-cluster uncertainty

This analysis resamples complete source-page families among the saved 500-query development predictions. It adds uncertainty estimates; it does not retrain a model, evaluate held-out pages, or score the test split.

- Dev queries: 500
- Source-page families: 461
- Families with multiple queries: 34 (73 rows)
- Bootstrap: 2,000 replicates, seed 1729

| Retriever | R@1 | R@5 | R@10 | MRR@10 |
| --- | ---: | ---: | ---: | ---: |
| `garhwali_word_bm25` | 0.0060 [0.0000, 0.0140] | 0.0080 [0.0020, 0.0163] | 0.0080 [0.0020, 0.0163] | 0.0064 [0.0004, 0.0144] |
| `garhwali_character_bm25` | 0.0080 [0.0020, 0.0163] | 0.0100 [0.0020, 0.0199] | 0.0100 [0.0020, 0.0199] | 0.0087 [0.0020, 0.0173] |
| `oracle_english_word_bm25` | 0.5760 [0.5299, 0.6206] | 0.8100 [0.7758, 0.8433] | 0.8520 [0.8206, 0.8834] | 0.6772 [0.6404, 0.7127] |

Paired character-minus-word Garhwali BM25 deltas:

| Metric | Difference | 95% clustered interval |
| --- | ---: | ---: |
| recall_at_1 | 0.0020 | [0.0000, 0.0061] |
| recall_at_5 | 0.0020 | [0.0000, 0.0061] |
| recall_at_10 | 0.0020 | [0.0000, 0.0061] |
| mrr_at_10 | 0.0023 | [0.0000, 0.0063] |

The candidate corpus is fixed and contains documents derived from train, dev, and test, so these intervals are conditional on that all-split retrieval corpus. They estimate query uncertainty within the existing dev set; they do not demonstrate generalization to unseen Wikipedia pages. The English-query result is only an upper-bound diagnostic. References remain unreviewed.

Benchmark SHA-256: `e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6`
Predictions SHA-256: `3f7df640f9a27f4fc565a9f890eb87c20d14061f59e682bc818704bfb5eccd29`
Parent report SHA-256: `dafb5582955de71b69cc0686104d3689eb976cc7c304d7a34c30b0128ac66fbf`
