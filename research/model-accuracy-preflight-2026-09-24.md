# Model accuracy improvement status and local preflight

**Checked:** 2026-09-24; **Execution style:** Native, sequential workstreams
**Cloud spend:** None

## Current status

The evaluation-lineage audit is complete. It inventories 11 manifest families, prior saved predictions, exact-hash overlaps, and explicit evaluation-use decisions. The aggregate report is [model-accuracy-lineage-2026-09-24.md](model-accuracy-lineage-2026-09-24.md). Its row-level JSON companion is kept local because it contains VAANI speaker identifiers.

No current split is approved for an independent held-out claim. The 112-row VAANI ASR test and several text/retrieval/translation tests have already been scored. The Meta Omnilingual test has 292 of 300 rows passing its own split-safety flags, but exact checkpoint exposure to upstream corpora is unknown; those 292 rows remain unresolved for final evaluation. The Meta validation has 271 internally safe rows and is suitable only for development selection/error analysis.

## ASR runtime preflight

- Meta Omnilingual Garhwali audio shards are local: 7 Parquet files, 2,548,283,553 bytes. The source manifest and the approved VAANI validation predictions are also local.
- A local Garhwali Whisper-tiny v0.2 checkpoint is present at `models/whisper-tiny-garhwali-v0.2` (155,077,066 bytes).
- The local SraVaani cache contains only 62,756 bytes of metadata; model weights are not present.
- Neither the project `.venv` nor system Python can import PyTorch, Transformers, NeMo, PyArrow, SoundFile, MLX, CTranslate2, or Whisper. `ffmpeg` is present.

This environment cannot currently decode the Meta Parquet audio or run either local ASR checkpoint. No packages, models, or audio were downloaded, and no new inference was run.

## Saved ASR validation comparison

The reproducible, validation-only analysis is in [asr-validation-error-analysis-2026-09-24.md](asr-validation-error-analysis-2026-09-24.md), with input hashes and per-record error counts in its JSON companion. It paired the same 269 frozen validation recordings for both systems:

| Saved system | WER | CER | Rows with fewer word errors | Rows with fewer character errors |
|---|---:|---:|---:|---:|
| SraVaani | 43.39% | 18.93% | 249 | 261 |
| Whisper Garhwali v0.2 | 78.05% | 46.30% | 8 | 5 |

These are useful for finding errors and choosing what to investigate. They are not independent accuracy estimates: the validation split has prior evaluation history, transcript references have not had native-speaker adjudication, and upstream model exposure is unresolved. Test rows in the combined prediction files were not parsed or scored. This is the practical meaning of the overlap concern: if a recording or matching text was seen during model training or earlier model selection, its score can look better than performance on genuinely unseen examples. It does not mean data was stolen or publicly exposed.

The next ASR step is to use validation-only errors to identify repeatable failure patterns, then enable a local runtime and obtain the model weights needed for new inference on an eligible development split. No test evaluation is authorized until model-data lineage is resolved.

## Recommendation on execution style

Use Native execution for the accuracy workstreams because each phase depends on the prior phase's split and checkpoint-lineage decisions. Subagents can be accurate for isolated tasks when their inputs, allowed splits, and acceptance tests are explicit, but parallel implementation here adds handoff and integration risk. Keep the main run sequential and use an independent reviewer for a bounded final audit if needed.
