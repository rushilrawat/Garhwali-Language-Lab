<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first language resource and research pipeline for Garhwali (gbm).**

Text, speech, folklore, scholarship, and local knowledge are organized into reusable datasets with source and quality information attached.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-718%20passing-brightgreen.svg)](research/corpus-preparation-status.md)
[![Speech dataset](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
[![Corpus dataset](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)

</div>

## What we are building

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together, records where each item came from, and prepares reproducible text, speech, vocabulary, and evaluation resources for language research.

The aim is to make Garhwali easier to study and support future language tools. The current models and automated language labels are research baselines; they are not yet native-speaker validated.

## Current status

Release figures last checked: **2 October 2026**. Internet Archive intake and source-evidence review updated **4 October 2026**.

- **Text:** 32,072 exact-unique values are in the local corpus. The public Hugging Face profile exposes 12,606 values under their recorded terms or narrow fact-only treatment; 19,466 full texts remain outside public text content pending a compatible basis. The public corpus repository is live on **v0.2.3**.
- **Speech:** the separate public dataset has 113,363 audio rows (about 154.65 hours), including 5,894 VAANI provider transcripts. The VAANI train/validation/test counts split all 110,436 audio rows; the linked corpus offers a narrower 2,002-row strict ASR view. SraVaani produced 104,542 source rows, deduplicated to 104,534 unique audio hashes: 104,500 have non-empty unreviewed drafts and 34 are empty. Drafts are not ground truth. Its **v0.2.1** release is live.
- **Knowledge records:** 216 geography, history, literature, songs, and research records are publicly listed as factual and bibliographic metadata.
- **Internet Archive (local only):** 119 verified payload files (6.01 GB), indexed as 4,011 page objects (3,983 non-empty OCR rows; 3,981 unique non-empty normalized texts) and 39 media files. A deeper review mapped 920 pages from three Garhwali-focused language/folklore studies and 432 non-empty pages from two English/contextual folklore sources, plus 8 empty OCR pages. It found one duplicated footer-only OCR pair, one normalization-empty row, a 1977 reprint catalogued as 1935, and conflicting or unverified rights claims. A scholarly source confirms Chatak's work contains Garhwali epics followed by Hindi translations, but page-level language and OCR accuracy remain unverified. No Archive text was added to public releases. See the [source evidence review](research/internet-archive-priority-language-rights-review-2026-10-04.md), [source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md), and [quality/overlap audit](research/internet-archive-intake-quality-2026-10-04.md).
- **Hugging Face fast-track:** corpus v0.2.3 is public at [commit `76dac8d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76dac8de70d37595c7af9a3c642c81ece615ec5d). It adds a `text_resources` config with **246** additional normalized-unique Garhwali records (40,759 words; 183,484 characters) already present in the catalog. These are newly surfaced resources, not new source acquisition; none is recommended for training or evaluation. The package has **827,450** overlapping-view rows (164,387 content/config rows plus 663,063 reference/join rows). Preflight passes with zero errors, and a direct streaming read returns all 246 rows. Dataset Viewer Parquet is returning HTTP 500, so Viewer confirmation remains pending.
- **Benchmark and models:** the benchmark is still a local draft. Independent accuracy claims and native-language validation are not complete.

Implementation scorecard (last measured 30 September 2026): **Corpus 88% · Benchmark 56% · Research Suite 66% · Models 39%**. These weighted work-completion estimates are not language-accuracy or data-quality scores.

See the [license policy](LICENSE_POLICY.md), [corpus status](research/corpus-preparation-status.md), [Hugging Face quality roadmap](research/huggingface-dataset-quality-roadmap.md), and [final review](finalreport.md) for the detailed rights approach, measures, evidence, and limits.

## Corpus scale

| Measure | Current figure |
| --- | ---: |
| Text source files / source rows | 49 / 34,505 |
| Exact-unique parent texts | 32,072 |
| Text size | 16,089,764 characters; 2,935,379 whitespace-separated tokens* |
| Prepared segments | 163,045 occurrences; 151,690 exact-unique segments |
| Rights-filtered corpus profile | 164,387 rows across 14 content configs / 20 config-split views, plus 663,063 reference/join rows (overlapping; public v0.2.3) |
| Public text values | 12,606 included; 19,466 full texts not included in public content |
| Hub corpus v0.2.3 release payload | 48 files including the root card; 806,624,937 bytes (~769.0 MiB) |
| Whole corpus Hub repository | 4,073,629,254 logical file bytes (~4.07 GB) across retained versioned releases |
| Local all-data text package | 51 files; 689,449,417 bytes (~657.5 MiB) |
| Local `data/` working directory | 77 GB on disk as of 1 Oct 2026 (30 GB VAANI, 22 GB processed, 21 GB HF cache, 3.2 GB downloads; variable) |
| Public speech dataset | v0.2.1: 113,363 rows; 113,350 unique audio hashes; 154.65 hours; 16.915 GiB source audio; 18.24 GB release files |
| Whole speech Hub repository | 36,468,214,621 logical file bytes (~36.47 GB), including earlier files and the additive v0.2.1 release; Xet may deduplicate shared chunks |
| Metadata reference index | 302,532 archive references; 5,019 sources; 355,294 source links |

\* A whitespace count is a storage statistic, not linguistic tokenization. Segment, archive-reference, and package-view counts include different derived views and should not be added together as unique data. Package sizes describe the current text release; the separate speech package is larger and includes audio.

## Project timeline

| Stage | Milestone |
| --- | --- |
| **v0.1.x** | Established the first reproducible corpus and release pipeline. |
| **v0.2.0** | Added deduplicated Garhwali-only sources, established the first public corpus and reproducible preparation workflow, and expanded benchmark/model research; the frozen snapshot remains available. |
| **v0.2.1 — 1 Oct 2026** | Follow-up release: added 164 exact-new texts, resolved more public-profile rights bases, listed factual metadata for all 216 structured records, published the speech companion, and added common quality/rights fields, a stable schema, exact-count quick-start, and searchable lexicon example. Earlier files remain available. |
| **v0.2.3 — 2 Oct 2026** | Added a deduplicated `text_resources` view with 246 existing records under recorded row-level redistribution terms; no source records or earlier release files were removed. Viewer Parquet check remains pending because of a Hugging Face 500. |

Release notes are concise; source-specific reuse terms are summarized in [Data and reuse](#data-and-reuse) and the [license policy](LICENSE_POLICY.md).

## Hugging Face datasets

- [**Garhwali Corpus**](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) — public on v0.2.3, with text, vocabulary, source references, and factual knowledge records. Content carries source-specific terms, not one blanket license; earlier release files remain available.
- [**Garhwali Speech**](https://huggingface.co/datasets/rushilrawat/garhwali-speech) — public on v0.2.1, with separate VAANI and Meta Omnilingual configs, audio, transcript provenance, and split-safety fields. Earlier files remain available.

The datasets are separate because speech and text have different formats, sources, and reuse terms. The Hub release cards and manifests describe their exact contents.

For a copy-paste loading example, exact configuration counts, pandas/DuckDB
recipes, and the first searchable vocabulary tool, see the
[developer quick start](docs/DEVELOPER_QUICKSTART.md). The common record fields
and per-configuration payload schema are described in the
[dataset schema](docs/DATASET_SCHEMA.md). The corpus has been rebuilt locally as
v0.2.1 with common rights and quality fields on every record. The guide labels
the rights-filtered profile and its overlapping row counts clearly.

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
