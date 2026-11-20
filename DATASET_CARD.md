# Garhwali Corpus — dataset card

**Current corpus release:** `garhwali-language-lab-v0.2.9`, public at [Hugging Face](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) since 20 November 2026 ([data commit `236f2ad`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/236f2adaa587fc237f23700a64d7cb777ee02756)). It is additive: v0.2.2 to v0.2.8 paths are unchanged, and the two v0.2.8 Meta text configs are carried forward. Build-level figures are on the [local candidate metrics](project-status/local-candidate-metrics.md) page; the older [8 October cross-platform audit](project-status/current-platform-metrics-2026-10-08.md) describes v0.2.8.
**Speech companion:** [Garhwali Speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech). The audio payload remains at base release `v0.2.1`; its additive v0.2 update adds text-only label indexes.

## What is in this dataset

The corpus brings together Garhwali text, vocabulary, speech references, machine-generated transcript drafts, songs and literary metadata, geography, historical terms, university research references, and source links. Each config is separately labeled because its source, task, quality, and reuse terms differ. The repo code is MIT-licensed; that license does not apply to corpus contents. The Hub reports the corpus license as `other` because there is no single license for all records.

## Read this before using the row totals

This release is a source-linked Garhwali research/resource collection, **not a large ready-to-train general text corpus**. The v0.2.9 configs hold **976,343 overlapping view rows** in all. Three metadata/reference tables contribute 790,404 of them (81.0%), and content configurations contribute 185,939. Neither figure is a count of unique language examples. The Dataset Viewer was still processing the new files when these figures were taken, so they come from the release manifests and the live card; the Viewer totals may differ slightly once it finishes.

The new `screened_meta_gbm` config contains **1,841** non-empty sentence-length rows (47,566 whitespace-separated words); `short_utterances_meta_gbm` contains **110** non-empty short context rows. Both are selected from existing Meta Omnilingual transcripts and were already present in the v0.2.7 `text`/`text_expansion` views. Thus, the v0.2.8 addition creates a clean, attributed, filterable training surface; it does not add 1,951 newly sourced unique texts. The training view has zero normalized duplicates internally and is recommended only for experimental sentence-level LM work. Every row remains machine-screened and **not native-speaker reviewed**.

The v0.2.9 `text` config has **19,321 rows** (15,044 train, 1,368 validation, 1,287 test, 1,622 source-overlap); those rows remain marked `recommended_for_training=false`. Its 1,559 `text_expansion` and 648 `text_resources` rows remain general-purpose training-ineligible. The 14,996 `paharili_gbm` rows are experimental language-identification material with unresolved sentence origins and unreviewed labels. The corpus `asr` config has 1,888 strict speaker-disjoint reference rows (1,533 train, 245 validation, 110 test). The speech companion now exposes a distinct 2,718-row VAANI `asr_reference` index with 2,202 train / 373 validation / 143 test rows, plus 2,294 optional Meta train rows. All references remain unadjudicated. Machine-generated SraVaani drafts are hypotheses, never gold transcripts.

The live corpus card lists **20 named configs and 30 config/split views (976,343 rows)**; the Hub repository holds 8.53 GB across all release paths. The local parent-text catalog has **36,105 exact-unique records**; it is not equivalent to 36,105 public or training-ready passages. The speech page reports **118,375 displayed rows / 36.5 GB**: 113,363 audio/source rows plus the 2,718- and 2,294-row text-only indexes. The count includes overlapping views. See the [current metrics audit](project-status/current-platform-metrics-2026-10-08.md) and [v0.2.8 quality-release report](research/quality-screened-text-release-report-2026-10-06.md) for methods and use limits.

