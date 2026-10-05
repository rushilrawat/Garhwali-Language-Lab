# Internet Archive priority-language and rights evidence review — 2026-10-04

## Finding

The source-level evidence now distinguishes Garhwali text collections from
regional research and English translations. It does **not** justify assigning
Garhwali labels to individual OCR pages or clearing any of these five works for
public redistribution or model training. All source files and candidate pages
remain preserved in the ignored local intake; no rows were removed and none
were added to the public corpus or Hugging Face releases.

The automated evidence summary is reproducible with
[`audit_archive_priority_page_evidence.py`](../scripts/audit_archive_priority_page_evidence.py).
Its machine-readable output is kept in the ignored
`data/extracted/research/internet_archive_priority_language_evidence_2026-10-04.json`.
The source OCR and candidate records remain in the ignored
`data/extracted/research/internet_archive_candidate_views_2026-10-04/` folder.

## Scope and page-level evidence

| Review group | Page objects | Non-empty OCR | Distinct normalized non-empty values | Script profile and text evidence |
| --- | ---: | ---: | ---: | --- |
| Three Garhwali-language/folklore studies | 920 | 920 | 919 | Chatak: 275 mostly Devanagari, 1 no-letter row. Juyal: 94 mostly Devanagari, 100 mixed Devanagari/Latin, 7 mostly Latin. Shailesh: 36 mostly Devanagari, 393 mixed, 14 mostly Latin. |
| Two translated/regional-folklore books | 440 | 432 | 431 | Himalayan Folklore: 368 mostly Latin pages and 8 empty pages. Snow Balls: 63 mostly Latin, 1 no-letter row. These are English-language/context signals, not Garhwali labels. |

Across these five sources there are 1,360 page objects, 1,352 non-empty OCR
rows, 1,350 distinct non-empty normalized values, one repeated normalized text
group, and one non-empty OCR row that normalizes to nothing. The repeated pair
is Juyal pages `0002` and `0203`; both contain only the same digitizer footer,
not book text. The normalization-empty row is Snow Balls page `0056`. These
three rows remain in the inventory and should not count as language content.

Script counts are computed automatically from Unicode characters. They cannot
separate Garhwali from Hindi in Devanagari, find page boundaries between
original and translation, or certify OCR correctness. OCR-warning rows are
heuristic flags: 29 of the 920 language-study pages and 7 of the 440
translated-folklore page objects have at least one flag. They are not measured
word error rates.

## Work-by-work interpretation

### Govind Chatak, *Gadwali Lok Gathayen* (1958)

The scan title page identifies the 1958 first edition and Mohini Prakashan.
The local OCR has 276 non-empty page rows (227,796 normalized characters),
275 mostly Devanagari pages, and five OCR-warning rows. A Harvard-hosted
scholarly article describes the 1958 work and 1996 revision as containing 47
epic texts, presented in Garhwali followed by Hindi translation, and discusses
four overlapping genre headings. That supports the book-level classification
as an important Garhwali/Hindi folk-epic source; it does not label every page
of this specific 1958 scan or supply a reusable-content license. The scan's
preface asks readers using excerpts to cite the book; that is attribution
guidance, not permission to reproduce the full work.

**Use decision:** high-priority local source for page/section mapping and
language-aware OCR work; no public text or training clearance recorded.

### Gunanand Juyal, *Madhya Pahadi Bhasha (Garhwali Kumauni) ...* (1967)

The LBSNAA catalogue confirms the 1967 Navyug Granthagar edition. The title
page calls it a dissertation on Garhwali and Kumauni and their relation to
Hindi, so it is a mixed-language comparative reference, not a Garhwali-only
textbook. The 201 page rows contain 297,528 normalized characters across
Devanagari, mixed-script, and Latin profiles. Three rows trigger OCR warnings.

The Archive record has an uploader-selected CC0 claim and the scan repeats a
digitizer CC0 watermark, but the book's own page `0009` says “all rights
reserved.” The claim and the facsimile therefore conflict. The duplicate
footer-only pages `0002` and `0203` are also excluded from any useful-text
count while remaining preserved in the source inventory.

**Use decision:** bibliographic and comparative-linguistics reference only;
the CC0 claim is not accepted as verified permission.

