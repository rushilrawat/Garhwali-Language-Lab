# Garhwali Language Lab — deep final audit

**Audit date:** 2026-09-25
**Scope:** current working tree, generated public/all-data Hugging Face package snapshots, model-data selection scripts, release and preflight validators, research status, and test coverage.
**Purpose:** identify defects that can make corpus claims, source reuse, evaluation, or model-quality conclusions incorrect; record verified fixes and the remaining release gates.

## Current conclusion

The project has a reproducible public-profile candidate. The license-classifier defect is fixed; structured records have normalized provenance and quality fields, and records without compatible rights evidence are excluded from the public profile while retained in all-data. Native-speaker review and dialect annotation are deferred by the project owner, so language and benchmark claims remain automated candidates. Future IndicBERT head/LoRA runs and text-scaling runs default to the strict recommended data view. Historical broad-corpus results remain tied to their original inputs.

The package inventory reports 257,807 rows across overlapping all-data views and 146,684 rows across 12 public configurations. Counts include multiple representations of the same source material and must not be described as unique examples. The corpus has 28,755 exact-unique parent texts and 114,064 prepared text segments. All-data includes every collected text value (zero catalog redactions); the public profile redacts 24,566 values and excludes all 216 structured rows without a compatible public-rights basis.

## Verified findings

### Fixed critical defect — noncommercial Creative Commons sources passed the public-rights classifier

`scripts/build_huggingface_dataset.py:is_publishable_provenance` treats the substring `cc-by-` as sufficient evidence of an open license. It does not reject the `NC` (noncommercial) or `ND` (no derivatives) variants. A provenance record for PanLex labeled `CC-BY-NC-SA-4.0` has no blocking rights marker that compensates for this, so the classifier returns publishable.

**Measured effect and correction:** the prior public-profile build exposed **13 segment rows** from `panlex_gbm` carrying a CC-BY-NC-SA license. The license classifier is fixed, regression-tested, and both packages were rebuilt; the current audit reports zero general text public-rights failures. The all-data package retains the full data locally. No remote Hugging Face publication was performed.

**Remediation complete:** restrictive CC variants are rejected before accepting an open-license marker; regression tests cover NC, ND, valid CC-BY, and the exact MIT identifier. The rebuilt public profile has zero general text-rights failures.

### High — 216 structured knowledge records still lack public-rights evidence

The public and all-data packages contain 216 records in six configurations: geography (50), historical terms (36), literary people (26), literary works (66), popular songs (30), and university research (8). Source hints previously used inconsistent field names such as `evidence`, `source_refs`, `source_ids`, `source_url`, `wikipedia_url`, `lyrics_sources`, and `translation_sources`. The builder now maps source pointers into standardized `provenance`, adds explicit quality/review status, and records rights without inventing a license. A web review has now examined the 186 previously unassessed geography, history, people, works, and university records. Some component sources carry reuse terms, but no whole-record public-rights basis was established for those mixed-source records. Current audit counts are **0 missing provenance**, **0 missing quality metadata**, **0 unreviewed rights statuses**, and **216 rows without compatible public rights**.

The release audit and cloud preflight enforce these fields. The all-data/private preflight passes. The public builder omits all six structured configurations until compatible rights are established; therefore the public audit and preflight now pass without treating any of the 216 records as cleared. The complete records remain in all-data.

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

The final audit now checks all six benchmark inputs and recomputes artifact hashes, counts, and leakage instead of trusting stored claims. It reports zero internal text, audio-hash, and identified-speaker overlap, plus one preserved XORQA train/dev warning. It also recomputes every `recommended_for_training` value from language, quality, flags, and public-rights evidence.

Package manifests carry per-shard SHA-256 values; both the final audit and cloud preflight recalculate them. The audit recalculates exported text IDs from content and catalog IDs from text hashes. Current audit counts are zero shard-hash failures and zero text-ID failures.

**Remaining:** use an independently signed or separately published manifest if tamper evidence across release artifacts is required. Current hashes detect shard drift relative to the package manifest; this same-manifest check does not protect against an actor replacing both the shard and its manifest entry.

### Resolved — release identity matches the reviewed repository state

The package and release index identify themselves as `garhwali-language-lab-v0.1.1`; annotated tag `v0.1.1` resolves to the reviewed release commit. The historical `v0.1.0` tag is unchanged. The exact reviewed commit passed the recorded release checks.

### Medium — “all-data” and “public-profile” are different products

The all-data package preserves all 28,755 catalog text values, including restricted/right-pending material, for local or access-controlled research. The public profile redacts 24,566 catalog values and omits 216 structured records with unresolved rights. The previous PanLex license leak has been fixed. Keep the distinction visible in cards, package manifests, and release reports.

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
- [x] Refresh local release audit artifacts and package preflights; the v0.1.1 public audit and index pass. The current full suite passes 466 tests.
- [x] Review online reuse terms for the 186 previously unassessed structured records and retain per-record findings; all remain present in all-data.
- [ ] Establish a compatible public-rights basis for every field before adding any of the 216 structured records to a public package.
- [ ] Re-evaluate neural text models using the recommended view and fixed strict validation/test artifacts.
- [x] Recompute benchmark hashes/counts/leakage independently; internal overlap is zero and the XORQA source-split duplicate is explicitly flagged.
- [x] Set IndicBERT head/LoRA defaults to recommended train/validation views with separate outputs.
- [x] Add package-manifest shard-hash and content-derived text-ID recomputation to the release audit and cloud preflight.
- [x] Make cloud preflight run IDs profile-specific and regenerate the public report.
- [x] Create the reviewed commit and matching v0.1.1 tag locally. Native-speaker review and dialect annotation are deferred.

## Limits of this pass

This code and generated-data audit was refreshed on 2026-09-25. The public and all-data package checks pass. The benchmark audit verifies six inputs, reports zero internal text/audio/speaker overlap, and preserves one XORQA train/dev warning. The release index validates, all 466 tests pass, and the rebuilt compact bundle contains 131 files (2,585,212 bytes) with no hash or path errors.

Hugging Face visibility and Viewer status were last independently verified on 2026-09-24: `rushilrawat/garhwali-speech` was public with 110,436 VAANI and 2,927 Meta Omnilingual rows, and `rushilrawat/garhwali-corpus` was private. The speech Viewer checks passed and exact audio/transcript overlap counts matched the local audit. These checks do not establish source ownership or native-language correctness. The corpus remains private because 24,566 catalog values are redacted and 216 structured records lack compatible public-rights evidence; all remain present in the local all-data package.
