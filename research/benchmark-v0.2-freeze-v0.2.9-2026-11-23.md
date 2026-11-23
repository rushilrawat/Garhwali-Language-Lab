# GarhwaliBench v0.2 frozen on corpus v0.2.9 — 23 November 2026

**Status:** local draft, frozen and verified. Not cleared for public upload
(`public_upload_allowed=false`, `status=draft_local_only_not_release_ready`).

## What was frozen

The v0.2 export was rebuilt with its text views on the corpus v0.2.9 segment
splits and pinned with `scripts/freeze_benchmark.py`.

- Freeze file: [`release/garhwali_bench_v0.2-v0.2.9_freeze.json`](../release/garhwali_bench_v0.2-v0.2.9_freeze.json)
- Combined SHA-256: `2ed10b18e0c39569973f0474b6d58541fd464bfbb8857dfdb77228fb4d805b6d`
- 9 files, 1,990,970,931 bytes, frozen 2026-11-23T19:08:25Z; `verify` passes.
- The September pin, `release/garhwali_bench_v0.2-draft_snapshot.json`, is unchanged.

| View | Records | Splits |
| --- | ---: | --- |
| external/crosssum | 699 | dev 100 / test 500 / train 99 |
| external/flores | 2,009 | dev 997 / test 1,012 |
| external/xorqa | 1,139 | dev 500 / test 539 / train 100 |
| internal/asr | 110 | test |
| internal/text | 813 | test |
| text_recommended/train | 182,611 | train |
| text_recommended/validation | 10,145 | validation |
| text_recommended/test | 10,145 | test |
| **Total** | **207,671** | |

## Why the text views come from `splits/text/`

On v0.2.9 the rights-filtered `splits/text_recommended/` view is empty in every
split. Every source is `training_eligible: false` (the October Meta CC BY 4.0
decision covers only the screened Meta views), and the filter keeps train rows
only. Rebuilding on it would have frozen empty text views.

The owner chose (2026-11-23) to freeze on the full v0.2.9 splits in
`data/processed/model_ready/splits/text/` (182,611 / 10,145 / 10,145; SHA-256
prefixes `7dd0b871`, `be4088fe`, `99635059`). These are the same 90/5/5 splits
published in corpus v0.2.9 on Hugging Face. They are **not training-cleared**:

- the benchmark manifest records `text_views.rights = not_training_cleared`;
- the export manifest records `text_view_source = data/processed/model_ready/splits/text`
  and `text_view_rights = not_training_cleared`;
- full-split rows get `example_id = text_split:<segment_sha256>`, per-component
  rights, and usage labels `not_training_eligible` (train), `dev_select`
  (validation) and `open_test_historical` (test, after today's single scoring).

The view names stay `text_recommended/*` for schema stability. If sources are
cleared for training later, rebuild with
`build_garhwali_benchmark.py --text-splits-dir data/processed/model_ready/splits/text_recommended`.

## Integrity checks

- Contract validation: pass, 0 errors, 8 assets. Export self-validation: pass.
- Internal text vs train: 0. ASR speakers vs train: 0. External text exactly in train: 0.
- XORQA dev/train repeats unchanged at 1 group (2 rows).
- All 813 internal/text rows come from the v0.2.9 test split, so internal/text
  is a subset of `text_recommended/test`. Neither overlaps train or validation.
- The manifest's bigram sanity baseline on internal text is perplexity 17.666
  (OOV 0, vocabulary 411); on the empty view it had been 2.0 with OOV 1.0.

## Baselines rerun

All CPU-only, on Rush's Mac, with no paid jobs. Masked LM, NLLB, dense
retrieval and ASR were not rerun because they need model downloads or a GPU.

### Character n-gram LM (`run_text_scaling_experiment.py`)

Train/validation/test from v0.2.9 `splits/text/`; 6 fractions × seeds 17/29/43
× orders 2/3 (3 min 10 s). Train–validation and train–test overlap 0; no test
rows used in selection.

- Selected: order 3, fraction 1.0. Validation perplexity **10.840** (cross-entropy 2.3832).
- Frozen v0.2.9 test (10,145 rows, 1,088,937 characters, OOV 3.7e-6): perplexity
  **11.242** (cross-entropy 2.4197). Scored once; this test split is now
  `open_test_historical` for selection purposes.

| Train fraction (rows) | Order 2 val PPL | Order 3 val PPL |
| --- | ---: | ---: |
| 0.01 (1,827) | 18.890 ± 0.075 | 21.980 ± 0.108 |
| 0.05 (9,131) | 17.428 ± 0.044 | 14.623 ± 0.223 |
| 0.10 (18,262) | 17.208 ± 0.013 | 13.242 ± 0.033 |
| 0.25 (45,653) | 17.014 ± 0.011 | 11.898 ± 0.053 |
| 0.50 (91,306) | 16.934 ± 0.006 | 11.257 ± 0.030 |
| 1.00 (182,611) | 16.888 | **10.840** |

Earlier runs used other data and test sets, so they are context, not a trend:

| Run | Train rows | Test set (rows) | Val PPL | Test PPL |
| --- | ---: | --- | ---: | ---: |
| 2026-09-11 | 80,926 | older split test (2,492) | 11.713 | 11.894 |
| 2026-09-22 broad | 106,915 | internal_text (398) | 12.336 | 12.196 |
| 2026-09-22 recommended | 7,490 | internal_text (398) | 10.249 | 10.210 |
| **2026-11-23 (v0.2.9)** | **182,611** | **v0.2.9 test (10,145)** | **10.840** | **11.242** |

### BM25 retrieval, XORQA dev (500 queries)

Same input as 2026-09-11; differences come from the current script's ranking
and accounting, not data.

| Baseline | R@1 | R@5 | R@10 | MRR@10 |
| --- | --- | --- | --- | --- |
| Character BM25 | 0.008 → 0.008 | 0.016 → 0.010 | 0.020 → 0.010 | 0.0114 → 0.0087 |
| Word BM25 | 0.006 → 0.006 | 0.008 → 0.008 | 0.014 → 0.008 | 0.0071 → 0.0064 |
| Oracle English BM25 | 0.576 | 0.810 | 0.852 | 0.6772 |

Garhwali-side BM25 finds no relevant passage for 493/500 (character) and
496/500 (word) queries.

### Translation, FLORES gbm→en dev (997 rows)

Run without `--allow-historical-test`. The current script normalizes text and
excludes the exact source from the translation memory.

| Baseline | BLEU (custom) | chrF2 (custom) | Exact match |
| --- | --- | --- | --- |
| Copy source | 0.00043 → 0.00100 | 0.0075 → 0.0081 | 0 → 0 |
| Dev translation memory | 0.0082 → 0.0199 | 0.2159 → 0.2381 | 0 → 0 |

## Tests

`python -m unittest` on the Mac: 971 run, 967 pass; the 4 errors are
`test_ingestion_graph` needing the optional `langgraph` package.

## Local artifacts (gitignored)

- Export: `data/processed/evaluation/garhwali_bench/v0.2-draft/` (1.9 GB).
- LM: `data/processed/evaluation/controlled_modeling/text_scaling_v0.2.9.json`.
- Retrieval / translation: `data/processed/evaluation/{retrieval,translation}/v0.2.9-2026-11-23/`.
- Backup of the pre-freeze benchmark and splits: `.claude-backup-2026-11-23/`.
