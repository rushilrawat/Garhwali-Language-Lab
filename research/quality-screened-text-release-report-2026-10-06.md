# Quality-screened Garhwali text release report

**Prepared:** 6 October 2026
**Source package:** Hugging Face corpus v0.2.7 staging
**Local candidate:** `garhwali-screened-text-v0.1` / additive corpus paths under v0.2.8
**Publication status:** Hugging Face v0.2.8 update published and online-loaded; Kaggle upload is pending.

Pinned source manifest SHA-256: `642e492418a0b0ec4bbdf62faed286da381c1bb16995cdb9ac22914a1b956ef0`.

## What this release is

A focused, small download for experimental Garhwali text training and language
tooling. The source material is transcript text from the Meta Omnilingual ASR
Corpus. It is not the 961k-row mixed corpus, a book corpus, an independent
benchmark, or a native-verified reference set.

The package presents two use-specific views:

| View | Rows | Words | Use |
|---|---:|---:|---|
| `screened_meta_gbm` | **1,841** | **47,566** | Recommended for experimental sentence-level LM training. Every row has at least five whitespace tokens. |
| `short_utterances_meta_gbm` | **110** | **347** | Preserved for context; not recommended for general LM training. |
| Total screened values | **1,951** | **47,913** | Both views combined; no normalized duplicate values across either view. |

The candidate has 234,500 characters total (232,638 in the main training view,
1,862 in the short context view). It is a modest starting resource, not a
large-scale Garhwali language-model corpus.

All 1,951 selected strings were matched against the earlier public v0.2.7
`text` and `text_expansion` values. Their appearance in the v0.2.8 configs
improves training eligibility labels and discoverability; it does not add
1,951 unique Garhwali strings to the corpus.

## Quality gates and measured result

- Evaluated 16,947 rows from the v0.2.7 `text/train` and
  `text_expansion/train` inputs.
- Accepted 1,952 strict candidates with the exact Meta-only provenance and
  rights basis; excluded one punctuation-only normalized duplicate, leaving
  1,951 unique values.
- Blank candidates admitted: **0**. Blank rows in the published candidate
  views: **0**.
- Normalized duplicate rows in the candidate views: **0**. The excluded pair's
  retained ID, excluded ID, and normalized-key hash are saved in
  `quality-screened-exclusions.json`.
- 110 values shorter than five whitespace tokens are separated and have
  `recommended_for_training=false`; no text was deleted from the source release.
- All included rows are labeled `gbm`, Devanagari, upstream `train`, with no
  detected upstream dev/test overlap. All 1,951 retained values have strict
  automated quality status and zero record-quality flags.
- Every row includes a stable project ID, exact source record ID, source URL,
  attribution, license and rights evidence, quality fields, text hash, and
  review status.
- Native-speaker review: **not performed**. Automated screens cannot establish
  spelling, meaning, dialect, or naturalness. These are training candidates,
  not gold references.

### Unicode duplicate-key fix

The previous normalized text key retained only Unicode letters and digits,
which dropped Devanagari combining vowel marks. That could incorrectly merge
different words. The key now preserves Unicode letters, marks, and numbers
while normalizing compatibility forms, case, spacing, and punctuation. A
regression test verifies that `कला` and `काली` remain different while
punctuation/spacing variants match. On the screened candidate, this leaves one
punctuation-only duplicate pair to exclude.

## Rights and provenance

The new view applies the project decision
`meta_omnilingual_cc_by_4_0_training_2026_10_06` only to exact Meta source
records whose URL, source ID, license, rights status, and saved evidence
locator match. The retained output is scoped to transcript text; it does not
include audio or clear any mirror or other corpus source. The earlier
`training_eligible=false` source value is preserved in the derived records.

Evidence and decision scope are documented in
[meta-omnilingual-training-rights-decision-2026-10-06.md](meta-omnilingual-training-rights-decision-2026-10-06.md).
The decision relies on the [official Meta dataset card](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus/blob/main/README.md)
and [CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en).
This project-specific decision applies only to these exact source-derived
rows and does not relicense the existing mixed-source corpus.

## Files and reproducibility

The local, Git-ignored build outputs are:

- Hugging Face overlay: `data/huggingface/garhwali-screened-text-v0.1-upload/`
- Kaggle package: `data/kaggle/garhwali-screened-text-v0.1/`
- Builder: `scripts/build_quality_text_release.py`
- Input source manifest: `data/huggingface/garhwali-language-lab-v0.2.7-staging/manifest.json`

The Hugging Face overlay contains two new v0.2.8 configs and an updated card;
its upload tree contains only the card plus the new data and reports, so it is
an additive upload. The Kaggle package includes `train.csv`,
`short_utterances.csv`, schema, attribution, license policy, exclusion report,
and a manifest with source and artifact hashes.

## Verification

- Full project suite: **827 tests passed**.
- Focused quality-release builder tests: **3 passed**.
- Hugging Face `datasets` loaded both local JSONL views with the declared
  features: 1,841 and 110 rows.
- Kaggle CSV parsing: 1,841 training rows and 110 context rows; text order and
  values match the Hugging Face JSONL training view.
- Every recorded artifact size and SHA-256 verified against the manifests.
- A second clean build produced identical output hashes.
- Hugging Face commit [`48f9107d0285b3b3ec3c893303efb8a997cfc49b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/48f9107d0285b3b3ec3c893303efb8a997cfc49b)
  added the two v0.2.8 configs and their files. A stale v0.2.7 overview was
  subsequently corrected; the latest card-only update is commit
  [`cf60b217d9d3de045d81fb41d82514e29db2bf33`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cf60b217d9d3de045d81fb41d82514e29db2bf33).
  Remote read-back confirms the card reports 963,484 displayed rows,
  185,327 overlapping content-view rows, 20 named configs, and 31 config/split
  views. Earlier paths remain present.
- Loaded both configs directly from the public Hub with `datasets.load_dataset`:
  `screened_meta_gbm` returned 1,841 rows; `short_utterances_meta_gbm`
  returned 110. Both checks confirmed zero blank values, zero exact duplicate
  values, `gbm`, CC BY 4.0 lineage, and the intended training flags.
- Kaggle has not been uploaded. The user approved enabling the ChatGPT
  extension's “Allow access to file URLs” permission, but Chrome security
  blocks automated extension-setting changes. The user must toggle it manually
  before the authorized upload can proceed. No files were sent to Kaggle.

## Next actions

1. Publish `rushilrawat1/garhwali-screened-text-candidates` on Kaggle when an
   approved upload route is available, then verify the files and public preview.
2. Keep native accuracy claims explicitly unverified until qualified speakers
   review the text.
