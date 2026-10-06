# Hugging Face Phase 2: source rights and lineage audit

**Reviewed:** 2026-10-05
**Release:** `garhwali-language-lab-v0.2.6`
**Data commit:** [`bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1)
**Latest card commit:** [`cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e)
**Result:** v0.2.6 is published and its data files match the local additive plan.
The Dataset Viewer still needs a successful post-card-fix check; its latest
requests returned Hugging Face service-busy HTTP 500 responses.

## What changed in the candidate

The source text in `data/extracted/research/vaani-official-test-remainder.jsonl`
was previously attributed to a synthetic file-derived source ID. Its rows
identify `ARTPARK-IISc/Vaani-transcription-part` as the canonical transcript
source and carry the upstream `transcription_split=test` label. The candidate
now records the actual transcript source, its CC BY 4.0 metadata, attribution,
source URL, and upstream split on all **338** rows. All 338 remain in the
catalog; rows from that source are routed out of default train when they appear
in text expansion views. They are preserved as `source_overlap`, not deleted.

The Hugging Face card for [VAANI Transcription Part](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part)
declares CC BY 4.0 and states that access to file contents requires accepting
the repository conditions and sharing contact information. The release records
the card's license and attribution while keeping audio out of this text-only
package. License, gated access, and the project's separate training-quality
recommendation remain distinct fields.

## Source-to-view reconciliation

These are record-ID links, not counts of unique text values; a source row may
map to several text segments, and a segment can name several sources.

| Source manifest | Upstream records | Public `text` rows linked | Parent/catalog records linked | No direct `text` row link |
| --- | ---: | ---: | ---: | ---: |
| `indic_dialect_asr_gbm` | 7,823 | 7,476 | 7,823 | 347 |
| `meta_omni` | 2,927 | 2,915 | 2,927 | 12 |
| VAANI official test remainder | 338 | varies by segment/view | 338 catalog components | 0 missing from catalog |

All **347** Indic-Dialect records without a direct link in the public `text`
view were found in both the canonical cleaned parents and the public catalog
with their text present and rights-compatible provenance. They comprise 306
VAANI Uttarkashi, 33 VAANI Tehri Garhwal, and 8 Meta Omnilingual records. The
other **12** Meta records missing a direct `text`-view link are also present in
the cleaned parents and catalog. This means the segment-oriented `text` view
does not directly link every upstream record; the catalog and parent lineage
retain those links. No source text is removed by this reconciliation.

The **338** VAANI test-remainder rows all retain `transcription_split=test`.
The candidate routes 91 text-expansion and 190 supplementary-text view rows
that carry this held-out lineage to `source_overlap`; the remainder stays in
the catalog/reference layer. Those are overlapping view counts, not additional
upstream transcripts.

Machine-readable, content-free reports:

- [Indic-Dialect lineage in public text](huggingface-indic_dialect_asr_gbm-lineage-2026-10-05.json)
- [Indic-Dialect lineage in cleaned parents](huggingface-indic_dialect_asr_gbm-cleaned-lineage-2026-10-05.json)
- [Indic-Dialect lineage in public catalog](huggingface-indic_dialect_asr_gbm-catalog-lineage-2026-10-05.json)
- [Meta lineage in public text](huggingface-meta_omnilingual-lineage-2026-10-05.json)
- [Meta lineage in cleaned parents](huggingface-meta_omnilingual-cleaned-lineage-2026-10-05.json)
- [Meta lineage in public catalog](huggingface-meta_omnilingual-catalog-lineage-2026-10-05.json)

The reports contain source identifiers and counts, not transcript text.

## Release-continuity and package gates

The [continuity audit](huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json)
compares the prior public `text` view with the candidate across all public
text-bearing configurations using NFKC, case-folding, and whitespace
normalization:

- 18,934 unique normalized v0.2.5 text values were checked.
- 18,902 appear exactly in a v0.2.6 text-bearing configuration.
- 32 are contained in the same-source public catalog parent text.
- **0 are unrepresented.**
- 351 old row IDs are absent from the new segment-oriented `text` view; this
  row-ID change is not a content-loss count.

The independent [package preflight](huggingface-v0.2.6-candidate-preflight-2026-10-05.json)
passed all **26** configs and reported **945,926** overlapping-view rows,
**zero** deleted or mutated records, **zero** missing source-traceability rows,
and **zero** remaining cross-split identity leakage. These figures are
config/view totals, not unique corpus records.

The candidate manifest reports 36,105 catalog records. The public profile has
12,657 catalog records with full text and 23,448 metadata-only records under
current source-reuse decisions. The local all-data profile retains all
36,105 text values. The public package contains 168,388 rows across
content-bearing configurations and 355,537 metadata/reference-index rows;
these views overlap and must not be summed as unique examples.

The additive upload plan contains **53 files (907,215,611 bytes)** under
`releases/v0.2.6/` plus an updated root card, with no deletion operations.
All 53 paths and sizes match remotely; all 19 LFS SHA-256 and 34 Git blob
SHA-1 checks match. All 348 prior paths remain. The only changed pre-existing
non-card file is `.gitattributes`, which adds 19 LFS tracking rules for the new
release shards and removes zero prior rules.

After the first Viewer check exposed a streaming-schema cast error in `text`
and `text_resources`, commit `dc2bab7` published stable whole-config features
to both cards. The next successful Viewer check confirmed those previews, but
found only 23 splits because the three reference-table declarations had been
omitted from the card, although their data files remained. The reference-index
finalizer restored `record_index`, `source_catalog`, and `record_sources` at
`cd43e9e`; both remote card hashes match local files. The latest check after
that correction returned service-busy HTTP 500 responses for validation,
split listing, Parquet, and sample rows. The card now declares all 26 expected
config/split views; live confirmation of those views is pending. See the
[hotfix report](huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md).

## Other rights findings and remaining decisions

| Source family | Evidence in this audit | Current scope |
| --- | --- | --- |
| Meta Omnilingual ASR | 2,927 local manifest records; all carry CC BY 4.0 and `upstream_meta_cc_by_4_0`. The [official dataset card](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus) is the cited terms source. | Attribution and source links are retained. The project's ordinary model-training flag stays false until separate quality and split eligibility gates pass. |
| Indic-Dialect ASR, Garhwali subset | 7,823 rows; 1,930 from Meta and 5,893 from VAANI; all carry CC BY 4.0 with upstream source evidence. | Experimental text; source aggregation/duplicate and quality flags remain. Overlapping held-out material is kept out of default train. |
| HinDialect / MTEB | MTEB frontmatter says CC BY-SA 4.0, while its cited LINDAT record says CC BY-NC-SA 4.0. | Retain the more restrictive noncommercial/share-alike basis until exact export/version scope is resolved. |
| Open Bible Stories | Garhwali edition states CC BY-SA 4.0. | Attribution and share-alike terms are preserved; translation quality is not native-reviewed. |
| 1916 *Linguistic Survey of India* | The cited scan page supports a public-domain mark for the historical volume. | OCR and table alignment remain unreviewed; provenance and scan references are retained. |

No source license automatically certifies Garhwali accuracy, grants rights in
separate audio or images, or turns on model training. Native-language review
and dialect annotation remain deferred as requested.

## Next action

Retry the read-only Viewer checks after Hugging Face service availability
returns. The data and card commits are already public, their payload/card
checksums match, and all 802 local tests pass. Do not claim the release's
Viewer preview or Parquet capabilities are verified until those endpoints
return successful responses.
