# Garhwali-to-English translation baseline: development-only refresh

**Run date:** 2026-09-26

**Roadmap phase:** 5 — reproduce and consolidate baselines

**Evaluation status:** development-only; no new test scores
**Model execution:** local; no downloads, paid jobs, or Hugging Face changes

## Scope and split integrity

The frozen IndicGenBench FLORES file contains 2,009 Garhwali-to-English rows:
997 `dev` and 1,012 `test`. This run scored all 997 development records in
stable `record_id` order. The FLORES test already has saved predictions and is
historical; this run did not score it. The copy and translation-memory
diagnostics are not independent final-accuracy measurements.

| Artifact | SHA-256 |
| --- | --- |
| Input file, including both published splits | `7c96d63be5f43e6a65fc229238c6d295d983fe46be032e9f8418d32150225097` |
| Canonical selected development rows | `d3bf6084025d78bd2eede315965ee2cb981be2d3a1b59d7952e7c1deb7b5e0d5` |
| Translation runner | `7ff279cfee49372017ff27b28c575d90b28447f97ddd0d1523ee63eaac83550d` |

The prediction manifest records all 997 selected IDs from
`indicgenbench_flores:dev:0` through `indicgenbench_flores:dev:996` (lexical
record-ID ordering). Machine-readable predictions and report are saved under
the Git-ignored path `data/processed/evaluation/translation/accuracy_dev/`.
The run used Python `3.12.5` and the default full-split cap (`max_records=null`).

## Results

Scores use the project's dependency-free custom metrics: add-one-smoothed
corpus BLEU, character orders 1–6 with beta 2, and NFC/case-fold/whitespace
normalization. These values are not SacreBLEU scores.

| Development diagnostic | Records | Smoothed BLEU | chrF2 | Exact match | Empty hypotheses |
| --- | ---: | ---: | ---: | ---: | ---: |
| Copy Garhwali source | 997 | 0.00099523 | 0.00806000 | 0.00000000 | 0 |
| Development translation memory | 997 | 0.01992188 | 0.23808697 | 0.00000000 | 0 |

The translation-memory diagnostic uses the development rows as a searchable
memory but excludes every candidate whose normalized source exactly matches
the query. This prevents a record from retrieving itself, and the current
development split has **zero exact normalized-source duplicate groups**. It is
still a nearest-neighbor diagnostic evaluated within the development split;
near-duplicate or semantically related sources may remain, so interpret the
score as exploratory rather than a generalization estimate. Its mean source
similarity is `0.15458843`; no query had zero similarity.

## NLLB preflight

The NLLB dev run was not started. The active `.venv` has no `torch`,
`transformers`, or `peft`; an optional cached runtime exposes `torch` and
`transformers` only when `PYTHONPATH=.cache/asr-runtime` is set, and still has
no `peft`. The pinned NLLB base snapshot is not cached. A small community
adapter directory exists, but it cannot run without the base checkpoint and
adapter runtime. No packages or model weights were installed or downloaded.
The script now defaults to `dev` and writes under
`accuracy_dev/`; any future NLLB metric remains a Hindi-source-token proxy
(`hin_Deva`), not evidence of native Garhwali-token support.

## Reproduction and interpretation

Run the dependency-free baseline with:

```bash
python3 scripts/run_translation_baseline.py --split dev
```

The NLLB runner accepts the same `--split dev` argument when its pinned local
runtime and weights are available. Its `--max-records` selection is sorted by
record ID; zero means the complete requested split. Test results remain
historical and must not be used for selection or represented as blind
evaluation.

The results show that literal copying is ineffective on this benchmark and
that a simple character-overlap memory diagnostic improves chrF2, but neither
result establishes useful Garhwali translation quality. References are not
native-adjudicated, external model training exposure is unknown, and there is
no untouched independent Garhwali-to-English test set. No model is promoted.
