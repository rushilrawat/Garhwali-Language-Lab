# Nested benchmark overlap review — 2026-09-27

## Purpose and scope

This review extends the primary-text benchmark scan into nested task fields,
where source passages, questions, answers, translations, and summaries can
create split dependence even when top-level record text looks different. It is
an exact normalized-text audit, not semantic translation matching or a
language-quality review. It does not remove, redact, or rewrite any source row.

The scan examined 10,571 nested text fields from FLORES, CrossSum, and XORQA,
and compared them with 7,490 recommended Garhwali training records. It uses
NFKC normalization, case folding, letter/mark/number retention, and collapsed
whitespace. Long-match candidates require at least 20 normalized characters;
short matches are reported separately.

## Findings

- **41 exact same-field groups cross source splits:** 27 English XORQA contexts,
  6 English answer spans, 5 English oracle questions, 2 Garhwali translated
  answer spans, and 1 Garhwali question.
- **0 exact long groups cross different fields under the same task-language label.**
- **0 long exact nested-field matches with recommended training text.**
- **15 short exact matches with recommended training text** are all brief
  Garhwali translated-answer spans (3–4 normalized characters); they are
  retained as common-answer candidates rather than treated as leakage.
- **No source rows were removed.**

The exact repeat findings are evidence of shared strings across the original
benchmark partitions, not proof that an answer was exposed to a model or that
every repeat invalidates a metric. Repeated contexts are the strongest
source-independence warning. Repeated answer spans alone are not enough to
establish source leakage, so they remain documented candidates without an
automatic use restriction.

**Supplemental label-agnostic scan (2026-09-28):** the earlier cross-field
count grouped by the task-declared field language. A follow-up grouping exact
normalized strings across labels found 50 short strings shared by English
`answers[*].text` and Garhwali `translated_answers[*].text`; 10 occur across
source splits, all only 2–6 normalized characters. They remain common-answer
candidates, not confirmed translations or leakage. See the separate
[cross-language exact-overlap review](benchmark-cross-language-exact-overlap-2026-09-28.md).

## Overlay and benchmark export

The XORQA usage overlay now contains **67 unique records** for open-diagnostic
use: records in the 27 repeated-context groups, one repeated top-level
Garhwali-question group, and five repeated English oracle-question groups.
Where a record appears in more than one group, it is counted once. The overlay
sets `independent_source_generalization_eligible=false`, permits explicitly
labeled open diagnostics, and records `record_retained=true`. It does not change
training data or delete source material.

The builder verifies each selected context/question hash against the actual
XORQA source row and verifies the nested report's XORQA input hash before
writing labels. The v0.2 adapter now validates nested oracle-question hashes as
well. It rebuilt the local-only draft with **8 views / 12,622 records** and
manifest SHA-256:

`4346c40e39458640e55579d68c91d301e2e8de8dca19f2477a783cbcaf0732f8`

The v0.2 validator passes all eight assets with zero errors. The package stays
ignored and local-only; this work is neither a rights decision nor release
clearance.

## Reproducibility

Commands from the repository root:

```bash
PYTHONPATH=scripts python scripts/audit_benchmark_nested_overlap.py
PYTHONPATH=scripts python scripts/build_benchmark_usage_labels.py
PYTHONPATH=scripts python scripts/build_benchmark_v02.py
PYTHONPATH=scripts python scripts/validate_benchmark_v02.py
```

The generated, ignored audit JSON has SHA-256
`efbd62164cc91919562826be5164fe6412f41e8dc25fe5298e5e4c7243f67082`;
its Markdown has SHA-256
`08ec2115cc5440139ada7a44f3abdc1556e69c484093a62286f8189344e2beb3`.
The current ignored usage-overlay JSON has SHA-256
`e6bc3dc9d01e3efb52fcb7d303be4ff5247b532f7f50286255b44df03a779ae2`.
The source hashes are included in the generated audit and overlay artifacts.

Focused overlap, overlay, and export tests pass. The latest full pytest suite
passes **559/559** with project `.venv` dependencies; the documented unittest
runner passes 557/557. The earlier system-interpreter pytest invocation did
not see the `.venv` LangGraph packages and failed those three imports.

## Remaining Phase 2 work

The configured exact-string scan is complete for these nested fields. It does
not detect paraphrases, translations, cross-language semantic duplicates,
shared underlying cultural works with different text, or undocumented model
pretraining exposure. Those questions require source-alignment evidence or a
separately validated multilingual method. No blind-test or native-language
accuracy claim follows from a zero exact-match count.
