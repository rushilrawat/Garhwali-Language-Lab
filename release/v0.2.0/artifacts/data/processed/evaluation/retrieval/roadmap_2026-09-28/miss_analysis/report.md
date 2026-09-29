# XORQA BM25 dev retrieval miss analysis — 2026-09-28

This analysis checks whether each saved dev query’s gold passage exists in the fixed candidate corpus, then separates no lexical score from poor rank placement. It reads saved predictions only and does not copy query, answer, title, or passage text.

- Dev queries: 500
- Candidate passages: 1059
- Gold context available: 500/500
- Unique dev gold contexts: 479
- Unique gold contexts also sourced from multiple splits: 24

| Retriever | Rank 1 | Rank 2–5 | Rank 6–10 | Rank >10 | Zero score | Misses at 10 | Same-page alternatives among misses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `garhwali_word_bm25` | 3 | 1 | 0 | 0 | 496 | 496 | 1 |
| `garhwali_character_bm25` | 4 | 1 | 0 | 2 | 493 | 495 | 0 |
| `oracle_english_word_bm25` | 288 | 117 | 21 | 73 | 1 | 74 | 6 |

## Gold-passage lexical overlap by outcome

Mean shared analyzer units and mean query-unit coverage are computed between each query and its own gold context. Zero-score rows should have no shared unit for the corresponding saved BM25 analyzer; rank >10 rows do share terms but miss the top-10 cutoff.

| Retriever | Outcome | Queries | Mean shared units | Mean query-unit coverage | Same-page alternatives in top 10 |
| --- | --- | ---: | ---: | ---: | ---: |
| `garhwali_word_bm25` | rank_1 | 3 | 3.667 | 0.363 | 0 |
| `garhwali_word_bm25` | rank_2_5 | 1 | 1.000 | 0.071 | 0 |
| `garhwali_word_bm25` | zero_score | 496 | 0.000 | 0.000 | 1 |
| `garhwali_character_bm25` | rank_1 | 4 | 15.000 | 0.161 | 0 |
| `garhwali_character_bm25` | rank_2_5 | 1 | 3.000 | 0.020 | 0 |
| `garhwali_character_bm25` | rank_11_plus | 2 | 1.000 | 0.006 | 0 |
| `garhwali_character_bm25` | zero_score | 493 | 0.000 | 0.000 | 0 |
| `oracle_english_word_bm25` | rank_1 | 288 | 5.660 | 0.643 | 16 |
| `oracle_english_word_bm25` | rank_2_5 | 117 | 5.103 | 0.568 | 19 |
| `oracle_english_word_bm25` | rank_6_10 | 21 | 4.619 | 0.505 | 3 |
| `oracle_english_word_bm25` | rank_11_plus | 73 | 3.301 | 0.381 | 6 |
| `oracle_english_word_bm25` | zero_score | 1 | 0.000 | 0.000 | 0 |

All dev gold contexts are available in the fixed candidate set, so the measured misses arise from lexical matching or rank placement in this setup, not missing gold passages. The corpus includes contexts from every original split; these results are not a page-held-out evaluation. Same-page alternatives are lineage signals, not proof of supporting evidence.

Benchmark SHA-256: `e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6`
Predictions SHA-256: `3f7df640f9a27f4fc565a9f890eb87c20d14061f59e682bc818704bfb5eccd29`
Parent retrieval report SHA-256: `dafb5582955de71b69cc0686104d3689eb976cc7c304d7a34c30b0128ac66fbf`