### Haridatta Bhatta ‘Shailesh’, *Garhwali Bhasha Aur Uska Sahitya* (1976)

The LBSNAA catalogue identifies the 1976 U.P. Hindi Samiti edition and
classifies it under Garhwali language history and criticism. The scan's
preface identifies the Uttar Pradesh Government Hindi Samiti; the author's
preface describes field collection of Garhwali songs, epics, stories, and
legends. The OCR index contains 443 non-empty pages (578,264 normalized
characters), including mixed Hindi and Garhwali-script material, and 21
heuristic warning rows. This is strong work-level evidence that the book
contains Garhwali examples, but not page-level language validation.

The Archive uploader and digitizer assert CC0/public-domain status. No
rightsholder authorization for that assertion was located. The Indian
Copyright Act says Government is first owner of a Government work absent an
agreement to the contrary, and the term for such a work runs for 60 years from
the start of the calendar year after first publication. If those provisions
apply to this 1976 publication, the term could continue through 31 December
2036. The publisher/prelude evidence makes this a concrete ownership question,
not a basis for declaring the uploader claim false or for making a final legal
determination.

**Use decision:** priority source for local passage mapping; no public text or
training clearance recorded pending evidence of who owns and licensed the
work.

### *Himalayan Folklore: Kumaon and West Nepal* (Archive item dated 1935)

This item has a significant edition mismatch: Internet Archive/DLI metadata
dates it 1935, but the scanned title page and CiNii university-library record
identify a **1977 Kathmandu reprint** with a new introduction by Marc
Gaborieau. CiNii also notes that it reprints the 1935 edition. The local
candidate view has 376 page objects, 368 non-empty OCR pages (439,783
normalized characters), all mostly Latin, plus eight empty OCR pages. The
work is an English-language collection about Kumaon and Garhwal; this page
view is not Garhwali text. A 1935 date for the underlying edition must not be
copied onto the 1977 scan as its edition date. No reuse license is recorded;
the reprint and its added introduction need edition-specific rights evidence.

**Use decision:** historical/translation reference, not Garhwali-language
training text; preserve the 1977-edition distinction and do not redistribute
OCR pending rights review.

### N. S. Bhandari, *Snow Balls of Garhwal* (1946)

The Archive's DLI metadata describes a 1946 English book from Universal
Publishers, Lucknow; the local extraction covers the Garhwal chapter (64
page-rows). It has 63 mostly Latin rows, one no-letter row, three OCR-warning
rows, and no Archive reuse license. The existing download manifest records an
“All Rights Reserved” notice in the scan. Its regional games and rhyming-game
descriptions may be culturally useful, but their English exposition is not
evidence of Garhwali-language text.

**Use decision:** local cultural-reference material only until a compatible
reuse basis is documented.

## Page map and alternate OCR pass — 2026-10-04

The page map joins the original DjVu XML layout to the existing candidate
records without changing either source. It covers all **722 scan pages**:
278 for Chatak and 444 for Shailesh. It aligns all **719 existing OCR rows**
(276 and 443 respectively) and retains three blank pages. A visual check of
Shailesh's contents page (physical scan page 13) identified **15 printed-page
ranges**. The printed-to-scan offset of **+13** was checked at physical pages
26 (printed 13), 27 (printed 14), and 439 (printed 426). The LBSNAA catalogue
also describes the edition as 426 pages. The initial OCR parser found only 13
line-ending page references; its result was incomplete and is not used as the
section map.

| Shailesh contents section | Printed pages | Physical scan pages |
| --- | ---: | ---: |
| Preface | 9–14 | 22–27 |
| Garhwali development | 15–31 | 28–44 |
| Grammar | 32–51 | 45–64 |
| Word sources and meanings | 52–62 | 65–75 |
| Published Garhwali literature | 65–140 | 78–153 |
| Folk songs | 141–179 | 154–192 |
| Folk epics | 180–309 | 193–322 |
| Folk tales | 310–357 | 323–370 |
| Proverbs | 358–366 | 371–379 |
| Riddles | 367–368 | 380–381 |
| Vocabulary appendix | 369–403 | 382–416 |
| Grierson classification appendix | 404–405 | 417–418 |
| Language-classification appendix | 406–408 | 419–421 |
| Bibliography | 409–411 | 422–424 |
| Word index | 412–426 | 425–439 |

