# mT0 validation run manifest audit — 2026-09-27

## Result

The three saved 32,768-step mT0 generation runs now have hash-linked local
manifests. This is a post-hoc packaging and lineage check only: it ran no
model inference and scored no test rows.

The 390 saved prediction rows split into three systems with 130 rows each.
Every `instruction_sha256` joins to a validation example in
`data/processed/model_ready/instructions_v0.2/validation.jsonl`; task and
reference values also match exactly. The same 130 IDs are present for all
three seeds. Their ordered selection hash is
`8e6d9667f80d659eedb518b58be721340161c159c5587243f9ba0616cd7cea44`, equal to
the validation hash recorded in the seed-43 training report. The fixed test
was not opened in the source generation-analysis report.

| Seed | Validation cross-entropy | chrF2 | Exact match | Mean adjacent repetition | Manifest SHA-256 |
| --- | ---: | ---: | ---: | ---: | --- |
| 17 | 4.26628047 | 0.06468880 | 0.01538462 | 0.03525641 | `2276bbfd94cd9b5424b6d95589042cb20a1744dbcd9411a1b9f25c3c3ccfd507` |
| 29 | 4.21928229 | 0.07400284 | 0.01538462 | 0.02500000 | `596f9921b9417eea049ca85f7ac03f2aeb9a6bbf943ce47ff36890f2aba1e4cd` |
| 43 | 4.18828743 | 0.07087263 | 0.01538462 | 0.03602564 | `0ba7c36c279e1c67ecd60bf35a5c015bd9bc354a79a4cea4baa82617fe97c0e7` |

Seed 43 has the lowest validation loss; seed 29 has the highest generation
chrF2. This confirms that teacher-forced validation loss did not select the
best saved generation metric. None of these aggregate metrics certifies
Garhwali correctness; the references are not native-adjudicated.

The saved aggregate metrics reproduce exactly under the stored **primary
reference** for each prediction. The saved prediction rows do not contain the
alternate-reference arrays now present in the validation file. Re-scoring with
those current, unreviewed alternatives yields this chrF2 sensitivity:

| Seed | Primary-reference chrF2 | Current candidate multi-reference chrF2 | Difference |
| --- | ---: | ---: | ---: |
| 17 | 0.06468880 | 0.06662183 | +0.00193303 |
| 29 | 0.07400284 | 0.07638596 | +0.00238312 |
| 43 | 0.07087263 | 0.07336194 | +0.00248931 |

Exact match is unchanged at `0.01538462` for all three seeds. The higher
multi-reference values are a sensitivity result, not evidence of better model
quality: the alternate answers are not native-adjudicated. The manifests retain
both metric views and verify the primary-reference reproduction against the
saved report.

## Hashes and limits

- Validation input file SHA-256:
  `71c86477f8acc56d11b9bf1f9da421cbb244bc241a0910b30bb3cdee87ca856b`
- Combined saved prediction file SHA-256:
  `ddfe215bf5d8607216aad2a8c4b2866a6ff01818ed8715aab80edd14ffc0652f`
- Source generation-analysis report SHA-256:
  `00aef2f58c58be8c8edfc0f9a04f499e4a05abb3d40195d4d51c638e4f8f7401`
- Recomputed primary-reference diagnostics, including per-task slices and
  row-level failure flags, match the saved report for each seed. All saved
  per-row diagnostic flags also match recomputation.
- Output predictions/report hashes for each seed are recorded in that seed's
  ignored `run_manifest.json`.
- The synced generation-analysis artifact does not retain the original
  selection seed/parameters or per-seed checkpoint hashes. The source IDs,
  references, task labels, full validation-file hash, combined predictions
  hash, and selected-ID hash are verified; original sampling parameters and
  exact adapter bytes cannot be recovered from these artifacts.
- All manifests and per-row outputs are local under
  `data/processed/evaluation/generation/mt0_32768_validation_manifested_2026-09-27/`
  and remain Git-ignored.

## Reproduction

```bash
PYTHONPATH=scripts python scripts/manifest_saved_generation_validation.py
PYTHONPATH=scripts pytest -q tests/test_manifest_saved_generation_validation.py
```

The script rejects non-validation input, mismatched tasks or references,
unknown/duplicate prediction IDs, unequal seed record sets, and report/count
mismatches before writing any run artifacts.
