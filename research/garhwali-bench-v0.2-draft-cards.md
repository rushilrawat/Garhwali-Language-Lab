# GarhwaliBench v0.2 draft cards — local review pack

- **Prepared:** 2026-09-29
- **Status:** local documentation draft; not a public benchmark release
- **Canonical draft:** `data/processed/evaluation/garhwali_bench/v0.2-draft/`
- **Manifest SHA-256:** `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`

This pack documents the candidate suite and current evidence without copying
benchmark example text, audio, speaker identifiers, or private local paths.
The adapter reports `public_upload_allowed=false`. Upstream license labels are
recorded as declarations; they do not by themselves establish rights for every
embedded source component or this adapted package. Keep this pack local until
the source-specific rights and publication gates are resolved.
The current machine-readable count is reproducible with
[`audit_benchmark_v02_rights.py`](../scripts/audit_benchmark_v02_rights.py);
see the [component rights inventory](garhwali-bench-v0.2-rights-inventory-2026-09-29.md).

## Suite card

**Purpose.** Provide reproducible, task-specific diagnostics for Garhwali
language modeling, translation, summarization, question answering/retrieval,
and speech recognition. The suite supports development and error analysis; it
does not currently provide a single defensible model-accuracy number.

**Current size.** Eight views contain **14,703 view rows**: 3,847 external
IndicGenBench rows, 402 internal text evaluation rows, 112 internal VAANI ASR
rows, and the recommended text split of 9,486 train / 454 validation / 402
test. These are not unique examples: the internal-text view and recommended
text-test view intentionally mirror the same 402 records. The recommended
text split totals 10,342 rows. The current build added 2,077 rows relative to
the prior 8,265-row parent-safe candidate, retained all previous row IDs, and
did not move old rows across splits.

**Integrity.** The dependency-free validator reports eight assets, zero
structural/integrity errors, and 112/112 matching local ASR audio hashes. All
10,342 recommended text IDs map to source segments; their 3,246 parent-text
hashes and 3,072 duplicate-component IDs stay within a single split. The
underlying `all_segments.jsonl` SHA-256 is
`c77b54aa8ec7a550068b65ef2d07d65cfe8cfe65ae70c617890ae80246d5f429`. A coarser
check over 11 ingestion-file pointers finds nine shared across splits; these
files contain multiple source works and are not document IDs, so this does not
prove document-level leakage or source-work independence. This does not test
paraphrase equivalence or pretraining exposure. One exact XORQA primary-text group remains across upstream train/dev;
54 XORQA source-page families (134 records) cross upstream splits. A
review-only usage overlay labels 138 records for open diagnostics. Four
near-text pairs were reviewed and are same-split candidates. No row was deleted
or silently reassigned by these audits.

**Evaluation standing.** Current test references have prior scoring or
unresolved checkpoint exposure. **Independent-final eligibility is 0/5** for
language modeling, translation, retrieval, generation, and ASR. Native-language
review and dialect annotation remain deferred by project direction; cards do
not make native-validated or gold-benchmark claims.

