# Hugging Face corpus text-availability and closeout audit — 2026-10-06

## v0.2.8 follow-up — 6 October 2026

The 1,841-row training config and 110-row context config added in v0.2.8
contain exact text values already present in the v0.2.7 `text` and
`text_expansion` configs. They add a filtered, attributed use view but do not
make new unique text public. A direct comparison found no match between the
1,951 values and the 8,444 full catalog texts previously absent from all
public configs, so the reported rights-pending availability gap is unchanged.
The [quality-screened text report](quality-screened-text-release-report-2026-10-06.md)
documents the comparison and current publication commits.

## Result

The public corpus is usable as a source-linked Garhwali research resource, but it
does not publish every full text retained by the project. The v0.2.7 release
contains 36,105 parent catalog rows. Its `catalog` config has 12,657 rows with
text and 23,448 rows whose text field is intentionally blank under the recorded
rights decisions. A cross-config scan shows that the blank catalog count is not
the same as text absent from the whole public repository:

| Availability measure | Rows / distinct values | Interpretation |
| --- | ---: | --- |
| Blank `catalog.text` fields | 23,448 | Per-config presentation; the source text may occur in another config |
| Values found elsewhere in public JSONL fields | 15,004 | 14,988 occur in `paharili_gbm`; 16 occur in other public fields |
| Distinct full texts not found in any public JSONL field | **8,444** | Remain only in the local all-data package, marked `rights_pending` / `not_cleared` |
| Words / characters in the 8,444 locally retained texts | **2,936,664 / 16,388,267** | Whitespace word count and character count, not language-token counts |

The exact-normalized comparison used Unicode NFKC, case folding, and collapsed
whitespace. It scanned the string-valued fields of all 961,533 JSONL rows across
the 18 named public configs, including reference tables. A match means the
normalized string is present somewhere in the repository; it does **not** mean
the matching config has a verified reuse license, that the value is a good
training example, or that it is easy to locate without the source lookup below.
The 14,988 PahariLI matches inherit PahariLI's unresolved sentence-origin and
language-label caveats.

## Training readiness and size interpretation — 2026-10-06

The current live corpus page reports 961,533 combined rows and 7.56 GB of
repository storage. Of the displayed rows, 778,157 (80.9%) are the
`record_index`, `source_catalog`, and `record_sources` reference views; they
are valuable for source discovery but are not language examples. The remaining
183,376 are overlapping content-config views, not unique passages. In the
current public text configs, `text` has 18,598 rows / 291,914 words,
`text_expansion` has 1,737 rows, and `text_resources` has 475 rows; all 20,810
are currently marked not recommended for general text-model training. The
separate speech repository reports 113,363 rows / 36.5 GB, but machine drafts
are not gold transcripts. See the [full current metrics audit](huggingface-current-metrics-and-utility-2026-10-06.md)
for counts, local disk accounting, and intended-use limits.

## What is already fixed

All 8,444 locally retained texts have a source locator in their public
provenance: 7,675 rows contain an inline source URL, and 769 rows resolve a URL
through the public `source_catalog` config. The public [developer quick start](../docs/DEVELOPER_QUICKSTART.md#follow-a-catalog-record-to-its-source)
now handles both cases. Some locators identify a dataset or collection rather
than the exact work, edition, or page. Treat them as discovery leads, not proof
of record-level source identification. The lookup gap is fixed; exact item
identification and reuse clearance remain open where the locator is broad.

A source URL is a locator, not permission to redistribute its contents. The
cross-config matches likewise remain experimental where their own provenance
and rights are unresolved. The public corpus makes those limits visible and
does not treat “online”, “open to read”, or “not explicitly private” as a reuse
grant.

## Largest groups in the remaining 8,444-text queue

Counts below are source-associated records in the unmatched set; a source can
have multiple works or URLs. They are triage groups, not rights findings.

| Source group | Records | Resolution route |
| --- | ---: | --- |
| e-Magazine of Uttarakhand | 1,770 | Seek publication/author permission or a work-specific open license |
| Bhatta (1976) | 443 | Identify edition and rights holder; verify public-domain or permission basis |
| UOU CGL material | 436 | Verify the exact university work and its repository license/permission |
| Chatak, *Lokgeet* (1956) | 369 | Verify edition, author/translator, and term; seek permission if protected |
| *Himalayan Folklore* (1977 reprint; cataloged as 1935) | 368 | Resolve edition mismatch, then establish the source edition’s status |
| Rahul Sankrityayan (1953) | 305 | Verify the exact work/edition and applicable rights status |
| Shanti Chaudhary (1994) | 298 | Identify rights holder and seek permission or a documented license |
| Dabral, *Yatra/Darshan* | 284 | Verify edition and rights holder |
| Chatak, *Lok Gathayen* (1958) | 276 | Verify edition and rights holder |
| Tehri Gazetteer | 253 | Verify publication date, edition, and applicable public-domain basis |
| Dabral, Alaknanda ethnography | 248 | Verify edition and rights holder |
| *British Garhwal* (1910) | 246 | Verify the exact scan/edition and document public-domain basis |
| Incoming Garhwali–Hindi dictionary | 239 | Identify the submitted edition and its reuse terms |
| Juyal (1967) | 200 | Resolve the CC0-vs-all-rights-reserved conflict against authoritative evidence |
| Dabral, *History*, volume 1 | 186 | Verify edition and rights holder |
| Rai Pati Ram (1916) | 185 | Verify exact edition and public-domain status |

The source decision ledger is
[`text-rights-resolution-2026-09-30.md`](text-rights-resolution-2026-09-30.md);
Archive edition/claim findings are in the
[`priority-language and rights review`](internet-archive-priority-language-rights-review-2026-10-04.md).
The source group list is intentionally not represented as a new permission
decision.

## Resolution workflow

This is the concrete path for closing the remaining public-content gap without
dropping records or making unsupported claims:

1. Use the public `source_catalog` join to group unmatched record IDs by source,
   edition, URL, and rights status. Preserve all original record IDs and hashes.
2. For each group, attach authoritative evidence: the exact license and scope;
   written permission covering redistribution; or edition-specific evidence
   supporting public-domain treatment in the relevant jurisdiction. A library
   scan or public webpage alone is insufficient.
3. Apply the existing source-level decision to each linked record. Mark only
   evidenced rows as eligible; retain unresolved records in the local all-data
   package and keep their public reference metadata discoverable.
4. Rebuild the additive public profile and its reference tables, run the rights,
   quality, deduplication, split, and continuity gates, then publish a new
   version only if every changed full-text row has an auditable basis.
5. Independently track linguistic correction/native review. Rights clearance
   does not certify language identity or spelling; native review does not grant
   copyright permission.

No full-text rights decision was made by this audit. It changes documentation
and source findability only. The released corpus data did not change. The
project is stopping active ingestion at v0.2.7 for now; any later expansion
starts from this queue and the existing additive release pipeline, not from a
new source dump.

## Reproduction and report links

This report records the exhaustive scan performed against the ignored local
v0.2.7 all-data and public-package snapshots. The raw expressive text and
row-level candidate list are not copied into this tracked report. Package
counts, release checks, and current project limits are summarized in
[`README.md`](../README.md), [`DATASET_CARD.md`](../DATASET_CARD.md), and
[`finalreport.md`](../finalreport.md); the public release itself is documented
in the [v0.2.7 release report](huggingface-corpus-v0.2.7-release-2026-10-06.md).
