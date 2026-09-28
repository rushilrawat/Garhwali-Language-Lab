# Garhwali Language Lab — deep final audit

**Audit date:** 2026-09-28
**Scope:** current working tree, generated public/all-data Hugging Face package snapshots, model-data selection scripts, release and preflight validators, research status, and test coverage.
**Purpose:** identify defects that can make corpus claims, source reuse, evaluation, or model-quality conclusions incorrect; record verified fixes and the remaining release gates.

## Current conclusion

The public Hugging Face corpus now combines the rights-filtered content profile with a content-free index of the complete all-data archive. The index has one reference row for each of 257,807 archive rows, plus 590 deduplicated sources and 277,637 source links. It includes factual and bibliographic metadata, but no restricted source text or media. The license-classifier defect is fixed; the content profile excludes records without compatible reuse evidence while the full payload remains in local all-data. Native-speaker review and dialect annotation are deferred by the project owner, so language and benchmark claims remain automated candidates. Future IndicBERT head/LoRA runs and text-scaling runs default to the strict recommended data view. Historical broad-corpus results remain tied to their original inputs.

Phase 8 result labels are now reconciled: test rows with matched saved predictions and the aggregate-scored 398-row internal text set are historical-only; CrossSum and Meta Omnilingual test exposure remains unresolved. No task result is independent-final-eligible. See the [result eligibility report](research/task-result-eligibility-2026-09-28.md) and [fresh lineage audit](research/model-accuracy-lineage-2026-09-28.md).

The package inventory reports 257,807 rows across overlapping all-data views and 146,684 content rows across 12 public config/split entries. Public reference tables add 257,807 archive-row references, 590 sources, and 277,637 record-to-source links. Counts include multiple representations of the same source material and are not unique-example totals. The corpus has 28,755 exact-unique parent texts and 114,064 prepared text segments. All-data includes every collected text value (zero catalog redactions); the public content profile redacts 24,566 values and omits full content for all 216 structured rows without a compatible public-rights basis. Those structured records are now present in the public reference index as metadata and source pointers. The index marks record-level rights `not_recorded` for 228,836 rows; linked source terms still require review before reuse.

## Verified findings

### Fixed critical defect — noncommercial Creative Commons sources passed the public-rights classifier

`scripts/build_huggingface_dataset.py:is_publishable_provenance` treats the substring `cc-by-` as sufficient evidence of an open license. It does not reject the `NC` (noncommercial) or `ND` (no derivatives) variants. A provenance record for PanLex labeled `CC-BY-NC-SA-4.0` has no blocking rights marker that compensates for this, so the classifier returns publishable.

**Measured effect and correction:** the prior public-profile build exposed **13 segment rows** from `panlex_gbm` carrying a CC-BY-NC-SA license. The license classifier is fixed, regression-tested, and both packages were rebuilt; the current audit reports zero general text public-rights failures. The all-data package retains the full data locally. At the time of the 2026-09-26 review, remote publication had not occurred; the subsequent public reference-index release is documented in the Hugging Face status at the end of this audit.

**Remediation complete:** restrictive CC variants are rejected before accepting an open-license marker; regression tests cover NC, ND, valid CC-BY, and the exact MIT identifier. The rebuilt public profile has zero general text-rights failures.

### High — 216 structured knowledge records still lack public-rights evidence

The public and all-data packages contain 216 records in six configurations: geography (50), historical terms (36), literary people (26), literary works (66), popular songs (30), and university research (8). Source hints previously used inconsistent field names such as `evidence`, `source_refs`, `source_ids`, `source_url`, `wikipedia_url`, `lyrics_sources`, and `translation_sources`. The builder now maps source pointers into standardized `provenance`, adds explicit quality/review status, and records rights without inventing a license. A web review has now examined the 186 previously unassessed geography, history, people, works, and university records. Some component sources carry reuse terms, but no whole-record public-rights basis was established for those mixed-source records. Current audit counts are **0 missing provenance**, **0 missing quality metadata**, **0 unreviewed rights statuses**, and **216 rows without compatible public rights**.

