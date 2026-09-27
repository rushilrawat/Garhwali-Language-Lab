# Garhwali Benchmark and Model Research Roadmap

**Status snapshot:** 2026-09-26
**Scope:** GarhwaliBench and the model-research suite in this repository
**Execution:** Local-first; no paid Hugging Face Jobs. Native-speaker review and dialect annotation remain deferred at the owner's direction.

This is the working plan for moving from useful but mixed-history experiments to a reproducible, accurately described benchmark and model-research program. It records what exists, what evidence permits us to say, what happens next, the tools to use, and the gate for each phase.

## 1. What we are building

The project has two connected deliverables:

1. **GarhwaliBench:** versioned, source-traceable evaluation data and scripts for Garhwali language modeling, translation, retrieval, question answering, generation, speech recognition, and future speech synthesis.
2. **Model research suite:** reproducible comparisons and bounded experiments showing what current multilingual models can and cannot do with Garhwali.

A corpus row, a valid benchmark row, and evidence of model quality are different things. A row may be valuable language material but have uncertain rights, noisy OCR, an unreviewed transcript, a duplicate, or prior evaluation use. Represent and count these states rather than collapsing them into one overall accuracy number.

Native or dialect review is not a prerequisite for internal automated experiments. Reports must state when references are machine- or source-derived and have not been adjudicated by a Garhwali speaker. Automated metrics cannot certify that a transcript, translation, spelling, or dialect label is linguistically correct.

## 2. Honest status at this snapshot

The project-wide measured scorecard is [benchmark-research-status-2026-09-25.md](benchmark-research-status-2026-09-25.md); this translation workstream has a [2026-09-26 dev-only refresh](translation-quality-2026-09-26.md), the ASR tasks have a [2026-09-26 baseline consolidation](asr-baseline-consolidation-2026-09-26.md), and the living issues are in the [issues and improvement plan](issues%26improvement%20plan.md). Row-level split and prediction lineage is in [model-accuracy-lineage-2026-09-24.md](model-accuracy-lineage-2026-09-24.md).

| Area | Verified state | What the evidence supports |
| --- | --- | --- |
| Benchmark artifacts | Five candidate artifacts exist: FLORES, CrossSum, XORQA, internal text, internal ASR. Three external schemas pass validation across 3,847 records. | A machine-checkable candidate suite exists; it is not yet a fully independent or native-validated benchmark. |
| Internal text | 398 candidate rows; zero exact overlap against the 7,490-row recommended Garhwali training view. Character-bigram perplexity is 14.122106 on that candidate versus 17.000058 for the broad 106,915-row view, using the same deterministic scorer. | A controlled data/modeling floor, not neural-model accuracy or proof that all training rows are correct. |
| Language modeling | IndicBERTv2's 4,096-step continuation has mean validation cross-entropy 5.089108 across three seeds. | Validation loss only; tokenizer and model differences limit comparisons, and no independent final set is approved. |
| Translation | FLORES copy and translation-memory baselines were scored on 1,012 rows; an NLLB Hindi-token proxy used 32 rows. | Historical comparison/debugging evidence. FLORES test has already been examined; the tiny proxy is exploratory, not a Garhwali-token translation benchmark. |
| Retrieval | XORQA has 539 test questions with prior predictions; best saved IndicBERTv2 Recall@10 is 0.103896. A new 500-query dev-only BM25 rerun gets 0.8% word and 1.0% character Recall@10; English-oracle BM25 gets 85.2%. | A historical test baseline and clear Garhwali-to-English retrieval gap. Dense dev inference is blocked by missing local runtime/weights; the test is not fresh. |
| Generation | All three mT0 32,768-step seeds and validation diagnostics are saved. Seed 43 has the best validation cross-entropy (4.188287); the best adapter chrF2 is 0.074003 versus 0.088327 for zero-shot base. Existing run records report one selected-seed evaluation on an 86-row test. | No generation adapter is promoted. Test is historical, and 172 test-prediction rows do not map to current local manifests; references remain unreviewed. The earlier partial-run report is superseded by a later seed-43 retry. |
| ASR decoding | The six-configuration sweep completed. RNNT beam size 8 was selected on validation: WER 43.253%, CER 18.919%, versus greedy WER 43.454%, CER 18.948%. Its report contains a 112-row test aggregate of WER 42.761%, CER 17.410%. | A small decoding improvement on validation; the test is historical and its report has no manifest hash. SraVaani's upstream VAANI example overlap is unknown. One unsupported TSD configuration failed and is documented. |
| ASR fine-tuning: 61 trials | All 61 trials completed. The validation-selected decoder/joint run improved WER from 43.454% to 42.711% and CER from 18.948% to 18.660%. Its historical test aggregate is WER 43.528% / CER 17.494%; the base report is 42.761% / 17.606%. | Not promoted: the fine-tune report omits a test-manifest hash, so the apparent WER change is not a verified paired delta. This work was not stopped by a rate limit. |
| ASR fine-tuning: expanded human transcripts | Training used 5,513 hash-filtered human-transcript clips (8.112 hours); 3,886 rows lacked complete speaker identity. Validation WER/CER improved to 42.209%/18.302%; the historical test aggregate is 43.289%/17.396%. | Not promoted: the fine-tune report omits a test-manifest hash, so a paired comparison to base is unverified. Experimental because speaker identity is incomplete and SraVaani upstream exposure is unresolved. |
| ASR references and independence | VAANI validation/test predictions already exist. SraVaani's model card identifies VAANI as an upstream source and reports 31,255 hours of VAANI pretraining plus about 31,270 hours of labeled fine-tuning from VAANI and other open speech data; it does not expose example-level overlap. | VAANI results are development/historical evidence, not independent estimates of generalization. Do not rescore test to choose a model. |
| TTS | Speech manifests and readiness checks exist; no TTS system has a valid Garhwali quality result. | Readiness and pair-integrity only. MOS or naturalness needs listeners and cannot be inferred from automated checks. |
| Independent final accuracy | Zero of five task areas are approved for independent final-accuracy claims: language modeling, translation, retrieval, generation, and ASR. | There is no defensible single project-wide model-accuracy score today. |
| Review and tests | Native adjudications remain deferred. The current full suite passes 519/519 automated project tests. | Passing checks prove the checks passed, not that language labels are correct. |

