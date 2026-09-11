# Garhwali Corpus Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the collected Garhwali sources into reproducible, quality-labelled, deduplicated candidate datasets for text and speech modeling.

**Architecture:** Raw and source-layer files remain immutable. Preparation scripts stream records into Git-ignored `data/processed/` views, retain every source reference in duplicate groups, and write deterministic reports and split assignments. Speech preparation consumes the verified VAANI manifests and produces supervised, flagged-experimental and unlabeled views without copying audio.

**Tech Stack:** Python 3.12 standard library, JSONL, SHA-256, `unittest`.

**Spec:** `PIPELINE.md` and `research/vaani-full-use-plan.md`.

## Global Constraints

- Never modify or delete raw downloads.
- Preserve source URLs, identifiers, licenses, rights status and attribution.
- Treat normalization as a reversible derived field.
- Keep exact duplicates in provenance groups while emitting one canonical text.
- Assign duplicate texts to one split only.
- Keep native review and uncertain language labels explicit.
- Store generated datasets under Git-ignored `data/processed/`.

---

### Task 1: Unified text preparation

**Files:**
- Create: `scripts/prepare_text_corpus.py`
- Create: `scripts/test_prepare_text_corpus.py`
- Generate: `data/processed/text/canonical.jsonl`
- Generate: `data/processed/text/duplicates.jsonl`
- Generate: `data/processed/text/report.json`

**Interfaces:**
- Consumes: JSONL records under `corpus/`, `restricted/`, `experimental/`, `extracted/`, and `data/extracted/`.
- Produces: `normalize_text(text: str) -> str`, `quality_signals(text: str) -> dict`, `split_for_hash(digest: str) -> str`, and `prepare(paths, output_dir) -> dict`.

- [x] Write tests proving NFC/whitespace normalization, fallback text fields, provenance-preserving deduplication, deterministic split assignment and rejection of empty records.
- [x] Run the focused test and verify failure because the module is absent.
- [x] Implement streaming discovery, normalization, exact-hash grouping, quality signals and deterministic split assignment.
- [x] Run the focused test and then the full script test suite.
- [x] Build the current dataset and validate report counts against emitted line counts.

### Task 2: VAANI supervised and flagged-experimental views

**Files:**
- Create: `scripts/prepare_vaani_supervised.py`
- Create: `scripts/test_prepare_vaani_supervised.py`
- Generate: `data/processed/vaani/supervised.jsonl`
- Generate: `data/processed/vaani/experimental_review.jsonl`
- Generate: `data/processed/vaani/untranscribed.jsonl`

**Interfaces:**
- Consumes: `data/vaani/canonical-supervised-manifest.jsonl`, `canonical-full-manifest.jsonl`, and reconciliation reports.
- Produces: transcript-selection and quality decisions keyed by stable WAV path.

- [x] Test transcript precedence, pause-tag normalization, Bengali-script flags and preservation of supplied splits.
- [x] Implement the minimal manifest transformer.
- [x] Verify 5,894 supervised rows, eight Bengali-script flags and 104,542 unlabeled rows.

### Task 3: Audio quality inventory

**Files:**
- Create: `scripts/audit_audio_quality.py`
- Create: `scripts/test_audit_audio_quality.py`
- Generate: `data/processed/audio/quality.jsonl`
- Generate: `data/processed/audio/report.json`

**Interfaces:**
- Consumes: canonical VAANI and podcast manifests plus local WAV/M4A paths.
- Produces: duration, sample format, silence/clipping proxies, readability status and failure reason per file.

- [x] Test WAV header metrics and corrupt-file handling with generated fixtures.
- [x] Implement streaming header and PCM checks without loading the corpus into memory.
- [x] Audit the supervised set first, then the unlabeled set.

### Task 4: Review queues and release report

**Files:**
- Create: `scripts/build_review_queues.py`
- Create: `research/corpus-preparation-status.md`

**Interfaces:**
- Consumes: Tasks 1–3 reports and prepared views.
- Produces: bounded native-review samples stratified by source, dialect, script and quality flag.

- [x] Generate review queues for transcript disagreements, OCR pages, social vocabulary and low-confidence text.
- [x] Verify no text hash or speaker identity crosses candidate train/validation/test partitions.
- [x] Document open, restricted, active-experimental and unlabeled totals and the exact commands required to reproduce them.
