# Structured-record rights review — 2026-09-23

## Result

Reviewed the 186 structured records that were previously marked `not_assessed`:

| Family | Records reviewed |
| --- | ---: |
| Geography | 50 |
| Historical terms | 36 |
| Literary people | 26 |
| Literary works | 66 |
| University research | 8 |
| **Total** | **186** |

No records or fields were removed. Each source catalog row and extracted package row now has `rights_status: reviewed_rights_unresolved` and a `rights_review` object with its source-specific findings and review date. This means rights were investigated; it does **not** mean all 186 are licensed for public redistribution. All remain in the complete local all-data package. The public builder still excludes all 216 structured records (the 186 reviewed here plus 30 song records with explicit metadata-only restrictions) because no whole-record public-rights basis is documented.

## Source findings

- **Wikipedia:** Wikimedia states that its text is available under CC BY-SA 4.0 and GFDL; reuse requires attribution and applicable share-alike terms. This is evidence for material actually derived from the cited Wikipedia pages. It does not license content from other sources mixed into the same record. Check page history and any source-specific notices before attributing an entire record to Wikipedia. [Wikimedia Terms of Use](https://foundation.wikimedia.org/wiki/Terms_of_Use)
- **OpenStreetMap:** OSM data is available under ODbL 1.0 with attribution and share-alike obligations. The geography records contain OSM search-query strings, but no returned OSM features or coordinates; the query strings do not establish OSM data provenance. [OSM copyright and license](https://www.openstreetmap.org/copyright)
- **Indian government sources:** The 2017 Open Government Data License of India grants reuse only for covered shareable, non-sensitive government data generated using public funds, subject to attribution and exclusions. This review did not establish that each cited portal page or document is covered by that license. A generic Government of India policy is not assigned to individual records without item-level evidence. [Official OGL India Gazette notification](https://www.meity.gov.in/static/uploads/2024/02/Gazette-Notification_OpenDataLicense_13.02.2017.pdf)
- **NIC S3WaaS:** Its general website policy permits accurate reproduction with source acknowledgment and excludes third-party material, but individual portal policies can differ. The Pauri Garhwal district policy specifically says reproduction requires prior email permission. That permission is not recorded here, so the Pauri material is not treated as cleared. [S3WaaS policies](https://s3waas.gov.in/website-policies/), [Pauri district policy](https://pauri.nic.in/website-policies/)
- **Historical scans:** The Internet Archive item for the 1881 *Himalayan Gazetteer* labels that item with Public Domain Mark 1.0. The Wikimedia Commons scan page marks the 1916 *Linguistic Survey of India*, Vol. 9, Part 4 public domain. These observations apply only to the identified works, not to other works or sources. [Archive item](https://archive.org/details/1882himalayangazetteervol1pt1), [LSI scan rights page](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu)
- **INFLIBNET IndCat:** Its FAQ says bibliographic records are free to the academic community and records can be downloaded in MARC format. No explicit general public/commercial redistribution license was found for the specific thesis record. The Garhwali catalog contains bibliographic metadata, not the thesis. [IndCat FAQ](https://indcat.inflibnet.ac.in/index.php/main/faq)
- **Other pages and captures:** The Itihaas capture has no canonical URL or reuse license in the captured source metadata. The supplied writers list is retained as a user-provided bibliographic lead, not treated as a license from the original authors or publishers. University pages/PDFs were checked where accessible; no compatible general reuse license was found for the cited syllabus or research materials. The TUFS repository page could not be inspected during this pass, so its item rights remain unverified.

The Indian Copyright Act distinguishes government works and states a 60-year term from the beginning of the calendar year after first publication when Government is the first copyright owner. This does not make every government-hosted document public domain, nor does it show who owns a particular work. [India Code, Copyright Act, 1957](https://www.indiacode.nic.in/bitstream/123456789/1367/5/a1957-14.pdf)

## What the catalog contains

These six structured configurations contain names, titles, classifications, dates, short catalog descriptions, bibliographic pointers, language relevance, and source metadata. They do not contain the full referenced novels, plays, lyrics, theses, journal papers, university syllabi, or the full Itihaas page. Source links and public availability are retained as provenance, not treated as a license.

For exact findings, inspect the `rights_review.source_assessments` field on each record in the source catalogs and generated `data/extracted/*/records.jsonl` files. A reviewed record stays public-release-blocked until a compatible right applies to the entire exported record or the record is revised with field-level provenance and rights.

## Package and quality snapshot

The rebuilt local all-data package has 257,807 rows in 18 configurations and contains **493,380,651 bytes** of JSONL and package metadata (about **470.5 MiB / 0.459 GiB**). It includes all collected text values and the 216 structured records, but no source audio. The rebuilt rights-filtered public profile has 146,684 rows in 12 configurations and is **254,596,037 bytes** (about **242.8 MiB / 0.237 GiB**). It redacts 24,566 catalog text values and excludes all 216 structured records. These row totals count overlapping representations, not unique examples.

The local `data/` workspace occupies **52G** according to `du -sh`; this includes source audio, caches, and intermediate/derived files and is not the upload-package size. The corpus currently has 28,755 exact-unique parent texts and 114,064 prepared text segments. Language accuracy remains an automated candidate: native-speaker review is deferred, only 29 parent texts have explicit dialect labels, and machine-generated transcripts are not ground truth. The 112-record speaker-safe ASR comparison reports 42.761% WER / 17.606% CER for base SraVaani; the human-reference adaptation reports 43.528% WER / 17.452% CER and was not promoted because WER worsened. GarhwaliBench is not native-reviewed.
