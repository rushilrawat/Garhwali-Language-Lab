# Hugging Face release metric comparison: garhwali-language-lab-v0.2.5 to garhwali-language-lab-v0.2.6

Both package preflights passed under the same record schema, validator code, and metric definitions.

| Measure | Previous | Candidate | Change |
| --- | ---: | ---: | ---: |
| Config/split rows (overlapping views) | 827,450 | 945,926 | +118,476 |
| Config/split views | 25 | 26 | +1 |
| Records deleted or mutated | 0 | 0 | — |

These config/split totals overlap and are not unique-record or newly acquired-text counts.

## Per-view row counts

| Config / split | Previous | Candidate | Change |
| --- | ---: | ---: | ---: |
| `asr/test` | 112 | 112 | +0 |
| `asr/train` | 1,621 | 1,621 | +0 |
| `asr/validation` | 269 | 269 | +0 |
| `catalog/train` | 32,072 | 36,105 | +4,033 |
| `geography/train` | 50 | 50 | +0 |
| `historical_terms/train` | 36 | 36 | +0 |
| `instructions/test` | 186 | 186 | +0 |
| `instructions/train` | 2,686 | 2,686 | +0 |
| `instructions/validation` | 356 | 356 | +0 |
| `lexicon/train` | 1,493 | 1,493 | +0 |
| `literary_people/train` | 26 | 26 | +0 |
| `literary_works/train` | 66 | 66 | +0 |
| `popular_songs/train` | 30 | 30 | +0 |
| `record_index/train` | 302,641 | 355,537 | +52,896 |
| `record_sources/train` | 355,403 | 412,431 | +57,028 |
| `source_catalog/train` | 5,019 | 9,570 | +4,551 |
| `sravaani_drafts/train` | 104,534 | 104,534 | +0 |
| `text/source_overlap` | 1,308 | 1,305 | -3 |
| `text/test` | 765 | 745 | -20 |
| `text/train` | 15,981 | 15,664 | -317 |
| `text/validation` | 895 | 884 | -11 |
| `text_expansion/source_overlap` | 363 | 454 | +91 |
| `text_expansion/train` | 1,284 | 1,283 | -1 |
| `text_resources/source_overlap` | — | 190 | +190 |
| `text_resources/train` | 246 | 285 | +39 |
| `university_research/train` | 8 | 8 | +0 |

## Aggregate metric deltas

Counts below sum across config/split views. They are descriptive QA counts, not accuracy scores or unique records.

| Metric | Previous | Candidate | Change |
| --- | ---: | ---: | ---: |
| `empty_content` | 34 | 34 | +0 |
| `records` | 827,450 | 945,926 | +118,476 |
| `rows_with_factual_publication_basis` | 17 | 17 | +0 |
| `rows_with_license_label` | 168,209 | 168,229 | +20 |
| `rows_with_noncommercial_rights_basis` | 269 | 269 | +0 |
| `rows_with_nonempty_quality_evidence` | 140,255 | 144,604 | +4,349 |
| `rows_with_provenance` | 57,851 | 61,852 | +4,001 |
| `rows_with_provenance_array` | 57,851 | 61,852 | +4,001 |
| `rows_with_public_rights_basis` | 37,891 | 37,910 | +19 |
| `rows_with_quality_evidence_fields_present` | 159,666 | 163,667 | +4,001 |
| `rows_with_quality_metadata` | 159,666 | 163,667 | +4,001 |
| `rows_with_quality_status` | 827,450 | 945,926 | +118,476 |
| `rows_with_reuse_scope` | 827,450 | 945,926 | +118,476 |
| `rows_with_rights_status` | 827,450 | 945,926 | +118,476 |
| `rows_with_source_traceability` | 827,450 | 945,926 | +118,476 |
| `rows_without_source_traceability` | 0 | 0 | +0 |
| `source_overlap_rows` | 1,671 | 1,949 | +278 |

## Reproducibility

- Validator SHA-256: `7b24c0833710c42dd19e793f02fc82f895857fd81f46a639b122270f1c63fffe`
- Comparison script SHA-256: `677cae11fb6e23e876a851740acf3e1a132f40037676bd0cf03718c65c6a58bb`
- Metric-definition SHA-256: `8e1d7328e5158ee815efecc0f5619cc326b472ce09d9f8d3a1951b470489a15b`
- Previous preflight report SHA-256: `4cfff4b10577f490eb1b94f2bc77a1f9c0bbd061450515dbc554d66042ee95e4`
- Candidate preflight report SHA-256: `1b561d44a9a98d35622b01e385f48bf41df77be584515a002062f7d750f86171`
