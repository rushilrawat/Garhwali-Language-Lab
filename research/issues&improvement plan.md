# Benchmark and model roadmap issues & improvement plan

**Updated:** 2026-10-07 (current platform status; detailed benchmark evidence below remains dated snapshots)

**Scope:** issues found while executing the benchmark/model roadmap and its
immediately preceding retrieval, generation, and ASR work. This is a living
issue log, not a claim that every project file or dataset has been re-audited.

Every item records evidence, impact, action, and remaining status. Data and
model outputs stay local and Git-ignored. Living status documents are refreshed
after each material benchmark/research milestone; dated experiment and release
snapshots remain historical. The 2026-09-29 refresh rebuilt local benchmark
artifacts, repaired aggregate score-lineage reporting, added six local draft
cards, integrated corpus/per-record ASR scoring, and inventoried benchmark
rights. On 2026-09-30 the owner approved active work toward independent
final-accuracy evidence across all five task areas. Generation scoring was
added to the shared runner and saved outputs were reconciled to current
validation rows. The v0.2.1 corpus package was published additively to the
existing public Hugging Face dataset at payload commit `5db2673`; the root and
versioned cards were corrected at `53a0aff`. No paid job or visibility change
occurred. The pipeline now has a tested one-command resumable ingest-and-refresh
mode. Use this current summary for present benchmark counts; dated entries
below preserve earlier evidence.

## Current closeout status — 2026-10-07

The public corpus is v0.2.8; its current Hugging Face Viewer reports 20 named
configs, 31 config/split views, 963,484 displayed rows, and 7.57 GB. The speech
page reports 118,375 rows / 36.5 GB, including 113,363 audio/source rows and
text-only indexes of 2,718 VAANI references and 2,294 optional Meta train
references. These platform totals overlap and are not unique examples. The
current ASR reference and Kaggle status is in the [7 October cross-platform
audit](current-platform-metrics-2026-10-07.md). The public Kaggle text view is
version 1; the private ASR package is version 2. Its baseline notebook is
saved at version 3 and has not been run.

The most recent recorded full project suite run was 827 passing tests on
6 October; this documentation refresh did not rerun it. The catalog visibility
audit separates 15,004 text values already found elsewhere in the public
package from 8,444 distinct full texts still local with rights pending. Each
has a source locator: 7,675 inline URLs and 769 URLs via `source_catalog`; some
point only to a source container, not an exact work or page. The
[closeout audit](huggingface-corpus-gap-resolution-2026-10-06.md) defines the
source-by-source path to resolve that gap. The benchmark remains local-only
and draft, independent-final eligibility is still 0/5, and native-language
review and dialect annotation remain deferred. Detailed benchmark evidence
and issue entries below are dated historical snapshots.

**Historical status — 4 October:** the public corpus was v0.2.3; speech remained v0.2.1.
The Archive intake quality and overlap audit produced no benchmark or model
results. The full working-tree unittest suite passes **707/707**; those tests
check code and data contracts, not linguistic correctness.

## Historical roadmap position — benchmark snapshot 2026-09-30

The public corpus is at v0.2.3 and speech is at v0.2.1. GarhwaliBench remains
a local draft; the benchmark counts below are the preserved 30 September
snapshot and were not changed by the later corpus access view or Archive
intake:
five candidate task artifacts exist, three external schemas pass across 3,847
records, and the current v0.2 adapter validates eight views / 14,703 rows
(manifest SHA-256 `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`).
The 9,486/454/402 recommended text split retains all rows from the prior
8,265-row candidate and adds 2,077 without moving prior rows between splits.
The adapter and metric contract are not fully release-frozen; ASR corpus and
per-record aggregation plus retrieval rank/tie policies are now explicit and
tested. The 138-row
XORQA usage overlay remains intact. Exact/family scans are updated, but semantic/paraphrase and
checkpoint exposure remain open. The 2026-09-30 row-level audit also finds 15
exact-text overlaps from recommended training in instruction test and 29 in
instruction validation; the Meta Omnilingual family has four train/test audio
and four train/test text groups, plus 27 train/validation text groups. Keep all
rows and flag the affected eval records. The current internal text test's 402 rows
were aggregate-scored (character-bigram PPL 14.397995), so evidence eligibility
remains 0/5 for independent final-accuracy claims despite the owner's approval
to work toward all five areas.

The [rights inventory](garhwali-bench-v0.2-rights-inventory-2026-09-29.md)
found all 14,703 draft view rows still marked `public_upload_allowed=false`;
2,077 recommended-text rows have source components assessed compatible, 8,265
have item-level rights status not recorded, and external/audio components need
separate review. The component candidate counts are not publication clearance.
The [ASR scorer integration check](asr-corpus-metric-integration-2026-09-29.md)
reproduces the saved 269-row validation aggregate with the new corpus and
per-record metrics. The current row-level lineage output is kept under ignored
`data/processed/evaluation/garhwali_bench/model_accuracy_lineage_2026-09-30`
because its JSON includes speaker IDs. The [generation scorer follow-up](generation-scoring-integration-2026-09-30.md)
records the shared scorer and 130/320 matched-validation reconciliation; the
other 190 rows have no saved predictions.

**Open work, in order:**

1. Finish semantic/paraphrase, cross-language, and source-family checks. Keep
   the newly detected 15/29 recommended-train-to-instruction text overlaps and
   Meta audio/transcript cross-split groups flagged; do not delete their source
   rows. Update task eligibility overlays and document which examples remain
   open-diagnostic, development-only, historical, or unresolved.
2. Freeze the v0.2 schema, normalization/metric contracts, split manifests,
   public/local field cards, and missing-reference denominator rules.
3. Complete standardized manifests and baseline consolidation for remaining
   tasks without rescoring historical test rows.
4. Add source-cluster uncertainty and failure analysis where usable source
   lineage exists; keep XORQA dev retrieval intervals conditional on its fixed
   all-split candidate corpus.
5. Publish benchmark cards/artifacts only after rights, integrity, and
   reproducibility gates pass.

The frozen v0.2.0 release verification's 607/607 pytest and 605/605 unittest
counts are historical; the 682/682 run was the recorded v0.2.1 working-tree
check, not the current project test count.
Fresh NLLB, dense IndicBERT retrieval, and SraVaani inference remain blocked:
the project `.venv` has no PyTorch/Transformers/NeMo/PEFT/PyArrow, while the
optional cached runtime lacks NeMo/PEFT/audio readers and the necessary NLLB/
IndicBERT base weights are not present in the project-local model cache. A
legacy 269-row SraVaani comparator still
differs from the later greedy-sweep aggregate by 3 word and 4 character errors;
the original row-level greedy output is missing. Native review and dialect
annotation remain deferred at the owner's direction; a blind-first-pass
transcript packet is prepared, but zero native decisions exist. Automated
diagnostics cannot be called native-validated.

