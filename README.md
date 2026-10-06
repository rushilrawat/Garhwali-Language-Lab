<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first language resource and research pipeline for Garhwali (gbm).**

Text, speech, folklore, scholarship, and local knowledge are organized into reusable datasets with source and quality information attached.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-803%20passing-brightgreen.svg)](research/corpus-preparation-status.md)
[![Speech dataset](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
[![Corpus dataset](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)

</div>

## What we are building

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together, records where each item came from, and prepares reproducible text, speech, vocabulary, and evaluation resources for language research.

The aim is to make Garhwali easier to study and support future language tools. The current models and automated language labels are research baselines; they are not yet native-speaker validated.

## Current status

Release figures last checked: **5 October 2026**. Internet Archive intake and source-evidence review updated **4 October 2026**.

- **Text:** the local corpus contains 36,105 exact-unique parent texts. The v0.2.6 public profile contains 12,657 full-text catalog records and 23,448 metadata-only records under the sources' current reuse terms. Its segment-oriented `text` view has 18,598 rows: 15,664 train, 1,305 source-overlap, 884 validation, and 745 test. The local all-data profile retains the full text inventory.
- **Speech:** the separate public dataset has 113,363 audio rows (about 154.65 hours), including 5,894 VAANI provider transcripts. The VAANI train/validation/test counts split all 110,436 audio rows; the linked corpus offers a narrower 2,002-row strict ASR view. SraVaani produced 104,542 source rows, deduplicated to 104,534 unique audio hashes: 104,500 have non-empty unreviewed drafts and 34 are empty. Drafts are not ground truth. Its **v0.2.1** release is live.
- **Knowledge records:** 216 geography, history, literature, songs, and research records are publicly listed as factual and bibliographic metadata.
- **Internet Archive (local only):** 119 verified payload files (6.01 GB), indexed as 4,011 page objects (3,983 non-empty OCR rows; 3,981 unique non-empty normalized texts) and 39 media files. A deeper review mapped 920 pages from three Garhwali-focused language/folklore studies and 432 non-empty pages from two English/contextual folklore sources, plus 8 empty OCR pages. It found one duplicated footer-only OCR pair, one normalization-empty row, a 1977 reprint catalogued as 1935, and conflicting or unverified rights claims. A separate map covers 722 scan pages from Chatak and Shailesh; Shailesh's contents map assigns 416 pages to 15 printed-page ranges with a verified +13 scan offset. Alternate Hindi OCR covers 29 flagged/empty pages; one formerly empty page yielded text. A text-free comparison and scan inspection found 11 high-, 3 medium-, and 15 low-priority pages, but no corrected text was promoted. The 39 media files pass file-hash and stream checks (15 audio-only, 24 video-with-audio; 14:09:25.531 total playback; 0 exact file duplicates). A sidecar scan found no transcript/caption candidates in 1,047 files listed by 31 Archive snapshots and no matching local sidecars. One 27.5-second local Whisper-tiny pilot produced a repetitive unreviewed draft; the model's existing test WER is 74.3%, so no more media was transcribed. Six catalog language fields claim Garhwali, but no media content has been verified and Garhwali speech hours remain unknown. All Archive material remains local; no Archive text or media was added to public releases. See the [source evidence review](research/internet-archive-priority-language-rights-review-2026-10-04.md), [media first pass](research/internet-archive-media-first-pass-2026-10-04.md), [source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md), and [quality/overlap audit](research/internet-archive-intake-quality-2026-10-04.md).
- **Hugging Face:** corpus v0.2.6 is public at [data commit `bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1); its 53-path release payload is 907,215,611 bytes. The latest root and versioned cards at [commit `cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e) declare stable text schemas and all three reference tables. All planned release paths match sizes and hashes; the previous 348 paths remain, with only additive LFS tracking rules in `.gitattributes`. The full test suite has 803 passing tests and local preflight reports zero errors. Final live Viewer validation now lists all 26 expected splits and 26 Parquet outputs with no pending or failed jobs; preview, viewer, search, and filter are enabled. Sample rows load for text, text resources, and all three reference tables. Viewer statistics are unavailable, but that does not block dataset access. See the [v0.2.6 publication report](research/huggingface-corpus-v0.2.6-release-2026-10-05.md), [Viewer schema/card fix](research/huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md), [source-rights and lineage audit](research/huggingface-phase2-source-rights-lineage-audit-2026-10-05.md), and [preflight](research/huggingface-v0.2.6-candidate-preflight-2026-10-05.json).
- **Benchmark and models:** the benchmark is still a local draft. A 5 October rights/provenance audit confirms the 3,847 external task rows carry source IDs, attribution, and hashed snapshots; provider use labels keep them evaluation-only. The 2,077 recommended text rows already marked component-compatible are 1,793 Garhwali Open Bible Stories records and 284 1916 LSI records; the other 8,265 rows still need item/component decisions. **All 14,703 benchmark view rows remain uncleared for public upload.** The same audit identifies exact citation fixes for Tatoeba and Wikimedia/Wiktionary records. On 241 Whisper-compatible Meta validation clips, one training epoch lowered Whisper-tiny v0.2 from 93.44% to 89.32% WER and from 70.52% to 68.50% CER; the older local v0.1 scored 95.37% / 71.88% on the same clips. These are development results; Meta test remains unscored and no task has independent-final eligibility. See the [rights/provenance audit](research/benchmark-rights-provenance-audit-2026-10-05.md), [adaptation report](research/meta-omnilingual-asr-adaptation-2026-10-05.md), [lineage refresh](research/model-lineage-refresh-2026-10-05.md), [Meta development report](research/meta-omnilingual-asr-validation-2026-10-04.md), and [VAANI split report](research/vaani-official-split-lineage-2026-10-04.md).

Implementation scorecard (last measured 30 September 2026): **Corpus 88% · Benchmark 56% · Research Suite 66% · Models 39%**. These weighted work-completion estimates are not language-accuracy or data-quality scores.

See the [license policy](LICENSE_POLICY.md), [corpus status](research/corpus-preparation-status.md), [Hugging Face quality roadmap](research/huggingface-dataset-quality-roadmap.md), and [final review](finalreport.md) for the detailed rights approach, measures, evidence, and limits.

## Corpus scale

The figures below describe the **public v0.2.6 release**. Configurations and
reference tables overlap; they are not unique-example counts. The final live
check confirms all 26 split views and Parquet outputs, with sample previews
working for the core text and reference-table configs.

<!-- AUTO-CORPUS-METRICS:START -->
| Metric | garhwali-language-lab-v0.2.6 public release |
| --- | ---: |
| Source files / records before deduplication | 75 / 43,014 |
| Exact-unique parent texts | 36,105 |
| Characters / whitespace-separated tokens | 21,990,238 / 4,023,979 |
| Prepared segment occurrences / exact-unique segments | 220,034 / 200,548 |
| Public catalog rows with text / metadata-only | 12,657 full-text / 23,448 metadata-only |
| Main text config rows across splits | 18,598 |
| Public content-config rows (overlapping content-view rows) | 168,388 |
| Metadata-only reference-index rows | 355,537 |
<!-- AUTO-CORPUS-METRICS:END -->

The separate public speech dataset is v0.2.1: 113,363 rows, 113,350 unique
audio hashes, and about 154.65 hours. It is a speech release, so these audio
figures should not be added to the text-corpus counts. Whitespace-separated
token counts are storage statistics, not linguistic tokenization.

## Project timeline

| Stage | Milestone |
| --- | --- |
| **v0.1.x** | Established the first reproducible corpus and release pipeline. |
| **v0.2.0** | Added deduplicated Garhwali-only sources, established the first public corpus and reproducible preparation workflow, and expanded benchmark/model research; the frozen snapshot remains available. |
| **v0.2.1 — 1 Oct 2026** | Follow-up release: added 164 exact-new texts, resolved more public-profile rights bases, listed factual metadata for all 216 structured records, published the speech companion, and added common quality/rights fields, a stable schema, exact-count quick-start, and searchable lexicon example. Earlier files remain available. |
| **v0.2.3 — 2 Oct 2026** | Added a deduplicated `text_resources` view with 246 existing records under recorded row-level redistribution terms; no source records or earlier release files were removed. Viewer Parquet indexing was initially delayed. |
| **v0.2.4 — 5 Oct 2026** | Added recovered contributor attribution for 36 Tatoeba sentence records and immutable revision/history links for 319 Wikimedia/Wiktionary records. No source text changed; previous paths remain. |
| **v0.2.5 — 5 Oct 2026** | Kept every text value while routing 1,308 core and 363 expansion rows linked to upstream held-out sources into a public `source_overlap` split. A follow-up typed-schema card repair is live; Viewer indexing is being retried. |
| **v0.2.6 — 5 Oct 2026** | Published an additive 53-path corpus package preserving v0.2.5 text values and correcting VAANI transcript-source and held-out-split provenance. Follow-up cards declare stable `text` and `text_resources` schemas plus all three reference tables; all 26 splits and Parquet outputs now load in Hugging Face Dataset Viewer. |

Release notes are concise; source-specific reuse terms are summarized in [Data and reuse](#data-and-reuse) and the [license policy](LICENSE_POLICY.md).

## Hugging Face datasets

- [**Garhwali Corpus**](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) — public on v0.2.6, with text, vocabulary, source references, and factual knowledge records. Content carries source-specific terms, not one blanket license; earlier release files remain available.
- [**Garhwali Speech**](https://huggingface.co/datasets/rushilrawat/garhwali-speech) — public on v0.2.1, with separate VAANI and Meta Omnilingual configs, audio, transcript provenance, and split-safety fields. Earlier files remain available.

The datasets are separate because speech and text have different formats, sources, and reuse terms. The Hub release cards and manifests describe their exact contents.

For a copy-paste loading example, exact configuration counts, pandas/DuckDB
recipes, and the first searchable vocabulary tool, see the
[developer quick start](docs/DEVELOPER_QUICKSTART.md). The common record fields
and per-configuration payload schema are described in the
[dataset schema](docs/DATASET_SCHEMA.md). The v0.2.1 release introduced common
rights and quality fields; v0.2.6 retains them and adds corrected VAANI source
and held-out-split provenance. The guide labels the rights-filtered profile and
its overlapping row counts clearly.

## How to work with the project

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pipeline.txt
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

With the source data available locally, rebuild derived corpus views with:

```bash
.venv/bin/python scripts/refresh_corpus_after_ingestion.py
```

The [pipeline guide](PIPELINE.md) covers ingestion and refresh commands. Raw downloads, PDFs, caches, and generated data are excluded from Git; see [incoming PDF guidance](incoming/pdfs/README.md) before adding scans.

## Data and reuse

Each source has its own provenance and reuse terms. Public access alone does not grant redistribution rights, and the project does not claim one license for all collected material. Full texts without a compatible public basis remain in the local all-data package; public records retain source references and available metadata. See [LICENSE_POLICY.md](LICENSE_POLICY.md) and [ATTRIBUTION.md](ATTRIBUTION.md).

## Where to read next

- [Documentation index](docs/README.md) — project docs and research reports.
- [Project file map](PROJECT_FILE_MAP.md) — repository structure.
- [Benchmark and model roadmap](research/benchmark-model-roadmap.md) — planned research stages and release gates.
- [Final report](finalreport.md) — current audit findings and remaining issues.
- [Deep-dive audit](DEEP_DIVE_FINAL_AUDIT.md) — code, data, and release review.
- [Source catalog](sources/online/deep-search-catalog.md) — collected and investigated Garhwali sources.

## Contributions

Source leads, corrections, and review contributions are welcome. Please include the source, relevant rights information, and dialect or regional context when known. The [review guide](review/README.md) explains the current workflow.
