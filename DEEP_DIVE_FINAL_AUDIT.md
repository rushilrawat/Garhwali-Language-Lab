# Garhwali Language Lab — deep final audit

## Current release and local Archive intake — 2026-10-04

The current public corpus release is **v0.2.3** at Hub commit
[`76dac8d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76dac8de70d37595c7af9a3c642c81ece615ec5d).
Its 246-row `text_resources/train` config surfaces existing catalog records;
the package contains 827,450 overlapping-view rows. The speech repository
remains at v0.2.1. The local Internet Archive intake contains 119
checksum-verified payload files (6,005,077,831 bytes) and 4,011 OCR page
objects after two local DjVu sidecars were reconciled. There are 3,983
non-empty OCR rows and 3,981 unique normalized non-empty values; one duplicate
group covers two page rows. A broader check against all 32,072 canonical
cleaned parent texts found 2 exact page matches (already represented Walton
gazetteer pages) and 0 near-match candidates at 5-gram Jaccard ≥0.85, after
scoring 1,910,194 length-compatible pairs. This does not test semantic
similarity or every corpus layer. The 39 media files total 14:09:25.531 of
playback, not verified Garhwali speech time. All pages remain unverified for
language and OCR accuracy and none was newly cleared for training or
redistribution. No Archive intake files or new extracted rows were published;
the two exact page matches already exist as Walton gazetteer records. Raw files remain ignored.
See the [source ledger](research/internet-archive-intake-2026-10-03.md),
[source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md),
and [quality/overlap audit](research/internet-archive-intake-quality-2026-10-04.md).

A technical media first pass re-hashed and reconciled all 39 files against the
source-linked candidates and `ffprobe` records: 39/39 passed, comprising 15
audio-only files and 24 videos with audio, with zero exact duplicate file
hashes. They occupy 4.38 GB (4.08 GiB) and total 14:09:25.531 playback, not
verified Garhwali speech. All remain unreviewed. One separate 27.481-second
local pilot produced a repetitive machine draft with no reference for scoring;
the saved model's existing test WER/CER are 74.3% / 40.4%, so bulk draft
generation was not started. No content or rights state changed. See the
[media first-pass report](research/internet-archive-media-first-pass-2026-10-04.md).
No transcript/caption sidecars were found in 31 captured Archive snapshots
(1,047 listed files) or their local item folders. Six item language fields
claim Garhwali; the files remain unreviewed.

The follow-up examines five priority works: 920 language-study page objects
and 440 translated/contextual folklore page objects (432 non-empty, 8 empty).
After normalization, 1,350 distinct non-empty values remain; the repeated
Juyal pair is digitizer-footer-only, and one Snow Balls row normalizes empty.
External academic and library evidence strengthens the book-level
classification of selected sources, but automated script composition does
not identify page language. A scan dated 1935 in Archive metadata is a 1977
reprint; the Juyal CC0 claim conflicts with the scan's “all rights reserved”
notice; the Shailesh uploader claim has no verified rights-holder authority.
No new Archive pages are eligible for public content or training based on this
review. See the [detailed evidence report](research/internet-archive-priority-language-rights-review-2026-10-04.md).

The following local page/section map indexes 722 physical pages from Chatak
and Shailesh, aligns 719 OCR records, and retains the three empty scans.
Shailesh's visually checked contents page defines 15 printed-page ranges
covering 416 scans; the +13 physical-to-printed offset was checked at three
points. Printed pages 63–64 are unlisted; Chatak still has no edition-specific
page map. A Hindi/English Tesseract alternate was generated for all 29
flagged/empty pages; one empty scan yielded text and two remain empty. It adds
3,796 characters versus the selected original rows, but this is not evidence
of accuracy. A text-free comparison triaged 11 high-, 3 medium-, and 15
low-priority pages. Image inspection of all 14 high/medium pages identified
administrative/title matter, blank scans, index pages, and two unresolved
text-bearing cases; it produced no transcription or correction. The 29
alternates have no exact match or ≥0.85 5-gram Jaccard candidate against the
32,072-row canonical cleaned text view (17,924 pairs scored). No record was
promoted or deleted. Rights and page-language verification remain unresolved.
See the [detailed evidence report](research/internet-archive-priority-language-rights-review-2026-10-04.md).

## VAANI official-split and model-exposure audit — 2026-10-04

The 5,894 prepared transcript rows map to VAANI's official 4,778/666/450
train/validation/test partitions, with unique audio hashes and no audio-hash
crossings. The project's strict 1,621/269/112 ASR manifests map entirely into
the corresponding official splits. However, the 5,513-row expanded-human
SraVaani training manifest contains 397 other official validation records and
338 other official test records that were outside the smaller fixed evaluation
hashes. This checkpoint cannot be evaluated on the full official validation
or test split. The exact crosswalk is generated by
[`audit_vaani_official_split_lineage.py`](scripts/audit_vaani_official_split_lineage.py)
and covered by regression tests.

The other 338 official test rows were scored once using the local human-only
Whisper-tiny v0.2 checkpoint, which trained on the strict 1,621-row training
view. WER is **83.249%** (3,449/4,143 words) and CER **48.468%**
(7,356/15,177 characters). All 338 audio hashes/references align, and an
independent re-score reproduces every row's metric counters. No direct audio
hash or identifiable-speaker overlap with strict training was found; only five
test rows carry identifiable speaker metadata, however, so speaker
independence is unproven. The split is public and has been used in published
research, while this checkpoint had already been scored on the related 112-row
subset. This is an open diagnostic, not independent accuracy. The 2026
five-seed paper reports 47.0% mean WER for a different w2v-BERT 2.0 system on
the full official split; its result is methodological context, not a direct
comparison. Details and exact hashes are in the
[lineage report](research/vaani-official-split-lineage-2026-10-04.md).

## Meta Omnilingual ASR validation and decode check — 2026-10-04 to 2026-10-05

The offline preparation reconciles all 2,927 source rows and seven Parquet
shards to the transcript/release manifests. It retains 70 internally unsafe
records in the source audit and exposes only 2,294 train, 271 validation, and
292 unresolved test rows to the corresponding safe views. All 2,857 materialized
WAVs passed SHA-256 and PCM-header checks. Whisper-tiny Garhwali v0.2 scored
93.900% WER / 72.918% CER on the development view. A paired beam-5 candidate
improves WER by 0.4543 points but worsens CER by 0.0325, so greedy remains
selected under the stated guardrail. It is a poor, development-only result;
Meta test was not scored. Original Whisper-tiny and runnable SraVaani assets
are unavailable locally. See the [complete report](research/meta-omnilingual-asr-validation-2026-10-04.md).

## Repository verification — 2026-10-05

CI's unittest discovery command passes **743/743**, and the release-index
validator passes for the tracked v0.1.1 snapshot. The bundle itself has no
path/hash failures when source comparison is disabled. The full local
`build_release_bundle.py --check` finds **59 stale-source entries**: 35
current selected files are absent from the frozen v0.1.1 bundle, and 24
indexed files differ from the current workspace. Three missing paths are
reports generated during the Meta ASR step. The old snapshot was not
overwritten; this workspace therefore still needs a separately versioned
current-release bundle before any new release claim. The CI runner does not
have the ignored local data tree, so its behavior on GitHub is not established
by this local source-tree check.

## Hugging Face quality release v0.2.2 — 2026-10-01 (historical audit)

At the time of this 1 October snapshot, the public corpus was v0.2.2; its corrective commit was
[`b18933b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b18933bb2e98f091add0b1889e70587448d9891f). It adds a separate `text_expansion` train config with
1,647 existing catalog values promoted into a ready-to-load training view.
They are net-new against existing text, provider ASR, machine drafts,
instructions, and lexicon fields; their appearance in `catalog` is
intentional. The package has 826,986 overlapping-view rows (164,141
content/config and 662,845 reference/join rows), all with config-specific
source locators; preflight reports zero errors and zero deleted/mutated rows.
Every expansion row has a recorded public-rights basis and an automated
strict-tier label. This is not new source ingestion, native language review,
or proof of source-page-family independence. The release preserves prior
versioned files. A Hub Viewer diagnostic found null-to-string schema inference
failure in `sravaani_drafts`; the package now writes empty strings for missing
speaker IDs and its remote manifest matches the corrected local shard hash.
The Hub Viewer is temporarily busy, so post-fix endpoint verification remains
pending. All **699/699** configured tests
pass, and `git diff --check` passes.

