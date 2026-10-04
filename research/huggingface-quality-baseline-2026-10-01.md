# Hugging Face Dataset Quality Baseline — 2026-10-01

**Package checked:** local public v0.2.1 corpus package at
`data/huggingface/garhwali-language-lab/`
**Validator:** `scripts/validate_hf_package_cloud.py`
**Hub corpus revision:** `7cae908`
**Result:** passed; zero errors; `records_deleted_or_mutated=0`.

This is an engineering and metadata baseline. Passing these checks does not
verify Garhwali spelling, meaning, dialect, transcription accuracy, or
commercial reuse rights.

## Counts by grain

| Measure | Baseline | Meaning |
| --- | ---: | --- |
| Total package rows | 821,083 | Sum of all configs; overlapping views included |
| Content/config rows | 162,494 | Text, lexicon, ASR, drafts, instructions, catalog, and knowledge views; still not all unique |
| Reference and join rows | 658,589 | `record_index` 300,915 + `record_sources` 352,765 + `source_catalog` 4,909 |
| Public `text` config | 18,949 | 17,289 train / 895 validation / 765 test |
| Lexicon | 1,493 | Word forms and gloss/provenance fields; native review deferred |
| Instructions | 3,228 | Task-oriented examples; source and review status vary |
| Catalog | 32,072 | 12,606 content values exposed under recorded bases; 19,466 full text values redacted from the public table |
| Factual/bibliographic knowledge records | 216 | Metadata projections, not full books, lyrics, or poems |
| Public speech rows | 113,363 | 113,350 unique audio hashes; 154.645 hours across VAANI and Meta |
| VAANI provider transcripts | 5,894 | Provider-supplied transcript rows; not native-adjudicated |
| Strict speaker-disjoint ASR view | 2,002 | 1,621 train / 269 validation / 112 test |
| SraVaani draft source rows | 104,542 | 104,508 non-empty raw outputs; eight duplicate audio hashes carry identical drafts |
| SraVaani packaged draft rows | 104,534 | One row per unique audio hash; 34 empty outputs remain visible, leaving 104,500 non-empty unique-hash rows |

The raw-to-packaged draft arithmetic reconciles: 104,542 source rows minus
eight repeated audio hashes gives 104,534 packaged rows; 34 empty transcripts
leave 104,500 non-empty packaged rows. The 104,508 figure is the non-empty
source-row count. These are different grains, not conflicting dataset sizes.

## Integrity and metadata checks

- The release preflight passed with zero package errors, zero deleted/mutated
  rows, zero stable-identity crossings between train/validation/test within
  `text`, `asr`, and `instructions`, and zero normalized instruction-prompt
  crossings within the instruction splits.
- The preflight found zero missing identities and zero duplicate identities
  within each config. This does not detect every cross-config or parent-document
  overlap.
- A direct package scan found all five v1.0.0 envelope fields present and
  non-null for all 821,083 rows. The package validator enforces field types and
  non-empty strings; optional list values may correctly be empty.
- The package contains 34 empty SraVaani hypotheses. They are preserved for
  audit, but are not usable transcript text and must be excluded from any
  text-supervision view.
- Exact within-config identity checks do not prove cross-config or
  source-document isolation. Prior model-lineage and overlap audits report
  cross-view/source overlaps; those must remain visible in task-specific
  eligibility filters.

## Metrics that need clearer definitions

The clarified metrics from the 1 October scorecard run are:

| Metric | Rows | Definition |
| --- | ---: | --- |
| Non-empty `quality_status` label | 821,083 | Status-label coverage; does not mean reviewed or correct |
| Detailed quality-field key present | 157,773 | At least one of six configured keys exists, even if its value is empty |
| Detailed quality field has a non-empty value | 138,362 | At least one configured field contains a non-empty value; not a pass/review score |
| Generic `provenance`/`sources` array present | 55,958 | Does not include alternate source pointers in ASR or reference configs |

