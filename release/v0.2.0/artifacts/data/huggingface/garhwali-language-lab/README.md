---
language:
- gbm
license: other
task_categories:
- automatic-speech-recognition
- text-generation
- translation
configs:
- config_name: asr
  data_files:
  - split: test
    path: data/asr/test-*.jsonl
  - split: train
    path: data/asr/train-*.jsonl
  - split: validation
    path: data/asr/validation-*.jsonl
- config_name: catalog
  data_files:
  - split: train
    path: data/catalog/train-*.jsonl
- config_name: instructions
  data_files:
  - split: test
    path: data/instructions/test-*.jsonl
  - split: train
    path: data/instructions/train-*.jsonl
  - split: validation
    path: data/instructions/validation-*.jsonl
- config_name: lexicon
  data_files:
  - split: train
    path: data/lexicon/train-*.jsonl
- config_name: sravaani_drafts
  data_files:
  - split: train
    path: data/sravaani_drafts/train-*.jsonl
- config_name: record_index
  data_files:
  - split: train
    path: data/record_index/train-00000.jsonl
- config_name: source_catalog
  data_files:
  - split: train
    path: data/source_catalog/train-00000.jsonl
- config_name: record_sources
  data_files:
  - split: train
    path: data/record_sources/train-00000.jsonl
- config_name: text
  data_files:
  - split: test
    path: data/text/test-*.jsonl
  - split: train
    path: data/text/train-*.jsonl
  - split: validation
    path: data/text/validation-*.jsonl
---
# Garhwali Language Lab

Release: **garhwali-language-lab-v0.2.0**

## What this repository provides

This public dataset has two layers. Its rights-filtered content configurations contain **150,065 rows** across six named configurations and twelve config/split views. Separately, the metadata-only reference index covers every one of the **260,199 rows** in the complete all-data archive, including all 216 structured geography, history, literature, music, and research records.

The reference index includes **600 deduplicated source records** and **283,752 record-to-source links**. It exposes available names and titles, source URLs, attribution, rights status, and quality metadata. Record-level rights are marked `not_recorded` for **230,557 rows**; other rows include rights-pending, reviewed-unresolved, metadata-only, or cleared statuses. `not_recorded` is not permission to reuse a record: inspect its linked source entry and terms. The index does not contain the referenced works' text, lyrics, transcripts, audio, speaker identifiers, local paths, or content hashes. These are archive-row counts with overlapping views, not unique-example counts; the reference rows themselves are not training examples. Links and bibliographic facts do not grant rights to copy or reuse source material.


Public content tables withhold full content from **216 structured-knowledge records**
whose provenance does not include an explicit compatible public-rights basis.
Their full records remain in the access-controlled all-data package. The
reference tables expose source pointers and factual metadata, not full content.
No source license is inferred from a URL. The text catalog records each text identity and
redacts values without compatible redistribution evidence. Native-speaker
review and dialect annotation are deferred; benchmark and model scores are
automated research results, not native-validated claims.


## Garhwali-only additions in v0.2.0

This release adds **671 exact-unique source texts** after normalization and
cross-corpus deduplication (696 source rows; 673 unique values within this
intake, including two exact matches already held in earlier layers):

- 632 Garhwali entries from the dialect-comparison table in the
  [Linguistic Survey of India, Vol. IX, Part IV](https://archive.org/details/LSIV0-V11),
  representing 609 exact-unique forms explicitly tagged Standard, Rathi, or
  Tehri. 496 table rows have OCR confidence below 60/100; all OCR remains
  machine-produced and unreviewed.
- Nine Devanagari Garhwali language specimens from the same historical volume.
  These are source-grounded OCR excerpts, not modern conversational speech.
- Five sayings explicitly identified as Garhwali in Upreti's 1894
  [*Proverbs & Folklore of Kumaun and Garhwal*](https://archive.org/details/cu31924089930774).
- Fifty Garhwali Open Bible Stories from the pinned
  [Door43 OBS-TLF source](https://git.door43.org/OBS-TLF/gbm_obs), revision
  `f08afc73e1770129fbcd3089181f2faf2abbf54d`, licensed CC BY-SA 4.0.

The historical excerpts use a recorded Public Domain Mark basis; each story
retains the upstream attribution and CC BY-SA terms. The corpus rows preserve
page, source revision or checksum, rights, script/language evidence, and quality
status. The OCR and translated stories have not received native-speaker review.
For the public profile, only rows passing the project's rights filter carry
full text; the all-data package retains every collected value locally.


This rights-filtered profile contains Garhwali
text, human transcripts, lexicon and instructions, plus experimental SraVaani
drafts. Geography, historical terms, literary people and works, songs, and
university-research records are present in the source-reference tables; their
full contents are not redistributed when source rights are unresolved.

This public-profile package contains **150,065 records** across 6 named configurations (12 config/split entries), including transcripts for **104,534
unique SraVaani recordings**. This transcript-only package does not include audio files or source filenames.

This dataset card describes data scope, not model accuracy. Native-speaker
review and dialect annotation are deferred; transcripts and machine drafts retain
their review status. The project pipeline uses Python 3.12 and LangGraph for
resumable ingestion; quality checks and model metrics use task-specific scripts.
LangChain is not part of the current pipeline. See the [project README](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/README.md)
and [benchmark research status](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/research/benchmark-research-status-2026-09-25.md)
for the latest measured results and limitations.

The `catalog` configuration publicly accounts for all
**29,426 exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
only the protected text value is redacted. Nothing is silently omitted.

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Targeted rows also retain their local Whisper alternative,
cross-model agreement, and bounded review-confidence evidence. Draft export
status: **complete**.

All **1,188** targeted recordings retain
the third-checkpoint hypothesis. For the **1,090**
Garhwali review records, the package also carries a structurally ranked machine
proposal and its evidence limits. These proposals are pending audio review and
are never represented as automatic corrections or human references.
The remaining **35** structural
outliers also include deterministic re-decoding, waveform activity, and
human-reference calibration evidence. They still require listening review.

The draft layer also preserves **98
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

To keep Dataset Viewer schemas stable across shards, the SraVaani draft
configuration stores nested evidence objects and draft quality-flag arrays as
compact JSON strings. Parse those columns with a JSON parser; their values are
preserved without flattening or omission.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).


## Complete source reference index

The three metadata tables cover **260,199 records** from the complete local all-data archive. `record_index` has one row per archived record, `source_catalog` contains 600 deduplicated source references, and `record_sources` contains 283,752 join rows. The tables include source URLs, available attribution, rights and quality status, and factual catalog fields. They exclude source text, lyrics, transcripts, machine drafts, audio, speaker identifiers, local paths, and content hashes.

The current public package has **150,065 rows** across its content configurations; **125,500** indexed records have a corresponding public content value. The difference is metadata-only catalog rows whose values are redacted. Reference-index rows are not training examples and must not be added to corpus sample counts. Source links point to original material and do not grant reuse rights.

See [`reference_index_manifest.json`](reference_index_manifest.json) for counts by family and the three table checksums.

## Linked speech dataset

The companion [Garhwali Speech dataset](https://huggingface.co/datasets/rushilrawat/garhwali-speech) contains VAANI audio with provider transcripts and separately labeled SraVaani drafts.
