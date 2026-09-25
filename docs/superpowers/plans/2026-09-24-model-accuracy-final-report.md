# Garhwali Model Accuracy Final Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver one verifiable account of what each model track measured, which results are reproducible, what was promoted or rejected, and what remains unknown.

**Architecture:** Build the report from the lineage audit and per-track machine-readable reports, with explicit provenance and status fields. The generated Markdown is a readable release-readiness artifact; the JSON is the stable metric registry. No report may invent a missing result or call a previously viewed set blind.

**Tech Stack:** Python 3 standard library, JSON/JSONL, unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), completion gate. **Dependencies:** completed audit and all applicable model-track plans.

## Global Constraints

- Include completed, skipped, unavailable, inconclusive, development-only, and promoted results; do not suppress failed candidates.
- Do not merge different tasks into one “accuracy” score.
- State human/native validation status, rights status, upstream pretraining uncertainty, compute/runtime, and test exposure.
- Generate from saved reports and predictions. If an input report is absent or malformed, fail with its path rather than filling in estimated metrics.
- This report does not authorize Hugging Face uploads, model releases, corpus publication, or further compute spend.

## Review Focus

- Numbers must reconcile to saved machine-readable reports and prediction counts.
- Every metric identifies task, split, normalization, model revision/checkpoint hash, and input manifest hash.
- Promotion status must match the per-track gate; a validation gain alone is never reported as held-out success.
- Limitations must be visible near the claim they qualify, especially non-native reference quality and unknown upstream training exposure.

---

### Task 1: Define the report registry and generator

**Files:**
- Create: `scripts/build_model_accuracy_report.py`
- Create: `tests/test_build_model_accuracy_report.py`
- Generate: `research/model-accuracy-improvement-report-2026-09-24.json`
- Generate: `research/model-accuracy-improvement-report-2026-09-24.md`

- [ ] **Step 1: Add fixture-based tests** with ASR, MLM/downstream, generation/translation, retrieval, TTS, and lineage reports, including one failed/skipped result.
- [ ] **Step 2: Define the required registry schema.** Each run records task, status, source manifest/hash, split/status, model/revision/artifact hash, config, counts, metrics, runtime, promotion decision, and caveats.
- [ ] **Step 3: Implement deterministic input discovery from the fixed report paths created by the track plans.** Sort inputs, include each input file SHA-256, and fail clearly on missing required reports or invalid JSON.
- [ ] **Step 4: Render a concise Markdown table by task** plus sections for reproducibility, model decisions, data/split limitations, costs, and work still required. Do not average heterogeneous metrics.
- [ ] **Step 5: Test reproducibility.** Running the builder twice on unchanged inputs must produce byte-identical JSON and Markdown.

### Task 2: Reconcile and validate the completed study

- [ ] **Step 1: Run all relevant focused test modules** and the full project test suite once after track implementations are complete.
- [ ] **Step 2: Recompute every reported aggregate from saved row-level predictions** where the project has predictions; compare with saved reports and fail on disagreement.
- [ ] **Step 3: Validate each status** against the lineage ledger: eligible held-out, development-only, unresolved, not run, or unavailable. Confirm test reuse and model-data overlap disclosures.
- [ ] **Step 4: Review every promotion claim** against that track's stated validation and held-out criteria. Downgrade claims that lack either result.
- [ ] **Step 5: Run `PYTHONPATH=scripts .venv/bin/python scripts/build_model_accuracy_report.py --project-root . --output-prefix research/model-accuracy-improvement-report-2026-09-24` and `git diff --check`.**
- [ ] **Step 6: Verify corpus source files, rights metadata, split manifests, model checkpoints, and audio files have not been modified by evaluation.**
