# XORQA BM25 retrieval miss analysis — 2026-09-28

This post-hoc diagnostic explains misses in the saved 500-query XORQA development retrieval run. It verified the benchmark, prediction IDs, parent report, and fixed candidate-passage corpus before analyzing ranks. It checked each top-10 list against the saved gold rank and score, then reproduced Recall@1/5/10 and MRR@10 against the parent report. It copied no query, answer, title, or passage text into its outputs.

## Result

All **500/500 dev gold passages are present** in the candidate set. There are 479 unique dev gold contexts. The fixed index contains 1,059 unique passages built from 1,139 benchmark source rows; 65 passage groups have multiple source rows. Among the 479 gold contexts, 39 have duplicate source rows and 24 have source rows in more than one split.

| Retriever | Rank 1 | Rank 2–5 | Rank 6–10 | Rank >10 | Zero score | Recall@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Garhwali word BM25 | 3 | 1 | 0 | 0 | 496 | 0.8% |
| Garhwali character BM25 | 4 | 1 | 0 | 2 | 493 | 1.0% |
| English-oracle word BM25 | 288 | 117 | 21 | 73 | 1 | 85.2% |

Here, **zero score** means the saved BM25 analyzer shared no token or character n-gram with the gold passage. **Rank >10** means the passage had a positive lexical score but fell below the top-10 cutoff. The Garhwali word baseline has 496 zero-score misses. The character baseline has 493 zero-score misses and two additional passages ranked below 10. The English-oracle run is a diagnostic ceiling for this setup, not a Garhwali model score.

## Interpretation and limits

The observed Garhwali-query misses are not caused by absent gold documents in this candidate corpus. They mostly reflect the lexical mismatch between Garhwali queries and the English passages; the diagnostic does not test semantic retrieval or establish that a same-page passage answers a query. The small character-over-word difference remains inconclusive under the already-computed source-page-cluster bootstrap: +0.2 percentage points Recall@10, 95% interval 0.0–0.6.

The candidate corpus contains contexts from train, dev, and test. This is conditional analysis of saved dev predictions, not unseen-page generalization. No test predictions, new inference, model selection, or benchmark edits were performed. No source rows were removed. Native-language review remains deferred, and these automated retrieval metrics do not establish Garhwali correctness.

## Reproducibility

Run from the repository root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_retrieval_misses.py
```

The command writes local-only JSON/Markdown diagnostics under the ignored path `data/processed/evaluation/retrieval/roadmap_2026-09-28/miss_analysis/`. The JSON contains row IDs and hashes only.

| Input | SHA-256 |
| --- | --- |
| Benchmark JSONL | `e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6` |
| Saved dev predictions | `3f7df640f9a27f4fc565a9f890eb87c20d14061f59e682bc818704bfb5eccd29` |
| Parent retrieval report | `dafb5582955de71b69cc0686104d3689eb976cc7c304d7a34c30b0128ac66fbf` |
| Canonical candidate passage corpus | `9618e40f63f8e2744e8394b0d480f258a4730847b8399da7e644b45d27e7d9c0` |

## Follow-up

The retrieval miss inventory is complete for these saved predictions. Remaining Phase 7 work includes source-family uncertainty for other tasks where lineage supports it, generation-output diagnostics, and reconciling task-specific result eligibility. Dense retrieval remains a separate model experiment and requires the pinned local checkpoint/runtime preflight to pass.
