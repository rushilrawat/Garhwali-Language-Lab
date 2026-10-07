# Hugging Face speech training views — 7 October 2026

## Live state after the v0.2 update

The current Viewer shows **118,375 rows / 36.5 GB**: 113,363 audio/source
rows plus the 2,718-row VAANI `asr_reference` index and 2,294-row
Meta `asr_meta_extra_train` index. The counts in the initial v0.1 publication
table below (1,621 / 269 / 112) are historical. The current VAANI view has
2,202 train / 373 validation / 143 test rows after adding 716 existing
references; no audio or transcript was newly created. See the [current live
metrics audit](current-platform-metrics-2026-10-07.md) and the [nine-step
ASR report](asr-nine-step-progress-2026-10-07.md).

Published to [`rushilrawat/garhwali-speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech) in commit [`caaf398`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/caaf398aa8db981d0855785ff94c1e424ffbcc63), then repaired in commit [`070057b`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/070057be180c3e5279b92722cb4360421097d38f).

The additive upload contains four text-only Parquet indexes, an updated dataset card, a guide, and a manifest. All seven files were visible in the Hub file listing after publication. Existing audio shards and source configurations were not replaced or duplicated. The local generator is `scripts/build_hf_speech_training_views.py`; its output is `data/huggingface/garhwali-speech-training-views-v0.1-upload/`.

| Config | Train | Validation | Test | Label source |
| --- | ---: | ---: | ---: | --- |
| `asr_reference` | 1,621 | 269 | 112 | Cleaned VAANI provider references from the existing speaker-disjoint ASR profile |
| `asr_meta_extra_train` | 2,294 | — | — | Optional Meta Omnilingual upstream references passing the existing exact-overlap screen |

Each row has the existing audio hash and speech source record ID, `target_text`, label kind/source/normalization, review status, split policy, and license. The card shows how to join the small label index to the corresponding streaming audio config by record ID. The default reference view excludes all machine-generated drafts. The Meta view is train-only because its source validation material is not an independent benchmark.

No new recordings or transcripts were made. The source references are unadjudicated and have not been reviewed by a native speaker. This release improves discoverability and split selection, not label accuracy or unique-example count.

The first upload used JSONL for the four new configs while the existing repository used Parquet. Hugging Face's split-name worker selected the Parquet reader and raised `Parquet magic bytes not found` on the JSONL files. The repair commit changed the card paths to Parquet, uploaded four Parquet files with the same records, and deleted the four obsolete JSONL files. At the repair commit, `datasets.get_dataset_split_names` returned all expected splits, and `datasets.load_dataset(..., streaming=True)` read one nonempty row from every new split. After the viewer queue caught up, `/splits` returned HTTP 200 with all four new splits and no pending or failed split jobs. `/first-rows` returned HTTP 200 with 100 preview rows for `asr_reference` train, validation, and test and `asr_meta_extra_train` train.
