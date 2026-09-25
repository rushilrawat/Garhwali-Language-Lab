# Hugging Face source overlap and release audit

**Checked:** 2026-09-24; **Scope:** current Hugging Face releases, the public speech package, and the Garhwali-labeled Hub datasets identified for possible ingestion.
**Decision:** Meta Omnilingual audio adds useful speech coverage and is published as a second config. The other inspected sources either duplicate data already held, add no verified Garhwali rows, or have an unresolved access or reuse condition.

## Current Hub state

- [`rushilrawat/garhwali-speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech) is public with VAANI and Meta Omnilingual configs. Commit [`914eb221b6f58f88d85a8d5dd826acac827ee1c4`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/914eb221b6f58f88d85a8d5dd826acac827ee1c4) adds 50 Meta shards and refreshed cards/manifests. Remote files reconcile with the local package; all 50 new Parquet sizes and SHA-256 hashes match.
- Follow-up card-only commit [`b64f0c4b914296c979947cf551ec976a0342d8af`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/b64f0c4b914296c979947cf551ec976a0342d8af) documents the Meta split-safety flags and filtering recipe. Read-back at that exact revision has the same SHA-256 as the local card; no data shard changed in this commit.
- [`rushilrawat/garhwali-corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) is owner-private. Its exported text profile contains redacted catalog values and omits 216 structured records without a compatible public-rights basis. This remains consistent with the project's no-redactions direction; it is not a claim that those records are absent locally.
- The refreshed public card describes both sources, separate configs, split counts, transcript status, exact-overlap flags, source terms, and citations. The text companion remains owner-private. No paid job or storage purchase was used.
- The first post-upload Dataset Viewer check returned a generic HTTP 500 while indexing. A later retry succeeded; a fresh check after the card-only commit also returned HTTP 200 for `/splits`, `/is-valid`, `/parquet`, and `/rows`. The Viewer lists both configs with train/validation/test splits, 267 Parquet shards across both configs, and preview/viewer/search/filter/statistics enabled. The Meta validation preview reports 298 rows and loads a transcript/audio example. The temporary Viewer failure is resolved.
- Hugging Face Jobs reports no running jobs and no active schedules. The latest canceled job is a Whisper Turbo 15,000-row follow-up (`6aac7f02b1dc2b62dc58fb5c`); its last log shows 13,840/15,000 processed, but no predictions/report were synced to the local batch directory. Its status gives no cancellation reason and its logs show no rate-limit error, so this cannot be attributed to usage limits.

## Meta Omnilingual Garhwali subset

