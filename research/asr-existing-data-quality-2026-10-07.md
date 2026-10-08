# Existing ASR data quality audit — 7 October 2026

## v0.2 follow-up — speaker metadata recovery

The versioned [`asr_reference` v0.2 index](https://huggingface.co/datasets/rushilrawat/garhwali-speech/tree/main/training_views/v0.2) now contains 2,718 existing provider-labeled VAANI recordings: 2,202 train, 373 validation, and 143 test. It exposes 716 additional existing references whose speaker identity was resolved by an exact, unambiguous `speakerImageHash` to one known source `speakerID` join. Two more exact matches remain excluded by existing transcript-review flags. No audio or transcript was created; the new version only indexes already-present source material. The upload is recorded in [commit `18fb1fb`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/18fb1fb85ee40cc0ba59be4b1c5484b3a0993f8b); the card clarification is in [commit `dcf12e5`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/dcf12e50b0c88529c44ad6723877c64d551c4b28).

The recovered split has unique audio hashes, normalized transcript strings, and known speaker IDs across partitions. Raw speaker IDs and image hashes are not published. Its Parquet files were downloaded from the Hub and match the local files byte-for-byte. The `asr_meta_extra_train` Parquet also matches its existing local file and parses as 2,294 rows. The split API initially returned a generic HTTP 500 “server is busier than usual” response. On the follow-up live Viewer check on 2026-10-07, both `asr_reference` and `asr_meta_extra_train` had populated previews. The earlier malformed-Parquet footer error is not reproduced by the current Hub files.

## What changed

The existing [`rushilrawat/garhwali-speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech) dataset was updated in [commit `6e1cab3`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/6e1cab33526f55cf294379dfc9fd2ec8ed78694c). The three `asr_reference` Parquet files still contain exactly 1,621 train, 269 validation, and 112 test records. Their existing audio and target text were not copied or expanded. Two metadata fields were added to each existing row: `reference_quality_flags` (from source cleanup) and `district`. The dataset card and training guide now explain the label and geographic evaluation limits. The existing audio files and optional Meta config were not changed.

The generator is `scripts/build_hf_speech_training_views.py`. Its staged output is `data/huggingface/garhwali-speech-training-views-v0.1-upload/`.

The updated lowercase manifest was synced in [commit `9d17ac5`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/9d17ac5f21d61b00c7dd6ad8431c8e71a09d8fda). An accidentally uploaded uppercase duplicate manifest was removed in [commit `365bb2d`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/365bb2d2e259cc0a5fd4cb1f569b2234760bbeae); the repository now lists only the lowercase manifest in `training_views/v0.1/`.

Read-only `datasets.get_dataset_split_names` and streaming loads succeeded after publication: `asr_reference` exposed train/validation/test, `asr_meta_extra_train` exposed train, and the live `asr_reference` row had both new fields. On the follow-up live Viewer check on 2026-10-07, `asr_reference/train` displayed 2,202 rows and the landing page showed the populated `asr_meta_extra_train/train` preview with 2,294 rows.

## Findings

| Strict ASR split | Rows | Tehri Garhwal | Uttarkashi | Source flagged `possibly_incomplete` |
| --- | ---: | ---: | ---: | ---: |
| Train | 1,621 | 1,242 | 379 | 257 |
| Validation | 269 | 269 | 0 | 55 |
| Test | 112 | 9 | 103 | 8 |

The strict splits have unique audio hashes and identified speakers do not cross splits. The geography is uneven: the development score describes Tehri Garhwal, while the held-out test largely describes Uttarkashi. Neither is a broad dialect benchmark. The provider references are still unadjudicated. `possibly_incomplete` is a source cleanup flag, not proof of an incorrect transcript.

The completed CPU model's existing predictions cover all 269 strict validation rows. On these same predictions, WER/CER were 0.7251/0.4190 overall, 0.7772/0.4857 on the 55 flagged rows, and 0.7106/0.4007 on the other 214. These are diagnostic slices of a model already evaluated on validation, not a new test result or corrected-label score.

## Review queue

The local review CSV (`data/review/existing-asr-validation-labels-v0.1/review.csv`) points to 80 existing validation recordings without copying audio: all 55 `possibly_incomplete` references plus 25 high model-disagreement records spread across 25 speakers. Each row retains the current reference and model prediction, has a blank correction field, and starts at `pending_listen`. Model disagreement alone cannot establish which text is correct. Human listening review is required before applying corrections; keep these validation clips out of training. The machine-readable audit (`data/review/existing-asr-validation-labels-v0.1/audit.json`) records source hashes and counts.

## Next useful improvement

Review and correct the highest-priority existing references, record reviewer and version provenance, then rerun the unchanged model against the corrected evaluation labels. For broader coverage, collect or curate an independent test set with both districts and known speakers; do not reassign current published splits without versioning the benchmark.
