# v0.2.2 fast-tracked text-view audit

Updated 1 October 2026. The additive v0.2.2 corpus release is public at
[Hub commit `b9d0538`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b9d0538b5b4dda3be73e5ae33b279b371ef75c3f).
The local package passed preflight before upload; the release adds the new
versioned config while retaining prior release files.

## What changed

The candidate adds `text_expansion/train`, a separate, train-only view of
**1,647 Garhwali strings** already collected in the catalog. This makes
eligible catalog text easier to load as a training subset. It does **not** add
1,647 newly discovered source texts, and those rows still also appear in the
catalog inventory. The overall exact-unique collected text inventory remains
32,072 values.

The additions pass the pipeline's strict automated quality tier, have a
recorded public-rights basis, and pass the current automated training
recommendation rule. Their row-level labels and source terms remain
authoritative. This is not a legal opinion, native-speaker validation, or a
claim that the texts are linguistically correct. Their recorded licenses vary,
including attribution and share-alike requirements.

## Selection and overlap checks

The builder selects non-empty catalog rows that are tagged as Garhwali
candidates, have an exact source-language set of `gbm`, carry the
`strict_gold_candidate` automated tier, and pass the project's recorded
rights-basis filter. It then excludes existing IDs, normalized text matches,
validation/test source-record IDs, and duplicates within the expansion. Text
normalization uses NFKC, Unicode case folding, and retention of alphanumeric
characters, consistent with the project's release audit.

| Check | Result |
| --- | ---: |
| Strict-tier, rights-basis, Garhwali source candidates before exclusions | 5,051 |
| Excluded because an ID already exists in main text | 3,205 |
| Excluded for validation/test source-record overlap | 174 |
| Excluded as normalized duplicate of existing text-bearing views | 23 |
| Excluded as within-expansion normalized duplicate | 2 |
| Included in `text_expansion/train` | **1,647** |
| Empty text, repeated normalized text, or missing rights-basis rows included | **0** |
| Normalized exact overlaps with `text`, `asr`, `sravaani_drafts`, `instructions`, or `lexicon` | **0** |
| Source-record-ID overlaps with frozen benchmark validation/test | **0** |

The source-record overlap check does not establish source-page-family
independence. A shared source page or related passage may still warrant a
future document-level leakage audit, so this config is not an independent
evaluation set. It is explicitly labeled `train` only.

## Candidate package impact

The regenerated v0.2.2 candidate contains **826,986 package-view rows**:
164,141 content/config rows and 662,845 reference/join rows. The counts overlap
by design and are not unique-example counts. Relative to v0.2.1, the candidate
adds a named, filterable text view without changing the existing frozen
`text` train/validation/test split assignments. The candidate also retains the
full 32,072-row text catalog; 19,466 values remain redacted from the
rights-filtered public catalog content.

The package preflight reports zero errors, zero rows without
config-specific source traceability, zero deleted/mutated rows, and zero
within-config duplicate identities. See
[`huggingface-quality-candidate-preflight-2026-10-01.json`](huggingface-quality-candidate-preflight-2026-10-01.json)
for per-config counts and hashes, and
[`huggingface-dataset-quality-roadmap.md`](huggingface-dataset-quality-roadmap.md)
for remaining release gates.
