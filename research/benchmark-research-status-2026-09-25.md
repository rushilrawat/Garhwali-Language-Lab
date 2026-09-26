# Benchmark and research suite: measured status

**Checked:** 2026-09-25  
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
| Automated project tests | 466 of 466 pass; compile and shell syntax checks pass | Pass |

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

The release audit independently passes with 6 artifacts checked, 0 artifact
failures, 0 internal text overlap, 0 ASR audio overlap, and 0 identified-speaker
overlap. Its warning identifies the XORQA train/dev duplicate. Source manifests
and original records remain unchanged.

## Research results already available

These results cover the main task areas, but they are not one unified final
benchmark and their test usage is not interchangeable.

| Task area | Existing evidence | What it does not establish |
| --- | --- | --- |
| Text modeling | Recommended-view character baseline above; IndicBERTv2 4,096-step continuation averaged 5.089108 validation cross-entropy across 3 seeds | The 4,164-row recommended test remains unresolved for final claims; pretrained exposure for IndicBERTv2 is unknown |
| Translation | FLORES copy and translation-memory results on 1,012 rows; 32-row NLLB Hindi-token proxy; adapter underperforms base | No Garhwali-token NLLB configuration or independent final test; existing FLORES test is already scored |
| Retrieval | 539-question XORQA test; best IndicBERTv2 Recall@10 is 0.103896 | Low absolute retrieval quality; all 539 test rows have prior predictions |
| Speech | On the fixed 112-row comparison, SraVaani WER/CER is 42.761% / 17.606%; the fine-tune has higher WER and remains unselected | The test is already scored, upstream VAANI exposure is unspecified, and references are not native-adjudicated |
| Generation/instructions | mT0 32,768-step continuation has 2 completed seeds (validation cross-entropy 4.266280 and 4.219282); prior small-run exact match is 0% | Seed 43 and full generation diagnostics did not finish; the current 32,768-step test remains unopened |

## Remaining work, in order

1. **Keep the benchmark candidate auditable.** Retain the source-split duplicate
   flag and baseline-training hash; rerun the full release audit after any
   manifest or source change.
2. **Finish comparable experiments on validation only.** Fix model revisions,
   training-view hashes, decoding rules, and selection metrics before opening a
   test. Do not tune from the already-scored FLORES, XORQA, or VAANI test results.
3. **Prepare an untouched evaluation plan.** A test may support a project-split
   claim only after its exact rows and hashes are frozen, prior use is checked,
   and the selected checkpoints are fixed. Unknown pretraining exposure and
   unreviewed references must remain explicit limitations.
4. **Do not promote automated language guesses.** Native review and dialect
   annotation remain deferred. Scores must continue to say “automated
   candidate,” not “gold” or “native-validated.”
5. **Release only the package supported by its rights evidence.** The complete
   257,807-row package retains all gathered values locally. The Hugging Face
   corpus is private and rights-filtered; its 24,566 redacted catalog values and
   216 omitted structured records have no compatible public-rights basis in the
   current audit. This report does not authorize making that full package
   public.

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
