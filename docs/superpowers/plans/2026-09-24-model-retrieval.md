# Garhwali Retrieval Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve and measure Garhwali-question retrieval against the existing BM25 and IndicBERTv2 baselines without selecting on test results.

**Architecture:** Treat XORQA training rows as labeled query-to-context pairs, train a small projection over locally cached IndicBERT embeddings with training pairs only, choose its configuration against development queries, and evaluate the selected retriever once on an eligible held-out set. Keep a clear distinction between the benchmark passage collection and labeled query splits.

**Tech Stack:** Python 3, PyTorch, Transformers, JSONL, existing `run_retrieval_baseline.py` and `run_indicbert_retrieval_baseline.py`, unittest.

**Spec:** [model accuracy design](../specs/2026-09-24-model-accuracy-improvement-design.md), Phase 5. **Dependency:** [lineage audit](2026-09-24-model-accuracy-audit.md).

**Audit gate update (2026-09-24):** All 500 XORQA development queries and all 539 test queries have saved retrieval predictions. Development may support exploratory error analysis; test is development-only history and cannot confirm a new retriever. The current audit does not approve an independent held-out retrieval set, so keep any local projection experiment explicitly exploratory and do not promote it on these scores.

## Global Constraints

- Use the local IndicBERTv2 checkpoint only; no downloads, cloud compute, or credit spend.
- Use train query/context pairs for fitting, dev for selection, and only audit-approved test queries for final scoring.
- Do not delete duplicate passages. Deduplicate the searchable passage collection deterministically while retaining all source record IDs for provenance.
- Report that the benchmark corpus contains contexts from all benchmark splits if that remains the intended retrieval setup; do not describe it as a fully isolated corpus.
- Keep Garhwali-query and oracle-English-query results separate. The English query is an upper-bound diagnostic, not Garhwali model quality.

## Review Focus

- Candidate collection definition — distinguish documents available to the retriever from labeled query rows used to fit or score it.
- Duplicate passage handling — preserve source IDs and map each positive answer context to its deduplicated document ID.
- Training leakage — no development/test question or answer label may enter gradient updates, negative mining, early stopping, or checkpoint selection.
- Small-data risk — compare against deterministic word and character BM25 and zero-shot IndicBERT; promote only reproducible gains on dev and eligible test.

---

### Task 1: Make the retrieval evaluation protocol explicit

**Files:**
- Modify: `scripts/run_retrieval_baseline.py`
- Modify: `scripts/run_indicbert_retrieval_baseline.py`
- Tests: `tests/test_run_retrieval_baseline.py`, `tests/test_run_indicbert_retrieval_baseline.py`
- Output: `data/processed/evaluation/retrieval/`

- [ ] **Step 1: Add tests for document/query separation.** Training, dev, and test rows must be labeled explicitly; each row's positive context must resolve to exactly one stable deduplicated document ID.
- [ ] **Step 2: Add a deterministic `--selection-split` for BM25 parameter choice and keep test scoring separate.** The default report should include dev metrics and record that no tuning used test.
- [ ] **Step 3: Add input manifest hash, passage corpus hash, row IDs, duplicate-group mapping, and `evaluation_status` to both baseline reports.** Preserve current ranking/metric output fields.
- [ ] **Step 4: Recompute current word-BM25, character-BM25, and zero-shot IndicBERT scores on dev.** Confirm current reported test metrics are marked previously evaluated in the lineage ledger.

### Task 2: Train a small, reproducible dense retriever

**Files:**
- Create: `scripts/train_indicbert_retriever.py`
- Create: `tests/test_train_indicbert_retriever.py`
- Write: `data/processed/evaluation/retrieval/indicbert_projection_dev/`

- [ ] **Step 1: Test pair construction and split safety.** Each train pair contains a Garhwali question, its positive context ID, and candidate document IDs; assert no dev/test query IDs or labels enter training batches.
- [ ] **Step 2: Implement a small linear projection over frozen, mean-pooled IndicBERT embeddings.** Normalize embeddings and optimize an in-batch contrastive objective using only train pairs; avoid unfreezing the full encoder for this small benchmark.
- [ ] **Step 3: Expose only bounded CLI options:** `--input`, `--model`, `--output`, `--seed`, `--epochs`, `--batch-size`, `--learning-rate`, `--max-query-tokens`, `--max-document-tokens`, and `--device`. Default all model loading to local-only.
- [ ] **Step 4: Evaluate every epoch on dev only and select by MRR@10, with Recall@10 as a guardrail.** Save the selected projection, exact training row IDs/hash, model revision, options, and dev predictions.
- [ ] **Step 5: Test deterministic seeds, empty inputs, missing positive passages, and leakage rejection.**
- [ ] **Step 6: Run one bounded local training sweep** only if the local model and PyTorch device pass preflight; otherwise record why the supervised branch could not run.

### Task 3: Held-out evaluation and decision

**Files:**
- Create: `research/retrieval-quality-2026-09-24.md`
- Write selected predictions/report under `data/processed/evaluation/retrieval/indicbert_projection_test/`.

- [ ] **Step 1: Select the projection using dev only** and freeze the chosen seed/config before checking test eligibility.
- [ ] **Step 2: If the lineage audit approves held-out queries, score BM25, zero-shot IndicBERT, and the selected projection on exactly the same test queries.** If no eligible test remains, do not run test evaluation and mark the study development-only.
- [ ] **Step 3: Report Recall@1/5/10, MRR@10, median rank, per-query ranks, missing positives, query coverage, bootstrap intervals, and query-language limitations.**
- [ ] **Step 4: Promote only if the projection improves MRR@10 and Recall@10 against both existing baselines on dev and eligible held-out data.** Otherwise retain the baselines.
- [ ] **Step 5: Run focused tests, `git diff --check`, and verify no benchmark source row changed.**
