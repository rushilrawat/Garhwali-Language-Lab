<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-first corpus and research project for Garhwali (gbm).**

We organize Garhwali text, speech, folklore, scholarship, and local knowledge into reusable resources with source, rights, and quality information.

[![Python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-832%20passing%20(last%20run%208%20Oct)-brightgreen.svg)](project-status/corpus-preparation-status.md)
[![Hugging Face corpus](https://img.shields.io/badge/Hugging%20Face-corpus-brightgreen?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
[![Hugging Face speech](https://img.shields.io/badge/Hugging%20Face-speech-yellow?logo=huggingface)](https://huggingface.co/datasets/rushilrawat/garhwali-speech)

</div>

## About

Garhwali resources are scattered across archives, books, websites, research, and speech collections. This project brings them together and prepares reproducible text, speech, vocabulary, and evaluation resources for language research and future language tools.

Primary language identifier: **garhwali:gbm** (Garhwali, ISO 639-3). English (`eng`) appears in documentation, glosses, and translation/evaluation references; Hindi (`hin`) appears in bilingual glosses and some translation/evaluation material. Kumaoni (`kfy`) occurs in a small number of mixed-source entries, not as a standalone training subset. This is a Garhwali-focused corpus, not a balanced multilingual dataset; use row-level language and quality labels when selecting data.

## Current versions

Platform versions below were checked on **8 October 2026**. This table shows current versions only; dated release reports preserve earlier history.

| Resource | Current version | What it contains |
| --- | --- | --- |
| [Hugging Face corpus](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) | **v0.2.8** | Mixed-source corpus with provenance and rights fields, plus purpose-labeled text views. |
| [Hugging Face speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech) | **audio v0.2.1; training views v0.2** | VAANI and Meta audio, with separate text-only indexes for existing ASR references. |
| [Kaggle screened text](https://www.kaggle.com/datasets/rushilrawat1/garhwali-screened-text-candidates) | **v1 — public** | 1,841 screened training candidates and 110 short context rows. |
| [Kaggle ASR references](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1) | **v2 — private** | 2,718 existing VAANI audio/reference pairs with train, validation, and test splits. |
| [Kaggle ASR notebook](https://www.kaggle.com/code/rushilrawat1/garhwali-asr-baseline-reference-labels) | **v3 — saved, not run** | Baseline notebook configured to use the v2 reference dataset. |

## Training starting points

For fresh-clone setup and runnable CPU-first text training, start at the
[developer quick start](docs/DEVELOPER_QUICKSTART.md). Its ASR section links to
a Kaggle Whisper fine-tuning notebook. Both examples use existing data and
unreviewed labels; their loss and WER/CER outputs are experimental, not
independent quality claims. See the [developer readiness checklist](docs/DEVELOPER_READINESS.md)
for the current release boundary.

### Text experiments

The corpus offers **1,841 automatically screened sentence-length candidates** (47,566 whitespace-separated words) in the `screened_meta_gbm` configuration. These transcript values already appeared in earlier corpus views: the new configuration makes them easier to select, but adds no unique text examples. A separate 110-row `short_utterances_meta_gbm` configuration is for context and is not recommended for general language-model training.

    from datasets import load_dataset

    train = load_dataset(
        "rushilrawat/garhwali-corpus",
        "screened_meta_gbm",
        split="train",
    )

### Speech recognition experiments

The speech dataset contains **113,363 audio/source rows**, **113,350 unique audio hashes**, and about **154.65 hours**. Its `asr_reference` index points to 2,718 existing VAANI clips and transcripts: **2,202 train / 373 validation / 143 test**. Join the index to audio using `source_record_id`; see the [speech training guide](https://huggingface.co/datasets/rushilrawat/garhwali-speech/blob/main/training_views/v0.2/TRAINING_GUIDE.md).

The optional `asr_meta_extra_train` index adds 2,294 train-only Meta references. Do not use it for evaluation. VAANI and Meta references are upstream labels, not native-speaker-adjudicated ground truth. SraVaani outputs are machine-generated hypotheses and are not used as reference labels.

## Current scale and limits

The Hugging Face corpus page displays **963,484 rows** and **7.57 GB** across 20 configurations and 31 config/split views. The display includes **778,157 source/reference rows** and **185,327 overlapping content-view rows**. These are view counts, not unique passages or training examples. The speech page displays **118,375 rows** because it totals the 113,363 audio/source rows and both text-only indexes.

Source terms vary; there is no single license for the entire corpus. Check each source and the row-level rights fields before reuse. The main catalog gap is **8,444 distinct full texts** retained locally pending rights evidence; they are not part of the public corpus. See the [license policy](LICENSE_POLICY.md), [attribution guide](ATTRIBUTION.md), and [current metrics audit](project-status/current-platform-metrics-2026-10-08.md).

Automated screening does not verify Garhwali spelling, meaning, dialect, or transcript accuracy. The benchmark remains a local draft, and independent-final evaluation eligibility is **0 of 5 task areas**. Existing model scores are development results, not independent confirmation. See the [model roadmap](research/benchmark-model-roadmap.md) and [final review](project-status/finalreport.md).

## Work with the project

Create an environment, install the developer requirements, and run the test suite:

    python3.12 -m venv .venv
    .venv/bin/python -m pip install -r requirements-dev.txt
    PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'

Load and inspect the dataset with the Hugging Face Datasets library. To rebuild local Kaggle exports or refresh derived corpus views, follow the [pipeline guide](PIPELINE.md). These commands write local artifacts; they do not publish data.

Raw downloads, PDFs, caches, and generated data are excluded from Git. Review the [PDF intake guide](incoming/pdfs/README.md) before adding scans.

## Project guides

- [Dataset card](DATASET_CARD.md) — scope, configurations, and intended use.
- [Dataset schema](docs/DATASET_SCHEMA.md) — common fields and per-configuration layouts.
- [Developer quick start](docs/DEVELOPER_QUICKSTART.md) — loading and querying examples.
- [Developer readiness](docs/DEVELOPER_READINESS.md) — setup, training examples, data contract, evaluation, and release checks.
- [Documentation index](docs/README.md) — project documentation and research.
- [Project status and audit index](project-status/README.md) — current status, readiness, metrics, and project-wide reports.
- [Current platform metrics](project-status/current-platform-metrics-2026-10-08.md) — verified Hugging Face, Kaggle, GitHub, and CI state.
- [Corpus preparation status](project-status/corpus-preparation-status.md) — current preparation state.
- [Kaggle and Hugging Face roadmap](research/huggingface-kaggle-quality-release-roadmap-2026-10-06.md) — release decisions and remaining gates.
- [Source catalog](sources/online/deep-search-catalog.md) — investigated source leads.
- [Review guide](review/README.md) — ways to contribute checks and corrections.

## Contributions

Source leads, corrections, and review contributions are welcome. Please include the source and any relevant rights, attribution, dialect, or regional context.
