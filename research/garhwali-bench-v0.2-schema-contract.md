# GarhwaliBench v0.2 schema contract (draft)

**Draft date:** 2026-09-26

**Status:** validation baseline passed; migration and metric contracts remain open.
**Purpose:** specify the record, split, provenance, rights, and reporting fields
that a versioned v0.2 benchmark export must carry. This contract does not alter
the v0.1 candidate files or authorize public release.

## Contract principles

1. Preserve the original source row and its raw text/audio references. Scoring
normalization is a separate, versioned value; it never overwrites raw data.
2. Keep task membership, score eligibility, training eligibility, rights, and
language-quality status as separate fields. A row remains in the dataset when
its use is restricted; the eligibility label records the intended use.
3. Publicly available benchmark references are an **open development/test
choice**, not blind evaluation. Previously scored public test items are
historical and cannot support a final independent-accuracy claim.
4. Keep rights evidence at source/component level. A declared upstream license
is metadata, not automatic clearance of every embedded work or component.
5. Keep speaker IDs, local audio paths, and row-level private review data in
local-only artifacts. Public cards may expose counts and hashes, not those
fields.

## Canonical record shape proposed for v0.2

Every exported record will carry the following logical fields. Task-specific
payloads may differ, but these fields must not be lost during conversion.

| Field group | Required values |
| --- | --- |
| Identity | `schema_version`, `benchmark_id`, `task`, stable `example_id`, `split`, and `source_split` when the source has its own partitions |
| Language | ISO 639-3 label, declared script, observed script profile, and dialect evidence state; unknown values stay explicit |
| Payload | Task-specific input and reference fields; raw source text preserved separately from normalized/scoring text |
| Text processing | `text_raw`, `text_scoring`, `normalizer_id`, and hashes for both values; ASR also keeps audio hash and reference hash |
| Provenance | Source dataset/work ID, row/document/page locator where available, source snapshot hash, extraction/transformation version, and attribution |
| Rights | `rights_status`, license declaration and URL, component-rights state, and redistribution state; pending/unknown remain valid values but do not pass a release gate |
| Quality | Automated screen result, native-review state, dialect-review state, and unresolved flags; automated status cannot be promoted to human-reviewed |
| Usage | Original source split, prior scoring/use history, training eligibility, dev-selection eligibility, open-diagnostic eligibility, and independent-claim eligibility |
| Lineage | Exact/near duplicate family IDs, source-context family ID, and an overlap-label artifact/hash when one exists |

The v0.2 export will use task adapters rather than forcing every task into a
single text shape:

- **Translation:** source-language input, Garhwali reference, direction, and
  source/target language labels.
- **Summarization:** source document, Garhwali summary, source-work grouping,
  and document-level split ID.
- **Question answering/retrieval:** question, context/document ID, answerability,
  reference answer(s), source-context family, and fixed candidate-corpus ID for
  retrieval metrics.
- **Language modeling/generation:** raw and scoring Garhwali text plus the
  frozen train/dev/test assignment and source-family ID.
- **ASR:** audio content hash, local-only audio locator, reference transcript,
  transcript hash, speaker group, duration, and audio-quality fields.
- **TTS:** paired text/audio IDs and speaker-group lineage; no quality score is
  allowed without listener evidence.

## Eligibility vocabulary

The following are proposed use labels, not deletion instructions:

| Label | Meaning |
| --- | --- |
| `train_candidate` | Eligible only for the named training experiment after rights and split checks |
| `dev_select` | May guide checkpoint, prompt, or hyperparameter selection |
| `open_test_historical` | Public or previously scored test data; diagnostic/historical only |
| `open_diagnostic_only_split_overlap` | Retained row whose exact question/context family spans source splits; not independent source-generalization evidence |
| `internal_auto_candidate` | Automated Garhwali candidate; not native-reviewed gold |
| `not_release_cleared` | Retained locally, but a compatible redistribution basis is not established |
| `unknown_exposure` | No adequate evidence about checkpoint/pretraining exposure |

Rights and use eligibility are orthogonal. `not_release_cleared` does not mean
the linguistic value is unusable; `open_diagnostic_only_split_overlap` does not
remove text from the corpus.

## Task and metric report contract

Every run report must contain the exact benchmark, split, and source-context
overlay hashes; ordered example IDs; model and revision/checkpoint hash; prompt
or decoder configuration hash where used; code revision; metric/normalizer ID;
seed; environment/device; start/end/status; prediction hash; evaluated and
excluded denominators; coverage; source/language/script strata; and limitations.

The task metric definitions are not frozen by this draft. v0.2 must pin them
before new model comparisons:

- ASR: corpus WER/CER from summed errors/reference units, plus per-record
  distribution and empty-reference policy.
- Translation/generation: exact normalizer and BLEU/chrF implementation/signature;
  existing custom scores must not be relabeled as a different library's metric.
