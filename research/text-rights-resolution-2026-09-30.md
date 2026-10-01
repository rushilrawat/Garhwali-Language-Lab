# Text rights resolution — 2026-10-01

## Decision and release state

This is the source-by-source decision log for the published v2.1.0 release.
It supersedes the older v2.0 figures below for the current public package.

| V2.1.0 release measure | Count |
| --- | ---: |
| Exact-unique catalog values | 32,072 |
| Publicly included text values with an open, exact source-specific, policy, or fact-only basis | 12,606 |
| Of those, values with a compatible open-license or work-specific public-domain basis | 12,258 |
| CC BY-NC-SA 4.0 values (noncommercial and share-alike) | 134 |
| Source-policy values: PIB instrument facts (5) and Mountain Voices/Panos glossary headwords (193) | 198 |
| Isolated individual-word facts (no definitions, record positions, or list order exported) | 16 |
| Full text still redacted for lack of a compatible public basis | 19,466 |
| Structured knowledge records exposed as factual/bibliographic metadata | 216 / 216 |
| Full expressive text in local all-data catalog | 32,072 / 32,072 |

The four public text categories sum to 12,606. The 530 `sharealike_required`
values are a condition-bearing subset of those public values, not additional
records. Source-association counts below overlap and must not be summed to get
the 19,466 distinct redacted texts.

