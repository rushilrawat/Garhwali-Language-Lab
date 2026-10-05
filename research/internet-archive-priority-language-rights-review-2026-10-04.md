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

## Next work

1. Build page/section maps for the two strongest Garhwali sources, Chatak and
   Shailesh, keeping Garhwali examples, Hindi translations, and editorial
   discussion in separate reversible views. Re-run corpus-wide exact/near
   duplicate checks before counting any newly extracted segments.
2. Re-OCR only pages with transparent OCR-warning or empty-content signals;
   keep original OCR and machine-corrected text side by side. Do not call the
   result language-correct without native review.
3. Continue rights research for the five works, especially the Shailesh CC0
   authority, Juyal conflict, Chatak rightsholder, and the 1977 reprint layer.
4. Review Archive audio/video language and transcript content as a separate
   source family. Do not include its 14-hour playback duration as Garhwali
   speech until language content is measured.

### Sources checked

- [Harvard-hosted Oral Tradition research on Garhwali epics and Chatak's work](https://oraltradition.org/vocal-delivery-and-ritual-epic-performance-in-central-himalayan-pandava-stories/)
- [LBSNAA catalogue: *Garhwali Bhasha Aur Uska Sahitya* (1976)](https://gsl.lbsnaa.gov.in/cgi-bin/koha/opac-detail.pl?biblionumber=206983)
- [LBSNAA catalogue search result for Juyal's 1967 comparative-language study](https://gsl.lbsnaa.gov.in/cgi-bin/koha/opac-search.pl?count=100&limit=su-to%3AHindi&q=ccl%3Dpl%3A%22Lucknow%22+and+itype%3AREF&sort_by=relevance_dsc)
- [CiNii university-library record for the 1977 *Himalayan Folklore* reprint](https://ci.nii.ac.jp/ncid/BA3260610X)
- [Internet Archive Rights guidance](https://archivesupport.zendesk.com/hc/en-us/articles/360014759692-Rights)
- Indian Copyright Act: [definition of Government work](https://copyright.gov.in/Copyright_Act_1957/chapter_i.html), [first ownership](https://copyright.gov.in/Copyright_Act_1957/chapter_iv.html), and [terms of copyright](https://copyright.gov.in/Copyright_Act_1957/chapter_v.html).
- Local primary evidence retained in the intake: Chatak page `0004`/`0005`; Juyal pages `0008`/`0009`; Shailesh pages `0008`–`0010`; Himalayan Folklore scan page `0005`; Snow Balls rights note in `data/downloads/folklore/internet_archive/snow_balls_garhwal_1946/download_manifest.json`.
