# Garhwali ASR Accuracy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish comparable speech-recognition results on eligible Garhwali audio, diagnose errors, and promote a candidate only after validation selection and an eligible held-out result.

**Architecture:** Convert the locally available Meta Omnilingual Garhwali rows into a hash-verified ASR manifest, run pinned local SraVaani and Whisper baselines without changing decode settings, select any bounded adaptation on validation, then evaluate only the selected candidate on the audit-approved held-out split. Keep VAANI as historical development evidence because its test has already informed prior work.

**Tech Stack:** Python 3, JSONL, PyArrow for local Parquet audio shards, existing PyTorch/Transformers/NeMo runners, `scripts/asr_metrics.py`, pytest/unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 2. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md) defines permitted row use; only internally safe Meta validation rows are available for development work at present. No test inference is authorized by the current audit.

**Audit gate update (2026-09-24):** The VAANI validation (269 rows) and test (112 rows) are development-only; all have prior saved predictions. The Meta Omnilingual validation has 271 internally safe rows and may be used for development selection/error analysis only. Its 292 internally safe test rows remain `unresolved` because SraVaani's example-level upstream training exposure is unknown. Do not open Meta test for this study or claim independent held-out accuracy. The expanded-human training view overlaps the experimental evaluation view heavily; never combine those views in one split protocol. Before inference, local preflight must also verify checkpoint, dependencies, and audio files; no download or cloud substitute is allowed.

**Execution update (started 2026-10-04; completed through validation on 2026-10-05):** Task 1 completed locally. The source audit reconciles all 2,927 Parquet rows and both pinned manifests; it contains 2,294 safe train rows, 271 safe development rows, and 292 safe test rows. All 70 excluded rows remain in the audit. No Meta test inference was run. Task 2 preflight found the Garhwali-adapted Whisper-tiny v0.2 checkpoint, but not the original Whisper-tiny weights; the cached SraVaani repository lacks model weights, preprocessor, and tokenizer, and NeMo is not installed. Greedy and beam-5 Whisper-tiny v0.2 predictions were paired on all 271 validation rows and independently rescored. Greedy remains selected because beam-5 reduces WER but slightly regresses CER. Both results are poor development evidence, not independent accuracy; full details are in the [Meta validation report](../../../research/meta-omnilingual-asr-validation-2026-10-04.md). No checkpoint was fetched and no paid compute was launched.

## Global Constraints

- Use only model weights and audio already present locally; do not download checkpoints, launch Hugging Face Jobs, or spend credits.
- Do not train on Meta validation/test audio, use pseudo-transcripts as supervised truth, rewrite source transcripts, or remove conflicting rows.
- Preserve `record_id`, source split, transcript, source-file hash, audio hash, and duplicate/conflict flags in every derived prediction.
- If the audit finds the Meta test was previously used or its checkpoint lineage is unresolved, report it as development evidence and do not call it blind.
- If local audio bytes, model artifacts, compatible libraries, or hardware are missing, stop that experiment with a precise preflight result; do not silently fetch or substitute resources.

## Review Focus

- Parquet-to-manifest mapping — exact row count and audio/text hashes must match the signed source manifest.
- Duplicate-audio transcript conflicts — retain rows, exclude unsafe rows only from the named evaluation view, and report excluded IDs.
- Split leakage — assert audio hash, normalized transcript hash, and known speaker are disjoint for the selected train/dev/test subsets.
- Model comparison — score the same rows with identical metric normalization and report WER, CER, counts, source strata, and paired uncertainty.
- Test reuse — the held-out command may run only after the lineage report authorizes it.

---

### Task 1: Build and verify the local Meta ASR manifest

**Files:**
- Create: `scripts/prepare_meta_omnilingual_asr.py`
- Create: `tests/test_prepare_meta_omnilingual_asr.py`
- Read: `data/huggingface/garhwali-language-lab-speech-2026-09-23/meta_omnilingual-manifest.jsonl`
- Read: `data/downloads/meta_omni_gbm/data/gbm_Deva/*.parquet`
- Write: `data/processed/model_ready/splits/meta_omnilingual_asr/{train,validation,test}.jsonl`

- [x] **Step 1: Test row mapping before implementation.** Synthetic Parquet fixtures verify IDs, splits, transcript, license, hashes, and preserved safety metadata.
- [x] **Step 2: Test safety filtering.** Unsafe test material remains in `source_audit.jsonl` with an explicit exclusion reason and is absent from the evaluation view.
- [x] **Step 3: Implement an offline CLI.** It decodes source bytes to local mono 16 kHz PCM WAVs and writes runner-compatible manifests.
- [x] **Step 4: Add source reconciliation.** The builder checks all shard hashes, row keys, record IDs, audio hashes, transcript hashes, language metadata, and durations; failures leave no partial output.
- [x] **Step 5: Run focused tests and build the manifests.** All 2,927 source rows reconciled; results are under ignored `data/processed/model_ready/splits/meta_omnilingual_asr/`.