Phase 1 is complete. Cross-config exact normalized-text overlap and frozen
benchmark source-record overlap checks now pass for the added config. Broader
source-page-family and rights-scope audits remain release gates.
See [`research/huggingface-dataset-quality-roadmap.md`](research/huggingface-dataset-quality-roadmap.md)
and [`research/huggingface-quality-baseline-2026-10-01.md`](research/huggingface-quality-baseline-2026-10-01.md)
for current definitions and counts, and [`research/huggingface-text-expansion-audit-2026-10-01.md`](research/huggingface-text-expansion-audit-2026-10-01.md)
for the exact inclusion, dedupe, and release limitations of the added config.

## Developer access, schema, and v0.2.1 Hub release audit — 2026-10-01

The v0.2.1 text and speech packages add consistent record-level rights and
quality fields without replacing source-specific terms or evidence. The
package validator checks the five common fields and their types on every row
when the manifest declares schema v1.0.0, and requires the shipped schema and
quick-start assets. Empty license and quality-flag lists remain valid when no
label or flag was recorded.

Both public Hub packages were uploaded additively and verified: corpus commit
[`7cae908`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/7cae908fee51acd2e1e47955acaa9ee035c9bfbc)
and speech commit
[`9da266e`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/9da266e23bfc198f70784a6e81edbf32f946102f).
Earlier release files remain present. Corpus follow-up commit
[`0a76bc6`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/0a76bc6a1f403b2ba460ef0ece464050c178c189)
corrects the versioned quick-start that the card links to. Validation passes for **821,083**
rights-filtered text-package views and **300,915** all-data archive views. All
267 speech Parquet shards match the 113,363-row manifest and common schema. The
local lexicon example loaded through Hugging Face Datasets and queried through
pandas and DuckDB. These checks validate structure and lineage only; they do
not establish native-speaker accuracy. The complete unit suite passes
**684/684**. A speech-card follow-up at [commit `2808ad7`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/2808ad7d4c59becbd842f76ed38af1ee06274ba8) clarifies that VAANI split counts refer to all 110,436 audio rows; the provider-transcribed pool is 5,894 rows and the strict linked ASR view is 2,002 rows. It marks SraVaani outputs as unreviewed drafts. No audio or Parquet payload changed. The Dataset Viewer API returned a temporary HTTP 500 busy response
after upload; the repository cards, commit revisions, and file trees were
verified separately.