| Config | Rows | What it contains |
| --- | ---: | --- |
| `screened_meta_gbm` | 1,841 | Strict, non-empty Meta Garhwali transcripts; experimental LM candidates, not native-reviewed |
| `short_utterances_meta_gbm` | 110 | Short transcript context; not recommended for general LM training |
| `text` | 19,321 | Main text segments with train, validation, test, and source-overlap splits |
| `paharili_gbm` | 14,996 | PahariLI Garhwali-labeled sentence-classification examples; experimental |
| `catalog` | 36,105 | Parent-text inventory; some `text` fields are empty in this config |
| `text_expansion` | 1,559 | Existing catalog text selected for a separate access view; 1,128 train and 431 source-overlap |
| `text_resources` | 648 | Supplementary lookup/research view; 401 train, 247 source-overlap; 0 currently recommended for general text training |
| `asr` | 1,888 | Strict speaker-disjoint ASR reference rows |
| `sravaani_drafts` | 104,534 | Machine transcript drafts; 104,500 non-empty, 34 empty; not ground truth |
| `lexicon` | 1,493 | Vocabulary and pronunciation candidates |
| `instructions` | 3,228 | Experimental instruction/response examples |
| `geography` / `historical_terms` | 50 / 36 | Place and historical-term records |
| `literary_people` / `literary_works` | 26 / 66 | People and work-level bibliography |
| `popular_songs` / `university_research` | 30 / 8 | Song metadata (no lyrics) and research bibliography |
| `record_index` | 358,180 | One metadata reference per archived row |
| `source_catalog` | 9,425 | Deduplicated sources and their available URLs/rights metadata |
| `record_sources` | 422,799 | Record-to-source reference links |

## Text availability and the remaining gap

In the v0.2.9 `catalog` config, 13,108 rows carry text and 22,997 rows expose metadata without the text value (v0.2.8: 12,657 and 23,448). The availability figures below come from the v0.2.7 closeout scan and have not been re-run for v0.2.9. That per-config count overstates how much text is missing from Hugging Face as a whole. The v0.2.7 closeout scan found **15,004 values already exposed elsewhere** and **8,444 distinct full texts**, totaling 2,936,664 words and 16,388,267 characters, absent from public configs. They remain in the local all-data package, marked `rights_pending` / `not_cleared`. The v0.2.8 text configs re-expose rows already present in v0.2.7; a direct comparison found no overlap between these 1,951 values and the 8,444 pending catalog texts, so that unresolved public-availability count is unchanged.

The public reference tables retain source locators for these records: 7,675
have inline URLs and 769 resolve a URL through `source_catalog`. The quick
start shows both cases. Some locators identify a collection or dataset rather
than the exact work or page. A locator does not establish full source
identification or grant permission to republish the text. The
[gap-resolution audit](research/huggingface-corpus-gap-resolution-2026-10-06.md)
lists the largest source groups and the remaining steps.

The v0.2.7 release separately includes PahariLI's 14,988 normalized-unique rows. PahariLI declares Apache-2.0 for its repository, but does not identify sentence-level source origins. Those rows are available in a clearly labeled experimental config; their underlying reuse rights remain unresolved, and they are not recommended for general language-model training or independent evaluation.

## Intended uses and limitations

Use the dataset for corpus discovery, source-linked research, vocabulary exploration, language-identification experiments, and development of text, ASR, retrieval, and benchmark workflows. **Do not treat all rows as uniformly licensed, training-ready, or linguistically verified.** Inspect `rights_status`, `reuse_scope`, `license_labels`, `quality_status`, and `record_quality_flags` for each record and config.

The dataset has not had native-speaker or dialect validation. The PahariLI language labels are upstream labels, machine drafts are unreviewed hypotheses, and benchmark/model numbers are automated research results. They are not native-validated accuracy claims. The 104,500 non-empty SraVaani drafts are especially noisy and are not human transcripts.

Source terms vary across records, including attribution, noncommercial/share-alike, source-specific policies, pending rights, and metadata-only records. No single license covers the complete collection. The [license policy](LICENSE_POLICY.md), [attribution guide](ATTRIBUTION.md), and [schema guide](docs/DATASET_SCHEMA.md) explain the fields and conditions.

## Quick start

```python
from datasets import load_dataset

lexicon = load_dataset(
    "rushilrawat/garhwali-corpus", "lexicon", split="train", streaming=True
)
for row in lexicon.take(3):
    print(row["form"], row.get("glosses"), row["rights_status"], row["quality_status"])
```

For exact config counts, pandas/DuckDB examples, and a source-URL lookup, see the [developer quick start](docs/DEVELOPER_QUICKSTART.md). The separate speech repository contains audio and distinct human/provider transcript and machine-draft fields.

## Provenance and reproducibility

The release preserves source identifiers, available source URLs, attribution, upstream split labels, hashes, rights/quality fields, and transformation notes. Configs can overlap; use split and overlap fields before evaluation. Current platform counts and limitations are in the [project README](README.md), [8 October metrics audit](project-status/current-platform-metrics-2026-10-08.md), and [final report](project-status/finalreport.md). The original v0.2.7 publication evidence is in the [release report](research/huggingface-corpus-v0.2.7-release-2026-10-06.md).
