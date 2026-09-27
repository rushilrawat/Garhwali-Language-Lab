# GarhwaliBench v0.2 draft export — 2026-09-26

## Result

Built a deterministic, local-only adapter export for all eight current
benchmark/model-data views. It contains **12,622 rows** and retains the complete
v0.1 source record in every adapted row. No input records were removed, merged,
or edited. The export is a schema migration artifact, not a public release or a
claim that all included values are accurate or rights-cleared.

The ignored output is
`data/processed/evaluation/garhwali_bench/v0.2-draft/`. Its manifest SHA-256 is
`0352298d966d4ebcf1540bad913db283bc1cb9e69dfd85b7ea9e5b4fd8525fd1`.

| View | Rows | Split counts |
| --- | ---: | --- |
| FLORES translation | 2,009 | dev 997; test 1,012 |
| CrossSum summarization | 699 | train 99; dev 100; test 500 |
| XORQA question answering | 1,139 | train 100; dev 500; test 539 |
| Internal text candidate | 398 | test 398 |
| Internal VAANI ASR candidate | 112 | test 112 |
| Recommended text train | 7,490 | train 7,490 |
| Recommended text validation | 377 | validation 377 |
| Recommended text test | 398 | test 398 |

## Adapter behavior

- External benchmark rows retain `text_original` as raw source text and
  `text_normalized` as scoring text, with separate SHA-256 values and the
  `unicode-nfc-trim-v1` normalizer ID.
- Internal text and recommended text retain their v0.1 text value as
  `text_source` and `text_scoring`. Since those views do not carry a verified
  raw-original field, the adapter leaves `text_raw` null and labels the gap; it
  does not misrepresent the candidate text as original raw text.
- ASR rows preserve the source `transcript`, selected ASR target, scoring form,
  audio hash, full source row, speaker ID, and local audio path. The ASR output
  and the complete export are explicitly marked local-only and not allowed for
  public upload by this adapter.
- The current XORQA overlay is linked into the matching 62 rows. The builder
  verifies each overlay question/context hash, split, source-family hash, and
  retained-row flag against the source data. It also verifies the overlay's
  XORQA input hash against the current benchmark file.
- Each output JSONL has row counts and SHA-256 in the versioned manifest. The
  builder verifies output hashes, counts, IDs, schema IDs, retained-row flags,
  and agreement with the written manifest after each build.
- Rights status and source declarations are preserved, but every record has
  `public_release_cleared: false`; export generation is not rights clearance.

## Metric signatures recorded

The manifest records draft signatures for translation, summarization, question
answering, language modeling, and ASR. They are explicitly marked
`draft_not_release_frozen`, and **the export computes no new model scores**.
The existing custom BLEU/chrF implementation is identified as custom and not
SacreBLEU. CrossSum ROUGE-L and XORQA exact-match/token-F1 are still
unimplemented; ASR corpus aggregation and empty-reference handling are not
frozen. Per-run denominators, exclusions, uncertainty, and source-stratum
reporting remain to be added before metric contracts can be frozen.

## Validation

- Source v0.1 contract validator: pass, eight views / 12,622 rows, zero errors;
  all 112 local ASR audio hashes verified.
- Adapter tests: **7 passed**, covering raw/scoring separation, explicit raw
  text absence, overlay linkage, ASR privacy, row retention, deterministic
  output, draft metric signatures, and output-hash drift detection.
- At export time, the full suite passed **508 tests**. After Phase 4 runner
  changes, the current full suite passes **519 tests**.
- Python compilation and `git diff --check`: passed.
- Rebuilding the export produced the same manifest hash.
- Output is under the ignored `data/processed/` tree; it was not uploaded or
  committed.

## Remaining phases 1–3 work

**Phase 1 — inventory/reproducibility:** the builder, final release audit,
lineage audit, local runtime preflight, and report reconciliation are recorded.
The remaining reproducibility limitation is that the workspace is dirty, so
the input state is not a clean commit-pinned snapshot. The historical ASR test
aggregates also remain unpaired where their reports omit the relevant test
manifest hashes; those scores stay historical and are not re-evaluated here.

**Phase 2 — split/exposure:** the exact XORQA overlap overlay and four near-pair
adjudications are recorded. Full source-family assignment across all benchmark
records, semantic/paraphrase and cross-language duplicate checks, grouped
diagnostic policy, and upstream checkpoint-exposure evidence remain open.
Unknown VAANI/SraVaani and Meta exposure must remain explicitly unknown where
example-level training IDs are unavailable.

**Phase 3 — v0.2 contract:** the local adapter/export and integrity checks are
implemented. Still open are raw-text recovery where original source values can
be linked, final task-specific metric and denominator policies, edge-case
tests and implementations for CrossSum/QA, run-level uncertainty/source-strata
reports, and task cards that distinguish local-only from public fields. Rights
clearance remains a separate release gate.

## Next work item

Freeze and implement the task metric contracts before new model comparisons:
start with explicit corpus WER/CER aggregation and empty-reference handling,
then implement/test the CrossSum and XORQA signatures, with Unicode,
punctuation, whitespace, and multi-reference edge cases. Keep all work on
development data; do not refresh historical test scores.