## Rights-resolution update incorporated into v0.2.1 — 2026-10-01

The v0.2.1 public profile was rebuilt from the preserved all-data layer. It
contains 32,072 unique catalog texts; the public catalog exposes 12,606 under
open, noncommercial/share-alike, source-policy, or narrowly fact-only bases and
redacts 19,466 with unresolved reuse rights. All 216 structured knowledge
records are represented as fact/bibliographic metadata only. The interim
rights-resolution package was uploaded at Hugging Face commit
[`53c1ce9`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53c1ce9baa07e6fb05722e5a1ed750f33096124b); previous versioned files remain present.

The rights-resolution log now lists exact source-associated pending counts,
why each source remains unresolved, and the next evidence needed. Counts overlap
across source links. The local all-data manifest confirms all 32,072 full
catalog texts remain included. Do not remove or recast the remaining rights
redactions as a code defect: repository license labels, a public URL, and the
absence of an explicit “private” notice do not grant rights in underlying
blogs, books, translations, quotations, or compilations. Copyright arises
without a visible notice according to the Indian Copyright Office. See
[`research/text-rights-resolution-2026-09-30.md`](research/text-rights-resolution-2026-09-30.md).
The source log records the exact current preflight, file-size, and test results.
The public package is audited for zero pending-text leaks and the 216
metadata projections are checked against the field allowlist.

## Source expansion checkpoint incorporated into v0.2.1 — 2026-09-30

The latest ingestion refresh retains **34,505 source rows from 49 files** and
produces **32,072 exact-unique parent texts**, **16,089,764 characters**,
**2,935,379 whitespace-separated tokens**, and **151,690 exact-unique
segments**. All-data and public-profile package views contain 300,915 and
155,516 overlapping rows respectively; the public profile has 129,186 content
rows and a metadata-only index over 300,915 records. The added source is the
MIT-labelled Garhwali Language Library (164 exact-new strings); Jambu and
Hikinegi were exact-deduplicated with zero net-new strings.

The repeatable refresh, generated file map, rights-profile preflight, and
additive Hub upload are complete. The initial source-expansion payload is live at
[Hugging Face commit `5db2673`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/5db26737c4dcb4bd3e6a3750d30c2d9cae3048c1); the corrected dataset cards are at
[commit `53a0aff`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53a0aff5ebaf7e676954065d86e2d78c0ff70504). No older corpus records or
release paths were deleted. Public content still redacts 26,330 text values and
withholds 216 structured payloads for unresolved reuse terms. Rights-unclear
web candidates remain in the local experimental layer; no new model inference
or accuracy claim was made. Native review remains deferred. The earlier web-wave
metrics below are retained as historical, not current, measurements.

At the frozen v0.2.0 review snapshot, the full working-tree suite passed
**656/656 unittest** tests. At the interim rights-review snapshot, the working tree passed
**671/671 pytest** and **669/669 unittest**. These validate code and data contracts, not
linguistic correctness, unrestricted reuse rights, or independent model accuracy.

## Frozen v0.2.0 audit snapshot (2026-09-29)

The four new Garhwali-only source ingesters and the rebuilt v0.2.0 packages pass
local checks. The intake adds **671 exact-new unique texts** (696 source rows;
180,043 characters) from the LSI dialect table/specimens, five explicitly
Garhwali Upreti proverbs, and 50 pinned Door43/TLF stories. Current scale is
**29,426 exact-unique parent texts** and **115,785 exact-unique sentence
segments**. The local all-data package has 260,199 overlapping rows; the
public-profile package has 150,065 rows and metadata references for every
all-data row.

