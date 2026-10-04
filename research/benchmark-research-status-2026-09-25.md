# Benchmark and research suite: measured status

**Original scorecard:** 2026-09-25; dated evidence below includes historical refreshes through 2026-09-28.
**Benchmark evidence refresh:** 2026-10-01. The public corpus has since
advanced to v0.2.3 (2 October); speech remains at v0.2.1. The benchmark
measurements below remain the 1 October snapshot and were not changed by the
4 October Archive intake. Benchmark v0.2 remains local-only. The adapter validates eight views /
**14,703 view rows** (3,847 external, 402 internal text, 112 ASR, and
recommended text split 9,486/454/402), with zero structural errors. The 402
internal-text rows intentionally mirror recommended test rows. The
character-bigram perplexity of 14.397995 is matched to exact historical/open
test rows. Six local draft task cards remain local. The shared scorer now
includes ASR corpus/per-record WER/CER and generation EM/chrF2. The generation
follow-up reconciles three saved seeds to 130 of the current 320 validation
rows; 190 have no saved prediction, and no fresh inference was run. All 14,703
benchmark rows remain upload-blocked; 2,077 recommended-text rows have
compatible recorded source assessments, 8,265 have item-level rights status
unrecorded, and component rights remain unresolved. Semantic/paraphrase and
upstream model exposure are also unresolved. The owner approved work toward
independent evidence across all five task areas; **eligibility remains 0/5**.
Latest full tests: 656/656 unittest; v0.2.0 release-time counts (607/605) are
historical. See the [roadmap](benchmark-model-roadmap.md),
[rights inventory](garhwali-bench-v0.2-rights-inventory-2026-09-29.md),
[ASR integration check](asr-corpus-metric-integration-2026-09-29.md),
[generation scorer report](generation-scoring-integration-2026-09-30.md), and
[issue log](issues%26improvement%20plan.md).
**Checked:** 2026-09-30 current counts and lineage; older model-score tables remain historical snapshots.
**Priority:** GarhwaliBench integrity, then controlled model research  
**Execution:** local only; no Hugging Face jobs or paid compute

### Current evidence — refreshed 2026-09-30

| Check | Current result | Meaning/limit |
| --- | --- | --- |
| v0.2 adapter and structural validation | 8 views / 14,703 rows; 0 errors; adapter manifest SHA-256 `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`; validator JSON SHA-256 `170476050d38da75b4a21f55d50bd3fdfc76f0fd4f4d954be1dd0cef26a02583` | Sum of views, not unique records; includes 402 intentional internal-text/recommended-test mirrors. Draft remains local-only and `public_upload_allowed=false`. |
| Recommended text split | 9,486 train / 454 validation / 402 test; all 10,342 IDs map to source segments covering 3,246 parent-text hashes and 3,072 duplicate components | Zero parent-hash/component split crossings. Nine of 11 broad ingestion-file pointers span splits, but these files cover multiple works and are not document identities. Compared with the earlier 8,265-row candidate: +2,077, all prior IDs retained, none removed or moved across splits. |
| Exact/near overlap refresh | 14,591 text-relevant rows; 411 exact groups; 1 group crosses source splits; 402 expected cross-view mirrors; 4 near-text candidates, all same-split. The 2026-09-30 lineage audit additionally finds 15 recommended-train exact text matches in instruction test and 29 in validation. | The single within-source split crossing is the known XORQA train/dev repeat. Cross-view matches are retained and flagged; no semantic/paraphrase clearance is implied. |
| Speech/model cross-split overlap | Meta Omnilingual has 4 train/test audio and 4 train/test transcript-text groups, plus 27 train/validation text groups. Expanded-human ASR train overlaps experimental test in 338 audio / 575 transcript-text groups, and validation in 397 audio / 683 text groups. | These are direct split conflicts for models trained on those views; affected records remain in the corpus. Full row IDs remain in the ignored speaker-safe lineage ledger. |
| Source-family scan | 1,995 groups; 29 cross-split families (27 content-linked XORQA plus two broad URL candidates) | Broad collection/book URLs are not proof that all grouped records are duplicates. |
| Nested fields and XORQA page families | 10,571 fields; 41 same-field cross-split groups; 0 cross-field groups and 0 long exact training overlaps; 50 short cross-language-label groups (10 across splits). 993 page families; 54 cross-split / 134 rows; 32 with multiple contexts; 0 unparsed titles. | Exact short-answer or source-page reuse is a review signal, not automatic leakage. All source rows remain. |
| XORQA page overlay | 138 retained records labeled open-diagnostic; overlay SHA-256 `deb49ebee8dc9b41de9ec0c87116b8934c14d2796dbb633aa4714b6f254def22` | Labels document split/source-page overlap; records remain present. |
| Current text-test score lineage | Exact 402-row match; character-bigram PPL 14.397995; row-set SHA-256 `d1ed8310f891926ba91e24f79367554dc4e22aeeeb56ad26be01e15c8246d06a` | Aggregate baseline evidence now recorded separately from row-level predictions; test is historical/open, not independent-final. |
| Release/accuracy gate | 0/5 task areas independent-final; benchmark card pack is local-only | Component rights, semantic exposure, and metric/reproducibility freeze still block benchmark publication and independent claims. |