**Reproduction.** From the repository root, after installing the project
environment:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/build_benchmark_v02.py
PYTHONPATH=scripts .venv/bin/python scripts/validate_benchmark_v02.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_benchmark_overlap_candidates.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_model_accuracy_lineage.py
```

Outputs under `data/processed/evaluation/` are generated, ignored local
artifacts. Compare output hashes and the manifest before interpreting any
scores. Do not use a previously scored test split for selection.

## Card 1 — Garhwali ↔ English translation (FLORES)

- **Task and intended use:** evaluate translation diagnostics between Garhwali
  and English; the current saved development work is Garhwali-to-English.
  Use development rows for error analysis and controlled selection only.
- **Data:** 2,009 rows: 997 dev and 1,012 test. Upstream source is Google
  IndicGenBench FLORES, attributed to Singh et al. (2024); pinned source files,
  revisions, and checksums are in the local manifest.
- **Declared terms:** CC BY-SA 4.0 is declared upstream. Component-level rights
  review remains required before redistribution; the adapter has not cleared
  any row for upload.
- **Metrics:** current historical work uses project custom add-one-smoothed
  corpus BLEU and custom corpus chrF2. These are not SacreBLEU scores. A future
  frozen run must pin direction, reference, normalizer, scorer hash, and row IDs.
- **Evidence:** saved predictions cover all 1,012 test rows, so test is
  historical-only. A saved 997-row dev translation-memory comparison against
  source-copy has BLEU delta +0.01892665 (paired record-bootstrap 95% CI
  +0.01411908 to +0.02385223) and chrF2 delta +0.23002697 (95% CI
  +0.22559907 to +0.23435906). The translation memory uses other dev targets;
  intervals are record-level and do not account for source clusters.
- **Limits:** FLORES lacks row-level source URLs in the local material, and
  exact text checks cannot rule out translation/paraphrase or model pretraining
  exposure. This is open, historical evidence, not blind generalization.
- **Release state:** local candidate; no public task payload or model claim is
  authorized by this card.

## Card 2 — English-to-Garhwali summarization (CrossSum)

- **Task and intended use:** generate Garhwali summaries from English source
  articles; current safe use is development and error-analysis planning.
- **Data:** 699 rows: 99 train, 100 dev, and 500 test. The local preflight found
  non-empty target summaries for all 100 dev rows. Exact source/target URL
  checks found no cross-split repeated URLs in this snapshot.
- **Source and terms:** Google IndicGenBench CrossSum, attributed to Singh et
  al. (2024); upstream declares CC BY-NC-SA 4.0. Embedded-source rights and
  the adapted package have not been cleared for redistribution.
- **Metrics:** the draft runner supports token ROUGE-L F1 and the project's
  custom chrF2, with explicit missing-reference exclusions. Metric signatures
  are not release-frozen; report denominators and source-group uncertainty.
- **Evidence/standing:** no local prediction match is known for the 500-row
  test, but upstream checkpoint exposure is unknown. Therefore test is
  unresolved, not blind. No current CrossSum model score is claimed here.
- **Limits:** URL grouping is not proof of independent source documents, and
  automated script checks do not verify summary correctness or Garhwali fluency.
- **Release state:** local candidate; rights and exposure gates remain open.

## Card 3 — Garhwali question answering and retrieval (XORQA)

- **Task and intended use:** answer Garhwali questions from evidence passages
  and evaluate retrieval against a fixed candidate corpus. Separate answer
  generation from retrieval scores.
- **Data:** 1,139 rows: 100 train, 500 dev, and 539 test. One exact primary-text
  group repeats between upstream train/dev. The source-page audit found 54
  page families / 134 rows crossing upstream splits; 32 have distinct
  passages. The retained local overlay flags 138 unique rows as open-diagnostic
  for independent source-generalization claims.
- **Source and terms:** Google IndicGenBench XORQA, attributed to Singh et al.
  (2024); upstream declares MIT. Component-level redistribution review is
  still required.
- **Metrics/evidence:** QA scoring uses normalized exact match and token F1;
  records without a target-language reference are retained but excluded and
  reported. One of 500 dev rows lacks a non-empty Garhwali target reference.
  Saved 500-query BM25 dev results are 0.8% word and 1.0% character Recall@10;
  the English-oracle control is 85.2%. A paired source-page-cluster bootstrap
  for character-minus-word Recall@10 is +0.2 percentage points (95% CI 0.0–0.6),
  conditional on the fixed all-split 1,059-document retrieval corpus. Saved
  test predictions cover all 539 rows; test is historical-only.
- **Limits:** retrieval intervals condition on a fixed corpus that includes
  all source splits. Page reuse and short cross-language answer strings remain
  diagnostic candidates, not automatically adjudicated leakage. No claim of
  independent QA/retrieval accuracy is supported.
- **Release state:** local candidate; retain all rows and usage labels.

## Card 4 — Garhwali text modeling candidate

- **Task and intended use:** compare character/token language-modeling and text
  representation baselines. This card covers a strict automated Garhwali text
  candidate, not a validated lexicon or native-reviewed language test.
- **Data:** recommended split has 9,486 train, 454 validation, and 402 test
  records. A separate internal evaluation view contains the same 402 test
  records; the two views are intentional mirrors, not 804 unique texts. The
  current 402-row test matches the recommended test IDs/text exactly.
- **Metrics/evidence:** a dependency-free add-one-smoothed character bigram,
  trained on 9,486 rows, scores perplexity **14.397995**, character OOV rate
  0.0, vocabulary 123, and 38,304 boundary-inclusive evaluation characters.
  The score is matched to the current text-test row-set hash by the 2026-09-29
  lineage audit; it is therefore historical/open, not independent-final.
- **Split/quality limits:** all rows map to source segments, with zero parent
  text-hash and duplicate-component crossings in the recommended split. Coarse
  collection-file pointers cross splits and do not establish source-work
  independence. Four near-text
  candidates were reviewed as same-split. Semantic paraphrases, upstream
  checkpoint exposure, OCR quality, and native correctness are not established.
  Raw source text and row-level rights are not fully recoverable/cleared in the
  legacy benchmark view.
- **Release state:** local candidate only; native-speaker and dialect review
  are deferred, and no language-quality score is claimed.

## Card 5 — Garhwali ASR candidate

- **Task and intended use:** speech recognition diagnostics on the fixed VAANI
  Garhwali evaluation subset. Keep model selection on validation; the test is
  already used and must not be retuned against.
- **Data:** 112 test utterances and 19 speaker IDs. Local audio locators and
  speaker identifiers are private/local-only. All 112 audio hashes match the
  saved evaluation manifest, and the fixed ASR test is speaker-disjoint from
  the configured base ASR training/validation split.
- **Evidence:** RNNT beam size 8 was selected on validation (WER 43.253%, CER
  18.919%; greedy WER 43.454%, CER 18.948%). Its historical test is WER
  42.761%, CER 17.410%. Paired speaker-cluster intervals versus base include
  zero: WER delta +0.000 percentage points (95% CI −0.583 to +0.656), CER
  −0.196 (−0.391 to +0.000). The 61-trial and expanded-human models also have
  test intervals including zero; they are not promoted.
- **Metric runner:** the shared benchmark scorer now emits pooled and
  per-record WER/CER and fingerprints its ASR metric code in each run manifest.
  Its 269-row saved-validation check exactly reproduced the historical
  SraVaani aggregate; see the [integration report](asr-corpus-metric-integration-2026-09-29.md).
- **Limitations:** SraVaani reports broad VAANI pretraining/fine-tuning exposure
  without example-level IDs, so exact upstream overlap is unknown. The broader
  experimental ASR views also have train/eval audio overlap; do not transfer
  this candidate's split-safe statement to those views. Audio, speaker data,
  and training identities are not included in this card.
- **Release state:** local evaluation only; no audio/transcript package is
  approved for upload by this benchmark draft.

## Card 6 — Suite release and maintenance

- **Rights:** the adapter preserves declared licenses and source metadata but
  sets `public_upload_allowed=false`; it does not adjudicate source-component
  rights. No benchmark values should be uploaded from this draft as a shortcut.
- **Reproducibility:** retain the source manifest, view hashes, script/code
  revision, model/checkpoint and decoder configuration, ordered IDs, metric
  normalizer, denominators, exclusions, and output hash for every run. Compare
  with the current manifest before using a historical score.
- **Versioning:** any changed rows, split assignments, references, normalizer,
  metric, or task definitions require a new benchmark version or an explicit
  additive revision with regression evidence. Never overwrite a historical
  release snapshot.
- **Maintenance:** after each source update, rebuild all views, exact and
  supported near-duplicate scans, parent/source-family split checks, usage
  labels, contract validation, and row-retention comparisons; update the
  roadmap, issue log, eligibility report, task cards, and release index.
- **Current decision:** keep the benchmark local and draft. 0/5 task areas are
  independent-final-eligible. Existing task-card documentation is complete as
  a review aid; public release remains blocked by rights, exposure, contract,
  and reproducibility gates.

## Change record

| Date | Change |
| --- | --- |
| 2026-09-29 | Created six local review cards from the current 14,703-row draft, updated split/lineage hashes, and verified aggregate-score history. No data payload copied; no model inference, upload, or paid job run. |
| 2026-09-29 | Refreshed the draft manifest to include the tested corpus WER/CER contract. The package remains local-only with no benchmark payload upload. |
