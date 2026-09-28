# Benchmark result eligibility and prior-use audit

**Checked:** 2026-09-28

**Roadmap phase:** 8 — result eligibility and benchmark labels
**Evidence:** fresh local lineage audit in [model-accuracy-lineage-2026-09-28.md](model-accuracy-lineage-2026-09-28.md)

This pass corrects stale labels in the lineage audit and records what each result
can support. It ran no model inference and did not alter, remove, redact, or
repartition corpus records. Eligibility labels limit evaluation claims; they do
not make language data unusable.

## Labels

- **Candidate:** structurally available, but a task result or its reference
  quality is not established.
- **Development-only:** suitable for development diagnostics and selection;
  it cannot serve as independent final evidence.
- **Historical-only:** previously scored or used for selection. Preserve and
  report the result as history, not fresh confirmation.
- **Unresolved:** prior local use may be absent, but checkpoint exposure or
  row identity is not adequately known to make an independent claim.
- **Independent-final eligible:** none. This requires frozen, prior-use-audited
  rows, disjoint training/development groups, documented references, and
  reasonably characterized checkpoint exposure.
- **Native-reviewed:** none; native review remains deferred at the owner's
  direction.

## Fixed evaluation row sets

| Task and split | Selected rows | Prior row-level matches | Status | What the evidence permits |
|---|---:|---:|---|---|
| CrossSum dev | 100 rows; references present for 100 / 100 | 0 | Development-only | Available for development; no saved prediction artifact has been reconciled to this split. |
| CrossSum test | 500 / 500 | 0 | Unresolved | No local prediction match was found. Upstream checkpoint exposure is unknown, so the set is not a blind or independent final test. |
| FLORES dev | 997 / 997 | 997 | Development-only | Existing translation diagnostics may be reported as development evidence. |
| FLORES test | 1,012 / 1,012 | 1,012 | Historical-only | Saved translation predictions cover the full test split; do not rescore for selection or claim fresh confirmation. |
| Instructions validation | 320 / 320 | 144 | Development-only | Use for validation and error analysis under the recorded protocol; prior results make it unsuitable as fresh confirmation. |
| Instructions test | 260 / 260 | 134 | Historical-only | 134 rows match saved predictions. The other 126 unmatched rows are not proof of non-use; an older mT0 sidecar has different membership. Treat the entire fixed split as historical. |
| Meta Omnilingual validation | 271 / 298 internally safe | 0 | Development-only | The remaining 27 rows fail internal evaluation-safety flags and are excluded from this selected view; source rows remain preserved. Upstream exposure is unknown. |
| Meta Omnilingual test | 292 / 300 internally safe | 0 | Unresolved | Eight rows fail internal evaluation-safety flags. The 292 selected rows still have unknown upstream exposure; no independent claim is justified. All 300 source rows remain preserved. |
| Recommended-text test / internal text candidate | 398 / 398 | 0 row-level prediction matches | Historical-only | The character-bigram baseline scored this exact 398-row set in aggregate. The selected candidate texts match the fixed test texts exactly by normalized-text digest; no row-level prediction file was saved. |
| VAANI ASR validation | 269 / 269 | 269 | Development-only | Reuse for development selection and error analysis only. |
| VAANI ASR test | 112 / 112 | 112 | Historical-only | Saved ASR predictions cover the test rows. SraVaani reports broad VAANI training exposure; example-level overlap is unknown. |
| XORQA dev | 500 / 500 | 500 | Development-only | Existing retrieval results are development evidence on a fixed corpus that includes documents from all source splits; they do not establish unseen-page generalization. |
| XORQA test | 539 / 539 | 539 | Historical-only | Saved retrieval predictions cover the full test split. Do not treat it as blind or independently held out. |

The lineage audit inventories **11 manifest families and 38 prediction
artifacts**. Its JSON companion contains row-level identifiers, including
speaker identifiers, and remains local-only; the Markdown report publishes
counts and hashes instead.

## Other saved evaluations that need narrower claims

- **mT0 generation:** the saved test report records 86 examples, marks the test
  as opened once, and prohibits further test-based selection. Its row-set hash
  does not reconcile to the current fixed instruction-test manifest. Treat the
  result as historical, with row identity unresolved; its scores are not a
  fresh benchmark claim.
- **NLLB Hindi-token proxy:** a report records 32 evaluation examples but no
  split or manifest hash. NLLB has no Garhwali language token in this setup, so
  the proxy is exploratory and cannot substantiate Garhwali translation
  accuracy. Its exact fixed-split eligibility remains unresolved.
- **ASR experiments:** saved decoder-sweep, 61-trial, and expanded-human
  outputs include 112-row held-out results. These are historical comparisons;
  their test references have already been scored, and SraVaani's upstream
  example-level exposure is unknown. Missing test-manifest hashes in some
  reports also prevent treating reported differences as verified paired
  changes.
- **TTS:** the project has candidate audio/text splits but no valid TTS model
  evaluation. ASR predictions matching the same audio hashes do not constitute
  a TTS result.

## Decision and next work

There are **zero independent-final-eligible task results** and **zero
native-reviewed task references**. Historical-only results remain useful for
describing completed experiments; unresolved results remain documented and
available for research. If a historical test set is later used for model
training, retain the data but stop calling that split held out and create a new
independent evaluation set before making a final accuracy claim.

The audit code now promotes a test decision to `historical_only` whenever at
least one saved prediction row matches that fixed test split. The internal
text decision is explicitly historical because the aggregate character-bigram
baseline used the same rows even without a row-level prediction artifact. The
focused tests cover both cases.

**Phase 8 is complete for the configured benchmark decisions and the saved
result artifacts listed above.** Phase 9 remains: publish per-task cards and a
reproducible research report, using these labels and carrying forward the
split, provenance, checkpoint-exposure, and reference-quality limitations.
