# Text source and rights audit

> Historical snapshot from 2026-09-15. Its row counts and 145,497-row package
> figure were superseded by the 2026-09-19 build: 28,755 parent texts,
> 114,064 prepared segments, 146,912 public rows, and 257,807 all-data rows.
> See [`all-data-package-2026-09-19.md`](all-data-package-2026-09-19.md) and
> [`finalreport.md`](../finalreport.md) for current release evidence and the
> later structured-record rights/provenance gap.

## Outcome

This pass audited all **27,986 exact-unique text records** and fixed two release
errors. Canonical provenance now preserves `license_id`, `rights_evidence`, and
attribution. Rights warnings are normalized before matching, so spaces, hyphens,
and underscores cannot change a source decision.

The release now treats exact duplicates by their valid source grant. If the same
text is present in both an open source and a rights-pending mirror, the open source
is the public rights basis; the mirror and every warning remain attached. This
promotes content only when an identical open copy is already in the corpus.

## Measured result

| Measure | Records |
| --- | ---: |
| Exact-unique collected texts | 27,986 |
| Texts with at least one public rights basis | 4,195 |
| Texts with only rights-pending provenance | 23,791 |
| Mixed-rights exact duplicates | 1,913 |
| Strict records using an open exact duplicate | 1,906 |
| Strict public candidates | 3,559 |
| High-quality rights-pending candidates | 1,748 |
| Public source/native review queue | 176 |

The largest resolved group is the strict text overlap shared by Meta Omnilingual
and the Indic Dialect ASR mirror. Meta's pinned corpus declares CC BY 4.0 and the
community mirror identifies Meta as the upstream source. Six additional strict
forms have an open Wiktionary copy plus a rights-pending community copy. The full
source-level counts are generated in
`data/processed/model_ready/text_source_audit/report.json`.

## Remaining high-quality rights queue

| Source group | Exact-unique texts | Reason still pending |
| --- | ---: | --- |
| Indic Dialect ASR, mirror-only | 1,216 | Component source/consent lineage is unresolved |
| Hindialect | 128 | Upstream component review is explicitly required |
| Dhyani idioms, source ID absent in legacy rows | 99 | Public page has no open-content license |
| E-magazine animal vocabulary | 96 | Public page has no open-content license |
| Dhyani occupations | 65 | Publisher license is not stated |
| Uttarakhandi Words animals | 53 | Public page has no open-content license |
| Open Bible Stories Garhwali | 49 | Catalog license is present, item-level scope remains unresolved |
| GarhwaliLanguage dictionary | 32 | Publisher license is not stated |
| E-magazine + Uttarakhandi duplicate forms | 6 | Neither retained source supplies an open license |
| PIB Ramman instrument terms | 5 | Government hosting alone does not establish reusable-content terms |
| UOU quoted material | 2 | Module terms do not automatically license quoted works |

All **1,748** rows remain active in the complete experimental view and visible in
the public catalog by stable hash, source, rights state, and quality evidence.

## Accuracy boundary

An open license and an upstream `gbm` label establish release provenance and
source scope. They do not prove native spelling, semantic alignment, dialect, or
transcription accuracy. After the source-grounded accuracy pass, the
**176-record** public review queue remains separate: 163 source-accuracy reviews,
nine surface/scaffolding reviews, and four Romanized-orthography reviews. These
are 172 Translatewiki records and four PanLex records.

## Public package

Every public text, lexicon, and instruction row now carries
`public_rights_basis` alongside its complete provenance. The final release audit
checks the named basis and still requires explicit Garhwali scope. The rebuilt
transcript-only package contains **145,497 rows**, accounts for all 27,986 text
identities, and passes with zero rights, provenance, language-scope, or leakage
errors.

## Reproduction

```bash
.venv/bin/python scripts/prepare_text_corpus.py
PYTHONPATH=scripts .venv/bin/python scripts/refine_priority_text.py
PYTHONPATH=scripts .venv/bin/python scripts/build_quality_tiers.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_text_sources.py
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py
.venv/bin/python scripts/audit_final_release.py
```

Source references: [Meta Omnilingual ASR Corpus](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus),
[Indic Dialect ASR dataset card](https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr),
and [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).
