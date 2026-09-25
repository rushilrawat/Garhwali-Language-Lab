# Garhwali Model Accuracy Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve and honestly measure Garhwali ASR, text understanding, generation/translation, and retrieval, then define TTS readiness without spending on cloud compute.

**Architecture:** Run a shared lineage and evaluation-integrity audit first. Then proceed serially through task-specific workstreams; each uses its own data, metrics, frozen evaluation, and promotion decision. Reuse valid existing outputs and change model code only where a specific evaluation gap requires it.

**Tech Stack:** Python 3, existing PyTorch/Transformers/NeMo scripts, JSONL manifests, PyArrow for local speech shards, pytest/unittest.

**Spec:** [2026-09-24-model-accuracy-improvement-design.md](../specs/2026-09-24-model-accuracy-improvement-design.md)

## Global Constraints

- Prefer local, reproducible experiments.
- Do not launch paid Hugging Face Jobs, buy compute, publish model artifacts, delete corpus rows, or automatically replace source transcripts.
- Native-speaker review and dialect annotation remain deferred at the owner's direction.
- Keep machine transcripts experimental; confidence and model agreement are not correctness probabilities.
- Do not tune on test data; disclose any known or unknown upstream pretraining overlap.
- Keep source text, audio, rights, quality, and split provenance intact.

## Review Focus

- Duplicate audio or speaker crossing train/evaluation splits — cover in the lineage audit regression tests.
- One audio hash with conflicting transcripts — preserve each source row and expose the conflict in the audit and ASR manifest tests.
- A previously inspected test presented as a blind test — record evaluated hashes and test history in the lineage audit.
- Missing local model weights or unsupported local device — fail/skip before training; verify in each runner's preflight test.
- Low-quality or unadjudicated references presented as native ground truth — assert report status and caveat fields in each evaluation test.

---

## Ordered workstreams

Each independent model task has its own plan. Run them serially in this order; the lineage audit is a hard dependency for every later workstream. The final report consolidates completed results after the task plans finish.

- [x] 1. **Evaluation lineage and baseline audit** — [plan](2026-09-24-model-accuracy-audit.md). Deliverable: verified input, split, and prior-test-use ledger. Result: no independent held-out set is currently approved; see [lineage report](../../../research/model-accuracy-lineage-2026-09-24.md).
- [ ] 2. **ASR accuracy** — [plan](2026-09-24-model-asr-accuracy.md). Deliverable: comparable SraVaani/Whisper results on an eligible Meta evaluation split and a promotion decision. Status: saved-output analysis is complete for the 269-row previously evaluated validation set; it favors SraVaani, but is development-only. New inference remains blocked by missing local runtime dependencies and cached SraVaani weights; no test rows were scored.
- [ ] 3. **Text representation quality** — [plan](2026-09-24-model-text-understanding.md). Deliverable: domain-stratified IndicBERT results beyond MLM validation loss.
- [ ] 4. **Generation and translation** — [plan](2026-09-24-model-generation-translation.md). Deliverable: validated mT0/NLLB output quality and model decisions.
- [ ] 5. **Retrieval** — [plan](2026-09-24-model-retrieval.md). Deliverable: a train/dev-selected retriever compared with existing baselines.
- [ ] 6. **TTS readiness** — [plan](2026-09-24-model-tts-readiness.md). Deliverable: verified pair/split audit and a measurable future evaluation protocol; no TTS model training in this cycle.
- [ ] 7. **Final model report** — [plan](2026-09-24-model-accuracy-final-report.md). Deliverable: reproducible per-task result registry, promotion decisions, and limitations.

**Execution update (2026-09-24):** Phase 1's code, tests, deterministic JSON/Markdown outputs, row-set fingerprints, evaluation decisions, and upstream SraVaani source note are complete. The first ASR subtask also compares the saved SraVaani and Whisper predictions on the exact same 269 validation hashes; its limits and the plain-language meaning of overlap are recorded in [model-accuracy-preflight-2026-09-24.md](../../../research/model-accuracy-preflight-2026-09-24.md). Use Native sequential execution for dependent accuracy phases; an independent reviewer may be used after the workstreams are complete.

## Completion Gate

The effort is complete when every eligible task has a reproducible report, each selected candidate has been compared on a valid held-out set, every rejected candidate remains labeled experimental, and TTS readiness is documented without overstating automated quality signals.
