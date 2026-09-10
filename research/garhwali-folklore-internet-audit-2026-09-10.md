# Garhwali folklore and folk-literature Internet audit

Updated 2026-09-10. This audit distinguishes public discoverability and file
download from permission to redistribute or use the text in a training corpus.
The raw Internet Archive API result is saved in
`internet-archive-garhwali-folklore-search.json`.

## Current ingestion status

| Material | Local result | Rights/treatment |
| --- | ---: | --- |
| Ganga Datt Upreti, *Proverbs & Folklore of Kumaun and Garhwal* (1894) | 440 page-level OCR records | Historical mixed Kumauni/Garhwali/English source; retained with OCR and language-mixture flags |
| Uttarakhand Open University MAHL-204 and MAHL-611 | 156 selected page records | Garhwali folk songs, ballads, tales and folk-literature history; CC BY-NC-SA restricted layer with component-rights review |
| UOU CGL study material | 436 selected page records | Garhwali language and literature, including folk literature; CC BY-NC-SA restricted layer |
| Open Bible Stories, Garhwali | 50 stories | CC BY-NC-SA restricted layer; narrative material but not traditional Garhwali folklore |
| Atkinson, Crooke and 1911 Wikisource cultural references | 317 exact-unique records / 1,501,195 characters | Public-domain historical context, mostly English rather than Garhwali training text |

This means folklore has been collected substantially, but the Garhwali-language
folk-book layer is not complete. After the initial audit, the user authorized
local ingestion of publicly downloadable sources with unclear rights, provided
the payloads remain in Git-ignored storage and retain their provenance.

## Newly archived and extracted

| Source | Raw archive | Extraction |
| --- | ---: | ---: |
| Govind Chatak, *Gadwali Lokgeet* (1956) | PDF, OCR text, DjVu XML and Archive metadata | 370 page records |
| Shanti Chaudhary, *Garhwali Lokkala Aur Loksahitya Ka Tulnatmak Anusilan* (1994) | PDF, OCR text, DjVu XML and Archive metadata | 298 page records |
| Sushila Devi Maindola, *Garhwali Folktales* podcast | Official RSS feed, Apple lookup record and all 66 exposed audio enclosures | 66 audio records with titles, dates, source URLs, byte counts and SHA-256 hashes |
| Pushkar Singh Kandari, *Garhwali Muhavaron-Kahavaton Ka Vrihat Sangrah* | TUFS record, cover/title PDF and contents PDF | No full text is exposed by the repository |
| Mohanlal Babulkar, *Garhwali Lok-Sahitya Ka Vivechanatmak Adhyayan* (1964) | Google Books catalogue/search response | Google reports no eBook available; no full payload to extract |

The two new book datasets contain 668 non-empty OCR page records and 761,404
characters. They contain no exact duplicate pages relative to each other. Raw
files are under `data/downloads/folklore/`; page records are under
`data/extracted/folklore/`. Both paths are ignored by Git. Rights-pending labels
remain in every extracted record so later filtering is deterministic.

## Fresh Internet Archive result

The Garhwali-plus-folklore query returned four records:

1. `in.ernet.dli.2015.481134`, Shanti Chaudhary, *Garhwali Lokkala Aur
   Loksahitya Ka Tulnatmak Anusilan* (1994): archived and extracted locally.
2. `in.ernet.dli.2015.404620`, Govind Chatak, *Gadwali Lokgeet* (1956): archived
   and extracted locally.
3. `sgng.1764-a-themetic-study-of-garhwali-folk-songs-lokgeet`, *A Themetic
   Study of Garhwali Folk Songs Lokgeet* (2013): already represented locally as
   the one-record folk-song thesis/research item; CC BY-NC-SA 4.0.
4. `recastingfolkinh0000fiol`, *Recasting Folk in the Himalayas* (2017): broad
   modern scholarship, not a Garhwali-language folklore book and no open license;
   excluded from text ingestion.

## Other public-web books found or reconfirmed

- Mohanlal Babulkar, *Garhwali Lok-Sahitya Ka Vivechanatmak Adhyayan*, volume 1
  (1964), 307 pages: Google Books snippets and library holdings only; no open
  license found.
- Govind Chatak, *Garhwali Lokgeet*: TUFS exposes cover and contents files, and
  Lucknow Digital Library requires registration for scans. Neither source states
  an open-content license.
- Pushkar Singh Kandari, *Garhwali Muhavaron-Kahavaton Ka Vrihat Sangrah*:
  TUFS exposes cover and contents only, without an open license.
- *Himalayan Folklore* (1935): English translations of Kumaoni and Garhwali
  heroic ballads. It is a valuable reference, but jurisdiction and edition
  rights remain separated from the globally reusable corpus.
- The Garhwali Folktales podcast lists 66 narrated stories under an explicit
  creator copyright; permission and transcript export are required.

## Rate-limit state

No collector is currently paused. The earlier Wiktionary HTTP 429 run completed
after request throttling, and its 56-page extraction is present. A Google Books
429 affected one metadata lookup only and was replaced with library and Internet
Archive catalogue evidence. The pipeline now classifies HTTP 429 as transient
and retries it with exponential backoff and jitter. TUFS returned HTTP 429 to a
web-preview request during this pass; a throttled direct retry succeeded and its
public files were archived. The Mera Pahad forum currently fails local DNS
resolution and remains resumable from its 14-page thread index.

## Remaining work

The largest gap is licensed full text for the modern Garhwali folk-song,
folk-tale, proverb, ballad, *jagar*, *mangal* and folk-theatre books. The next
safe acquisition step is rights outreach for the Chatak, Babulkar, Chaudhary and
Kandari works, followed by OCR only after permission or authoritative
public-domain evidence is recorded. Historical periodicals and microfilm remain
an access/digitization problem rather than a rate-limit problem.
