# Source-grounded text accuracy review

## Outcome

This pass reduced the public text review queue from **628 to 177 records** without
inventing Garhwali spellings, translations, or dialect labels. All 27,986
exact-unique texts remain active in the complete experimental corpus, and every
changed release view retains its immutable source value and provenance.

The 451 resolved records were closed through better extraction or explicit
scholarly source evidence. They were not marked as native-reviewed.

## Measured changes

| Measure | Before | After |
| --- | ---: | ---: |
| Public Garhwali candidates | 3,734 | 3,735 |
| Strict public candidates | 3,106 | 3,558 |
| Public review queue | 628 | 177 |
| Romanized-orthography queue | 426 | 4 |
| Source-accuracy queue | 135 | 163 |
| Surface/scaffolding queue | 42 | 10 |
| Semantic-alignment queue | 24 | 0 |
| Language-identity queue | 1 | 0 |

## Extraction corrections

- Replaced 56 flattened English Wiktionary page blobs with **77 structured
  Garhwali records**: 55 lemmas, 13 alternative forms, and nine example
  sentences. English definitions and translations remain metadata.
- Rendered cached Wikimedia and Incubator wikitext conservatively, removing
  templates, tables, categories, media, and interface scaffolding while
  preserving Garhwali prose and link labels.
- Skipped redirect-only Wikimedia snapshots instead of treating redirects as
  language data.
- Preserved extraction fields such as `text_format`, `source_text_format`,
  `relation`, and `headword` through canonical preparation.
- Fixed Unicode length checks so Devanagari combining marks count as linguistic
  characters rather than causing valid short words to be flagged.
- Removed complete nested MediaWiki placeholders such as `{{SITENAME}}` without
  leaving stray braces.

The rebuilt public candidate layer contains no old Wiktionary raw-page blobs and
no detected wikitext scaffolding residue.

## Scholarly transcription handling

The pipeline now recognizes **392 source-attested Garhwali linguistic
transcriptions** from ASJP, the Linguistic Survey of India CLDF derivative,
SAND/Numeralbank, Chan's numeral data, and Mamta's South Asia examples. Their
source notation is retained exactly and labeled
`source_attested_linguistic_notation`. The 25 Mamta parallel examples also carry
`source_attested_parallel_alignment`.

These labels mean that the form or alignment is explicitly supplied by a named
linguistic source. They do not claim native review, modern standard spelling, or
a preferred Devanagari transliteration.

## Remaining human boundary

The remaining **177 records** are all present in the active experimental layer:

| Source | Records | Main decision still needed |
| --- | ---: | --- |
| Translatewiki | 172 | Native accuracy and short interface-context review |
| PanLex | 4 | Romanized form and sense review |
| Mamta South Asia examples | 1 | Slash-separated alignment boundary |

No native-speaker decisions were available during this pass. These records stay
out of the strict public candidate tier until source context or human evidence
supports promotion. Nothing is quarantined or hidden from the local all-data
view.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python scripts/ingest_open.py --sources wikimedia
PYTHONPATH=scripts .venv/bin/python scripts/collect_online.py wiktionary
.venv/bin/python scripts/prepare_text_corpus.py
PYTHONPATH=scripts .venv/bin/python scripts/tag_language_quality.py
PYTHONPATH=scripts .venv/bin/python scripts/refine_priority_text.py
PYTHONPATH=scripts .venv/bin/python scripts/build_quality_tiers.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_text_sources.py
.venv/bin/python scripts/build_huggingface_dataset.py
.venv/bin/python scripts/audit_final_release.py
```

This pass used cached source snapshots and local code. It incurred **$0** in API,
GPU, or Hugging Face billing charges.
