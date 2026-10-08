# Product progress scorecard — historical estimates (refreshed 2026-09-30)

> **Historical snapshot:** This scorecard predates corpus v0.2.7 and the
> 2026-10-06 project closeout. Its completion percentages are dated estimates,
> not current percentages. For the current verified state, use
> [`project-status/finalreport.md`](finalreport.md) and [`README.md`](../README.md).

This scorecard covered every product in the plan as of its dated snapshot.
It reflects delivered implementation and verified artifacts, not linguistic
accuracy, public completeness, or the percentage of Garhwali that has been
captured. A released dataset can be operational while still needing broader
coverage and better review.

## Portfolio view

```text
GarhwaliCorpus          88%  ██████████████████░░
GarhwaliBench           56%  ███████████░░░░░░░░░
Research Suite          66%  █████████████░░░░░░░
Garhwali Models         39%  ████████░░░░░░░░░░░░
Community Layer         20%  ████░░░░░░░░░░░░░░░░
Garhwali API             0%  ░░░░░░░░░░░░░░░░░░░░
Public Infrastructure   20%  ████░░░░░░░░░░░░░░░░
```

The bars are a weighted implementation snapshot through 2026-09-30, including
the ASR scorer integration, rights audit, shared generation scoring, tenth
web-intake pipeline, and v0.2.1 source-to-Hugging-Face release. Saved generation
predictions reconcile to 130/320 current validation rows; this produced no
fresh model inference. The refresh added 164 exact-new lexical strings, rebuilt
all downstream views, published a versioned additive Hub package, and added
package-integrity tests. These improve reproducibility but do not close overall
source coverage, benchmark independence, or native-review gates. The
percentages use the scope weights described below and are rounded planning
estimates. Their equal-weight mean is
**41%**, only an orientation point, not a single objective project-completion
metric. Product scopes differ greatly.

## GarhwaliCorpus — 88%

Six corpus deliverables are scored equally; fully verified is 100%, substantial
but incomplete is 75%, and ongoing coverage work is 60%.

```text
Current-scope intake and provenance     100%  ████████████████████
Canonical merge and exact dedup          100%  ████████████████████
Automated quality and noise controls      75%  ███████████████░░░░░
Rights-aware packaging and additive upload 100%  ████████████████████
Splits, manifests, and release checks       90%  ██████████████████░░
Source and content coverage closure         60%  ████████████░░░░░░░░
```

The v0.2.1 corpus and speech dataset releases are live. The latest v0.2.1 local
working view has **32,072 exact-unique parent texts** from 34,505 source rows
across 49 files, 16,089,764 characters, 2,935,379 whitespace-separated tokens,
and 151,690 exact-unique segments. The tenth-wave web layer retains 1,772
exact-new candidate pages / 6,758,808 source characters; language identity and
reuse rights remain unresolved, so those pages remain experimental. The V2
refresh added 164 exact-new words, phrases, proverbs, and riddles from the
MIT-labelled Garhwali Language Library, and the v0.2.1 public content package is
live at Hugging Face commit `5db2673` (its cards were corrected at `53a0aff`).
The score stays
below 100% because public corpus content is rights-filtered, OCR and story
quality remain unreviewed, and source coverage is not exhaustive. Native review
and dialect annotation are deferred and are not treated as an active release
blocker.

Weighted result: **88%** (525/6 = 87.5%, rounded). The update from 83% reflects
completion of the rights-aware packaging and additive v0.2.1 Hub publication
workstream. It does not mean every source has been cleared for unrestricted
reuse; unresolved content remains out of the public full-text profile and is
accounted for in the source-coverage and rights-quality work.

## GarhwaliBench — 56%

Weighted against the benchmark's principal gates. Integrity and schemas are
necessary but do not substitute for independent final evaluation.

```text
Candidate task artifacts (10% weight)    100%  ████████████████████
Schema checks and draft adapters (10%)    100%  ████████████████████
Split and contamination controls (20%)    55%  ███████████░░░░░░░░░
Scoring and run tooling (20%)              75%  ███████████████░░░░░
Lineage and uncertainty evidence (15%)     65%  ████████████░░░░░░░░
Independent final-ready benchmark (25%)    0%  ░░░░░░░░░░░░░░░░░░░░
```

Weighted result: **56%** (10 + 10 + 11 + 15 + 9.75 + 0 = 55.75%, rounded).
The shared scorer now emits corpus and per-record ASR WER/CER; a 269-row
validation-only replay reproduced 2,161/4,980 word errors (43.3936%) and
3,282/17,342 character errors (18.9252%). The aggregate-score lineage also
matches the exact 402-row text test, and six local task cards document the
candidate suite. These are historical/development checks, not new model
inference. Semantic/source-family contamination work and fresh final-result
eligibility remain unfinished. The owner approved work toward independent
final-accuracy evidence in all five task areas on 2026-09-30, but current
evidence eligibility remains **0/5**; the benchmark is an automated candidate,
not a public-cleared benchmark. Native review is deferred and excluded from
the active completion gates at the owner's direction.

Rights audit: all **14,703 draft view rows** currently have both public-clearance
flags set to false (the total includes 402 intentional cross-view mirrors).
Within the 10,342 recommended text split rows, 2,077 have recorded compatible
rights assessments but are not yet cleared for this export, while 8,265 have no
item-level rights status recorded. The external text tasks and 112-row VAANI
audio task also need component-specific review. This is why the benchmark
release gate remains at zero; no records were deleted by the audit.

