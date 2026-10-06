# Documentation index

This page indexes the project Markdown intended for the shared repository, including current release, status, source-intake, roadmap, and review documents. Local-only draft artifacts, ignored caches, downloaded dependency documentation, and model outputs are not part of this public-facing index.

## Read these first

- [README.md](../README.md) — Project overview and current narrative.
- [DEVELOPER_QUICKSTART.md](DEVELOPER_QUICKSTART.md) — Exact Hugging Face config counts, copy-paste loaders, pandas/DuckDB examples, and lexicon search.
- [DATASET_SCHEMA.md](DATASET_SCHEMA.md) — Common rights/quality envelope and configuration-specific fields.
- [PROJECT_FILE_MAP.md](../PROJECT_FILE_MAP.md) — Generated inventory of tracked and non-ignored project files plus ignored payload totals.
- [v2.0-release-report-2026-09-30.md](../research/v2.0-release-report-2026-09-30.md) — 30 September source intake, metrics, rights-aware package, and publication record.
- [product-progress-2026-09-29.md](../research/product-progress-2026-09-29.md) — Completion bars for corpus, benchmark, research, model, community, API, and infrastructure work.
- [finalreport.md](../finalreport.md) — Authoritative release verdict, counts, and blockers.
- [huggingface-corpus-v0.2.5-release-2026-10-05.md](../research/huggingface-corpus-v0.2.5-release-2026-10-05.md) — v0.2.5 publication commits, split-safety change, exact counts, and checks.
- [huggingface-corpus-v0.2.5-viewer-schema-repair-2026-10-05.md](../research/huggingface-corpus-v0.2.5-viewer-schema-repair-2026-10-05.md) — Dataset Viewer schema repair and current Hub re-index status.
- [huggingface-corpus-v0.2.6-release-2026-10-05.md](../research/huggingface-corpus-v0.2.6-release-2026-10-05.md) — v0.2.6 corpus upload, exact file verification, continuity, and Viewer status.
- [huggingface-corpus-v0.2.7-release-2026-10-06.md](../research/huggingface-corpus-v0.2.7-release-2026-10-06.md) — v0.2.7 PahariLI expansion, exact row and storage deltas, test/preflight evidence, and pending Viewer processing.
- [huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md](../research/huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md) — Root/versioned card schema repair, follow-up commit, and post-fix Viewer check.
- [huggingface-v0.2.6-remote-file-verification-2026-10-05.json](../research/huggingface-v0.2.6-remote-file-verification-2026-10-05.json) — Remote release path, file-size/hash, continuity, and card-hotfix evidence.
- [huggingface-phase2-source-rights-lineage-audit-2026-10-05.md](../research/huggingface-phase2-source-rights-lineage-audit-2026-10-05.md) — v0.2.6 source-rights, VAANI held-out lineage, and v0.2.5-to-v0.2.6 continuity review.
- [huggingface-v0.2.6-candidate-preflight-2026-10-05.json](../research/huggingface-v0.2.6-candidate-preflight-2026-10-05.json) — Candidate package gate: 26 configs, 945,926 overlapping-view rows, zero errors or deleted/mutated records.
- [huggingface-v0.2.5-comparison-preflight-2026-10-05.json](../research/huggingface-v0.2.5-comparison-preflight-2026-10-05.json) — Fresh same-validator preflight report for the v0.2.5 predecessor package.
- [v0.2.5-to-v0.2.6 metric comparison](../research/huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.md) — Reproducible release-to-release counts, per-view deltas, metric contract, and limitations.
- [scripts/compare_hf_release_metrics.py](../scripts/compare_hf_release_metrics.py) — Rejects incompatible/failed preflights and writes comparable JSON and Markdown reports.
- [huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json](../research/huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json) — Text-value continuity check; zero old unique values are unrepresented.
- [huggingface-upstream-split-overlap-2026-10-05.md](../research/huggingface-upstream-split-overlap-2026-10-05.md) — Content-free audit of source-split overlap and preserved public rows.
- [Hugging Face source-lineage reports](../research/huggingface-phase2-source-rights-lineage-audit-2026-10-05.md) — Six machine-readable reports linked from the audit compare Indic-Dialect and Meta source rows in the public text view, cleaned parents, and public catalog.
- [scripts/audit_hf_source_lineage.py](../scripts/audit_hf_source_lineage.py) — Reproducible content-free source-lineage counter used by the Phase 2 audit.
- [DEEP_DIVE_FINAL_AUDIT.md](../DEEP_DIVE_FINAL_AUDIT.md) — Detailed code, data, and release audit.
- [text-rights-resolution-2026-09-30.md](../research/text-rights-resolution-2026-09-30.md) — Rights decisions, source-associated pending queue, and release boundaries.
- [benchmark-research-status-2026-09-25.md](../research/benchmark-research-status-2026-09-25.md) — Measured benchmark and model-research snapshot with the latest translation addendum.
- [task-result-eligibility-2026-09-28.md](../research/task-result-eligibility-2026-09-28.md) — Current split labels, prior test use, and result-claim limits.
- [model-accuracy-lineage-2026-09-28.md](../research/model-accuracy-lineage-2026-09-28.md) — Fresh split-manifest and saved-prediction matching audit.
- [asr-heldout-lineage-audit-2026-09-28.md](../research/asr-heldout-lineage-audit-2026-09-28.md) — Paired post-hoc comparison of five saved ASR runs on the same held-out rows.
- [meta-omnilingual-asr-validation-2026-10-04.md](../research/meta-omnilingual-asr-validation-2026-10-04.md) — Local Meta split reconciliation and development-only Whisper validation, with source hashes and error slices.
- [meta-omnilingual-asr-adaptation-2026-10-05.md](../research/meta-omnilingual-asr-adaptation-2026-10-05.md) — Hash-linked Whisper adaptation on a model-compatible Meta training view, paired validation gains, deterministic rerun check, and claim limits.
- [benchmark-model-roadmap.md](../research/benchmark-model-roadmap.md) — Phased benchmark and model-research plan, metrics, tooling, and release gates.
- [v0.2-public-announcement-roadmap-2026-09-29.md](../research/v0.2-public-announcement-roadmap-2026-09-29.md) — Verification, disclosure, documentation sync, and LinkedIn preparation for a truthful v0.2.0 announcement.
- [issues & improvement plan](../research/issues%26improvement%20plan.md) — Evidence-backed issue log and blockers for roadmap implementation.
- [benchmark-nested-overlap-review-2026-09-27.md](../research/benchmark-nested-overlap-review-2026-09-27.md) — Nested benchmark overlap findings and retained-row review labels.
- [benchmark-cross-language-exact-overlap-2026-09-28.md](../research/benchmark-cross-language-exact-overlap-2026-09-28.md) — Supplemental exact-string check across XORQA English/Garhwali answer labels.
- [benchmark-source-page-families-2026-09-28.md](../research/benchmark-source-page-families-2026-09-28.md) — Exact XORQA page-title families crossing source splits and their retained-row diagnostic labels.
- [benchmark-parent-safe-split-audit-2026-09-28.md](../research/benchmark-parent-safe-split-audit-2026-09-28.md) — Historical parent-document split leakage, corrected candidate hashes, and source-family limits.
- [retrieval-source-page-cluster-uncertainty-2026-09-28.md](../research/retrieval-source-page-cluster-uncertainty-2026-09-28.md) — Cluster-bootstrap intervals for saved XORQA BM25 dev predictions.
- [retrieval-miss-analysis-2026-09-28.md](../research/retrieval-miss-analysis-2026-09-28.md) — Gold-passage coverage and rank diagnosis for saved XORQA BM25 dev predictions.
- [generation-output-diagnostics-2026-09-28.md](../research/generation-output-diagnostics-2026-09-28.md) — Task-local mode collapse, length, Unicode, and script diagnostics for saved mT0 validation outputs.
- [asr-validation-run-manifest-2026-09-27.md](../research/asr-validation-run-manifest-2026-09-27.md) — Hash-linked post-hoc ASR validation comparison.
- [mt0-validation-run-manifest-2026-09-27.md](../research/mt0-validation-run-manifest-2026-09-27.md) — Hash-linked post-hoc manifests for three mT0 validation runs.
- [asr-baseline-consolidation-2026-09-26.md](../research/asr-baseline-consolidation-2026-09-26.md) — Saved ASR comparison, validation alignment, and local inference blockers.
- [translation-quality-2026-09-26.md](../research/translation-quality-2026-09-26.md) — Development-only translation metrics and NLLB runtime preflight.
- [retrieval-quality-2026-09-25.md](../research/retrieval-quality-2026-09-25.md) — Development retrieval scores and dense-model blockers.
- [generation-quality-2026-09-25.md](../research/generation-quality-2026-09-25.md) — mT0 generation diagnostics and historical test limits.
- [corpus-preparation-status.md](../research/corpus-preparation-status.md) — Chronological corpus-preparation log.
- [internet-archive-intake-2026-10-03.md](../research/internet-archive-intake-2026-10-03.md) — Internet Archive intake ledger, source checksums, rights notes, and media inventory.
- [internet-archive-intake-quality-2026-10-04.md](../research/internet-archive-intake-quality-2026-10-04.md) — Automated OCR/media profile and cross-dedup against the canonical cleaned text view; identifies what remains local and unverified.
- [internet-archive-source-disposition-2026-10-04.md](../research/internet-archive-source-disposition-2026-10-04.md) — Item-by-item Archive metadata claims, expanded 4,011-page inventory, source-linked local review views, and duplicate links to already-ingested records.
- [internet-archive-source-disposition-2026-10-04.json](../research/internet-archive-source-disposition-2026-10-04.json) — Machine-readable, metadata-only Archive source register; extracted page/media content remains in ignored local review indexes.
- [garhwali-data-expansion-2026-09-29.md](../research/garhwali-data-expansion-2026-09-29.md) — Deduplicated, rights-documented v0.2.0 Garhwali-only source intake.
- [garhwali-web-goldmines-2026-09-30.md](../research/garhwali-web-goldmines-2026-09-30.md) — Tenth-wave web acquisition, exact deduplication, candidate language/rights status, and repeatable local refresh workflow.

