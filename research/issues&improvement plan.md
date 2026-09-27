# Benchmark and model roadmap issues & improvement plan

**Updated:** 2026-09-26

**Scope:** issues found while executing the benchmark/model roadmap and its
immediately preceding retrieval, generation, and ASR work. This is a living
issue log, not a claim that every project file or dataset has been re-audited.

Every item records evidence, impact, action, and remaining status. Data and
model outputs stay local and Git-ignored. No Hugging Face jobs, paid compute,
downloads, uploads, or visibility changes were used in this pass.

## Current roadmap position

Phase 1's inventory/reproducibility refresh is complete for the 2026-09-26
workspace snapshot: the benchmark was rebuilt, the release and model-lineage
audits were rerun, the no-download runtime preflight was checked, and the full
suite passed 508 tests at the Phase 3 snapshot, 516 after the first Phase 4
slice, 518 after preflight checks, and now 519 after historical-test gating.
Phase 2 is in progress: exact source-context/question
overlaps now have a conservative row-level usage overlay, and the four
same-split near pairs were inspected. Phase 3 has started: a v0.2 schema
contract, validator, and deterministic local adapter cover the existing eight
views. The adapter links the overlay and keeps all 12,622 source rows, but
metric signatures remain draft. The schema/eligibility freeze and broader
semantic/cross-language review remain open.

Phase 5, baseline consolidation, is **partially complete**. The dependency-free
copy and translation-memory baselines cover all 997 FLORES development rows,
and the ASR candidates are consolidated from saved validation predictions and
aggregate test reports in [the ASR comparison](asr-baseline-consolidation-2026-09-26.md).
The ASR sweep, 61-trial, and expanded-human jobs represented by those reports
completed; none is known to have stopped because of a usage limit. Phase 5
still has other task areas and blockers, including NLLB inference. Phase 6 and
later gates remain open.

### What is paused or stopping progress

- **No recorded rate-limit pause in the completed ASR experiments:** saved
  reports show 6/6, 61/61, and 1/1 trials complete. This says nothing about
  unrelated remote jobs; no Hugging Face job status was checked in this
  local-only pass.
- **Fresh SraVaani inference is locally blocked:** the Hugging Face cache has
  metadata but no base-model weights; the local ASR runtime has PyTorch and
  Transformers only when `PYTHONPATH=.cache/asr-runtime` is set, and lacks
  NeMo. PyArrow and common audio readers (SoundFile, librosa, torchaudio) are
  also absent. `ffmpeg` is installed. Existing fine-tuned `.nemo` checkpoints
  and the Whisper-tiny model weights are present, but this pass did not run a
  new inference job.
- **Independent final ASR accuracy is not available:** the fixed VAANI test
  already has saved scores, SraVaani's upstream VAANI exposure is not
  item-level auditable, and references have not been native-adjudicated.
  Native review and dialect annotation remain deferred at the owner's
  direction.
- **One baseline provenance discrepancy remains:** a legacy 269-row SraVaani
  validation comparator differs from the current decoder-sweep greedy output
  by 3 word errors and 4 character errors. Its exact decoder/checkpoint/run is
  not recorded, so both values remain visible until provenance is resolved.
- **Historical test aggregates are not demonstrably paired:** the base report
  pins its 112-row test manifest, but the decoder-sweep and fine-tune reports
  omit their test manifest hashes. Matching word/character denominators alone
  cannot prove they contain identical utterances.

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
  `data/processed/evaluation/asr/curriculum_stage_0/report.json` record the
  same 269-row validation manifest and denominator (4,980 words; 17,342
  characters), with SraVaani at 2,161 word errors and 3,282 character errors.
  The saved RNNT greedy-batch validation output recomputes to 2,164 word errors
  and 3,286 character errors on 269 rows, using the same current normalizer.
- **Impact:** Both are credible development observations, but the old
  comparator lacks enough decoder/checkpoint/run metadata to designate it as
  the same baseline or explain the different hypotheses. Mixing the values
  without labeling the runs would make the ASR trend misleading.
- **Action:** Preserve both results as distinct runs in the dated
  [ASR consolidation report](asr-baseline-consolidation-2026-09-26.md). Before
  any later combined scorecard treats them as one baseline, recover the legacy
  prediction artifact/configuration or explicitly retire that comparator from
  current comparisons.

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

