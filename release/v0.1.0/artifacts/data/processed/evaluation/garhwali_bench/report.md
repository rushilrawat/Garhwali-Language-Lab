# GarhwaliBench v0.1 experimental baseline

This checksum-addressed benchmark contains 3,847 external task records,
2,492 held-out text segments, and 112
speaker-safe ASR rows. Every record is active for experimental evaluation.

## Integrity

- Internal text overlaps with training: **0**
- ASR speakers shared with training: **0**
- External benchmark texts matching training exactly: **0**

## Dependency-free text baseline

- Character bigram perplexity: **16.464093**
- Evaluation character OOV rate: **4.98e-06**
- Training character vocabulary: **328**

The bigram result is a reproducible floor for later language-model comparisons.
External exact matches are reported rather than silently removed so benchmark
contamination remains measurable.
