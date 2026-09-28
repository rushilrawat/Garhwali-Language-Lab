# Garhwali Benchmark and Model Research Roadmap

**Status snapshot:** 2026-09-28
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

The project-wide measured scorecard is [benchmark-research-status-2026-09-25.md](benchmark-research-status-2026-09-25.md); this translation workstream has a [2026-09-26 dev-only refresh](translation-quality-2026-09-26.md), the ASR tasks have a [2026-09-26 baseline consolidation](asr-baseline-consolidation-2026-09-26.md), and the living issues are in the [issues and improvement plan](issues%26improvement%20plan.md). Current split and prediction lineage is in [model-accuracy-lineage-2026-09-28.md](model-accuracy-lineage-2026-09-28.md), with the full [task-result eligibility report](task-result-eligibility-2026-09-28.md); the 2026-09-24 lineage report is a historical snapshot.

| Area | Verified state | What the evidence supports |
| --- | --- | --- |
| Benchmark artifacts | Five candidate artifacts exist: FLORES, CrossSum, XORQA, internal text, internal ASR. Three external schemas pass validation across 3,847 records. | A machine-checkable candidate suite exists; it is not yet a fully independent or native-validated benchmark. |
| Internal text | 398 candidate rows; zero exact overlap against the 7,490-row recommended Garhwali training view. Character-bigram perplexity is 14.122106 on that candidate versus 17.000058 for the broad 106,915-row view, using the same deterministic scorer. | A controlled data/modeling floor, not neural-model accuracy or proof that all training rows are correct. |
| Language modeling | IndicBERTv2's 4,096-step continuation has mean validation cross-entropy 5.089108 across three seeds. | Validation loss only; tokenizer and model differences limit comparisons, and no independent final set is approved. |
| Translation | FLORES copy and translation-memory baselines cover 997 dev and 1,012 historical test rows. A shared scorer re-ran the saved 997-row dev translation-memory predictions and exactly reproduced the old report; a 2,000-resample paired record bootstrap compared them with source-copy. | Dev-only diagnostic: BLEU delta +0.01892665 (95% CI [0.01411908, 0.02385223]); chrF2 delta +0.23002697 ([0.22559907, 0.23435906]). The translation memory uses other dev targets, and intervals do not account for source-family clusters. It is not independent translation accuracy. The tiny NLLB Hindi-token proxy remains exploratory. |
| Retrieval | XORQA has 539 test questions with prior predictions; best saved IndicBERTv2 Recall@10 is 0.103896. The 500-query dev-only BM25 rerun gets 0.8% word and 1.0% character Recall@10; source-page-clustered 95% intervals are 0.2–1.6% and 0.2–2.0%, respectively. English-oracle BM25 gets 85.2% (clustered interval 82.1–88.3%). | A historical test baseline and clear Garhwali-to-English retrieval gap. Character-vs-word paired intervals touch zero; this dev result does not establish a reliable winner. Dense dev inference is blocked by missing local runtime/weights; the test is not fresh. |
| Generation | All three mT0 32,768-step seeds and validation diagnostics are saved. Seed 43 has the best validation cross-entropy (4.188287); the best adapter chrF2 is 0.074003 versus 0.088327 for zero-shot base. Existing run records report one selected-seed evaluation on an 86-row test. | No generation adapter is promoted. Test is historical, and 172 test-prediction rows do not map to current local manifests; references remain unreviewed. The earlier partial-run report is superseded by a later seed-43 retry. |
| ASR decoding | The six-configuration sweep completed. RNNT beam size 8 was selected on validation: WER 43.253%, CER 18.919%, versus greedy WER 43.454%, CER 18.948%. A post-hoc audit matches its saved 112 test predictions to the fixed audio/reference manifest; test WER/CER are 42.761%/17.410%. | Historical paired comparison to base: WER delta +0.000 pp (95% speaker-cluster interval −0.583 to +0.656); CER −0.196 pp (−0.391 to +0.000). No reliable difference. Upstream VAANI example overlap is unknown. |
| ASR fine-tuning: 61 trials | All 61 trials completed. Validation WER/CER improved from 43.454%/18.948% to 42.711%/18.660%. Post-hoc audit matches all 112 test audio hashes and cleaned references; test WER/CER are 43.528%/17.494%. | Historical paired deltas vs base: WER +0.767 pp (95% interval −0.107 to +1.591); CER −0.112 pp (−0.683 to +0.384). Both include zero; no promotion. This work was not stopped by a rate limit. |
| ASR fine-tuning: expanded human transcripts | Training used 5,513 hash-filtered human-transcript clips (8.112 hours); 3,886 rows lacked complete speaker identity. Validation WER/CER are 42.209%/18.302%. Post-hoc audit matches all 112 test audio hashes and cleaned references; test WER/CER are 43.289%/17.396%. | Historical paired deltas vs base: WER +0.527 pp (95% interval −0.710 to +1.518); CER −0.210 pp (−0.949 to +0.366). Both include zero; no promotion. Training speaker metadata is incomplete and upstream exposure unresolved. |
| ASR references and independence | VAANI validation/test predictions already exist. SraVaani's model card identifies VAANI as an upstream source and reports 31,255 hours of VAANI pretraining plus about 31,270 hours of labeled fine-tuning from VAANI and other open speech data; it does not expose example-level overlap. | VAANI results are development/historical evidence, not independent estimates of generalization. Do not rescore test to choose a model. |
| TTS | Speech manifests and readiness checks exist; no TTS system has a valid Garhwali quality result. | Readiness and pair-integrity only. MOS or naturalness needs listeners and cannot be inferred from automated checks. |
| Independent final accuracy | Zero of five task areas are approved for independent final-accuracy claims: language modeling, translation, retrieval, generation, and ASR. | There is no defensible single project-wide model-accuracy score today. |
| Review and tests | Native adjudications remain deferred. Latest pytest run: 584/584 passed; documented unittest runner: 582/582 passed. | Run `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`; passing checks do not certify language labels. |

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
- Group all segments from the same parent document before reassigning duplicate components; recheck parent hashes after assignment.
- Group questions, paraphrases, translations, and summaries tied to one source passage or cultural work before splitting.
- Preserve the XORQA train/dev repeat and expose it as a named warning.
- Treat previously scored public test rows as historical/development-only.
- Keep VAANI as development evidence for SraVaani. Zero local audio-hash overlap proves only that the local split hashes differ; it cannot reveal upstream SraVaani training examples.
- Keep Meta Omnilingual internally safe test rows unresolved until model-pretraining exposure is documented. Internal split flags do not settle checkpoint exposure.
- Do not treat a benchmark canary string or a negative exact-text match as proof that a checkpoint never saw translated or paraphrased test content.

