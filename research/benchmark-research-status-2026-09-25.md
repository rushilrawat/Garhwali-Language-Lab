# Benchmark and research suite: measured status

**Checked:** 2026-09-26; translation, ASR, and integrity refreshes included
**Priority:** GarhwaliBench integrity, then controlled model research  
**Execution:** local only; no Hugging Face jobs or paid compute

## What “done” means here

There is no defensible single completion percentage for this work. A candidate
benchmark can be built and pass file checks without being an independent,
accurate measure of Garhwali. The counts below separate those gates.

| Gate | Measured result | Status |
| --- | ---: | --- |
| Candidate benchmark artifacts | 5 of 5 present: FLORES, CrossSum, XORQA, internal text, internal ASR | Built |
| External task schemas | 3 of 3 valid; 0 schema errors across 3,847 records | Pass |
| Internal text candidate | 398 rows; 0 exact matches against its 7,490-row recommended training view | Pass for automated split integrity |
| Internal ASR candidate | 112 rows; 0 audio-hash or identified-speaker overlaps against ASR train/validation | Pass for automated split integrity |
| External source-split repeats | 1 exact primary-text group / 2 rows in XORQA `train` and `dev`; neither row is in `test` | Flagged; rows preserved |
| Independent final accuracy sets | 0 of 5 task areas approved: language modeling, translation, retrieval, generation, and ASR | Not established |
| Native-language validation | 0 adjudications | Deferred at the owner's direction |
| Automated project tests | 508 of 508 pass; compile and shell syntax checks pass | Pass |

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
verifies all 27 XORQA context groups against `source_example.context` and adds
row-level usage labels for 62 affected records. One exact train/dev question
repeat is included in those 62 records. The rows remain in place and available
for open diagnostics; the affected groups cannot support independent
source-generalization claims. The four near-text pairs were also inspected:
three recommended-training pairs already share duplicate-component IDs, and
one pair in XORQA dev has the same exact context and answer. All stay within
their original split; the dev diagnostics should group those questions by
source context. The deterministic overlay hashes and scope are in the linked
adjudication record. The candidate phase remains open for semantic,
cross-language, and broader source-family review.

### Phase 3 v0.2 contract draft (2026-09-26)

[`garhwali-bench-v0.2-schema-contract.md`](garhwali-bench-v0.2-schema-contract.md)
defines the proposed record and usage axes and migration gates. The dependency-
free [`validate_benchmark_v02.py`](../scripts/validate_benchmark_v02.py) checked
eight asset views / 12,622 rows and found zero structural/integrity errors,
including all 112 local ASR path/audio hashes. Its ignored local JSON has
SHA-256 `2e0f2dc6286a6a96f8043ce1c6ef6d09ae1987f3ff486974c7cb32e828d4c32c`.
The v0.2 export is not built or frozen: internal text still needs separate
raw/scoring text and a normalizer ID, metric signatures need pinning, and the
usage overlay must be linked into the versioned package.

## Research results already available

These results cover the main task areas, but they are not one unified final
benchmark and their test usage is not interchangeable.

