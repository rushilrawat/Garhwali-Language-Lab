# XORQA source-page family review — 2026-09-28

## Finding

An exact source-page audit parsed the canonical page-title segment from the
upstream XORQA title locator for all **1,139/1,139** records. It found 993
distinct normalized page families. **54 page families (134 records) span
original train/dev/test splits.** Thirty-two of the 54 families contain more
than one distinct exact context passage across those splits, so exact context
matching alone missed page-level source overlap.

| Original split pattern | Page families |
| --- | ---: |
| dev + test | 33 |
| dev + train | 12 |
| dev + test + train | 5 |
| test + train | 4 |

This is source-lineage evidence from an exact page title, not proof that the
answers duplicate one another, that model training saw these rows, or that a
model's output is contaminated. It does mean same-page records should not be
counted as independent source-generalization evidence. The audit normalizes
titles using NFKC, case-folding, and whitespace collapse, then groups the
upstream `title:` segment before `_parentSection:`. It does not fuzzy-match
aliases or related pages.

## Overlay and v0.2 handling

The review-only XORQA usage overlay now labels **138 unique records** as
`open_diagnostic_only_split_overlap`: 134 belong to the cross-split page
families, and four additional records are flagged by exact question/oracle
question reuse. The earlier overlay had 67 labels; this refresh adds 71 unique
records. Current labels by original split are dev 64, test 49, and train 25.
Every row remains in its source file and original split, and all flagged rows
remain available for explicitly labeled open diagnostics.

The local v0.2 adapter now records both `source_page_family_sha256` and its
normalized title hash for XORQA rows, alongside the existing exact context
family and row-level overlay evidence. The rebuilt draft still contains all
eight views and 12,622 rows; it is not a frozen benchmark or a public package.

## Reproduction and provenance

Run from the project root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_xorqa_source_page_families.py
PYTHONPATH=scripts .venv/bin/python scripts/build_benchmark_usage_labels.py
PYTHONPATH=scripts .venv/bin/python scripts/build_benchmark_v02.py
```

The source-page report JSON is local-only and contains record IDs and hashes,
not source titles, questions, answers, or passages. Its SHA-256 is
`aeb5e845e9d128a82785156145db27f9a60a865eab9716763349403c0886e45c`; the
Markdown summary hash is
`96f869d07b7b73df2f68ea38671bc9ad9a565ffbdf438ccfbc1d672ba6e629bc`.
The XORQA input hash is
`e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6`.
The refreshed usage overlay JSON hash is
`deb49ebee8dc9b41de9ec0c87116b8934c14d2796dbb633aa4714b6f254def22`, and
the rebuilt local v0.2 draft manifest hash is
`2ca84a51cf916d336d7a4e92c5fb34f313b19c72900b7b47f6fa79728e82e25e`.

The implementation and focused regression tests are in
[`audit_xorqa_source_page_families.py`](../scripts/audit_xorqa_source_page_families.py),
[`build_benchmark_usage_labels.py`](../scripts/build_benchmark_usage_labels.py),
and [`build_benchmark_v02.py`](../scripts/build_benchmark_v02.py). No source
records were deleted, moved, or rewritten, and no model inference or held-out
rescoring was run.

## Remaining limits

Exact source-page grouping does not identify related pages, paraphrases,
translation-equivalent content, or checkpoint pretraining exposure. Semantic
cross-language analysis and source-family review for other benchmark tasks
remain open. Existing public benchmark partitions are still historical/open
diagnostics, not blind final evaluation.