The release audit and cloud preflight enforce these fields. The all-data/private preflight passes. The public content builder omits the full payloads for all six structured configurations until compatible rights are established; the public metadata-reference index includes all 216 records without treating them as cleared. The complete records remain in all-data.

**Additional traceability fix:** a deeper row-level check found that some geography evidence labels and a literary capture reference still exported as internal IDs without a URL or capture fingerprint. Geography evidence IDs now resolve through the geography catalog, and shared source IDs inherit the best available metadata across the project's structured-source catalogs. The regenerated all-data package has **zero untraceable structured rows** and passes cloud preflight. This improves citation traceability; it does not establish redistribution rights.

**Remaining:** establish source-specific rights evidence for every field if these structured records are to be added to a later public version. A source URL alone is not a license. Their exclusion resolves this release's package gate, not the underlying rights status. Findings and exact source links are in [`research/structured-rights-web-review-2026-09-23.md`](research/structured-rights-web-review-2026-09-23.md); all 216 records remain intact in all-data.

### High — historical broad text-model runs do not establish Garhwali-only quality

`scripts/run_text_scaling_experiment.py`, `scripts/run_indicbert_adaptation.py`, and its LoRA variant previously defaulted to the broad `splits/text/train.jsonl` file. The text-scaling and IndicBERT head/LoRA defaults now use the checksum-addressed recommended view. The strict view has **7,490 of 106,915 rows (7.0%)** in training; the historical all-data split has 31,392 Garhwali candidates, 47,821 mixed-language, 14,918 review, and 13,036 non-Garhwali context rows. These categories may overlap with quality tiers, so do not sum them as mutually exclusive classes.

Historical experiments remain valid only for their original broad-data question; they are not evidence of Garhwali-only model quality. The strict-default IndicBERT configuration has not yet been trained, and its improvement over historical runs is unknown.

**Code remediation complete:** preserve historical results and use strict checksum-addressed train/validation defaults with separate output paths. A new neural study has not been run; record hashes and composition if local compute is available.

### High — text-model experiment default evaluated the wrong held-out set

Before this audit, `scripts/run_text_scaling_experiment.py` defaulted to `data/processed/model_ready/splits/evaluation/text_candidate.jsonl` (3,603 rows). The historical `text_scaling.json` actually records a 2,492-row held-out artifact. GarhwaliBench separately filters its candidates to 398 strict automated text records at `data/processed/evaluation/garhwali_bench/internal_text.jsonl`. Neither the old 2,492-row report nor the former 3,603-row default is the current 398-row GarhwaliBench test.

**Remediation verified:** the default uses the recommended 7,490-row train view, 377-row validation view, and exact 398-row frozen benchmark. Broad and recommended character n-gram baselines were run on the same 377/398 validation/test artifacts. The recommended corpus reached test cross-entropy **2.3233** (perplexity **10.2095**), compared with **2.5011** (perplexity **12.1965**) for the broad corpus. This is a character n-gram signal, not proof of neural-model improvement.

### High — GarhwaliBench's character baseline used the wrong default training view

The benchmark builder still defaulted to the broad 106,915-row training split
after the text-scaling and IndicBERT workflows had moved to the recommended
7,490-row Garhwali view. Its headline baseline and training-overlap check
therefore did not describe the strict modeling view.

**Fixed and verified:** the builder now defaults to
`text_recommended/train.jsonl`, records the training row count and SHA-256, and
the final release audit rejects a broad training view. On the same 398-row
candidate and with the same character-bigram scorer, recommended training gets
2.647741 cross-entropy / **14.122106 perplexity** versus 2.833217 /
17.000058 for broad training. The separate controlled text-scaling experiment
uses a different character n-gram scoring implementation and reports 10.209546
versus 12.196482 perplexity; those scales must not be compared directly. These
are automated-candidate results, not native-language accuracy.

