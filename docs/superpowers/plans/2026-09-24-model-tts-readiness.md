# Garhwali TTS Readiness Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish whether the current speech/text pairs and split manifests are safe and sufficient for a future TTS experiment, and define an evaluation protocol without training a TTS model now.

**Architecture:** Audit the existing VAANI TTS and language-resource TTS manifests against their audio files and source records. Report split isolation, exact duplicates, speaker coverage, duration/audio-quality distributions, transcript coverage, and unresolved alignment risks. Produce a future evaluation protocol with explicit automatic and listening-based measures.

**Tech Stack:** Python 3 standard library, JSONL, WAV inspection, existing `scripts/audit_audio_quality.py`, unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 6. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md).

**Audit gate update (2026-09-24):** Existing ASR predictions over the VAANI audio do not constitute TTS synthesis evaluation. No TTS model-output evaluation is present, and model lineage and native listening review remain open. This workstream is a read-only readiness audit; it cannot make a speech-naturalness or TTS-accuracy claim.

## Global Constraints

- Do not train, synthesize, or publish audio in this phase.
- Preserve every source row and audio file; audits may report unsafe/unknown status but must not delete or rewrite data.
- Do not treat automated ASR agreement or MOS predictors as proof of naturalness or transcript correctness.
- Use only local files and existing manifests; no network fetches.
- Honor the owner's decision to defer native-speaker and dialect review, and identify that limitation explicitly.

## Review Focus

- Missing or changed audio — verify path existence, decoded duration/sample rate/channels, and SHA-256 against manifest fields where those hashes are available.
- Split leakage — compare audio SHA-256, normalized transcript SHA-256, and known speaker IDs across train/validation/test.
- Pair usability — report empty text, transcript status/quality flags, clipping/silence flags, duration outliers, and multiple transcripts for the same audio.
- Evaluation realism — separate automated intelligibility proxies from human naturalness, prosody, and dialect judgments.

---

### Task 1: Implement a deterministic TTS manifest audit

**Files:**
- Create: `scripts/audit_tts_readiness.py`
- Create: `tests/test_audit_tts_readiness.py`
- Read: `data/processed/model_ready/splits/tts/{train,validation,test}.jsonl`
- Read: `data/processed/model_ready/language_resources/tts/{train,validation,test}.jsonl`
- Write: `research/tts-readiness-2026-09-24.json` and `.md`

- [ ] **Step 1: Add fixture tests for clean pairs, missing audio, mismatched audio hash, duplicate audio, conflicting transcripts, repeated speaker, and split overlap.** Assert all findings identify source row IDs and never mutate inputs.
- [ ] **Step 2: Implement read-only manifest checks** for required text/audio fields, local-path existence, SHA-256, source and rights metadata, audio duration, split, and speaker ID.
- [ ] **Step 3: Reuse `audit_audio_quality.py` WAV checks** where suitable; expose clipping/silence/format summaries without copying or normalizing audio.
- [ ] **Step 4: Compute counts and distributions** for unique audio, unique text, speakers, districts, durations, sample rates, quality flags, empty/short transcripts, and transcript conflicts by split.
- [ ] **Step 5: Compare both TTS views.** Identify duplicate overlap between the two manifests and explain whether they are alternate views or separate records; retain all source entries.
- [ ] **Step 6: Run `PYTHONPATH=scripts .venv/bin/python -m unittest tests/test_audit_tts_readiness.py -v` and generate the JSON/Markdown audit.**

### Task 2: Define a future measurable TTS protocol

**Files:**
- Modify: `research/tts-readiness-2026-09-24.md`
- Optional focused test: `tests/test_audit_tts_readiness.py`

- [ ] **Step 1: State data-entry criteria** for any future pilot: minimum confirmed transcript quality, intact audio, speaker-disjoint splits, no duplicate audio across splits, clear source/license provenance, and sufficient per-speaker examples.
- [ ] **Step 2: Define objective evaluation** before training: held-out speaker set; audio integrity and duration; ASR-based intelligibility as a proxy; voice consistency and coverage; and paired confidence intervals against a baseline.
- [ ] **Step 3: Define listening evaluation fields** for a future native-speaker protocol: intelligibility, pronunciation, naturalness, prosody, dialect fit, artifact severity, rater guidance, and disagreement tracking. Mark these as pending rather than fabricating scores.
- [ ] **Step 4: Document the release gate.** No public claim of natural Garhwali TTS until listening evaluation and rights review are completed.
- [ ] **Step 5: Run focused tests, `git diff --check`, and verify that source manifests and audio files are unchanged.**
