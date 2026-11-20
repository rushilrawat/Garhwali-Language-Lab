# Current platform metrics — 20 November 2026

This page records the state after corpus **v0.2.9** was published on
20 November 2026. It replaces the corpus and CI parts of the
[8 October metrics audit](current-platform-metrics-2026-10-08.md). The speech
and Kaggle figures were not re-checked for this update; they are carried over
from 8 October because neither platform changed. Config and view totals count
overlapping views, not unique language examples.

## Hugging Face: corpus

v0.2.9 was uploaded to [Garhwali Corpus](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
at [data commit `236f2ad`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/236f2adaa587fc237f23700a64d7cb777ee02756)
under `releases/v0.2.9/` (56 files plus the root card). Earlier release paths
(v0.2.2 to v0.2.8) are unchanged.

The live card lists **20 named configurations** and **30 config/split views**.
The release manifests give **976,343 view rows**: 974,392 in the v0.2.9
package plus 1,951 in the two v0.2.8 Meta text configs carried forward. Of
these, **790,404 are source/reference-table rows** (`record_index` 358,180,
`record_sources` 422,799, `source_catalog` 9,425) and **185,939 are
overlapping content-view rows**. The Hub repository holds **8.53 GB** across
all release paths.

The Dataset Viewer was still processing the new files when these figures were
taken, so the totals come from the release manifest and card, not from the
Viewer's own display. Re-check the Viewer once it finishes.

| Config | Rows | Splits |
| --- | ---: | --- |
| `text` | 19,321 | 15,044 train / 1,368 validation / 1,287 test / 1,622 source-overlap |
| `paharili_gbm` | 14,996 | 11,997 train / 2,999 test |
| `catalog` | 36,105 | 13,108 with text / 22,997 metadata-only |
| `text_expansion` | 1,559 | 1,128 train / 431 source-overlap |
| `text_resources` | 648 | 401 train / 247 source-overlap |
| `asr` | 1,888 | 1,533 train / 245 validation / 110 test |
| `instructions` | 3,228 | 2,686 train / 356 validation / 186 test |
| `sravaani_drafts` | 104,534 | train |
| `lexicon` | 1,493 | train |
| `screened_meta_gbm` | 1,841 | train (carried from v0.2.8) |
| `short_utterances_meta_gbm` | 110 | train (carried from v0.2.8) |
| `geography` / `historical_terms` | 50 / 36 | train |
| `literary_people` / `literary_works` | 26 / 66 | train |
| `popular_songs` / `university_research` | 30 / 8 | train |
| `record_index` | 358,180 | train |
| `source_catalog` | 9,425 | train |
| `record_sources` | 422,799 | train |

What changed from v0.2.8:

- **Held-out splits.** The segment-level text split is now 182,611 train /
  10,145 validation / 10,145 test (90/5/5). Whole duplicate components are
  moved into validation and test until each reaches 5%, so every leakage check
  stays at 0.
- **Segmentation.** A danda followed directly by a Devanagari letter now ends a
  segment, giving 202,901 exact-unique segments.
- **PahariLI.** Texts that another source already holds are counted instead of
  stopping the build; their source IDs stay on the matching `text_expansion` row.
- **Row counts.** `text` grew from 18,598 to 19,321 rows. `text_expansion`
  (1,737 to 1,559), `text_resources` (475 to 648) and `asr` (2,002 to 1,888)
  also changed with the rebuild.

Build-level figures (parent texts, characters, segments) are on the
[local candidate metrics](local-candidate-metrics.md) page.

## Hugging Face: speech (unchanged since 8 October)

[Garhwali Speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
reported **118,375 rows** and **36.5 GB**: 113,363 source/audio rows (113,350
unique audio hashes, about 154.65 hours), a 2,718-row VAANI `asr_reference`
index (2,202 train / 373 validation / 143 test) and a 2,294-row train-only Meta
`asr_meta_extra_train` index. References remain unadjudicated.

## Kaggle (unchanged since 8 October)

- [Screened text candidates](https://www.kaggle.com/datasets/rushilrawat1/garhwali-screened-text-candidates): version 1, public; 1,841 candidates and 110 context rows.
- [ASR reference clips](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1): version 2, private; 2,718 VAANI audio/reference pairs.
- [ASR baseline notebook](https://www.kaggle.com/code/rushilrawat1/garhwali-asr-baseline-reference-labels): version 3, saved, not run.

## GitHub and CI

The [CI run on main after the v0.2.9 doc refresh](https://github.com/rushilrawat/Garhwali-Language-Lab/actions/runs/44677966885)
(commit `beaf1e0`) ran **968 tests: all passed, 1 skipped**, with **62% line
coverage** against the 60% floor. `release/versions.json` lists v0.2.9 as
published and v0.2.10 as the next corpus version.

## Unchanged limits

- **0 records** have been native-speaker adjudicated.
- The **8,444 distinct full texts** still held locally pending rights evidence
  come from the v0.2.7 closeout scan; that scan has not been re-run for v0.2.9.
- The benchmark remains a local draft; independent-final evaluation
  eligibility is 0 of 5 task areas.