| Task area | Existing evidence | What it does not establish |
| --- | --- | --- |
| Text modeling | Recommended-view character baseline above; IndicBERTv2 4,096-step continuation averaged 5.089108 validation cross-entropy across 3 seeds | The 4,164-row recommended test remains unresolved for final claims; pretrained exposure for IndicBERTv2 is unknown |
| Translation | Historical test: 1,012 rows; latest dev-only refresh: 997 rows, copy 0.000995 BLEU / 0.008060 chrF2; leave-exact-source-out TM 0.019922 / 0.238087; historical 32-row NLLB Hindi-token proxy | No Garhwali-token NLLB configuration or independent final test; FLORES test and prior NLLB output are already scored |
| Retrieval | Historical: 539-question XORQA test; best IndicBERTv2 Recall@10 is 0.103896. Current dev rerun: Garhwali word/character BM25 Recall@10 is 0.8%/1.0%; English-oracle BM25 is 85.2% | Historical test has prior predictions. Dev lexical gap shows cross-language retrieval remains unsolved; zero independent final score |
| Speech | Saved ASR comparisons: SraVaani base test report 42.761% WER / 17.606% CER; decoder sweep selected RNNT beam-8 on validation at 43.253% / 18.919%, with saved test aggregate 42.761% / 17.410%; 61-trial validation 42.711% / 18.660%, saved test aggregate 43.528% / 17.494%; expanded-human validation 42.209% / 18.302%, saved test aggregate 43.289% / 17.396%. | All are historical. The base report pins its test manifest, but the sweep/fine-tune test aggregates do not, so exact paired test deltas are unverified. SraVaani's VAANI training overlap is unknown at example level, and references are not native-adjudicated. See the [ASR consolidation](asr-baseline-consolidation-2026-09-26.md). |
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

### ASR refresh (2026-09-26)

Saved SraVaani greedy, beam-8, six-config fine-tune, 61-trial fine-tune, and
expanded-human predictions were consolidated in
[`asr-baseline-consolidation-2026-09-26.md`](asr-baseline-consolidation-2026-09-26.md).
All five validation files align on the same 269 ordered audio paths and
references; recomputed validation error counts match the stored values. Fine-
tunes are not promoted: the test numbers are historical aggregates, and the
sweep/fine-tune reports omit test-manifest hashes needed to confirm row
identity with the base. The report also flags an older SraVaani validation comparator
whose result differs slightly and lacks sufficient run/config provenance.
Existing test metrics are reported from saved aggregates only; no test rows
were opened or rescored. None of the saved ASR trial reports indicates a
rate-limit interruption.

### Retrieval refresh (2026-09-25)

The new [development-only retrieval report](retrieval-quality-2026-09-25.md)
records a reproducible 500-query run over 1,059 unique passages from 1,139
source rows. BM25 has almost no coverage for Garhwali questions against the
English passages (4/500 word matches; 7/500 character matches), while paired
English-oracle questions retrieve 499/500 passages. Zero-score BM25 ties are
now correctly treated as not retrieved. The 539-row test was not scored again.
Dense IndicBERTv2 evaluation is blocked by missing local runtime packages and
uncached pinned weights; no download or paid job was used.

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

## Remaining work, in order

1. **Finish Phase 2 overlap adjudication and usage labeling.** Resolve or
   conservatively label the 27 XORQA source-context groups, the exact train/dev
   text repeat, and four within-split near-duplicate candidates. Preserve all
   rows and keep historical XORQA test use explicit. The local candidate report
   is reviewable, but its matches remain unreviewed.
2. **Freeze v0.2 schemas and eligibility labels.** Include exact and candidate
   duplicate-family IDs, per-row prior-use state, source/reference provenance,
   rights state, and explicit claim limits. Keep unresolved overlap visible;
   the current scan does not cover semantic/cross-language matches.
3. **Finish Phase 5 baseline consolidation.** Keep the saved ASR/translation/
   retrieval/generation comparisons; do not reopen historical test sets. Fresh
   NLLB, dense-retrieval, and SraVaani runs remain blocked by local prerequisites.
4. **Continue only validation-safe experiments** after a relevant local
   checkpoint/runtime preflight passes. Keep dev selection separate from
   historical test reporting and do not start paid cloud jobs in this plan.
5. **Quantify uncertainty and diagnose errors** for comparisons that can be
   paired from existing dev predictions. Do not use automated scores to label
   language correctness or dialect.
6. **Publish task cards and a final research report** after baseline and
   lineage evidence reconcile. Keep independent-final and native-reviewed
   counts at zero until their stated criteria are met.
7. **Release only artifacts with a documented redistribution basis.** The
   complete local corpus, rights-filtered public candidate, and benchmark
   package have distinct scopes and must be described separately.

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