Source: [`facebook/omnilingual-asr-corpus`](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus), config `gbm_Deva`, pinned revision `8648ba8946377697b427ae952076e49fc0e5e44d`, marked CC BY 4.0 by the source. Cite the [Omnilingual ASR paper](https://arxiv.org/abs/2511.09690).

| Check | Result |
| --- | ---: |
| Rows / duration | 2,927 / 19.135543 hours |
| Source splits | train 2,329; dev→validation 298; test 300 |
| Source audio bytes | 2,546,971,905 |
| Unique audio hashes | 2,922 |
| Exact-audio duplicate groups / rows | 5 / 10 |
| Duplicate-audio groups crossing source splits | 4 |
| Duplicate-audio groups with conflicting text | 5 of 5 |
| Exact-transcript duplicate groups / rows | 63 / 126 |
| Exact-transcript groups crossing splits | 31 |
| Audio-hash overlap with VAANI | 0 rows |
| Exact transcript-hash overlap with VAANI release | 0 rows |
| Split-safe rows after exact overlap checks | 2,857 for training; 2,857 for evaluation |

All 2,927 records remain present. `split_safe_for_training` and
`split_safe_for_evaluation` are conservative exact-overlap indicators; they are
not a judgment of transcript correctness, dialect, or overall language quality.
The upstream train/validation/test partitions are not clean exact-duplicate
evaluation partitions as-is. For leakage-sensitive use, filter training rows by
`split_safe_for_training == true` and validation/test rows by
`split_safe_for_evaluation == true`; each flag has 2,857 true rows. This excludes
affected examples from that particular run without removing them from the
published dataset or placing them in quarantine.
The duplicate audio rows have different source transcripts, so both copies stay
visible with their conflict, duplicate-count, cross-split, and safety fields.
Meta's transcripts were already present in the local `corpus/meta_omni.jsonl`
text collection; this adds audio and a separated audio/text source config, not
2,927 new unique text records. No speaker, prompt, or segment IDs are republished.

The published package is also available locally at
`data/huggingface/garhwali-language-lab-speech-2026-09-23/`. It has two configs:
the current VAANI config and `meta_omnilingual`. The combined package has
113,363 source rows, 113,350 unique audio hashes, 154.645543 hours, and
18,162,515,483 source-audio bytes (about 16.91 GiB). The Meta config uses 50
Parquet shards. Source shard hashes and output shard hashes are recorded in the
manifests and match the Hub objects.

Local validation verified every output Parquet hash and every embedded audio
hash, 2,927 unique record IDs, expected source counts and splits, `gbm` /
Devanagari / `garh1243` labels, source revision, and CC BY 4.0 provenance. The
first end-to-end check caught and fixed a shard-index reset that would have
repeated row IDs and mismatched transcripts; the rebuilt package now passes
the complete row/audio-hash scan. A later repeated metadata build exposed
duplicate card sections; the builder now normalizes its additions and a
regression test proves that a second run leaves the README, attribution, and
manifest unchanged. The regenerated card's SHA-256 matches its Hub read-back at
commit `b64f0c4b914296c979947cf551ec976a0342d8af`. Native-speaker review remains
outstanding.

## Other candidate datasets and overlap decisions

| Source(s) | Finding | Decision |
| --- | --- | --- |
| `Sellopale/omnilingualpaleoi`, `lindonghello/omnilingual-asr-corpus`, `KathleenKunLiu/omnilingual-asr-corpus` | Their seven Garhwali Parquet shards match the Meta source files byte for byte (2,548,283,553 bytes). | Mirror copies; no ingestion. |
| `vnahata/OmnilingualASR-retrieval` | 300 Garhwali transcript strings exactly match Meta's test transcript set. | Derived text duplicate; no new transcript records. |
| `Helsinki-NLP/tatoeba` | Dataset Viewer returned 501 for the filtered query; the local corpus already has 36 Tatoeba records. | No newly verified rows. |
| `lbourdois/language_tags` | Language metadata/tags, not a Garhwali text or speech corpus. | No language examples to ingest. |
| `lbourdois/panlex` | Local snapshot has 13 Garhwali forms. The official PanLex terms are CC BY-NC-SA; a mirror card's CC0 label is not sufficient to override those terms. | Keep in the local restricted layer; do not export under CC BY 4.0. |
| `google/IndicGenBench_flores_in`, `google/IndicGenBench_xorqa_in`, `google/IndicGenBench_crosssum_in`; `VarunGumma/IGB_*`; `mteb/IndicGenBenchFloresBitextMining` | Counts/text match existing local evaluation data: 2,009 FLORES rows; 1,139 XORQA; 699 CrossSum; bitext-mining entries are the same FLORES sentences in the opposite direction. | Existing evaluation data; no duplicate import. |
| `mteb/HinDialectClassification` | 128 Garhwali records are already in `restricted/hindialect_gbm.jsonl`; source is non-commercial/share-alike. | Keep evaluation-only/restricted; no public duplicate. |
| `openbmb/DCAD-2000` | 119 Garhwali records are already in the experimental layer; underlying CommonCrawl/MADLAD reuse basis is unresolved. | Preserve locally as experimental; no public duplicate. |
| `espnet/mms_ulab_v2` | Correct Garhwali filter returned zero records. | No ingestion. |
| `amine-khelif/mms_ulab_v2`, `sundram1996/mms_ulab_v2`, `coml/mmsulab` | Fresh `/is-valid`, `/splits`, and first-row schema checks work. Schemas expose language IDs such as `iso3` plus audio; `coml/mmsulab` identifies itself as segmented from `espnet/mms_ulab_v2` and declares CC BY-NC-SA 4.0. Bounded `gbm` filter/search requests against `amine-khelif` and a `gbm` search against `coml` timed out (12–20 seconds); exact `gbm` counts and audio-hash comparisons remain unavailable. | No bulk download or ingestion. Treat the repositories as unresolved related candidates, not verified unique data. |
| `jake-anto/wiktionary` | Fresh `/is-valid`, `/splits`, and first-row schema checks work; `entries`, `examples`, and `forms` expose `lang_code`. The bounded `Garhwali` search timed out, and the `gbm` filter did not return a usable comparison. Existing source-aware extraction has 77 Garhwali lemmas, forms, and examples. | No full dump or duplicate claim; no newly verified records. |
| `kapturecx/Chaashini` | Garhwali audio listing is gated; viewer returned 401. | No access workaround; no ingestion. |

No candidate was rejected by deleting source rows. Existing restricted and
experimental records remain in their local layers with their status metadata.

## Remaining HF action

The public speech upload and Viewer checks are complete. Remaining source-audit
limits are explicit above: the candidate schemas now load, but their Garhwali
filters/searches time out before returning counts or row matches, and gated
sources were not accessed. Do not count unresolved candidates as unique data;
retry targeted comparisons only when those index queries or a reliable
file-level access path become available.

## Dataset Viewer follow-up — 2026-09-25

A fresh check reproduced a generic “taking too long to fetch the data” message
on `meta_omnilingual/test`. Without changing the repository, its files, or its
Hub revision, the same route later rendered the 300-row table. The `train`
(2,329 rows) and `validation` (298 rows) tables also rendered in this session.
The timeout is therefore intermittent and did not persist on recheck; it does
not currently point to a malformed release artifact.

Local comparison found matching Parquet schemas and one row group per shard
across all three Meta splits. All 2,927 local audio payloads are non-empty
FLACs; the test split has 300 rows / 254.1 MB and validation has 298 rows /
216.1 MB. Shard sizes and local counts match the release manifest; the Hub
Viewer reports the corresponding split counts. No repack, data edit, or Hub
upload was warranted. Retry a split once if the generic
Viewer timeout returns; escalate only if it persists while the corresponding
Parquet files and manifest remain unchanged.
