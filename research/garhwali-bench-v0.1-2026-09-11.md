# GarhwaliBench v0.1 experimental baseline

Generated on 2026-09-11 from the checksum-addressed evaluation assets. The
benchmark is active for local experiments and keeps uncertainty, source rights,
and later correction fields separate from evaluation eligibility.

## Current tasks

| Task | Records | Purpose |
| --- | ---: | --- |
| IndicGenBench FLORES | 2,009 | Garhwali–English translation |
| IndicGenBench CrossSum | 699 | Cross-lingual summarization |
| IndicGenBench XORQA | 1,139 | Cross-lingual question answering |
| Held-out corpus text | 2,492 | Language modeling and generation |
| Speaker-safe VAANI ASR | 112 | Speech recognition |

All three external task schemas validate. Exact normalized text overlap between
the external benchmarks and training split is **0**. The held-out corpus has
**0** exact training-text matches, and the ASR evaluation has **0** speakers in
common with ASR training.

## First reproducible floor

The dependency-free add-one-smoothed character bigram baseline uses only the
80,926 training segments. On the 2,492 held-out text segments it produces:

- character perplexity: **16.464093**;
- negative log likelihood per character: **2.801182**;
- character OOV rate: **0.00000498**;
- observed training character vocabulary: **328**.

This is a deterministic lower baseline, not a competitive language model. Future
multilingual and Garhwali-adapted systems should beat it under the same frozen
manifest and report results separately by task, source, script, and dialect
evidence.

## Next execution cycle

1. Evaluate multilingual text, translation, retrieval, and ASR models against the
   frozen manifests.
2. Use model disagreement and confidence to propose OCR, spelling,
   Hindi/Garhwali, mixed-language, and dialect corrections.
3. Apply only traceable corrections as new fields while preserving original text.
4. Rebuild the corpus and benchmark, then measure whether the cleanup improves
   held-out performance.

Reproduce the index and baseline with:

```bash
.venv/bin/python scripts/build_garhwali_benchmark.py
```