- **Severity/status:** High; open, historical comparison limitation.
- **Evidence:** The base model report records test manifest SHA-256
  `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`. The
  original 102-step adaptation report records a different SHA-256,
  `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`. The
  decoder-sweep report's `selected_test` aggregate and the six-config,
  61-trial, and expanded-human `held_out_test` aggregates do not include a
  test-manifest hash. Their denominators match, but that alone does not prove
  identical examples. The separate 2026-09-11 report does document a successful
  audio-hash/reference match for the local Whisper fine-tunes. No ASR test
  prediction files were opened for this audit.
- **Impact:** Historical WER/CER values can be quoted with their source
  reports, but apparent differences between SraVaani decoder/fine-tune runs
  are not verified paired deltas. The earlier local-Whisper comparison is
  separately row-aligned by audio hashes and references. Prior reports call
  these SraVaani runs the fixed 112-row VAANI test, but local aggregate metadata
  is insufficient to independently verify that claim for every run.
- **Action:** Keep test metrics labeled historical and prohibit model
  selection from them. For a future reproducibility audit, require each run
  to save the test manifest hash and selected record IDs; do not re-score or
  inspect the existing held-out payloads as part of this step.

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
  records 62 row-level labels, and never removes source rows. Seven detector
  tests and seven usage-label tests cover Unicode normalization, same-language
  near-match guards, source-link grouping, stable ordering, collection-URL
  exclusion, exact-hash verification, retained-row behavior, split consistency,
  and CLI output.
- **Remaining action:** Carry the usage overlay and context-family grouping into
  the v0.2 schema; decide a group-aware diagnostic aggregation/split policy.
  Add cross-language candidate links only when source-alignment metadata supports
  them; do not infer them from script-different character similarity.
- **Verification target:** tests prove repeated rows are reported without
  deletion, stable hashes/order are reproducible, and a negative scan is
  labeled “no candidates found by this method,” not “no leakage.”

### BMR-014 — v0.2 schema and metric contract is not frozen

- **Severity/status:** High; open, Phase 3 blocker.
- **Evidence:** The draft contract is in
  [garhwali-bench-v0.2-schema-contract.md](garhwali-bench-v0.2-schema-contract.md).
  The dependency-free validator `scripts/validate_benchmark_v02.py` passes
  eight views / 12,622 rows with zero structural or integrity errors, including
  112/112 local ASR audio hashes. Its local JSON report SHA-256 is
  `2e0f2dc6286a6a96f8043ce1c6ef6d09ae1987f3ff486974c7cb32e828d4c32c`.
  The deterministic adapter `scripts/build_benchmark_v02.py` now writes all
  eight views / 12,622 rows to an ignored local-only package; its manifest
  SHA-256 is
  `0352298d966d4ebcf1540bad913db283bc1cb9e69dfd85b7ea9e5b4fd8525fd1`. It
  links the 62-row overlay, preserves each legacy source row, records available
  raw/scoring text separately, and self-validates output hashes/counts.
  Seven focused adapter tests and the 508-test suite passed at export time; the
  current Phase 4 suite passes 519 tests.
- **Known migration gaps:** verified original raw text is absent from some
  internal/recommended v0.1 rows; the adapter explicitly leaves those raw
  values unavailable. Metric signatures are recorded as drafts, but
  denominators, empty-reference rules, source-group uncertainty, and
  CrossSum/QA metric implementations are not frozen. Broader source-family and
  cross-language checks remain open. Rights remain a separate release gate;
  schema validation is not rights clearance.
- **Action:** recover raw values only where provenance supports an exact link;
  implement and edge-test task metrics; define denominators, exclusions,
  uncertainty, and source strata; complete Phase 2 grouping; and write public vs
  local-only cards. Keep this draft local until those gates are complete.
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
- **Remaining:** Adopt the shared contract in ASR, retrieval, masked-LM,
  generation, and QA runners; add task-specific preflight and row-level output
  reconciliation tests. Real NLLB inference remains unverified because its
  pinned model snapshot is not cached. Do not describe Phase 4 as complete yet.
- **Exit condition:** every in-scope scoring runner can reproduce the requested
  split from recorded code/config/input/model/runtime hashes, and every output
  row reconciles exactly to the selected split.

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

See the [benchmark/model roadmap](benchmark-model-roadmap.md) for remaining
phases and the [benchmark research status](benchmark-research-status-2026-09-25.md)
for the earlier project-wide snapshot.
