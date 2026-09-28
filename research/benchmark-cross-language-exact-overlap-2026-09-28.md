# Cross-language-label exact-overlap review — 2026-09-28

## Result

The nested-field audit now also groups exact normalized strings across task
language labels instead of partitioning them by the declared field language.
This is an exact-string check only: it does not determine the actual language
of a value, whether two answers are translations, or whether a model saw a
record.

Across 10,571 nested fields from FLORES, CrossSum, and XORQA, it found **50
exact strings represented under both `en` and `gbm` field labels**. Every group
is between the XORQA English `answers[*].text` and Garhwali
`translated_answers[*].text` fields. All 50 are short (2–6 normalized
characters), below the audit's 20-character long-match threshold. **Ten groups
occur across source splits**: seven span dev/test, two span train/dev/test, and
one spans train/test. Together they contain 35 field occurrences across 25
unique records.

These are repeated short answer candidates, not confirmed translations or
confirmed leakage. Names, numerals, and common short answers can be identical
across language labels. The prior `zero cross-field groups` result was
conditioned on matching language labels; this supplemental result makes that
scope explicit. The original same-field result remains 41 long exact
cross-split groups, and the scan still finds zero long exact matches to the
7,490-row recommended Garhwali training view.

No source rows were deleted, rewritten, or moved. The XORQA usage overlay was
not expanded: answer-span repetition alone remains insufficient evidence for
an automatic eligibility restriction. Keep these 25 records available, but
group answer diagnostics by exact answer/source family and avoid presenting
the matches as independent examples without a sensitivity check.

## Reproduction and provenance

Run from the repository root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_benchmark_nested_overlap.py \
  --output-json data/processed/evaluation/garhwali_bench/nested_overlap_candidates_2026-09-28.json \
  --output-markdown data/processed/evaluation/garhwali_bench/nested_overlap_candidates_2026-09-28.md
PYTHONPATH=scripts .venv/bin/python -m unittest tests.test_audit_benchmark_nested_overlap
```

The generated JSON includes hashes, record IDs, field paths, splits, labels,
and value indices; it includes no copied text. Its SHA-256 is
`e357a18e4e212e7a470ea1ce10bb0b871edcd41d7849f110945dbfa4e6bbe730`; the
generated Markdown SHA-256 is
`affdaf4aebd7a53337b624f83fca6007017666c7b4e21344e9bf914d6a061367`. Both
artifacts remain Git-ignored under `data/processed/`.

The four source input hashes are recorded in the JSON. The nested audit code
and regression test are `scripts/audit_benchmark_nested_overlap.py` and
`tests/test_audit_benchmark_nested_overlap.py`. The new test verifies that a
long exact string crossing the English/Garhwali field labels is reported
separately from same-language split and cross-field groups, and that short
matches are counted below the long-match threshold.

## Limits and next use

This closes only the exact-string portion of the cross-language scan. It does
not find paraphrases, translations with different wording, related cultural
works, or upstream model pretraining exposure. The 10 cross-split groups are
open diagnostic candidates; do not call them leakage without source/task
evidence. Semantic matching remains deferred until a validated multilingual
method and reliable source alignments are available locally.
