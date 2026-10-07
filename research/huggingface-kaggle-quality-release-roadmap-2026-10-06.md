# Hugging Face and Kaggle quality-first release roadmap

**Original plan:** 6 October 2026  
**Current status:** checked 7 October 2026; see the [cross-platform metrics audit](current-platform-metrics-2026-10-07.md).
**Scope:** Improve the user-facing training value of the existing Garhwali
Hugging Face corpus, then mirror the same quality-screened data on Kaggle.
**Policy:** Add purpose-built views and preserve prior releases. A filter may
exclude a row from a specific training view, but it does not delete the source
record, its provenance, or the reason for exclusion.

## Goal

Make the first download a small, clearly named Garhwali text dataset that can
be tried without sorting through reference indexes, joins, blank catalog text,
or machine transcript drafts. Keep the full corpus available for source
discovery and research, but report its reference rows separately from usable
language examples. The Kaggle files must be generated from the same selected
records and release manifest as the Hugging Face view.

“Clean” here means non-empty, schema-valid, exact-deduplicated, provenance-
linked, task-split-safe, and admitted under a documented source-use decision.
Automated checks cannot certify spelling, meaning, or dialect correctness; the
screened subset must continue to say **not native-reviewed**.

## Baseline and first candidate

The live corpus v0.2.7 shows 961,533 combined config rows, but 778,157 (80.9%)
are `record_index`, `source_catalog`, and `record_sources` reference views.
Those tables support source lookup; they are not language examples. The
`text`, `text_expansion`, and `text_resources` configs have 20,810 overlapping
view rows, and none currently has `recommended_for_training=true`.

The local release audit finds a narrow candidate that can be safely surfaced
without treating all corpus records alike:

| Measure | Current evidence |
| --- | ---: |
| Main `text` / expansion strict-screen candidates before the source-use decision | 1,994 |
| Meta Omnilingual-only records before normalized deduplication | 1,952 |
| Deduplicated Meta-only candidate across both views | **1,951** |
| Sentence-length LM training rows (5+ whitespace tokens) | **1,841** |
| Training words / characters | **47,566 / 232,638** |
| Short context-only rows (<5 whitespace tokens) | **110** |
| Short-view words / characters | **347 / 1,862** |
| Normalized duplicate pairs excluded | **1** |
| Blank text values in the candidate | **0** |
| Source partition | Upstream `train` only; no detected dev/test source overlap |
| Linguistic review | Automated screen only; **not native-reviewed** |

The 42 remaining diagnostic candidates come from Wiktionary and carry
share-alike/native-review flags, so they are excluded from this narrowly
licensed first profile. The Meta-only records point to the official
`facebook/omnilingual-asr-corpus` source, whose card declares CC BY 4.0. The
project's old source flag was conservatively false; the release adds a
source-specific, attributed decision for this exact license and keeps the
original value visible in provenance. One pair differing only in punctuation is
excluded from the new view, with both IDs recorded; prior release files remain
untouched. The Unicode duplicate key preserves combining marks, so vowel-mark
distinctions are not collapsed. [Upstream dataset card](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus/blob/main/README.md) ·
[CC BY 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en).

Of the 1,951 values, 110 nonblank short utterances are preserved in a
context-only view and are not recommended for general language-model training.

This candidate is a **short prompted-speech transcript text set**, not a large
general-purpose book corpus. It is appropriate for small experimental
text-model runs and language-resource exploration. It is not native-validated
ground truth, an independent benchmark, or an ASR audio/transcript package.

## Ordered work plan

### 1. Freeze the measured baseline — complete

- Pin the source release, source-card snapshot hash, exact source records, and
  baseline counts.
- Keep package rows, reference rows, content rows, and model-eligible examples
  as separate metrics.
- Confirm that prior v0.2.7 files remain untouched.

**Exit check:** the source package and rights evidence reproduce the counts
above; no count is presented as unique text unless deduplicated at that grain.

### 2. Apply a narrow source decision and deterministic screen — complete

- Allow only Meta `CC-BY-4.0` records with exact source identity and recorded
  rights evidence; preserve source attribution and the prior source flag.
- Require `gbm`, Garhwali-candidate labels, strict automated quality tier,
  non-empty text, zero quality flags, project `train` split, and no detected
  held-out-source overlap.
- Keep all other sources and machine drafts out of this first training view;
  do not silently discard them from the broader corpus.
- Reject duplicate IDs; log normalized duplicate text exclusions with both
  retained and excluded record IDs.
- Preserve Unicode combining marks in normalized text keys so distinct
  Devanagari vowel forms are not merged.
- Route utterances under five whitespace tokens to a separate context view;
  retain them, but do not recommend them for general LM training.

**Exit check:** every selected row has text, a stable ID, the same CC BY basis,
source record ID, and an explicit automated/unreviewed quality status; zero
blank values, normalized duplicates, held-out rows, mixed-source rows, or
rights-unknown rows. The short-utterance view carries
`recommended_for_training=false`.

### 3. Build matching Hugging Face and Kaggle packages — local build complete

