# GarhwaliBench v0.2 schema contract (draft)

**Updated:** 2026-09-30

**Status:** eight-view validation passes; task-specific scorers exist for QA, summarization, translation, retrieval, ASR, and generation. The shared runner emits corpus and per-record ASR WER/CER with explicit empty-reference policy, and validation-only generation EM/chrF2 plus output diagnostics. Full release review and independent/native evidence remain open.
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
| Lineage | Exact/near duplicate family IDs, source-context and source-page family IDs where available, and an overlap-label artifact/hash when one exists |

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

### Implemented metric behavior (2026-09-27)

[`scripts/benchmark_metrics.py`](../scripts/benchmark_metrics.py) implements
dependency-free QA and summary metrics. Their versioned definitions are:

- **Normalization:** Unicode NFC, case-folding, Unicode punctuation/symbols
  replaced with spaces, then whitespace collapse. Letters, combining marks,
  and digits are preserved; there is no transliteration, stemming, or
  English-only article removal.
- **Tokenization and aggregation:** split on Unicode whitespace. For each row,
  take the maximum metric over its non-empty reference alternatives, then
  macro-average across rows. Report requested/scored rows, reference counts,
  multi-reference rows, empty-reference alternatives, and empty predictions.
- **QA:** exact match and multiset token-overlap F1. A blank model prediction
  scores zero and remains in the denominator. The metric function rejects a
  row with no non-empty reference. The task runner instead excludes that row
  from the metric denominator, lists its ID and reason, and retains its
  prediction; this does not imply a no-answer label. Explicit no-answer scoring
  is unsupported until the benchmark schema represents answerability.
- **Summarization:** token-level ROUGE-L F1 using longest-common-subsequence
  precision and recall. Blank hypotheses score zero and remain in the
  denominator; the task runner explicitly reports and excludes rows with no
  non-empty reference while retaining their predictions.

