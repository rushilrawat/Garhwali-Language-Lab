# ASR corpus and model improvement pass — 7 October 2026

This pass worked through the nine existing-data actions in order. The scope was
to make current material more useful for training and evaluation without
recording new speech or manufacturing reference transcripts. The only new
training-index rows are existing VAANI provider labels newly exposed after
source-backed speaker-identity recovery; no audio payload or transcript text
was created.

The review queues, raw source material, model outputs, and builders named below
remain local-only unless a public URL is explicitly provided. They are not
linked to downloadable repository artifacts.

## Progress by step

1. **Human review of existing transcripts — queued, no labels changed.** The
   80-row review queue contains the 55 existing `possibly_incomplete` validation
   references and 25 high-disagreement records. Corrections remain blank and
   each row is marked `pending_listen`; a model disagreement is not a correction.
   The local review CSV and audit JSON remain under
   `data/review/existing-asr-validation-labels-v0.1/` and are not published.

2. **Recover missing source speaker IDs — completed and published.** An exact,
   unique `speakerImageHash` to existing `speakerID` join resolved 718 records;
   two were excluded by existing transcript-review flags. The remaining **716
   existing references** now join the prior strict view, producing 2,718 total
   rows (2,202 train / 373 validation / 143 test). Audio hashes are unique,
   known speakers and normalized references do not cross splits, and every
   audio hash maps to the already-published audio. Raw speaker IDs and image
   hashes are not exposed. The Hub update is [commit `18fb1fb`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/18fb1fb85ee40cc0ba59be4b1c5484b3a0993f8b);
   its wording correction is [commit `dcf12e5`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/dcf12e50b0c88529c44ad6723877c64d551c4b28).
   The builder and split report remain local at
   `scripts/build_vaani_speaker_recovered_asr_v0_1.py` and
   `data/processed/model_ready/splits/asr_speaker_recovered_v0.1/report.json`.

3. **Report by district — completed as a post-hoc diagnostic.** The saved
   baseline and fine-tuned predictions cover the same 449 already-consulted
   official-test records. Only 116 have identified speakers; 333 do not. The
   source split has 41 Tehri and 408 Uttarkashi records.

   | District | Rows | Baseline WER / CER | Fine-tuned WER / CER |
   | --- | ---: | ---: | ---: |
   | Tehri Garhwal | 41 | 0.7805 / 0.4474 | 0.7500 / 0.3951 |
   | Uttarkashi | 408 | 0.8045 / 0.4603 | 0.7223 / 0.4269 |

   These are descriptive slices of a test set already inspected during
   development, not a blind benchmark or an estimate for all Garhwali dialects.
   Prediction artifacts are under
   `data/processed/evaluation/asr/whisper_cpu_final_test_2026-10-07/`.

4. **Compare training recipes — existing results reviewed; weak pseudo-label
   recipe not promoted.** On the same 269-row validation set, the CPU
   Whisper-tiny run changed WER/CER from 0.7805/0.4630 to 0.7251/0.4190. The
   two small pseudo-label pilots were worse: 0.7841/0.4630 and 0.7882/0.4637.
   No full pseudo-label training run is justified by those pilots. The
   development references remain unadjudicated, and missing speaker IDs in
   training prevent a claim of complete speaker-level independence. The
   strongest existing validation comparator is SraVaani 1.0 with beam-8
   decoding (WER/CER 0.4325/0.1892 on the same 269 references), but its model
   card reports substantial VAANI pretraining, so it is not independent
   evidence of generalization. Reports:
   [stage-1 pilot](asr-curriculum-stage1-pilot-2026-09-14.md) and
   [weighted-batch ablation](asr-weighted-batch-ablation-2026-09-14.md).

5. **Make the supervised loader direct — completed.** The published
   [`asr_reference` v0.2 guide](https://huggingface.co/datasets/rushilrawat/garhwali-speech/blob/main/training_views/v0.2/TRAINING_GUIDE.md)
   includes a streaming join from the audio config to the text index, with the
   same split on each side. It also explains the unadjudicated-label status,
   quality flags, district imbalance, and the train-only Meta option. The index
   contains no audio bytes.

6. **Audit long Meta clips — review list prepared, no guessed segmentation.**
   There are 434 existing clips over 30 seconds (399 train / 10 validation /
   25 test). A local-only review queue points to existing clips and records
   duration and transcript length.
   No audio was copied, no transcript changed, and no segment was created:
   source transcripts do not contain reliable time boundaries.

7. **Check Meta text for novel examples — no expansion needed.** The 1,841-row
   Meta training view and 110-row context view added in the previous release
   are exact normalized values already present in the existing public
   `text`/`text_expansion` configs. They make a filtered view, not new unique
   text. See the [corpus gap audit](huggingface-corpus-gap-resolution-2026-10-06.md).

8. **Check PDF-derived text and rights — candidate review queued, no import.**
   The rights audit keeps unlicensed or uncertain books local. In the
   edition-specific 1916 LSI scan check, 626 of 632 extracted non-empty
   selected-column OCR strings match public text after normalization. The six
   unmatched stored strings correspond to printed cells on the scan pages, but
   their OCR or row alignment is unreliable; five separate standard-form OCR
   values are already present in public text and are not dialect-cell labels.
   A local queue leaves all six corrections blank for page transcription and
   fluent-speaker review. No LSI text was uploaded. See the [rights triage](pdf-text-release-rights-triage-2026-10-07.md);
   its local LSI review queue remains unpublished.

9. **Prepare the local Whisper Tiny release description — corrected, not
   published.** The card now uses the primary 269-row development comparison
   and states that the 338-row test remainder is only exploratory: 333 of
   those rows lack known speaker IDs and the test set has been consulted. The
   staged model weight hash matches the card. Model weights remain in local
   staging; no public model release was made.

## Hugging Face viewer status

The v0.2 `asr_reference` Parquet files were downloaded back from the Hub and
match their local SHA-256 values; each parses as Parquet. The unchanged
`asr_meta_extra_train` file likewise matches locally and parses as 2,294 rows.
The split API initially returned a generic HTTP 500 “server is busier than
usual” response. On the follow-up live Viewer check on 2026-10-07, the subset
menu showed all four configs and `asr_reference/train` displayed its 2,202
rows with label and metadata columns. The dataset landing page also displayed
`asr_meta_extra_train/train` with 2,294 rows and a populated preview. The
earlier corrupt-footer response is not reproducible from the current Hub files.
This Viewer recovery followed Hub processing; it did not add data.

## Artifacts

Local artifacts (not published): the combined split builder, Hugging Face
training view, long-clip and LSI review queues, and corrected local/staged
Whisper Tiny model cards are retained in their corresponding `scripts/`,
`data/`, and `models/` workspace directories. No model weights or review
labels are included in this report.
