# Hugging Face text-training eligibility audit — 2026-10-05

## Current v0.2.7 status — 2026-10-06

The tables below are the historical v0.2.5 audit and must not be read as the
current release counts. A fresh v0.2.7 package scan finds `text` 18,598 rows,
`text_expansion` 1,737 rows, and `text_resources` 475 rows; **zero rows in all
three configs currently carry `recommended_for_training=true`**. The main `text`
view contains 291,914 whitespace-separated words and 1,373,045 characters.
The v0.2.7 counts and live repository totals are documented in the [current
Hugging Face metrics and utility audit](../project-status/huggingface-current-metrics-and-utility-2026-10-06.md).
This update changes documentation only; no row flag or payload was changed.

## Scope and method

This audit reads the published public-profile v0.2.5 package (payload commit
[`46407fc`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/46407fcb623d7f51d3f401f5842f73209dbffc4c))
and reruns the repository's `recommended_text_training_row` rule on
every row in `text`, `text_expansion`, and `text_resources`. The companion JSON
contains split-level and source-level counts. The command is:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_hf_training_eligibility.py \
  --package data/huggingface/garhwali-language-lab-v0.2.5-staging \
  --output research/huggingface-training-eligibility-audit-2026-10-05.json
```

The diagnostic simulation changes nothing on disk: it temporarily flips only
explicit source-level `training_eligible: false` values to `true` in memory,
then re-runs the recommendation function. It does **not** resolve rights,
waive quality flags, use `experimental_training_eligible` as permission, or
change any record. No source or row status was modified by this audit.

## Results

| Public config | Rows and splits | Recommended now | Explicit source `training_eligible=false` | Rows with source quality flags | Rows with record quality flags | Strict-tier rows | Missing public rights basis | Diagnostic pass after resolving only source flags |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `text` | 18,949 total: 15,981 train / 1,308 source-overlap / 895 validation / 765 test | 0 | 18,949 | 15,440 | 15,658 | 12,664 | 0 | 1,731 train rows |
| `text_expansion` | 1,647 total: 1,284 train / 363 source-overlap | 0 | 1,647 | 1,041 | 1,041 | 1,647 | 0 | 263 train rows |
| `text_resources` | 246 train | 0 | 246 | 118 | 118 | 0 | 128 | 0 |

There are zero stored-versus-recomputed recommendation mismatches. All rows in
these configs have at least one recorded source-level
`experimental_training_eligible: true` value, but that field is explicitly
experimental and does not override a false ordinary training flag or any
quality gate. The new `source_overlap` rows remain present and public, but the
diagnostic simulation does not count them as training rows. Evaluation splits
also remain ineligible because their split assignment is unchanged.

The `text_resources` set is a lookup/research view, not a strict training
candidate set. Its 128 HinDialect rows have a noncommercial share-alike basis
rather than a public training basis; the other 118 include quality flags.
Presence of content in a public repository and presence of a redistribution
basis are not equivalent to a project's recommendation for training or
commercial use.

## Highest-count source queues

Counts below are **per source within a config**; a row may name more than one
source, so these values overlap and must not be summed as unique rows.

| Config | Source | Rows | Relevant recorded issue |
| --- | --- | ---: | --- |
| `text` | `indic_dialect_asr_gbm` | 10,943 | Every row carries `community_aggregation` and `possible_upstream_duplicate`; resolve component lineage and duplication before changing source eligibility. |
| `text` | `meta_omni` | 7,930 | Explicit training flag is false; no source-level quality flags were recorded for this source. Verify the applicable upstream license scope and why the project flag was set. |
| `text` | `obs_tlf_gbm_v1` | 1,794 | Translation quality unreviewed; native review pending; illustrations excluded. |
| `text` | `obs_garhwali` | 1,488 | Item pages do not repeat the license block; translation quality unreviewed. |
| `text` | `lsi_1916_grierson_garhwali_table` | 628 | Historical Latin transcription; automated OCR and column alignment remain unreviewed. |
| `text` | `jambu-garhwali` | 497 | Historical lexical forms; source spelling retained; native review deferred. |

These are evidence queues, not legal findings. In particular, a source's
license label alone does not establish item-level scope or model-training
permission. The next work is to inspect each source family and its underlying
provenance, preserve the evidence and uncertainty, and change a flag only when
the record supports that exact use. Quality and linguistic flags need their own
resolution path; rights findings cannot clear them.

## Decision

The dataset is accessible and internally consistent, but no text row currently
meets the project's conservative training-recommendation rule. The v0.2.5
split update keeps **1,308** core and **363** expansion rows with identified
upstream held-out-source overlap in a public `source_overlap` split; it does not
remove their values. This audit
quantifies why and gives a prioritized source queue. It does not certify the
texts as correct Garhwali, establish independent evaluation, or grant
redistribution/training rights. The next Phase 2 deliverable is a source-family
evidence matrix separating public display, text redistribution, research,
model-training, commercial use, attribution, and unresolved quality issues.
The first matrix and a source-row/view-row count reconciliation are now in the
[Phase 2 source rights and lineage audit](huggingface-phase2-source-rights-lineage-audit-2026-10-05.md).
That follow-up does not change this audit's recommendations or any row flags.