## Issues

### BMR-001 — Translation runners defaulted to an already-scored test split

- **Severity/status:** High; fixed.
- **Evidence:** Before this change, `run_translation_baseline.py` evaluated
  `test` by default and wrote to the legacy translation output directory.
  `run_nllb_translation_baseline.py` selected test rows by default as well.
  The FLORES test already has saved predictions, so an ordinary reproduction
  command could rescore the historical test and overwrite its result files.
- **Impact:** Unsafe model-selection boundary and risk of destroying the
  historical record.
- **Fix:** Both runners now default to `dev`, take an explicit `--split`, sort
  by record ID, record selected IDs and SHA-256 digests, and place default
  outputs under `accuracy_dev/` or `accuracy_test/`. Reports mark test output
  as `historical_already_scored`.
- **Verification:** Default-path tests use a malformed test fixture with no
  translation payload; the dev run succeeds and emits only the dev record.
  Legacy prediction/report hashes remain
  `759c28e6ec78f8ad5c70a6f500c9c773dcc2ab2e16860f5c940b62532c1bc73f` and
  `cb70be03e95e90db828a5fd7820801d72a991eaad0b10338dc8b9767f49c9312`.
- **Residual:** The explicit `--split test` option remains for controlled
  historical reproduction. It must not be used for model selection or a blind
  accuracy claim.

### BMR-002 — Development translation memory could retrieve the query itself

- **Severity/status:** High; fixed for exact normalized-source matches.
- **Evidence:** Using `dev` both as searchable translation memory and the
  evaluation set would let each example retrieve its own target. The earlier
  test-only setup did not expose this when the memory was `dev` and evaluation
  was `test`.
- **Impact:** Inflated development-memory results and misleading comparisons.
- **Fix:** Dev evaluation now excludes all memory entries whose normalized
  source is identical to the query. The protocol is recorded as
  `dev_leave_exact_normalized_source_out`; predictions include the selected
  memory record ID.
- **Verification:** Unit tests cover self/duplicate exclusion. The 997-row
  dev set has zero exact normalized-source duplicate groups, so no exact
  duplicate query weight is concealed.
- **Residual:** Near-duplicate and semantically related source pairs have not
  been clustered; the memory score remains a diagnostic, not a generalization
  estimate.

### BMR-003 — Empty translation inputs could produce misleading metric values

- **Severity/status:** Medium; fixed.
- **Evidence:** The custom smoothed BLEU implementation returned `2.71828183`
  for a one-record empty-reference/empty-hypothesis corpus because its brevity
  penalty divided by a fallback length of one. Empty corpora and mismatched
  reference/hypothesis counts were also accepted silently.
- **Impact:** Invalid denominators could look like a perfect or greater-than-one
  translation score.
- **Fix:** BLEU and chrF reject empty or unpaired corpora; BLEU returns zero
  when either whole-corpus token length is zero; summaries record total,
  empty-reference, and empty-hypothesis counts.
- **Verification:** Tests cover empty corpora, unpaired inputs, empty-string
  records, identical text, and Devanagari text.

### BMR-004 — NLLB comparison cannot be reproduced in the active local runtime

- **Severity/status:** Medium; blocked pending local prerequisites.
- **Evidence:** The project's `.venv` has no `torch`, `transformers`, or
  `peft`; the optional `.cache/asr-runtime` exposes `torch` and `transformers`
  only when added to `PYTHONPATH`, but has no `peft`. The pinned
  `facebook/nllb-200-distilled-600M` snapshot is absent. `sacrebleu` is also
  absent, though the local baseline uses its documented custom metric.
- **Impact:** No fresh NLLB development result or cross-model translation
  comparison can be produced safely in this environment.
- **Action:** Leave NLLB as a documented preflight blocker. No dependency or
  model download was initiated. A future run must use already-local pinned
  dependencies and weights; no paid/cloud path is authorized in this roadmap.
- **Related evidence:** [translation quality refresh](translation-quality-2026-09-26.md).

### BMR-005 — Translation evaluation is not an independent accuracy benchmark

- **Severity/status:** Open; data/lineage limitation.
- **Evidence:** FLORES `test` has prior saved predictions; the 32-row NLLB
  Hindi-token proxy is also historical. Translation references are not
  native-adjudicated, and the external models' training exposure is unknown.
- **Impact:** Existing scores cannot support a blind Garhwali translation
  accuracy claim or model promotion.
- **Action:** Keep all current results exploratory/historical. A future
  independent benchmark requires eligible, source-traceable Garhwali pairs,
  fixed split hashes, and a held-out split not used in model development.

### BMR-006 — Current translation metrics are custom, not SacreBLEU

- **Severity/status:** Open; interpretation constraint.
- **Evidence:** Current scripts use add-one-smoothed corpus BLEU and custom
  character n-gram F-score. `sacrebleu` is not installed in the active
  environment.
- **Impact:** Values are not directly comparable to SacreBLEU publications or
  leaderboards, and relabeling them would be incorrect.
- **Action:** Keep the metric implementation and normalizer explicit in each
  report. If a standard-metric comparison becomes necessary, install only in a
  separately approved local environment and record the exact metric signature.

### BMR-007 — Garhwali-to-English lexical retrieval remains weak

- **Severity/status:** Open; quality limitation carried forward from the
  retrieval workstream.
- **Evidence:** The 2026-09-25 dev-only BM25 run reported word/character
  Recall@10 of 0.8%/1.0%, while English-oracle queries reached 85.2%. See the
  [retrieval quality report](retrieval-quality-2026-09-25.md).
- **Impact:** Cross-script lexical overlap is a major limitation for
  Garhwali-query retrieval over English passages.
- **Action:** Keep this as a separate retrieval issue; do not claim a successful
  RAG system. Dense IndicBERT comparison remains blocked until exact local
  weights/runtime are available.

### BMR-008 — mT0 test lineage does not reconcile with current manifests

- **Severity/status:** Open; historical-result limitation carried forward from
  the generation workstream.
