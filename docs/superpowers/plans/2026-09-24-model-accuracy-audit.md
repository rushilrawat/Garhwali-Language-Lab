# Model Accuracy and Evaluation Lineage Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish which model results and evaluation rows are trustworthy for further selection.

**Architecture:** Add a small offline audit that reads fixed split manifests and saved prediction manifests, computes exact hash overlap, and writes a deterministic JSON/Markdown ledger. It never changes source data or model artifacts.

**Tech Stack:** Python standard library, JSONL, hashlib, pytest/unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phases 1 and 2.

## Global Constraints

- Prefer local, reproducible experiments.
- Do not launch paid Hugging Face Jobs, buy compute, publish model artifacts, delete corpus rows, or automatically replace source transcripts.
- Native-speaker review and dialect annotation remain deferred at the owner's direction.
- Keep machine transcripts experimental; confidence and model agreement are not correctness probabilities.
- Do not tune on test data; disclose any known or unknown upstream pretraining overlap.
- Keep source text, audio, rights, quality, and split provenance intact.

## Review Focus

- Duplicate IDs or hashes across split files — `test_reports_audio_and_text_split_overlap`.
- Missing optional evaluation output — `test_missing_prediction_file_is_recorded_as_unavailable`.
- Malformed JSONL or required hash missing — `test_invalid_manifest_fails_with_path_and_line`.
- Same audio with conflicting text — `test_audio_conflicts_are_counted_without_row_removal`.
- Repeated test use — `test_evaluated_hashes_are_marked_seen_not_blind`.

---

### Task 1: Add deterministic lineage-audit helpers

**Files:**
- Create: `scripts/audit_model_accuracy_lineage.py`
- Test: `tests/test_audit_model_accuracy_lineage.py`

**Interfaces:**
- `read_jsonl(path) -> list[dict]` reports malformed input with its path and one-based line number.
- `hash_overlap(named_rows, field) -> list[dict]` returns sorted duplicate hash groups with split names and row IDs; it never drops rows.
- `build_report(project_root) -> dict` and `render_markdown(report) -> str` produce a deterministic audit.
- CLI: `--project-root` defaults to the repository root; `--output-prefix` defaults to `research/model-accuracy-lineage-2026-09-24` and writes `.json` and `.md` siblings.

- [x] **Step 1: Write a failing overlap test.** Assert that one hash in train and test is returned as a leakage group and unique hashes are not.
- [x] **Step 2: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_audit_model_accuracy_lineage.py -v`.** Expected: import/attribute failure.
- [x] **Step 3: Implement the three pure helpers.** Normalize only hash-field values; preserve original IDs and split labels.
- [x] **Step 4: Add tests for conflicting transcript hashes on one audio hash, empty manifests, and malformed line diagnostics.**
- [x] **Step 5: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_audit_model_accuracy_lineage.py -v`.** Expected: all audit-helper tests pass.

### Task 2: Inventory fixed splits and prior evaluations

**Files:**
- Modify: `scripts/audit_model_accuracy_lineage.py`
- Create locally: `research/model-accuracy-lineage-2026-09-24.json` (excluded from Git because it contains VAANI speaker identifiers)
- Create: `research/model-accuracy-lineage-2026-09-24.md`
- Test: `tests/test_audit_model_accuracy_lineage.py`

**Inputs:** `data/processed/model_ready/splits/asr/{train,validation,test}.jsonl`, `asr_expanded_human/{train,validation,test}.jsonl`, and `asr_experimental/{train,validation,test}.jsonl`; `data/huggingface/garhwali-language-lab-speech-2026-09-23/meta_omnilingual-manifest.jsonl`; `data/processed/model_ready/splits/text_recommended/{train,validation,test}.jsonl`; `data/processed/model_ready/instructions_v0.2/{train,validation,test}.jsonl`; `data/processed/model_ready/splits/tts/{train,validation,test}.jsonl`; and FLORES, XORQA, and CrossSum benchmark JSONL files.

- [x] **Step 1: Add a test that the configured audit covers every listed split family and benchmark and fails clearly when a required split is missing.**
- [x] **Step 2: Run the new test and confirm it fails before implementation.**
- [x] **Step 3: Add explicit manifest configuration and gather evaluated hashes/IDs from saved prediction files under `data/processed/evaluation/asr/`, `translation/`, `retrieval/`, and `controlled_modeling/`.** Record each manifest and prediction-file SHA-256, row counts, split membership, model/revision when recorded, prior test rows already scored, and unknown training or pretraining lineage as `unknown`.
- [x] **Step 4: Run `PYTHONPATH=scripts .venv/bin/python scripts/audit_model_accuracy_lineage.py --project-root . --output-prefix research/model-accuracy-lineage-2026-09-24`.** Expected: JSON and Markdown ledgers with deterministic counts and hashes.
- [x] **Step 5: Add a repeat-run test that byte-compares the generated JSON after two builds.** The unit suite verifies deterministic rendering, and two full CLI builds were byte-compared for both outputs.
- [x] **Step 6: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_audit_model_accuracy_lineage.py -v` and `git diff --check`.**

### Task 3: Decide usable evaluation sets

**Files:**
- Modify: `research/model-accuracy-lineage-2026-09-24.md`

- [x] **Step 1: Mark the VAANI 112-row ASR test and previously scored translation/retrieval rows as previously inspected, using the ledger hashes.**
- [x] **Step 2: Check Meta test rows against duplicate-safety flags and checkpoint training lineage.** 292/300 rows pass the Meta manifest's internal safety flags; 8 are excluded. SraVaani's external data sources are known at corpus level, but example-level overlap is not, so the 292 rows remain unresolved for final evaluation.
- [x] **Step 3: Mark each evaluation `eligible`, `development_only`, or `unresolved`; never call an evaluation blind if model lineage is unknown.** Exact manifest and row-set hashes, prior scored row counts, reasons, and source evidence are in the JSON/Markdown ledgers. No independent held-out set is currently approved.
- [x] **Step 4: Confirm the ASR, text, generation/translation, and retrieval plans name only eligible selection and final-evaluation splits.** Workstream plans now explicitly permit only development-only exploration where appropriate and prohibit test claims absent an eligible held-out set.