V2.1.0 was uploaded additively to Hugging Face at commit
[`53c1ce9`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53c1ce9baa07e6fb05722e5a1ed750f33096124b).
It reduces the redacted catalog count by 6,864 from v2.0.0 and adds factual or
bibliographic projections for all 216 structured records. The full all-data
package remains local and retains every text value, including the 19,466 whose
expressive content still lacks a compatible public reuse basis. Nothing was
deleted.
The latest docs-only amendment is at Hub head
[`f2def9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/f2def9e717390008ebf7aac05decebf1c264fa98); it does not change the v2.1.0 data payload.

## What the user's “not explicitly private” rule can safely achieve

Public access, absence of a password, and absence of a “private” label do not
grant permission to republish a copyrighted work. The Indian Copyright Office
says copyright acquisition is automatic and requires no formality; a visible
notice is not a prerequisite. Original prose, lyrics,
translations, expressive definitions, and protected compilations can remain
protected even when found on a public page. Individual facts, names, titles,
short phrases, and independently verified lexical facts can often be exposed as
facts, but that does not authorize copying a site's wording, a book's pages, or
the selection/arrangement of a protected dictionary. Indian fair-dealing
exceptions are limited and do not provide blanket permission for a public
corpus. The same Office says titles, names, short word combinations, and factual
information are not ordinarily protected, while its handbook warns that even
a short, distinctive lyric phrase may infringe; each phrase and compilation
still needs context-specific review. [Copyright Office FAQ](https://copyright.gov.in/frmFAQ.aspx),
[Copyright Office handbook](https://copyright.gov.in/documents/handbook.html),
[Copyright Act §§13–14](https://copyright.gov.in/Copyright_Act_1957/chapter_iii.html),
[§52 exceptions](https://copyright.gov.in/Exceptions.aspx/FORMXV/FORMXV/Society/Documents/Documents/WaitingApplicationsForObjection.aspx).

Accordingly, “release all” is implemented as: retain every payload locally;
publish every verifiable fact, bibliographic identifier, source URL, license
decision, and attribution that does not reproduce protected expression; publish
full text only where a compatible source-specific reuse basis is documented.
This preserves discovery and auditability without calling unlicensed material
open data.

### New Scripture rights lead found during this review

Bible.com lists two distinct Garhwali versions: a Wycliffe-published version
and **GHMNT**, published by The Love Fellowship. A GHMNT chapter page credits
the text under **CC BY-SA 4.0**. This is a compatible source when attribution
and share-alike terms are followed, and it should be represented as its own
edition. However, YouVersion's terms prohibit robots or other automated means
from accessing or copying its materials; its developer API requires a
registered application and acceptance of the applicable license agreements.
The linked Free Bibles India page offers Bible applications, not a verified
bulk text package. Therefore this review did not scrape or bulk-download
GHMNT. Obtain an authorized publisher-provided text copy or explicit platform
authorization before ingesting it. [GHMNT license credit](https://www.bible.com/bible/3164/1PE.5.GHMNT),
[YouVersion terms](https://www.bible.com/terms), [API access conditions](https://developers.youversion.com/api-usage),
[Free Bibles India downloads](https://www.freebiblesindia.in/bible/gbm/download.html).

A second GHMNT host, Zeno, also credits the text under a share-alike license,
but its current terms prohibit systematic retrieval to build a collection
without Zeno's written permission and restrict use of platform content without
the respective owners' written consent. The text license and permission to
bulk-collect it from this host are separate questions. Do not scrape Zeno;
request a publisher-provided file or written platform authorization instead.
[Zeno GHMNT chapter](https://zeno.fm/bible/GBMDPI/PHM/1/),
[Zeno terms, prohibited activities and content use](https://zeno.fm/terms/).

The PahariLI paper labels 5,000 scripture sentences only as “The New
Testament”; it does not identify an edition, and the imported rows have no
chapter/verse or source-component map. The GHMNT license therefore does **not
yet** clear any PahariLI row. If an authorized GHMNT copy is obtained, exact
and reviewed fuzzy matches can be attributed to that edition; unmatched
scripture and web-excerpt rows remain pending. [PahariLI repository](https://github.com/rachanagusain/PahariLI),
[PahariLI paper](https://doi.org/10.1007/s10579-023-09651-6).

A follow-up inspection of the public PahariLI repository confirmed that its
README describes 44,014 training and 11,004 test sentences, while the
repository-level Apache-2.0 file does not map individual sentences to source
works or state which embedded third-party text the repository owner can
license. The dataset README itself does not provide a separate content-rights
statement. This confirms the existing decision; it does not create a new
redistribution basis for the 14,999 linked catalog values. Ask the authors for
row-level provenance and written permission, then apply any grant only to
identified components. The corresponding author is publicly identified by
Springer as Rachana Gusain; no permission request was sent during this review.
[Repository README](https://github.com/rachanagusain/PahariLI/blob/main/README.md),
[repository license](https://github.com/rachanagusain/PahariLI/blob/main/LICENSE).
The Springer landing page confirms the paper is subscription content and points
to the public corpus repository; it does not provide a license for the scraped
blog, story, play, interview, or scripture components. [Springer article page](https://link.springer.com/article/10.1007/s10579-023-09651-6).

### Further clearance checks — 2026-10-01

- **PahariLI:** the public repository declares Apache-2.0 for repository
  contents, but the Garhwali file is a mixture of third-party expressive text
  and scripture according to the authors' dataset description. The repository
  has no row-to-work/source map or component-specific permission evidence.
  Apache terms from the repository maintainer cannot by themselves document
  permission from the original authors of included works. No row-level
  PahariLI texts were newly cleared in this pass. The paper's corresponding
  author is publicly listed as Rachana Gusain; no outreach was sent.
- **1954 *Garhwali Sahitya ki Bhumika* scan (74 extracted pages):** a
  Garhwali literature article identifies it as a multi-contributor collection,
  with essays by Shyam Chand Negi and Damodar Prasad Thapliyal among others.
  Secondary biographical sources report Negi died in 1982 and Thapliyal in
  1977. If those identities and dates apply to the actual contributors, India's
  life-plus-60 term would ordinarily run through 2042 and 2037 respectively;
  this volume therefore cannot be presumed public domain based on its 1954
  publication date. The source's contributor-level rights and attribution
  still need verification. [Collection/contributor description](https://e-magazineofuttarakhand.blogspot.com/2011/12/criticism-in-garhwali-literature.html),
  [Negi biography](https://e-magazineofuttarakhand.blogspot.com/2009/10/garhwali-kumaoni-himalayan-literature_4216.html),
  [Thapliyal biography](https://e-magazineofuttarakhand.blogspot.com/2012/05/).
- **The 2016 English-Garhwali-Hindi dictionary** remains a currently sold,
  modern lexicon by Achlanand Jakhmola; no open license surfaced in this
  search. The 2007 Garhwali-Hindi dictionary credits compilers Arvind Purohit
  and Beena Benjwal and editor Ramakant Benjwal; a source article reports the
  2015 second edition and copyright notice, which confirms that its
  compilation/selection cannot be treated as a loose set of independently
  published facts. No dictionary page text or copied definitions were cleared.
  [2016 edition listing](https://garudalife.in/dictionary-english-garhwali-hindi),
  [2007/2013 edition discussion](https://e-magazineofuttarakhand.blogspot.com/2015/08/blog-post_79.html).
- These checks found no new blanket permission for the 19,466 distinct
  pending texts. Facts may be independently re-collected from sources whose
  terms permit it, but this does not clear the original prose, lyrics, OCR
  pages, or a source collection's expressive selection and arrangement.

## Cleared or conditionally shareable text

- **12,258 exact-unique values:** the public builder finds a source-specific
  compatible open-license or work-specific public-domain basis and carries its
  evidence/attribution. The build does not
  convert a URL or a repository's general license into a license for unrelated
  material.
- **134 CC BY-NC-SA 4.0 values:** 128 HinDialect and 6 PanLex-only values.
  These may be shared with attribution under noncommercial/share-alike terms;
  they are not cleared for unrestricted commercial training or commercial
  redistribution. PanLex's official current database terms are CC BY-NC-SA
  4.0, even though a third-party Hugging Face snapshot labels itself CC0; this
  candidate follows the more restrictive official source terms pending
  clarification. [HinDialect record](https://b2find.eudat.eu/dataset/bd804d5e-e53c-5ee3-b48c-cd2ecbad34de),
  [PanLex license](https://panlex.org/license/),
  [PanLex mirror card](https://huggingface.co/datasets/lbourdois/panlex).
- **5 PIB instrument values:** reproduced with prominent attribution under the
  PIB's source-specific reproduction policy. This is not a Creative Commons
  license, does not cover third-party material, and does not explicitly settle
  commercial use. [PIB copyright policy](https://www.pib.gov.in/ContentPage.aspx?lang=2&menuid=3604&reg=48).
- **193 Mountain Voices glossary headwords:** the archive's use guidance
  expressly allows attributed reproduction by press, educational and research
  institutions, and nonprofit organisations. The exported catalog contains
  only the headword field; English definitions and list arrangement are
  omitted. The row records the eligible audiences and attribution requirement.
  The guidance does not expressly address commercial scope or machine-learning
  training, so these values are excluded from the text/ASR/model-training
  views and do not carry a general open license. [Panos use guidance](https://mountainvoices.org/transcripts.html),
  [Mountain Voices glossary](https://mountainvoices.org/i_glossary.html).
- **16 isolated individual-word facts:** 11 previously selected one-token
  values plus five one-token facts found in two distinct thematic lexical
  sources. The five cross-source facts do not reproduce the larger animal or
  occupation lists. The release omits definitions, sentences, source record
  positions, and list ordering. Other one-token candidates remain pending
  where publishing them as a batch could reproduce a source compilation's
  selection; OCR/mixed-language/unconfirmed-language tokens and tokens from
  prose, grammar PDFs, or literary works also remain redacted. The Indian
  Copyright Office's draft *Practice and Procedure Manual: Literary Works*
  says a single word cannot be protected as a literary work; its copyright
  handbook says factual information and short word combinations are not
  ordinarily protected. This is a narrow fact-only publication basis, not a
  source license or legal clearance for the source compilations; all 16 remain
  out of model-training views and retain language-review flags. [Copyright Office draft manual](https://copyright.gov.in/Documents/Manuals/LITERARY_MANUAL.pdf),
  [Copyright Office handbook](https://copyright.gov.in/documents/handbook.html).
- **50 Open Bible Stories texts:** exact Garhwali OBS-TLF v1 text is covered by
  CC BY-SA 4.0. Audio and illustrations are excluded. [Garhwali edition](https://openbiblestories.org/l/gbm/),
  [v1 release](https://git.door43.org/OBS-TLF/gbm_obs/releases/tag/v1). These
  50 form part of the 12,258 values with compatible open-license or
  work-specific public-domain evidence, not an extra total.
- **216 structured records:** all are exposed as factual/bibliographic
  metadata only (names, titles, dates, classifications, identifiers and
  citations). The projection omits notes, abstracts, song lyrics, translations,
  summaries, passages, and full-work text. This is not a rights clearance for
  the referenced work.

## Remaining text queue, by source association

Counts are exact-unique redacted text values linked to that source in the
current canonical catalog. One value can have several source links, so these
figures overlap. `source_id` resolves to the exact source record in the local
reference index and source manifests.

| Source ID | Values linked | Resolution / next action |
| --- | ---: | --- |
| `paharili_gbm` | 14,999 | PahariLI's root Apache-2.0 declaration does not identify component terms for this mixed Garhwali corpus: the paper describes 10,000 blog/story/commentary/play/interview excerpts and 5,000 sentences from an unspecified New Testament edition. The imported rows have no component map. A distinct GHMNT edition by The Love Fellowship is credited CC BY-SA 4.0, but PahariLI does not identify that edition or verse references. YouVersion prohibits automated access/copying; Zeno's terms prohibit systematic retrieval to build a database without its written permission. No authorized bulk text copy was available in this check. No PahariLI subset is cleared. Obtain an authorized publisher text copy or permission, then match before changing row decisions; keep unmatched scripture and web excerpts pending. [PahariLI repository](https://github.com/rachanagusain/PahariLI), [repository license](https://github.com/rachanagusain/PahariLI/blob/main/LICENSE), [Gusain et al. 2023](https://doi.org/10.1007/s10579-023-09651-6), [GHMNT license credit](https://www.bible.com/bible/3164/1PE.5.GHMNT), [YouVersion terms](https://www.bible.com/terms), [Zeno terms](https://zeno.fm/terms/) |
| `emagazineofuttarakhand` | 1,770 | Author-attributed posts; at least one post has an explicit 2019 copyright notice. No blanket license. Seek author permission; otherwise publish citations and factual metadata only. [e-Magazine](https://e-magazineofuttarakhand.blogspot.com/) |
| `uou_cgl` | 436 | Per-PDF page 3 says no part may be reproduced without UOU written permission; this conflicts with current sitewide SLM CC BY-NC-SA wording, and pages quote third-party works. Get written clarification and component licenses. [UOU terms](https://uou.ac.in/terms-use), [CGL-101 PDF](https://uou.ac.in/sites/default/files/slm/CGL-101.pdf) |
| `uou_more` | 156 | Same PDF notice/third-party-excerpt conflict; keep full OCR pending. Request item- and component-level permission. |
| `govind_chatak_gadwali_lokgeet_1956` | 370 | The author died in 2007; under the Indian life-plus-60 term the work is not public domain until after 2067, subject to the correct author/edition/jurisdiction. Keep scan/OCR local; bibliographic facts may be public. [Author profile](https://rajkamalprakashan.com/author/govind-chatak), [Copyright Act §22](https://copyright.gov.in/Copyright_Act_1957/chapter_v.html) |
| `shanti_chaudhary_garhwali_lokkala_loksahitya_1994` | 298 | No compatible license or public-domain basis found for this 1994 book. Seek publisher/author permission. |
| `incoming_garhwali_hindi_dictionary` | 239 | User-supplied scan; no redistribution authorization from the publisher/author. Preserve OCR locally and request permission. |
| `incoming_garhwali_bhasha_linguistic_grammatical_study` | 147 | User-supplied scholarly scan; permission not established. |
| `incoming_english_hindi_garhwali_dictionary` | 123 | User-supplied dictionary scan; individual lexical facts may be independently re-sourced, but do not export copied definitions/selection without permission. |
| `incoming_chandola_syntactic_sketch` | 110 | User-supplied scholarly scan; no compatible redistribution grant recorded. |
| `incoming_garhwali_language_and_culture` | 76 | User-supplied book scan; no compatible redistribution grant recorded. |
| `incoming_gadwali_sahitya` | 74 | User-supplied literary scan; no compatible redistribution grant recorded. |
| **User-supplied PDFs subtotal** | **769** | Sum of the six source associations above; obtain permissions or separately verify source-level public-domain status. User-provided copies are not publication permission. |
| `dcad_gbm` | 119 | Dataset packaging does not establish rights in crawled source-page text. Resolve source lineage and component terms. |
| `idioms_proverbs` | 99 | No license for the copied collection. Independently documented short sayings may be evaluated one by one; do not redistribute the collection/annotations wholesale. [Dhyani collection](https://sites.google.com/view/dhyani/) |
| `emagazine_animals` | 92 | Public page without a reuse license; five exact one-token facts also appear in a distinct thematic lexicon and are exposed without definitions, source record positions, or list ordering. Other source-associated values remain pending. |
| `languageshome` | 80 | No compatible content license recorded; request permission for sentences and phrases or extract independently verifiable facts with citations. Eight exact one-token values are exposed without the source list, ordering, or accompanying sentences. |
| `dhyani_occupations` | 65 | No reuse license for the copied list/wording. Its individual terms remain in local all-data; bulk headword export could reproduce the source selection. |
| `uttarakhandiwords_animals` | 52 | Public blog without a stated open license; five exact one-token facts also appear in a distinct thematic lexicon and are exposed without definitions, source record positions, or list ordering. Other source-associated values remain pending. |
| `garhwalilanguage_dictionary` | 26 | No compatible license found; its individual terms remain in local all-data. Bulk headword export could reproduce the source selection. |
| `hikinegi_garhwali` | 53 | Hub dataset has no declared dataset license/authorship terms; exact strings are retained locally. |
| `euttaranchal_3` | 38 | Site terms prohibit copying/publishing site content without written consent; third-party rights remain with authors. Seek written consent. [Terms](https://www.euttaranchal.com/about_us/tos.php) |
| `euttaranchal_2` | 34 | Same explicit site restriction; seek written consent. |
| `euttaranchal_1` | 23 | Same explicit site restriction; seek written consent. |
| `madlad400_gbm_clean` | 18 | Crawl-derived rows lack item-level author/source rights; a dataset/dump license cannot grant rights in crawled pages. |
| `records` | 12 | Public social-post text; no author consent/reuse license. Preserve reference identifiers privately and publish aggregate/factual metadata only. |
| `omniglot` | 4 | No reuse license found for copied phrase text; seek permission or make independently sourced entries. |
| `archive_folksong_thesis` | 1 | Archive metadata is CC BY-NC-SA, but the thesis contains quoted/collected songs with unresolved component rights. Review the exact passage and underlying songs; keep text pending. |
| `uttarakhandkhabarsaar` | 2 | The source identifies a Garhwali news/publishing site, but no compatible text-reuse grant is recorded for these two article values. Preserve citation and seek publisher permission; do not infer permission from public access. |

The source-associated table deliberately reports overlapping links. It contains
the 19,466 distinct pending strings but its rows are not additive. Its purpose
is to route permissions and provenance checks; it is not a claim that every
association represents a distinct text.

## Structured records: all 216 accounted for

The public v2.1.0 release makes every structured record discoverable in six
metadata configurations: geography 50, historical terms 36, literary people
26, literary works 66, popular songs 30, university research 8. The public
projection contains no source prose, full abstracts, lyrics, translations,
extended notes, or full-work text. Any song lyrics/audio, full book, thesis,
paper, and university course text remains in local all-data or is referenced by
source URL only. A metadata row is not an assertion that the underlying work is

## Release integrity checks

- Public and all-data v2.1.0 packages each pass
  `scripts/validate_hf_package_cloud.py` with zero errors. The public
  preflight checks 162,494 overlapping config/view rows; the all-data
  preflight checks 300,915. These are package-view counts, not unique examples.
- A row-level comparison confirms 32,072 matching catalog identities, all
  32,072 local full-text values present, exactly 12,606 public text values, and
  exactly 19,466 rights-pending texts redacted. No `rights_pending` row has a
  non-null public text payload.
- The 16 fact-only word rows expose neither source record positions nor list
  ordering and remain excluded from text, ASR, and model-training views.
- All 216 public structured rows pass the strict factual-field allowlist. The
  export contains no `notes`, `abstract`, `lyrics`, `translation`, `summary`,
  `source_passage`, or full-work text fields. No field value exceeds 240
  characters; the longest field is the generic 181-character metadata note.
- The current code suite passes **671/671 pytest** and **669/669 unittest**
  tests. This is implementation/package verification, not language validation.
- The public v2.1.0 package has 42 versioned release files / 601,509,542 bytes,
  plus the root dataset card (43 upload paths total). The 51-file /
  689,449,417-byte all-data package remains local. The Dataset Viewer/parquet
  endpoint returned HTTP 500 on the initial check and its single retry; preview
  availability remains unverified. The remote file tree and docs-only head
  `f2def9e` were verified after the content release.

## Release checklist and follow-up

- [x] Preserve every acquired full text in the local all-data package; all-data
  manifest reports 0 redacted catalog values.
- [x] Publish exact counts and source-level decisions; retain source links,
  attribution, evidence, and conditions.
- [x] Publish all 216 structured records as a field-limited fact/bibliographic
  projection.
- [x] Share 12,258 compatible-open, 134 NC-SA, 5 PIB-policy, 193 Mountain
  Voices policy, and 16 individual-word fact values with their distinct
  per-record conditions in the public v2.1.0 package.
- [x] Upload the public v2.1.0 package additively at Hub commit `53c1ce9`; no
  earlier versioned files were deleted.
- [ ] Recheck Dataset Viewer/parquet availability after the recorded HTTP 500
  on both the first request and one retry; release-file integrity is verified
  independently of the preview service.
- [ ] Obtain written permissions for the 1,770 e-Magazine and 95 eUttaranchal
  source-associated values; retain overlap-aware counts.
- [ ] Resolve the PahariLI row-level blog/translation provenance (14,999 linked
  values) with the repository authors and underlying source owners. Do not
  scrape Bible.com to obtain GHMNT; first obtain an authorized text copy or
  platform permission.
- [ ] Obtain publisher/author permission or component-level licenses for the
  six incoming books (769 source associations), both UOU texts (592), and the
  two modern literary books (668 total source associations, with source overlap
  checked at record level).
- [ ] Re-source vocabulary and proverb facts independently rather than
  republishing protected compilation wording; then exact/fuzzy deduplicate and
  preserve citations.

No pending row was deleted, and no pending payload was labeled public because
it lacked an explicit “private” marker. Full text is redacted only in the
public redistribution view; it stays present in local all-data. Copyright
protection generally arises automatically; a “private” label is not the test
for reuse permission. A successful future rights change requires an actual
open license/permission, authoritative public-domain evidence for the exact
work and jurisdiction, or a redesigned factual projection that no longer
republishes protected expression.
