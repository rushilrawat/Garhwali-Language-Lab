# Hugging Face corpus v0.2.6 publication and verification

**Published:** 2026-10-05
**Repository:** [`rushilrawat/garhwali-corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
**Data commit:** [`bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1)
**Latest dataset-card commit:** [`cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e)
**Previous public version:** v0.2.5

## What was published

The upload adds the 53-file v0.2.6 package under `releases/v0.2.6/` and updates
the root dataset card. It is additive; the upload plan contains no deletion
operations. The planned payload totals **907,215,611 bytes**. The new release
preserves the prior text inventory and source lineage while carrying forward
the corrected VAANI transcript-source and held-out-split provenance.

The package reports 36,105 parent catalog records, of which 12,657 have public
full text and 23,448 are metadata-only under current source-reuse decisions.
Its segment-oriented `text` view has 18,598 rows; `text_expansion` has 1,737;
and `text_resources` has 475. These views overlap. The wider public content
configs contain 168,388 rows, and the complete metadata/reference index has
355,537 rows; neither figure is a unique-example count.

## Local release gates

- The full test suite passed: **802 tests** (including the text-config schema
  regression test added during the Viewer hotfix).
- Candidate preflight passed all **26 configs** and **945,926** overlapping-view
  rows, with zero missing source-traceability rows, zero remaining
  cross-split identity leakage, and zero deleted or mutated records.
- The continuity audit found all **18,934** unique normalized v0.2.5 text
  values in the new package: 18,902 exact matches and 32 represented inside
  linked catalog parent text; zero were unrepresented.
- Hub tree inspection at commit `bddb006` found every planned path and matching
  file size: **53 present, zero missing, zero size mismatches**. All 19 LFS
  SHA-256 hashes and 34 Git-blob SHA-1 checks match the local plan, with zero
  content-hash mismatches. All 348 paths from the prior release remain. The
  only pre-existing non-card path with changed contents is `.gitattributes`,
  which adds 19 LFS rules for v0.2.6 shards and removes zero prior rules.

## Dataset Viewer status

The first post-publication requests exposed a streaming-schema cast error in
`text` and `text_resources`; stable whole-config schemas were published at
`dc2bab7`. Successful previews confirmed that repair, but also revealed that
the three metadata-reference configs were missing from the generated card;
their files remained on the Hub. The reference-index finalizer restored
`record_index`, `source_catalog`, and `record_sources` at card commit
`cd43e9e`. Both latest card hashes match their local files. The final live
Viewer check lists all 26 expected splits and Parquet outputs, with no pending
or failed jobs. Preview, viewer, search, and filter are enabled; sample rows
load for text, text resources, and all three reference configs. Statistics are
unavailable from the Hub endpoint. See the [Viewer schema/card fix report](huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md)
and [remote file verification](huggingface-v0.2.6-remote-file-verification-2026-10-05.json).

## Access and limits

The public v0.2.6 profile retains its per-record rights and quality fields.
Metadata-only catalog rows remain downloadable as records, while their source
text is not included in public text fields. The local all-data profile retains
the full collected text inventory. Automated quality labels are not native
validation, and the `recommended_for_training` flag remains false across the
current text views.

See the [Phase 2 rights and lineage audit](huggingface-phase2-source-rights-lineage-audit-2026-10-05.md),
[preflight JSON](huggingface-v0.2.6-candidate-preflight-2026-10-05.json),
[continuity JSON](huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json),
and [quality roadmap](huggingface-dataset-quality-roadmap.md) for methodology
and unresolved work.