**Tools:** existing hash-lineage scripts; Python Unicode normalization and SHA-256; MinHash/character n-gram candidate generation only if needed; reviewable pair reports. Add dependencies only for a demonstrated performance need.

**Exit gate:** candidate rows have duplicate-family IDs, split manifests are content-addressed, source-split errors are itemized, and every exposure claim is evidenced or explicitly unknown.

**Status (2026-09-26):** the review-only scan covers 12,510 text rows. Exact verification confirmed 27 XORQA source-context groups across original splits and one exact train/dev question repeat; a local overlay labels 62 affected records as open-diagnostic-only for source-independent claims while retaining all rows. The four near-text pairs were inspected: three are variants inside existing recommended-train duplicate components, and one is a same-context/same-answer pair within XORQA dev. No near pair crosses splits. The raw candidate scan remains available, while the adjudication and usage-label record supplies the reviewed interpretation. Semantic and cross-language matching remain outside the scan, so Phase 2 is still open. Independent final-test approval remains zero of five areas.

**Refresh (2026-09-27):** rerunning the configured overlap scan over the same
12,510 inputs reproduces its JSON SHA-256
`abbf44d81c4afd092afce845043dddc16230780f5157eabe5f4f26ccbf3b1d1b` and the
same key counts: 407 exact-text groups (one crosses source splits), 616
source-family groups (27 cross source splits), and four same-language
near-text candidates (none cross splits). All 27 cross-split source families
are exact source-content groups matching the reviewed XORQA context families.
The scan reports zero groups with multiple top-level record-language labels;
this does **not** clear cross-language contamination because nested aligned
fields are not semantically compared. Semantic/paraphrase and cross-language
matching therefore remain open, and no rows were removed.

