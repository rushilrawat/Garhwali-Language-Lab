# Garhwali Corpus — dataset card

**Current corpus release:** `garhwali-language-lab-v0.2.7`, public at [Hugging Face](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) and [commit `1f7b2ce`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/1f7b2ceed1b743412b75d6288757e1d2cadac9c4).
**Speech companion:** [Garhwali Speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech), release `v0.2.1`.

## What is in this dataset

The corpus brings together Garhwali text, vocabulary, speech references, machine-generated transcript drafts, songs and literary metadata, geography, historical terms, university research references, and source links. Each config is separately labeled because its source, task, quality, and reuse terms differ. The repo code is MIT-licensed; that license does not apply to corpus contents. The Hub reports the corpus license as `other` because there is no single license for all records.

## Read this before using the row totals

This release is a source-linked Garhwali research/resource collection, **not a ready-to-train general text corpus**. The live Hub page reports 961,533 rows, but these are overlapping config views. Three metadata/reference tables contribute 778,157 of them (80.9%); those rows describe records and sources and are not language examples. The other 183,376 rows are also overlapping views and include catalogs, reference material, speech transcripts, vocabulary, instructions, and experimental text.

The published `text` config has **18,598 rows, 291,914 whitespace-separated words, and 1,373,045 characters**. All 18,598 are currently marked `recommended_for_training=false`. The 1,737 `text_expansion` and 475 `text_resources` rows are also all marked not recommended for general text training. The 14,988 `paharili_gbm` rows are experimental language-identification material with unresolved sentence origins and unreviewed labels; they are not a general-purpose LM corpus. The 2,002 strict speaker-disjoint ASR reference rows contain 36,228 transcript words, but all remain unreviewed and are not native-adjudicated. Machine-generated SraVaani drafts are hypotheses, never gold transcripts.

The v0.2.7 package has **18 named configs and 29 config/split views**. The local parent-text catalog has **36,105 exact-unique records**; it is not equivalent to 36,105 public or training-ready passages. The Hub page reported **7.56 GB** total repository file size on 6 October 2026. The speech companion is separate and reported 113,363 rows / 36.5 GB. See the [current metrics and utility audit](research/huggingface-current-metrics-and-utility-2026-10-06.md) for methodology, local storage accounting, and intended-use limits.

| Config | Rows | What it contains |
| --- | ---: | --- |
| `text` | 18,598 | Main text segments with train, validation, test, and source-overlap splits |
| `paharili_gbm` | 14,988 | PahariLI Garhwali-labeled sentence-classification examples; experimental |
| `catalog` | 36,105 | Parent-text inventory; some `text` fields are empty in this config |
| `text_expansion` | 1,737 | Existing catalog text selected for a separate access view; 1,283 train and 454 source-overlap |
| `text_resources` | 475 | Supplementary lookup/research view; 285 train, 190 source-overlap; 0 currently recommended for general text training |
| `asr` | 2,002 | Strict speaker-disjoint ASR reference rows |
| `sravaani_drafts` | 104,534 | Machine transcript drafts; 104,500 non-empty, 34 empty; not ground truth |
| `lexicon` | 1,493 | Vocabulary and pronunciation candidates |
| `instructions` | 3,228 | Experimental instruction/response examples |
| `geography` / `historical_terms` | 50 / 36 | Place and historical-term records |
| `literary_people` / `literary_works` | 26 / 66 | People and work-level bibliography |
| `popular_songs` / `university_research` | 30 / 8 | Song metadata (no lyrics) and research bibliography |
| `record_index` | 355,846 | One metadata reference per archived row |
| `source_catalog` | 9,571 | Deduplicated sources and their available URLs/rights metadata |
| `record_sources` | 412,740 | Record-to-source reference links |

## Text availability and the remaining gap

In the `catalog` config, 12,657 rows carry text and 23,448 rows expose metadata without the text value. That per-config count overstated how much text was missing from Hugging Face as a whole. A closeout audit compared every pending catalog value with all string values in all 961,533 public JSONL rows using Unicode NFKC normalization, case folding, and collapsed whitespace. It found **15,004 values already exposed elsewhere**—14,988 in `paharili_gbm` and 16 in other public fields. **8,444 distinct full texts, totaling 2,936,664 whitespace-separated words and 16,388,267 characters, do not appear in any public config.** They remain in the local all-data package; each is marked `rights_pending` / `not_cleared`.

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

The release preserves source identifiers, available source URLs, attribution, upstream split labels, hashes, rights/quality fields, and transformation notes. Configs can overlap; use split and overlap fields before evaluation. The complete 2026-10-06 release counts and limitations are in the [project README](README.md) and [final report](finalreport.md). The original v0.2.7 publication evidence is in the [release report](research/huggingface-corpus-v0.2.7-release-2026-10-06.md).
