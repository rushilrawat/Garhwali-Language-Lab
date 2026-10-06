<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first language resource and research pipeline for Garhwali (gbm).**

Text, speech, folklore, scholarship, and local knowledge are organized into reusable datasets with source and quality information attached.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-820%20passing-brightgreen.svg)](research/corpus-preparation-status.md)
[![Speech dataset](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
[![Corpus dataset](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)

</div>

## What we are building

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together, records where each item came from, and prepares reproducible text, speech, vocabulary, and evaluation resources for language research.

The aim is to make Garhwali easier to study and support future language tools. The current models and automated language labels are research baselines; they are not yet native-speaker validated.

## Current status

Release figures last checked: **6 October 2026**. Internet Archive intake and source-evidence review updated **4 October 2026**.

**Project closeout:** active ingestion is paused at corpus v0.2.7. This pass
updated the documentation and reproducibility defaults; it did not add corpus
rows or change either Hugging Face data payload. The main unresolved data gap
is rights evidence for 8,444 full texts retained locally. See the
[closeout report](finalreport.md) for the full state and the
[gap-resolution audit](research/huggingface-corpus-gap-resolution-2026-10-06.md)
for the source-by-source work queue.

- **Text and training readiness:** the local parent-text inventory has 36,105 exact-unique records, but the public `text` config has 18,598 records (291,914 whitespace-separated words; 1,373,045 characters). **Zero are currently marked recommended for general text training.** The 1,737 `text_expansion` and 475 `text_resources` rows are also all marked not recommended for training. The 14,988 `paharili_gbm` rows are experimental language-identification material with unresolved item origins and unreviewed labels, not a general LM corpus. These are the actual training-readiness figures; config-view totals are not a substitute.
- **Text availability:** in the `catalog` config, 12,657 rows have text and 23,448 do not. A full public-package text-field scan found 15,004 of those values already exposed elsewhere (14,988 in `paharili_gbm` and 16 in other public fields); **8,444 distinct texts are not present in any public config** (2,936,664 whitespace-separated words). All 8,444 are retained locally with `rights_pending` status and have a source locator: 7,675 URLs are inline and 769 are recovered through `source_catalog`. Some locators identify a collection or dataset, not an exact page.
- **Speech:** the separate public dataset has 113,363 audio rows (about 154.65 hours; 36.5 GB total Hub file size), including 5,894 VAANI provider transcripts. Only 2,002 rows are in the stricter speaker-disjoint ASR view, and none is native-adjudicated. SraVaani produced 104,542 source rows, deduplicated to 104,534 unique audio hashes: 104,500 have non-empty unreviewed drafts and 34 are empty. Drafts are not ground truth. Its **v0.2.1** release is live.
- **Knowledge records:** 216 geography, history, literature, songs, and research records are publicly listed as factual and bibliographic metadata.
- **Internet Archive (local only):** 119 verified payload files (6.01 GB), indexed as 4,011 page objects (3,983 non-empty OCR rows; 3,981 unique non-empty normalized texts) and 39 media files. A deeper review mapped 920 pages from three Garhwali-focused language/folklore studies and 432 non-empty pages from two English/contextual folklore sources, plus 8 empty OCR pages. It found one duplicated footer-only OCR pair, one normalization-empty row, a 1977 reprint catalogued as 1935, and conflicting or unverified rights claims. A separate map covers 722 scan pages from Chatak and Shailesh; Shailesh's contents map assigns 416 pages to 15 printed-page ranges with a verified +13 scan offset. Alternate Hindi OCR covers 29 flagged/empty pages; one formerly empty page yielded text. A text-free comparison and scan inspection found 11 high-, 3 medium-, and 15 low-priority pages, but no corrected text was promoted. The 39 media files pass file-hash and stream checks (15 audio-only, 24 video-with-audio; 14:09:25.531 total playback; 0 exact file duplicates). A sidecar scan found no transcript/caption candidates in 1,047 files listed by 31 Archive snapshots and no matching local sidecars. One 27.5-second local Whisper-tiny pilot produced a repetitive unreviewed draft; the model's existing test WER is 74.3%, so no more media was transcribed. Six catalog language fields claim Garhwali, but no media content has been verified and Garhwali speech hours remain unknown. All Archive material remains local; no Archive text or media was added to public releases. See the [source evidence review](research/internet-archive-priority-language-rights-review-2026-10-04.md), [media first pass](research/internet-archive-media-first-pass-2026-10-04.md), [source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md), and [quality/overlap audit](research/internet-archive-intake-quality-2026-10-04.md).
- **Hugging Face:** corpus v0.2.7 is public at [commit `1f7b2ce`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/1f7b2ceed1b743412b75d6288757e1d2cadac9c4). The live Hub page reports 7.56 GB and 961,533 displayed rows. Of those rows, 778,157 (80.9%) are source/reference-table rows; 183,376 are overlapping content-config views, not unique training examples. The repository has 18 configs and 29 config/split views. The separate speech repository page reports 36.5 GB and 113,363 rows. The corpus card is `license: other` because reuse terms vary by source and row. The latest recorded live Viewer check reports all 29 split views and Parquet exports ready. See the [current metrics and utility audit](research/huggingface-current-metrics-and-utility-2026-10-06.md), [v0.2.7 release report](research/huggingface-corpus-v0.2.7-release-2026-10-06.md), and [text-availability audit](research/huggingface-corpus-gap-resolution-2026-10-06.md).
- **Local storage:** `data/` currently occupies about **119.93 GiB** on disk. Its file-path sizes sum to 171.25 GB because versioned Hugging Face packages reuse hard-linked files; grouping identical file inodes yields 128.50 GB. The largest logical groups are Hub staging/releases (87.10 GB), processed/model artifacts (41.81 GB), VAANI source/audio (32.12 GB), and downloads (9.35 GB). These bytes include package snapshots, checkpoints, raw audio/video, and metadata; they are not unique Garhwali text. See the [storage and training-utility audit](research/huggingface-current-metrics-and-utility-2026-10-06.md).
- **Kaggle packaging:** reproducible CSV exports are prepared locally: 17 corpus configs with 946,545 overlapping view rows, a content-free index for the 14,988 excluded PahariLI sentence rows, and a 113,363-row speech transcript/metadata companion. The Kaggle speech package does not duplicate audio; audio remains on Hugging Face. The generated packages are Git-ignored and are not published on Kaggle yet. See the [Kaggle release audit](research/kaggle-release-readiness-2026-10-06.md).
- **Benchmark and models:** the benchmark is still a local draft. A 5 October rights/provenance audit confirms the 3,847 external task rows carry source IDs, attribution, and hashed snapshots; provider use labels keep them evaluation-only. The 2,077 recommended text rows already marked component-compatible are 1,793 Garhwali Open Bible Stories records and 284 1916 LSI records; the other 8,265 rows still need item/component decisions. **All 14,703 benchmark view rows remain uncleared for public upload.** The same audit identifies exact citation fixes for Tatoeba and Wikimedia/Wiktionary records. On 241 Whisper-compatible Meta validation clips, one training epoch lowered Whisper-tiny v0.2 from 93.44% to 89.32% WER and from 70.52% to 68.50% CER; the older local v0.1 scored 95.37% / 71.88% on the same clips. These are development results; Meta test remains unscored and no task has independent-final eligibility. See the [rights/provenance audit](research/benchmark-rights-provenance-audit-2026-10-05.md), [adaptation report](research/meta-omnilingual-asr-adaptation-2026-10-05.md), [lineage refresh](research/model-lineage-refresh-2026-10-05.md), [Meta development report](research/meta-omnilingual-asr-validation-2026-10-04.md), and [VAANI split report](research/vaani-official-split-lineage-2026-10-04.md).

The previous weighted completion percentages were last estimated on 30
September and are not a current measure. The evidence-based closeout is: corpus
v0.2.7 and speech v0.2.1 are public; the benchmark is local and rights-uncleared;
independent-final eligibility is **0/5** task areas; native-language and
dialect review remain deferred; and the 8,444-text public-content gap remains
pending source-specific rights evidence. These are release-state facts, not
language-accuracy scores.

See the [license policy](LICENSE_POLICY.md), [corpus status](research/corpus-preparation-status.md), [Hugging Face quality roadmap](research/huggingface-dataset-quality-roadmap.md), and [final review](finalreport.md) for the detailed rights approach, measures, evidence, and limits.

## Corpus scale

The figures below separate local source inventory, public language content,
metadata references, and actual training recommendation. Configuration views
overlap. The Hub's combined viewer row count is not a count of unique or
training-ready examples. The latest recorded live Viewer check found 29 split
views and 29 Parquet exports, with preview and sample rows working; the current
live repository totals are listed separately below.

<!-- AUTO-CORPUS-METRICS:START -->
| Metric | Current measured value |
| --- | ---: |
| Local exact-unique parent texts / whitespace-separated words | 36,105 / 4,023,979 |
| Public `text` rows / words / characters | 18,598 / 291,914 / 1,373,045 |
| `text` rows marked recommended for general training | **0 of 18,598** |
| `text_expansion` / `text_resources` rows marked recommended for training | **0 of 1,737 / 0 of 475** |
| Strict speaker-disjoint ASR reference rows / words | 2,002 / 36,228 (unreviewed) |
| Experimental PahariLI rows / words | 14,988 / 236,566 (origins and labels unresolved/unreviewed) |
| Non-empty SraVaani machine drafts / total draft rows | 104,500 / 104,534 (not ground truth) |
| Public catalog rows with text / blank in `catalog.text` | 12,657 / 23,448 |
| Blank-catalog values found elsewhere publicly / full texts not in any public config | 15,004 / 8,444 |
| Public content-config view rows (overlapping) | 183,376 |
| Public source/reference-table view rows (not training examples) | 778,157 (80.9% of displayed total) |
| Hub corpus displayed rows / total file-size display | 961,533 / 7.56 GB |
| Hub speech displayed rows / total file-size display | 113,363 / 36.5 GB |
<!-- AUTO-CORPUS-METRICS:END -->

The speech package contains 113,363 rows, 113,350 unique audio hashes, and
154.65 hours. Only 5,894 VAANI recordings have provider transcripts, and the
strict speaker-disjoint ASR view contains 2,002 unreviewed transcript/audio
rows. Do not describe every audio row as a supervised pair. Local `data/`
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

Release notes are concise; source-specific reuse terms are summarized in [Data and reuse](#data-and-reuse) and the [license policy](LICENSE_POLICY.md).

## Hugging Face datasets

- [**Garhwali Corpus**](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) — public on v0.2.7, with text, vocabulary, source references, factual knowledge records, and the new PahariLI text-classification config. Content carries source-specific terms, not one blanket license; earlier release files remain available.
- [**Garhwali Speech**](https://huggingface.co/datasets/rushilrawat/garhwali-speech) — public on v0.2.1, with separate VAANI and Meta Omnilingual configs, audio, transcript provenance, and split-safety fields. Earlier files remain available.

The datasets are separate because speech and text have different formats, sources, and reuse terms. The Hub release cards and manifests describe their exact contents.

For a copy-paste loading example, exact configuration counts, pandas/DuckDB
recipes, and the first searchable vocabulary tool, see the
[developer quick start](docs/DEVELOPER_QUICKSTART.md). The common record fields
and per-configuration payload schema are described in the
[dataset schema](docs/DATASET_SCHEMA.md). The v0.2.1 release introduced common
rights and quality fields; v0.2.7 adds PahariLI provenance and its explicit
unresolved-origin and unreviewed-language caveats. The guide labels each config,
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
