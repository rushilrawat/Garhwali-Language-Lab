# Internet Archive deep search and intake — 2026-10-03 to 2026-10-04

## Outcome

The first Internet Archive search returned **70 text-item records, 27 audio
listings, and 17 video listings**. The 4 October title-focused pass returned
21 directly titled text items, 22 audio listings, and 6 video listings; broader
regional queries were much noisier. These are discovery counts, not counts of
Garhwali sources. Search results include government records, scientific
papers, duplicate scans, metadata-only leads, and regional references.

Across this intake, **119 source payload files total 6,005,077,831 bytes
(6.01 GB / 5.59 GiB)**. They include 26 PDFs with OCR sidecars, 24 MP4s, and
15 MP3s. Every payload has a unique SHA-256 among the downloaded files. The
five latest books add 15 PDF/OCR files; the ten newly screened instructional
audio tracks add 10 MP3s. Archive file sizes and advertised SHA-1 values were
verified for these latest acquisitions. Item manifests, Archive metadata, and
rights notes remain with the ignored source files under `data/downloads/`.

The local page-level index now has **3,369 OCR page records, 3,368 exact-unique
normalized page texts, 4,960,578 normalized characters (4,960,579 source text
characters)**. A canonical comparison found zero exact and zero ≥0.85 5-gram
near-match candidates against the 32,072-row cleaned parent-text view. One
repeated OCR page is flagged. Sixty-one pages
from a 1959 alternate scan belong to the same work as the supplied Garhwali
grammar and are not counted as a new book. Most added history, geography, and
botany pages are English or Hindi contextual references; their inclusion is
not a claim that they are Garhwali passages. Automated page/media quality
signals and the canonical-text overlap method are documented in the
[intake quality and overlap audit](internet-archive-intake-quality-2026-10-04.md).

The 39 local audio/video files total **14:09:25.531 of playback**. That is
media duration, not verified Garhwali speech hours: sources include mixed
Garhwali/Kumaoni material, Hindi and English presentations, an unreviewed
Garhwali-labeled film, and short language-learning tracks. Nothing from this
intake has been segmented, language-reviewed, or transcribed. No new material
has been added to GitHub or the published Hugging Face v0.2.3 package.

## New language-study text intake