Verification on 2026-09-29: pytest **607/607 passed** and unittest **605/605 passed**; public and all-data HF
package cloud preflights passed; final release audit passed with no hash,
provenance, or compatible-rights failures; release index validation passed; the
compact bundle contains 160 files / 4,303,470 bytes and its hash/path check
passed. The cloud preflight was corrected to validate identities for the three
metadata-only reference tables and to recognize their manifest file. Two
retrieval reports were regenerated with repository-relative paths so the
release bundle no longer includes local machine paths.

The release audit retains one XORQA upstream train/dev exact-text warning. New
LSI OCR is still unreviewed (496/632 table rows have OCR confidence below
60/100); the 50 story translations are not speaker-reviewed. Rights and
quality remain row-level: the public profile redacts 24,565 catalog values and
omits 216 structured payloads without a compatible public-rights basis. The
complete all-data package retains those values locally/access-controlled.
Native-speaker review and dialect annotation remain deferred, so v0.2.0 is not
a native-validated benchmark. Hugging Face v0.2.0 is verified at commit
`cb6314880b8a28c3bf3dcc025d8ff9ebe062c927`; GitHub published tag `v0.2.0`
from commit `e2fdf5b`.

See the [v0.2.0 source expansion report](research/garhwali-data-expansion-2026-09-29.md),
[release notes](release/v0.2.0/README.md), and
[`release/v0.2.0/final-audit.json`](release/v0.2.0/final-audit.json).

## Post-release local web expansion before the v0.2.1 refresh (2026-09-30)

The counts in this section are an interim pre-refresh snapshot and are retained for
history; the current corpus values are at the top of this audit.

The tenth ingestion wave scanned 6,844 entries from the Uttarakhand e-Magazine
Blogger feed plus two Khabar Saar short-story pages. It selected 1,818 page
candidates, skipped 46 exact duplicates, and added 1,772 exact-new records
(6,758,808 source characters) to the local experimental layer. No page was
promoted to a rights-cleared or native-reviewed dataset.

The refreshed working tree contains 33,562 source rows from 47 files,
31,198 exact-unique parent texts, 16,084,744 characters, and 150,814
exact-unique segments. The segment-split report reports zero exact cross-split
leakage. Language-quality buckets for this wave are 1,147 mixed-script review,
543 Romanized Garhwali candidates, and 82 scope-unverified candidates. Rights
are unassessed for every new page. Full text remains in the Git-ignored local
all-data view; public Hugging Face received zero new full-text rows and the
remote v0.2.0 release was not changed.

The local package previews carry development release ID `garhwali-language-lab-v0.2.1-dev`:
all-data is 297,000 overlapping-view rows; the public-profile preview is
151,812 rows including redacted catalog rows, with 125,475 records exposing
profile content. Its content-free index contains 297,000 rows, 4,144 source
entries, and 324,338 links. None of these local-preview changes have been
uploaded.

The ingestion itself is repeatable through the LangGraph tenth wave. The new
`scripts/refresh_corpus_after_ingestion.py` command chains the existing
canonicalization, quality, split, language-resource, benchmark, instruction,
package-preview, and reference-index builders, then regenerates the current
metrics block in `README.md`. Its scope and limitations are in
[`PIPELINE.md`](PIPELINE.md) and the
[web-goldmine intake report](research/garhwali-web-goldmines-2026-09-30.md).
The pre-refresh post-ingestion test suite passed **635 pytest** and **633
unittest** tests. The next source-refresh suite passed **656 pytest** and **654
unittest** tests. The current v0.2.1 configured-environment suite passes **684** tests. The pytest runner available in this workspace is the system
installation with the project virtualenv's dependency path supplied; the
`.venv` itself does not contain pytest.

---

## Historical audit (2026-09-28; v0.1.1 snapshot)

**Audit date:** 2026-09-28
**Scope:** current working tree, generated public/all-data Hugging Face package snapshots, model-data selection scripts, release and preflight validators, research status, and test coverage.
**Purpose:** identify defects that can make corpus claims, source reuse, evaluation, or model-quality conclusions incorrect; record verified fixes and the remaining release gates.

## Current conclusion

Hugging Face serves the interim rights-resolution corpus update at commit `53c1ce9`.
The public package has 32,072 unique catalog texts, exposes 12,606 under
recorded source-specific or narrow fact-only bases, and redacts 19,466 full
texts still lacking compatible reuse evidence. It exposes all 216 structured
records as factual/bibliographic projections while leaving expressive notes,
lyrics, translations, abstracts, and passages out. No all-data payload is
public. The local all-data package retains all
32,072 catalog values. The detailed source queue, restrictions, test results,
and exact package inventory are in
[`research/text-rights-resolution-2026-09-30.md`](research/text-rights-resolution-2026-09-30.md).
Native-speaker review and dialect annotation are deferred; language and
benchmark claims remain automated candidates.

