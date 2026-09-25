# Garhwali ASR Accuracy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish comparable speech-recognition results on eligible Garhwali audio, diagnose errors, and promote a candidate only after validation selection and an eligible held-out result.

**Architecture:** Convert the locally available Meta Omnilingual Garhwali rows into a hash-verified ASR manifest, run pinned local SraVaani and Whisper baselines without changing decode settings, select any bounded adaptation on validation, then evaluate only the selected candidate on the audit-approved held-out split. Keep VAANI as historical development evidence because its test has already informed prior work.

**Tech Stack:** Python 3, JSONL, PyArrow for local Parquet audio shards, existing PyTorch/Transformers/NeMo runners, `scripts/asr_metrics.py`, pytest/unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 2. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md) defines permitted row use; only internally safe Meta validation rows are available for development work at present. No test inference is authorized by the current audit.

**Audit gate update (2026-09-24):** The VAANI validation (269 rows) and test (112 rows) are development-only; all have prior saved predictions. The Meta Omnilingual validation has 271 internally safe rows and may be used for development selection/error analysis only. Its 292 internally safe test rows remain `unresolved` because SraVaani's example-level upstream training exposure is unknown. Do not open Meta test for this study or claim independent held-out accuracy. The expanded-human training view overlaps the experimental evaluation view heavily; never combine those views in one split protocol. Before inference, local preflight must also verify checkpoint, dependencies, and audio files; no download or cloud substitute is allowed.

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

- [ ] **Step 1: Test row mapping before implementation.** Use synthetic manifest rows and synthetic Parquet-like records to assert stable record IDs, split names, transcript, source license, audio SHA-256, and conflict/split-safety flags are preserved.
- [ ] **Step 2: Test safety filtering.** Assert rows with `split_safe_for_training=false` never enter train; rows with `split_safe_for_evaluation=false` never enter validation/test; conflicting audio rows remain present in the source audit and are excluded only from the derived evaluation view with an exclusion reason.
- [ ] **Step 3: Implement an offline CLI.** Require `--source-manifest`, `--parquet-root`, and `--output-dir`; resolve each source file without network access, decode audio bytes to deterministic local WAV files at 16 kHz, and emit the ASR runner fields `record_id`, `audio_sha256`, `local_audio_path`, `asr_target_clean`, `source_split`, and provenance fields.
- [ ] **Step 4: Add source reconciliation.** Fail if source rows are missing, duplicated unexpectedly, audio hashes disagree, or transcript hashes disagree; report every intentional exclusion separately.
- [ ] **Step 5: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_prepare_meta_omnilingual_asr.py -v`, then run the manifest builder locally.** Save its deterministic report beside the generated manifest under `data/processed/model_ready/splits/meta_omnilingual_asr/`.

### Task 2: Establish comparable zero-shot baselines

**Files:**
- Modify only if needed: `scripts/run_sravaani_comparison.py`, `scripts/run_whisper_comparison.py`
- Tests: `tests/test_run_sravaani_comparison.py`, `tests/test_run_whisper_comparison.py`
- Write: `data/processed/evaluation/asr/meta_omnilingual_baselines/`

- [ ] **Step 1: Add regression tests for manifest compatibility and prediction identity.** Predictions must retain `record_id`, `audio_sha256`, `source_split`, reference, hypothesis, and per-row WER/CER counts.
- [ ] **Step 2: Preflight both pinned local checkpoints and every selected audio path.** Record model ID/revision, artifact SHA-256, device, library versions, input-manifest SHA-256, and eligible row IDs. Missing weights produce a clear non-run status.
- [ ] **Step 3: Run SraVaani and Whisper with unchanged deterministic decoding** on the same 271 internally safe Meta validation rows only, using `--input`, `--output`, `--max-records 0`, and the actual supported local `--device` option. Use separate output directories and do not overwrite existing VAANI reports. Do not run inference on Meta test while lineage is unresolved.
- [ ] **Step 4: Verify paired coverage.** Assert identical ordered audio hashes across both prediction files; compute corpus WER/CER and per-row paired deltas from `scripts/asr_metrics.py`.
- [ ] **Step 5: Add error slices.** Report results by duration bucket, source speaker/district where available, transcript length, and audio-quality flag, with counts so tiny slices are not overstated.
- [ ] **Step 6: Run the two focused unittest modules and inspect both JSON reports and prediction manifests.**

### Task 3: Select one bounded development experiment

**Files:**
- Modify only as evidence requires: `scripts/sweep_sravaani_decoding.py`, `scripts/train_sravaani_garhwali.py`, or `scripts/train_whisper_garhwali.py`
- Add focused tests beside the touched script tests.
- Write: `data/processed/evaluation/asr/meta_omnilingual_dev/`

- [ ] **Step 1: Read the lineage ledger and baseline error slices.** Choose either one decode-only hypothesis or one supervised adaptation hypothesis; do not run both as an unbounded search.
- [ ] **Step 2: For decode-only work, use Meta validation only.** Keep the exact configuration list bounded to the existing supported decoder variants and save the full configuration and per-row validation predictions.
- [ ] **Step 3: For training, use only the audit-approved Meta train subset and the existing confirmed-human transcript view.** Exclude validation/test audio, exact audio hashes, normalized transcript hashes, and known speaker overlaps before training; write the filtered training manifest and exclusion counts first.
- [ ] **Step 4: Add a preflight test for local model artifacts, selected device, empty data, and split-hash disjointness.** A training run must fail before allocating model state if an integrity check fails.
- [ ] **Step 5: Run no more than one reproducible local candidate.** Save seed, config, training-manifest hash, checkpoint hash, elapsed time, and validation predictions. If the local runtime is impractical or a required model is absent, record the reason and retain the baseline.
- [ ] **Step 6: Select the candidate on validation WER with CER as a guardrail.** Record the decision before any eligible held-out rows are evaluated.

### Task 4: One held-out confirmation and report

**Files:**
- Create: `scripts/report_asr_accuracy.py`
- Create: `tests/test_report_asr_accuracy.py`
- Write: `research/asr-accuracy-results-2026-09-24.json`
- Write: `research/asr-accuracy-results-2026-09-24.md`

- [ ] **Step 1: Test paired scoring, bootstrap interval reproducibility, and an explicit `development_only` status.** A report must not say `blind` when lineage is unknown or the held-out split was previously inspected.
- [ ] **Step 2: Evaluate only the validation-selected candidate and the pinned baseline** on rows the lineage ledger marks eligible. If none are eligible, skip held-out inference and state that no untouched evaluation remains.
- [ ] **Step 3: Report corpus WER/CER, paired per-record deltas, a deterministic bootstrap confidence interval, coverage, exclusions, all hashes, and runtime.** Do not use a confidence interval to claim native-language validity.
- [ ] **Step 4: Promote only if the candidate improves both WER and CER on validation and held-out data without a material source-stratum regression.** Otherwise mark it experimental and keep SraVaani 1.0 as the baseline.
- [ ] **Step 5: Run the focused tests, `git diff --check`, and verify no source manifest changed.**
