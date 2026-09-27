# Garhwali-to-English translation baseline

Generated on 2026-09-11 from the frozen IndicGenBench FLORES asset in
`benchmarks/indicgenbench_flores.jsonl`. This is an experimental model audit;
the original benchmark records, model revisions, predictions, and metric
settings remain identifiable.

**Status note (2026-09-26):** The results below are historical test results;
FLORES test rows have already been scored. The runners now default to `dev`
and save to split-specific directories. Do not rerun the old test experiment
for model selection. The latest dev-only refresh is documented in
[`translation-quality-2026-09-26.md`](translation-quality-2026-09-26.md).

## Evaluation data

The benchmark contains **2,009** Garhwali-to-English pairs: **997 development**
and **1,012 test**. The development split is available to the translation-memory
floor; every score uses test references only.

## Results

| System | Test rows | Smoothed BLEU | chrF2 | Exact match |
| --- | ---: | ---: | ---: | ---: |
| Copy Garhwali source | 1,012 | 0.000434 | 0.007460 | 0.000000 |
| Development translation memory | 1,012 | 0.008208 | 0.215886 | 0.000000 |
| NLLB-200 distilled, Hindi source-token proxy | 32 | **0.219719** | **0.574134** | 0.000000 |
| `Gaurav17/garhwali-nllb-v12` adapter, same proxy | 32 | 0.095460 | 0.460474 | 0.000000 |

BLEU is a dependency-free corpus implementation with add-one smoothing. chrF2
uses character orders 1–6 and beta 2. Values are reported on a 0–1 scale. The
32-row NLLB numbers are a fixed pilot and must not be compared as though they
cover the full 1,012-row test split.

## Model decision

The current pilot is the pinned `facebook/nllb-200-distilled-600M` base model at
revision `f8d333a098d19b4fd9a8b18f94170487ad3f821d`. NLLB publishes no Garhwali
language token, so the runner explicitly uses `hin_Deva` for the source and
`eng_Latn` for the target. This measures a practical transfer baseline, not a
native Garhwali model configuration.

The community LoRA adapter is retained as an experimental comparison at revision
`c17ad35a9fc522aae5da231adb5a0ecf1258e4a3`. It underperforms the base on the
same records, and its model card does not document its training corpus, metrics,
license, or Garhwali language-token mapping. Those omissions prevent a defensible
claim about what the adapter learned.

## Reproduction

The original predictions and reports are preserved in the local ignored
evaluation directory. To reproduce the current development-only copy and
translation-memory baseline, run:

```bash
python3 scripts/run_translation_baseline.py --split dev
```

The NLLB historical test pilot is not rerun here; its pinned model/adapter
revisions and prior aggregate values are retained above.

Model weights, adapter files, predictions, and generated reports remain ignored
by Git. The tracked release manifest copies the resulting aggregate metrics.