## How to keep the docs consistent

- Treat `finalreport.md` as the current release decision and consolidated audit summary.
- Treat `research/benchmark-research-status-2026-09-25.md` as the measured benchmark/research scorecard with later dated addenda; older experiment reports are historical snapshots.
- The latest broad benchmark scorecard refresh is dated 2026-09-30; the Meta Omnilingual ASR validation and adaptation addenda are dated 2026-10-04/05. These are development diagnostics, not independent final accuracy; no native-language adjudications have been completed.
- Keep dated research reports as records of the data and model version used at that time. Update the current status docs when new evidence supersedes them; do not rewrite history.
- Treat `release/v0.1.0/`, `release/v0.1.1/`, and `release/v0.2.0/` as frozen snapshots. The live Hub corpus is v0.2.7 at commit [`1f7b2ce`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/1f7b2ceed1b743412b75d6288757e1d2cadac9c4); it adds the `paharili_gbm` config with 14,988 normalized-unique sentences, and the v0.2.6 paths remain present. The candidate passed package preflight and all 816 project tests, and three rows stream from the published commit. Final Viewer checks confirm all 29 split views, 29 Parquet exports, and enabled preview, viewer, search, filter, and statistics; PahariLI sample rows are visible. The public `catalog` still has 23,448 metadata-only text entries. See the [v0.2.7 publication report](../research/huggingface-corpus-v0.2.7-release-2026-10-06.md), the [v0.2.6 publication report](../research/huggingface-corpus-v0.2.6-release-2026-10-05.md), and the [v0.2.6 schema/card fix report](../research/huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md). The Internet Archive acquisition dated 3–4 October remains local-only and is not in either package; the latest local inventory and item decisions are in the Archive source-disposition report.
- Keep dataset-card and policy copies inside each Hugging Face package aligned with the root policies when preparing a new package.
- The historical v0.2.5 corpus contains 32,072 exact-unique parent texts; its 246-row `text_resources` and 1,647-row `text_expansion` views surface existing catalog values, not new source acquisition. V0.2.5 adds no source text; it makes upstream held-out-source overlap explicit while preserving all rows. See the [release verification](../research/huggingface-corpus-v0.2.5-release-2026-10-05.md) and source-expansion report. The frozen v0.2.0 snapshot remains documented below.
- The v0.2.1 rights-filtered corpus builds on the earlier rights-resolution snapshot at commit [`53c1ce9`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53c1ce9baa07e6fb05722e5a1ed750f33096124b) and docs amendment [`f2def9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/f2def9e717390008ebf7aac05decebf1c264fa98). Its 19,466 unresolved full texts remain outside public content and are accounted for in the rights-filtered metadata index; see the rights log for counts and source-specific next actions.
- The rights review found a CC BY-SA 4.0 Garhwali GHMNT edition by The Love Fellowship; it is distinct from the Wycliffe version and is not yet mapped to the scripture lines in PahariLI. See the source-by-source rights log before changing any PahariLI release decision.
- For the next source wave, `PIPELINE.md` documents one checkpointed command that ingests a pinned wave, refreshes all derived views and figures, and stages a separately versioned additive Hub upload.
- Add an entry here when adding or removing a shared project Markdown file. The generated file map covers the Git-visible and non-ignored file inventory; this index focuses on project documentation.

## Release snapshot v0.2.0

- [`release/v0.2.0/README.md`](../release/v0.2.0/README.md) — v0.2.0 release summary, source intake, package counts, and verification.
- [`release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/README.md`](../release/v0.2.0/artifacts/data/huggingface/garhwali-language-lab/README.md) — v0.2.0 public Hugging Face dataset card.
- [`release/v0.2.0/final-audit.json`](../release/v0.2.0/final-audit.json) — Machine-readable final release audit.
- [`release/v0.2.0/huggingface-publication.json`](../release/v0.2.0/huggingface-publication.json) — Verified Hub commit, file hashes, and Dataset Viewer status.
- [`research/garhwali-data-expansion-2026-09-29.md`](../research/garhwali-data-expansion-2026-09-29.md) — Source-level data addition and deduplication report.
- [`research/garhwali-web-goldmines-2026-09-30.md`](../research/garhwali-web-goldmines-2026-09-30.md) — Tenth-wave web candidate intake and repeatable corpus-refresh report.

## Exact duplicate files

The four exact-duplicate groups below are package/release copies, not competing current reports. They remain in place for self-contained packages and reproducible release snapshots.
- `ATTRIBUTION.md`: root copy and v0.1.0/v0.1.1 release copies.
- `LICENSE_POLICY.md`: root copy and v0.1.1 release copy.
- `REMOVAL_POLICY.md`: root copy and v0.1.0/v0.1.1 release copies.
- Online-ingestion report: v0.1.0 and v0.1.1 release copies.

## Full Git-tracked Markdown inventory

### Root-level docs

- [`ATTRIBUTION.md`](../ATTRIBUTION.md) — Dataset attribution
- [`DATASET_CARD.md`](../DATASET_CARD.md) — Dataset card: Garhwali Language Lab
- [`DEEP_DIVE_FINAL_AUDIT.md`](../DEEP_DIVE_FINAL_AUDIT.md) — Garhwali Language Lab — deep final audit
- [`LICENSE_POLICY.md`](../LICENSE_POLICY.md) — Corpus redistribution and model-use policy
- [`PIPELINE.md`](../PIPELINE.md) — Garhwali ingestion pipeline
- [`README.md`](../README.md) — 🏔️ Garhwali Language Lab
- [`REMOVAL_POLICY.md`](../REMOVAL_POLICY.md) — Data correction and removal policy
- [`finalreport.md`](../finalreport.md) — Garhwali Language Lab — final review report
- [`report-source.md`](../report-source.md) — GarhwaliCorpus source inventory — research note

### Corpus documentation

- [`corpus/README.md`](../corpus/README.md) — Garhwali corpus: first ingestion

### Implementation plans

- [`docs/superpowers/plans/2026-09-10-corpus-preparation.md`](../docs/superpowers/plans/2026-09-10-corpus-preparation.md) — Garhwali Corpus Preparation Implementation Plan
- [`docs/superpowers/plans/2026-09-18-final-release-review.md`](../docs/superpowers/plans/2026-09-18-final-release-review.md) — Final release review plan
- [`docs/superpowers/plans/2026-09-24-model-accuracy-audit.md`](../docs/superpowers/plans/2026-09-24-model-accuracy-audit.md) — Model Accuracy and Evaluation Lineage Audit Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-accuracy-final-report.md`](../docs/superpowers/plans/2026-09-24-model-accuracy-final-report.md) — Garhwali Model Accuracy Final Report Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-accuracy-improvement.md`](../docs/superpowers/plans/2026-09-24-model-accuracy-improvement.md) — Garhwali Model Accuracy Improvement Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-asr-accuracy.md`](../docs/superpowers/plans/2026-09-24-model-asr-accuracy.md) — Garhwali ASR Accuracy Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-generation-translation.md`](../docs/superpowers/plans/2026-09-24-model-generation-translation.md) — Garhwali Generation and Translation Quality Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-retrieval.md`](../docs/superpowers/plans/2026-09-24-model-retrieval.md) — Garhwali Retrieval Quality Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-text-understanding.md`](../docs/superpowers/plans/2026-09-24-model-text-understanding.md) — Garhwali Text Representation Quality Implementation Plan
- [`docs/superpowers/plans/2026-09-24-model-tts-readiness.md`](../docs/superpowers/plans/2026-09-24-model-tts-readiness.md) — Garhwali TTS Readiness Audit Implementation Plan

### Design specifications

- [`docs/superpowers/specs/2026-09-24-model-accuracy-improvement-design.md`](../docs/superpowers/specs/2026-09-24-model-accuracy-improvement-design.md) — Garhwali model accuracy improvement design

### Incoming-material guidance

- [`incoming/pdfs/README.md`](../incoming/pdfs/README.md) — PDF intake

### Release snapshot v0.1.0

- [`release/v0.1.0/README.md`](../release/v0.1.0/README.md) — Garhwali Language Lab v0.1.0
- [`release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md`](../release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md) — Dataset attribution
- [`release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md`](../release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md) — Corpus redistribution and model-use policy
- [`release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/README.md`](../release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/README.md) — Garhwali Language Lab
- [`release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md`](../release/v0.1.0/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md) — Data correction and removal policy
- [`release/v0.1.0/artifacts/data/processed/evaluation/garhwali_bench/report.md`](../release/v0.1.0/artifacts/data/processed/evaluation/garhwali_bench/report.md) — GarhwaliBench v0.1 experimental baseline
- [`release/v0.1.0/artifacts/outputs/online-ingestion-2026-09-07/report.md`](../release/v0.1.0/artifacts/outputs/online-ingestion-2026-09-07/report.md) — Garhwali online ingestion report

### Release snapshot v0.1.1

- [`release/v0.1.1/README.md`](../release/v0.1.1/README.md) — Garhwali Language Lab v0.1.1
- [`release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md`](../release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/ATTRIBUTION.md) — Dataset attribution
- [`release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md`](../release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/LICENSE_POLICY.md) — Corpus redistribution and model-use policy
- [`release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/README.md`](../release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/README.md) — Garhwali Language Lab
- [`release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md`](../release/v0.1.1/artifacts/data/huggingface/garhwali-language-lab/REMOVAL_POLICY.md) — Data correction and removal policy
- [`release/v0.1.1/artifacts/data/processed/evaluation/garhwali_bench/report.md`](../release/v0.1.1/artifacts/data/processed/evaluation/garhwali_bench/report.md) — GarhwaliBench v0.1 experimental baseline
- [`release/v0.1.1/artifacts/outputs/online-ingestion-2026-09-07/report.md`](../release/v0.1.1/artifacts/outputs/online-ingestion-2026-09-07/report.md) — Garhwali online ingestion report

### Research archive

- [`research/product-progress-2026-09-29.md`](../research/product-progress-2026-09-29.md) — Product progress graphs across corpus, benchmark, research, models, community, API, and public infrastructure
- [`research/all-data-package-2026-09-15.md`](../research/all-data-package-2026-09-15.md) — Complete all-data package
- [`research/all-data-package-2026-09-19.md`](../research/all-data-package-2026-09-19.md) — Complete all-data package — 2026-09-19
- [`research/asr-baseline-2026-09-10.md`](../research/asr-baseline-2026-09-10.md) — Garhwali ASR baseline
- [`research/asr-curriculum-stage0-2026-09-14.md`](../research/asr-curriculum-stage0-2026-09-14.md) — ASR curriculum stage-0 selection
- [`research/asr-curriculum-stage1-pilot-2026-09-14.md`](../research/asr-curriculum-stage1-pilot-2026-09-14.md) — ASR curriculum stage-1 machine-label pilot
- [`research/asr-training-curriculum-2026-09-14.md`](../research/asr-training-curriculum-2026-09-14.md) — Confidence-aware ASR training curriculum
- [`research/asr-validation-error-analysis-2026-09-24.md`](../research/asr-validation-error-analysis-2026-09-24.md) — Saved ASR validation comparison
- [`research/asr-heldout-lineage-audit-2026-09-28.md`](../research/asr-heldout-lineage-audit-2026-09-28.md) — Paired post-hoc comparison of five saved ASR runs on the same held-out rows
- [`research/asr-weighted-batch-ablation-2026-09-14.md`](../research/asr-weighted-batch-ablation-2026-09-14.md) — ASR normalized weighted-batch ablation
- [`research/asr-weighted-trainer-2026-09-14.md`](../research/asr-weighted-trainer-2026-09-14.md) — Weighted curriculum trainer and dry-run audit
- [`research/automated-pre-release-quality-plan.md`](../research/automated-pre-release-quality-plan.md) — Automated Pre-release Quality Plan
- [`research/benchmark-research-status-2026-09-25.md`](../research/benchmark-research-status-2026-09-25.md) — Benchmark and research suite: measured status
- [`research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md`](../research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md) — Current component and item-level rights inventory for GarhwaliBench v0.2
- [`research/retrieval-source-page-cluster-uncertainty-2026-09-28.md`](../research/retrieval-source-page-cluster-uncertainty-2026-09-28.md) — Clustered uncertainty for XORQA BM25 development retrieval
- [`research/retrieval-miss-analysis-2026-09-28.md`](../research/retrieval-miss-analysis-2026-09-28.md) — Gold-passage availability and BM25 miss types for saved XORQA dev queries
- [`research/generation-output-diagnostics-2026-09-28.md`](../research/generation-output-diagnostics-2026-09-28.md) — Task-local output concentration and structural checks for saved mT0 validation predictions
- [`research/benchmark-model-roadmap.md`](../research/benchmark-model-roadmap.md) — Garhwali Benchmark and Model Research Roadmap
- [`research/v0.2-public-announcement-roadmap-2026-09-29.md`](../research/v0.2-public-announcement-roadmap-2026-09-29.md) — v0.2.0 public announcement readiness roadmap
- [`research/benchmark-parent-safe-split-audit-2026-09-28.md`](../research/benchmark-parent-safe-split-audit-2026-09-28.md) — Parent-document split correction and source-family audit
- [`research/benchmark-overlap-adjudication-2026-09-26.md`](../research/benchmark-overlap-adjudication-2026-09-26.md) — Reviewed XORQA split-overlap findings and retained-row usage labels
- [`research/benchmark-v02-export-2026-09-26.md`](../research/benchmark-v02-export-2026-09-26.md) — Initial local v0.2 adapter/export snapshot
- [`research/garhwali-bench-v0.2-schema-contract.md`](../research/garhwali-bench-v0.2-schema-contract.md) — Draft v0.2 schema, metrics, and validation contract
- [`research/issues&improvement plan.md`](../research/issues%26improvement%20plan.md) — Benchmark and model roadmap issues & improvement plan
- [`research/asr-baseline-consolidation-2026-09-26.md`](../research/asr-baseline-consolidation-2026-09-26.md) — ASR baseline consolidation — 2026-09-26
- [`research/controlled-modeling-2026-09-12.md`](../research/controlled-modeling-2026-09-12.md) — Controlled Garhwali modeling: continuation and instruction tuning
- [`research/controlled-text-scaling-2026-09-11.md`](../research/controlled-text-scaling-2026-09-11.md) — Controlled Garhwali text-scaling experiment
- [`research/corpus-preparation-status.md`](../research/corpus-preparation-status.md) — Corpus preparation status
- [`research/cultural-ingestion-report.md`](../research/cultural-ingestion-report.md) — Garhwali cultural-source ingestion report
- [`research/dataset-splits-2026-09-10.md`](../research/dataset-splits-2026-09-10.md) — Garhwali dataset split status
- [`research/gap-closure-plan.md`](../research/gap-closure-plan.md) — Garhwali data gap-closure plan
- [`research/garhwali-access-blockers-2026-09-10.md`](../research/garhwali-access-blockers-2026-09-10.md) — Garhwali access blockers after VAANI
- [`research/garhwali-bench-v0.1-2026-09-11.md`](../research/garhwali-bench-v0.1-2026-09-11.md) — GarhwaliBench v0.1 experimental baseline
- [`research/garhwali-folklore-internet-audit-2026-09-10.md`](../research/garhwali-folklore-internet-audit-2026-09-10.md) — Garhwali folklore and folk-literature Internet audit
- [`research/garhwali-poetry-plays-inventory-2026-09-15.md`](../research/garhwali-poetry-plays-inventory-2026-09-15.md) — Garhwali poetry and plays inventory — 2026-09-15
- [`research/garhwali-scholarly-guide.md`](../research/garhwali-scholarly-guide.md) — Garhwali scholarly guide for corpus design
- [`research/huggingface-release-overlap-audit-2026-09-24.md`](../research/huggingface-release-overlap-audit-2026-09-24.md) — Hugging Face source overlap and release audit
- [`research/incoming-pdf-ingestion-2026-09-16.md`](../research/incoming-pdf-ingestion-2026-09-16.md) — Incoming PDF ingestion — 2026-09-16
- [`research/incoming-pdf-reocr-pilot-2026-09-17.md`](../research/incoming-pdf-reocr-pilot-2026-09-17.md) — Incoming PDF multi-layout OCR pilot
- [`research/indicbert-balanced-domain-2026-09-16.md`](../research/indicbert-balanced-domain-2026-09-16.md) — Balanced general/book IndicBERTv2 continuation
- [`research/indicbert-cloud-continuation-2026-09-16.md`](../research/indicbert-cloud-continuation-2026-09-16.md) — IndicBERTv2 Garhwali cloud continuation
- [`research/indicbert-pdf-domain-2026-09-16.md`](../research/indicbert-pdf-domain-2026-09-16.md) — IndicBERTv2 incoming-PDF domain continuation
- [`research/indicbert-pdf-domain-extended-2026-09-16.md`](../research/indicbert-pdf-domain-extended-2026-09-16.md) — Extended incoming-PDF domain continuation
- [`research/intensive-quality-audit-2026-09-14.md`](../research/intensive-quality-audit-2026-09-14.md) — Intensive quality audit
- [`research/language-quality-status-2026-09-10.md`](../research/language-quality-status-2026-09-10.md) — Garhwali language-quality status
- [`research/model-accuracy-lineage-2026-09-24.md`](../research/model-accuracy-lineage-2026-09-24.md) — Model accuracy split and evaluation lineage audit
- [`research/model-accuracy-lineage-2026-09-28.md`](../research/model-accuracy-lineage-2026-09-28.md) — Current split and saved-prediction lineage audit
- [`research/task-result-eligibility-2026-09-28.md`](../research/task-result-eligibility-2026-09-28.md) — Current task-result eligibility decisions
- [`research/model-accuracy-preflight-2026-09-24.md`](../research/model-accuracy-preflight-2026-09-24.md) — Model accuracy improvement status and local preflight
- [`research/model-assisted-text-cleanup-2026-09-11.md`](../research/model-assisted-text-cleanup-2026-09-11.md) — Model-assisted text cleanup and ablation
- [`research/mt0-16384-validation-2026-09-16.md`](../research/mt0-16384-validation-2026-09-16.md) — mT0 16,384-step validation continuation
- [`research/mt0-32768-partial-2026-09-16.md`](../research/mt0-32768-partial-2026-09-16.md) — Initial canceled mT0 continuation attempt; later seed-43 recovery is documented
- [`research/generation-quality-2026-09-25.md`](../research/generation-quality-2026-09-25.md) — Reconciled three-seed mT0 generation quality and test history
- [`research/mt0-cloud-continuation-2026-09-16.md`](../research/mt0-cloud-continuation-2026-09-16.md) — mT0 Garhwali instruction continuation
- [`research/mt0-extended-validation-2026-09-16.md`](../research/mt0-extended-validation-2026-09-16.md) — Extended mT0 validation-only continuation
- [`research/mt0-validation-run-manifest-2026-09-27.md`](../research/mt0-validation-run-manifest-2026-09-27.md) — Reconciled saved mT0 validation predictions and per-seed manifests
- [`research/multilingual-model-audit-2026-09-11.md`](../research/multilingual-model-audit-2026-09-11.md) — Multilingual model audit
- [`research/native-reference-review-readiness-2026-09-15.md`](../research/native-reference-review-readiness-2026-09-15.md) — Native-reference review readiness
- [`research/ocr-proposal-validation-2026-09-16.md`](../research/ocr-proposal-validation-2026-09-16.md) — OCR and spelling proposal validation
- [`research/outreach-drafts.md`](../research/outreach-drafts.md) — Outreach drafts for Garhwali dataset access
- [`research/popular-song-ingestion-2026-09-15.md`](../research/popular-song-ingestion-2026-09-15.md) — Garhwali popular-song ingestion — 2026-09-15
- [`research/retrieval-baseline-2026-09-11.md`](../research/retrieval-baseline-2026-09-11.md) — Garhwali cross-lingual retrieval baseline
- [`research/retrieval-quality-2026-09-25.md`](../research/retrieval-quality-2026-09-25.md) — Current dev-only retrieval rerun, corrected zero-score BM25 handling, and dense-model preflight
- [`research/semantic-duplicate-audit-2026-09-16.md`](../research/semantic-duplicate-audit-2026-09-16.md) — Semantic duplicate and split-leakage audit
- [`research/semantic-duplicate-refinement-2026-09-16.md`](../research/semantic-duplicate-refinement-2026-09-16.md) — Semantic duplicate refinement
- [`research/social-media-ingestion-2026-09-10.md`](../research/social-media-ingestion-2026-09-10.md) — Garhwali social-media ingestion
- [`research/speech-baseline-comparison-2026-09-11.md`](../research/speech-baseline-comparison-2026-09-11.md) — Garhwali speech baseline comparison
- [`research/sravaani-adaptation-evaluation-2026-09-16.md`](../research/sravaani-adaptation-evaluation-2026-09-16.md) — SraVaani Garhwali adaptation evaluation
- [`research/sravaani-adaptation-readiness-2026-09-14.md`](../research/sravaani-adaptation-readiness-2026-09-14.md) — SraVaani Garhwali adaptation readiness
- [`research/sravaani-audio-grounded-review-2026-09-14.md`](../research/sravaani-audio-grounded-review-2026-09-14.md) — SraVaani structural-outlier audio evidence
- [`research/sravaani-budget-sweep-2026-09-16.md`](../research/sravaani-budget-sweep-2026-09-16.md) — SraVaani Garhwali budget sweep
- [`research/sravaani-confidence-integration-2026-09-14.md`](../research/sravaani-confidence-integration-2026-09-14.md) — SraVaani confidence-aware manifest integration
- [`research/sravaani-expanded-human-2026-09-16.md`](../research/sravaani-expanded-human-2026-09-16.md) — Expanded human-transcript SraVaani experiment
- [`research/sravaani-recovery-adjudication-2026-09-14.md`](../research/sravaani-recovery-adjudication-2026-09-14.md) — SraVaani risky-draft three-checkpoint review
- [`research/sravaani-recovery-confidence-2026-09-13.md`](../research/sravaani-recovery-confidence-2026-09-13.md) — SraVaani recovery confidence calibration
- [`research/sravaani-refined-61-result-2026-09-16.md`](../research/sravaani-refined-61-result-2026-09-16.md) — SraVaani refined 61-trial result
- [`research/sravaani-transcript-recovery-2026-09-13.md`](../research/sravaani-transcript-recovery-2026-09-13.md) — SraVaani transcript recovery routing
- [`research/structured-rights-web-review-2026-09-23.md`](../research/structured-rights-web-review-2026-09-23.md) — Structured-record rights review — 2026-09-23
- [`research/text-accuracy-review-2026-09-15.md`](../research/text-accuracy-review-2026-09-15.md) — Source-grounded text accuracy review
- [`research/text-noise-audit-2026-09-16.md`](../research/text-noise-audit-2026-09-16.md) — Model-backed text noise audit
- [`research/text-release-quality-2026-09-16.md`](../research/text-release-quality-2026-09-16.md) — Text release quality audit
- [`research/text-source-rights-audit-2026-09-15.md`](../research/text-source-rights-audit-2026-09-15.md) — Text source and rights audit
- [`research/thematic-vocabulary-report.md`](../research/thematic-vocabulary-report.md) — Garhwali thematic vocabulary web pass
- [`research/translation-baseline-2026-09-11.md`](../research/translation-baseline-2026-09-11.md) — Garhwali-to-English translation baseline
- [`research/translation-quality-2026-09-26.md`](../research/translation-quality-2026-09-26.md) — Development-only translation baseline refresh and NLLB preflight
- [`research/vaani-audit-2026-09-09.md`](../research/vaani-audit-2026-09-09.md) — VAANI Garhwali metadata audit
- [`research/vaani-collection-completion-2026-09-09.md`](../research/vaani-collection-completion-2026-09-09.md) — VAANI Garhwali collection completion
- [`research/vaani-full-use-plan.md`](../research/vaani-full-use-plan.md) — Project VAANI: remaining work for full Garhwali use
- [`research/xhigh-final-data-audit-2026-09-10.md`](../research/xhigh-final-data-audit-2026-09-10.md) — X-high final Garhwali data audit

### Review workflow

- [`review/README.md`](../review/README.md) — Native-review workflow

### Script documentation

- [`scripts/README.md`](../scripts/README.md) — Script layout

### Source inventories and captured references

- [`sources/manual/garhwali-literature-writers-2026-09-16.md`](../sources/manual/garhwali-literature-writers-2026-09-16.md) — User-supplied Garhwali literature and writers leads
- [`sources/online/README.md`](../sources/online/README.md) — Online ingestion register
- [`sources/online/deep-search-catalog.md`](../sources/online/deep-search-catalog.md) — Garhwali public-source search catalog
- [`sources/online/source-audit-2026-09-08.md`](../sources/online/source-audit-2026-09-08.md) — Garhwali source audit — started 2026-09-08, updated 2026-09-09

### Task notes

- [`tasks/lessons.md`](../tasks/lessons.md) — Lessons
- [`tasks/todo.md`](../tasks/todo.md) — Code structure cleanup
