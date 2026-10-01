# Public dataset schema

The schema has a common envelope and configuration-specific payload fields.
The envelope makes basic filtering consistent; it does not replace detailed
provenance or turn an upstream source's terms into one corpus-wide license.

## Common record envelope

Current envelope version: **1.0.0** (recorded in each package manifest).

The v2.2.0 corpus schema adds these fields to every corpus record. The speech
builders emit the same envelope when the Parquet package is regenerated.
Existing source-specific rights, license, quality, transcript, and provenance
columns remain intact.

| Field | Type | Meaning |
| --- | --- | --- |
| `rights_status` | string | Exact recorded status, such as `licensed`, `rights_pending`, `metadata_only; no license asserted for underlying work`, or `resolve_via_record_and_source_join`. Inspect linked provenance for the applicable item-level terms. |
| `reuse_scope` | string | Plain-language filter aid: attribution, noncommercial/share-alike, source-specific policy, metadata-only, pending, or resolve through the source join. It is not independent legal advice. |
| `license_labels` | list of strings | License IDs or source license labels found on the record or its cited rights basis. Empty means no label was recorded, not that the material is unrestricted. |
| `quality_status` | string | Review state for the record's primary payload. Values preserve provider status where available; common fallbacks include `machine_generated_unreviewed`, `automated_quality_assessed_unreviewed`, `provenance_metadata_only`, and `not_reviewed`. |
| `record_quality_flags` | list of strings | Machine-readable quality or review signals copied from source fields, plus explicit redaction/draft signals where applicable. |

The envelope is deliberately conservative: unknown or missing terms stay
`not_assessed`; public visibility does not imply permission. The details in
`provenance`, `public_rights_basis`, `source_license`, `transcript_review_status`,
and other source-specific fields remain the evidence of record.

## Configuration payloads

| Config | Main fields |
| --- | --- |
| `text` | `id`, `text`, `language`, `script`, `split`, `quality_tiers`, `quality_flags`, `provenance`, `public_rights_basis` |
| `lexicon` | `form`, `glosses`, `graphemes`, `pronunciation_status`, `dialect_quality`, source hashes and provenance |
| `asr` | `audio_sha256`, `transcript`, `source`, `district`, `split`, transcript review and quality fields |
| `sravaani_drafts` | `audio_sha256`, `transcript`, machine model/revision, review and confidence evidence; nested evidence may be compact JSON strings |
| `catalog` | stable content hashes, optional `text`, redaction state, `redistribution_status`, commercial-use/share-alike signals, quality and provenance |
| `instructions` | `task`, `instruction`, `response`, acceptable response set, split, source and rights basis |
| `geography`, `historical_terms`, `literary_people`, `literary_works`, `popular_songs`, `university_research` | Factual/bibliographic projections, source citations, `record_scope`, omissions, and quality metadata; a citation does not include the underlying expressive work |
| `record_index` | content-free record reference, `record_family`, rights/quality summary, and source reference IDs |
| `source_catalog` | deduplicated source details, attribution, source-specific terms, and quality/provenance status |
| `record_sources` | record/source join IDs; resolve rights and reuse through the linked record and source |

## Speech schema

The separate speech dataset has two configs: `garhwali_speech` (VAANI-derived
audio and transcript metadata) and `meta_omnilingual` (the Meta subset). Both
carry `rights_status`, `reuse_scope`, `license_labels`, `quality_status`, and
`record_quality_flags` in the regenerated schema. They retain the audio hash,
source license, transcript source/review status, split, and split-safety fields.
The VAANI provider transcript is not necessarily adjudicated; SraVaani output is
a separate machine draft. Meta examples are upstream references that have not
received native-speaker adjudication.

For current counts and runnable examples, use the card for the selected
dataset/configuration. The corpus card links to the full developer quick start.
