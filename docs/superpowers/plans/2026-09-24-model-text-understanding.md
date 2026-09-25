# Garhwali Text Representation Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Determine whether IndicBERTv2 continuation improves useful Garhwali text behavior, rather than treating lower masked-language-model loss as proof of language understanding.

**Architecture:** First repair evaluation selection so checkpoints are chosen on validation and only the selected checkpoint reaches an eligible held-out set. Then compare the pinned base and existing continuation checkpoints on the recommended text corpus and on source-labeled downstream tasks where reliable labels already exist. Keep mixed-language and OCR-heavy views as separately reported robustness slices.

**Tech Stack:** Python 3, PyTorch, Transformers, PEFT, JSONL, existing IndicBERT adaptation/evaluation code, unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 3. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md).

**Audit gate update (2026-09-24):** The recommended text split has no detected within-family exact-hash overlap, but its test is `unresolved` because the base model's pretraining exposure is unknown. Validation can be used only for development selection. The recommended training view overlaps Meta validation/test by 85/75 exact text hashes and instruction validation/test by 29/15; do not mix those families when claiming independent evaluation. Do not make a held-out claim until checkpoint lineage is established.

## Global Constraints

- Use only locally cached IndicBERTv2 weights and existing local checkpoints; no network downloads, Hugging Face Jobs, or spending.
- Use `text_recommended/{train,validation,test}.jsonl` as the default source-aware view. Do not fold the broad/mixed-language corpus into the primary score.
- Do not choose a checkpoint, seed, mask rate, task definition, or threshold from test results.
- Do not manufacture language labels from model predictions or silently treat unreviewed source metadata as ground truth; report label provenance and limits.
- Preserve source text, rights/provenance fields, record IDs, and text hashes.

## Review Focus

- Existing test-selection flaw — `evaluate_indicbert_transfer.py` currently selects a family using a frozen-test metric; regression tests must prove selection moves to validation.
- Duplicate texts across train/validation/test — use exact normalized text and existing duplicate-component metadata from the audit.
- Comparison integrity — base and candidate receive identical examples, masking positions, tokenizer revision, maximum length, and scoring code.
- Small or noisy task labels — report label source, class counts, and coverage; do not claim language accuracy from masked-token accuracy.

---

### Task 1: Repair checkpoint selection and held-out evaluation

**Files:**
- Modify: `scripts/evaluate_indicbert_transfer.py`
- Test: `tests/test_evaluate_indicbert_transfer.py`
- Write: `data/processed/evaluation/controlled_modeling/indicbert_transfer_validation.json` and `indicbert_transfer_test.json`

- [ ] **Step 1: Add tests that fail if a model family is selected using test loss.** The selected family must be the minimum validation cross-entropy; the test report must contain only base plus that selected family, not every candidate seed.
- [ ] **Step 2: Add explicit `--validation` and `--test` inputs and separate outputs.** Default validation to the audit-approved validation manifest; require an audit-approved test manifest for final evaluation.
- [ ] **Step 3: Refactor scoring into a shared deterministic path.** Hash the exact ordered row IDs, text hashes, mask seed, tokenizer/model revision, and evaluated token count for both splits.
- [ ] **Step 4: Run all candidate seeds on validation only and persist candidate validation metrics.** Select the family and seed on validation; do not open test files in the selection path.
- [ ] **Step 5: Evaluate the pinned base and only the validation-selected candidate once on an eligible held-out text split.** If no eligible split remains, emit a `development_only` report rather than using a test-derived comparison.
- [ ] **Step 6: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_evaluate_indicbert_transfer.py -v`.**

### Task 2: Verify MLM continuation on recommended Garhwali text

**Files:**
- Use: `scripts/run_indicbert_adaptation.py`, `scripts/run_indicbert_lora_adaptation.py`
- Add/modify tests only for identified defects in those scripts.
- Write: `data/processed/evaluation/controlled_modeling/indicbert_recommended_text/`

- [ ] **Step 1: Inventory cached base weights, every claimed continuation checkpoint, tokenizer revision, and each checkpoint's training manifest.** Record missing artifacts as unavailable; do not reconstruct checkpoint lineage from names.
- [ ] **Step 2: Use validation text from the recommended split for candidate selection.** Recompute base and existing candidate MLM cross-entropy and masked-token accuracy on the same deterministic rows and mask positions; use at least three fixed masking seeds if runtime permits.
- [ ] **Step 3: Add a source-aware slice report** for script, genre, quality tier, and source family only where those labels exist; include per-slice record/token count and exact text-hash list hash.
- [ ] **Step 4: Run one short continuation only if local weights, training code, and an eligible fixed validation set all pass preflight.** Use the recommended training split, fixed seed list, and the existing bounded configuration; save optimizer/config and input hashes with the checkpoint.
- [ ] **Step 5: Treat MLM loss/accuracy as diagnostics only.** No promotion is possible from MLM metrics alone.

### Task 3: Measure downstream text behavior with existing labels

**Files:**
- Create: `scripts/evaluate_indicbert_text_tasks.py`
- Create: `tests/test_evaluate_indicbert_text_tasks.py`
- Read: source-aware text split manifests and existing lexicon/paired-example records identified by the lineage audit.
- Write: `data/processed/evaluation/controlled_modeling/indicbert_text_tasks/`

- [ ] **Step 1: Inventory source-provided language labels and lexicon/example pairs.** Define only tasks with labels traceable to a source record; if Garhwali-versus-Hindi or lexical pairs are absent or unreliable, record the task as unavailable rather than synthesizing targets.
- [ ] **Step 2: Implement deterministic task construction.** Use training rows for fitting a linear probe or retrieval index, validation rows for feature/hyperparameter selection, and test rows only for the single selected result. Assert no normalized text or duplicate component crosses partitions.
- [ ] **Step 3: Test task label provenance, split isolation, empty-class handling, and stable scoring.** Include macro-F1/accuracy for classification and Recall@k/MRR for retrieval where applicable.
- [ ] **Step 4: Evaluate the base and validation-selected continuation with the same examples.** Include class counts, confusion matrix, source/genre slices, and text normalization rules.
- [ ] **Step 5: Mark unsupported or undersized tasks inconclusive.** Automated task scores are not a substitute for native-speaker review.

### Task 4: Produce a text-quality decision

**Files:**
- Create: `research/indicbert-text-quality-2026-09-24.md`
- Include links to JSON reports and checkpoint/manifests by SHA-256.

- [ ] **Step 1: Compare base and selected candidate on validation and any eligible held-out downstream tasks.** Separate MLM, classification, lexical retrieval, and mixed-language robustness results.
- [ ] **Step 2: Promote only when the downstream metric selected in advance improves and no supported source/genre slice materially regresses.** Otherwise retain the base model and label the continuation experimental.
- [ ] **Step 3: Run focused tests, `git diff --check`, and confirm no source text or corpus split changed.**