### Medium — one external benchmark text repeats across source splits

XORQA has one exact `text_normalized` duplicate across source `train` and `dev`
(`indicgenbench_xorqa:train:64` and `indicgenbench_xorqa:dev:296`). Neither row
is in test. The builder and final audit now recompute and expose the overlap;
both source rows remain present and the audit emits a warning. FLORES and
CrossSum have zero such groups.

### High — release index status could remain “ready” after a failed audit

The release finalizer synchronized the release index before running the final audit. The index status could therefore still say `release_ready_with_public_rights_filtered_export` while the audit subsequently failed. The index validator did not compare release readiness with the final-audit status.

**Remediation verified:** the finalizer synchronizes the index again after auditing; index status is blocked unless the final audit passes, and the index validator enforces this relationship. The current public audit reports zero text-rights failures and zero included structured records without rights basis. The v0.1.1 release index records `final_audit_status: passed` and `status: release_ready_with_public_rights_filtered_export`.

### High — native accuracy and dialect quality remain unmeasured

There are no completed native-speaker adjudications. The current benchmark remains an automated candidate: 398 text records and 112 speaker-safe ASR rows. Only 29 of 28,755 parent texts carry an explicit dialect label. The fixed SraVaani comparison reports 42.761% WER and 17.606% CER, but the reference set itself has not been independently adjudicated. This is a material limitation on claims about correctness, dialect coverage, and ASR quality.

**Disposition:** native-speaker adjudication and dialect annotation are deferred at the project owner's direction. Automated integrity is checked separately. Keep the benchmark labeled as an automated candidate; do not call it gold or make definitive native-accuracy claims.

### Medium — benchmark and package integrity checks are now recomputed

The final audit checks all six benchmark inputs and recomputes artifact hashes, counts, exact text/audio-hash and identified-speaker overlap, plus one preserved XORQA train/dev warning. It also recomputes every `recommended_for_training` value from language, quality, flags, and public-rights evidence. That audit did not group sibling segments by parent document. A subsequent audit found 50 parent documents / 1,523 rows crossing historical text splits; the split builder now groups parents before duplicate reassignment, and a separate candidate reports zero parent-document crossings. The historical release remains unchanged. See the [parent-safe split audit](research/benchmark-parent-safe-split-audit-2026-09-28.md).

Package manifests carry per-shard SHA-256 values; both the final audit and cloud preflight recalculate them. The audit recalculates exported text IDs from content and catalog IDs from text hashes. Current audit counts are zero shard-hash failures and zero text-ID failures.

**Remaining:** use an independently signed or separately published manifest if tamper evidence across release artifacts is required. Current hashes detect shard drift relative to the package manifest; this same-manifest check does not protect against an actor replacing both the shard and its manifest entry.

### Resolved — release identity matches the reviewed repository state

The package and release index identify themselves as `garhwali-language-lab-v0.1.1`; annotated tag `v0.1.1` resolves to the reviewed release commit. The historical `v0.1.0` tag is unchanged. The exact reviewed commit passed the recorded release checks.

### Medium — “all-data” and “public-profile” are different products

The all-data package preserves all 28,755 catalog text values, including restricted/right-pending material, for local or access-controlled research. The public content profile redacts 24,566 catalog values and withholds full content for 216 structured records with unresolved rights; the metadata-reference index points to all of them. The previous PanLex license leak has been fixed. Keep the distinction visible in cards, package manifests, and release reports.

### Fixed low-severity reporting defect — public preflight carried an all-data run ID

The cloud preflight used a constant `garhwali-hf-all-data-cloud-validation-v0.1` run ID for both package profiles, so the saved public preflight was mislabeled despite declaring `manifest_profile: public`. The run ID now includes the manifest profile, a regression test checks both names, and the public preflight artifact was regenerated as `garhwali-hf-public-cloud-validation-v0.1`. The regenerated public preflight passes; it excludes structured records without compatible public-rights evidence.

