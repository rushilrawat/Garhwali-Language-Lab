# Existing-corpus expansion audit — 2026-10-02

## Result

The published v0.2.3 release adds a purpose-built `text_resources` view to the
published v0.2.2 corpus. This is an additive *access view* over records already
in the local corpus, not new source acquisition. It contributes **246
normalized-unique Garhwali records** (183,484 characters; 40,759
whitespace-delimited words) beyond the existing public text-bearing configs.
No source rows, previous release files, or corpus records were deleted.

The published package has **827,450 package-view rows**: 164,387 content/config rows
and 663,063 reference/join rows. These are overlapping package counts, not
unique examples. Relative to v0.2.2, the package adds 246 content-view rows;
the remaining count change comes from indexing the added view in the
reference/join tables. The source corpus itself has no new text records from
this work.

## Selection and quality

The selection began with 11,108 catalog rows that have a Garhwali-only `gbm`
source-language label, a Garhwali-candidate label, and a recorded
redistribution basis. The builder removed 6,096 rows already present by
identity in another text-bearing view, 647 rows whose source records occur in
held-out evaluation data, and 4,119 normalized-text matches across existing
text, lexicon, provider ASR, machine drafts, instruction/response, and
`text_expansion` views. The remaining 246 records have unique normalized text
within the new view.

| Field | Published result |
| --- | ---: |
| Additional normalized-unique records | 246 |
| Whitespace-delimited words | 40,759 |
| Characters | 183,484 |
| Devanagari / Latin script labels | 243 / 3 |
| CC BY 4.0 rows | 118 |
| CC BY-NC-SA 4.0 rows | 128 |
| `experimental_review` quality tier | 118 |
| `high_quality_rights_pending` quality tier | 128 |
| Recommended for training / evaluation | 0 / 0 |

The `high_quality_rights_pending` quality tier means no compatible training
basis was recorded by the quality pipeline; it does not override the row's
separately resolved noncommercial redistribution status. The 128 affected
records retain `rights_cleared_noncommercial_sharealike`,
`noncommercial_only`, and the CC BY-NC-SA attribution/share-alike terms. None
of the 246 is promoted into a supervised training or benchmark evaluation
view. Quality fields are machine-assessed and remain unreviewed by native
speakers.

The 246 records trace to the existing `hindialect_gbm` (128),
`indic_dialect_asr_gbm` (115), `upreti_1894_garhwali` (2), and
`lsi_1916_grierson_garhwali_table` (1) source families. Those sources were
already in the corpus; this release does not add new copies of their source
material.

## Rights and completeness

The existing public catalog still has 32,072 identities: 12,258 rows under
open-license or work-specific compatible bases, 134 under CC BY-NC-SA 4.0,
198 under narrow source reproduction policies, 16 fact-only single-word
projections, and 19,466 full text values whose current record does not support
public text redistribution. The 246-row view draws only from the first two
categories and preserves per-row terms. Source-policy glossary values and
fact-only tokens are not copied into this text view.

The catalog and reference tables remain available for discovery and
provenance. The 19,466 pending text values are not included in this new view.
Their references remain documented; public accessibility of a source alone
does not supply a redistribution license. The 216 structured knowledge
records remain publicly represented as factual/bibliographic metadata.

## Validation and release state

- Builder output is additive and versioned as `garhwali-language-lab-v0.2.3`.
- The full public-package preflight passed with zero errors, zero rows missing
  their configuration-specific source locator, and zero deleted or mutated
  records. The exact per-config results and file hashes are in
  [`huggingface-quality-candidate-preflight-2026-10-02.json`](huggingface-quality-candidate-preflight-2026-10-02.json).
- `text_resources/train` contains 246 non-empty rows, all with a rights basis,
  a non-empty quality status, source traceability, and explicit
  `recommended_for_training=false` and `recommended_for_evaluation=false`.
- The separate audio dataset is unchanged; no audio payload was added to this
  corpus release.
- Published additively at [Hub commit `76dac8d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76dac8de70d37595c7af9a3c642c81ece615ec5d). The public repo head reports `private=false`; the v0.2.3 release tree contains 47 versioned files plus the root card.
- A fresh `datasets.load_dataset(..., "text_resources", split="train", streaming=True)` read returned all 246 rows with the expected rights-status split: 118 `rights_cleared`, 128 `rights_cleared_noncommercial_sharealike`.
- Hugging Face Dataset Viewer Parquet returned HTTP 500 twice with a “server is busier than usual” response. The direct dataset stream works; Viewer/Parquet preview remains unverified pending service recovery.

## Next steps

1. Retry Dataset Viewer/Parquet validation after the Hub service recovers.
2. Begin the next Phase 6 source intake using the existing rights, dedup, and
   provenance pipeline; report genuinely new source rows separately from
   re-exposed views.
