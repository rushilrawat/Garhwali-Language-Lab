# GarhwaliBench v0.1 experimental baseline

This checksum-addressed benchmark contains 3,847 external task records,
398 held-out text segments, and 112
speaker-safe ASR rows. The internal text is an automated strict candidate set,
not a native-reviewed or dialect-aware gold benchmark.

## Integrity

- Internal text overlaps with training: **0**
- ASR speakers shared with training: **0**
- External benchmark texts matching training exactly: **0**

## Dependency-free text baseline

- Character bigram perplexity: **17.000058**
- Evaluation character OOV rate: **0.0**
- Training character vocabulary: **327**

The bigram result is a reproducible floor for later language-model comparisons.
External exact matches are reported rather than silently removed so benchmark
contamination remains measurable.