**Nested-field refresh (2026-09-27):** the new exact scan covers 10,571 fields
from FLORES, CrossSum, and XORQA against the 7,490-row recommended training
view. It found 41 same-field groups across source splits: 27 contexts, 6
English answer spans, 5 English oracle questions, 2 Garhwali translated-answer
spans, and 1 Garhwali question. It found zero cross-field groups and zero long
same-label cross-field groups or long exact matches to recommended training;
15 brief answer-span matches remain
separate common-answer candidates. A 2026-09-28 label-agnostic exact scan found
50 strings shared by the XORQA English-answer and Garhwali translated-answer
fields; 10 occur across splits, all at 2–6 normalized characters. These remain
common-answer candidates and were not added to the overlay. See the
[cross-language exact-overlap review](benchmark-cross-language-exact-overlap-2026-09-28.md).
The rebuilt overlay labels 67 unique XORQA
records for open diagnostics only: 27 context groups, one exact top-level
question group, and five oracle-question groups. Repeated answer spans were not
automatically labeled as leakage. All rows remain present. The audit details
and hashes are in [the nested-overlap review](benchmark-nested-overlap-review-2026-09-27.md).

**Source-page refresh (2026-09-28):** parsing the exact page-title segment in
all 1,139 XORQA title locators produced 993 page families; 54 families (134
records) cross source splits, and 32 contain different exact context passages.
The local-only overlay now labels 138 unique rows for open diagnostics while
retaining every record and split. The rebuilt eight-view/12,622-row v0.2 draft
hash-links the page family on XORQA records. This closes exact page-title
grouping for XORQA; related pages, paraphrases, translation equivalence, and
source lineage in other tasks remain open. See the
[source-page family review](benchmark-source-page-families-2026-09-28.md).

**Parent-safe split refresh (2026-09-28):** the historical text manifests
contain 114,064 segments from 28,754 parent documents. A parent-hash audit
found 50 documents (1,523 segment rows) crossing train/test or
train/validation, although exact segment hashes did not cross. The builder now
groups parent segments before normalized and supported-semantic reassignment,
rejects any remaining parent crossing, and records source input hashes. Its
separate local candidate has zero parent-document crossings; 1,624 segment
assignments moved to keep linked components together. CrossSum's 699 exact
source and target URLs do not repeat across splits. FLORES provides only one
dataset-level `source_id` and no row-level source URLs, so a finer source-family
check cannot be done from current fields. Semantic/paraphrase analysis and
candidate promotion remain open; historical splits and scores are unchanged.
The split was also fed into a separate ignored GarhwaliBench candidate: 392
internal text rows exactly match the corrected recommended test view, alongside
112 ASR rows and 3,847 external records. Its built-in character-bigram
diagnostic on already-used test rows is historical/open only and was not used
for model selection; no neural inference ran. The candidate manifest hash and
row-level evidence are in the
[parent-safe split audit](benchmark-parent-safe-split-audit-2026-09-28.md).

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
Still open are raw-text recovery where provenance permits, complete task-field
and translation-metric integration, source-group and cross-language review
from Phase 2, and a public/local field card. Details:
[the adapter report](benchmark-v02-export-2026-09-26.md).

**Overlay refresh (2026-09-27):** the exact nested oracle-question groups are
now verified against the benchmark input and included in the review-only
overlay. The adapter validates their hashes and was rebuilt with all **12,622
rows** retained; its current manifest SHA-256 is
`2ca84a51cf916d336d7a4e92c5fb34f313b19c72900b7b47f6fa79728e82e25e`. The
validator passes all eight assets with zero errors. The refreshed overlay
contains 67 unique records and has SHA-256
`e6bc3dc9d01e3efb52fcb7d303be4ff5247b532f7f50286255b44df03a779ae2`. The
export is still a draft and remains ignored/local-only.

**Metric update (2026-09-27):** dependency-free, versioned QA exact-match and
token-F1, summary ROUGE-L/chrF2, and custom translation BLEU/chrF2 now have
scoring paths. CrossSum maps to its target summary, XORQA to target-language
`translated_answers`, and Garhwali-to-English FLORES to `source_example.target`.
The scorer verifies complete prediction-ID coverage and writes the shared run
manifest. A preflight found 100/100 CrossSum dev references and 499/500 XORQA
dev references; the missing target answer remains in output but is excluded
from the score denominator. Re-scoring existing translation-memory predictions
reproduced all 997-row dev baseline metrics exactly. No fresh neural-model
scores were generated. The v0.2 package remains a local draft because semantic
overlap, source-group uncertainty, raw-text recovery, and release/rights gates
remain open.

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
This 2026-09-26 runner slice passed 519 tests. Before the mT0 manifest tests,
the 2026-09-27 full-suite run collected 554 tests: 551 passed and three graph
tests could not import the project-pinned LangGraph package because it was
absent from this environment. The previous full-suite run collected 557 tests:
554 passed and the same three LangGraph imports remained unavailable locally.
The previous system-interpreter pytest run collected 558 tests: 555 passed and
three LangGraph imports failed because that interpreter did not see the project
`.venv`. At the 2026-09-28 source-page-cluster checkpoint, pytest passed
569/569 and the documented unittest runner passed 567/567. The latest
verification counts are in the current status table above.
Compilation and `git diff --check` were rerun for the new metric implementation.