- Add clearly named training and context configs to the existing Hugging Face
  corpus, with a short card section and copy-paste `load_dataset` examples.
- Create a focused Kaggle package with a 1,841-row training CSV and a separate
  110-row context CSV, plus schema, attribution, license, and build manifest.
- Keep source catalogs, joins, metadata-only records, PahariLI rows with
  unresolved origins, and SraVaani machine drafts outside the training file.
- Make the card distinguish the focused view from the larger research/source
  catalog. Do not inflate the corpus-size headline.

**Local result:** both packages are built under ignored `data/` paths. The
Hugging Face overlay adds two versioned configs without replacing earlier
release files; Kaggle has separate training and short-context CSVs.

**Exit check:** Hugging Face and Kaggle row counts, text values, rights fields,
and manifest totals reconcile; every training field is present and non-empty.

### 4. Run release validation before upload — complete

- Run deterministic rebuild twice and compare manifests/hashes.
- Validate JSONL/CSV parsing, schema, required fields, Unicode, empty rows,
  stable IDs, exact duplicates, and source/split leakage.
- Load both published Hugging Face configs with `datasets.load_dataset`; check
  live row counts, blank/duplicate text, language, license, and training flags.
- Validate Kaggle CSV parsing, row-level values, metadata, field descriptions,
  rights notice, and local artifact hashes.

**Exit check:** passed locally and against the live Hugging Face configs. Kaggle
publication and manifest-preview state is summarized in step 5 below and the
7 October sync report.

### 5. Publish additively and verify online — complete as of 2026-10-07

- **Hugging Face complete:** added both configs under `releases/v0.2.8/` in
  `rushilrawat/garhwali-corpus`, retaining earlier release paths. Commit:
  [`48f9107d0285b3b3ec3c893303efb8a997cfc49b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/48f9107d0285b3b3ec3c893303efb8a997cfc49b).
- **Card corrected and read back:** the first v0.2.8 card retained stale v0.2.7
  totals. The current card-only correction is at
  [`cf60b217d9d3de045d81fb41d82514e29db2bf33`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cf60b217d9d3de045d81fb41d82514e29db2bf33).
  It reports 963,484 displayed rows, 185,327 overlapping content-view rows,
  20 named configurations, and 31 config/split views.
- **Hugging Face online load verified:** `screened_meta_gbm` returned 1,841
  rows and `short_utterances_meta_gbm` returned 110. Both have zero blank rows
  and exact duplicate values; all language and license fields match the build.
- **Kaggle screened text complete:** public version 1 contains 1,841 training
  candidates and 110 context rows, matching the Hugging Face views. It reuses
  existing Meta transcript values and adds no unique examples.
- **Kaggle ASR references complete:** private version 2 contains 2,718 existing
  VAANI reference pairs (2,202 train / 373 validation / 143 test), preserving
  the earlier 2,002 pairs and indexing 716 already-existing references. Its
  manifest preview works.
- **Notebook saved:** baseline notebook version 3 selects the v2 input but has
  not been run. See the [7 October Kaggle sync report](kaggle-asr-v0.2-sync-2026-10-07.md).

**Exit check:** a fresh user can load the exact text subset from either platform
and sees the same count, schema, source attribution, and review limitations.

### 6. Expand only after the first clean profile is proven

- Add separately labeled glossed lexicon entries after checking their source
  permissions and required gloss fields.
- Build an ASR training view only from non-empty audio/transcript pairs with
  permitted reuse and speaker-disjoint splits. Keep provider references and
  machine drafts distinct.
- Audit near-duplicates and source-document overlap; preserve alternatives and
  provenance rather than deleting original records.
- Revisit OCR, folklore, and book-derived text only after item/edition rights
  and language-origin evidence are tied to the exact rows.

**Exit check:** each modality receives its own counts, eligibility rules,
license scope, validation, and task-specific loading example.

## Hard release rules

- No blank or metadata-only record may enter a named language-training view.
- Do not remove source/reference records from the historical corpus to make a
  headline look smaller; show them in a source/reference view and keep them out
  of training examples.
- Never turn machine drafts into human references. Empty machine outputs do
  not enter transcript-training views.
- Keep held-out evaluation material out of training; exact split boundaries
  are part of the release manifest.
- A CC BY source basis supports reuse subject to its attribution conditions;
  it does not certify Garhwali accuracy. The public card must say so.
- Native-speaker review remains a later accuracy step and is not implied by
  automated screening.

## Current stop point — 2026-10-07

Baseline profiling, source-specific rights review, Unicode-safe duplicate
handling, screening, and local package generation are complete. Hugging Face
publication and online row/card checks are complete. The screened-text dataset
is public on Kaggle; the reference-clips dataset remains private. The baseline
notebook is saved but unrun. This is additive: v0.2.7 and its source rows are
preserved. ASR, lexicon, and book/OCR resources need separate quality and
rights gates; they are outside these text counts.

The latest release report and current-metrics audit remain the source of truth
for published counts. The focused text view reuses rows already present in the
v0.2.7 source package; v0.2.8 is an additive usable view, not a claim that new
source material was collected. Broader modality-specific views still need
separate quality and rights gates.