## Four requested improvement tracks — active status, 2026-09-29

| Track | Work completed or verified in this pass | What still blocks the claimed outcome |
| --- | --- | --- |
| Better neural model scores | Rechecked local runtimes and model artifacts. The project `.venv` has no PyTorch, Transformers, NeMo, PEFT, PyArrow, SentenceTransformers, or Datasets. Fine-tuned SraVaani `.nemo` checkpoints and adapters exist, but required base assets/runtime are not usable in this environment. Existing outputs and sweeps remain preserved. | No fresh NLLB, dense retrieval, or SraVaani inference was run. All available test scores are historical or exposure-unknown. A fresh run needs compatible weights/runtime and a verified, explicitly capped compute budget; this refresh incurred $0. |
| Independent accuracy | Owner approved work in all five task areas; evidence eligibility remains 0/5. Existing public tests have saved predictions or unknown upstream model exposure. | A new, sealed post-freeze evaluation set must be newly authored/recorded, source-grouped, rights-cleared, and kept out of model selection/training. Existing public data cannot be relabeled as blind. |
| Public benchmark release | Revalidated 8 views / 14,703 view rows with zero structural errors. Shared scoring covers ASR corpus/per-record WER/CER and saved generation validation predictions with exact ID coverage and metric/code hashes. | All 14,703 draft view rows currently say `public_release_cleared=false`, and the manifest remains `public_upload_allowed=false`. Full component/field-level rights review remains open. See the [rights inventory](garhwali-bench-v0.2-rights-inventory-2026-09-29.md). |
| Native-validated claims | Regenerated two-reviewer packets and templates. Transcript reviewers now have a blind first-pass CSV that omits references and model hypotheses; current packets include 176 priority text rows and 113 transcript rows. | Zero decisions/adjudications exist. Two independent Garhwali reviewers must complete the queue; automated checks and model agreement cannot establish linguistic correctness. No dialect claim is being made. |

### Source terms checked for benchmark payloads