**Scoring-runner update (2026-09-27):**
[`scripts/score_benchmark_predictions.py`](../scripts/score_benchmark_predictions.py)
scores existing FLORES translation, CrossSum summary, and XORQA answer
predictions on development by default. It requires exact prediction-ID
coverage, labels historical test results, and writes the same hash-linked
prediction/report/manifest artifacts. Translation uses the existing custom
BLEU/chrF implementation, not SacreBLEU; CrossSum uses ROUGE-L and custom
chrF2; XORQA uses exact-match and token F1. Rows with missing target-language
references remain in output but are excluded from metric denominators.

**Retrieval integration (2026-09-27):** `run_retrieval_baseline.py` now writes
the shared manifest for a dev-only BM25 run. Its fresh 500-query dev run
reconciles ordered query IDs and output hashes. Word and character Recall@10
are 0.8%/1.0%; English-oracle Recall@10 is 85.2%. The same-language retrieval
gap remains a data/model limitation. The IndicBERT retrieval runner does not
yet write this manifest, and its pinned local weights/runtime remain
unavailable. NLLB inference is also blocked by its absent pinned checkpoint.

**ASR post-hoc scoring integration (2026-09-27):**
[`analyze_saved_asr_validation.py`](../scripts/analyze_saved_asr_validation.py)
now writes the shared manifest for a paired comparison of saved SraVaani 1.0
and Garhwali Whisper v0.2 predictions on the fixed 269-row validation set.
Results reproduce the previous report exactly: SraVaani 43.3936% WER /
18.9252% CER; Whisper v0.2 78.0522% / 46.2980%. The manifest links all
validation IDs, source prediction hashes, model revisions where available,
scorer/code hashes, and outputs. It does not parse or score held-out prediction
rows and performs no new model inference. See the
[ASR run-manifest report](asr-validation-run-manifest-2026-09-27.md). This does
not resolve upstream VAANI exposure or establish independent accuracy.

**Generation post-hoc manifest integration (2026-09-27):**
[`manifest_saved_generation_validation.py`](../scripts/manifest_saved_generation_validation.py)
joins the three saved mT0 systems to the frozen 130-row validation selection
using instruction hashes and verifies every task/reference. All three systems
share selected-ID hash
`8e6d9667f80d659eedb518b58be721340161c159c5587243f9ba0616cd7cea44`, which
matches the selected validation digest recorded in the seed-43 training report.
No inference or test scoring ran. Recomputed primary-reference diagnostics
match the saved report; current unreviewed alternate references shift chrF2 by
0.0019–0.0025 across seeds. This is reference sensitivity, not evidence of
better model quality. The output manifests are local-only; original sampling
parameters and per-seed adapter hashes are unavailable. Details are in the
[mT0 manifest report](mt0-validation-run-manifest-2026-09-27.md).

Fresh ASR inference/training, IndicBERT retrieval, masked-LM, runtime locks,
and representative local model reruns remain before Phase 4 is complete. The
saved mT0 outputs now have post-hoc manifests, but no fresh generation scoring
runner or per-seed checkpoint hashes are available.

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
numerically higher than the base report, but they were not promoted. A later
post-hoc audit matched all five saved test prediction sets by audio hash and
cleaned reference, then computed 10,000-replicate speaker-clustered paired
intervals. Every WER/CER interval includes zero or touches it, so the historical
test does not support a reliable candidate improvement. The legacy 269-row
SraVaani comparator is now traced to its saved prediction input and reproduces
2,161/3,282 errors; the sweep's greedy aggregate is 2,164/3,286, but its
per-row greedy output/configuration is unavailable. This small discrepancy
remains open under BMR-009 in
the [issues and improvement plan](issues%26improvement%20plan.md). No test
audio was loaded and no model inference ran. The audit is documented in
[ASR held-out lineage](asr-heldout-lineage-audit-2026-09-28.md). This completes
the saved-artifact lineage comparison, not Phase 5 overall.

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

