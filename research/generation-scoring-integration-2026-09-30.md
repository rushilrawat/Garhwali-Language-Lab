# Generation scoring integration and saved-prediction reconciliation

- **Date:** 2026-09-30
- **Status:** shared validation scorer implemented; historical predictions reconciled
- **Claim level:** development diagnostics only

## What changed

`scripts/score_benchmark_predictions.py` now accepts `--task generation` for
the saved `instructions_v0.2` mT0 validation outputs. It creates stable IDs as
`instruction:<instruction_sha256>`, scores exact match against any accepted
reference and multi-reference chrF2, and reports empty outputs, instruction
copying, control-token leakage, and adjacent repetition. Reports carry an
explicit validation-only claim limit and hashes for the inputs and scoring
code. Generation rows have no original benchmark `source_split`; the scorer
therefore reports an empty source-split breakdown instead of inventing one.

## Prediction/source reconciliation

The current validation manifest contains 320 rows. The three historical saved
seed runs contain the same 130 stable IDs. All selected IDs match the current
source records on task label, primary reference, and accepted-reference list.
The other 190 current validation rows have no saved predictions and were not
scored. The reconstructed 130-row subset has SHA-256
`9e547c1efe9574d6433a0182cf6b26cd0381fe8f6b716393091da5ed6a137b4d`; the full
current validation manifest has SHA-256
`f2416fccd273871b18356110e89153835977c480d7082eca6a7e998047a12812`.

| Saved seed | Rows | Multi-reference chrF2 | Exact match | Empty / copied / control-token outputs | Mean adjacent repetition |
| --- | ---: | ---: | ---: | ---: | ---: |
| 17 | 130 | 0.06662183 | 0.01538462 | 0 / 0 / 0 | 0.03525641 |
| 29 | 130 | 0.07638596 | 0.01538462 | 0 / 0 / 0 | 0.02500000 |
| 43 | 130 | 0.07336194 | 0.01538462 | 0 / 0 / 0 | 0.03602564 |

Seed 29 has the highest recorded multi-reference chrF2 on this matched
development subset. This is descriptive only; it does not establish a
statistically reliable winner or improved Garhwali quality.

## Limits and next use

These are rescored historical predictions, not fresh inference. The validation
examples have already been used during model development; reference variants
have not received native-speaker review; the original per-seed checkpoint
hashes and source-cluster confidence intervals are unavailable. This result
does not make generation eligible for an independent final-accuracy claim.
That eligibility remains 0/5 across language modeling, translation,
retrieval, generation, and ASR. Owner approval authorizes work toward all five
areas; it does not change evidence status.

The locally generated predictions and manifests remain under the ignored
`data/processed/evaluation/` tree. Reconciliation uses
`scripts/manifest_saved_generation_validation.py` to build
`data/processed/evaluation/generation/mt0_32768_validation_reconciled_2026-09-30/benchmark-validation-subset.jsonl`
and one `seed-{17,29,43}/predictions.jsonl` file per seed. Scoring uses
`scripts/score_benchmark_predictions.py` with `--task generation`,
`--split validation`, that subset as `--benchmark`, the seed predictions as
`--predictions`, `hypothesis` as `--prediction-field`, and the corresponding
`data/processed/evaluation/benchmark_scoring/generation_shared_20260930/seed-{17,29,43}`
as `--output-dir`. `--model-id` and `--model-revision` describe the saved
prediction source; the checkpoint hash was not recorded and the scorer loads
no model. The full pytest suite passed 624 tests and unittest passed 622 tests on
2026-09-30. These checks validate code and record integrity, not linguistic
correctness or independence.
