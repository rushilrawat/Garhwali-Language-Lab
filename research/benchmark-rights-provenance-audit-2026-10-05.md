# GarhwaliBench v0.2 rights and provenance audit

**Reviewed:** 2026-10-05  
**Scope:** frozen local v0.2 draft; eight views, 14,703 view rows  
**Manifest SHA-256:** `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`  
**Disposition:** evidence audit only; no rows removed, redacted, or reclassified, and no upload or release flag changed.

This report separates a source's declared license from proof that the exact
exported components meet their attribution, privacy, use, and redistribution
conditions. It is an evidence record, not a legal opinion. The machine-readable
counts are in [benchmark-rights-provenance-audit-2026-10-05.json](benchmark-rights-provenance-audit-2026-10-05.json).

## Result

The draft still passes the structural contract, but **none of its 14,703 view
rows is cleared for public upload**. All 14,703 have
`public_upload_allowed=false` and `public_release_cleared=false`. This is a
release-state flag, not a deletion or a statement that the language material
was removed. Every draft row remains in the local views.

The audit now verifies the external source snapshots and use labels, and it
distinguishes unique text rows from repeated parent-rights components. It also
found two unusually well-supported text groups that are realistic candidates
for separate, correctly attributed exports: 1,793 Garhwali Open Bible Stories
records under CC BY-SA 4.0 and 284 1916 *Linguistic Survey of India* records
identified as public domain. They remain candidates until the corresponding
export carries the required source credit, license or public-domain notice,
modification notes, and page/record references.

## Frozen view inventory

| View | Rows | Audit finding |
| --- | ---: | --- |
| `external/crosssum` | 699 | CC BY-NC-SA 4.0 declared; source and target article URLs are present on all rows; provider says evaluation use and excludes LLM pretraining. Third-party article-text rights still need component review. |
| `external/flores` | 2,009 | CC BY-SA 4.0 declared; source snapshot URL, SHA-256, retrieval time, and attribution are present on all rows; provider says evaluation use and excludes LLM pretraining. |
| `external/xorqa` | 1,139 | MIT declared; snapshot provenance and attribution are present on all rows; provider says evaluation use and excludes LLM pretraining. Underlying passage/question/translation components still need review. |
| `internal/asr` | 112 | CC BY 4.0 declared; every row has a local audio locator and local identifiers, so this view is not a publishable package as currently shaped. |
| `internal/text` | 402 | Mirrors the same 402 records as `text_recommended/test`; these are not 402 additional examples. Its 641 component-rights entries include 10 compatible, 404 unrecorded, and 227 pending source/component/consent review. |
| `text_recommended/train` | 9,486 | Text rows retained; rights states are item/component-level, not blanket-cleared by this audit. |
| `text_recommended/validation` | 454 | Text rows retained; same rights distinctions as train/test. |
| `text_recommended/test` | 402 | Text rows retained; mirrored by `internal/text`. |
| **Total view rows** | **14,703** | **View-row total; not a unique-example total. Every row-level public gate remains false.** |

Across the 3,847 external task rows, all have a source ID, attribution,
snapshot URL, snapshot SHA-256, and retrieval timestamp. All 3,847 also have
`training_eligibility_as_recorded=false`, matching the upstream IndicGenBench
cards' instruction to use these benchmark examples for evaluation rather than
LLM pretraining. CrossSum carries both upstream article URLs for all 699 rows;
the FLORES and XORQA adapters preserve their hashed dataset snapshots and
source IDs, but do not carry per-example source/target URLs in this export.

## Recommended text split: exact source counts

The 10,342 recommended text rows divide into **2,077 rows whose recorded
components are marked rights-compatible** and **8,265 whose component status
is `not_recorded`**. `not_recorded` means the v0.2 export did not record a
component decision; it does not mean the text, license URL, or attribution is
absent. The 8,265 rows are grouped by distinct source-family combination:

