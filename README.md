<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first language resource and research pipeline for Garhwali (gbm).**

Text, speech, folklore, scholarship, and local knowledge are organized into reusable datasets with source and quality information attached.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-671%20pytest%20checks-brightgreen.svg)](research/corpus-preparation-status.md)
[![Speech dataset](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
[![Corpus dataset](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)

</div>

## What we are building

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together, records where each item came from, and prepares reproducible text, speech, vocabulary, and evaluation resources for language research.

The aim is to make Garhwali easier to study and support future language tools. The current models and automated language labels are research baselines; they are not yet native-speaker validated.

## Current status

Last checked: **1 October 2026**.

- **Text:** 32,072 exact-unique values are in the local corpus. The public Hugging Face corpus exposes 12,606 values under their recorded terms or narrow fact-only treatment; 19,466 full texts remain in the local all-data package pending a compatible public basis.
- **Speech:** the separate public speech dataset contains 113,363 rows, about 154.65 hours, across its current source configurations.
- **Knowledge records:** 216 geography, history, literature, songs, and research records are publicly listed as factual and bibliographic metadata.
- **Benchmark and models:** the benchmark is still a local draft. Independent accuracy claims and native-language validation are not complete.

Implementation scorecard (last measured 30 September 2026): **Corpus 88% · Benchmark 56% · Research Suite 66% · Models 39%**. These weighted work-completion estimates are not language-accuracy or data-quality scores.

See the [license policy](LICENSE_POLICY.md), [corpus status](research/corpus-preparation-status.md), and [final review](finalreport.md) for the detailed rights approach, evidence, and limits.

## Corpus scale

| Measure | Current figure |
| --- | ---: |
| Text source files / source rows | 49 / 34,505 |
| Exact-unique parent texts | 32,072 |
| Text size | 16,089,764 characters; 2,935,379 whitespace-separated tokens* |
| Prepared segments | 163,045 occurrences; 151,690 exact-unique segments |
| Public corpus content | 162,494 rows across 15 configs / 21 config-split views (overlapping, not unique) |
| Public text values | 12,606 included; 19,466 full texts not included in public content |
| Public corpus V2.1.0 release payload | 42 versioned files; 601,509,542 bytes (~573.6 MiB), plus the dataset card |
| Whole public corpus Hub repository | ~1.67 GB, as currently reported by Hugging Face |
| Local all-data text package | 51 files; 689,449,417 bytes (~657.5 MiB) |
| Local `data/` working directory | 77 GB on disk as of 1 Oct 2026 (30 GB VAANI, 22 GB processed, 21 GB HF cache, 3.2 GB downloads; variable) |
| Public speech dataset | 113,363 rows; 113,350 unique audio hashes; 154.65 hours; 16.91 GiB source audio (~18.2 GB on Hub) |
| Public metadata reference index | 300,915 archive references; 4,909 sources; 352,765 source links |

\* A whitespace count is a storage statistic, not linguistic tokenization. Segment, archive-reference, and package-view counts include different derived views and should not be added together as unique data. Package sizes describe the current text release; the separate speech package is larger and includes audio.

## Project timeline

| Stage | Milestone |
| --- | --- |
| **v0.1.x** | Established the first reproducible corpus and release pipeline. |
| **v0.2.0** | Added a deduplicated Garhwali-only source wave and expanded benchmark and model research. |
| **v2.0.0 — 30 Sep 2026** | Added 164 exact-new texts; the corpus reached 32,072 unique text values and gained a resumable ingestion workflow. |
| **v2.1.0 — 1 Oct 2026** | Added no new unique texts; made 6,864 more values public under reviewed bases and added metadata for all 216 structured records. Earlier release files remain available. |

The v2.1.0 entry is a short release note; source-specific reuse terms are summarized in [Data and reuse](#data-and-reuse) and the [license policy](LICENSE_POLICY.md).

## Public datasets

- [**Garhwali Corpus**](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) — text, vocabulary, source references, and factual knowledge records. Content carries source-specific terms; the whole corpus does not have one blanket license.
- [**Garhwali Speech**](https://huggingface.co/datasets/rushilrawat/garhwali-speech) — speech recordings and associated metadata in a separate dataset.

The two datasets are linked because speech and text have different formats, sources, and reuse terms. The latest release cards and manifests describe their exact contents.

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