Phase 8 result labels are now reconciled: test rows with matched saved predictions and the aggregate-scored 398-row internal text set are historical-only; CrossSum and Meta Omnilingual test exposure remains unresolved. No task result is independent-final-eligible. See the [result eligibility report](research/task-result-eligibility-2026-09-28.md) and [fresh lineage audit](research/model-accuracy-lineage-2026-09-28.md).

The package inventory reports 257,807 rows across overlapping all-data views and 146,684 content rows across 12 public config/split entries. Public reference tables add 257,807 archive-row references, 590 sources, and 277,637 record-to-source links. Counts include multiple representations of the same source material and are not unique-example totals. The corpus has 28,755 exact-unique parent texts and 114,064 prepared text segments. All-data includes every collected text value (zero catalog redactions); the public content profile redacts 24,566 values and omits full content for all 216 structured rows without a compatible public-rights basis. Those structured records are now present in the public reference index as metadata and source pointers. The index marks record-level rights `not_recorded` for 228,836 rows; linked source terms still require review before reuse.

## Verified findings

### Fixed critical defect — noncommercial Creative Commons sources passed the public-rights classifier

`scripts/build_huggingface_dataset.py:is_publishable_provenance` treats the substring `cc-by-` as sufficient evidence of an open license. It does not reject the `NC` (noncommercial) or `ND` (no derivatives) variants. A provenance record for PanLex labeled `CC-BY-NC-SA-4.0` has no blocking rights marker that compensates for this, so the classifier returns publishable.

**Measured effect and correction:** the prior public-profile build exposed **13 segment rows** from `panlex_gbm` carrying a CC-BY-NC-SA license. The license classifier is fixed, regression-tested, and both packages were rebuilt; the current audit reports zero general text public-rights failures. The all-data package retains the full data locally. At the time of the 2026-09-26 review, remote publication had not occurred; the subsequent public reference-index release is documented in the Hugging Face status at the end of this audit.

**Remediation complete:** restrictive CC variants are rejected before accepting an open-license marker; regression tests cover NC, ND, valid CC-BY, and the exact MIT identifier. The rebuilt public profile has zero general text-rights failures.

### Historical high — full content for 216 structured records lacked public-rights evidence at v0.1.1

The public and all-data packages contain 216 records in six configurations: geography (50), historical terms (36), literary people (26), literary works (66), popular songs (30), and university research (8). Source hints previously used inconsistent field names such as `evidence`, `source_refs`, `source_ids`, `source_url`, `wikipedia_url`, `lyrics_sources`, and `translation_sources`. The builder now maps source pointers into standardized `provenance`, adds explicit quality/review status, and records rights without inventing a license. A web review has now examined the 186 previously unassessed geography, history, people, works, and university records. Some component sources carry reuse terms, but no whole-record public-rights basis was established for those mixed-source records. Current audit counts are **0 missing provenance**, **0 missing quality metadata**, **0 unreviewed rights statuses**, and **216 rows without compatible public rights**.

The release audit and cloud preflight enforce these fields. The all-data/private
preflight passed for that snapshot. The current v0.2.1 public release exposes a
factual/bibliographic projection for each record in six metadata
configurations. Full expressive payloads remain in all-data because compatible
reuse evidence has not been established. The projection does not claim that
the referenced works are cleared.

**Additional traceability fix:** a deeper row-level check found that some geography evidence labels and a literary capture reference still exported as internal IDs without a URL or capture fingerprint. Geography evidence IDs now resolve through the geography catalog, and shared source IDs inherit the best available metadata across the project's structured-source catalogs. The regenerated all-data package has **zero untraceable structured rows** and passes cloud preflight. This improves citation traceability; it does not establish redistribution rights.

**Remaining:** obtain source-specific rights or permission for the expressive
full records. A source URL alone is not a license. Findings and exact source
links are in [`research/structured-rights-web-review-2026-09-23.md`](research/structured-rights-web-review-2026-09-23.md); all 216 full records remain intact in all-data.

### High — historical broad text-model runs do not establish Garhwali-only quality

`scripts/run_text_scaling_experiment.py`, `scripts/run_indicbert_adaptation.py`, and its LoRA variant previously defaulted to the broad `splits/text/train.jsonl` file. The text-scaling and IndicBERT head/LoRA defaults now use the checksum-addressed recommended view. The strict view has **7,490 of 106,915 rows (7.0%)** in training; the historical all-data split has 31,392 Garhwali candidates, 47,821 mixed-language, 14,918 review, and 13,036 non-Garhwali context rows. These categories may overlap with quality tiers, so do not sum them as mutually exclusive classes.