| Source-family grouping | Rows |
| --- | ---: |
| Meta Omnilingual only | 7,931 |
| Tatoeba only | 36 |
| Wikimedia only | 78 |
| Wiktionary English only | 49 |
| Wiktionary Swadesh/thematic only | 155 |
| Both Wiktionary source families | 10 |
| Wikimedia Incubator Wiktionary only | 6 |
| **Total with component status unrecorded** | **8,265** |

These counts are record-level groups; source/component memberships can overlap
inside an example. The machine audit reports both rows-with-source and
component occurrences. For example, 7,931 deduplicated rows carry 8,149 Meta
parent components: 212 rows have two same-source components and two rows have
four. These are repeated source parents for one normalized text row, not 218
new unique texts. The same distinction applies to a few Wikimedia and
Wiktionary rows.

The 2,077 compatible-status rows are:

| Source | Rows | Evidence checked | Remaining export requirement |
| --- | ---: | --- | --- |
| Garhwali Open Bible Stories (`obs_tlf_gbm_v1`) | 1,793 | All components carry source URL, snapshot SHA-256, rights evidence, attribution, and CC BY-SA 4.0 metadata. The official Garhwali edition lists all 50 stories and explicitly says commercial reuse/adaptation is allowed under CC BY-SA 4.0 with attribution and same-license sharing. | Export exact source/version, credit unfoldingWord/Door43 and the Garhwali translation, link CC BY-SA 4.0, note normalization/extraction changes, and share this adaptation under a compatible share-alike license. |
| 1916 *Linguistic Survey of India* (`lsi_1916_grierson_garhwali_specimens`) | 284 | Every component records George A. Grierson, 1916, source URL, rights-evidence URL, source-PDF SHA-256, and PDM 1.0. The linked Commons page identifies the matching 1916 volume as public domain and links the Internet Archive source scan. | Retain author/title/year, Commons/Archive links, scan hash, and page locator; describe the extracted/OCR text as modified from the scan and mark it public domain rather than assigning a new CC license. |

The source cards support these source-level bases, but their own row flags are
still false. The output has not yet been regenerated as two license-specific
exports.

## Unrecorded source decisions and concrete fixes

| Source | Verified fact | Remaining work |
| --- | --- | --- |
| Meta Omnilingual (`meta_omni`) | The official dataset card declares CC BY 4.0; the v0.2 records carry the source URL, license URL, attribution, rights-evidence metadata path, and source record IDs. | Apply the card-level license decision to the specific transcript components after confirming the record-to-source mapping and carrying the citation/modification statement into the export. The current v0.2 rows still say `not_recorded`; this audit does not silently overwrite that state. |
| Tatoeba | All 36 sentence IDs are now matched to sentence pages. Each page identifies `sabretou` as the contributor; the API reports `owner=null` (orphaned) for all 36 and none as unapproved, with CC BY 2.0 FR declared for every row. | Attribution metadata is saved in [the Tatoeba sidecar](tatoeba-attribution-audit-2026-10-05.json), and a separately licensed local export is built by [the source export script](../scripts/export_licensed_sources.py). The frozen v0.2 rows still say `not_recorded`; their release flags were deliberately not rewritten by this supplement. |
| Wikimedia and Wikimedia Incubator | The local source files have page/history links and immutable revisions for 35 `Wp/gbm` and 4 `Wt/gbm` records. The 6 `incubator_wt` and 80 `wikimedia` entries in the v0.2 view are component occurrences, not unique source-page counts. | The local license export standardizes page title, revision, oldid, and history fields. Page-specific third-party material and exact contributor lists remain unaudited; frozen v0.2 component statuses remain `not_recorded`. |
| Wiktionary and thematic Swadesh source | The 77 English Wiktionary source rows have revision and history links. The 203 Swadesh rows share the saved source-page revision 87247279 but lacked item/history URLs. | The local export now constructs an immutable oldid and history link for the Swadesh revision and standardizes fields for all 280 source records. Wiktionary warns that some entries contain third-party material; item-level exceptions remain unaudited, and the frozen v0.2 component statuses remain `not_recorded`. |
| IndicGenBench CrossSum | The official card declares CC BY-NC-SA 4.0, shows BBC source/target article URLs in examples, and limits intended use to evaluation (no LLM pretraining). The local export retains source and target URLs for all 699 rows. | Review whether the upstream declaration covers the embedded publisher article text as adapted, and keep commercial use blocked unless the rights basis expressly permits it. |
| IndicGenBench FLORES | The official card declares CC BY-SA 4.0, maps its development/test files to the original FLORES dev/devtest files, and excludes LLM pretraining. | Carry source/version attribution, indicate extraction/normalization changes, and prepare a separate evaluation-only CC BY-SA export. |
| IndicGenBench XORQA | The official card declares MIT, says the benchmark is evaluation-only (not LLM pretraining), and describes human translations of underlying task data. Its cited XORQA source describes TyDiQA lineage and the Wikipedia snapshot used for retrieval. | Reconcile underlying passages, questions, annotations, and translations individually; a repository-level MIT field is not the complete component map. |
| VAANI ASR | The upstream card declares CC BY 4.0; the local 112-row candidate retains audio and speaker-related fields. | Keep all rows; create a public-safe projection only after the audio URI, speaker/local identifiers, provider terms, and record-level provenance are explicitly reviewed. |

