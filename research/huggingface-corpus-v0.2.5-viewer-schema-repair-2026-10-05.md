# Hugging Face v0.2.5 Dataset Viewer schema repair — 2026-10-05

## Change

After v0.2.5 went live, Hugging Face listed all 25 configured splits but its
Parquet conversion failed for `text_expansion` and `sravaani_drafts` with
`Couldn't cast array of type string to null`. The cause was split/shard-local
inference: arrays empty in one JSONL file were assigned a null element type,
although other rows in the same config contain strings.

The generated dataset card now includes explicit, config-level feature
metadata for both configs. The repair is published at
[Hub commit `dc3308d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dc3308d4eb1d0eb619ab78071d0b34c2cbe8ac09),
which changes only the root and versioned README cards. No data files, record
values, split assignments, or older release paths changed. The release builder
now infers each shard schema using a whole-shard JSON read, merges null-only
feature types across shards, and emits the explicit config metadata. The
additive-upload validator also recognizes the two split-overlap audit support
files shipped with v0.2.5.

## Local verification

- The merged `text_expansion` feature schema casts both JSONL shards: 363
  `source_overlap` rows and 1,284 `train` rows (1,647 total).
- The merged `sravaani_drafts` schema casts all 11 JSONL shards and 104,534
  rows.
- The card metadata parses through 🤗 Datasets' YAML feature reader.
- Full repository test suite: **791/791 passed** after adding the schema
  regression and upload-plan tests.

## Hub status at the latest check

Before the card repair, `/splits` returned 25 entries with no pending or failed
splits, while `/parquet` listed 22 outputs and both affected configs failed
generation with the null/string type error. The latest post-repair API check returns HTTP 200: all Viewer capabilities are enabled; `/splits` lists 25 splits with none pending or failed; `/parquet` lists 25 outputs with none pending or failed. `/rows` returns a sample and expected total for both `text_expansion/train` (1,284 rows) and `sravaani_drafts/train` (104,534 rows). Dataset-wide `/is-valid` is true. The schema issue is resolved.

The repository tree contains 348 files and **5,707,580,438 logical bytes** at
the latest Hub check. Older versioned release content remains in place.
