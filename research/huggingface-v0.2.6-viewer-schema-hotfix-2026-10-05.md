# Hugging Face v0.2.6 Dataset Viewer schema and card fixes

**Published:** 2026-10-05
**Corpus data commit:** [`bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1)
**Latest card commit:** [`cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e)

## Finding and repair

After the v0.2.6 data upload, Hugging Face Dataset Viewer returned a type-cast
error for `text` and `text_resources`: its streaming JSON reader inferred a
`null` field before encountering populated values. Stable schemas inferred
across all JSONL shards are now declared for `text` (22 fields) and
`text_resources` (40 fields), alongside existing declarations for
`text_expansion` and `sravaani_drafts`. A local row scan found no non-null
values that conflict with those schemas.

The first card-only update, commit `dc2bab7`, fixed text previews but revealed a
second card issue: only 23 splits were listed because the root and versioned
cards were missing the three metadata-only reference configs. Their data
files remained present. The reference-index finalizer restored
`record_index`, `source_catalog`, and `record_sources` in both cards at
`cd43e9e`. The two card files at this latest commit match their local SHA-256
hashes. Both follow-up commits changed only dataset-card files; neither
replaced nor removed any data payload.

The schema-generation regression test loads both affected configs against the
generated features, including fields that are empty in early rows and
populated later. The complete test suite passes: **802 tests**. Independent
local package preflight passes with zero errors.

## Live Viewer check

After commit `dc2bab7`, `/is-valid` and the text/resource previews returned
success, but `/splits` and `/parquet` listed only 23 views because the three
reference configs were absent from that card. The latest card at `cd43e9e`
declares all **26** manifest config/split views. The final live check lists
**26/26** splits and **26/26** Parquet outputs, with no pending or failed jobs.
`/is-valid` reports preview, viewer, search, and filter enabled; statistics are
unavailable. Sample rows load for `text` (57 rows), `text_resources` (29), and
each reference table (`record_index`, `source_catalog`, and `record_sources`,
100 rows each). The earlier service-busy and pending responses cleared; the
v0.2.6 Viewer check is complete.

The v0.2.6 payload remains at commit `bddb006`. Its additive payload audit
verified all 53 planned paths and sizes, 19 LFS SHA-256 hashes, 34 Git blob
SHA-1 hashes, and preserved all 348 prior release paths. The only earlier path
whose contents changed is `.gitattributes`: it adds 19 LFS tracking rules for
new v0.2.6 shards and removes zero existing rules.
