# Meta Omnilingual text-view rights decision

**Decision date:** 6 October 2026
**Scope:** Only records with exact `meta_omni` source provenance included in the
new `screened_meta_gbm` or `short_utterances_meta_gbm` derived views.
**Decision ID:** `meta_omnilingual_cc_by_4_0_training_2026_10_06`

## Decision

For these narrowly scoped derived views, the project accepts the upstream Meta
Omnilingual ASR Corpus declaration of **CC BY 4.0** as a basis for including
the source transcript text with attribution. This decision applies only when
the record's source ID, source URL, rights status, license ID, license URL, and
saved evidence locator match the exact Meta source declaration. It does not
clear any mirror, unrelated corpus source, audio file, or record with mixed
provenance. Original rows and source metadata are unchanged; each derived row
preserves the earlier `training_eligible=false` flag and records this decision.

## Evidence

- [Official Meta Omnilingual ASR Corpus card](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus/blob/main/README.md)
- [Creative Commons Attribution 4.0 legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en)
- Locally saved card metadata: `sources/online/meta_omni/card.md.metadata.json`
- Saved card SHA-256: `ec52ce7ee1bd2960f3c8d3b76d734683be979e4f8c0dc087e90d6e9ecaebf836`
- Saved source text: `sources/online/meta_omni/ec52ce7ee1bd2960f3c8d3b76d734683be979e4f8c0dc087e90d6e9ecaebf836-card.md`

The project decision assumes the upstream card's declared license covers the
corpus text. The card snapshot is pinned so that the evidence used for this
release can be inspected later. The decision is not a legal opinion and does
not change the license or status of the wider mixed-source corpus.

## Row-level limits

1. A row must resolve to one exact `meta_omni` provenance record and one
   matching public-rights basis record.
2. Both records must identify the Meta source URL, `CC-BY-4.0`, and the saved
   source evidence locator.
3. The derived release includes source record IDs, source URL, attribution,
   license URL, rights status, evidence snapshot hash, and decision ID.
4. The original source eligibility value is kept in
   `source_training_eligible_before_project_decision`.
5. The release does not include Meta audio. The decision is applied to
   transcript text rows only.

## Resulting release scope

The local candidate derives from the v0.2.7 source package and contains 1,951
nonblank, normalized-deduplicated Meta transcript values. The main
sentence-length training view contains 1,841 rows; 110 shorter utterances are
kept in a separate context-only view and are not recommended for general
language-model training. All are automated-screened and none is native-speaker
reviewed. This rights decision supports release under CC BY 4.0; it is not an
accuracy certification.
