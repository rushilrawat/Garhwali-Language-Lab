<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first language resource and research pipeline for Garhwali (gbm).**

Text, speech, folklore, scholarship, and local knowledge are organized into reusable datasets with source and quality information attached.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-827%20passing%20(last%20run%206%20Oct)-brightgreen.svg)](research/corpus-preparation-status.md)
[![Speech dataset](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
[![Corpus dataset](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)

</div>

## What we are building

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together, records where each item came from, and prepares reproducible text, speech, vocabulary, and evaluation resources for language research.

The aim is to make Garhwali easier to study and support future language tools. The current models and automated language labels are research baselines; they are not yet native-speaker validated.

## Current status

Live platform figures checked: **7 October 2026**. Internet Archive intake and source-evidence review updated **4 October 2026**. See the [current cross-platform metrics audit](research/current-platform-metrics-2026-10-07.md) for count definitions and live source links.

**Current release:** the mixed-source corpus has an additive v0.2.8 release
layer over the v0.2.7 source package. Its Hugging Face card now reports
**963,484 displayed rows** and **7.57 GB**; 778,157 rows are source/reference
tables, leaving 185,327 overlapping content-view rows. These are configuration
rows, not unique language examples. The new views reuse existing Meta
Omnilingual transcript rows; they add no newly collected source text. The main
unresolved data gap is rights evidence for 8,444 full texts retained locally.
See the [quality-release report](research/quality-screened-text-release-report-2026-10-06.md)
and [closeout report](finalreport.md) for exact scope and remaining work.

- **Text and training readiness:** the local parent-text inventory has 36,105 exact-unique records. The historical v0.2.7 `text` config has 18,598 records (291,914 whitespace-separated words; 1,373,045 characters); none in that config is marked recommended for general text training. An additive v0.2.8 view now exposes **1,841 sentence-length, machine-screened training candidates** (47,566 words) from existing Meta Omnilingual transcript rows. A separate **110-row short-utterance** config is context-only. This is a new usable view, not 1,841 newly collected texts or a native-reviewed gold corpus. See the [quality-release report](research/quality-screened-text-release-report-2026-10-06.md).
- **Quality-first text add-on:** data published at [Hugging Face commit `48f9107`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/48f9107d0285b3b3ec3c893303efb8a997cfc49b); the corrected, live card was read back at [commit `cf60b217`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cf60b217d9d3de045d81fb41d82514e29db2bf33). Online `load_dataset` checks returned 1,841 training rows and 110 context rows; both had zero blanks and zero exact duplicates. Every row retains source and CC BY 4.0 attribution, rights evidence, split and quality fields. Automated screening does not certify spelling, meaning, or dialect. The [rights decision](research/meta-omnilingual-training-rights-decision-2026-10-06.md) and [release roadmap](research/huggingface-kaggle-quality-release-roadmap-2026-10-06.md) document scope.
- **Text availability:** in the `catalog` config, 12,657 rows have text and 23,448 do not. A full public-package text-field scan found 15,004 of those values already exposed elsewhere (14,988 in `paharili_gbm` and 16 in other public fields); **8,444 distinct texts are not present in any public config** (2,936,664 whitespace-separated words). All 8,444 are retained locally with `rights_pending` status and have a source locator: 7,675 URLs are inline and 769 are recovered through `source_catalog`. Some locators identify a collection or dataset, not an exact page.
- **Speech:** the audio package has 113,363 rows (113,350 unique audio hashes; about 154.65 hours; 36.5 GB on the Hub), including 5,894 VAANI provider transcripts. The speech repository's additive text-only `asr_reference` view has **2,718** speaker-disjoint VAANI pairs (2,202 train / 373 validation / 143 test); none is native-adjudicated. The corpus's older `asr` view remains at 2,002 rows. An optional Meta `asr_meta_extra_train` view has 2,294 train-only pairs. The speech Viewer displays 118,375 rows because it totals the audio rows and both text indexes. SraVaani drafts remain unreviewed hypotheses: 104,500 non-empty of 104,534 rows. The audio payload remains at v0.2.1; the v0.2 update adds text indexes and documentation.
- **Knowledge records:** 216 geography, history, literature, songs, and research records are publicly listed as factual and bibliographic metadata.
- **Internet Archive (local only):** 119 verified payload files (6.01 GB), indexed as 4,011 page objects (3,983 non-empty OCR rows; 3,981 unique non-empty normalized texts) and 39 media files. A deeper review mapped 920 pages from three Garhwali-focused language/folklore studies and 432 non-empty pages from two English/contextual folklore sources, plus 8 empty OCR pages. It found one duplicated footer-only OCR pair, one normalization-empty row, a 1977 reprint catalogued as 1935, and conflicting or unverified rights claims. A separate map covers 722 scan pages from Chatak and Shailesh; Shailesh's contents map assigns 416 pages to 15 printed-page ranges with a verified +13 scan offset. Alternate Hindi OCR covers 29 flagged/empty pages; one formerly empty page yielded text. A text-free comparison and scan inspection found 11 high-, 3 medium-, and 15 low-priority pages, but no corrected text was promoted. The 39 media files pass file-hash and stream checks (15 audio-only, 24 video-with-audio; 14:09:25.531 total playback; 0 exact file duplicates). A sidecar scan found no transcript/caption candidates in 1,047 files listed by 31 Archive snapshots and no matching local sidecars. One 27.5-second local Whisper-tiny pilot produced a repetitive unreviewed draft; the model's existing test WER is 74.3%, so no more media was transcribed. Six catalog language fields claim Garhwali, but no media content has been verified and Garhwali speech hours remain unknown. All Archive material remains local; no Archive text or media was added to public releases. See the [source evidence review](research/internet-archive-priority-language-rights-review-2026-10-04.md), [media first pass](research/internet-archive-media-first-pass-2026-10-04.md), [source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md), and [quality/overlap audit](research/internet-archive-intake-quality-2026-10-04.md).
- **Hugging Face:** the corpus has two additive v0.2.8 configs over the v0.2.7 package. Its live page reports **963,484 displayed rows**, **7.57 GB**, 20 named configs, and 31 config/split views: 778,157 reference rows plus 185,327 overlapping content-view rows. The speech page reports **118,375 displayed rows** and **36.5 GB**, including 113,363 audio rows and the two text-only training indexes (2,718 VAANI references and 2,294 optional Meta train rows). Both Hub datasets are tagged for Garhwali (`gbm`). The corpus card remains `license: other` because terms vary across the full repository; the screened text configs identify their CC BY 4.0 source. See the [7 October live metrics audit](research/current-platform-metrics-2026-10-07.md), [v0.2.7 release report](research/huggingface-corpus-v0.2.7-release-2026-10-06.md), and [text-availability audit](research/huggingface-corpus-gap-resolution-2026-10-06.md).
- **Local storage:** `data/` currently occupies about **119.93 GiB** on disk. Its file-path sizes sum to 171.25 GB because versioned Hugging Face packages reuse hard-linked files; grouping identical file inodes yields 128.50 GB. The largest logical groups are Hub staging/releases (87.10 GB), processed/model artifacts (41.81 GB), VAANI source/audio (32.12 GB), and downloads (9.35 GB). These bytes include package snapshots, checkpoints, raw audio/video, and metadata; they are not unique Garhwali text. See the [storage and training-utility audit](research/huggingface-current-metrics-and-utility-2026-10-06.md).
- **Kaggle availability (checked 7 October 2026):** [Garhwali Screened Text Candidates](https://www.kaggle.com/datasets/rushilrawat1/garhwali-screened-text-candidates) is public at version 1 with 1,841 training texts (47,566 words) and 110 short context utterances; it mirrors existing Meta-derived Hugging Face views and adds no unique examples. [Garhwali ASR reference clips](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1) is private at version 2 with 2,718 existing VAANI audio/reference pairs (2,202 train / 373 validation / 143 test). It preserves all 2,002 earlier pairs and newly indexes 716 existing references. Its manifest preview works. The [baseline notebook](https://www.kaggle.com/code/rushilrawat1/garhwali-asr-baseline-reference-labels) was saved as version 3 with v2 input; it has not been run. See the [Kaggle ASR sync status](research/kaggle-asr-v0.2-sync-2026-10-07.md) and [live metrics audit](research/current-platform-metrics-2026-10-07.md). The broad corpus and speech-metadata Kaggle packages remain local only.
- **Benchmark and models:** the benchmark is still a local draft. A 5 October rights/provenance audit confirms the 3,847 external task rows carry source IDs, attribution, and hashed snapshots; provider use labels keep them evaluation-only. The 2,077 recommended text rows already marked component-compatible are 1,793 Garhwali Open Bible Stories records and 284 1916 LSI records; the other 8,265 rows still need item/component decisions. **All 14,703 benchmark view rows remain uncleared for public upload.** The same audit identifies exact citation fixes for Tatoeba and Wikimedia/Wiktionary records. On 241 Whisper-compatible Meta validation clips, one training epoch lowered Whisper-tiny v0.2 from 93.44% to 89.32% WER and from 70.52% to 68.50% CER; the older local v0.1 scored 95.37% / 71.88% on the same clips. These are development results; Meta test remains unscored and no task has independent-final eligibility. See the [rights/provenance audit](research/benchmark-rights-provenance-audit-2026-10-05.md), [adaptation report](research/meta-omnilingual-asr-adaptation-2026-10-05.md), [lineage refresh](research/model-lineage-refresh-2026-10-05.md), [Meta development report](research/meta-omnilingual-asr-validation-2026-10-04.md), and [VAANI split report](research/vaani-official-split-lineage-2026-10-04.md).

The previous weighted completion percentages were last estimated on 30
September and are not a current measure. The evidence-based closeout is: corpus
v0.2.8 and speech v0.2.1 are public; the benchmark is local and rights-uncleared;
independent-final eligibility is **0/5** task areas; native-language and
dialect review remain deferred; and the 8,444-text public-content gap remains
pending source-specific rights evidence. These are release-state facts, not
language-accuracy scores.

See the [license policy](LICENSE_POLICY.md), [corpus status](research/corpus-preparation-status.md), [Hugging Face quality roadmap](research/huggingface-dataset-quality-roadmap.md), and [final review](finalreport.md) for the detailed rights approach, measures, evidence, and limits.

## Corpus scale

The figures below separate local source inventory, public language content,
metadata references, and actual training recommendation. Configuration views
overlap. The Hub's combined viewer row count is not a count of unique or
training-ready examples. The corrected Hugging Face card was read back from
the live repository and declares 20 named configs and 31 config/split views.
The historical Viewer check before v0.2.8 found 29 split views and 29 Parquet
exports. Current repository totals are listed below.

<!-- AUTO-CORPUS-METRICS:START -->
| Metric | Current measured value |
| --- | ---: |
| Local exact-unique parent texts / whitespace-separated words | 36,105 / 4,023,979 |
| v0.2.7 `text` rows / words / characters | 18,598 / 291,914 / 1,373,045 |
| v0.2.7 `text` rows marked recommended for general training | **0 of 18,598** |
| v0.2.7 `text_expansion` / `text_resources` rows marked recommended | **0 of 1,737 / 0 of 475** |
| v0.2.8 `screened_meta_gbm` rows / words | **1,841 / 47,566** (experimental; automated, unreviewed) |
| v0.2.8 `short_utterances_meta_gbm` rows | **110** (context-only) |
| Corpus `asr` config rows / words | 2,002 / 36,228 (unreviewed; older view) |
| Speech `asr_reference` rows / splits | 2,718 (2,202 train / 373 validation / 143 test; unreviewed) |
| Optional Meta `asr_meta_extra_train` rows | 2,294 (train-only; unreviewed) |
| Experimental PahariLI rows / words | 14,988 / 236,566 (origins and labels unresolved/unreviewed) |
| Non-empty SraVaani machine drafts / total draft rows | 104,500 / 104,534 (not ground truth) |
| Public catalog rows with text / blank in `catalog.text` | 12,657 / 23,448 |
| Blank-catalog values found elsewhere publicly / full texts not in any public config | 15,004 / 8,444 |
| Public content-config view rows (overlapping) | 185,327 |
| Public source/reference-table view rows (not training examples) | 778,157 (80.8% of displayed total) |
| Hub corpus displayed rows / total file-size display | 963,484 / 7.57 GB |
| Hub speech displayed rows / total file-size display | 118,375 / 36.5 GB (includes text-only indexes) |
<!-- AUTO-CORPUS-METRICS:END -->

The speech audio configs contain 113,363 rows, 113,350 unique audio hashes,
and 154.65 hours. The speech repository's current speaker-disjoint index has
2,718 VAANI reference rows; its optional Meta training index has 2,294 rows.
The corpus's separate older `asr` config remains 2,002 rows. Only 5,894 VAANI
recordings have provider transcripts. None of these references has native
adjudication, and SraVaani drafts are not ground truth. Local `data/`
occupies about 119.93 GiB; file-path sizes and hard-linked package copies are
explained in the [current metrics audit](research/huggingface-current-metrics-and-utility-2026-10-06.md).
Whitespace-separated word counts are storage statistics, not linguistic
tokenization.

## Project timeline

| Stage | Milestone |
| --- | --- |
| **v0.1.x** | Established the first reproducible corpus and release pipeline. |
| **v0.2.0** | Added deduplicated Garhwali-only sources, established the first public corpus and reproducible preparation workflow, and expanded benchmark/model research; the frozen snapshot remains available. |
| **v0.2.1 — 1 Oct 2026** | Follow-up release: added 164 exact-new texts, resolved more public-profile rights bases, listed factual metadata for all 216 structured records, published the speech companion, and added common quality/rights fields, a stable schema, exact-count quick-start, and searchable lexicon example. Earlier files remain available. |
| **v0.2.3 — 2 Oct 2026** | Added a deduplicated `text_resources` view with 246 existing records under recorded row-level redistribution terms; no source records or earlier release files were removed. Viewer Parquet indexing was initially delayed. |
| **v0.2.4 — 5 Oct 2026** | Added recovered contributor attribution for 36 Tatoeba sentence records and immutable revision/history links for 319 Wikimedia/Wiktionary records. No source text changed; previous paths remain. |
| **v0.2.5 — 5 Oct 2026** | Kept every text value while routing 1,308 core and 363 expansion rows linked to upstream held-out sources into a public `source_overlap` split. Viewer indexing was queued after the upload; the schema repair and final Viewer state are recorded in the v0.2.6 report. |
| **v0.2.6 — 5 Oct 2026** | Published an additive 53-path corpus package preserving v0.2.5 text values and correcting VAANI transcript-source and held-out-split provenance. Follow-up cards declare stable `text` and `text_resources` schemas plus all three reference tables; all 26 splits and Parquet outputs now load in Hugging Face Dataset Viewer. |
| **v0.2.7 — 6 Oct 2026** | Added a separately labeled `paharili_gbm` config: 14,988 normalized-unique sentences from 15,000 upstream Garhwali-labeled rows, with normalized duplicates handled and four train/test overlap groups isolated. PahariLI source origins and language labels remain unresolved/unreviewed; prior release files were preserved. |
| **v0.2.8 — 6 Oct 2026** | Added two purpose-labeled Meta Omnilingual transcript views: 1,841 sentence-length training candidates and 110 short context rows, with CC BY 4.0 attribution, source/split lineage, and quality flags. These rows were already present in the v0.2.7 `text`/`text_expansion` views; v0.2.8 adds a clean training surface, not 1,951 newly sourced unique texts. |

Release notes are concise; source-specific reuse terms are summarized in [Data and reuse](#data-and-reuse) and the [license policy](LICENSE_POLICY.md).

## Hugging Face datasets

- [**Garhwali Corpus**](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) — public on v0.2.8, with text, vocabulary, source references, factual knowledge records, the PahariLI text-classification config, and purpose-labeled `screened_meta_gbm` / `short_utterances_meta_gbm` views. Content carries source-specific terms, not one blanket license; earlier release files remain available.
- [**Garhwali Speech**](https://huggingface.co/datasets/rushilrawat/garhwali-speech) — audio package public on v0.2.1 with additive v0.2 text-only `asr_reference` (2,718 VAANI rows) and `asr_meta_extra_train` (2,294 train-only Meta rows) indexes. Language tag: Garhwali (`gbm`). Audio and source transcript history remain separate from the training indexes.

The datasets are separate because speech and text have different formats, sources, and reuse terms. The Hub release cards and manifests describe their exact contents.

For a copy-paste loading example, exact configuration counts, pandas/DuckDB
recipes, and the first searchable vocabulary tool, see the
[developer quick start](docs/DEVELOPER_QUICKSTART.md). The common record fields
and per-configuration payload schema are described in the
[dataset schema](docs/DATASET_SCHEMA.md). The v0.2.1 release introduced common
rights and quality fields; v0.2.7 adds PahariLI provenance and its explicit
unresolved-origin and unreviewed-language caveats, while v0.2.8 adds an
experimental clean text view with explicit source attribution. The guide labels each config,
reuse status, and overlapping row counts clearly.

## How to work with the project

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pipeline.txt
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

After the Hugging Face staging packages are available locally, rebuild the
Kaggle-ready CSV exports with:

```bash
.venv/bin/python scripts/build_kaggle_release.py
```

This writes ignored package files under `data/kaggle/`; it does not upload or
publish them.

With the source data available locally, rebuild derived corpus views with:

```bash
.venv/bin/python scripts/refresh_corpus_after_ingestion.py
```

The [pipeline guide](PIPELINE.md) covers ingestion and refresh commands. Raw downloads, PDFs, caches, and generated data are excluded from Git; see [incoming PDF guidance](incoming/pdfs/README.md) before adding scans.

## Data and reuse

Each source has its own provenance and reuse terms. Public access alone does not grant redistribution rights, and the project does not claim one license for all collected material. The catalog's 23,448 blank text fields are not all absent from the public corpus: 15,004 matching values appear elsewhere; 8,444 distinct texts are local-only pending rights review. All 8,444 have a source locator (7,675 inline URLs and 769 via `source_catalog`); some locators point only to a collection or dataset, not an exact work or page. PahariLI text is separately published in v0.2.7 with unresolved sentence-origin rights and unreviewed Garhwali labels clearly recorded. See [LICENSE_POLICY.md](LICENSE_POLICY.md), [ATTRIBUTION.md](ATTRIBUTION.md), and the [closeout text-access audit](research/huggingface-corpus-gap-resolution-2026-10-06.md).

## Where to read next

- [Documentation index](docs/README.md) — project docs and research reports.
- [Project file map](PROJECT_FILE_MAP.md) — repository structure.
- [Benchmark and model roadmap](research/benchmark-model-roadmap.md) — planned research stages and release gates.
- [Final report](finalreport.md) — current audit findings and remaining issues.
- [Deep-dive audit](DEEP_DIVE_FINAL_AUDIT.md) — code, data, and release review.
- [Source catalog](sources/online/deep-search-catalog.md) — collected and investigated Garhwali sources.

## Contributions

Source leads, corrections, and review contributions are welcome. Please include the source, relevant rights information, and dialect or regional context when known. The [review guide](review/README.md) explains the current workflow.