The current draft contains mixed upstream material, so one umbrella license is
not a safe description of the whole benchmark. The official Google HF cards
declare **CC BY-SA 4.0** for IndicGenBench FLORES and **CC BY-NC-SA 4.0** for
CrossSum; CrossSum examples include English article text and source URLs. The
XORQA card declares **MIT**, while the original XORQA project and its upstream
data lineage still require a component-by-component compatibility review. The
VAANI card declares **CC BY 4.0** and requires gated access acceptance; the
local ASR manifest additionally contains speaker IDs and local audio/image
locators that are not public-card fields. These declarations are evidence to
retain, not a blanket clearance of the adapted v0.2 package. See the [FLORES
card](https://huggingface.co/datasets/google/IndicGenBench_flores_in),
[CrossSum card](https://huggingface.co/datasets/google/IndicGenBench_crosssum_in),
[XORQA card](https://huggingface.co/datasets/google/IndicGenBench_xorqa_in),
[original XORQA repository](https://github.com/AkariAsai/XORQA), and
[VAANI card](https://huggingface.co/datasets/ARTPARK-IISc/Vaani).

The ASR metric implementation is in
[`scripts/asr_metrics.py`](../scripts/asr_metrics.py), with synthetic edge-case
coverage in [`tests/test_asr_metrics.py`](../tests/test_asr_metrics.py). The
native-review workflow and current zero-decision status are detailed in
[`native-reference-review-readiness-2026-09-15.md`](native-reference-review-readiness-2026-09-15.md).
The task-by-task data collection and exposure protocol is
[`independent-evaluation-protocol-2026-09-29.md`](independent-evaluation-protocol-2026-09-29.md);
it is a protocol, not evidence that new items or reviews already exist.

The six local draft cards are in
[`garhwali-bench-v0.2-draft-cards.md`](garhwali-bench-v0.2-draft-cards.md).
No source values, audio, speaker IDs, or test payloads were copied into that
document. Older metric tables below retain their original measured snapshots;
do not compare scores across different input manifests as if they were one
current evaluation.

## What “done” means here

There is no defensible single completion percentage for this work. A candidate
benchmark can be built and pass file checks without being an independent,
accurate measure of Garhwali. The counts below separate those gates.

| Gate | Measured result | Status |
| --- | ---: | --- |
| Candidate benchmark artifacts | 5 of 5 present: FLORES, CrossSum, XORQA, internal text, internal ASR | Built |
| External task schemas | 3 of 3 valid; 0 schema errors across 3,847 records | Pass |
| Historical internal text candidate | 398 rows; 0 exact-segment matches against its 7,490-row recommended training view; later parent-hash audit found 50 parent documents / 1,523 segments across train/test or train/validation | Historical; exact-segment pass was incomplete |
| Parent-safe text split candidate | 114,064 rows; 0 parent-document, exact-segment, normalized-text, or supported-semantic crossings | Pass for local split structure; not promoted; its built-in text diagnostic uses already-scored open-test rows |
| Parent-safe benchmark candidate | 392 text rows, 112 ASR rows, and 3,847 external task records; internal text IDs/text match the corrected recommended test view | Historical/open diagnostic only; no independent-accuracy claim |
| Internal ASR candidate | 112 rows; 0 audio-hash or identified-speaker overlaps against ASR train/validation | Pass for automated split integrity |
| External source-split repeats | 1 exact primary-text group / 2 rows in XORQA `train` and `dev`; neither row is in `test` | Flagged; rows preserved |
| Independent final accuracy sets | 0 of 5 currently eligible: language modeling, translation, retrieval, generation, and ASR. Owner approved work across all five on 2026-09-30. | Not established |
| Native-language validation | 0 adjudications | Deferred at the owner's direction |
| Automated project tests | Current v0.2.1 working tree: 682/682 tests; frozen v0.2.0 release snapshot: 607/607 pytest and 605/605 unittest; 2026-09-28 snapshot: 584/584 and 582/582 | Current full suite passes; counts verify code/contracts, not language correctness or rights |

“Pass” above means only that the automated, checksum-addressed files satisfy the
listed checks. It does not certify spelling, meaning, dialect, or reference
quality. Existing test results have prior evaluation history, and external
checkpoint training exposure is unknown. No current score is a blind final
accuracy claim.

## Benchmark change made in this pass

The previous `build_garhwali_benchmark.py` default trained its character model
on the broad **106,915-row** text split even though the corrected modeling path
uses the **7,490-row** recommended Garhwali view. The baseline and its leakage
count therefore did not describe the strict training view used by current
experiments.

The builder now uses `text_recommended/train.jsonl`, records that manifest's row
count and SHA-256, and reports exact text repeats between official source splits.
The independent final audit recomputes those values and rejects a broad training
view. It leaves duplicate source rows intact and warns about the XORQA
train/dev repeat instead of silently deleting it.

Both baselines below use the same scorer, the same 398-row candidate, and the
same held-out text manifest (`dac10e0b1b5d0a1af0884008bfe734912042b707238ffabeeb35cc1af96e46c7`):

| Training view | Rows | Training manifest SHA-256 | Character-bigram cross-entropy | Perplexity | OOV rate |
| --- | ---: | --- | ---: | ---: | ---: |
| Broad | 106,915 | `4a1ec922599ba2d60e4bfddb0eb4a0e8572aa99fd43fa49d82dc855b45612bba` | 2.833217 | 17.000058 | 0.0 |
| Recommended Garhwali | 7,490 | `2de3f3f95f24d41df9a4ce142496b7e9e97ac402ff4cca4c00edb6bed41d6ec8` | **2.647741** | **14.122106** | 0.0 |

This is a deterministic character-model signal on an automated candidate, not a
neural-model accuracy claim or proof that every training row is correct. The
recommended view improves this controlled floor while using about one
fourteenth as many rows. The benchmark rebuild also found zero exact match
between the 3,847 external primary-text fields and the recommended train view.

The 2026-09-26 integrity refresh below reran the benchmark builder, final
release audit, model-lineage audit, local runtime preflight, and full test suite.
The XORQA train/dev repeat remains present and explicitly reported; no source
rows were removed.

## Fresh integrity and local runtime refresh (2026-09-26)

The benchmark rebuilt successfully from the current workspace. Its manifest
SHA-256 is `ce93c7c1c06680d04bf9b861cbfdf8ca11b6cf9bf1968ba9cf19687655b8865b`.
It still contains 3,847 external task rows, 398 internal text candidates, 112
internal ASR candidates, and the 7,490-row recommended text training view.
External primary text has zero exact matches against that training view; one
exact text group spanning XORQA train and dev (two source rows) remains flagged.

The final release audit passed with zero errors and six benchmark artifacts
checked. It recomputed zero internal text overlap, zero ASR audio overlap, and
zero identified-speaker overlap. The saved audit report hash is
`ad56213e9e3560e2fe61a0b2991891548afdb210abf8c74e9416f3519b6aa664`.
The model-lineage audit refreshed 11 manifest families and 34 prediction
artifacts. It still finds cross-split exact duplicates in expanded/experimental
ASR targets, the known XORQA train/dev repeat, and Meta Omnilingual audio/text
rows. Those rows remain in place and are described in the local-only JSON
ledger; this audit does not make any test eligible for a blind claim. The
human-readable lineage report SHA-256 is
`2d749eea33e1f0ccb57cc0a13b0485afc666b2c1909323e91a86e5b1d752d18f`.

The no-download preflight used Python 3.12.5. The project `.venv` has none of
Torch, Transformers, PEFT, NeMo, PyArrow, or common audio readers. The optional
cached runtime exposes Torch and Transformers only; it still lacks PEFT, NeMo,
PyArrow, SoundFile, librosa, and torchaudio. The pinned SraVaani base weights
and NLLB snapshot are absent. Existing SraVaani fine-tunes and a local
Whisper-tiny checkpoint are present, and FFmpeg is installed, but a complete
local audio-to-prediction path remains unverified. No downloads or paid jobs
were started.

The full suite passed **508/508** tests, and `git diff --check` passed. The
workspace was dirty at Git HEAD `0d5323eec75e808ecd1ed3dd4d271db2344511a7`,
so these checks describe the exact local workspace state identified by the
hashes above, not a clean committed checkout.

### Phase 2 candidate scan (2026-09-26)

The new review-only overlap scanner covered 12,510 rows from the three
recommended text splits, the internal text candidate, and the three external
benchmark files. Its ignored local outputs are
`data/processed/evaluation/garhwali_bench/overlap_candidates.json` and
`overlap_candidates.md`; the output hashes are
`abbf44d81c4afd092afce845043dddc16230780f5157eabe5f4f26ccbf3b1d1b` (JSON)
and `5c4426a5c184a154c9add59f897001e2dab6c43afe5144dac7ad9713c18f62a1`
(Markdown). The JSON records all seven input hashes, row IDs, match methods,
scores, and an `unreviewed_candidate` state, without copied source text or raw
source URLs.

The scan found 407 normalized exact-text groups. One crosses source splits: the
known XORQA train/dev repeat. The other 398 cross views are same-split copies
between the internal text candidate and recommended test view. Four character
5-gram near-duplicate pairs passed the configured 0.85 Jaccard threshold; all
four remain within one view/split. It also found 27 exact XORQA source-context
groups spanning source splits. Eleven include training plus dev/test, and four
include both training and test. Those context groups are contamination
candidates requiring eligibility labels; they are not grounds to delete rows or
claim leakage without source/task review. The scan is same-language/script for
near-duplicates and performs no semantic or translation-equivalence search.

The [Phase 2 adjudication record](benchmark-overlap-adjudication-2026-09-26.md)
verifies all 27 XORQA context groups against `source_example.context`. The
refreshed row-level overlay labels 67 unique records for open diagnostics: the
27 context groups, one repeated top-level Garhwali question group, and five
nested English oracle-question groups. The rows remain in place and available
for open diagnostics; the affected groups cannot support independent
source-generalization claims. The four near-text pairs were also inspected:
three recommended-training pairs already share duplicate-component IDs, and
one pair in XORQA dev has the same exact context and answer. All stay within
their original split; the dev diagnostics should group those questions by
source context. A new [nested-field overlap review](benchmark-nested-overlap-review-2026-09-27.md)
scanned 10,571 task fields and found 41 same-field cross-split groups (27
contexts, 6 English answer spans, 5 English oracle questions, 2 Garhwali
translated-answer spans, 1 Garhwali question), zero cross-field groups within
the same task-language label, and zero long exact matches with recommended training text. Fifteen short answer
matches remain generic candidates. A 2026-09-28 supplemental scan grouped
across task-language labels and found 50 short identical strings between
XORQA English answers and Garhwali translated answers; 10 span source splits,
all at 2–6 normalized characters. These are common-answer candidates, not
confirmed translation errors or leakage, and were not added to the overlay.
Only oracle-question groups were newly added to the use overlay; repeated
answer spans remain candidates. See the
[cross-language exact-overlap review](benchmark-cross-language-exact-overlap-2026-09-28.md).
The candidate phase remains open for semantic and broader source-family review.

### Source-page family refresh (2026-09-28)

The new exact source-page audit parsed all 1,139 XORQA page locators into 993
page families. **54 page families (134 records) cross original splits**, and 32
of those families contain multiple distinct exact context passages. The
updated local usage overlay flags 138 unique records for open diagnostics: 134
in cross-split page families and four additional exact question/oracle-question
records. All remain in their original files and splits. This is source-lineage
evidence, not proof of model exposure or answer leakage. The v0.2 adapter now
carries a source-page family hash on XORQA rows; its rebuilt local draft still
contains all eight views and 12,622 rows. See the
[source-page family review](benchmark-source-page-families-2026-09-28.md).

### Parent-safe split and other source-family refresh (2026-09-28)

The historical text split contained 50 parent documents / 1,523 segment rows
across train/test or train/validation. The split builder now groups parent
segments before normalized and supported-semantic reassignment, and records
source-file hashes in its report. The ignored candidate at
`data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/` retains all
114,064 text segments and reports zero parent-document crossings. It reassigns
1,624 segments to keep connected groups together; the recommended filtered view
changes by six rows from historical test to train without dropping any row.
The old manifests and scores remain unchanged. A separate GarhwaliBench
candidate now contains 392 internal text rows, 112 ASR rows, and the full 3,847
external records; all 392 text IDs and strings match the corrected recommended
test view. Its deterministic character-bigram diagnostic is perplexity
14.123460 with the 7,496-row candidate training view. These rows were used by
earlier benchmark work, so the metric is historical/open-set evidence only and
was not used for model selection; no neural inference ran. The manifest hash is
`f5bbed4250983a3af36d43c6e34647ff4ab0674136ad52a1d671114d1ac6c2bb`.

An exact canonical-URL scan of CrossSum finds no repeated source or target
URLs across its 99 train / 100 dev / 500 test rows. FLORES has 2,009 rows but
only a dataset-level source identifier and no row-level URLs, so its finer
source-family split independence cannot be determined from the available
fields. Semantic/paraphrase and cross-language matching remain open. Full
hashes, counts, and limitations are in the
[parent-safe split audit](benchmark-parent-safe-split-audit-2026-09-28.md).

### Phase 3 v0.2 contract draft (2026-09-26)

[`garhwali-bench-v0.2-schema-contract.md`](garhwali-bench-v0.2-schema-contract.md)
defines the proposed record and usage axes and migration gates. The dependency-
free [`validate_benchmark_v02.py`](../scripts/validate_benchmark_v02.py) checked
eight asset views / 12,622 rows and found zero structural/integrity errors,
including all 112 local ASR path/audio hashes. Its ignored local JSON has
SHA-256 `2e0f2dc6286a6a96f8043ce1c6ef6d09ae1987f3ff486974c7cb32e828d4c32c`.
The deterministic v0.2 export is built but not frozen: internal text still needs separate
raw/scoring text and a normalizer ID, metric signatures need pinning, and the
usage overlay must be linked into the versioned package.

## Research results already available

These results cover the main task areas, but they are not one unified final
benchmark and their test usage is not interchangeable.

| Task area | Existing evidence | What it does not establish |
| --- | --- | --- |
| Text modeling | Recommended-view character baseline above; IndicBERTv2 4,096-step continuation averaged 5.089108 validation cross-entropy across 3 seeds | The 4,164-row recommended test remains unresolved for final claims; pretrained exposure for IndicBERTv2 is unknown |
| Translation | Historical test: 1,012 rows; latest dev-only refresh: 997 rows, copy 0.000995 BLEU / 0.008060 chrF2; leave-exact-source-out TM 0.019922 / 0.238087; historical 32-row NLLB Hindi-token proxy | No Garhwali-token NLLB configuration or independent final test; FLORES test and prior NLLB output are already scored |
| Retrieval | Historical: 539-question XORQA test; best IndicBERTv2 Recall@10 is 0.103896. Current dev rerun: Garhwali word/character BM25 Recall@10 is 0.8%/1.0%, with source-page-clustered 95% intervals 0.2–1.6%/0.2–2.0%; English-oracle BM25 is 85.2% [82.1–88.3%] | Historical test has prior predictions. Character-vs-word paired intervals touch zero; cross-language retrieval remains unsolved and zero independent final score is approved |
| Speech | Saved ASR comparisons: SraVaani base 42.761% WER / 17.606% CER; decoder sweep selected RNNT beam-8 on validation, test 42.761% / 17.410%; 61-trial test 43.528% / 17.494%; expanded-human test 43.289% / 17.396%. A 2026-09-28 post-hoc audit verifies all five runs against the same 112 audio hashes and cleaned references, and provides speaker-clustered paired intervals. | All scores remain historical. Every paired WER/CER interval includes zero or touches it, so no fine-tune improvement is established. SraVaani's VAANI training overlap is unknown at example level, and references are not native-adjudicated. See the [ASR consolidation](asr-baseline-consolidation-2026-09-26.md) and [held-out lineage audit](asr-heldout-lineage-audit-2026-09-28.md). |
| Generation/instructions | All three mT0 32,768-step seeds and validation diagnostics are saved. Seed 43 has best validation cross-entropy (4.188287); best adapter chrF2 is 0.074003 versus 0.088327 for base. An existing report says the selected model was evaluated once on an 86-row test after selection. | No adapter is promoted. Test is historical; its 172 prediction rows do not map to the current local manifest inventory, and references remain unreviewed. |

### Translation refresh (2026-09-26)

Both translation runners now default to development and use separate
split-specific output directories. The full 997-row FLORES dev set was scored
with custom add-one BLEU / chrF2 metrics. Copy scored 0.000995 / 0.008060;
leave-exact-source-out translation memory scored 0.019922 / 0.238087. There are
zero exact normalized-source duplicate groups in dev. NLLB was not run because
the base model snapshot and local ML packages are missing. No FLORES test was
scored again. Exact IDs, manifest digests, metric configuration, predictions,
and limitations are in
[`translation-quality-2026-09-26.md`](translation-quality-2026-09-26.md).

### ASR refresh (2026-09-26; later lineage update supersedes this note)

Saved SraVaani greedy, beam-8, six-config fine-tune, 61-trial fine-tune, and
expanded-human predictions were consolidated in
[`asr-baseline-consolidation-2026-09-26.md`](asr-baseline-consolidation-2026-09-26.md).
All five validation files align on the same 269 ordered audio paths and
references; recomputed validation error counts match the stored values. Fine-
tunes are not promoted: the test numbers are historical aggregates. At this
snapshot, sweep/fine-tune reports omitted hashes needed to verify row identity;
the 2026-09-28 post-hoc audit later matched their saved predictions to all 112
fixed audio/reference pairs and computed speaker-clustered intervals. The
report also flags an older SraVaani validation comparator whose result differs
slightly and lacks sufficient sweep-row/config provenance. No saved ASR trial
report indicates a rate-limit interruption. The latest lineage evidence is in
the [held-out audit](asr-heldout-lineage-audit-2026-09-28.md).

### Retrieval refresh (2026-09-25)

The new [development-only retrieval report](retrieval-quality-2026-09-25.md)
records a reproducible 500-query run over 1,059 unique passages from 1,139
source rows. BM25 has almost no coverage for Garhwali questions against the
English passages (4/500 word matches; 7/500 character matches), while paired
English-oracle questions retrieve 499/500 passages. Zero-score BM25 ties are
now correctly treated as not retrieved. The 539-row test was not scored again.
Dense IndicBERTv2 evaluation is blocked by missing local runtime packages and
uncached pinned weights; no download or paid job was used.

The follow-up [source-page-clustered uncertainty analysis](retrieval-source-page-cluster-uncertainty-2026-09-28.md)
reused those 500 saved dev predictions. Exact ID and hash checks passed; 2,000
whole-family resamples cover 461 page families. The character-minus-word paired
Recall@10 difference is +0.2 percentage points (95% interval 0.0–0.6), so the
small difference is inconclusive. This is conditional on the fixed
1,059-document corpus drawn from every original split; it does not estimate
generalization to unseen pages. No test score was produced.

The subsequent [retrieval miss analysis](retrieval-miss-analysis-2026-09-28.md)
verified that all 500/500 dev gold passages are present in the fixed 1,059-
passage corpus. Of the 500 queries, Garhwali word BM25 has 496 zero-score
misses and character BM25 has 493 zero-score misses plus two gold passages
ranked below 10. The English-oracle diagnostic has 74 misses at 10. Thus these
saved-run misses are not caused by absent gold documents; the Garhwali lexical
overlap is the main measured failure mode. The candidate set includes passages
from all source splits, and this analysis does not establish semantic support
or unseen-page performance. No test was scored and no inference was run.

### Generation refresh (2026-09-25)

An earlier report said seed 43 and its generation diagnostics had stopped.
Synced local outputs show a later seed-43 retry completed, followed by a
three-seed validation-generation analysis. Saved predictions independently
reproduce the exact-match and chrF2 values. Seed 43 wins on teacher-forced loss,
but the base mT0 has higher validation chrF2 than every adapter, so no adapter
is promoted. Existing run records report one evaluation of the selected seed on
an 86-row test; it is historical, and its 172 prediction rows remain unmatched
to the current local manifest inventory. Details and hashes are in
[`generation-quality-2026-09-25.md`](generation-quality-2026-09-25.md).

### Translation scoring and uncertainty refresh (2026-09-27)

The shared scorer now supports the existing Garhwali-to-English FLORES outputs
and retains the project's custom add-one-smoothed BLEU and chrF2 definitions.
Re-scoring the saved translation-memory dev predictions reproduced all
existing values exactly on 997/997 rows: BLEU 0.01992188, chrF2 0.23808697,
and exact match 0.0. A 2,000-resample paired record bootstrap versus source-copy
estimates BLEU delta +0.01892665 (95% interval [0.01411908, 0.02385223]) and
chrF2 delta +0.23002697 ([0.22559907, 0.23435906]); exact-match delta is 0.
This compares a translation-memory diagnostic built from other dev pairs with a
copy baseline, so the gain is not neural translation accuracy or independent
generalization. The interval is row-resampled, not source-group clustered.
Inputs, per-row exact-match outcomes, report, and manifest are local-only under
`data/processed/evaluation/benchmark_scoring/translation_dev_uncertainty/`.

The same 2026-09-27 refresh ran the 500-query XORQA BM25 dev baseline through
the shared manifest writer. Its IDs reconcile exactly and its Recall@10 is
0.8% for Garhwali-word queries, 1.0% for character queries, and 85.2% for
English-oracle queries. This confirms the retrieval baseline's language gap;
it does not produce an answer-generation score.

The saved ASR comparison now also has a shared hash-linked manifest. It
reproduces the prior paired scores on all 269 frozen validation audio hashes:
SraVaani 43.3936% WER / 18.9252% CER and Whisper v0.2 78.0522% / 46.2980%.
No inference was run, and held-out rows were not scored. This is a validation
reproduction, not independent accuracy; source-model exposure and reference
quality remain limitations. Details and hashes are in the
[ASR manifest report](asr-validation-run-manifest-2026-09-27.md).

The three saved mT0 generation systems now also have hash-linked manifests.
Each run reconciles 130 prediction IDs to the validation file, verifies task
and reference values, and shares the selected-ID digest recorded by the
seed-43 training report. Recomputed primary-reference diagnostics match the
saved report. Current unreviewed alternate references shift chrF2 by
0.0019–0.0025 across seeds; this is reference sensitivity, not a model-quality
gain. No inference or test scoring ran. The synced analysis omits original
sampling parameters and per-seed checkpoint hashes; see the
[mT0 manifest report](mt0-validation-run-manifest-2026-09-27.md).

### Saved generation-output diagnostics (2026-09-28)

The next Phase 7 pass verifies each mT0 validation run manifest and its
prediction/report output hashes against the frozen validation input and synced
source predictions/report, then audits all 390 outputs by task. Empty outputs,
instruction copies, model control tokens, replacement/surrogate code points,
unexpected controls, and selected invisible/bidirectional controls all count
zero. Repeated-answer concentration is high in the 29-row Garhwali-to-English
lexicon slice: the largest output mode is 9/29, 13/29, and 23/29 across seeds
17, 29, and 43. This is a review signal, not a correctness finding; output
diversity and structural health do not establish reference accuracy. Length,
repetition, and script profiles are descriptive heuristics, and no inference,
held-out scoring, or native-language judgment ran. The aggregate local output
contains no generated text. See
[`generation-output-diagnostics-2026-09-28.md`](generation-output-diagnostics-2026-09-28.md).

## Remaining work, refreshed 2026-09-28

1. **Continue Phase 2 semantic and cross-language analysis.** Exact nested
   fields, cross-language-label exact strings, and XORQA page-title families
   are now covered; the overlay retains and flags 138 rows. The broader scan
   reproduces 616 exact source-content families and 54 XORQA page families
   across splits. It does not compare translations or paraphrases semantically,
   so cross-language independence remains unknown. CrossSum exact URL grouping
   is clean; FLORES lacks row-level source URLs. A validated, locally available
   aligned multilingual method and candidate exposure review remain open.
2. **Finish the v0.2 schema and metric integration.** Eight views and 12,622
   rows validate and export locally. QA, summarization, and translation now
   have versioned hash-linked scoring paths; CrossSum has 100/100 dev summaries
   and XORQA has 499/500 dev target answers. The missing target reference is
   retained but explicitly excluded from metric denominators. Still open are
   full ASR/retrieval/LM task manifests, source-group uncertainty, raw-text
   recovery where provenance supports it, and the final schema/card freeze.
3. **Finish Phase 5 baseline consolidation.** Keep the saved ASR/translation/
   retrieval/generation comparisons; do not reopen historical test sets. Fresh
   NLLB, dense-retrieval, and SraVaani runs remain blocked by local prerequisites.
4. **Continue only validation-safe experiments** after a relevant local
   checkpoint/runtime preflight passes. Keep dev selection separate from
   historical test reporting and do not start paid cloud jobs in this plan.
5. **Continue uncertainty and error analysis.** XORQA retrieval now has
   source-page-clustered intervals and fixed-corpus gold-passage/rank
   diagnostics; saved mT0 generation outputs have task-local structural and
   mode-concentration diagnostics. Phase 8 result eligibility is reconciled in
   [the 2026-09-28 report](task-result-eligibility-2026-09-28.md), and the
   current [lineage audit](model-accuracy-lineage-2026-09-28.md) regenerates
   with historical-only labels whenever saved predictions match test rows.
   CrossSum and Meta Omnilingual test exposure remains unresolved. Add
   source-family uncertainty to translation and other tasks where lineage
   exists. Do not use automated scores to label language correctness or
   dialect.
6. **Publish task cards and a final research report** after baseline and
   lineage evidence reconcile. Keep independent-final and native-reviewed
   counts at zero until their stated criteria are met.
7. **Release only artifacts with a documented redistribution basis.** The
   complete local corpus, rights-filtered public candidate, and benchmark
   package have distinct scopes and must be described separately.

The 2026-09-27 metric/scoring-runner pass generated no new neural-model
predictions. It re-scored existing translation-memory development predictions,
computed paired diagnostic intervals, and added post-hoc ASR and mT0 manifests;
the 2026-09-28 follow-ups add saved-generation structural diagnostics,
reconcile result eligibility, and build the parent-safe split candidate. The
candidate builder also recomputed a deterministic character-bigram diagnostic
on the already-scored open text test rows; it was not used for model selection.
These results do not establish native-language correctness or independent
final-model accuracy. The latest full pytest run
passed 584/584 using the installed pytest executable with `.venv` packages on
`PYTHONPATH`; the documented unittest runner passed 582/582. The earlier
system-interpreter invocation lacked the project LangGraph packages and
produced three import failures; use the documented environment command.

## Reproduction

```bash
.venv/bin/python scripts/build_garhwali_benchmark.py
PYTHONPATH=scripts .venv/bin/python - <<'PY'
from audit_final_release import audit_benchmark
import json
print(json.dumps(audit_benchmark('.'), ensure_ascii=False, indent=2, sort_keys=True))
PY
PYTHONPATH=scripts .venv/bin/python -m unittest tests.test_build_garhwali_benchmark
```

The row-level evaluation ledger contains VAANI speaker identifiers. Keep its
JSON companion local and excluded from Git/public packages.
