# Documentation index

This page is the map for the project’s Markdown documentation. It inventories all **113 Markdown files tracked by Git as of 2026-09-25**; this index is additional. Ignored caches, downloaded dependency documentation, and local model outputs are not repository documentation.

## Read these first

- [README.md](../README.md) — Project overview and current narrative.
- [finalreport.md](../finalreport.md) — Authoritative release verdict, counts, and blockers.
- [DEEP_DIVE_FINAL_AUDIT.md](../DEEP_DIVE_FINAL_AUDIT.md) — Detailed code, data, and release audit.
- [benchmark-research-status-2026-09-25.md](../research/benchmark-research-status-2026-09-25.md) — Measured benchmark and model-research status.
- [corpus-preparation-status.md](../research/corpus-preparation-status.md) — Chronological corpus-preparation log.

## How to keep the docs consistent

- Treat `finalreport.md` as the current release decision and consolidated audit summary.
- Treat `research/benchmark-research-status-2026-09-25.md` as the measured benchmark/research scorecard; older experiment reports are historical snapshots.
- Keep dated research reports as records of the data and model version used at that time. Update the current status docs when new evidence supersedes them; do not rewrite history.
- Treat `release/v0.1.0/` and `release/v0.1.1/` as frozen snapshots. Their repeated cards and reports are intentional so each release package is self-contained.
- Keep dataset-card and policy copies inside each Hugging Face package aligned with the root policies when preparing a new package.
- Add an entry here when adding or removing a tracked Markdown file.

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

- [`research/all-data-package-2026-09-15.md`](../research/all-data-package-2026-09-15.md) — Complete all-data package
- [`research/all-data-package-2026-09-19.md`](../research/all-data-package-2026-09-19.md) — Complete all-data package — 2026-09-19
- [`research/asr-baseline-2026-09-10.md`](../research/asr-baseline-2026-09-10.md) — Garhwali ASR baseline
- [`research/asr-curriculum-stage0-2026-09-14.md`](../research/asr-curriculum-stage0-2026-09-14.md) — ASR curriculum stage-0 selection
- [`research/asr-curriculum-stage1-pilot-2026-09-14.md`](../research/asr-curriculum-stage1-pilot-2026-09-14.md) — ASR curriculum stage-1 machine-label pilot
- [`research/asr-training-curriculum-2026-09-14.md`](../research/asr-training-curriculum-2026-09-14.md) — Confidence-aware ASR training curriculum
- [`research/asr-validation-error-analysis-2026-09-24.md`](../research/asr-validation-error-analysis-2026-09-24.md) — Saved ASR validation comparison
- [`research/asr-weighted-batch-ablation-2026-09-14.md`](../research/asr-weighted-batch-ablation-2026-09-14.md) — ASR normalized weighted-batch ablation
- [`research/asr-weighted-trainer-2026-09-14.md`](../research/asr-weighted-trainer-2026-09-14.md) — Weighted curriculum trainer and dry-run audit
- [`research/automated-pre-release-quality-plan.md`](../research/automated-pre-release-quality-plan.md) — Automated Pre-release Quality Plan
- [`research/benchmark-research-status-2026-09-25.md`](../research/benchmark-research-status-2026-09-25.md) — Benchmark and research suite: measured status
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
- [`research/model-accuracy-preflight-2026-09-24.md`](../research/model-accuracy-preflight-2026-09-24.md) — Model accuracy improvement status and local preflight
- [`research/model-assisted-text-cleanup-2026-09-11.md`](../research/model-assisted-text-cleanup-2026-09-11.md) — Model-assisted text cleanup and ablation
- [`research/mt0-16384-validation-2026-09-16.md`](../research/mt0-16384-validation-2026-09-16.md) — mT0 16,384-step validation continuation
- [`research/mt0-32768-partial-2026-09-16.md`](../research/mt0-32768-partial-2026-09-16.md) — Partial mT0 32,768-step continuation
- [`research/mt0-cloud-continuation-2026-09-16.md`](../research/mt0-cloud-continuation-2026-09-16.md) — mT0 Garhwali instruction continuation
- [`research/mt0-extended-validation-2026-09-16.md`](../research/mt0-extended-validation-2026-09-16.md) — Extended mT0 validation-only continuation
- [`research/multilingual-model-audit-2026-09-11.md`](../research/multilingual-model-audit-2026-09-11.md) — Multilingual model audit
- [`research/native-reference-review-readiness-2026-09-15.md`](../research/native-reference-review-readiness-2026-09-15.md) — Native-reference review readiness
- [`research/ocr-proposal-validation-2026-09-16.md`](../research/ocr-proposal-validation-2026-09-16.md) — OCR and spelling proposal validation
- [`research/outreach-drafts.md`](../research/outreach-drafts.md) — Outreach drafts for Garhwali dataset access
- [`research/popular-song-ingestion-2026-09-15.md`](../research/popular-song-ingestion-2026-09-15.md) — Garhwali popular-song ingestion — 2026-09-15
- [`research/retrieval-baseline-2026-09-11.md`](../research/retrieval-baseline-2026-09-11.md) — Garhwali cross-lingual retrieval baseline
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