**Started (2026-09-27):** `scripts/analyze_translation_uncertainty.py` performs
a deterministic paired record bootstrap over saved development predictions.
It precomputes per-record n-gram counts, samples the same row indices for both
systems, reports intervals for custom corpus BLEU/chrF2 and exact match, and
writes per-row outcomes plus the shared hash-linked manifest. On 997 FLORES dev
rows, copy-vs-translation-memory deltas are BLEU +0.01892665 (95% CI
[0.01411908, 0.02385223]) and chrF2 +0.23002697 ([0.22559907, 0.23435906]);
exact-match delta is 0. The output is local-only at
`data/processed/evaluation/benchmark_scoring/translation_dev_uncertainty/`.
The interval resamples records, not source families; it is a development
retrieval diagnostic and does not establish independent or native-validated
accuracy. Source-group bootstrap remains open.

**Completed (2026-09-28):** `scripts/analyze_retrieval_cluster_uncertainty.py`
resamples whole XORQA Wikipedia source-page families for the saved BM25 dev
predictions. It verified all 500 prediction IDs against the dev split, checked
the benchmark SHA against the parent retrieval report, and reproduced every
saved point metric before writing hash-linked outputs. The 500 queries map to
461 source pages; 34 pages have multiple queries (73 rows). Character-minus-
word BM25 paired intervals touch zero, so the small point-score difference is
inconclusive. See
[the clustered retrieval analysis](retrieval-source-page-cluster-uncertainty-2026-09-28.md).
This does not make the retrieval result page-held-out: the fixed 1,059-document
candidate corpus contains documents from all original splits. Translation
still has only record-level bootstrap intervals, and source-clustered
uncertainty for other tasks remains open where usable lineage exists.

**Completed (2026-09-28):** `scripts/analyze_retrieval_misses.py` reconciles
all 500 saved dev predictions to the fixed corpus and verifies that every
gold passage is present. It validates each reported rank and score against
the ordered top-10 candidate list and reproduces the saved Recall@1/5/10 and
MRR@10 metrics. The corpus has 1,059 unique passages from 1,139
source rows; 479 unique dev gold contexts are available, with 39 duplicated
across source rows and 24 represented in multiple splits. Garhwali word and
character BM25 have 496 and 493 zero-score misses, respectively; character
BM25 has two more gold passages ranked below 10. English-oracle BM25 has 74
misses at 10. These are saved-dev diagnostics on an all-split candidate corpus,
not a page-held-out evaluation or semantic-support assessment. See the
[retrieval miss report](retrieval-miss-analysis-2026-09-28.md) and the
reproduction command in [`scripts/README.md`](../scripts/README.md). This
completes the planned fixed-corpus availability and rank diagnosis for this
retrieval run.

**Completed (2026-09-28):** `scripts/analyze_generation_output_diagnostics.py`
reconciles the three manifested mT0 validation outputs to the full validation
input, original synced predictions/report, and per-seed output hashes. It
summarizes 390 saved predictions (130 shared IDs per seed) by task for output
length, repeated-token/character runs, exact normalized-output modes, selected
Unicode anomalies, and descriptive script profiles. It found no empty outputs,
instruction copies, model control tokens, replacement/surrogate characters,
unexpected controls, or selected invisible/bidirectional controls. The
Garhwali-to-English lexicon slice shows a repeated-answer concentration: the
largest mode is 9/29, 13/29, and 23/29 for seeds 17, 29, and 43. This is a
mode-collapse candidate, not a correctness label; duplicate inputs and valid
synonyms can also repeat. Outputs remain unmodified, the report contains no
generated text, and no inference or held-out scoring ran. See the
[generation-output diagnostic](generation-output-diagnostics-2026-09-28.md).
Source-group uncertainty for translation and other tasks remains open where
verified group lineage exists.

### Phase 8 — Assign result eligibility and benchmark labels

**Purpose:** make readiness visible without pretending all available sets are clean.

Use these labels:

- **Candidate:** schema/file checks pass; reference quality or independent exposure is not established.
- **Development-only:** usable for error analysis and selection under the documented protocol.
- **Historical-only:** previously scored or used for selection; retain scores but do not treat them as fresh confirmation.
- **Unresolved:** local prior-use evidence may be absent, but checkpoint exposure or result-row identity is too uncertain for an independent claim.
- **Independent-evaluation eligible:** frozen, prior use audited, training/dev groups disjoint, reference basis documented, checkpoint exposure reasonably characterized.
- **Native-reviewed:** a qualified Garhwali speaker adjudicated the reference or task labels with review provenance. This status remains deferred; automated checks cannot assign it.