The legacy `rows_with_quality_metadata` remains as an alias for key presence so
older report readers continue to work. It must not be reported as
“157,773 quality-reviewed records.” These totals span mixed content and
reference grains, so cross-config quality percentages would be misleading.

The legacy `rows_with_provenance` is **55,958** under the validator's narrow
rule: a non-empty `provenance` or `sources` array. It is not complete source
traceability coverage. Speech rows use audio hashes and upstream `source`
fields, while archive index and source links use reference IDs. Phase 1 will
add explicitly defined, config-aware measurements while preserving this
backward-compatible count.

## Phase 0 decision

The package is structurally usable and its major content views are countable,
but one 821k headline obscures the much smaller content and supervised subsets.
The next work should improve config-aware source traceability and quality evidence,
then resolve cross-view overlap and produce use-specific clean views. New
ingestion should be measured by net-new, traceable, use-eligible content rather
than extracted row totals.

## Published v0.2.2 quality release — 2026-10-01

The additive release is published at [Hub commit `b9d0538`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b9d0538b5b4dda3be73e5ae33b279b371ef75c3f). It
preserves existing v0.2.1 configs and adds a separate train-only
`text_expansion` config. The 1,647 rows are existing catalog values newly
surfaced as a filtered training view, not newly ingested source texts. They
have no normalized exact duplicates in text, provider ASR, machine drafts,
instructions/responses, or lexicon forms and no frozen benchmark validation/
test source-record overlap. The per-config machine-readable preflight is
[`huggingface-quality-candidate-preflight-2026-10-01.json`](huggingface-quality-candidate-preflight-2026-10-01.json).

| Measure | Published release | Comparison / meaning |
| --- | ---: | --- |
| Total package rows | 826,986 | 164,141 content/config + 662,845 reference/join rows; overlapping views |
| Content/config rows | 164,141 | Includes 1,647 new-to-text-view catalog values; not new source ingestion |
| Reference/join rows | 662,845 | `record_index` 302,532 + `source_catalog` 5,019 + `record_sources` 355,294 |
| Source catalog | 5,019 | +110 source-reference rows versus frozen v0.2.1; social records resolve to item URLs |
| Record/source joins | 355,294 | +2,529 links versus frozen baseline, including transcription-part and expansion provenance |
| Config/split views | 22 | Every row was assessed under its config-specific locator rule |
| Rows with source traceability | 826,986 / 826,986 | 100%; locator presence only, not rights or correctness |
| Catalog rows with source traceability | 32,072 / 32,072 | No missing item/source locator under the scorecard rule |
| Source references with traceability | 5,019 / 5,019 | No unresolved locator row in this package |

The published package records rights-status, reuse-scope, license-label,
and rights-basis-field counts for every config/split. For `catalog/train`, the
32,072 rows are labeled as 19,466 `rights_pending`, 12,258 `rights_cleared`,
134 `rights_cleared_noncommercial_sharealike`, 198
`reproduced_under_source_policy`, and 16 `individual_word_fact`. These are the
export's recorded categories, not a blanket license: 19,466 text values remain
redacted in the public content table. The `text_expansion` view has 1,647
rows; all meet the automated current training-recommendation rule and carry
strict-tier labels. This is not evidence of native-verified correctness. The
all-data source set remains local.

The 34 empty SraVaani outputs remain visible as audit rows and are excluded
from usable draft-text counts. Across the package, status labels cover all
826,986 rows, while detailed quality keys and non-empty detail values are
159,420 and 140,009; neither count establishes linguistic review or accuracy.
Preflight passes with zero errors and zero deleted or mutated records. The new
view has zero normalized text overlap across text, ASR, machine drafts,
instructions/responses, and lexicon forms, and zero frozen benchmark
validation/test source-record overlap. Source-page-family deduplication and
broader rights reconciliation remain active. See the roadmap and
[`huggingface-text-expansion-audit-2026-10-01.md`](huggingface-text-expansion-audit-2026-10-01.md).