## Research Suite — 66%

This is the equal-weight average of the 11 phases in the benchmark/model
roadmap. Phase percentages estimate the work completed within each phase; they
do not certify that a model result is correct or independent.

```text
Phase 0  Scope, claims, and use policy       60%  ████████████░░░░░░░░
Phase 1  Inventory and reproducibility      100%  ████████████████████
Phase 2  Split and contamination controls    60%  ████████████░░░░░░░░
Phase 3  Benchmark contract and freeze       65%  █████████████░░░░░░░
Phase 4  Reproducible evaluation runner      75%  ███████████████░░░░░
Phase 5  Baseline consolidation              65%  █████████████░░░░░░░
Phase 6  Bounded model experiments           70%  ██████████████░░░░░░
Phase 7  Uncertainty and error analysis      70%  ██████████████░░░░░░
Phase 8  Result eligibility labels            85%  █████████████████░░░
Phase 9  Task cards and publication           60%  ████████████░░░░░░░░
Phase 10 Maintenance and extension            25%  █████░░░░░░░░░░░░░░░
```

Arithmetic mean: **67%** (735/11 = 66.8%). The scorer contract and real-data
validation replay advanced the evaluation phases. Six local task cards now
cover task design, provenance, split history, metrics, and limits; rights
review and actual benchmark publication remain open. Other large remaining
items are closing semantic/source-family gaps, reproducing baselines where
model weights and runtimes permit, and preparing a genuinely independent
evaluation set. Phase 10 moved from 15% to 25% because the project now has a
tested refresh command, pinned intake manifests, additive release preparation,
and a generated project file map. It remains partial because web acquisition is
explicitly initiated, upload is not automated, and upstream source changes
still require review.

## Garhwali Models — 39% portfolio average

These are separate maturity estimates for the five planned model tracks. The
portfolio has research baselines and experiments, but no track is promoted as a
production-quality Garhwali model.

```text
Language model / text representation   40%  ████████░░░░░░░░░░░░
Translation                           35%  ███████░░░░░░░░░░░░░
Retrieval                             45%  █████████░░░░░░░░░░░
Speech recognition (ASR)              60%  ████████████░░░░░░░░
Speech synthesis (TTS)                15%  ███░░░░░░░░░░░░░░░░░
```

The arithmetic mean is **39%**. ASR has the most mature data and saved
experiments, but the current experiments do not establish a reliable promoted
improvement. TTS remains at data/readiness work; there is no validated TTS
system.

## Community Layer — 20%

```text
Review workflow and contributor guidance  100%  ████████████████████
Contribution intake interface               0%  ░░░░░░░░░░░░░░░░░░░░
Moderation and contributor operations        0%  ░░░░░░░░░░░░░░░░░░░░
Correction-to-corpus integration             0%  ░░░░░░░░░░░░░░░░░░░░
Community participation program              0%  ░░░░░░░░░░░░░░░░░░░░
```

Equal-weight result: **20%**. The repository has review guidance and queues;
there is no working public contribution product or ongoing contributor
program. Native review remains deferred.

## Garhwali API — 0% implemented

The API is specified in the roadmap, but no running service or implemented
endpoint is present.

```text
Search / lexicon / normalization / transliteration / culture  0%  ░░░░░░░░░░░░░░░░░░░░
ASR and translation beta endpoints                            0%  ░░░░░░░░░░░░░░░░░░░░
Authentication, quotas, monitoring, and hosting                0%  ░░░░░░░░░░░░░░░░░░░░
```

The endpoint plan is design work, not product implementation.

## Public Infrastructure — 20%

This score covers the broader planned public platform, not just data hosting.

```text
Versioned public corpus and speech datasets  100%  ████████████████████
Published model cards                          0%  ░░░░░░░░░░░░░░░░░░░░
Public leaderboard                             0%  ░░░░░░░░░░░░░░░░░░░░
Corpus explorer                                0%  ░░░░░░░░░░░░░░░░░░░░
Interactive demos                              0%  ░░░░░░░░░░░░░░░░░░░░
```

Equal-weight result: **20%**. The v0.2.1 Hugging Face corpus and separate
speech dataset are released and their current manifests/checks were verified.
The leaderboard, explorer, demos, and public model releases remain future
products.

## Evidence and limits

- Current corpus and release evidence: [`project-status/finalreport.md`](finalreport.md),
  [`README.md`](../README.md), and
  [`project-status/corpus-preparation-status.md`](corpus-preparation-status.md).
- Benchmark and modeling phase evidence:
  [`benchmark-model-roadmap.md`](../research/benchmark-model-roadmap.md),
  [`garhwali-bench-v0.2-rights-inventory-2026-09-29.md`](../research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md),
  [`project-status/benchmark-research-status-2026-09-25.md`](benchmark-research-status-2026-09-25.md),
  and [`task-result-eligibility-2026-09-28.md`](../research/task-result-eligibility-2026-09-28.md).
- Candidate benchmark example cards and supplementary working protocols remain
  local-only; the rights inventory records why they are not public release
  artifacts.
- These are implementation-scope estimates made on 2026-09-30. They are not
  accuracy scores, data-quality scores, legal conclusions, or a forecast of
  time remaining. A changed roadmap or acceptance gate changes the denominator.