## Remediation order

1. **Rights correctness:** the NC/ND classifier fix is implemented; the public profile filters all 216 structured records without compatible rights evidence. Preserve them in all-data and add only after source-specific evidence is recorded.
2. **Release metadata gates:** standardized source pointers/review status and fail-closed public-rights checks are implemented and pass for v0.1.1.
3. **Model-data quality:** strict training view and strict-default scripts are ready; run a neural comparison against historical broad-data results on fixed evaluations.
4. **Audit integrity:** benchmark hashes/counts/leakage, package shard hashes, text IDs, and training recommendations are recomputed; an independently signed release manifest remains optional hardening.
5. **Language validity:** native-speaker review and dialect annotation are deferred; retain automated-candidate language in this release and revisit before making native-accuracy claims.
6. **Version and release:** the reviewed commit and matching v0.1.1 tag are created locally; decide separately whether to publish. The repository code has an MIT license; data rights remain source-specific.

## Work started in this audit

- [x] Reproduced the CC-BY-NC-SA false acceptance in the rights classifier and found its current public-package effect.
- [x] Measured composition of the all-data text-training split and traced model experiments to the unfiltered split.
- [x] Confirmed structured metadata gaps against the generated preflight and audit code.
- [x] Fix the CC license classifier and add focused regression tests.
- [x] Normalize structured source pointers, explicit review status, and rights status without fabricating licenses.
- [x] Make release audits surface structured metadata and rights gaps as failures, not silent passes.
- [x] Rebuild packages and update final audit evidence; public profile excludes the 216 rights-pending structured records, while all-data retains them.
- [x] Build and compare a strict training view while preserving the historical broad-model experiment results.
- [x] Align the text-scaling experiment defaults with the checksum-frozen 398-row benchmark.
- [x] Tie release-index readiness to final-audit status.
- [x] Resolve geography evidence labels and shared literary capture IDs to source URLs or capture fingerprints; the structured-source traceability count is zero.
- [x] Refresh local release audit artifacts and package preflights; the v0.1.1 public audit and index pass. Latest full pytest run: 584/584 passed; documented unittest run: 582/582 passed. Run pytest with `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`.
- [x] Review online reuse terms for the 186 previously unassessed structured records and retain per-record findings; all remain in all-data and the public reference index.
- [ ] Establish a compatible public-rights basis for every field before adding any of the 216 structured records to a public package.
- [ ] Re-evaluate neural text models using the recommended view and fixed strict validation/test artifacts.
- [x] Recompute exact benchmark hashes/counts/leakage and flag the XORQA source-split duplicate; the parent-document gap found afterward is fixed in a separate candidate, while the historical release remains unchanged.
- [x] Set IndicBERT head/LoRA defaults to recommended train/validation views with separate outputs.
- [x] Add package-manifest shard-hash and content-derived text-ID recomputation to the release audit and cloud preflight.
- [x] Make cloud preflight run IDs profile-specific and regenerate the public report.
- [x] Create the reviewed commit and matching v0.1.1 tag locally. Native-speaker review and dialect annotation are deferred.
- [x] Publish the complete all-data reference inventory with the public corpus package: 257,807 archive-row references, 590 sources, and 277,637 source links, with payload fields excluded.

## Limits of this pass