Historical experiments remain valid only for their original broad-data question; they are not evidence of Garhwali-only model quality. The strict-default IndicBERT configuration has not yet been trained, and its improvement over historical runs is unknown.

**Code remediation complete:** preserve historical results and use strict checksum-addressed train/validation defaults with separate output paths. A new neural study has not been run; record hashes and composition if local compute is available.

### High — text-model experiment default evaluated the wrong held-out set

Before this audit, `scripts/run_text_scaling_experiment.py` defaulted to `data/processed/model_ready/splits/evaluation/text_candidate.jsonl` (3,603 rows). The historical `text_scaling.json` actually records a 2,492-row held-out artifact. GarhwaliBench separately filters its candidates to 398 strict automated text records at `data/processed/evaluation/garhwali_bench/internal_text.jsonl`. Neither the old 2,492-row report nor the former 3,603-row default is the current 398-row GarhwaliBench test.

**Remediation verified:** the default uses the recommended 7,490-row train view, 377-row validation view, and exact 398-row frozen benchmark. Broad and recommended character n-gram baselines were run on the same 377/398 validation/test artifacts. The recommended corpus reached test cross-entropy **2.3233** (perplexity **10.2095**), compared with **2.5011** (perplexity **12.1965**) for the broad corpus. This is a character n-gram signal, not proof of neural-model improvement.

### High — GarhwaliBench's character baseline used the wrong default training view

The benchmark builder still defaulted to the broad 106,915-row training split
after the text-scaling and IndicBERT workflows had moved to the recommended
7,490-row Garhwali view. Its headline baseline and training-overlap check
therefore did not describe the strict modeling view.

**Fixed and verified:** the builder now defaults to
`text_recommended/train.jsonl`, records the training row count and SHA-256, and
the final release audit rejects a broad training view. On the same 398-row
candidate and with the same character-bigram scorer, recommended training gets
2.647741 cross-entropy / **14.122106 perplexity** versus 2.833217 /
17.000058 for broad training. The separate controlled text-scaling experiment
uses a different character n-gram scoring implementation and reports 10.209546
versus 12.196482 perplexity; those scales must not be compared directly. These
are automated-candidate results, not native-language accuracy.

### Medium — one external benchmark text repeats across source splits

XORQA has one exact `text_normalized` duplicate across source `train` and `dev`
(`indicgenbench_xorqa:train:64` and `indicgenbench_xorqa:dev:296`). Neither row
is in test. The builder and final audit now recompute and expose the overlap;
both source rows remain present and the audit emits a warning. FLORES and
CrossSum have zero such groups.

### High — release index status could remain “ready” after a failed audit

The release finalizer synchronized the release index before running the final audit. The index status could therefore still say `release_ready_with_public_rights_filtered_export` while the audit subsequently failed. The index validator did not compare release readiness with the final-audit status.

**Remediation verified:** the finalizer synchronizes the index again after auditing; index status is blocked unless the final audit passes, and the index validator enforces this relationship. The current public audit reports zero text-rights failures and zero included structured records without rights basis. The v0.1.1 release index records `final_audit_status: passed` and `status: release_ready_with_public_rights_filtered_export`.

### High — native accuracy and dialect quality remain unmeasured

There are no completed native-speaker adjudications. The current benchmark remains an automated candidate: 398 text records and 112 speaker-safe ASR rows. Only 29 of 28,755 parent texts carry an explicit dialect label. The fixed SraVaani comparison reports 42.761% WER and 17.606% CER, but the reference set itself has not been independently adjudicated. This is a material limitation on claims about correctness, dialect coverage, and ASR quality.

**Disposition:** native-speaker adjudication and dialect annotation are deferred at the project owner's direction. Automated integrity is checked separately. Keep the benchmark labeled as an automated candidate; do not call it gold or make definitive native-accuracy claims.

### Medium — benchmark and package integrity checks are now recomputed

The final audit checks all six benchmark inputs and recomputes artifact hashes, counts, exact text/audio-hash and identified-speaker overlap, plus one preserved XORQA train/dev warning. It also recomputes every `recommended_for_training` value from language, quality, flags, and public-rights evidence. That audit did not group sibling segments by parent document. A subsequent audit found 50 parent documents / 1,523 rows crossing historical text splits; the split builder now groups parents before duplicate reassignment, and a separate candidate reports zero parent-document crossings. The historical release remains unchanged. See the [parent-safe split audit](research/benchmark-parent-safe-split-audit-2026-09-28.md).