### Key test-history rule

Some project fine-tuning experiments selected on validation and then evaluated once on the fixed VAANI test. That is a reasonable internal experiment protocol, but it does not make the result independent of upstream SraVaani exposure. All VAANI test scores are now historical. Use them to describe completed experiments; do not tune, choose, or claim a blind final model from them.

Saved outputs for the 61-trial, six-decoder, and expanded-human runs are under **data/processed/evaluation/asr/sravaani_refined_61/cloud_output/**, **data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/**, and **data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/**. These are generated artifacts and should stay excluded from Git unless an explicit, rights-reviewed release package calls for selected derived files.

## 3. Evaluation rules for every phase

1. **Pin every input.** Record source URL or dataset/repository revision, rights state, source-file hash, derived-manifest hash, model revision and weight hash, code commit, tokenizer, preprocessing, decoding, library versions, device, seed, run timestamp, and output hash.
2. **Keep provenance row-level.** Preserve stable record ID, source ID, parent page/book/audio ID, original script/text, normalized comparison form, transcript/reference status, language/script evidence, speaker where permitted, quality flags, exact/near-duplicate group, rights state, split, and exclusion reason.
3. **Keep source values intact.** Deduplication creates groups and task-specific views; it does not silently delete or rewrite source records. Report counts before and after each view.
4. **Select on development data only.** Choose prompts, checkpoints, decoding, normalizers, vocabulary boosts, thresholds, and hyperparameters on train/dev/validation under a frozen protocol. Never select a configuration from test performance.
5. **Use test evidence once per frozen candidate.** Before a test run, store selected checkpoint and configuration hashes. If test data are public or previously scored, call them open, historical, or development evidence, not blind or untouched.
6. **Treat external checkpoint exposure as unknown by default.** Exact matching catches some overlap, not translated, paraphrased, audio, or undocumented pretraining exposure. A negative local overlap audit does not prove uncontaminated evaluation.
7. **Separate task metrics.** WER, BLEU, Recall@10, cross-entropy, and OCR CER measure different behaviors. Never average them into a single accuracy score.
8. **Show uncertainty and slices.** Report row count and coverage with every metric; include paired confidence intervals where sample size allows. Cluster resampling by speaker, source work, or question family where examples are dependent. Mark small slices as descriptive.
9. **Keep quality and rights separate.** Rights determine redistribution; quality determines fitness for a task. A permissive license does not certify language quality, and uncertain rights do not mean the local source record should be erased.
10. **No paid cloud in this plan.** Use existing local artifacts and installed tools. If weights, compatible dependencies, or local compute are absent, record a preflight blocker and stop before downloading or launching paid compute.

## 4. Benchmark data contract

Every benchmark example should be representable as a stable JSONL row with the following conceptual fields:

- **Identity:** benchmark version, task, record ID, source-record ID, parent document/recording ID, source revision.
- **Inputs and references:** task input, reference output(s), original script, normalized scoring form, reference provenance, and whether a human adjudicated the reference.
- **Language context:** language/script tags and evidence, optional dialect/region/speaker tags with confidence and provenance, genre/domain, code-switch flags.
- **Integrity:** SHA-256 for text/audio/source bytes where available; exact and near-duplicate group IDs; conflicting-reference marker; allowed-for-training/dev/test booleans; exclusion reason.
- **Rights:** source license or terms URL, redistribution status, attribution requirement, review state. Do not present an inferred license as confirmed.
- **History:** which run scored the record, when, on which model/config hash, and whether it is still eligible for selection or final evaluation.

Keep identifiable speaker IDs in a local-only ledger when public disclosure is not appropriate. Public reports can retain aggregate split counts without publishing sensitive row-level fields.

Every prediction should carry benchmark record ID, input hash, raw prediction, scored prediction, normalization version, model/checkpoint/revision hash, decoding/prompt-config hash, run ID, and per-example error counts. This lets later audits distinguish model changes from normalization or data changes.

## 5. Task suite and score definitions

| Task | Candidate data and baseline | Primary metrics | Required diagnostics and caveats |
| --- | --- | --- | --- |
| Text modeling | Recommended 7,490-row Garhwali training view; 398-row internal candidate; character-bigram baseline and IndicBERTv2 continuation. | Token cross-entropy/perplexity within the same tokenizer/model; character bits-per-character for a fixed character model. | Record tokenizer and token fertility. Perplexities from different tokenizers are not fair direct comparisons. Break down by source and script. |
| Machine translation | Garhwali-to-English FLORES candidate; copy-source and development translation-memory baselines; existing NLLB Hindi-token proxy. | SacreBLEU with full signature and chrF2; exact match only for canonical-answer tasks. | Report direction, tokenization, normalization, references, and copy baseline. FLORES test is already scored. The 32-row Hindi proxy is exploratory. |
| Cross-lingual summarization | CrossSum candidate. | chrF2 and ROUGE-L; BLEU optional only for continuity. | Add source/target copy, length ratio, repetition, empty/malformed output, language checks. Verify source-family split isolation. |
| Question answering | XORQA candidate. | Exact match and token F1 under pinned normalization. | Separate answer generation from evidence retrieval; record answerability and evidence passage. Preserve and flag the known exact train/dev repeat; neither repeated row is in test. |
| Retrieval | XORQA and internal source-grounded query/document pairs; BM25 or TF-IDF, dense IndicBERT, optional reranker. | Recall@1/5/10, MRR@10, nDCG@10. | Group paraphrases/questions for one answer in one split. Fix candidate corpus; report its size and source coverage. Existing XORQA test has prior predictions. |
| Instruction/generation | Garhwali prompts/references in the instruction set; mT0 checkpoints. | Exact match/token F1/chrF as appropriate; validation loss is a training diagnostic. | Three seeds and diagnostics are complete; adapters have lower validation chrF2 than base. Existing records say the 86-row test was scored once after validation selection; its prediction-to-manifest mapping is unresolved. Do not rescore it or make native-correctness claims. |
| ASR | VAANI and Meta Omnilingual subsets with source-specific splits; SraVaani and Whisper comparisons. | Corpus WER and CER from summed edit counts, not mean per-row percentages. | Store raw/normalized text and normalization signature; slice by duration, source, noise, code-switch, transcript length. VAANI cannot confirm SraVaani generalization because example-level overlap is unavailable; Meta test is unresolved for this checkpoint. |
| TTS readiness | Paired audio/transcript manifests and speaker-safe split audits. | Current phase: coverage/integrity counts only. Future: listener ratings under an explicit protocol, intelligibility and pronunciation review. | Do not report MOS or human preference without listeners. ITU P.800.1 terminology is a reference for future listening-quality scales. |
| OCR/text extraction | Incoming PDFs only when a verified transcription/reference exists. | CER/WER on a page-stratified sample with explicit reference provenance. | Store extracted text, corrected reference, page-image hash, OCR engine/version/config, correction provenance. Without references, report coverage and structural failures, not accuracy. |

For error rates, publish raw numerator and denominator. WER should include word errors and reference words; CER should include character edits and reference characters. This prevents percentages with different sample sizes from looking interchangeable.

## 6. Phased work plan

Each phase has a deliverable and exit gate. A phase can be complete for internal research while public release or language-validation claims remain incomplete.

### Phase 0 — Lock scope, use policy, and claims

**Purpose:** define what the benchmark measures and keep historical scores honest.

**Work**
- Keep GarhwaliBench as task-specific evaluations rather than one blended score.
- Maintain two labels: **candidate benchmark** for automated/public/source-derived material, and **independent evaluation** only when split history and model exposure permit it.
- Freeze permitted uses of each split: training, development/model selection, historical-only, or final-evaluation-eligible.
- Keep the owner's deferral of native-language and dialect review visible in cards and reports.
- Do not hide or discard source rows to improve a metric. Record task-specific exclusions and reasons.

**Tools:** current lineage audit and JSON/Markdown status reports.

**Exit gate:** every manifest has a task, reference source, split status, scoring history, rights state, and claim limit.

**Status:** partly complete; scorecard and lineage audit exist. This roadmap records outstanding evidence limits.

### Phase 1 — Rebuild the inventory and reproducibility snapshot

**Purpose:** verify the workspace rather than assuming yesterday's counts or artifacts are current.

**Work**
1. Run the benchmark builder and final benchmark audit.
2. Run the model-accuracy lineage audit; verify prediction hashes and row-set fingerprints.
3. Inspect local model artifacts and runtime dependencies without downloading or installing anything.
4. Reconcile 61-trial, six-decoder, and expanded-human outputs against their JSON reports and research notes.
5. Ensure reports do not count .keep files, caches, or temporary files as usable artifacts.
6. Record Git commit, manifest hashes, tool versions, and test result in the status report.

**Existing tools:** **scripts/build_garhwali_benchmark.py**, **scripts/audit_final_release.py**, **scripts/audit_model_accuracy_lineage.py**, **scripts/asr_metrics.py**, Python standard library, project unittest suite.

**Exit gate:** deterministic rerun agrees with the current scorecard; changed counts or missing model artifacts become explicit findings.

**Status (2026-09-26):** the benchmark builder, final release audit, model-lineage audit, and no-download runtime preflight were rerun. The benchmark manifest rebuilt to SHA-256 `ce93c7c1c06680d04bf9b861cbfdf8ca11b6cf9bf1968ba9cf19687655b8865b`; the final audit passed with zero errors and one preserved XORQA train/dev exact-text warning. The suite passed 508 before Phase 4, 516 after its first runner slice, 518 after manifest/device-preflight checks, and now 519 after historical-test gating. The model-lineage report inventories 11 manifest families and 34 prediction artifacts, with exact split/cross-role overlaps retained in its local-only JSON ledger. The project `.venv` lacks model/audio dependencies; `.cache/asr-runtime` exposes PyTorch and Transformers but not PEFT, NeMo, PyArrow, SoundFile, librosa, or torchaudio. SraVaani base weights and the NLLB snapshot are not cached. The SraVaani fine-tuned checkpoints and Whisper-tiny checkpoint exist locally, but a complete local audio-to-prediction path remains unverified. No download or paid job was used. The detailed hashes and limitations are recorded in [the updated measured status](benchmark-research-status-2026-09-25.md).

### Phase 2 — Close split and contamination gaps

**Purpose:** protect model selection and avoid calling public or potentially exposed examples independent.

**Work**
- Freeze manifests by content hash and assign each row a usage state.
- Build exact duplicate groups across raw/normalized text, translated text, audio hash, reference hash, document/page ID, speaker ID where available, and task family.
- Add near-duplicate candidate checks for normalized text and cross-language parallel content. Save candidate pairs and scores with review state rather than auto-deleting rows.
- Group questions, paraphrases, translations, and summaries tied to one source passage or cultural work before splitting.
- Preserve the XORQA train/dev repeat and expose it as a named warning.
- Treat previously scored public test rows as historical/development-only.
- Keep VAANI as development evidence for SraVaani. Zero local audio-hash overlap proves only that the local split hashes differ; it cannot reveal upstream SraVaani training examples.
- Keep Meta Omnilingual internally safe test rows unresolved until model-pretraining exposure is documented. Internal split flags do not settle checkpoint exposure.
- Do not treat a benchmark canary string or a negative exact-text match as proof that a checkpoint never saw translated or paraphrased test content.

**Tools:** existing hash-lineage scripts; Python Unicode normalization and SHA-256; MinHash/character n-gram candidate generation only if needed; reviewable pair reports. Add dependencies only for a demonstrated performance need.

**Exit gate:** candidate rows have duplicate-family IDs, split manifests are content-addressed, source-split errors are itemized, and every exposure claim is evidenced or explicitly unknown.

**Status (2026-09-26):** the review-only scan covers 12,510 text rows. Exact verification confirmed 27 XORQA source-context groups across original splits and one exact train/dev question repeat; a local overlay labels 62 affected records as open-diagnostic-only for source-independent claims while retaining all rows. The four near-text pairs were inspected: three are variants inside existing recommended-train duplicate components, and one is a same-context/same-answer pair within XORQA dev. No near pair crosses splits. The raw candidate scan remains available, while the adjudication and usage-label record supplies the reviewed interpretation. Semantic and cross-language matching remain outside the scan, so Phase 2 is still open. Independent final-test approval remains zero of five areas.

### Phase 3 — Freeze benchmark v0.2 data and metric contracts

**Purpose:** ensure each task has precise input/reference schemas and scoring before more modeling.

**Work**
1. Version task schemas and required metadata.
2. Publish train/dev/test counts and file hashes for every view.
3. Validate empty strings, malformed Unicode, script mix, impossible references, duplicate IDs, conflicting labels, audio paths, and rights fields.
4. Keep raw input, normalized scoring text, and transformation version separately.
5. Add metric tests for Unicode, punctuation, whitespace, Devanagari combining marks, empty reference/prediction, and tokenizer edge cases.
6. Include denominators, exclusions, coverage, source strata, and run/config hashes in every report.
7. Freeze an **open development release** separately from a final-claim evaluation protocol. Public test references are acceptable as an open-benchmark choice; scores must then be labeled open-set/historical, never blind.

**Tools:** Python, JSONL, SHA-256, existing unit tests, Markdown cards. Add JSON Schema only if dependency and maintenance costs are justified.

**Exit gate:** schema, normalization, metric, hashes, and counts pass checks; cards specify public and local-only fields.

**Started (2026-09-26):** the v0.2 schema contract is drafted in
[garhwali-bench-v0.2-schema-contract.md](garhwali-bench-v0.2-schema-contract.md).
The dependency-free validator checks eight current views / 12,622 rows, exact
text normalization and hashes, required external task references, IDs, rights
metadata, and all 112 local ASR paths/audio hashes. It passes with zero errors.
This validates current v0.1 inputs against the draft contract; it does not mean
the v0.2 export or metric signatures are frozen. The contract records legacy
internal-text migration gaps and keeps source rights separate from use
eligibility.

**Adapter update (2026-09-26):** `scripts/build_benchmark_v02.py` now writes a
deterministic, local-only draft package to the ignored
`data/processed/evaluation/garhwali_bench/v0.2-draft/` directory. The export
retains all **12,622 rows** across eight views, links and verifies the 62-row
XORQA usage overlay, preserves each v0.1 record, separates source/scoring text
where available, records normalizer and draft metric IDs, and self-checks
output hashes/counts. Manifest SHA-256:
`0352298d966d4ebcf1540bad913db283bc1cb9e69dfd85b7ea9e5b4fd8525fd1`.
Seven focused adapter tests passed at export time with the 508-test suite; after
the Phase 4 runner additions, the current full suite passes 519 tests. The export
does not clear rights, score models, or make every raw source value available.
Still open are raw-text recovery where provenance permits, frozen metric and
denominator policies, metric implementations/edge-case tests, source-group and
cross-language review from Phase 2, and a public/local field card. Details:
[the adapter report](benchmark-v02-export-2026-09-26.md).

### Phase 4 — Build one small, reproducible evaluation runner

**Purpose:** standardize run metadata without building a generic agent framework.

**Work**
- Use task-specific Python entry points already present; do not replace them with a universal orchestration framework.
- Add a lightweight shared run manifest only if it removes repeated provenance code. Include benchmark/split/input hashes, model/revision hash, prompt/decoder config hash, metric/normalizer signature, code commit, library/device versions, seed, timestamps, output hash, and status.
- Write per-row predictions as JSONL and aggregate reports as JSON.
- Make an explicit split argument mandatory; default to dev and require a separate explicit option for test.
- Fail before model allocation when checkpoint, split, hashes, paths, or runtime are invalid.
- Keep speaker identifiers in a local-only ledger where appropriate; generate privacy-safe aggregate reports.
- Keep training logic separate from scoring logic.

**Tools:** Python, pathlib, hashlib, JSONL, unittest; PyTorch/Transformers/PEFT/NeMo only for tasks where they fit. Do not use LangChain or LangGraph for metric computation or experiment selection; deterministic scripts are simpler to reproduce and audit.

**Exit gate:** a run can be reproduced from its command/config/hashes/pinned environment, and output rows reconcile exactly to the requested split.

**Started (2026-09-26):** the shared writer in
[`scripts/evaluation_run_manifest.py`](../scripts/evaluation_run_manifest.py)
is now used by the dependency-free translation baseline and the NLLB runner.
Completed runs write predictions, aggregate report, and `run_manifest.json`;
the manifest links the input and selected-row hashes, exact selected IDs,
canonical config hash, pinned model/revision metadata (including local config
hash for NLLB), source-code hashes, Git commit and dirty flag, runtime/device,
timestamps, seed, completion status, and prediction/report hashes. It rejects
row-count or record-ID disagreement before writing any artifacts.

NLLB preflight now validates split policy, input rows, duplicate IDs, local
checkpoint/adapter structure, token limits, and device before importing
PyTorch/Transformers. Both translation runners require `--split test` and
`--allow-historical-test` for historical test scoring. Focused tests cover fail-fast paths and use mocked
model modules to verify a full dev-run artifact set without downloading or
allocating a model. A real dependency-free run then reproduced the complete
997-row FLORES dev baseline in the ignored
`data/processed/evaluation/translation/phase4_manifest_dev_gated/` directory. Its
input SHA-256 is
`7c96d63be5f43e6a65fc229238c6d295d983fe46be032e9f8418d32150225097`, its
selected-row SHA-256 is
`d3bf6084025d78bd2eede315965ee2cb981be2d3a1b59d7952e7c1deb7b5e0d5`, and all
997 ordered IDs reconcile between the manifest, report, and predictions. Its
prediction hash is `354bb782ed8c4c1361320a736e45ffe1043198bf08a248fbea24644d79bb0a2b`
and report hash is
`14fb80f411d2d30fe4bab5e97fc1576d01d19a9afe4e8939a2e9078d7592c459`; both
verify against the manifest. It reproduces dev
translation-memory BLEU 0.01992188 and chrF2 0.23808697; no test rows were run.
The latest full suite passes 519 tests; compilation and `git diff --check` pass.

This is the first Phase 4 slice, not the phase exit gate. The pinned NLLB
checkpoint is absent locally, so no real NLLB output has been generated. The
manifest/preflight contract still needs adoption and task-specific checks for
ASR, retrieval, masked-LM, generation, and QA runners. Runtime lockfiles and
representative local model reruns must also be reconciled before calling Phase
4 complete.

### Phase 5 — Reproduce and consolidate baselines

**Purpose:** establish one canonical baseline per task without rescoring tests.

**Work**
- **Text:** rebuild the deterministic character baseline on the recommended Garhwali training view; retain IndicBERT validation loss as a distinct representation-learning diagnostic.
- **Translation:** standardize copy/TM/NLLB baselines on eligible dev data; keep already-scored FLORES test historical.
- **Retrieval:** the lexical development baseline is now reproduced with fixed candidate-set hashes and source-row mappings; word/character Recall@10 is 0.8%/1.0%. Reproduce IndicBERTv2 on dev only when the pinned local weights and runtime are available. Do not tune on the 539 previously scored XORQA test questions.
- **Generation:** all three mT0 seeds and dev diagnostics are already saved. Seed 43 wins validation loss but not generation chrF2; all adapters underperform base chrF2. Preserve the result and do not reopen the historical 86-row test.
- **ASR:** retain base, decoder sweep, 61-trial, and expanded-human outputs with consistent metric normalization. Compare in one table; do not promote a fine-tune based on the already-used VAANI test.
- **TTS:** finish only pair-integrity and speaker-overlap readiness checks; no synthesis-quality claim.
- Do not overwrite historic reports; link them from a dated consolidation report.

**Execution update (2026-09-26):** Translation runners now default to `dev`,
write to split-specific output directories, sort and hash selected rows, and
record exact record IDs. The custom BLEU scorer now rejects empty denominators
and reports empty-record counts. The local copy/TM run covers all 997 FLORES
dev pairs; results and limitations are in
[translation-quality-2026-09-26.md](translation-quality-2026-09-26.md). The
previously scored test prediction and report hashes are unchanged. NLLB
inference is blocked because the pinned base snapshot and PEFT are not local;
the optional cached runtime exposes PyTorch/Transformers, but the project
`.venv` does not. This completes the dependency-free part of translation
baseline consolidation; it does not complete Phase 5 as a whole.

**ASR consolidation update (2026-09-26):** Saved base, decoder-sweep,
six-config, 61-trial, and expanded-human outputs are compared in
[the dated report](asr-baseline-consolidation-2026-09-26.md). The five
validation prediction files use identical ordered audio paths/references across
269 rows and recompute exactly with the local WER/CER normalizer. Fine-tunes
improve selected validation metrics. Their saved test WER aggregates are
numerically higher than the base report, but those reports omit test-manifest
hashes, so exact paired deltas are not verified and none is promoted. A legacy
SraVaani validation comparator differs slightly and lacks decoder/checkpoint
provenance; it is tracked as BMR-009 in
the [issues and improvement plan](issues%26improvement%20plan.md). No test
payloads were opened or re-scored. This completes ASR consolidation from saved
artifacts, not Phase 5 overall.

**Tools:** current task scripts and metrics; SacreBLEU only if installed/pinned and comparison is intended to follow its standard. The current custom BLEU uses add-one smoothing and must not silently be relabeled SacreBLEU.

**Exit gate:** one canonical reproducible baseline report per task, distinguishing current candidates, historical results, and final-eligible metrics.

### Phase 6 — Run bounded model-improvement experiments on dev only

**Purpose:** spend effort where an experiment can still change a model decision without consuming a final test.

**Shared experiment protocol**
1. Write an experiment card: hypothesis, baseline, training-view hash, eligible dev hash, one primary metric, guardrail metric, controlled variables, seeds, maximum local runtime, outputs, stop condition.
2. Preflight checkpoint bytes, software compatibility, inputs, CPU/GPU/MPS, storage, rights, and split isolation.
3. Change one factor per ablation; preserve failed and neutral runs.
4. Use dev only for checkpoint, prompt, decoding, tokenizer, and hyperparameter selection.
5. Save predictions and configuration hashes before drawing conclusions.
6. Do not promote a small noisy score difference without paired uncertainty and error-slice checks.

**Priority order**
1. **ASR decoding/error analysis:** use completed six-configuration and 61-trial results; do not repeat them. Investigate recurring validation errors only if a compatible local checkpoint/runtime exists. Current local preflight does not pass.
2. **Text modeling:** continue the existing three-seed IndicBERTv2 validation work only if exact checkpoint/runtime are local. Compare against the same frozen character baseline and domain-stratified dev. Report cross-entropy per tokenizer; do not make a cross-tokenizer perplexity league table.
3. **Retrieval:** compare BM25/TF-IDF with saved dense IndicBERT results on query-group-safe dev. Fix the candidate corpus and inspect misses before considering a reranker.
4. **Generation:** validation generation diagnostics already cover all three saved mT0 seeds. Use these to guide future data/metric changes; do not spend more compute reproducing them or rescore the historical test. Native language/script quality remains unverified.
5. **Translation:** use Garhwali-to-English dev pairs with copy/TM controls. Do not infer Garhwali quality from the Hindi-tokenizer proxy or tune the already-scored FLORES test.
6. **TTS:** no model training in this cycle. Finish pair integrity and specify listener evaluation; no automatic proxy substitutes for native listening.

**Training stack:** existing Python runners; PyTorch and Transformers/PEFT for IndicBERT/mT0 where installed; NeMo for SraVaani where compatible; PyArrow for local Parquet. **requirements-asr.txt** and **requirements-model-audit.txt** describe relevant pinned packages. As of 2026-09-26, the optional `.cache/asr-runtime` path exposes PyTorch and Transformers but lacks NeMo, PyArrow, and common audio-reader libraries; SraVaani base weights are not cached. See [the updated local preflight](model-accuracy-preflight-2026-09-24.md) and the [issues and improvement plan](issues%26improvement%20plan.md).

**Exit gate:** a validation-selected candidate has a reproducible experiment card and does not materially regress its guardrail or important data slices. Failed candidates remain experimental.

### Phase 7 — Quantify uncertainty and diagnose failures

**Purpose:** prevent small samples and aggregate percentages from overstating progress.

**Work**
- Use paired bootstrap for paired translation/system comparisons with a fixed seed; use source-group or speaker-cluster bootstrap where examples share a work, question source, or speaker.
- Report confidence intervals and absolute paired deltas, not only two percentages. If uncertainty is broad or spans no practical difference, call the result inconclusive.
- For WER/CER, compute corpus rates from total errors divided by total reference units; also report per-record distributions and paired win/tie/loss counts.
- Slice errors by source, duration, script, code-switching, transcript length, and audio-quality markers where evidence exists. Label tiny slices descriptive.
- For generated text, inspect exact/near-copy, repetition, empty outputs, malformed script, and output-length distributions.
- For retrieval, inspect misses and whether the correct source passage exists in the fixed candidate set.
- Distinguish confidence calibration from correctness: ASR confidence or model agreement can route review, but neither is a probability that a Garhwali transcript is correct.
- Put rights, source quality, and exposure limitations next to each metric.

**Tools:** deterministic Python analysis, paired bootstrap/approximate randomization for paired tasks. Do not use LLM-as-judge as a primary Garhwali metric. An automated judge is only a diagnostic after comparison with human judgments, which are deferred.

**Exit gate:** every comparison has sample size, pairing method, uncertainty, exclusions, known limitations, and error analysis.

### Phase 8 — Assign result eligibility and benchmark labels

**Purpose:** make readiness visible without pretending all available sets are clean.

Use these labels:

- **Candidate:** schema/file checks pass; reference quality or independent exposure is not established.
- **Development-only:** usable for error analysis and selection under the documented protocol.
- **Historical-only:** previously scored or used for selection; retain scores but do not treat them as fresh confirmation.
- **Independent-evaluation eligible:** frozen, prior use audited, training/dev groups disjoint, reference basis documented, checkpoint exposure reasonably characterized.
- **Native-reviewed:** a qualified Garhwali speaker adjudicated the reference or task labels with review provenance. This status remains deferred; automated checks cannot assign it.

**Current assignments**
- Internal text and external task data remain candidates, with historical test use and checkpoint-contamination limits in the lineage report.
- XORQA test is historical-only: all 539 rows have saved predictions.
- FLORES test is historical-only: all 1,012 rows have saved predictions.
- VAANI test is historical-only for current SraVaani work; broad upstream exposure is known, example-level overlap unknown.
- Meta Omnilingual validation's 271 internally safe rows are development-only.
- Meta Omnilingual test's 292 internally safe rows remain unresolved until upstream exposure and prior use are addressed.
- No current task is approved for an independent final-accuracy claim.

**Exit gate:** every card and score table uses the right label; no result is called blind, final, or native-validated without meeting that definition.

### Phase 9 — Publish reports, benchmark cards, and reproducible artifacts

**Purpose:** make results useful to others while exposing the conditions that produced them.

**Work**
- Write a versioned card for each task and an index card for suite-wide limitations.
- Include intended use, source citations, license/terms, script/dialect coverage, collection/processing, split logic, prior test use, metric signatures, model-exposure uncertainty, known errors, and correction/removal process.
- Publish only artifacts whose redistribution status is verified. A source value can remain in the local corpus; a report can cite it and publish aggregate counts when copying it is not permitted.
- Keep full model checkpoints, raw audio, protected identifiers, caches, and restricted material out of ordinary Git.
- Publish model cards with base revision, fine-tune view hash, steps/seeds, decoding, checkpoint hash, task results, failures.
- Generate release files deterministically from frozen manifests and verify hashes after export.
- Add a changelog; never silently replace a benchmark version.

**Tools:** Markdown cards, JSON results, Git, repository CI, Hugging Face Dataset Cards when preparing a rights-reviewed publication. Paid Hub Jobs are not required.

**Exit gate:** each public score can be reproduced from versioned permitted artifacts and includes provenance, metric, split history, and exposure disclosures.

### Phase 10 — Maintain and extend the suite

**Purpose:** add cultural and linguistic coverage without breaking comparability.

**Work**
- Add vocabulary, morphology, grammar, place names, history, folklore, poetry, plays, songs, and oral-narrative tasks only when each has stable source IDs, clear task design, split grouping, and usable references.
- Keep retrieval/memorization from a source collection distinct from general language understanding.
- Add sources in a new benchmark version or document a compatible additive revision.
- Track source/genre/script/dialect coverage by evidence and counts, not invented completion percentages.
- Re-run integrity audits after each source or code change; compare hashes and scores across versions.
- If native review is later authorized, prepare small stratified batches with original context, alternatives, and correction provenance; until then retain the no-native-review status.

**Exit gate:** new material has a tested task schema and does not alter old scores without a benchmark-version change.

## 7. Model promotion and release criteria

A model is **selected on development data** when its frozen experiment beats the baseline on the declared primary dev metric and passes guardrails. That does not imply independent accuracy.

A task gets an **independent evaluation result** only if:

- Candidate and configuration are frozen before test inference.
- Evaluation rows/references and their source/split history are frozen.
- Exact and known family-level overlaps with training/development data are checked.
- Relevant pretraining/fine-tuning exposure is documented; unresolved exposure limits the claim.
- Test has not already been used to select the model.
- Metric code, normalization, tokenizer, and evaluation command are pinned.
- Confidence intervals, denominators, exclusions, and source strata are reported.
- Rights permit the proposed evaluation artifacts to be distributed.
- A native-review claim is made only after actual native review.

If every test reference is published openly, that is a valid open-benchmark choice. Scores must be called **open-test results** and may be vulnerable to training contamination; they are not blind results. A hidden/private reference set is an optional future design choice, not a requirement to hide corpus language material.

## 8. Recommended tools and where they fit

| Tool | Role | Decision |
| --- | --- | --- |
| Python 3, JSONL, hashlib, pathlib | Deterministic manifests, hashes, task runners, reports | Use now; matches the repository. |
| unittest and existing CI | Regression checks for splits, metrics, provenance, report rules | Use now; 519 tests currently pass. |
| Draft v0.2 contract validator | Validate counts, hashes, normalization, references, provenance, rights, splits, and local ASR hashes | Use now; `scripts/validate_benchmark_v02.py` passes against eight views. |
| Existing benchmark/lineage scripts | Build and audit current task files and prior-use ledger | Reuse; extend for a concrete missing check. |
| PyTorch, Transformers, PEFT | Local IndicBERT/mT0 inference and adaptation | Only after local preflight; the project `.venv` lacks these packages, while the optional cached runtime has PyTorch/Transformers but not PEFT. |
| NVIDIA NeMo | SraVaani decoding/training | Use only in a compatible environment. Decoder support varies by model architecture; the prior TSD configuration failed for this reason. |
| PyArrow and SoundFile | Read local Parquet/audio and build deterministic ASR examples | Only when installed; no download implied. |
| Current dependency-free WER/CER code | Garhwali scoring with NFC, casefold, punctuation/symbol removal, whitespace collapse | Keep normalizer pinned; JiWER can be a one-time implementation cross-check if installed, not an unannounced metric change. |
| SacreBLEU | Standardized BLEU/chrF with metric signature | Optional for new comparable runs. Do not relabel existing custom add-one-smoothed BLEU as SacreBLEU. |
| EleutherAI lm-evaluation-harness | Standard causal-LM tasks it supports | Optional reference; do not force it onto custom low-resource tasks or lineage-sensitive rows. |
| BEIR/MTEB methodology | Retrieval task separation and Recall/MRR/nDCG metrics | Use as design references; project data/source grouping remain authoritative. |
| LangChain/LangGraph | App orchestration and tool workflows | Not needed for scoring, split audits, training reproducibility, or metrics. Deterministic scripts are simpler and auditable. |
| Hugging Face Hub/Jobs | Model/dataset hosting and optional remote compute | No paid jobs in this roadmap. Hub publication is a later rights-reviewed release action. |
| LLM-as-judge | Possible exploratory triage | Not a primary metric; Garhwali judge capability and bias are not calibrated here. |

## 9. Immediate work order from this snapshot

1. **Complete — correct the status record.** The 61-trial, six-decoder, and expanded-human SraVaani outcomes are recorded; the fine-tunes completed and were not promoted.
2. **Complete — refresh integrity evidence.** The benchmark builder, final release audit, and lineage audit were rerun; hashes and test output are in the status report. Existing test results were not rescored.
3. **Complete — run the no-download local preflight.** The active project environment lacks model dependencies and SraVaani base weights. No packages, weights, data, or paid compute were obtained.
4. **In progress — close Phase 2 split/source-family gaps.** Exact-question/context usage labels are generated at `data/processed/evaluation/garhwali_bench/benchmark_usage_labels.jsonl`; all 62 affected records remain intact and are labeled for open diagnostics, not independent source-generalization claims. Four same-split near pairs have been inspected and recorded in the [adjudication report](benchmark-overlap-adjudication-2026-09-26.md). Next, complete source-family grouping and address semantic/cross-language uncertainty. No source row was removed.
5. **In progress — v0.2 schema/export.** The validator and deterministic adapter now cover eight views and 12,622 rows; the output manifest hash is recorded in [the export report](benchmark-v02-export-2026-09-26.md). The adapter links overlap labels and records draft metric signatures. Next, recover original text where provenance permits, freeze and implement metric/denominator policies, and finish Phase 2 grouping before freezing v0.2.
6. **Finish Phase 5 baseline consolidation** without rescoring historical tests. NLLB, dense-retrieval, and fresh SraVaani inference require local prerequisites that are currently missing.
7. **Continue validation-safe experiments** only after the relevant local checkpoint/runtime preflight passes. Pre-register each experiment and stop when split/runtime checks fail.
8. **Quantify uncertainty, publish task cards, and write the final research report** after baseline and lineage evidence reconcile. Keep independent-final and native-reviewed counts at zero until criteria are met.
9. **Prepare releases only after rights and split audits.** Public open-test scores must not be described as blind; dataset publication and model promotion are separate decisions.

## 10. Research basis

The plan follows primary research and official tool documentation:

- [Holistic Evaluation of Language Models (HELM)](https://arxiv.org/abs/2211.09110) motivates broad scenario coverage, multiple metrics, and transparent outputs rather than one headline score.
- [Data Contamination Can Cross Language Barriers](https://aclanthology.org/2024.emnlp-main.990/) shows translated benchmark data can contaminate multilingual evaluations while evading simple same-language overlap checks.
- [IndicGenBench](https://aclanthology.org/2024.acl-long.595/) provides task-design precedent for translation, cross-lingual summarization, and QA across Indic languages. Its [official repository](https://github.com/google-research-datasets/indic-gen-bench) includes canaries, but a canary does not prove every checkpoint excluded test material.
- [Statistical Significance Tests for Machine Translation Evaluation](https://aclanthology.org/W04-3250/) motivates paired bootstrap comparisons.
- [A Call for Clarity in Reporting BLEU Scores (SacreBLEU)](https://aclanthology.org/W18-6319/) supports reproducible BLEU reporting with a metric signature.
- [BEIR](https://arxiv.org/abs/2104.08663) and [MTEB](https://aclanthology.org/2023.eacl-main.148/) inform retrieval task separation and Recall/MRR/nDCG reporting.
- [Dialect Matters: Cross-Lingual ASR Transfer for Low-Resource Indic Language Varieties](https://aclanthology.org/2026.vardial-1.12/) is directly relevant: it includes a Garhwali case study and examines dialect transfer and pretraining-language bias.
- The [SraVaani-1.0 model card](https://huggingface.co/ARTPARK-IISc/SraVaani-1.0) and its [paper](https://arxiv.org/abs/2608.08235) are sources for broad VAANI training exposure. Neither gives example-level IDs needed to clear our VAANI test.
- [NVIDIA NeMo ASR documentation](https://docs.nvidia.com/nemo-framework/user-guide/25.07/nemotoolkit/asr/intro.html) documents decoding paths and language-model fusion. Support is architecture-specific; the project's failed TSD configuration remains recorded as failed.
- [PyTorch reproducibility guidance](https://docs.pytorch.org/docs/stable/notes/randomness.html) explains why seeds/deterministic settings must be recorded but do not promise bit-for-bit identity across devices/releases.
- [Hugging Face dataset-card guidance](https://huggingface.co/docs/hub/en/datasets-cards) provides a publication-card structure for provenance and limitations.
- [Data Statements for Natural Language Processing](https://aclanthology.org/Q18-1041/) and [Datasheets for Datasets](https://arxiv.org/abs/1803.09010) inform documentation of collection, composition, intended use, and limitations.
- [ITU-T P.800.1](https://www.itu.int/ITU-T/recommendations/rec.aspx?rec=12972) defines subjective speech-quality terminology. It is a reference for a future TTS listening study, not a score collected by this project.

This is a project-specific application of those methods, not a claim that adopting a framework or metric automatically makes an evaluation valid.
