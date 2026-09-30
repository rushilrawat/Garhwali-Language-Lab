# ASR corpus metric integration — 2026-09-29

The shared benchmark prediction runner now supports `--task asr` and uses the
versioned corpus-WER/CER contract in `scripts/asr_metrics.py`. It enforces exact
prediction-ID coverage, preserves blank hypotheses as deletions, excludes and
lists references that normalize to an empty denominator, reports pooled corpus
errors/denominators, and includes per-record WER/CER for error analysis. The
run manifest fingerprints the ASR metric implementation.

## Real-data integration check

I ran the new scorer against the existing SraVaani validation comparison,
selecting only its 269 validation audio hashes. It matched the previously
recorded aggregate exactly:

| Measure | Errors / denominator | Result |
| --- | ---: | ---: |
| Corpus WER | 2,161 / 4,980 words | 43.3936% |
| Corpus CER | 3,282 / 17,342 characters | 18.9252% |
| Row coverage | 269 / 269 | complete |
| Per-record scores emitted | 269 | complete |
| Empty-reference exclusions | 0 | none |

This was a rescoring of saved **development/validation** predictions, not fresh
model inference. Only the selected validation rows were decoded and scored;
the held-out test rows were not scored. The check confirms metric-code
compatibility with the historic aggregate and does not show a model improvement.

## Claim limits

This set has previous model-selection history, VAANI training exposure cannot
be traced to example IDs, and references have not been adjudicated by local
native reviewers. Treat the numbers as historical validation diagnostics, not
independent accuracy or native-validated Garhwali correctness. Current native
review remains deferred at the owner's direction.