- Retrieval: fixed candidate corpus hash, Recall@k/MRR/nDCG definitions, tie and
  no-answer handling, and source-group-aware uncertainty.
- Question answering: exact-match/token-F1 normalization, answerability and
  empty-reference policy, with source-context groups used for clustered
  uncertainty.
- Language modeling: explicit tokenizer/model identity and loss denominator;
  perplexity from different tokenizers is not a direct league-table comparison.

The open development package and any future final-claim protocol must be
separate. No current public split should be described as blind.

## Current v0.1 asset baseline

The dependency-free validator is
[`validate_benchmark_v02.py`](../scripts/validate_benchmark_v02.py). It reads
the existing v0.1 manifest, validates source records and local audio hashes,
and writes ignored local output under
`data/processed/evaluation/garhwali_bench/v0.2_contract_validation.*`.

The current manifest SHA-256 is
`ce93c7c1c06680d04bf9b861cbfdf8ca11b6cf9bf1968ba9cf19687655b8865b`. The
validation report passes with **zero structural/integrity errors** across
eight views and 12,622 rows:

| View | Count | Split counts |
| --- | ---: | --- |
| FLORES | 2,009 | dev 997; test 1,012 |
| CrossSum | 699 | train 99; dev 100; test 500 |
| XORQA | 1,139 | train 100; dev 500; test 539 |
| Internal Garhwali text candidate | 398 | test 398 |
| Internal VAANI ASR candidate | 112 | test 112 |
| Recommended text train | 7,490 | train 7,490 |
| Recommended text validation | 377 | validation 377 |
| Recommended text test | 398 | test 398 |

All external task rows have unique IDs, nonempty required task references,
NFC-trimmed normalized primary text whose hash matches, and explicit source,
rights/license, and use metadata. There are no malformed-surrogate strings or
empty XORQA answer lists in this snapshot. The script-profile checker is a
Unicode-name heuristic: it sees mixed-script content in 85 FLORES, 354 CrossSum,
and 1 XORQA row, but does not reject these rows because the declared script is
the primary Garhwali script and code-mixing may be legitimate.

All **112/112** local ASR audio paths exist and match their recorded audio hash;
the view contains 19 distinct speaker IDs. Speaker IDs and local paths remain
local-only. The overlap usage overlay has SHA-256
`0569329afd721a2b8c2e525481048705fbde4ec6ae4fd949df2ccf6789f1273f`; it marks
62 XORQA rows for open diagnostics only because exact source contexts cross
original splits. All source rows remain present.

The generated validation JSON has SHA-256
`2e0f2dc6286a6a96f8043ce1c6ef6d09ae1987f3ff486974c7cb32e828d4c32c`.

## Current local v0.2 draft adapter

[`build_benchmark_v02.py`](../scripts/build_benchmark_v02.py) now produces a
deterministic, ignored, local-only draft at
`data/processed/evaluation/garhwali_bench/v0.2-draft/`. It adapts all eight
views and 12,622 rows, keeps each full v0.1 row under `legacy_record`, carries
the XORQA usage overlay, preserves source/scoring values separately where
available, records normalizer and draft metric IDs, and verifies output file
hashes, counts, and retained-row flags. The output manifest SHA-256 is
`0352298d966d4ebcf1540bad913db283bc1cb9e69dfd85b7ea9e5b4fd8525fd1`.

Rows from the internal-text and recommended-text views do not carry a verified
raw-original value in v0.1, so `text_raw` is null and the available field is
identified as `text_source`. The adapter does not claim that any row is
redistribution-cleared. The ASR view carries local audio and speaker locators;
therefore the generated package is local-only and cannot be uploaded as-is.
Metric entries are explicit draft signatures, not release-frozen protocols;
the export computes no new model scores.

## Migration blockers before v0.2 can be frozen

1. Recover original raw text for legacy internal/recommended rows only where
   their row-level provenance can verify an exact source value. Keep unresolved
   raw values explicit instead of reconstructing by guess.
2. Extend the current exact XORQA overlay to full source-family/group coverage;
   semantic, paraphrase, and cross-language relationships remain unassessed.
3. Freeze task-specific metric/normalizer signatures, denominators,
   empty-reference policy, exclusions, and source-grouped uncertainty. The
   adapter records draft signatures only; CrossSum ROUGE-L and XORQA
   exact-match/token-F1 still need implementations and edge-case tests.
4. Keep internal text rights status explicit at row level; this schema work does
   not clear any source for redistribution.
5. Preserve mixed-script rows while exposing script profile and any review
   status; do not equate a Devanagari declaration with a native-language pass.
6. Add metric-run reports with ordered IDs, denominators, exclusions, coverage,
   source strata, uncertainty, and prediction/configuration hashes.
7. Add public/local field cards and run the release gate only after rights and
   split/exposure decisions. Semantic equivalence and model exposure remain
   `unknown` where not tested.

Validation command:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/validate_benchmark_v02.py
```
