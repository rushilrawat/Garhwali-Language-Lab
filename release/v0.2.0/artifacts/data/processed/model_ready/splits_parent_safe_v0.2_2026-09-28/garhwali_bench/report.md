# GarhwaliBench experimental baseline

Release ID: `garhwali-bench-parent-safe-candidate-2026-09-28`

This checksum-addressed benchmark contains 3,847 external task records,
392 held-out text segments, and 112
speaker-safe ASR rows. The internal text is an automated strict candidate set,
not a native-reviewed or dialect-aware gold benchmark.

## Integrity

- Internal text overlaps with training: **0**
- ASR speakers shared with training: **0**
- External benchmark texts matching training exactly: **0**

## Exact primary-text repeats across source splits

These counts use each record's normalized `text_normalized` field. Source rows
remain unchanged and evaluation-only; inspect any overlap before using source
train/dev partitions for model fitting or selection.

- flores: **0 groups / 0 rows**
- crosssum: **0 groups / 0 rows**
- xorqa: **1 groups / 2 rows** across dev, train

## Dependency-free text baseline

Training view: `data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/text_recommended/train.jsonl` (7,496 rows;
SHA-256 `fc7b2357361b0ec0ce902e18a3b0bae87af01e8382508d3065b0b2c1ff168ee9`).

- Character bigram perplexity: **14.12346**
- Evaluation character OOV rate: **0.0**
- Training character vocabulary: **110**

The bigram result is a reproducible floor for later language-model comparisons.
External exact matches are reported rather than silently removed so benchmark
contamination remains measurable.