This code and generated-data audit was refreshed on 2026-09-28. The public and all-data package checks pass. The v0.1.1 benchmark audit verifies six inputs, reports zero exact text/audio/speaker overlap, and preserves one XORQA train/dev warning; it did not check parent-document sibling splits. A later audit found 50 parent documents / 1,523 rows crossing historical text splits; the corrected local candidate reports zero parent-document crossings and is not part of the release. The configured overlap scan reproduces 616 source-family groups, including 27 exact cross-split contexts. The nested-field review covers 10,571 fields and found 41 same-field cross-split groups (27 contexts, 6 English answer spans, 5 English oracle questions, 2 Garhwali translated-answer spans, and 1 Garhwali question), zero long exact training overlaps, and no long cross-language-label matches. A supplemental check found 50 short identical strings across English/Garhwali answer fields; 10 occur across source splits, all at 2–6 normalized characters, and remain common-answer candidates. The page-title audit found 54 exact source-page families crossing splits (134 rows), including 32 families with distinct context passages. The usage overlay now flags 138 retained rows for open diagnostics; repeated answer spans remain candidates. Semantic and cross-language independence remain unproven. See the [nested-overlap review](research/benchmark-nested-overlap-review-2026-09-27.md), [cross-language exact-overlap review](research/benchmark-cross-language-exact-overlap-2026-09-28.md), and [source-page family review](research/benchmark-source-page-families-2026-09-28.md).

The v0.2 draft validates eight views and 12,622 records with zero structural/integrity errors. Its deterministic local adapter retains all rows and verifies output hashes/counts. Versioned QA, summarization, and translation scorers verify exact IDs and retain missing-reference rows while excluding them from scores. Existing translation-memory predictions reproduce all 997 FLORES dev scores; a 2,000-resample record bootstrap reports descriptive copy-vs-memory intervals but does not account for source clusters. BM25 manifests reconcile all 500 XORQA dev query IDs; an additional 2,000-resample page-cluster bootstrap gives a paired character-minus-word Recall@10 delta of +0.2 percentage points (95% CI 0.0–0.6), conditional on the fixed all-split passage corpus. See [the retrieval uncertainty report](research/retrieval-source-page-cluster-uncertainty-2026-09-28.md). Saved ASR comparisons have a shared manifest for 269 validation rows, reproducing SraVaani at 43.3936% WER / 18.9252% CER and Whisper v0.2 at 78.0522% / 46.2980%. The three saved mT0 systems also have manifests for the same 130 validation IDs; their selected-ID digest matches the training report. Primary-reference diagnostics reproduce the saved report; current unreviewed alternate references shift chrF2 by +0.0019–0.0025, a sensitivity analysis rather than a quality gain. No inference ran and held-out rows were not scored. The mT0 adapter hashes and original sampling parameters are missing. These results do not establish native correctness or independent accuracy.

The overall metric contract remains draft; NLLB inference is blocked by absent local weights. The release index validates. Latest full pytest run: 584/584 passed; the documented unittest suite: 582/582 passed. Run pytest with `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`. The rebuilt compact bundle contains 131 files (2,585,212 bytes) with no hash or path errors. The XORQA retrieval miss analysis confirms all 500 dev gold passages are available in the fixed candidate corpus; word BM25 has 496 zero-score misses and character BM25 has 493 zero-score plus two rank-below-10 misses ([report](research/retrieval-miss-analysis-2026-09-28.md)). The mT0 generation-output audit finds substantial task-local repeated-answer concentration (up to 23/29 outputs for seed 43) but no empty/prompt-copy/control-token or selected Unicode anomalies; this is not a language-correctness finding ([report](research/generation-output-diagnostics-2026-09-28.md)). See [the Phase 2 adjudication record](research/benchmark-overlap-adjudication-2026-09-26.md), [the v0.2 schema contract](research/garhwali-bench-v0.2-schema-contract.md), and [the benchmark/model roadmap](research/benchmark-model-roadmap.md).

As of 2026-09-27, `rushilrawat/garhwali-speech` and `rushilrawat/garhwali-corpus` are public. The corpus repo is at commit [`a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2), contains all three reference tables and 11 draft shards, and exposes all 15 splits / 15 Parquet files. The Hub reports 682,718 rows across nine overlapping configs. All config previews, search, and filters pass; statistics work for seven configs, while the service returns HTTP 500 for `text` and `sravaani_drafts` because its histogram code fails on constant-valued columns. Locally, Datasets 5.0.1 loads all nine configs, and release audit/index checks pass. Full source payloads without compatible reuse terms remain unredistributed; these checks do not establish native-language correctness.