Package manifests carry per-shard SHA-256 values; both the final audit and cloud preflight recalculate them. The audit recalculates exported text IDs from content and catalog IDs from text hashes. Current audit counts are zero shard-hash failures and zero text-ID failures.

**Remaining:** use an independently signed or separately published manifest if tamper evidence across release artifacts is required. Current hashes detect shard drift relative to the package manifest; this same-manifest check does not protect against an actor replacing both the shard and its manifest entry.

### Resolved — release identity matches the reviewed repository state

The package and release index identify themselves as `garhwali-language-lab-v0.1.1`; annotated tag `v0.1.1` resolves to the reviewed release commit. The historical `v0.1.0` tag is unchanged. The exact reviewed commit passed the recorded release checks.

### Historical medium — “all-data” and “public-profile” are different products (v0.1.1 snapshot)

The V0.1.1 all-data package preserved 28,755 catalog text values, and that
snapshot's public profile redacted 24,566 values and omitted the 216 full
structured records. The current published v0.2.1 figures are stated in the
rights audit addendum at the top of this report. The PanLex license-classifier
defect is fixed; keep row-level terms visible in cards and manifests.

### Fixed low-severity reporting defect — public preflight carried an all-data run ID

The cloud preflight used a constant `garhwali-hf-all-data-cloud-validation-v0.1` run ID for both package profiles, so the saved public preflight was mislabeled despite declaring `manifest_profile: public`. The run ID now includes the manifest profile, a regression test checks both names, and the public preflight artifact was regenerated as `garhwali-hf-public-cloud-validation-v0.1`. The regenerated public preflight passes; it excludes structured records without compatible public-rights evidence.

## Remediation order

1. **Rights correctness:** the NC/ND classifier fix is implemented. The v0.2.1 public release exports factual/bibliographic projections for all 216 structured records, while full expressive text remains in all-data pending compatible rights evidence.
2. **Release metadata gates:** standardized source pointers/review status and fail-closed public-rights checks are implemented and pass for v0.1.1.
3. **Model-data quality:** strict training view and strict-default scripts are ready; run a neural comparison against historical broad-data results on fixed evaluations.
4. **Audit integrity:** benchmark hashes/counts/leakage, package shard hashes, text IDs, and training recommendations are recomputed; an independently signed release manifest remains optional hardening.
5. **Language validity:** native-speaker review and dialect annotation are deferred; retain automated-candidate language in this release and revisit before making native-accuracy claims.
6. **Version and release:** the reviewed commit and matching v0.1.1 tag are created locally; decide separately whether to publish. The repository code has an MIT license; data rights remain source-specific.

## Work started in this audit

- [x] Reproduced the CC-BY-NC-SA false acceptance in the rights classifier and found its current public-package effect.
- [x] Measured composition of the all-data text-training split and traced model experiments to the unfiltered split.
- [x] Confirmed structured metadata gaps against the generated preflight and audit code.
- [x] Fix the CC license classifier and add focused regression tests.
- [x] Normalize structured source pointers, explicit review status, and rights status without fabricating licenses.
- [x] Make release audits surface structured metadata and rights gaps as failures, not silent passes.
- [x] Rebuild packages and update final audit evidence; public profile excludes the 216 rights-pending structured records, while all-data retains them.
- [x] Build and compare a strict training view while preserving the historical broad-model experiment results.
- [x] Align the text-scaling experiment defaults with the checksum-frozen 398-row benchmark.
- [x] Tie release-index readiness to final-audit status.
- [x] Resolve geography evidence labels and shared literary capture IDs to source URLs or capture fingerprints; the structured-source traceability count is zero.
- [x] Refresh local release audit artifacts and package preflights; the v0.1.1 public audit and index pass. Latest full pytest run: 584/584 passed; documented unittest run: 582/582 passed. Run pytest with `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`.
- [x] Review online reuse terms for the 186 previously unassessed structured records and retain per-record findings; all remain in all-data and the public reference index.
- [x] Export all 216 structured records as a field-limited factual/bibliographic projection, without treating source references as rights clearance.
- [ ] Establish compatible reuse rights or obtain permission for the expressive full content of the 216 structured records.
- [ ] Re-evaluate neural text models using the recommended view and fixed strict validation/test artifacts.
- [x] Recompute exact benchmark hashes/counts/leakage and flag the XORQA source-split duplicate; the parent-document gap found afterward is fixed in a separate candidate, while the historical release remains unchanged.
- [x] Set IndicBERT head/LoRA defaults to recommended train/validation views with separate outputs.
- [x] Add package-manifest shard-hash and content-derived text-ID recomputation to the release audit and cloud preflight.
- [x] Make cloud preflight run IDs profile-specific and regenerate the public report.
- [x] Create the reviewed commit and matching v0.1.1 tag locally. Native-speaker review and dialect annotation are deferred.
- [x] Publish the complete all-data reference inventory with the public corpus package: 257,807 archive-row references, 590 sources, and 277,637 source links, with payload fields excluded.

