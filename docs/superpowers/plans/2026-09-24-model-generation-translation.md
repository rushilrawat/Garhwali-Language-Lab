# Garhwali Generation and Translation Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether existing mT0 instruction checkpoints and NLLB proxy baselines generate useful Garhwali-related outputs, and prevent test data from influencing model selection.

**Architecture:** Audit checkpoint and split lineage first. Re-run candidate generation diagnostics on validation with deterministic decoding, select one candidate per task, then evaluate only that candidate against an audit-approved held-out set. Keep NLLB's Hindi source token explicitly labeled as a proxy because it has no Garhwali language token.

**Tech Stack:** Python 3, PyTorch, Transformers, PEFT, JSONL, existing mT0/NLLB evaluation scripts, unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 4. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md).

**Audit gate update (2026-09-24):** The full FLORES test (1,012 rows) has saved translation predictions; XORQA dev/test (500/539) has saved retrieval predictions; and 134 current instruction-test rows match prior mT0 test predictions. Treat these sets as development history, not fresh confirmation. CrossSum test has no local prediction match but remains `unresolved` because upstream model exposure is unknown. Use validation/dev only for exploratory selection, and do not open any test set for a new result until its exact checkpoint lineage is established and the lineage report marks it eligible.

## Global Constraints

- Use only local base weights, adapters, and data. No downloads, paid jobs, or credit spend.
- Do not resume or recreate a training run unless exact checkpoint, training manifest, config, and local runtime are present and the audit permits it.
- Select on validation only. Previously viewed benchmark test rows are development evidence unless the audit establishes an untouched eligible subset.
- Preserve prompts, model revisions, adapters, decoding arguments, row hashes, and full outputs.
- Treat translated/reference text quality and generated content validity as unreviewed automated evidence; do not claim native correctness.

## Review Focus

- Test leakage — current mT0 selected-test and NLLB scripts can evaluate test rows directly; ensure a test command is run only after validation selection and audit approval.
- CUDA-only behavior — current mT0 evaluation scripts move models to `cuda` unconditionally; add explicit device selection and fail clearly when unsupported.
- Output diagnostics — measure empty/malformed output, exact match, chrF2, copy rate, repetition, length ratio, and unsupported additions where reference alignment supports them.
- Proxy naming — every NLLB result must identify `hin_Deva` as a source-token proxy, not Garhwali-native translation support.

---

### Task 1: Audit and repair generation evaluation controls

**Files:**
- Modify: `scripts/evaluate_mt0_generation_checkpoints.py`
- Modify: `scripts/evaluate_mt0_selected_test.py`
- Tests: create `tests/test_evaluate_mt0_generation_checkpoints.py`; add or update selected-test tests.
- Output roots: `data/processed/evaluation/controlled_modeling/mt0_accuracy/`

- [ ] **Step 1: Add tests for device resolution, split choice, and report fields.** Validation mode must open only `validation.jsonl`; held-out mode must require explicit test authorization metadata and must state the exact manifest hash.
- [ ] **Step 2: Add `--device` with `auto`, `mps`, `cuda`, and `cpu`; remove unconditional `.to("cuda")`.** Keep deterministic generation settings fixed across checkpoints.
- [ ] **Step 3: Add a validation CLI that accepts the existing instruction split directory, local base model path, exact adapter directories, output directory, and a deterministic record cap.** Include the adapter and base-model path/checkpoint hashes in the report.
- [ ] **Step 4: Run available mT0 seed/checkpoint candidates on validation only.** Compute the existing task metrics and diagnostics for exact match, chrF2, empty output, malformed output, source copying, repetition, and output/reference length ratios.
- [ ] **Step 5: Select one checkpoint by a declared validation metric plus diagnostic guardrails.** Do not select based on test output or a previously reported test metric.

### Task 2: Make translation baselines split-explicit

**Files:**
- Modify: `scripts/run_translation_baseline.py`
- Modify: `scripts/run_nllb_translation_baseline.py`
- Tests: `tests/test_run_translation_baseline.py`, `tests/test_run_nllb_translation_baseline.py`
- Write: `data/processed/evaluation/translation/accuracy_{dev,test}/`

- [ ] **Step 1: Add tests showing baseline evaluation selects the requested split and defaults to `dev`, never `test`.** Test rows must not be read in a dev-only invocation.
- [ ] **Step 2: Add `--split {dev,test}` to both runners and a `--max-records` option with stable `record_id` ordering.** Preserve existing output schema and record exact selected row IDs/hashes.
- [ ] **Step 3: Keep BLEU/chrF2/exact-match implementations shared and test zero-length, empty, and Unicode inputs.** Report full denominators and the normalizer used.
- [ ] **Step 4: Run the NLLB base and any locally available adapter on the same validation rows.** Include model/adapter revisions, `hin_Deva` proxy status, decoding config, local artifact hashes, and latency.
- [ ] **Step 5: Compare mT0 and translation baselines only on task-compatible, identical Garhwali-to-English rows.** If schemas or row sets differ, report separate tasks rather than making a direct score comparison.

### Task 3: One eligible held-out evaluation

**Files:**
- Create: `research/generation-translation-quality-2026-09-24.md`
- Save selected and base predictions/reports beneath the controlled evaluation directories.

- [ ] **Step 1: Check the lineage ledger for prior test exposure and model training overlap.** Use only an eligible untouched test subset; otherwise label the result `development_only` and do not claim held-out generalization.
- [ ] **Step 2: Run the selected mT0 checkpoint and selected translation baseline once on their eligible held-out rows.** Evaluate the corresponding zero-shot/base baseline on exactly the same rows.
- [ ] **Step 3: Report paired task metrics and the failure diagnostics.** Keep source-copy behavior, empty/malformed output, repetition, and length anomalies visible beside aggregate scores.
- [ ] **Step 4: Promote only a candidate that beats its baseline on validation and eligible test with no severe output-quality regression.** Otherwise retain the baseline and label adapters experimental.
- [ ] **Step 5: Run focused tests, `git diff --check`, and verify that no train/test manifest or source example was edited.**
