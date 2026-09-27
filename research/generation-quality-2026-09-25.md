# mT0 generation quality refresh

**Checked:** 2026-09-25

**Result:** all three 32,768-step validation runs and diagnostics are complete; no adapter is promoted for generation
**Test status:** an 86-row test was evaluated once after validation selection and is now historical

## Reconciled run status

The 2026-09-16 partial-run note describes the first continuation job, which was
canceled with seed 43 incomplete. Local synced artifacts show a later, separate
seed-43 run completed all 32,768 steps. A later validation-analysis job then
generated and scored all three adapters on the same 130-row validation split.
The older partial report is still accurate about its canceled job; it is not
the current status of the experiment. See the [initial-run addendum](mt0-32768-partial-2026-09-16.md)
and the [corpus status record](corpus-preparation-status.md).

All validation predictions were independently rescored from the saved JSONL
with the repository's current exact-match and chrF2 functions. The recomputed
scores match the saved reports exactly. The common validation-manifest SHA-256
is `8e6d9667f80d659eedb518b58be721340161c159c5587243f9ba0616cd7cea44`; the
pinned base model is `bigscience/mt0-small` revision
`8116a34237e19160ec003147e758f065876d95f0`.

## Validation results

| System | Validation CE | Exact match | chrF2 | Mean adjacent repetition rate | Empty / copied / control-token outputs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Zero-shot base mT0-small | 5.780505 | 0.00% | **0.088327** | 0.072949 | 0 / 0 / 0 |
| 32,768-step LoRA seed 17 | 4.266280 | 1.54% | 0.064689 | 0.035257 | 0 / 0 / 0 |
| 32,768-step LoRA seed 29 | 4.219282 | 1.54% | **0.074003** | **0.025000** | 0 / 0 / 0 |
| 32,768-step LoRA seed 43 | **4.188287** | 1.54% | 0.070873 | 0.036026 | 0 / 0 / 0 |

Each system covers the same 130 validation rows across six tasks. Seed 43 has
the lowest teacher-forced validation loss, so it was selected for the later
one-time test comparison. Seed 29 has the best chrF2 among adapters. Every
adapter's chrF2 is below the zero-shot base, and each reaches exact match on
only 2 of 130 rows; exact matches are confined to the two Garhwali/Hindi
lexicon tasks. The loss improvement therefore did not translate into better
aggregate generated text under chrF2. No adapter is promoted as a generation
improvement.

The saved per-task analysis reports 20 rows each for English-to-Garhwali and
Garhwali-to-English, 29 each for the English/Garhwali lexicon tasks, and 16 each
for Garhwali/Hindi lexicon tasks. Every adapter has zero empty outputs, literal
instruction copies, and remaining mT5 control tokens. Repetition rates and
automated lexical scores are diagnostics, not judgments of grammaticality or
Garhwali correctness; no native review was performed.

## Test use and eligibility

The 32,768-step validation report itself records `fixed_test_opened: false`.
After seed 43 was selected using validation cross-entropy, a separate run
reported evaluating it once against an 86-row test. The existing corpus status
records 4.358291 test cross-entropy, 2.33% exact match, and 0.062177 chrF2,
compared with base chrF2 0.085840. That test was not used for selection, but it
has now been scored and is historical; do not rerun it or use it to select a
new checkpoint.

There is an unresolved provenance gap: the run report's test-manifest digest
is `7fb06f4e3b968a6f1bda453a134c217986a2c390f93429c42d5e36528d7aae0e`, but it
does not match either current local instruction test manifest. The local
`instructions/test.jsonl` has 118 rows and canonical instruction digest
`ad94c18f158a2cfd72563b713c5e1b9a6aacefd5329a568f6117d634bfb30289`; the
`instructions_v0.2/test.jsonl` has 260 rows and digest
`a64b1782eb931359cfc31d7fe8e4d4648131d6a68c03ba54ab95eaa5340ba292`. The
lineage audit consequently lists the 172 selected-test prediction rows (86
examples times base/adapter) as unmatched. The test score is inherited from the
existing report, not independently recomputed here; exact test-row identity and
reference lineage remain unresolved. This refresh did not inspect or rescore the
selected-test prediction payload or references; it compared aggregate row counts
and stable instruction-hash manifests against the saved digest. Do not describe
these values as independent generalization evidence. References also remain
unreviewed by a Garhwali speaker.

## Provenance and outputs

- Three-seed validation predictions: 390 rows; SHA-256
  `ddfe215bf5d8607216aad2a8c4b2866a6ff01818ed8715aab80edd14ffc0652f`.
- Seed-43 run validation predictions (base plus seed 43): 260 rows; SHA-256
  `49f90c85c388fa61364cd42965e7b785b2f06bcfa3b33a2167f4fe59fed651b8`.
- Three-seed analysis report SHA-256:
  `00aef2f58c58be8c8edfc0f9a04f499e4a05abb3d40195d4d51c638e4f8f7401`.
- Seed-43 run report SHA-256:
  `6423a57941965228002cb5db104392ff16116c19b707c541399c2e187a15091a`.
- The lineage audit maps all 390 three-seed prediction rows and all 260 seed-43
  run validation rows to the frozen validation manifest with zero cross-split
  matches.

Generated predictions and adapter weights remain under ignored
`data/processed/evaluation/controlled_modeling/` paths. This refresh reads
those existing local outputs only; it starts no cloud job, downloads no model,
and does not open the saved test predictions.