## Limits of this pass

This code and generated-data audit was refreshed on 2026-09-28. The public and all-data package checks pass. The v0.1.1 benchmark audit verifies six inputs, reports zero exact text/audio/speaker overlap, and preserves one XORQA train/dev warning; it did not check parent-document sibling splits. A later audit found 50 parent documents / 1,523 rows crossing historical text splits; the corrected local candidate reports zero parent-document crossings and is not part of the release. The configured overlap scan reproduces 616 source-family groups, including 27 exact cross-split contexts. The nested-field review covers 10,571 fields and found 41 same-field cross-split groups (27 contexts, 6 English answer spans, 5 English oracle questions, 2 Garhwali translated-answer spans, and 1 Garhwali question), zero long exact training overlaps, and no long cross-language-label matches. A supplemental check found 50 short identical strings across English/Garhwali answer fields; 10 occur across source splits, all at 2–6 normalized characters, and remain common-answer candidates. The page-title audit found 54 exact source-page families crossing splits (134 rows), including 32 families with distinct context passages. The usage overlay now flags 138 retained rows for open diagnostics; repeated answer spans remain candidates. Semantic and cross-language independence remain unproven. See the [nested-overlap review](research/benchmark-nested-overlap-review-2026-09-27.md), [cross-language exact-overlap review](research/benchmark-cross-language-exact-overlap-2026-09-28.md), and [source-page family review](research/benchmark-source-page-families-2026-09-28.md).

The v0.2 draft validates eight views and 12,622 records with zero structural/integrity errors. Its deterministic local adapter retains all rows and verifies output hashes/counts. Versioned QA, summarization, and translation scorers verify exact IDs and retain missing-reference rows while excluding them from scores. Existing translation-memory predictions reproduce all 997 FLORES dev scores; a 2,000-resample record bootstrap reports descriptive copy-vs-memory intervals but does not account for source clusters. BM25 manifests reconcile all 500 XORQA dev query IDs; an additional 2,000-resample page-cluster bootstrap gives a paired character-minus-word Recall@10 delta of +0.2 percentage points (95% CI 0.0–0.6), conditional on the fixed all-split passage corpus. See [the retrieval uncertainty report](research/retrieval-source-page-cluster-uncertainty-2026-09-28.md). Saved ASR comparisons have a shared manifest for 269 validation rows, reproducing SraVaani at 43.3936% WER / 18.9252% CER and Whisper v0.2 at 78.0522% / 46.2980%. The three saved mT0 systems also have manifests for the same 130 validation IDs; their selected-ID digest matches the training report. Primary-reference diagnostics reproduce the saved report; current unreviewed alternate references shift chrF2 by +0.0019–0.0025, a sensitivity analysis rather than a quality gain. No inference ran and held-out rows were not scored. The mT0 adapter hashes and original sampling parameters are missing. These results do not establish native correctness or independent accuracy.

The overall metric contract remains draft; NLLB inference is blocked by absent local weights. The release index validates. Latest full pytest run: 584/584 passed; the documented unittest suite: 582/582 passed. Run pytest with `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`. The rebuilt compact bundle contains 131 files (2,585,212 bytes) with no hash or path errors. The XORQA retrieval miss analysis confirms all 500 dev gold passages are available in the fixed candidate corpus; word BM25 has 496 zero-score misses and character BM25 has 493 zero-score plus two rank-below-10 misses ([report](research/retrieval-miss-analysis-2026-09-28.md)). The mT0 generation-output audit finds substantial task-local repeated-answer concentration (up to 23/29 outputs for seed 43) but no empty/prompt-copy/control-token or selected Unicode anomalies; this is not a language-correctness finding ([report](research/generation-output-diagnostics-2026-09-28.md)). See [the Phase 2 adjudication record](research/benchmark-overlap-adjudication-2026-09-26.md), [the v0.2 schema contract](research/garhwali-bench-v0.2-schema-contract.md), and [the benchmark/model roadmap](research/benchmark-model-roadmap.md).

As of 2026-09-27, `rushilrawat/garhwali-speech` and `rushilrawat/garhwali-corpus` are public. The corpus repo is at commit [`a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2), contains all three reference tables and 11 draft shards, and exposes all 15 splits / 15 Parquet files. The Hub reports 682,718 rows across nine overlapping configs. All config previews, search, and filters pass; statistics work for seven configs, while the service returns HTTP 500 for `text` and `sravaani_drafts` because its histogram code fails on constant-valued columns. Locally, Datasets 5.0.1 loads all nine configs, and release audit/index checks pass. Full source payloads without compatible reuse terms remain unredistributed; these checks do not establish native-language correctness.