| Work | Acquired files | OCR result | Rights and use status |
| --- | --- | --- | --- |
| Gunanand Juyal, *Madhya Pahadi Bhasha Garhwali Kumauni Ka Anushilan Aur Uska Hindi Se Sambandh* (1967), [Internet Archive item](https://archive.org/details/ycbf_madhya-pahadi-bhasha-garhwali-kumauni-ka-anushilan-aur-uska-hindi-se-samban) | 65,446,978-byte PDF, DjVu text and XML | 203 scan-page objects; 201 non-empty page records; 200 exact-unique texts; 297,528 characters; zero exact overlap in the source/extraction layers scanned at intake | Archive uploader metadata claims CC0 1.0. Uploader authority and the claim are unverified. Kept as local reference OCR; not marked training-eligible. |
| Haridatta Bhatta ‘Shailesh’, *Garhwali Bhasha Aur Uska Sahitya* (1976), [Internet Archive item](https://archive.org/details/ezqp-garhwali-bhasha-aur-uska-sahitya-by-haridatta-bhat) | 166,004,711-byte PDF, DjVu text and XML | 444 scan-page objects; 443 non-empty and exact-unique texts; 578,264 characters; zero exact overlap in the source/extraction layers scanned at intake | Archive uploader metadata claims CC0 1.0. Uploader authority and the claim are unverified. Kept as local reference OCR; not marked training-eligible. |
| Govind Chatak, *Gadwali Lok Gathayen* (1958), [Internet Archive item](https://archive.org/details/dli.ernet.426855) | 9,024,147-byte PDF, DjVu text and XML | 278 scan-page objects; 276 non-empty, exact-unique page texts; 227,796 characters; zero exact overlap in the source/extraction layers scanned at intake | Garhwali folk-ballad collection by title; individual OCR page language and transcription quality remain unreviewed. No explicit reuse license recorded. |
| Govind Chatak, *Gadwali Bhasha* (1959), [Internet Archive item](https://archive.org/details/in.ernet.dli.2015.347446) | 1,611,015-byte PDF, DjVu text and XML | 66 OCR pages; 61 non-empty page records; zero exact overlap in the source/extraction layers scanned at intake | Title page matches the user-supplied 1959 grammar. This alternate/partial scan is retained for comparison, flagged as a work-level duplicate, and not counted as a new book. |

The page-level records are in the ignored local directory
`data/extracted/research/internet_archive_language_studies_2026-10-03/`.
The reproducible extractor is
[`scripts/ingest_archive_language_studies.py`](../scripts/ingest_archive_language_studies.py).
It preserves every non-empty page, flags the one exact repeated OCR page within
the Juyal book, and checks overlap against existing text layers. The source
files and page OCR still need language, OCR, and rights review before any
public dataset inclusion.

## Historical reference scans

| Work | Download and evidence | Scope |
| --- | --- | --- |
| H. G. Walton, *British Garhwal: A Gazetteer* (1910), [Archive item](https://archive.org/details/in.ernet.dli.2015.48008) | PDF, DjVu text/XML, scan data; all four files match Archive sizes and SHA-1 checksums. DLI's embedded metadata says `dc.rights: In Public Domain`; the 266-page extent is recorded in the item description. | English historical geography reference. The project already has two targeted language-description page records; this full scan adds no Garhwali training records. |
| *Himalayan Folklore: Kumaon and West Nepal* (1935), [Archive item](https://archive.org/details/in.ernet.dli.2015.532407) | 376-page PDF, DjVu text/XML and metadata; the PDF is 20,600,307 bytes. Hashes are in its local manifest. | Mostly English accounts/translations of Kumaoni and Garhwali oral ballads. The source is described as public domain in India; a U.S. term may continue through 2030. Kept as local cultural reference, not counted as Garhwali-language text or cleared for Hub redistribution. |

## Additional regional-reference OCR index

The reproducible page index is generated by
[`scripts/ingest_archive_dabral_references.py`](../scripts/ingest_archive_dabral_references.py)
and
[`scripts/ingest_archive_regional_historical_references.py`](../scripts/ingest_archive_regional_historical_references.py).
Both verify the source PDF and OCR SHA-1 values, retain exact source-page
references, and compare normalized page text against the source/extraction
layers included in their intake-time scan. Their combined output contains
**2,267 page records, all exact-unique within those books, with zero exact
overlap in the checked source/extraction layers**. The separate canonical
cleaned-text check is summarized in the [quality audit](internet-archive-intake-quality-2026-10-04.md).
These
are keyword-selected Hindi/English regional reference pages, not a Garhwali
training-text count.

| Work(s) | Selected page records | Source/rights note |
| --- | ---: | --- |
| Shiv Prasad Dabral: *Uttarakhand Ka Itihas* Vol. 1 (186), Vol. 3 (137), *Alakananda Upatyaka Mein Pravas* Vol. 1 (123), *Uttarakhand Ke Bhotantik Alaknanda Upatyaka Mein Pravas* Vol. 2 (248), and *Shri Uttarakhand Yatra Darshan* (284) | 978 | Hindi history/geography OCR. Four Archive records make uploader CC0 claims that remain unverified; *Yatra Darshan* has no explicit reuse license. |
| *Garhwal Ke Pracheen Abhilekha Aur Unka Itihasika Mahatva* (172), Mahidhar Sharma Barthwal, *Garhwal Me Kon Kahan Se* (96), Rahul Sankrityayan, *Himalaya Parichay, Vol. 1: Garhwal* (305), and *Note On The Bhotias Of Almora And British Garhwal* (24) | 597 | Three Hindi regional references and one English ethnographic reference. Archive CC0/Public Domain Mark claims remain unverified; the Bhotias item lists CC BY-NC 4.0. |
| Rai Pati Ram Bahadur, *Garhwal Ancient and Modern* (1916) [Archive](https://archive.org/details/in.ernet.dli.2015.43255); *Peaks and Passes of Garhwal Himalaya* (1990) [Archive](https://archive.org/details/dli.pahar.3635); *Uttar Pradesh District Gazetteers: Tehri Garhwal* (1971) [Archive](https://archive.org/details/dli.ministry.08781); Strachey and Duthie, *Catalogue of the Plants of Kumaon and of the Adjacent Portions of Garhwal and Tibet* (1906) [Archive](https://archive.org/details/catalogueplants00duthgoog); Dharmanand Joshi, *Notes on the Garhwal District* (1910) [Archive](https://archive.org/details/dli.ministry.29693) | 692 | Five new English history, geography, district, and flora references. The Peaks item has an unverified Archive CC BY-NC 4.0 uploader claim; the other four show no item-level reuse license. Vernacular botanical terms were not confirmed. |

All 2,267 rows remain local reference material with `training_eligible=false`
and `public_redistribution_eligible=false`. The code indexes pages containing
explicit place or region terms; it does not classify their language as
Garhwali.

## Archived speech and cultural media

| Archive item | Local media | Metadata evidence and disposition |
| --- | --- | --- |
| [ICCR-1282, *Garhwali Folk Songs*](https://archive.org/details/dni.ncaa.ICCR-1282-AC) | Two MP3 cassette sides; 33:23.136 total | The item describes Garhwali and Kumaoni folk songs by Yogender Bhandari and group. ICCR is named as rights holder; no permissive reuse license is stated. Preserved locally, with no transcription or training use. |
| [IGRMS, *Pahadi Cultural of Uttarakhand*, Vol. III](https://archive.org/details/dni.ncaa.IGRMS-A_599-AC) | Two MP3 sides; 1:33:09.024 total | Archive labels CC BY-NC 4.0 and describes Garhwali songs and Holi songs within a regional cultural program. Noncommercial terms remain attached; language proportions are not measured. |
| [IGRMS Bagwal Festival, Devidhura, Vols. I–III](https://archive.org/details/dni.ncaa.IGRMS-S_VHSC_29-SVHS) | Three MP4s; 1:36:23.891 total | 1996 recordings. Archive metadata labels Kumaoni and Garhwali and CC BY-NC 4.0. The three downloaded volumes form the complete listed series. |
| [CCRT, *Folk Music of Garhwal*, Vol. I](https://archive.org/details/dni.ncaa.CCRT-447-UMHB) and [Vol. II](https://archive.org/details/dni.ncaa.CCRT-448-UMHB) | Two MP4s; 1:16:42.320 total | Archive identifies CCRT as rights holder but states no permissive reuse license. These are local source copies only, pending terms review. The MP4 was selected for Vol. II; its separate MP3 was not copied as a second format of the same item. |
| [*MarginalizedAadhaar: Sampati*](https://archive.org/details/marginalized-aadhaar-sampati) | Seven original-resolution MP4 segments (`01`–`06` and `08`); 5:36.920 total | Creator metadata claims CC BY 4.0 and describes the speaker as using the Saunpuri Garhwali dialect. The Archive item contains no `07` file. Its description notes personal discussion of disability, poverty and Aadhaar enrollment; this intake does not transcribe it, use it for model training, or include it in a public speech release pending content and consent review. |
| [IGRMS Joshimath / Neeti Valley, Vols. I–V](https://archive.org/details/dni.ncaa.IGRMS-3B_2-BC) | Five MP4s; 3:02:37.981 total | The item records label language as Garhwali and Hindi and identify IGRMS as rights holder. No reuse license is recorded; locally preserved only. |
| [JESUS Film Garhwali Language](https://archive.org/details/jesus-film-garhwali-language) | One MP4; 2:01:44.115 | Archive title claims Garhwali. Language share has not been independently checked; no reuse license is recorded. |
| [Beej Bachao Andolan documentary series, Vols. I–V](https://archive.org/details/dni.ncaa.CVI-BH_R_39-BC) | Five MP4s; 2:59:09.800 total | Archive records claim CC BY 4.0. These are regional documentary interviews; Garhwali speech share is unmeasured and noncommercial status has not been separately evaluated. |
| [Garhwali-labeled instructional audio series](https://archive.org/details/1-salutations-garhwali) | Ten unique MP3 tracks; 18:30.831 total | Greetings, routines, song, naming/designation, and object-action titles. Duplicate mirrors were excluded by exact SHA-1. No transcripts or reuse license are recorded; no track has been language- or speaker-reviewed. |
| [Narendra Singh Negi, “TuDikhyandi”](https://archive.org/details/GarhwaliGeet) | One MP3; 5:40.565 | Archive lists CC BY-NC-ND 3.0. Kept as source-only; no transcription, adaptation, training, or public speech release. |
| [IGRMS Virasat, Vol. VII](https://archive.org/details/dni.ncaa.IGRMS-3B_184-BC) | One MP4; 36:26.948 | Regional cultural presentation, locally preserved; no reuse license is recorded. |

Across all 39 local audio/video files, playback time is **14:09:25.531**. The
recordings are not transcripts, and the mixed-language recording duration
must not be reported as Garhwali speech hours. Audio/video payload hashes,
rights statements, and full Archive metadata are saved alongside the files in
`data/downloads/{audio,video}/internet_archive/`.

Four related [IGNCA Garhwal Festival audio volumes](https://archive.org/details/dni.ncaa.IGNCA-AC_1091-AC)
were inspected but not acquired: their item descriptions identify English
lectures, museum presentations and an exhibition, not Garhwali speech or folk
music. This avoids inflating the language-media inventory with region-only
metadata.

## Exact duplicate and recovery decisions

- The 1994 Shanti Chaudhary thesis already existed as a PDF/OCR and 298 page
  records. PDF, OCR text and XML hashes matched the Archive files exactly. The
  existing source now has a complete metadata/hash manifest; the duplicate
  temporary copy from this search was removed.
- The 1954 *Gadwali Sahitya ki Bhumika* scan matches the supplied
  `incoming/pdfs/Gadwali Sahitya.pdf` SHA-1 exactly:
  `1ca3d737d81b2998345b3748a6cf6d748b86f84a`.
- The 1959 *Garhwali Bhasha* scan matches the supplied
  `incoming/pdfs/Garhwali Bhasha_ Ek Bhashashashtriya Aur Vyakarnik Adhyayan.pdf`
  SHA-1 exactly: `e2c8f7e0976144ab1dcfc82bfb3152e63096335a`.
- The 1956 *Gadwali Lokgeet*, 1894 Upreti book, and 1916 Linguistic Survey
  materials were already represented in local source/extraction layers and
  were not recounted.
- Wayback confirms two 1920 DSAL/LSI Garhwali recordings: a story and the
  Prodigal Son parable. Their linked MP3s are absent from Wayback and return
  404 on the current host. They remain documented recovery leads, not ingested
  audio.

## Release status and next work

Raw downloads and generated page OCR are Git-ignored. The current Hugging Face
v0.2.3 package and GitHub release numbers are unchanged; nothing from this
intake has been uploaded. The records remain visible locally with source IDs,
quality and rights status rather than being removed. Before adding any of these
items to a public dataset, the next work is to inspect and segment recordings,
separate speech/music/lecture and Garhwali/Kumaoni/Hindi, transcribe only
appropriate speech, and resolve each item's reuse scope. The two books can be
considered for a separately labeled research/reference view after the uploader
CC0 claim is checked.