**Current assignments**
- The configured split decisions and saved test artifacts were reconciled on 2026-09-28; see the [eligibility report](task-result-eligibility-2026-09-28.md) and [fresh lineage audit](model-accuracy-lineage-2026-09-28.md).
- FLORES test (1,012 rows), XORQA test (539), VAANI ASR test (112), and instructions test (260; 134 exact saved-prediction matches) are historical-only.
- The 398-row internal text test is historical-only because the exact rows were scored by the aggregate character-bigram baseline, despite having no row-level prediction artifact.
- CrossSum test (500) and Meta Omnilingual test (292 internally safe of 300) remain unresolved because checkpoint exposure is unknown; eight Meta rows are excluded from that evaluation view by internal safety flags but remain preserved.
- CrossSum's 100-row dev references are available for development, but no saved prediction is reconciled to that split. FLORES/XORQA development results and VAANI/Meta/instruction validation results are development-only. The complete counts and prior-use evidence are in the eligibility report.
- No task result is independent-final eligible; native-reviewed count remains zero at the owner's direction.

**Status (2026-09-28):** configured split/result labels reconciled and covered by regression tests. Phase 9 task cards and the final research report remain. No result is called blind, final, or native-validated without meeting that definition.

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
| unittest and existing CI | Regression checks for splits, metrics, provenance, report rules | Use now; latest run: pytest 584/584, documented unittest 582/582. |
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
4. **In progress — close Phase 2 split/source-family gaps.** Exact nested-field, cross-language-label exact-string, and XORQA page-title scans are complete for configured fields. The historical text split had 50 parent-document crossings (1,523 rows); the corrected local candidate has zero and is input-hash linked. CrossSum exact source/target URLs do not repeat across splits; FLORES lacks row-level source URLs. The XORQA source-page audit found 54 page families (134 rows) crossing splits; 32 have distinct context passages. The current retained-row overlay at `data/processed/evaluation/garhwali_bench/benchmark_usage_labels.jsonl` flags 138 records for open diagnostics. Four same-split near pairs are documented in the [adjudication report](benchmark-overlap-adjudication-2026-09-26.md), with details in the [nested-overlap review](benchmark-nested-overlap-review-2026-09-27.md), [source-page review](benchmark-source-page-families-2026-09-28.md), and [parent-safe split audit](benchmark-parent-safe-split-audit-2026-09-28.md). Remaining work is semantic/paraphrase and cross-language analysis, better source metadata where missing, and candidate evaluation-eligibility review; exact strings cannot clear those risks. No source row was removed.
5. **In progress — v0.2 schema/export.** The validator and deterministic adapter cover eight views and 12,622 rows; the refreshed draft manifest SHA-256 is `2ca84a51cf916d336d7a4e92c5fb34f313b19c72900b7b47f6fa79728e82e25e`. QA, summary, translation, BM25 retrieval, post-hoc ASR, and saved mT0 validation predictions have hash-linked manifests. The XORQA adapter now carries exact source-page family hashes and the expanded 138-row usage overlay. Next, extend manifests/preflight to fresh ASR runs and IndicBERT retrieval/masked-LM; recover original text only where provenance verifies it; finish semantic/cross-language review and source-cluster uncertainty for translation and other tasks (the XORQA retrieval cluster interval is now complete); then freeze v0.2. The mT0 selected-ID hash matches its training report, but original sample parameters and per-seed adapter hashes are not recorded.
6. **Finish Phase 5 baseline consolidation** without rescoring historical tests. NLLB, dense-retrieval, and fresh SraVaani inference require local prerequisites that are currently missing.
7. **Continue validation-safe experiments** only after the relevant local checkpoint/runtime preflight passes. Pre-register each experiment and stop when split/runtime checks fail.
8. **Complete — reconcile configured result eligibility.** Saved test matches now force historical-only labels; the internal text candidate is historical due to an aggregate score on the exact fixed test rows. CrossSum and Meta Omnilingual test exposure remains unresolved. Continue source-family uncertainty analysis where needed, then publish task cards and write the final research report. Keep independent-final and native-reviewed counts at zero until criteria are met. See [the eligibility report](task-result-eligibility-2026-09-28.md).
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