## Provider evidence

- [IndicGenBench CrossSum-IN card](https://huggingface.co/datasets/google/IndicGenBench_crosssum_in), [FLORES-IN card](https://huggingface.co/datasets/google/IndicGenBench_flores_in), and [XORQA-IN card](https://huggingface.co/datasets/google/IndicGenBench_xorqa_in) list their respective CC BY-NC-SA 4.0, CC BY-SA 4.0, and MIT declarations. Each states evaluation as the direct purpose and says the benchmark data should not be included in LLM pretraining.
- The [official XORQA repository](https://github.com/AkariAsai/XORQA) asks users to cite both XORQA and TyDiQA and references the 2019-02-01 Wikipedia dump used for its multilingual retrieval passages.
- The [Meta Omnilingual ASR card](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus) declares CC BY 4.0 and documents its speech/transcript fields and corpus citation.
- The [Tatoeba reuse rules](https://en.www.en.wiki.tatoeba.org/articles/show/usingthecorpus) specify CC BY 2.0 France for sentence text and require citing the sentence author. The [stable API schema](https://api.tatoeba.org/openapi) documents a sentence-by-ID endpoint with an `owner` field.
- The [Garhwali Open Bible Stories page](https://openbiblestories.org/l/gbm/) lists 50 stories and its CC BY-SA 4.0 terms, including commercial use subject to attribution and share-alike.
- The [Wikimedia content-reuse guide](https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse) instructs users to check each page's license, provide attribution, and identify modifications. The [Commons LSI scan page](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu) identifies the 1916 publication and author, points to Internet Archive, and marks the work public domain/PDM.
- Creative Commons explains that [CC BY-SA 4.0 permits commercial reuse with attribution and share-alike](https://creativecommons.org/licenses/by-sa/4.0/deed.en) and that the [Public Domain Mark is an identifier, not a legal instrument](https://creativecommons.org/publicdomain/mark/1.0/). For the LSI record, the specific Commons file page supplies the work-level public-domain assertion; the mark is not treated as the sole evidence.

## Reproduction and exit gate

Run these from the repository root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_benchmark_v02_rights.py
PYTHONPATH=scripts .venv/bin/python scripts/validate_benchmark_v02.py
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_audit_benchmark_v02_rights.py' -v
```

The structural validator passes all eight assets with zero errors. The rights
audit is separate and still reports 14,703 false public-upload/release flags.
The Tatoeba attribution, wiki revision-link normalization, and local
license-specific export work is now recorded in the
[2026-10-05 follow-up](license-specific-source-export-audit-2026-10-05.md).
That follow-up is supplemental evidence; it does not modify the frozen v0.2
manifest or certify its package-level release flags. Remaining work is to
reconcile source-level rights for Meta, CrossSum, FLORES, and XORQA components,
prepare a public-safe projection of the 112-row ASR view, and complete semantic
overlap/exposure checks. No external job, model run, data deletion, or Hugging
Face upload was started.
