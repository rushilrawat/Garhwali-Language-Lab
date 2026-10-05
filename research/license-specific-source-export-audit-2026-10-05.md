# License-specific source exports — 2026-10-05

This follow-up implements the attribution/export action from the benchmark
roadmap. It adds source-level evidence and produces local, reproducible export
candidates. It does **not** change the frozen GarhwaliBench v0.2 manifest or
its public-release flags, and it does not upload anything to Hugging Face.

## What is now prepared

The export command builds five license/source views from the existing local
corpus and the frozen v0.2 text splits:

| Export | Rows | Source data | License/notice | Distinct normalized texts |
| --- | ---: | --- | --- | ---: |
| `tatoeba_cc_by_2_0_fr` | 36 | 36 Garhwali sentences | CC BY 2.0 FR | 36 |
| `wikimedia_cc_by_sa_4_0` | 39 | 35 Wikimedia Incubator encyclopedia pages, 4 Wiktionary Incubator pages | CC BY-SA 4.0 | 39 |
| `wiktionary_cc_by_sa_4_0` | 280 | 77 English Wiktionary entries, 203 Swadesh-list entries | CC BY-SA 4.0 | 250 |
| `obs_tlf_gbm_v1_cc_by_sa_4_0` | 1,793 | Garhwali Open Bible Stories v1 benchmark text | CC BY-SA 4.0 | 1,793 |
| `lsi_1916_public_domain` | 284 | 1916 *Linguistic Survey of India* OCR text | Public Domain Mark evidence; no new copyright license asserted | 284 |
| **Total** | **2,432** |  |  | **2,402 across all views** |

The 30 repeated normalized strings are Wiktionary headwords present in both
the entry and Swadesh source records. Both records and their separate gloss,
source, and revision lineage are retained; they are not 30 additional unique
Garhwali spellings. All export record IDs are unique. These are repackaged
existing records, not 2,432 newly collected texts.

## Attribution findings

All 36 Tatoeba sentence pages now have recovered contributor attribution:
each page identifies `sabretou` as the contributor, and each page matched its
requested sentence ID. The API reports `owner: null` for all 36, which Tatoeba
defines as an orphaned sentence; it reports none as unapproved. The API still
declares CC BY 2.0 FR for every sentence. The source pages, API retrieval
metadata, usernames, profile links, retrieval times, and page SHA-256 hashes
are recorded in [the Tatoeba attribution sidecar](tatoeba-attribution-audit-2026-10-05.json).
Tatoeba's reuse instructions require sentence-author attribution, so the
export now names the recovered contributor and links the sentence page.
Orphaned status is kept visible as a quality warning; these records remain
unreviewed and `training_eligible=false`.

The local Wikimedia source rows already had page titles, immutable revision
IDs, oldid links, and history links: 35 `Wp/gbm` records and 4 `Wt/gbm`
records. The 77 English Wiktionary rows likewise already had revision IDs,
oldid links, and per-page history links. The 203 Swadesh rows had revision
87247279 and a source snapshot, but no item/history URLs; the exporter now
constructs both links to that exact revision. The export standardizes these
values into `source_title`, `source_revision`, `source_url`, and
`source_history_url` fields. Wikimedia reuse guidance calls for checking the
applicable page license, linking title/source/license, and noting changes;
Wiktionary also warns that individual entries may contain third-party material
with separate terms. Those item-specific exceptions have **not** been
independently audited, so the Wikimedia and Wiktionary files remain candidates
rather than cleared public releases.

The 1,793 Open Bible Stories rows and 284 LSI rows already had compatible
source-level rights assessments and are now exported with their share-alike
or public-domain evidence, original source IDs, modifications, and benchmark
splits. The LSI export retains its scan hash and printed-page references. Its
quality flags still identify unreviewed OCR; rights compatibility does not
mean the Garhwali text has been corrected.

## Release and model-use limits

The generated files and manifest are under the ignored local directory
`.cache/license_exports/2026-10-05/`. The manifest reports row counts,
license URLs, source counts, exact duplicate counts, and file hashes. Every
record retains its unreviewed quality state and non-training-ready flag where
present. The benchmark-derived rows retain `train`/`validation`/`test` labels
and are explicitly marked as overlapping the open v0.2 benchmark; do not use
them as an independent test set or move its held-out rows into training.

This is a source-export preparation step only. The frozen benchmark still has
14,703 rows with `public_upload_allowed=false` and
`public_release_cleared=false`; its recorded rights statuses have not been
rewritten by this sidecar. The external CrossSum/FLORES/XORQA component review,
the 112-row ASR privacy-safe projection, and the remaining source-component
rights reconciliation are still required before a **final public benchmark**
package is cleared. No Hugging Face files were changed in this step.

## Reproduction and verification

From the repository root, with the local ignored source files present:

```bash
python scripts/export_licensed_sources.py
python -m unittest tests.test_export_licensed_sources -v
```

The export command completed with 2,432 rows, 2,402 exact normalized text
values, zero duplicate record IDs, and 30 repeated text rows retained with
separate source lineage. Four focused tests pass. The script refuses to build
if the Tatoeba source IDs and attribution sidecar do not match exactly, if a
source license differs from the expected component, or if compatible
benchmark source IDs repeat without a unique example ID.

## Primary source references

- [Tatoeba sentence reuse rules](https://en.www.en.wiki.tatoeba.org/articles/show/using-the-tatoeba-corpus) require author credit for redistributed sentence text.
- [Tatoeba API schema](https://api.tatoeba.org/openapi.json) defines `owner: null` for orphaned sentences and exposes the sentence license.
- [Example recovered sentence page](https://tatoeba.org/en/sentences/show/4648044) identifies the contributor; all 36 pages are separately listed in the sidecar.
- [Wiktionary copyrights page](https://en.wiktionary.org/wiki/Wiktionary:Copyrights) describes the CC BY-SA 4.0/GFDL terms and warns that some entry content may have third-party terms.
- [Wikimedia content reuse guidance](https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse) describes license checks, title/author/source attribution, and modification notices.
- [Garhwali Open Bible Stories v1 manifest](https://git.door43.org/OBS-TLF/gbm_obs/src/tag/v1/gbm_obs/manifest.yaml) identifies the fixed source version and license evidence.
- [1916 LSI scan rights page](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu) identifies the matching volume and public-domain evidence.