### Task 2: Establish comparable zero-shot baselines

**Files:**
- Modify only if needed: `scripts/run_sravaani_comparison.py`, `scripts/run_whisper_comparison.py`
- Tests: `tests/test_run_sravaani_comparison.py`, `tests/test_run_whisper_comparison.py`
- Write: `data/processed/evaluation/asr/meta_omnilingual_baselines/`

- [x] **Step 1: Add regression tests for manifest compatibility and prediction identity.** Both local ASR runners preserve `record_id`, `audio_sha256`, `source_split`, split, reference, hypothesis, and per-row WER/CER counts when present.
- [x] **Step 2: Preflight local checkpoints and all selected audio paths.** The adapted Whisper-tiny v0.2 checkpoint and 271 eligible audio paths are present. The original Whisper-tiny and runnable SraVaani checkpoints are unavailable locally; no download or cloud substitute was used.
- [ ] **Step 3: Run both baseline families with unchanged deterministic decoding.** The available adapted Whisper-tiny v0.2 was run with greedy decoding and one beam-5 candidate on the same 271 safe Meta validation rows. Cross-model SraVaani/original-Whisper comparison is blocked by absent local weights/runtime. Meta test was not run.
- [x] **Step 4: Verify paired coverage for available configurations.** The two Whisper outputs match across all 271 record IDs, audio hashes, and references; row metrics and corpus WER/CER were recomputed. Cross-model pairing remains unavailable.
- [x] **Step 5: Add error slices.** Duration, reference length, and available speaker ID slices include counts. District and audio-quality slices are explicitly unavailable in this source.
- [x] **Step 6: Run focused tests and inspect available JSON reports and predictions.** The SraVaani prediction contract is unit-tested, but there is no runnable SraVaani output on this data.

### Task 3: Select one bounded development experiment

**Files:**
- Modify only as evidence requires: `scripts/sweep_sravaani_decoding.py`, `scripts/train_sravaani_garhwali.py`, or `scripts/train_whisper_garhwali.py`
- Add focused tests beside the touched script tests.
- Write: `data/processed/evaluation/asr/meta_omnilingual_dev/`

- [x] **Step 1: Read lineage and baseline error slices; choose one bounded hypothesis.** Selected a decode-only beam-5 candidate; no adaptation training was attempted.
- [x] **Step 2: Run decode-only work on Meta validation.** Greedy and beam-5 used exactly the same 271 safe validation rows, Hindi prompt, and 128-token limit.
- [x] **Step 3: Training-manifest isolation.** Not applicable: the bounded experiment was decoder-only; no Meta validation/test audio was used for training.
- [x] **Step 4: Local preflight.** The adapted Whisper checkpoint, input hashes, and all selected audio paths were verified. The missing SraVaani/base-Whisper models were documented; no fetch was attempted.
- [x] **Step 5: Run the bounded candidate.** Beam-5 completed on 271 validation rows; model-weight hash, input hash, predictions, metrics, and CPU runtime were saved. No checkpoint was trained.
- [x] **Step 6: Apply the validation WER/CER selection guardrail.** Beam-5 lowers WER by 0.4543 pp but raises CER by 0.0325 pp; greedy is retained. No held-out split was used for this selection.

### Task 4: One held-out confirmation and report

**Files:**
- Create: `scripts/report_asr_accuracy.py`
- Create: `tests/test_report_asr_accuracy.py`
- Write: `research/asr-accuracy-results-2026-09-24.json`
- Write: `research/asr-accuracy-results-2026-09-24.md`

- [ ] **Step 1: Test a held-out scoring/report command.** No eligible untouched Meta test remains for this checkpoint lineage, so the held-out report implementation is deferred; the development-only report does not label results blind.
- [x] **Step 2: Check held-out eligibility.** No row set is approved for an independent held-out score; Meta test remains unresolved and was not opened.
- [ ] **Step 3: Report corpus WER/CER, paired per-record deltas, a deterministic bootstrap confidence interval, coverage, exclusions, all hashes, and runtime.** Do not use a confidence interval to claim native-language validity.
- [ ] **Step 4: Promote only if the candidate improves both WER and CER on validation and held-out data without a material source-stratum regression.** Otherwise mark it experimental and keep SraVaani 1.0 as the baseline.
- [ ] **Step 5: Run the focused tests, `git diff --check`, and verify no source manifest changed.**
