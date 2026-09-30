# Model accuracy improvement status and local preflight

**Checked:** 2026-09-26; **optional runtime rechecked:** 2026-09-29; **project `.venv` rechecked:** 2026-09-30; **Execution style:** Native, sequential workstreams
**Cloud spend:** None

## Current status

The evaluation-lineage audit is complete. Its 2026-09-30 refresh inventories
11 manifest families, 41 saved prediction files, exact-hash overlaps, and
explicit evaluation-use decisions across five task areas. The row-level
current output is under the ignored
`data/processed/evaluation/garhwali_bench/model_accuracy_lineage_2026-09-30`
prefix because its JSON companion contains VAANI speaker identifiers. The
tracked [2026-09-24 report](model-accuracy-lineage-2026-09-24.md) is a
historical snapshot.

No current split is approved for an independent held-out claim. The 112-row
VAANI ASR test and several text/retrieval/translation tests have already been
scored. The Meta Omnilingual test had 292 of 300 rows pass its original
split-safety flags, but the 2026-09-30 exact-hash audit finds four train/test
audio groups and four train/test transcript-text groups; validation also has
27 train/validation text groups. Across the Meta manifest there are four
cross-split audio and 31 cross-split text groups. Keep these rows and flag
them; the original flag counts do not establish a clean held-out test. Exact
cross-view content matches are exposure risks, not proof that a model trained
on each matched item. The
Meta validation's 271 earlier flag-passing rows remain development-only, with
the exact overlaps recorded in the ignored lineage ledger. That audit also
finds 338 exact audio-hash groups and 575 transcript-text groups from expanded-
human train in the experimental test, and 397 audio / 683 text groups in its
experimental validation. Those experimental partitions are not held-out
evidence.

## ASR runtime preflight

- Meta Omnilingual Garhwali audio shards are local: 7 Parquet files, 2,548,283,553 bytes. The source manifest and the approved VAANI validation predictions are also local.
- A local Garhwali Whisper-tiny v0.2 checkpoint is present at `models/whisper-tiny-garhwali-v0.2` (155,077,066 bytes); the completed SraVaani fine-tune `.nemo` artifacts are also local under the ignored evaluation output directories.
- The local SraVaani cache contains about 63 KB of model metadata; base model weights are not present.
- The project `.venv` and system Python lack PyTorch, Transformers, NeMo, PyArrow, SoundFile, librosa, torchaudio, MLX, CTranslate2, and Whisper. An optional cached runtime at `.cache/asr-runtime` exposes PyTorch and Transformers only when invoked with `PYTHONPATH=.cache/asr-runtime`; it still lacks NeMo, PyArrow, and common audio readers. `ffmpeg` is present.

The current runtime cannot load the SraVaani fine-tuned checkpoints without NeMo or decode the Meta Parquet shards without PyArrow. The local Whisper weights and FFmpeg are present, but a complete local audio-to-prediction path has not been verified. No packages, models, or audio were downloaded, and no new inference was run.

**2026-09-29 recheck:** The optional cache exposes PyTorch 2.14.0 and
Transformers 5.17.0 when placed on `PYTHONPATH`; PEFT, NeMo, PyArrow,
SentenceTransformers, SoundFile, and torchaudio remain absent. The isolated
project Hub cache contains SraVaani model configuration/code but no base
checkpoint weights; it has no NLLB or IndicBERT base snapshot. Local adapters
and fine-tuned checkpoints do not replace those missing bases. The current
`.venv` itself has none of the above model runtimes. No downloads or inference
were attempted during the recheck.

**2026-09-30 project-runtime check:** direct import discovery in the project
`.venv` confirms that PyTorch, Transformers, PEFT, NeMo, PyArrow, SoundFile,
SentenceTransformers, and Datasets are unavailable there. Fresh model inference
was therefore not attempted; this check neither downloaded packages nor
accessed Hugging Face compute.

## Saved ASR validation comparison

The reproducible, validation-only analysis is in [asr-validation-error-analysis-2026-09-24.md](asr-validation-error-analysis-2026-09-24.md), with input hashes and per-record error counts in its JSON companion. It paired the same 269 frozen validation recordings for both systems:

| Saved system | WER | CER | Rows with fewer word errors | Rows with fewer character errors |
|---|---:|---:|---:|---:|
| SraVaani | 43.39% | 18.93% | 249 | 261 |
| Whisper Garhwali v0.2 | 78.05% | 46.30% | 8 | 5 |

These are useful for finding errors and choosing what to investigate. They are not independent accuracy estimates: the validation split has prior evaluation history, transcript references have not had native-speaker adjudication, and upstream model exposure is unresolved. Test rows in the combined prediction files were not parsed or scored. This is the practical meaning of the overlap concern: if a recording or matching text was seen during model training or earlier model selection, its score can look better than performance on genuinely unseen examples. It does not mean data was stolen or publicly exposed.

The 2026-09-26 [ASR consolidation report](asr-baseline-consolidation-2026-09-26.md) compares the saved decoder/fine-tune validation outputs and retains their existing test aggregates without reopening test rows. The next ASR inference step requires a working local model/audio path; the remaining blockers and the legacy baseline discrepancy are tracked in the [issues and improvement plan](issues%26improvement%20plan.md). No test evaluation is authorized until model-data lineage is resolved.

## Recommendation on execution style

Use Native execution for the accuracy workstreams because each phase depends on the prior phase's split and checkpoint-lineage decisions. Subagents can be accurate for isolated tasks when their inputs, allowed splits, and acceptance tests are explicit, but parallel implementation here adds handoff and integration risk. Keep the main run sequential and use an independent reviewer for a bounded final audit if needed.