Together, those ranges map **416 scan pages** to contents headings. Printed
pages 63–64 (scan pages 76–77) are not listed in the contents; 20 front-matter
pages plus the contents page and five unnumbered suffix scans remain
unassigned. The map does not turn a topic heading into a page-language label.
In particular, the `published_literature` range can contain poetry or other
quoted material, and the word index is not a verified lexicon. Chatak still
has no edition-specific page boundaries: genre cues and a scholarly outline
are work-level evidence only. Its five heuristic heading-candidate pages and
Shailesh's 33 heading-candidate pages remain unreviewed cues.

The reproducible map is generated by
[`build_archive_book_page_map.py`](../scripts/build_archive_book_page_map.py).
Its 722-row output, including a few short OCR heading/contents snippets, is
kept under Git-ignored `data/extracted/research/`; it is a local navigation
aid, not canonical text.

An alternate OCR pass covered every flagged page and every empty page: **29
pages** in total (7 Chatak, 22 Shailesh). It used Tesseract 5.5.2 LSTM with
`hin+eng`, 300 dpi, and page-segmentation mode 3. The official
[`tessdata_best` Hindi model](https://github.com/tesseract-ocr/tessdata_best/blob/main/hin.traineddata)
is Apache-2.0 licensed; the local model SHA-256 is
`bd2e65a2184af08a167b0be2439e91fa5edbc4394399ca2f692b843ae26e78d6`. Its
alternate output contains 30,184 characters versus 26,388 in the selected
original OCR rows (+3,796, or 14.4%). It produced text for 27 pages, including
one formerly empty page; two pages remain empty. Seventeen alternates are
longer, ten shorter, and two remain empty in both. No alternate is an exact
normalized match to its original. Mean Tesseract word confidence was 66.39
across five non-empty Chatak pages and 67.51 across 22 Shailesh pages.
Confidence, character growth, and script composition are not accuracy scores;
there is no verified reference transcript or native review for these pages.

The reproducible page-by-page comparison stores only IDs, hashes, counts,
script counts, and comparison signals—no OCR text. Of the 29 pages, three had
no original candidate row (the three pages with empty source OCR), two remain
empty in the alternate, and none is an exact normalized match. A conservative
triage rule marked 11 pages high, 3 medium, and 15 low priority for image
inspection based on empty/recovered output or character-sequence disagreement
(high below 0.50, medium 0.50–0.79, low at least 0.80). These are workflow
priorities, not OCR-quality grades.

Image-level inspection of all 11 high- and 3 medium-priority pages found that
several disagreements are non-content: Chatak pages 1, 260, 277, and 278 are
library/catalog or title matter; page 2 is blank; Shailesh page 2 is a damaged
title leaf with a digitization watermark; Shailesh pages 430 and 435–438 fall
in the word-index section; and Shailesh page 443 is a blank watermarked suffix
scan. Shailesh page 144 (printed page 131) is in the contents'
published-literature range and the two OCR versions disagree substantially.
**Correction after a full-resolution check:** Chatak scan page 144 has a sparse
heading whose existing six-normalized-character OCR record agrees with the
image. Scan page 145 is blank, and page 146 begins printed page 111. This
isolated heading is not a book-wide section map. No page text was corrected or
promoted; rights and linguistic accuracy remain unverified.

A separate duplicate audit compared these 29 alternates with all **32,072**
rows in `model_ready/cleaned/text`: zero exact normalized matches, zero
within-alternate duplicate groups, and zero ≥0.85 character 5-gram Jaccard
candidates among 17,924 scored pairs. This is scoped to that cleaned text
view and does not certify semantic uniqueness. Original OCR, alternate OCR,
and blank-page records are all preserved locally; none was promoted to
training, the canonical corpus, GitHub content files, or Hugging Face.

The map, alternate OCR, page comparison, and cross-view duplicate check are reproducible from
the repository root after installing the official Hindi model in the ignored
local OCR runtime:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/build_archive_book_page_map.py
PYTHONPATH=scripts .venv/bin/python scripts/reocr_archive_quality_pages.py
PYTHONPATH=scripts .venv/bin/python scripts/compare_archive_ocr_variants.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_alternate_ocr_overlap.py
```

The rendered page images are temporary and are removed after each page. The
OCR alternates, model, runtime links, and machine-readable audit outputs remain
under Git-ignored `data/extracted/research/`.

## Rights interpretation

The Internet Archive says it does not guarantee item copyright status or
uploader-provided rights information. It explains that the uploader may select
the displayed Creative Commons license. Accordingly, an Archive CC0 field or
a digitizer watermark is recorded as a claim, not treated as proof that the
uploader owned or could dedicate the book's rights.

For India, the Copyright Act's general term for named literary authors is
life of the author plus 60 years; a different 60-year-from-publication term
applies to Government works **where Government is the first owner**. The exact
authors, assignments, government-work classification, jurisdiction, and scope
of the 1977 reprint still need source-specific evidence. This report is an
evidence triage, not a legal opinion. Public online access is not treated as a
reuse license.

### Source-specific rights research follow-up — 2026-10-04

The follow-up searched for author-life evidence, edition records, and the
first-owner rules that could clarify the five works above. It found secondary
leads but no primary death record, assignment, publisher authorization, or
rightsholder response sufficient to change any eligibility state. Indian
sections 17 and 28 make Government ownership conditional on Government being
the first owner; a Government Press or Hindi Samiti imprint alone does not
establish that condition. Section 22 applies the author-life term to joint
works using the last surviving author. The 1992 amendment also says it does
not revive a work whose copyright had already expired when the amendment took
effect. These rules make early-author dates potentially material, but they do
not resolve the source facts or rights in other countries.

| Work | Evidence found | Conditional implication; current disposition unchanged |
| --- | --- | --- |
| *Gadwali Lok Gathayen* (1958; revised edition reported 1996) | Regional biographical accounts report Govind Chatak's death in 2007; no primary record or edition-specific rights transfer was found. | If that date is correct, the author held the relevant rights, and the Indian author-life term applies, the reported term would end 31 December 2067. The 1958 and revised 1996 contributions/ownership still need separation. Not cleared. |
| *Madhya Pahadi Bhasha ...* (1967) | A Garhwali-literature historian's profile reports Gunanand Juyal as 1905–1985, but this is not a primary life record. The scan says “all rights reserved”; the Archive CC0 claim conflicts with that notice. | If the reported death and author ownership are correct and the Indian author-life term applies, the term would end 31 December 2045. Neither that calculation nor the Archive claim resolves who owns the rights. Not cleared. |
| *Garhwali Bhasha Aur Uska Sahitya* (1976) | Secondary regional reports place Haridatt Bhatt “Shailesh”'s death in 2011. The edition identifies U.P. Hindi Samiti, but no employment, commission, assignment, or CC0 authority was found. | If the author held the rights, the conditional Indian author-life term would end 31 December 2071. If this qualifies as a Government work and Government was first owner, the conditional publication term would end 31 December 2036. The publisher imprint does not select either branch. Not cleared. |
| *Himalayan Folklore* (1935 original; 1977 reprint) | University catalogues identify E. S. Oakley and Tara Dutt Gairola as authors. Gairola's reported death conflicts: 1940 in a Wikipedia-derived record versus 1950 in a regional-literature article by a Garhwali historian. Oakley's reported 1935 death appears in a regional book page; contemporary records place a Rev. E. S. Oakley at Almora, but do not establish that identity or his death date. | If the reported Gairola dates and joint authorship are correct, the original may have expired in India: a 1940 last-author death implies expiry by 31 December 1990 under the then 50-year term; a 1950 death implies a still-subsisting term extended to 31 December 2010. The 1992 amendment bars revival of a term already expired. This is a jurisdiction-specific lead, not a worldwide clearance; the 1977 Gaborieau introduction is a separate layer with unresolved rights. The mixed-edition scan is not cleared. |
| *Snow Balls of Garhwal* (1946) | The scan says “All Rights Reserved”; no reliable author-life, assignment, or reuse evidence was found for N. S. Bhandari. | No term calculation or reuse basis can be established. Not cleared. |

The date leads are deliberately attributed rather than entered as verified
biographical facts. In particular, the two Gairola dates do not come from
independent primary records, and the historical missionary record's “E. S.
Oakley” has not been conclusively identified as E. Sherman Oakley. No release,
training, or public-rights flag changed after this research.

## Next work

1. Obtain primary rightsholder, assignment, or edition-specific permission
   evidence before changing any of the five works' reuse dispositions. The
   author-life research is complete for this pass but did not clear content.
2. Keep Chatak's full section map unresolved. Its scan page 144 heading and
   blank page 145 do not supply a contents map; do not infer section boundaries
   from this isolated cue or from the scholarly outline.
3. The technical media first pass is complete: all 39 files across 31 Archive
   items passed source-hash, size, duration, and stream checks, with no exact
   file duplicates. A sidecar scan covered 31 metadata snapshots / 1,047
   listed files and found no caption/transcript candidates or matching local
   sidecars. Six Archive language fields explicitly claim Garhwali, but none
   is verified at file or segment level. A separate local Whisper-tiny pilot
   produced one repetitive draft for 27.481 seconds; there is no reference to
   score, and the saved checkpoint's prior test result is 74.3% WER / 40.4%
   CER. Do not scale it for quality transcripts. Next, only consider a
   no-cost local model that can be independently evaluated on the frozen
   Garhwali validation set. Do not count 14-hour playback as Garhwali speech
   or change content/rights labels. See the
   [media first-pass report](internet-archive-media-first-pass-2026-10-04.md).

### Sources checked

- [Harvard-hosted Oral Tradition research on Garhwali epics and Chatak's work](https://oraltradition.org/vocal-delivery-and-ritual-epic-performance-in-central-himalayan-pandava-stories/)
- [LBSNAA catalogue: *Garhwali Bhasha Aur Uska Sahitya* (1976)](https://gsl.lbsnaa.gov.in/cgi-bin/koha/opac-detail.pl?biblionumber=206983)
- [LBSNAA catalogue search result for Juyal's 1967 comparative-language study](https://gsl.lbsnaa.gov.in/cgi-bin/koha/opac-search.pl?count=100&limit=su-to%3AHindi&q=ccl%3Dpl%3A%22Lucknow%22+and+itype%3AREF&sort_by=relevance_dsc)
- [CiNii university-library record for the 1977 *Himalayan Folklore* reprint](https://ci.nii.ac.jp/ncid/BA3260610X)
- [Internet Archive Rights guidance](https://archivesupport.zendesk.com/hc/en-us/articles/360014759692-Rights)
- Indian Copyright Act: [definition of Government work](https://copyright.gov.in/Copyright_Act_1957/chapter_i.html), [first ownership](https://copyright.gov.in/Copyright_Act_1957/chapter_iv.html), and [terms of copyright](https://copyright.gov.in/Copyright_Act_1957/chapter_v.html).
- [Copyright (Amendment) Act, 1992, including its no-revival clause](https://thc.nic.in/Central%20Governmental%20Acts/Copyright%20Act%2C1957.pdf).
- Secondary life-date leads: [Chatak biographical profile](https://www.merapahadforum.com/index.php?topic=844.130); [Juyal profile](https://www.merapahadforum.com/index.php?topic=844.40); [Shailesh obituary reprint](https://thenritime.blogspot.com/2011/09/noted-writer-dr-haridutt-bhatt-shailesh.html?m=0); [Gairola profile reporting 1950](https://e-magazineofuttarakhand.blogspot.com/2009/10/garhwali-kumaoni-himalayan-literature.html); [Gairola page reporting 1940 and Oakley 1935](https://uttarakhandhub.com/library/himalayan-folklore); [historical missionary-conference record mentioning Rev. E. S. Oakley at Almora](https://www.tamildigitallibrary.in/admin/assets/book/TVA_BOK_0047773/TVA_BOK_0047773_Report_of_the_Fourth_Decennial_India_Missionary_Conference_held_in_Madras_1902.pdf). These do not constitute primary death or assignment records.
- Local primary evidence retained in the intake: Chatak page `0004`/`0005`; Juyal pages `0008`/`0009`; Shailesh pages `0008`–`0010`; Himalayan Folklore scan page `0005`; Snow Balls rights note in `data/downloads/folklore/internet_archive/snow_balls_garhwal_1946/download_manifest.json`.