Metric IDs include `garhwali-qa-em-token-f1-v1`,
`garhwali-rouge-l-f1-v1`, `garhwali-custom-add1-bleu-v1`, and
`garhwali-custom-chrf2-v1`. The local scorer in
[`scripts/score_benchmark_predictions.py`](../scripts/score_benchmark_predictions.py)
binds CrossSum references to `source_example.summary` and XORQA references to
`source_example.translated_answers[*].text`. This follows the
[official IndicGenBench task definition](https://github.com/google-research-datasets/indic-gen-bench/blob/main/README.md):
CrossSum generates target-language summaries from English articles, while
XORQA provides both English and target-language answer spans. The scorer checks
exact row-ID coverage, defaults to development, requires an explicit flag for
historical test scoring, and writes the shared hash-linked run manifest.

Translation scoring is also bound to `source_example.target` for the
Garhwali-to-English FLORES task. It reuses the project's custom add-one-smoothed
corpus BLEU (orders 1-4) and custom corpus chrF2 (character orders 1-6,
beta=2); it does not claim SacreBLEU compatibility. CrossSum reports the
existing custom chrF2 alongside ROUGE-L. The metric signatures and normalizers
are recorded in the task run config.

**ASR corpus aggregation (2026-09-29):**
[`scripts/asr_metrics.py`](../scripts/asr_metrics.py) now exposes `score_corpus`.
It uses `asr-nfc-casefold-punctuation-symbol-space-v1`, computes corpus WER and
CER from summed edit counts divided by summed reference words/characters, and
returns both raw totals and denominators. A blank hypothesis is retained and
scored as deletions. A reference that normalizes to no words or characters is
excluded with its record ID and reason; the scorer fails if no valid reference
remains. This is the project contract `garhwali-asr-corpus-wer-v1` /
`garhwali-asr-corpus-cer-v1`; it does not make existing VAANI scores independent
or references native-validated.

The shared [`score_benchmark_predictions.py`](../scripts/score_benchmark_predictions.py)
runner accepts `--task asr`, uses `text.text_scoring` as the reference, enforces
exact row-ID coverage, and writes the scorer's corpus totals plus per-record
WER/CER into its report. Its run manifest fingerprints `asr_metrics.py` along
with the runner and shared metric modules. Per-record rates are descriptive;
the corpus metric remains the pooled edit-count rate.

**Generation scoring integration (2026-09-30):** the same runner accepts
`--task generation --split validation` for saved `instructions_v0.2`
predictions. It uses stable instruction hashes, scores exact match against any
accepted response plus multi-reference chrF2, reports repetition/empty/copy/
control-token diagnostics, and fingerprints the scoring implementation.
Three historical mT0 seed runs were reconciled to 130 exact current validation
rows; 190 of the current 320 validation rows have no saved prediction. The
scores are development diagnostics, not new inference or independent accuracy.
See the [generation integration report](generation-scoring-integration-2026-09-30.md).

**Retrieval contract already implemented:** the candidate corpus is the
deduplicated set of XORQA contexts, identified by the `passage_corpus_sha256`
in each run. Recall@k counts a query as retrieved only when its associated
context has a nonzero score and appears in the first k positions; MRR@10 is
zero for a null/out-of-top-10 rank. Ties are broken by stable document ID.
Reports keep the full query denominator and separately expose retrieved and
zero-score queries. Current BM25 reports use 1,059 fixed contexts and 500 dev
questions; this is a known benchmark collection, not unseen-corpus retrieval.
The implemented contract does not include nDCG, so nDCG claims must not be
reported until relevance grades and its scorer are defined.

The 2026-09-27 local reference preflight found 100/100 CrossSum dev rows with a
non-empty target summary. XORQA had 499/500 dev rows with a non-empty target
answer reference; one row has an English answer but no Garhwali reference. The
runner retains that row and its prediction, reports its exclusion, and scores
499 references. Existing 997-row translation-memory dev predictions were
re-scored through the shared scorer and matched their earlier custom metrics
exactly; no fresh neural-model predictions were run. The v0.2 contract still
needs:

- ASR: corpus scoring, per-record rates, exact ID checks, and empty-reference
  accounting are integrated and tested. Existing ASR model comparisons remain
  historical, with unknown upstream exposure and unreviewed references.
- Translation/generation: generation scoring is integrated for the saved
  validation outputs; broader metric/reference review remains open. Existing
  translation custom scores must not be relabeled as a different library's metric.
- Retrieval: the fixed candidate corpus hash, Recall@k/MRR, stable tie order, and
  zero-score policy are now documented. nDCG remains unsupported until graded
  relevance exists; source-cluster uncertainty remains an analysis layer.
- Question answering: source-context groups for clustered uncertainty and an
  explicit answerability field before no-answer scoring is supported.
- Language modeling: explicit tokenizer/model identity and loss denominator;
  perplexity from different tokenizers is not a direct league-table comparison.

The open development package and any future final-claim protocol must be
separate. No current public split should be described as blind.

## Current v0.1 asset baseline — refreshed 2026-09-29

The dependency-free validator is
[`validate_benchmark_v02.py`](../scripts/validate_benchmark_v02.py). It reads
the existing v0.1 manifest, validates source records and local audio hashes,
and writes ignored local output under
`data/processed/evaluation/garhwali_bench/v0.2_contract_validation.*`.

The source manifest SHA-256 is
`b833f81400d849ef80a14d2aae1b9803aab114dcac58f09e9e7b44de02b98b39`. The
fresh validation report passes with **zero structural/integrity errors** over
eight views and 14,703 rows. This is the sum of view rows, not unique examples:
the 402 internal-text records are intentionally mirrored by the recommended
test view.

| View | Count | Split counts |
| --- | ---: | --- |
| FLORES | 2,009 | dev 997; test 1,012 |
| CrossSum | 699 | train 99; dev 100; test 500 |
| XORQA | 1,139 | train 100; dev 500; test 539 |
| Internal Garhwali text candidate | 402 | test 402 |
| Internal VAANI ASR candidate | 112 | test 112 |
| Recommended text train | 9,486 | train 9,486 |
| Recommended text validation | 454 | validation 454 |
| Recommended text test | 402 | test 402 |

All external task rows have unique IDs, nonempty required task references,
NFC-trimmed normalized primary text whose hash matches, and explicit source,
rights/license, and use metadata. There are no malformed-surrogate strings or
empty XORQA answer lists in this snapshot. The script-profile checker is a
Unicode-name heuristic: it sees mixed-script content in 85 FLORES, 354 CrossSum,
and 1 XORQA row, but does not reject these rows because the declared script is
the primary Garhwali script and code-mixing may be legitimate.

All **112/112** local ASR audio paths exist and match their recorded audio hash;
the view contains 19 distinct speaker IDs. Speaker IDs and local paths remain
local-only. The 2026-09-28 source-page audit grouped all 1,139 XORQA title
locators into 993 page families. Fifty-four families (134 records) cross
original splits; 32 families contain distinct passages. The refreshed
review-only overlay flags 138 unique records, retaining each source row and
original split. Its JSON SHA-256 is
`deb49ebee8dc9b41de9ec0c87116b8934c14d2796dbb633aa4714b6f254def22`.
See [the nested-overlap review](benchmark-nested-overlap-review-2026-09-27.md)
and [the source-page family review](benchmark-source-page-families-2026-09-28.md)
for exact-field and source-lineage evidence and their limits.

The current validation JSON SHA-256 is
`170476050d38da75b4a21f55d50bd3fdfc76f0fd4f4d954be1dd0cef26a02583`. Older
counts and hashes in dated audit notes are historical snapshots, not current
adapter state.

## Current local v0.2 draft adapter

[`build_benchmark_v02.py`](../scripts/build_benchmark_v02.py) now produces a
deterministic, ignored, local-only draft at
`data/processed/evaluation/garhwali_bench/v0.2-draft/`. It adapts all eight
views and 14,703 rows, keeps each full v0.1 row under `legacy_record`, carries
the XORQA usage overlay, preserves source/scoring values separately where
available, records normalizer and draft metric IDs, and verifies output file
hashes, counts, and retained-row flags. The current adapter manifest SHA-256 is
`43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`; all eight
views and 14,703 rows validate with zero errors. XORQA rows carry exact
source-page family hashes alongside context hashes and the 138-row overlay.
The recommended text split is 9,486/454/402; every row from the prior 8,265-row
candidate remains present, with 2,077 added and none reassigned across splits.
All 10,342 recommended IDs map to source segments across 3,246 parent-text
hashes and 3,072 duplicate components, with zero parent-hash/component split
crossings (`all_segments.jsonl` SHA-256
`c77b54aa8ec7a550068b65ef2d07d65cfe8cfe65ae70c617890ae80246d5f429`). Nine of
11 coarse ingestion-file pointers span splits; those collection files can hold
multiple works and are not parent-document identities.
This build remains local-only and its manifest sets `public_upload_allowed=false`.

Rows from the internal-text and recommended-text views do not carry a verified
raw-original value in v0.1, so `text_raw` is null and the available field is
identified as `text_source`. The adapter does not claim that any row is
redistribution-cleared. The ASR view carries local audio and speaker locators;
therefore the generated package is local-only and cannot be uploaded as-is.
Metric entries are explicit draft signatures, not release-frozen protocols;
the export computes no new model scores.

The separate current character-bigram baseline did score the exact 402-row
text test (perplexity 14.397995), so the lineage audit labels that test
historical/open rather than independent-final. The local task-card pack is
[`garhwali-bench-v0.2-draft-cards.md`](garhwali-bench-v0.2-draft-cards.md).
It contains six documentation cards and aggregate evidence only, no benchmark
payload text, audio, speaker identifiers, or publication authorization.

## Migration blockers before v0.2 can be frozen

1. Recover original raw text for legacy internal/recommended rows only where
   their row-level provenance can verify an exact source value. Keep unresolved
   raw values explicit instead of reconstructing by guess.
2. Exact XORQA page-title and context reuse across splits is now linked in the
   draft overlay. Semantic, paraphrase, related-page, and cross-language
   relationships remain unassessed; source-family review in other tasks remains
   open.
3. Bind implemented QA, summarization, and translation metrics to verified task
   fields and run reports; freeze remaining task signatures, exclusions, and
   source-grouped uncertainty. Metric implementation does not
   establish reference correctness or produce model scores.
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
PYTHONPATH=scripts .venv/bin/python scripts/audit_benchmark_v02_rights.py
```
