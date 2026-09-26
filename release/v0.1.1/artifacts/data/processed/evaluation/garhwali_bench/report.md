# GarhwaliBench v0.1 experimental baseline

This checksum-addressed benchmark contains 3,847 external task records,
398 held-out text segments, and 112
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

Training view: `data/processed/model_ready/splits/text_recommended/train.jsonl` (7,490 rows;
SHA-256 `2de3f3f95f24d41df9a4ce142496b7e9e97ac402ff4cca4c00edb6bed41d6ec8`).

- Character bigram perplexity: **14.122106**
- Evaluation character OOV rate: **0.0**
- Training character vocabulary: **110**

The bigram result is a reproducible floor for later language-model comparisons.
External exact matches are reported rather than silently removed so benchmark
contamination remains measurable.