- **Evidence:** The earlier report records a selected mT0 result on 86 test
  rows, but its manifest digest does not match current local test manifests;
  172 saved test prediction rows remain unmatched. See the
  [generation quality report](generation-quality-2026-09-25.md).
- **Impact:** Those test metrics cannot be reproduced or treated as a current
  independent held-out result.
- **Action:** Preserve the outputs as historical, use validation diagnostics
  only for model decisions, and require a reconciled manifest before any new
  eligible test evaluation.

### BMR-009 — Legacy SraVaani validation comparator does not reconcile with the decoder sweep

- **Severity/status:** Medium; open, provenance mismatch.
- **Evidence:** `research/asr-validation-error-analysis-2026-09-24.json` and
  `confidence_calibration/sravaani/predictions.jsonl` resolve the legacy
  comparator's exact saved input (SHA-256
  `78b9509b5682474f391fb388a1a5ed1d25b5c48f527824eb9cf4cb879219f73a`). Its
  selected 269-row validation summary exactly matches the later manifested
  comparison row-for-row and reproduces 2,161 word errors / 3,282 character
  errors. The decoder-sweep greedy aggregate is 2,164 / 3,286 on the same
  denominators, but its per-row greedy predictions were not saved.
- **Impact:** The source of the legacy number is now known and reproducible;
  the small 3-word / 4-character discrepancy against the sweep remains
  unexplained because only the latter run's aggregate is available. The legacy
  score must not silently be substituted for the sweep baseline.
- **Action:** Keep both as separately named historical validation runs in the
  [ASR consolidation report](asr-baseline-consolidation-2026-09-26.md). Close
  this issue only if the original sweep's per-row greedy predictions/config
  become available or a rerun is justified on validation with pinned settings.
  Do not tune or select from the already-used test set.

### BMR-010 — New local ASR inference lacks a complete runtime path

- **Severity/status:** Medium; blocked pending local prerequisites.
- **Evidence:** `.cache/asr-runtime` provides PyTorch and Transformers only
  through an explicit `PYTHONPATH`; it lacks NeMo, PyArrow, SoundFile, librosa,
  and torchaudio. The SraVaani model cache contains metadata but no base
  weights. The fine-tuned `.nemo` files and a local Whisper-tiny checkpoint
  exist, and `ffmpeg` is installed.
- **Impact:** The existing ASR outputs can be audited, but another SraVaani
  run or Meta-Parquet audio experiment cannot be reproduced from the current
  runtime as-is. A direct end-to-end Whisper/audio path has not been verified.
- **Action:** Keep the work local-only. First assess whether the already-cached
  runtime and available audio files can support an end-to-end Whisper run; if
  SraVaani is required, document and resolve the local NeMo/base-weight
  prerequisite before running it. Do not launch paid jobs or download data as
  part of this issue.

### BMR-011 — No independent final ASR set is approved

- **Severity/status:** High; open, evaluation limitation.
- **Evidence:** The fixed 112-row VAANI test has prior saved results. SraVaani
  identifies VAANI as an upstream training source but does not expose
  example-level overlap. Transcript references have not had native-speaker
  adjudication.
- **Impact:** Historical WER/CER are useful experiment records, not a blind
  estimate of generalization or proof of Garhwali correctness.
- **Action:** Mark the test historical-only and do not select models from it.
  For future independent claims, define a new source/speaker-held-out set with
  traceable references and documented model exposure. Native review remains
  deferred as requested, so automated scores must keep that limitation visible.

### BMR-012 — ASR test reports do not fingerprint every evaluated row set

- **Severity/status:** High; exact row-set uncertainty resolved post hoc on
  2026-09-28; model-independence and native-reference limitations remain open.
- **Evidence:** The base model report records test manifest SHA-256
  `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`. The
  original 102-step adaptation report records a different SHA-256,
  `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`. The
  decoder-sweep report's `selected_test` aggregate and the six-config,
  61-trial, and expanded-human `held_out_test` aggregates omit a manifest hash.
  The post-hoc audit matched all 112 audio hashes and cleaned references from
  each saved prediction file to the fixed manifest. Per-row counters reproduce
  each report's aggregate WER/CER. The original 102-step report has a different
  input-manifest byte hash, but its saved rows also reconcile exactly by audio
  and reference identity.
- **Impact:** Exact row identity and paired comparisons are now verified.
  Speaker-clustered intervals across 19 speakers include zero or touch zero for
  every WER/CER difference. These are historical, post-hoc diagnostics, not
  independent accuracy evidence or a reason to promote a checkpoint.
- **Remaining:** The original 102-step input serialization difference is
  unexplained; example-level SraVaani upstream exposure is unknown; references
  have not been native-adjudicated. Keep results historical-only and require
  future run reports to write manifest hashes at run time.
- **Verification:** Five saved prediction sets reconcile 112/112 audio IDs
  and cleaned references; output counters match their reports. See the
  [reproducible audit](asr-heldout-lineage-audit-2026-09-28.md).

### BMR-013 — Near-duplicate and source-family contamination checks are incomplete

