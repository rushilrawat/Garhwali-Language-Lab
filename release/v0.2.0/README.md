# Garhwali Language Lab v0.2.0

This release adds a deduplicated Garhwali-only intake and rebuilds the transcript-only corpus packages. All counts below distinguish source rows, unique text values, segments, and overlapping package rows.

## New text in this release

- **696 source rows / 180,043 characters** across four source intakes.
- **673 exact-unique strings within the intake; 671 net-new exact-unique texts** after comparison with prior corpus layers. Two intake values were already present.
- 632 historical LSI dialect-table rows (609 exact-unique forms); explicit Standard, Rathi, and Tehri labels are retained. 496 rows have OCR confidence below 60/100.
- Nine OCR-derived Devanagari specimens across the LSI's Garhwali varieties.
- Five proverbs explicitly marked Garhwali in Upreti (1894).
- Fifty Garhwali Open Bible Stories at a pinned Door43 source revision under CC BY-SA 4.0.

New historical OCR has not been corrected or speaker-reviewed; story translation quality also remains unreviewed. Every row retains source, page/revision, rights, and quality metadata. New-source deduplication found no cross-source duplicate pairs; two values overlap prior corpus layers.

## Rebuilt corpus

- 29,426 exact-unique parent texts from 46 source files; 9,325,936 characters.
- 115,785 exact-unique text segments; document and duplicate-component splits have zero text/parent overlap.
- All-data package: 260,199 rows across overlapping configurations; all collected text values included, zero catalog redactions.
- Public-profile package: 150,065 rows across overlapping configurations; rights-filtered text plus a metadata-only index covering all 260,199 archive rows, 600 sources, and 283,752 source links.
- Final release audit, public and all-data cloud preflights, release-index validation, and compact bundle integrity check pass.

Counts across package configurations are not unique example counts. The all-data package retains restricted/right-pending values locally. The public profile redacts 24,565 catalog values and does not publish 216 structured records without compatible public-rights evidence. No blanket data license is claimed. Native-speaker review and dialect annotation remain deferred, so language and benchmark quality are not native-validated.

## Verification

- Pytest: **607 passed**; unittest: **605 passed**.
- Public Hugging Face corpus: [v0.2.0 commit `cb631488`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cb6314880b8a28c3bf3dcc025d8ff9ebe062c927). All 34 package files match the upload manifest by size and hash.
- Dataset Viewer: all 15 split validity checks returned HTTP 200 with preview and viewer enabled; one text preview loaded on 2026-09-29.
- GitHub tag/release: pending final publication.
- Hugging Face cloud preflights: public and all-data passed.
- Final audit: passed with zero package rights failures, zero cross-split text/audio/speaker identity overlap in the configured splits, and one retained XORQA train/dev duplicate warning.
- New source QA: all 696 rows passed the GBM/Garhwali scope check; 671 strings are net-new after exact deduplication.

See [`research/garhwali-data-expansion-2026-09-29.md`](../../research/garhwali-data-expansion-2026-09-29.md), [`final-audit.json`](final-audit.json), and [`v0.2.0-manifest.json`](../v0.2.0-manifest.json).
