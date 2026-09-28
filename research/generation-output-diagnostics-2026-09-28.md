# mT0 validation-output diagnostics — 2026-09-28

## Result

The Phase 7 structural audit covers the three saved 32,768-step mT0 seeds on
the same 130 selected validation examples (390 predictions total). It verifies
the complete 320-row validation file hash, the source prediction/report hashes,
each packaged prediction/report hash, each run manifest's selected IDs, and
task/reference joins. All checks reconcile. No held-out rows were read or
scored, and no inference was run.

The outputs have **no empty strings, full-instruction copies, model control
tokens, replacement characters, surrogate code points, unexpected control
characters, or selected invisible/bidirectional controls**. Repeated-token
runs of at least three tokens occur in 5, 2, and 5 rows for seeds 17, 29, and
43; maximum adjacent token runs are 5, 4, and 4. One output each for seeds 17
and 29 has a repeated-character run of at least six code points (longest runs
21 and 30); seed 43's longest is 3. These flags identify shape anomalies for
inspection, not language errors.

The strongest signal is **task-local repeated-answer concentration** in the
29-row Garhwali-to-English lexicon slice:

| Seed | Distinct normalized outputs | Largest repeated answer | Rows belonging to repeated-answer groups |
| --- | ---: | ---: | ---: |
| 17 | 7/29 | 9/29 (31.0%) | 27/29 |
| 29 | 3/29 | 13/29 (44.8%) | 29/29 |
| 43 | 4/29 | 23/29 (79.3%) | 27/29 |

English-to-Garhwali lexicon outputs also repeat: the largest answer accounts
for 7/29, 7/29, and 8/29 rows for seeds 17, 29, and 43. Sentence translation
slices are more diverse by exact normalized output: English-to-Garhwali has
18–19 distinct outputs among 20 rows per seed; Garhwali-to-English has 18–19.
This is only output diversity. It does not say whether a distinct answer is
correct, fluent, or supported by the source.

Across each 130-row mixed-task seed, the median output length is 5 Unicode
code points; p90 is 19.2, 19, and 17. The benchmark selection contains 90
lexicon rows and 40 sentence-translation rows, so those pooled length values
are not a sentence-length score. The task-specific character/token length
distributions and descriptive output/reference script profiles are in the
local aggregate JSON. The Garhwali-target sentence outputs use both Latin and
Devanagari, with one mixed-script output in seed 43. Neither script is called
incorrect: script choice is not native-reviewed and project records include
both conventions.

## Method and limits

`scripts/analyze_generation_output_diagnostics.py` reads only the frozen
validation source, the source saved-validation predictions/report, and the
three manifested per-seed validation prediction/report files. It fails closed
on hash drift, non-validation scope, ID/task/reference mismatch, output drift,
or unequal seed selections. It reports task-specific exact-output modes using
NFC, case-folding, and collapsed whitespace. It also reports length quantiles,
adjacent token/character runs, known structural Unicode anomalies, exact
instruction-copy/control-token counts, and script-family inventories.

Repeated answers are a **mode-collapse candidate**, not automatically bad
data or wrong translations: duplicate inputs, valid synonyms, and lexical
ambiguity can produce repeated references. The report therefore retains all
rows and makes no deletion or correctness decisions. Script, length, and
repetition checks are heuristics. References have not been native-adjudicated;
these measurements do not certify Garhwali quality or independent accuracy.
The analysis adds no generated text to tracked documentation or its aggregate
output.

Validation SHA-256:
`71c86477f8acc56d11b9bf1f9da421cbb244bc241a0910b30bb3cdee87ca856b`

Source prediction SHA-256:
`ddfe215bf5d8607216aad2a8c4b2866a6ff01818ed8715aab80edd14ffc0652f`

Source report SHA-256:
`00aef2f58c58be8c8edfc0f9a04f499e4a05abb3d40195d4d51c638e4f8f7401`

The local aggregate JSON is ignored at
`data/processed/evaluation/generation/mt0_32768_output_diagnostics_2026-09-28/diagnostics.json`.
Reproduce it with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_generation_output_diagnostics.py
PYTHONPATH=scripts .venv/bin/python -m unittest tests.test_analyze_generation_output_diagnostics -v
```

This completes the saved-generation structural diagnostic in Phase 7. Source-
family uncertainty for translation and task-specific result eligibility remain
open; this report does not authorize a model promotion.