- **Severity/status:** High; open, Phase 2 blocker.
- **Evidence:** The 2026-09-26 exact-hash lineage audit flags the XORQA train/dev
  primary-text repeat, cross-split ASR target repeats in experimental views,
  and Meta Omnilingual audio/text duplicate groups. The new local-only
  candidate output is summarized in the [measured status report](benchmark-research-status-2026-09-25.md#phase-2-candidate-scan-2026-09-26); its generated artifact is
  `data/processed/evaluation/garhwali_bench/overlap_candidates.md`. It scans
  12,510 text rows and records 407 normalized exact-text groups. Only one
  spans source splits (the known XORQA train/dev repeat); 398 cross-view groups
  are expected same-split mirrors between `internal_text` and the recommended
  test view. Four char 5-gram candidates are within one split. The report also
  records 27 exact XORQA source-context groups across source splits: 11 include
  training plus dev/test and four include both training and test. Direct
  verification confirmed all groups by exact normalized `source_example.context`
  hash, and a deterministic overlay labels 62 affected records as open-diagnostic-
  only for independent source-generalization claims. The one exact train/dev
  question repeat is included among those records. All four near pairs were
  inspected: three match existing same-split duplicate components in recommended
  train; the XORQA pair shares the same dev context and answer. Rows remain
  present, and the dev pair should be grouped by source context in diagnostics.
  The raw detector report retains `unreviewed_candidate` states; reviewed
  interpretations are in the [adjudication report](benchmark-overlap-adjudication-2026-09-26.md).
  The report hashes are JSON
  `abbf44d81c4afd092afce845043dddc16230780f5157eabe5f4f26ccbf3b1d1b` and
  Markdown `5c4426a5c184a154c9add59f897001e2dab6c43afe5144dac7ad9713c18f62a1`.
  Dataset-level Hugging Face repository URLs and collection IDs are excluded
  from source-family evidence. No semantic or cross-language matching is run.
- **Nested-field refresh (2026-09-27):** `audit_benchmark_nested_overlap.py`
  scanned 10,571 fields across FLORES, CrossSum, and XORQA against 7,490
  recommended-train records. It found 41 exact same-field cross-split groups:
  27 contexts, 6 English answer spans, 5 English oracle questions, 2 Garhwali
  translated-answer spans, and 1 Garhwali question. There were zero cross-field
  groups and zero long exact training matches; 15 short Garhwali answer matches
  are separately documented. The current overlay flags 67 unique records.
  Answer-span repeats are not automatically classified as leakage. The method,
  input hashes, and limits are in
  [the nested-overlap review](benchmark-nested-overlap-review-2026-09-27.md).
  A 2026-09-28 supplemental scan compared exact normalized hashes across field
  language labels and found 50 English/Garhwali XORQA answer-string groups;
  10 cross source splits, all 2–6 normalized characters. These are short-answer
  candidates, not confirmed translation errors or leakage, and were not added
  to the overlay. See
  [the cross-language exact-overlap report](benchmark-cross-language-exact-overlap-2026-09-28.md).
- **Source-page-family refresh (2026-09-28):** all 1,139 XORQA title locators
  parsed into 993 exact page families. Fifty-four families (134 records) cross
  source splits, including 32 groups with distinct context passages. The local
  overlay now labels 138 unique rows; all retain their original data and splits
  and remain open for diagnostic use. The v0.2 adapter carries page-family
  hashes. See
  [the source-page review](benchmark-source-page-families-2026-09-28.md).
- **Full input refresh (2026-09-29):** the detector scanned 14,591
  text-relevant rows across the current benchmark views. It found 411 exact-text
  groups, one exact group across source splits (the known XORQA train/dev
  repeat), 402 expected exact cross-view mirrors for the same internal text
  test records, and four near-text candidates; each near pair is in one split
  and matches previously reviewed pair IDs. Source-family grouping found 1,995
  groups and 29 cross-split families: 27 content/source-linked XORQA families
  plus two broad URL families (a TLF collection URL and a book URL). Those two
  are grouping candidates, not evidence that all records in either collection
  are duplicates. The 138-row overlay is unchanged. Detector JSON SHA-256:
  `23e454a2ced303457866e26fa55b9ca5386f30fb26f38cfda6b3fe199266294a`;
  generated local report: `data/processed/evaluation/garhwali_bench/overlap_candidates.md`.
- **Impact:** Exact-match clearance cannot establish source-family or
  cross-language independence. Candidate benchmark rows must remain
  historical/open/development-only according to their existing use decisions;
  no negative exact-match result supports a blind-test claim.
- **Progress:** The deterministic detector is implemented at
  `scripts/audit_benchmark_overlap_candidates.py`; it records stable row IDs,
  match types, input hashes, similarity settings/scores, exact family-key
  hashes, and an unresolved state. It does not copy raw source text/URLs or
  change data. The follow-up verifier/labeler is `scripts/build_benchmark_usage_labels.py`;
  it validates source contexts and exact questions against the source manifest,
  records 138 current row-level labels, and never removes source rows. Seven detector
  tests and seven usage-label tests cover Unicode normalization, same-language
  near-match guards, source-link grouping, stable ordering, collection-URL
  exclusion, exact-hash verification, retained-row behavior, split consistency,
  and CLI output.
- **Remaining action:** CrossSum exact source/target URL grouping is complete
  and found no cross-split repeats; FLORES exposes no row-level source URLs, so
  source-family provenance there needs better upstream metadata. Continue
  semantic/cross-language review only where reliable alignments exist and decide
  a group-aware diagnostic aggregation/split policy. Exact XORQA page and
  context groups are carried into the v0.2 draft. Do not infer translation
  leakage from script-different character similarity.
- **Verification target:** tests prove repeated rows are reported without
  deletion, stable hashes/order are reproducible, and a negative scan is
  labeled “no candidates found by this method,” not “no leakage.”

### BMR-014 — v0.2 schema and metric contract is not frozen

- **Severity/status:** High; open, Phase 3 blocker.
- **Evidence:** The draft contract is in
  [garhwali-bench-v0.2-schema-contract.md](garhwali-bench-v0.2-schema-contract.md).
  The dependency-free validator `scripts/validate_benchmark_v02.py` passes
  eight views / 14,703 rows with zero structural or integrity errors, including
  112/112 local ASR audio hashes. The 2026-09-29 validation JSON SHA-256 is
  `170476050d38da75b4a21f55d50bd3fdfc76f0fd4f4d954be1dd0cef26a02583`.
  The deterministic adapter `scripts/build_benchmark_v02.py` writes all eight
  views / 14,703 rows to an ignored local-only package; its current manifest
  SHA-256 is `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`. It
  links the 62-row overlay from that historical export snapshot, preserves each legacy source row, records available
  raw/scoring text separately, and self-validates output hashes/counts.
  The shared scorer now covers FLORES translation, CrossSum, XORQA, and ASR,
  including prediction-ID reconciliation, split gates, and missing-reference
  reporting. ASR run manifests fingerprint their metric implementation; its
  real-data validation check reproduced saved aggregate counts exactly. The
  current export links the 138-record overlay, including
  source-page family hashes; all eight assets validate with zero errors. At
  the 2026-09-28 source-page-cluster checkpoint,
  pytest passed 569/569 and the documented unittest runner passed 567/567;
  current test totals are listed at the top of this plan.
- **Known migration gaps:** verified original raw text is absent from some
  internal/recommended v0.1 rows; the adapter explicitly leaves those raw
  values unavailable. QA, summary, translation, and ASR metric paths are
  integrated, but source-page uncertainty is now measured for XORQA BM25 dev;
  translation and other source-group uncertainty, LM/generation scoring contracts, and
  explicit no-answer support remain open. The overlap audit
  still cannot establish semantic or cross-language independence. Rights remain
  a separate release gate; schema validation is not rights clearance.
- **Action:** recover raw values only where provenance supports an exact link;
  extend run manifests to remaining tasks, define exclusions/uncertainty/source
  strata, and continue
  Phase 2's aligned-field review. Keep this draft local until the remaining
  gates are complete.
- **Exit condition:** rebuilding the v0.2 package is deterministic, all task
  validators/tests pass, and cards distinguish local-only from public fields
  without describing any current split as blind or native-reviewed.

### BMR-015 — Evaluation runners did not share a complete run record

- **Severity/status:** High; partially addressed, Phase 4 remains open.
- **Evidence:** Translation and NLLB runners previously wrote a prediction file
  and aggregate report but had no common artifact manifest for output hashes,
  config hash, timestamps, runtime/device, Git state, or exact row reconciliation.
  NLLB imported Torch/Transformers before checking its inputs and local model
  snapshot. Neither runner previously had a separate historical-test opt-in.
- **Fix in this pass:** `scripts/evaluation_run_manifest.py` now writes
  `run_manifest.json` alongside prediction JSONL and aggregate JSON. Translation
  and NLLB use it; it checks selected record IDs and prediction count against the
  report, then records input/selected-row hashes, config and source-code hashes,
  model revision/config hashes where available, Git commit/dirty state,
  runtime/device, timestamps, seed, completion status, and output hashes. NLLB
  performs preflight before model imports. Both translation runners require
  `--split test` plus the additional `--allow-historical-test` opt-in.
  The post-hoc scorer applies the same contract to translation, CrossSum, and
  XORQA; the BM25 retrieval baseline also emits a run manifest. A paired
  translation analysis records its bootstrap protocol and per-row outcomes in
  the same artifact format. The XORQA source-page-cluster analysis verifies
  exact dev IDs, the parent report's benchmark hash, and all saved BM25 point
  metrics before writing 2,000 family-cluster replicates; it reads no test
  predictions. The saved-prediction ASR validation comparison now
  emits a shared manifest for 269 validation audio hashes and reproduces the
  previous SraVaani/Whisper metrics exactly without inference or held-out
  scoring. Three saved mT0 generation systems now have per-seed manifests;
  each reconciles 130 instruction hashes, task labels, and references to the
  validation source, and the selected-ID digest matches the seed-43 training
  report. No new inference or test scoring was run.
- **Verification:** Four manifest unit tests, ten translation tests, and ten
  NLLB tests pass. The NLLB mock-runtime integration test verifies manifest
  output without real weights; missing input/checkpoint/config paths fail before
  the model runtime import. The unavailable-MPS check also proves preflight
  stops before tokenizer/model loading. The project suite passes 519 tests,
  Python compilation passes, and the changed-file diff check passes.
- **Real-run check:** The 997-row FLORES dev run completed into the ignored
  `data/processed/evaluation/translation/phase4_manifest_dev_gated/` directory.
  Manifest, report, and all prediction IDs reconcile; its input hash is
  `7c96d63be5f43e6a65fc229238c6d295d983fe46be032e9f8418d32150225097`, and the
  selected-row hash is
  `d3bf6084025d78bd2eede315965ee2cb981be2d3a1b59d7952e7c1deb7b5e0d5`. The
  prediction and report hashes were independently recomputed and match the
  manifest.
- **Remaining:** Add task-specific shared manifests and preflight for fresh
  ASR, IndicBERT retrieval, masked-LM, and future generation inference; the
  current mT0 manifests are post-hoc only. Recover the original mT0 sampling
  parameters and adapter hashes if the source run artifacts are available.
  Real NLLB inference remains unverified because its pinned model snapshot is
  not cached. Do not describe Phase 4 as complete yet.
- **Exit condition:** every in-scope scoring runner can reproduce the requested
  split from recorded code/config/input/model/runtime hashes, and every output
  row reconciles exactly to the selected split.

### BMR-016 — Saved mT0 validation outputs lacked shared run manifests

- **Severity/status:** Medium; post-hoc provenance added, source-run metadata
  still incomplete.
- **Evidence:** The synced generation analysis contains 390 prediction rows
  across three mT0 seeds, with 130 rows per seed. It omitted the per-seed
  checkpoint hashes and original sample-selection parameters.
- **Impact:** Metrics were saved, but their exact model bytes and sampling
  procedure were not fully recoverable from the cloud output alone.
- **Fix in this pass:** `scripts/manifest_saved_generation_validation.py`
  joins every saved prediction to the frozen validation file by
  `instruction_sha256`, verifies task and reference strings, checks all seeds
  have the same 130 IDs, and writes a hash-linked manifest per seed. The shared
  selected-ID digest matches the validation digest recorded in the seed-43
  report. It ran no inference and did not inspect test predictions. A second
  metric check recomputes primary-reference aggregate/task diagnostics and
  row flags exactly; current alternate references shift chrF2 by +0.00193303,
  +0.00238312, and +0.00248931 for seeds 17, 29, and 43. These unreviewed
  alternatives provide a sensitivity result, not an accuracy improvement. See
  the [mT0 manifest report](mt0-validation-run-manifest-2026-09-27.md).
- **Remaining:** Recover the original selection parameters and exact adapter
  hashes if the source job artifacts are still available. Treat the metrics as
  development diagnostics only; references have not been native-adjudicated.
- **Verification:** Four focused tests pass; all three output manifests
  reconcile 130 records and their output hashes.

### BMR-017 — Retrieval misses were not separated by gold-passage availability

- **Severity/status:** Analysis gap resolved for the saved XORQA BM25 dev run;
  weak Garhwali-query retrieval remains an open quality limitation.
- **Evidence:** `scripts/analyze_retrieval_misses.py` reconciles all 500 saved
  dev predictions and the fixed 1,059-passage corpus. All 500 gold passages
  and rank/score positions in each saved top-10 list are verified; the
  aggregate Recall@1/5/10 and MRR@10 reproduce the parent report.
  Word BM25 has 496 zero-score misses; character BM25 has 493
  zero-score misses and two passages ranked below 10; English-oracle BM25 has
  74 misses at 10. The candidate corpus is built from all source splits, so
  this does not measure unseen-page performance.
- **Impact:** Aggregate Recall@10 alone did not distinguish missing evidence
  from lexical mismatch or low rank. The diagnostic shows missing gold
  passages are not the cause in this fixed-corpus run; semantic support is
  still unassessed.
- **Action:** Keep the error breakdown and input hashes in the
  [dated miss report](retrieval-miss-analysis-2026-09-28.md). Use the result to
  scope a future dev-only dense retrieval experiment after local model/runtime
  preflight; do not promote a model from this analysis.
- **Verification:** Three focused regression tests pass, including exact
  duplicate-context-group counting and rejection of corpus drift/test rows.
  No new inference, test scoring, or source-data change occurred.

### BMR-018 — Saved mT0 generation output concentration was not quantified

- **Severity/status:** Medium; structural diagnostic complete, output quality
  and target correctness remain unresolved.
- **Evidence:** Existing generation reports covered empty outputs, full prompt
  copies, control tokens, and mean adjacent repetition, but did not summarize
  task-local repeated-answer modes, output lengths, or selected Unicode/script
  characteristics.
- **Fix in this pass:**
  `scripts/analyze_generation_output_diagnostics.py` checks all three saved
  validation runs against the full validation hash, source prediction/report
  hashes, per-seed manifests, and packaged prediction/report hashes. It adds
  task-local normalized-output mode counts, length quantiles, character/token
  runs, structural Unicode flags, and descriptive script profiles. The report
  contains aggregate counts only; no row is removed or rewritten.
- **Finding:** In the 29-row Garhwali-to-English lexicon slice, the largest
  answer mode is 9/29, 13/29, and 23/29 (31.0%, 44.8%, and 79.3%) for seeds
  17, 29, and 43. This is a mode-collapse candidate, not proof of incorrect
  answers; repeated valid translations and duplicate inputs remain possible.
  There were no empty outputs, instruction copies, control tokens, replacement
  characters, surrogates, unexpected controls, or selected invisible controls.
- **Remaining:** Compare repeated answers with the task inputs and accepted
  references using explicit task-specific rules; do not automatically label
  repeated outputs as wrong. Native-language correctness remains unassessed.
- **Verification:** Two focused regression tests, full pytest 574/574, and
  unittest 572/572 pass; compilation passes. No inference or test scoring ran.
  Details are in the
  [generation-output diagnostic report](generation-output-diagnostics-2026-09-28.md).

### BMR-019 — Evaluation status labels did not reflect recorded prior use

- **Severity/status:** High; fixed 2026-09-28.
- **Evidence:** The original lineage audit hardcoded several test splits with
  saved predictions as `development_only`. At the time, the 398-row internal
  text candidate had also been scored by an aggregate character-bigram
  baseline, but the audit marked it unresolved because no row-level prediction
  file existed.
- **Fix:** Test decisions become `historical_only` when saved predictions match
  any row in the fixed test split. Aggregate-only scoring is independently
  matched by the 2026-09-29 follow-up under BMR-021. The current text set has
  402 rows, all exactly matched to the aggregate baseline input. A split stays
  unresolved when no local prior-use match exists and model exposure is unknown.
- **Reports:** [Task-result eligibility](task-result-eligibility-2026-09-28.md)
  and the [fresh lineage audit](model-accuracy-lineage-2026-09-28.md) record
  the corrected assignments and counts. No data rows changed.
- **Verification:** The lineage suite passes 20/20; full pytest passes 577/577,
  the documented unittest suite passes 575/575, compilation succeeds, and
  `git diff --check` is recorded for the completed change.

### BMR-020 — Duplicate reassignment split siblings from the same source document

- **Severity/status:** High; builder defect fixed in a local candidate on
  2026-09-28. Historical manifests remain unchanged.
- **Evidence:** Rechecking all 114,064 historical text segments by parent
  `text_sha256` found 50 parent documents / 1,523 segment rows crossing
  train/test (33 documents) or train/validation (17 documents). Exact segment
  hashes did not cross, so the earlier segment-only leakage check missed this.
- **Cause:** Normalized or supported-semantic duplicate components could move
  one segment without moving all other segments extracted from the same parent.
- **Fix:** `scripts/build_dataset_splits.py` unions every segment from each
  parent document before normalized and supported-semantic links, rejects any
  remaining parent crossing, and records hashes for text, audio, and semantic
  source files. A separate ignored candidate at
  `data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/` retains all
  114,064 rows and reports zero parent-document crossings. It moves 1,624
  assignments to keep connected groups together; the recommended view moves
  six records from test to train with no additions or deletions. A separate
  GarhwaliBench candidate now matches all 392 internal test rows to the
  corrected recommended test view and retains 112 ASR rows and all 3,847
  external task records.
- **Limits:** The candidate is not promoted, published, or used for new model
  selection. Its deterministic character-bigram diagnostic is 14.123460 on
  already-scored open test rows, so it is historical evidence, not an
  independent accuracy result. Previously used checkpoints may have seen rows
  assigned differently in the candidate; old scores remain historical.
  CrossSum exact URL grouping is clean, but FLORES lacks row-level source URLs.
  Semantic/paraphrase and checkpoint-exposure audits remain open. See the
  [parent-safe split audit](benchmark-parent-safe-split-audit-2026-09-28.md).
- **Verification:** Split-focused tests pass 6/6; full pytest passes 580/580;
  documented unittest passes 578/578; candidate report shows zero exact-text,
  normalized-text, supported-semantic, parent-document, and identified-speaker
  crossings; all output artifact hashes and counts independently match the
  report. No source rows were removed and no neural inference ran.

### BMR-021 — Aggregate-scored test rows were not reconciled to current lineage

- **Severity/status:** High; audit logic fixed locally on 2026-09-29.
- **Evidence:** The prior lineage audit treated the current internal-text test
  as unresolved because it found no row-level prediction file. The current
  benchmark had computed an aggregate character-bigram score on that exact set,
  so prediction-row matching alone understated prior test use.
- **Fix:** `scripts/audit_model_accuracy_lineage.py` now verifies the benchmark
  manifest and internal-text input hashes, selected test IDs and normalized
  text, row count, row-set fingerprint, baseline identity, and aggregate score.
  Its report keeps aggregate-scored rows distinct from saved per-row
  predictions. Mismatched manifests or row sets are not counted as evidence.
- **Current result:** 402/402 recommended text-test rows match the aggregate
  baseline input; PPL is 14.397995 and the row-set SHA-256 is
  `d1ed8310f891926ba91e24f79367554dc4e22aeeeb56ad26be01e15c8246d06a`. The
  decision is historical/open, not independent-final. No row-level prediction
  output was saved and this audit computed no new score.
- **Split cross-check:** all 10,342 current recommended IDs map to source
  segments with 3,246 parent-text hashes and 3,072 duplicate-component IDs;
  neither group type crosses splits. The source file
  `all_segments.jsonl` hashes to
  `c77b54aa8ec7a550068b65ef2d07d65cfe8cfe65ae70c617890ae80246d5f429`. A
  coarser `provenance.file` scan finds nine of 11 ingestion files in multiple
  splits; those files can contain several works and are not parent-document
  identifiers, so source-work-level isolation is still not established.
- **Artifacts:** machine-readable evidence is generated locally at
  `data/processed/evaluation/garhwali_bench/model-accuracy-lineage-2026-09-29.json`
  (SHA-256 `a7f167fa3e007178814f352ebbe8a9a86577a16bb5a628d08a87442d7c134833`).
  It includes VAANI speaker identifiers and stays Git-ignored/local-only.
- **Verification:** focused regression tests cover an exact aggregate row-set
  match and rejection of a mismatched set; full-suite result is recorded below.

## Verification log

| Date | Check | Result |
| --- | --- | --- |
| 2026-09-26 | Translation runner focused tests | 13 passed after the metric edge-case fixes |
| 2026-09-26 | Translation dev baseline | 997/997 records; results in `data/processed/evaluation/translation/accuracy_dev/` |
| 2026-09-26 | NLLB local preflight | Blocked: pinned base snapshot and PEFT are missing; optional cached runtime supplies PyTorch/Transformers |
| 2026-09-26 | Legacy test prediction/report hashes | Unchanged from the recorded historical files |
| 2026-09-26 | ASR validation consolidation | Five saved validation outputs re-scored; all 269 ordered IDs/references and stored per-row metric counts reconcile; no test payloads opened |
| 2026-09-26 | ASR local preflight | Blocked for fresh SraVaani inference by missing base weights/NeMo; PyArrow and common audio-reader packages absent |
| 2026-09-26 | Initial Phase 2 suite before usage-labeler tests | `PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -q` — 485 passed; `git diff --check` passed; 17 updated documents had 0 missing local links |
| 2026-09-26 | Benchmark and final release audit refresh | Builder manifest SHA-256 `ce93c7c1c06680d04bf9b861cbfdf8ca11b6cf9bf1968ba9cf19687655b8865b`; release audit passed with 6 benchmark artifacts checked, zero errors, zero internal text/audio/speaker overlap, and one preserved XORQA train/dev duplicate group |
| 2026-09-26 | Model-lineage audit refresh | 11 manifest families and 34 saved prediction artifacts inventoried; exact split/cross-role duplicates remain listed; no new test inference or metrics were run |
| 2026-09-26 | No-download model/runtime preflight | Python 3.12.5; project `.venv` has no Torch/Transformers/PEFT/NeMo/PyArrow/audio readers; optional cache has Torch/Transformers only; SraVaani base and NLLB weights absent; existing fine-tuned checkpoints and Whisper-tiny weights present; no downloads |
| 2026-09-26 | Phase 2 overlap candidate scan | Initial detector output covered 12,510 text rows; 27 exact XORQA source-context groups were initially unreviewed. The subsequent adjudication verified and labeled them; four near pairs were also inspected. All rows remain present. |
| 2026-09-26 | Phase 2 usage adjudication | 27 exact XORQA source-context groups and 1 exact question group verified; 62 rows labeled diagnostic-only for independent source-generalization; four near pairs reviewed in same split; all rows retained |
| 2026-09-26 | Phase 3 draft contract validation | Eight views / 12,622 rows; 0 errors; 112/112 local ASR paths and audio hashes verified; contract migration gaps recorded |
| 2026-09-26 | Prior full-suite after Phase 2 usage labels | 498 tests passed before recommended-text and internal-text v0.2 validation cases were added |
| 2026-09-26 | v0.2 adapter export | Eight views / 12,622 rows; all legacy rows retained; 62 XORQA overlay rows validated; manifest SHA-256 `0352298d966d4ebcf1540bad913db283bc1cb9e69dfd85b7ea9e5b4fd8525fd1`; output is ignored/local-only |
| 2026-09-26 | v0.2 adapter focused tests | Seven passed: raw/scoring separation, missing-raw status, overlay linkage, ASR privacy, deterministic row retention, draft metrics, and hash-drift detection |
| 2026-09-26 | Full-suite verification before Phase 4 runner work | 508 tests passed; workspace was dirty, so recorded hashes identify workspace inputs rather than a clean commit |
| 2026-09-26 | Phase 4 evaluation-runner slice | 519 tests passed; manifest and translation focused tests passed; both historical-test gates, NLLB preflight paths, unavailable-MPS guard, mocked NLLB dev run, and real 997-row translation dev run passed; compilation and `git diff --check` passed; no downloads or paid jobs used |
| 2026-09-27 | Phase 2 overlap refresh | 12,510 inputs; 407 exact-text groups, 1 cross-split; 616 source-family groups, 27 cross-split exact-content families matching reviewed XORQA context groups; four near-text candidates, none cross-split; semantic and nested cross-language comparison still unresolved |
| 2026-09-27 | Phase 3/4 task scoring slice | Added versioned QA, summary, and translation scoring; scorer enforces exact IDs, dev-first/test opt-in, explicit missing-reference exclusion, and shared hash manifests. Schema preflight: 100/100 CrossSum dev summaries; 499/500 XORQA dev target answers. Draft export: 8 views / 12,622 records, manifest SHA-256 `8b6953da2bb4a45d2a72274617ca13949ad1cfdddb21b9fec54fb110194e03f1` |
| 2026-09-27 | Translation scoring and uncertainty | Shared scorer re-ran 997 saved FLORES dev predictions and exactly matched custom BLEU/chrF; 2,000 paired record-bootstrap resamples gave copy-vs-TM dev deltas of BLEU +0.01892665 (95% CI 0.01411908–0.02385223) and chrF2 +0.23002697 (0.22559907–0.23435906). Diagnostic only; no source clustering or new neural inference |
| 2026-09-27 | Retrieval manifest integration | Fresh dev-only BM25 baseline wrote shared run manifest; all 500 query IDs reconciled, with Recall@10 0.8% word / 1.0% character / 85.2% English oracle |
| 2026-09-27 | Saved generation manifest integration | Three mT0 seed outputs reconciled 390 predictions to 130 shared validation IDs and matching task/reference values; selected-ID hash equals the seed-43 training report; primary-reference diagnostics reproduce saved values; alternate-reference chrF2 sensitivity recorded; no inference/test scoring; checkpoint hashes and original sampling parameters unavailable |
| 2026-09-28 | Cross-language-label exact audit | 50 exact answer strings shared between XORQA English and Garhwali translated-answer fields; 10 cross source splits, all 2–6 normalized characters; report contains hashes and IDs only; rows and usage overlay unchanged |
| 2026-09-28 | Pre-source-page local verification | pytest 559/559 passed with project `.venv` dependencies; documented unittest 557/557 passed; compilation, v0.2 validator (8 assets, 0 errors), and `git diff --check` passed |
| 2026-09-28 | XORQA source-page family audit | 1,139/1,139 page locators parsed; 54 page families / 134 records cross splits, 32 with distinct passages; review-only overlay expanded to 138 retained rows; local v0.2 draft rebuilt with page-family hashes; no model inference or held-out rescoring |
| 2026-09-28 | Source-page integration verification | pytest 565/565; documented unittest 563/563; Python compilation and the v0.2 validator passed (8 assets, 0 errors); no inference or source-row removals |
| 2026-09-28 | XORQA retrieval source-page-cluster uncertainty and verification | 500 saved BM25 dev queries map to 461 page families; 34 multi-query families contain 73 rows. The 2,000-resample paired character-minus-word Recall@10 difference is +0.2 percentage points (95% CI 0.0–0.6); intervals are conditional on a fixed all-split 1,059-document corpus. Full pytest 569/569, unittest 567/567, compilation, v0.2 validation (8 assets, 0 errors), and `git diff --check` passed; no test scoring or inference |
| 2026-09-28 | XORQA saved-retrieval miss diagnosis | Hash/ID checks passed; 500/500 gold passages available in the fixed 1,059-passage all-split corpus. Word BM25: 496 zero-score misses; character BM25: 493 zero-score plus 2 ranked below 10; English-oracle: 74 misses at 10. No inference/test scoring |
| 2026-09-28 | Retrieval miss-analysis verification | Focused tests 3/3; full pytest 572/572 and documented unittest 570/570; compileall and `git diff --check` passed; no data or model output changed |
| 2026-09-28 | mT0 generation-output diagnostics | Verified 390 validation predictions across three 130-row seeds against source and per-seed hashes; strongest mode is 23/29 on Garhwali-to-English lexicon; no structural Unicode/empty/prompt-copy/control-token flags; focused tests 2/2, pytest 574/574, unittest 572/572, compileall passed; no inference/test scoring |
| 2026-09-28 | Phase 8 result eligibility reconciliation | Corrected stale development-only labels for previously scored test splits and the aggregate-scored internal text view; fresh lineage audit: 11 manifest families, 38 prediction artifacts; focused lineage tests 20/20, pytest 577/577, unittest 575/575, compileall passed; no inference or data changes |
| 2026-09-28 | Parent-safe split correction and source-family audit | Historical manifests: 50 parent documents / 1,523 segments cross train/test or train/validation; rebuilt ignored split and benchmark candidate: zero parent-document crossings and 392 text rows aligned to candidate test; CrossSum exact URLs do not repeat; FLORES lacks row-level source URLs; pytest 580/580, unittest 578/578, split tests 6/6; deterministic historical bigram diagnostic only, no neural inference or model selection |
| 2026-09-28 | ASR held-out identity and paired audit | Five saved runs reconciled to 112/112 audio hashes and cleaned references; 10,000-resample speaker-cluster intervals for four candidate-vs-base comparisons all include/touch zero; no inference/selection; focused tests 4/4; pytest 584/584, unittest 582/582 |
| 2026-09-28 | Legacy SraVaani validation source recovery | Legacy comparator input hash matched the 381-row saved SraVaani file; its 269-row selected per-record errors exactly reproduce the later manifested run (2,161 WER errors / 3,282 CER errors); 3/4-error gap to greedy sweep remains because sweep per-row outputs/config are unavailable |
| 2026-09-29 | Six-workstream benchmark refresh | Rebuilt v0.2 draft: 8 views / 14,703 rows; adapter SHA-256 `f1355a1096ab272c113c64e07199c6db9814731e6b06e1431806cb000383b98d`; validation 8 assets / 0 errors; recommended text 9,486/454/402, +2,077 versus prior candidate with all old rows retained and no split moves; 10,342 rows map to 3,246 parent-text hashes with no crossings; overlap audit 14,591 text-relevant inputs, 1 exact cross-split group, 402 intentional cross-view mirrors, 4 same-split near pairs, and 29 cross-split source-family groups; current aggregate text-test score lineage matched at PPL 14.397995; six local review cards added; full tests: pytest 608 and unittest 606; no inference, download, or upload |
| 2026-09-29 | ASR scorer integration | Shared scorer now emits corpus and per-record WER/CER, enforces exact record-ID coverage, lists empty-reference exclusions, and fingerprints ASR metric code in the run manifest; focused ASR/scorer tests passed; no inference, download, or upload |
| 2026-09-29 | ASR/rights audit verification | ASR shared scorer reproduced saved 269-row validation aggregates exactly; rights audit confirms 14,703/14,703 rows uncleared, 2,077 compatible-status and 8,265 unrecorded recommended-text rows, 112/112 ASR rows carry local audio/identifier flags; builder/validator pass with 0 errors; full pytest 622/622 and unittest 620/620; compileall and `git diff --check` passed; no paid job, inference, or upload |
| 2026-09-30 | Generation scorer and saved-output reconciliation | Integrated generation EM/chrF2 and failure diagnostics into the shared runner; reconciled three saved mT0 seeds to 130 matching rows in current validation, with 190/320 rows unscored; rescored only development predictions; see [generation report](generation-scoring-integration-2026-09-30.md); full pytest 624/624 and unittest 622/622; no new inference, paid job, download, or upload |
| 2026-09-30 | Five-area evaluation-lineage refresh | Re-audited 11 manifest families and 41 saved prediction files; found 15/29 recommended-train-to-instruction exact-text overlaps, 4 Meta Omnilingual train/test audio and 4 text groups plus 27 train/validation text groups, and 338 audio / 575 text groups from expanded-human train to experimental ASR test; experimental validation also has 397 audio / 683 text groups. Test sets remain historical/unresolved; 0/5 independent final-accuracy eligibility. Row-level ledger saved under ignored `data/processed/evaluation/garhwali_bench/model_accuracy_lineage_2026-09-30` because it includes speaker identifiers. |

See the [benchmark/model roadmap](benchmark-model-roadmap.md) for remaining
phases and the [benchmark research status](benchmark-research-status-2026-09-25.md)
for the earlier project-wide snapshot.
