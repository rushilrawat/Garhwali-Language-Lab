# Hugging Face corpus release v0.2.5 — 2026-10-05

## Release status

The v0.2.5 public package is live in the public
[`rushilrawat/garhwali-corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
repository. The 51-file additive payload is at [commit
`46407fc`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/46407fcb623d7f51d3f401f5842f73209dbffc4c).
The root card upload is at [`c89d6af`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/c89d6afba0b08d446e4d6dd99d5033e726568604);
its versioned config paths were corrected at [`dbb1c99`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dbb1c99503e11db454392a6c232254a37c9189d7).
The typed-feature card repair for the two failing configs is at
[`dc3308d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dc3308d4eb1d0eb619ab78071d0b34c2cbe8ac09).
All package files and both cards are present at the latest revision. The
The updated schema has been verified against all 13 affected local JSONL
shards. Viewer indexing has recovered for all splits and most Parquet files;
one `university_research` conversion and the dataset-wide validity check remain.
Streaming access has also been independently verified for one row in each new
`source_overlap` split and the existing lexicon train split.

## Why this update exists

A source-lineage audit found public text assigned to the default `train` split
that carries direct Meta Omnilingual ASR development/test record IDs or a
transcript match to held-out Meta/VAANI material. The new version preserves all
values and provenance, moves those records to an explicit public
`source_overlap` split, and leaves the rest of the dataset content intact.
This is a conservative source-lineage warning; transcript similarity does not
prove that two recordings are identical.

## Exact package impact

The public package contains **827,450 overlapping-view rows**: **164,387** rows
across 14 content configurations and 22 content config/split views, plus
**302,641** archive-row references, **5,019** deduplicated source records, and
**355,403** record-to-source links. These counts overlap and are not unique
training-example counts.

| Config | v0.2.4 train | v0.2.5 train | v0.2.5 `source_overlap` | Validation | Test | Total preserved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `text` | 17,289 | 15,981 | 1,308 | 895 | 765 | 18,949 |
| `text_expansion` | 1,647 | 1,284 | 363 | — | — | 1,647 |
| `text_resources` | 246 | 246 | 0 | — | — | 246 |

The public `text` content remains 18,949 rows; `text_expansion` remains 1,647;
`text_resources` remains 246. An ID-and-text comparison against the local
v0.2.4 package found **zero added or missing rows and zero changed text values**
in those three views. The only intended record changes are split assignment,
`original_split`/assignment context where needed, explicit overlap evidence, and
the conservative training recommendation on moved rows. No values were
removed or redacted by this update.

A total of **1,671** rows are in `source_overlap` across `text` and
`text_expansion`. All remain publicly addressable in their original
configurations. They are excluded from default `train` loads. This count is not
an audio-identity or semantic-leakage finding.

## Validation

- Independent package preflight: **passed**, zero errors and zero deleted or
  mutated records.
- Cross-split record-identity intersections: **zero** for each checked text,
  ASR, and instruction split pair.
- Upstream-held-out source IDs or transcript matches left in default text
  training: **zero**.
- Source-overlap rows without corresponding audit evidence: **zero**.
- Exact preservation check against v0.2.4 for `text`, `text_expansion`, and
  `text_resources`: all record IDs and text values match; 1,308, 363, and 0
  train rows respectively moved into `source_overlap`.
- Full repository test suite: **791/791 passed** after the card-schema regression tests.
- Planned public payload: **51 files**, **818,257,864 bytes** (about 780.4 MiB),
  plus the updated root dataset card. Prior versioned files are retained.
- Live tree verification: all 51 planned release paths and sizes match; 18
  LFS SHA-256 hashes and 33 Git blob SHA-1 hashes match the local package.
  The latest repository revision is `dc3308d4eb1d0eb619ab78071d0b34c2cbe8ac09`.
- Hugging Face `datasets.load_dataset(..., streaming=True)` opened
  `text/source_overlap`, `text_expansion/source_overlap`, and `lexicon/train`
  at that immutable revision and returned one row from each without fetching
  full splits.
- The prior Viewer failure was a schema inference error in `text_expansion` and
  `sravaani_drafts`: empty list fields were inferred as `null` in one split or
  shard and as strings in another. The root and versioned cards now declare
  merged feature schemas for those configs. Local `datasets` loading with the
  declared schema succeeds for all 13 JSONL shards (1,647 expansion rows and
  104,534 draft rows); no dataset rows or payload files changed. The latest
  Viewer check reports all capabilities enabled, all 25 splits and 25 Parquet outputs ready, with no pending or failed jobs. Row samples load from both repaired configs, and dataset-wide `/is-valid` is true.
- The reference index was rebuilt from the intact v0.2.4 all-data snapshot so
  this release does not inherit the later v2.2.0 bundle's omission of the
  1,617-row `text_expansion` and 109-row `text_resources` archive views.

The package has **zero rows recommended for text training** under the current
conservative project rule. Publishing records or moving a record to
`source_overlap` does not establish linguistic correctness, training rights,
independent evaluation, or native-speaker review. Native-language review and
dialect annotation remain deferred.

## Reproduction

```bash
GARHWALI_RELEASE_VERSION=0.2.5 PYTHONPATH=scripts .venv/bin/python \
  scripts/build_huggingface_dataset.py \
  --output data/huggingface/garhwali-language-lab-v0.2.5-staging \
  --profile public

GARHWALI_RELEASE_VERSION=0.2.5 \
GARHWALI_HF_PUBLIC_OUTPUT=data/huggingface/garhwali-language-lab-v0.2.5-staging \
GARHWALI_HF_ALL_DATA_OUTPUT=data/huggingface/garhwali-language-lab-all-data-v0.2.4-local \
PYTHONPATH=scripts .venv/bin/python scripts/build_hf_reference_index.py

PYTHONPATH=scripts .venv/bin/python scripts/validate_hf_package_cloud.py \
  --package data/huggingface/garhwali-language-lab-v0.2.5-staging \
  --output research/huggingface-quality-candidate-preflight-2026-10-05.json
```

The upload plan and content-free split-evidence crosswalk are
[`huggingface-v0.2.5-upload-plan.json`](huggingface-v0.2.5-upload-plan.json)
and [`huggingface-upstream-split-overlap-2026-10-05.json`](huggingface-upstream-split-overlap-2026-10-05.json).
The follow-up card-only schema repair and Viewer retry evidence are recorded in
[`huggingface-corpus-v0.2.5-viewer-schema-repair-2026-10-05.md`](huggingface-corpus-v0.2.5-viewer-schema-repair-2026-10-05.md).
