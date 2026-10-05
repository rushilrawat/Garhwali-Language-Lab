# Internet Archive source disposition — 2026-10-04

## Result

The captured local metadata covers **55 distinct Archive items**: 24 text items, 13 audio items, and 18 movie items. It links to **4,011 OCR page objects** (3,983 with non-empty OCR; 28 empty), and 39 technically probed local audio/video files.

No source text, page, or media was deleted or edited. No new Archive content was approved for model training or public redistribution by this pass. The full OCR pages and source files remain in the ignored local data folders; the tracked register contains item metadata and evidence labels, not extracted expressive text.

**Follow-up:** a separate [priority-language and rights evidence review](internet-archive-priority-language-rights-review-2026-10-04.md) adds scholarly/catalog evidence for the five highest-priority works, identifies the scanned 1977 Himalayan Folklore reprint, and records unresolved Archive CC0 claims against book-level and statutory ownership evidence. This supplemental research does not overwrite the captured metadata claims or alter any eligibility flag.

## Rights evidence recorded

The following counts describe captured metadata fields, not independently verified rights or permission from authors, publishers, performers, institutions, or other rightsholders:

| Captured item-level claim | Items |
| --- | ---: |
| CC0 URI recorded | 9 |
| CC BY URI recorded | 1 |
| CC BY-NC URI recorded | 11 |
| CC BY-NC-ND URI recorded | 1 |
| CC BY-NC-SA URI recorded | 1 |
| No reuse-license field recorded | 31 |
| Public Domain Mark URI recorded | 1 |

A **metadata conflict** is present on 1 item(s): *MarginalizedAadhaar: Sampati* has an Archive `licenseurl` for CC BY 4.0 while its `rights` field says CC BY-SA 4.0. The register preserves both statements and does not choose between them.

The register also preserves Archive copyright-status fields as recorded claims, including the two US-region `NOT_IN_COPYRIGHT` records. Such fields are not presented as a cross-jurisdictional or edition-level determination.

## Non-destructive text review views

All OCR page objects in the review inventory were retained and assigned a source-linked follow-up group. The groups guide language review; they do not call a page Garhwali based on title or script.

| Follow-up group | Rows |
| --- | ---: |
| Empty OCR sidecar page; source scan retained | 28 |
| Known alternate scan of an already represented work | 61 |
| Garhwali-focused language/folklore sources; page language unverified | 920 |
| Regional context; not verified as Garhwali text | 2,570 |
| Garhwali folk material with translation; page scope uncertain | 432 |

Page-level script and OCR triage signals (these are not language-identification results):

| Review group | Pages | Mostly Devanagari | Mostly Latin | Mixed script | Other/unclear | No letters | Any OCR warning |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Empty OCR sidecar page; source scan retained | 28 | 0 | 0 | 0 | 0 | 28 | 0 |
| Known alternate scan of an already represented work | 61 | 61 | 0 | 0 | 0 | 0 | 4 |
| Garhwali-focused language/folklore sources; page language unverified | 920 | 405 | 21 | 493 | 0 | 1 | 29 |
| Regional context; not verified as Garhwali text | 2,570 | 728 | 1,033 | 809 | 0 | 0 | 378 |
| Garhwali folk material with translation; page scope uncertain | 432 | 0 | 431 | 0 | 0 | 1 | 7 |

Script profiles describe Unicode character composition only. OCR-warning rows can overlap and are heuristic review flags. They do not establish Garhwali versus Hindi, text correctness, or training suitability.

The priority group includes 920 pages from three Garhwali-focused works. Another 61 pages belong to an alternate scan of the user-supplied 1959 grammar and stay linked as an existing-work duplicate. Translated-folklore rows need language/translation-boundary review; regional-reference pages remain contextual. One exact duplicate page-text group occurs within the full inventory, covering two records; both are retained. No page is individually language-verified.

The original 3,369-page index came from 20 JSONL files. This reconciliation found two more downloaded text items with local DjVu OCR sidecars but no page index: *Himalayan Folklore: Kumaon and West Nepal* (376 scan objects; 368 non-empty) and *British Garhwal: A Gazetteer* (266 scan objects; 246 non-empty). The local review view now covers all 4,011 page objects found in these captured text items. Those 614 non-empty additions are contextual or translated source pages, not new verified Garhwali training records.

Normalization and overlap counts: **3,983** rows have OCR text; **3,982** remain non-empty after Unicode/punctuation normalization; those collapse to **3,981** distinct normalized values. One non-empty OCR row normalizes to no letters or numbers. The full intake has 1 repeated normalized-text group covering 2 page rows. Of the unique normalized values, 2 match the named canonical view and 3,979 do not. This is a scoped duplicate check, not a Garhwali-language, rights, or training-eligibility decision.

The generated text review JSONL includes every indexed and supplemental OCR row, source/page identifiers, original text, prior rights/quality labels, exact-duplicate signals, available OCR-engine word-confidence signals, and the follow-up group. It is stored under ignored `data/extracted/research/internet_archive_candidate_views_2026-10-04/`. The media index has one row per probed local file and stores source link, file hash, duration, metadata rights claim, and unreviewed language/transcript state. Neither local view changes eligibility or publishes content.

## Item-by-item disposition

Every captured item appears below. License/rights language is quoted or labeled as a source claim; `No content cleared` means this pass did not establish new training or redistribution permission.

| Archive item | Scope evidence | OCR pages | Media files | Canonical exact-match pages | Captured rights evidence | OCR confidence | Disposition |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| [1 Salut Anglais Garhwali](https://archive.org/details/1-salut-anglais-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [1 Salutations Garhwali](https://archive.org/details/1-salutations-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [2 Automatismes Garhwali](https://archive.org/details/2-automatismes-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [3 Chanson Garhwali](https://archive.org/details/3-chanson-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [4 Déno Anglais Garhwali](https://archive.org/details/4-deno-anglais-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [4 Dénomination Garhwali](https://archive.org/details/4-denomination-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [5 Dési Anglais Garhwali](https://archive.org/details/5-desi-anglais-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [5 Désignation Garhwali](https://archive.org/details/5-designation-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [6 Manip Objets Anglais Garhwali](https://archive.org/details/6-manip-objets-anglais-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [6 Manip Objets Garhwali](https://archive.org/details/6-manip-objets-garhwali) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Garhwali Khanyatitji Administrative Record Garhwali History Paper Manuscript 1865 Unknown Jagannath Bhattarai Collection](https://archive.org/details/aoml_garhwali-khanyatitji-administrative-record-garhwali-history-paper-manuscrip) | metadata only or non ocr payload content unreviewed | 0 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Catalogue of the Plants of Kumaon and of the Adjacent Portions of Garhwal ...](https://archive.org/details/catalogueplants00duthgoog) | contextual regional reference not verified garhwali text | 124 | 0 | 0 | No reuse-license field recorded; Archive possible-copyright-status recorded | not available | No new content cleared |
| [Garhwal Ke Pracheen Abhilekha Aur Unka Itihasika Mahatva By Krishna Kumar Haridwar Mayank Prakashan](https://archive.org/details/cVko_garhwal-ke-pracheen-abhilekha-aur-unka-itihasika-mahatva-by-krishna-kumar-haridwar-mayank-praka) | contextual regional reference not verified garhwali text | 172 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Uttarakhand Ka Itihas Bhag 3 Rajnaitik Tatha Sanskritik Itihas By Shiv Prasad Dabral Charan Hindi History Illustrated Dogadda Garhwal 2026 Veer Gatha Prakashan](https://archive.org/details/cylk_uttarakhand-ka-itihas-bhag-3-rajnaitik-tatha-sanskritik-itihas-by-shiv-pras) | contextual regional reference not verified garhwali text | 137 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Gadwali Lok Gathayen (1958)](https://archive.org/details/dli.ernet.426855) | source labeled garhwali focused but page language unverified | 276 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Uttar Pradesh District Gazetteers: Tehri Garhwal](https://archive.org/details/dli.ministry.08781) | contextual regional reference not verified garhwali text | 253 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Notes on the Garhwal district](https://archive.org/details/dli.ministry.29693) | contextual regional reference not verified garhwali text | 49 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Note On The Bhotias Of Almora And British Garhwal](https://archive.org/details/dli.pahar.1694) | contextual regional reference not verified garhwali text | 24 | 0 | 0 | CC BY-NC URI recorded; archive license recorded cc by nc 4 0 | not available | No new content cleared |
| [Peaks and Passes of Garhwal Himalaya](https://archive.org/details/dli.pahar.3635) | contextual regional reference not verified garhwali text | 81 | 0 | 0 | CC BY-NC URI recorded; unverified uploader cc by nc 4 0 claim | not available | No new content cleared |
| [Folk Music of Garhwal (Vol. I)](https://archive.org/details/dni.ncaa.CCRT-447-UMHB) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Folk Music of Garhwal (Vol. II)](https://archive.org/details/dni.ncaa.CCRT-448-UMHB) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Documentation of Beej Bachao Andolan - A Campaign by Shri Vijay Jardhari (Vol. I)](https://archive.org/details/dni.ncaa.CVI-BH_R_39-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded; archive metadata claim unverified noncommercial only | not available | No new content cleared |
| [Documentation of Beej Bachao Andolan - A Campaign by Shri Vijay Jardhari (Vol. II)](https://archive.org/details/dni.ncaa.CVI-BH_R_40-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded; archive metadata claim unverified noncommercial only | not available | No new content cleared |
| [Documentation of Beej Bachao Andolan - A Campaign by Shri Vijay Jardhari (Vol. III)](https://archive.org/details/dni.ncaa.CVI-BH_R_41-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded; archive metadata claim unverified noncommercial only | not available | No new content cleared |
| [Documentation of Beej Bachao Andolan - A Campaign by Shri Vijay Jardhari (Vol. IV)](https://archive.org/details/dni.ncaa.CVI-BH_R_42-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded; archive metadata claim unverified noncommercial only | not available | No new content cleared |
| [Documentation of Beej Bachao Andolan - A Campaign by Shri Vijay Jardhari (Vol. V) and Interview of Friends of Vrindavan (Vol. I)](https://archive.org/details/dni.ncaa.CVI-BH_R_43-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded; archive metadata claim unverified noncommercial only | not available | No new content cleared |
| [Garhwali Folk Songs](https://archive.org/details/dni.ncaa.ICCR-1282-AC) | archive metadata only media language and content unreviewed | 0 | 2 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Virasat (Dehradun Tour) (Vol. VII)](https://archive.org/details/dni.ncaa.IGRMS-3B_184-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Joshi Math (Uttarakhand) (Vol. I)](https://archive.org/details/dni.ncaa.IGRMS-3B_2-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Joshi Math (Uttarakhand) (Vol. II)](https://archive.org/details/dni.ncaa.IGRMS-3B_3-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Joshi Math (Uttarakhand) (Vol. III)](https://archive.org/details/dni.ncaa.IGRMS-3B_4-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Joshi Math (Uttarakhand) (Vol. IV)](https://archive.org/details/dni.ncaa.IGRMS-3B_5-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Joshi Math (Uttarakhand) (Vol. V)](https://archive.org/details/dni.ncaa.IGRMS-3B_6-BC) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded; rights holder named no reuse license recorded | not available | No new content cleared |
| [Pahadi Cultural of Uttarakhand (Vol. III)](https://archive.org/details/dni.ncaa.IGRMS-A_599-AC) | archive metadata only media language and content unreviewed | 0 | 2 | 0 | CC BY-NC URI recorded | not available | No new content cleared |
| [Bagwal Festival, Devidhura, Uttrakhand (Vol. I)](https://archive.org/details/dni.ncaa.IGRMS-S_VHSC_29-SVHS) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded | not available | No new content cleared |
| [Bagwal Festival, Devidhura, Uttrakhand (Vol. II)](https://archive.org/details/dni.ncaa.IGRMS-S_VHSC_34-SVHS) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded | not available | No new content cleared |
| [Bagwal Festival, Devidhura, Uttrakhand (Vol. III)](https://archive.org/details/dni.ncaa.IGRMS-S_VHSC_36-SVHS) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC URI recorded | not available | No new content cleared |
| [Garhwali Bhasha Aur Uska Sahitya By Haridatta Bhatta Shailesh Hindi Linguistics Lucknow 1976 Hindi Samiti](https://archive.org/details/ezqp-garhwali-bhasha-aur-uska-sahitya-by-haridatta-bhat) | source labeled garhwali focused but page language unverified | 443 | 0 | 0 | CC0 URI recorded | not available | No new content cleared |
| [Garhwal Me Kon Kahan Se](https://archive.org/details/garhwal-me-kon-kahan-se_20250415) | contextual regional reference not verified garhwali text | 96 | 0 | 0 | Public Domain Mark URI recorded; unverified archive public domain mark claim | not available | No new content cleared |
| [Garhwali geet](https://archive.org/details/GarhwaliGeet) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | CC BY-NC-ND URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Holy Himalaya; the religion, traditions, and scenery of Himalayan province (Kumaon and Garwhal)](https://archive.org/details/holyhimalayareli00oaklrich) | contextual regional reference not verified garhwali text | 57 | 0 | 0 | No reuse-license field recorded; Archive possible-copyright-status recorded; archive public domain metadata claim recorded local reference only until project rights review | not available | No new content cleared |
| [Shri Uttarakhand Yatra Darshan](https://archive.org/details/in.ernet.dli.2015.309034) | contextual regional reference not verified garhwali text | 284 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Gadwali Bhasha](https://archive.org/details/in.ernet.dli.2015.347446) | source labeled garhwali focused but page language unverified | 61 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [Garhwal Ancient And Modern](https://archive.org/details/in.ernet.dli.2015.43255) | contextual regional reference not verified garhwali text | 185 | 0 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [British Garhwal - A Gazetteer](https://archive.org/details/in.ernet.dli.2015.48008) | contextual regional reference not verified garhwali text | 266 | 0 | 2 | No reuse-license field recorded | not available | No new content cleared |
| [Himalayan Folklore Kumaon And West Nepal](https://archive.org/details/in.ernet.dli.2015.532407) | source mentions garhwali folk material but page scope unverified | 376 | 0 | 0 | No reuse-license field recorded | 368 pages; word mean 49.461 | No new content cleared |
| [Snow balls of garhwal](https://archive.org/details/in.gov.ignca.12846) | source mentions garhwali folk material but page scope unverified | 64 | 0 | 0 | No reuse-license field recorded; printed all rights reserved no reuse license | not available | No new content cleared |
| [JESUS Film Garhwali Language](https://archive.org/details/jesus-film-garhwali-language) | archive metadata only media language and content unreviewed | 0 | 1 | 0 | No reuse-license field recorded | not available | No new content cleared |
| [MarginalizedAadhaar: Sampati](https://archive.org/details/marginalized-aadhaar-sampati) | archive metadata only media language and content unreviewed | 0 | 7 | 0 | CC BY URI recorded; conflicting rights field | not available | No new content cleared |
| [Uttarakhand Ka Itihas Katyuri Yug Tak Bhag 1 Sakshya Sankalan By Shiv Prasad Dabral Charan Hindi History Dogadda Garhwal 1965 Veer Gatha Prakashan](https://archive.org/details/ozkb_uttarakhand-ka-itihas-katyuri-yug-tak-bhag-1-sakshya-sankalan-by-shiv-prasa) | contextual regional reference not verified garhwali text | 186 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Himalaya Parichay ( 1) Garhwal By Rahul Sankrityayan Hindi Himalayan Studies Allahabad 1953 Allahabad Law Journal Press](https://archive.org/details/pawc_himalaya-parichay-1-garhwal-by-rahul-sankrityayan-hindi-himalayan-studies-allaha) | contextual regional reference not verified garhwali text | 305 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [A THEMETIC STUDY OF GARHWALI FOLK SONGS LOKGEET](https://archive.org/details/sgng.1764-a-themetic-study-of-garhwali-folk-songs-lokgeet) | metadata only or non ocr payload content unreviewed | 0 | 0 | 0 | CC BY-NC-SA URI recorded; archive item declares CC BY NC SA 4.0 unverified authority | not available | No new content cleared |
| [Alakananda Upatyaka Mein Pravas Bhag 1 Alakananda Upatyaka By Shiva Prasad Dabral Hindi Geography Dogadda Garhwal Veer Gatha Prakashan](https://archive.org/details/wsxq_alakananda-upatyaka-mein-pravas-bhag-1-alakananda-upatyaka-by-shiva-prasad-) | contextual regional reference not verified garhwali text | 123 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Uttarakhand Ke Bhotantik Alaknanda Upatyaka Mein Pravas Bhag 2 By Shivaprasad Dabral Hindi Ethnography Illustrated Dogadda Garhwal 1964 Veer Gatha Prakashan](https://archive.org/details/xhed_uttarakhand-ke-bhotantik-alaknanda-upatyaka-mein-pravas-bhag-2-by-shivapras) | contextual regional reference not verified garhwali text | 248 | 0 | 0 | CC0 URI recorded; unverified uploader license claim | not available | No new content cleared |
| [Madhya Pahadi Bhasha Garhwali Kumauni Ka Anushilan Aur Uska Hindi Se Sambandh By Gunanand Juyal Hindi Linguistics Lucknow 1967 Navyug Granthagar](https://archive.org/details/ycbf_madhya-pahadi-bhasha-garhwali-kumauni-ka-anushilan-aur-uska-hindi-se-samban) | source labeled garhwali focused but page language unverified | 201 | 0 | 0 | CC0 URI recorded | not available | No new content cleared |

Canonical exact-match references:

- `ia_british_garhwal_1910:scan-page:0090` matches existing `walton_gazetteer_1910:scan-page-90` (source IDs: walton_gazetteer_1910; rights evidence: `public_domain_india_government_work_term_expired`).
- `ia_british_garhwal_1910:scan-page:0091` matches existing `walton_gazetteer_1910:scan-page-91` (source IDs: walton_gazetteer_1910; rights evidence: `public_domain_india_government_work_term_expired`).

## Reproduction and limitations

Run the complete six-command sequence documented in [`scripts/README.md`](../scripts/README.md) from the project root when source indexes change. The disposition builder reads the captured Archive metadata plus the generated 4 October audits, then regenerates this report, the tracked JSON register, and ignored review indexes. It does not download anything, edit the input records, alter GitHub/Hugging Face, or contact any rightsholder.

Captured Archive metadata is a snapshot. This run did not obtain independent confirmation from any source uploader/rightsholder or conduct legal research on the source works. The Archive metadata endpoint was not available to the browsing tool during this run; item URLs below point to the captured source records for follow-up.

The full review candidate set was compared with all 32,072 canonical cleaned parent-text rows: 2 exact page-row match(es), 0 5-gram Jaccard candidates at ≥0.85, and the within-intake duplicate group noted above. The exact overlaps are linked to existing source records in the local index; they were not added again. These checks cover this named text view and exact normalization, not all segments, transcripts, or semantic overlap.

All 39 media files passed the existing ffprobe check for **14:09:25.531 of playback**. That duration does not measure Garhwali speech. This task did not listen to or transcribe those files, run language identification, correct OCR, or review individual pages. Only the Himalayan Folklore DjVu XML sidecar exposes OCR-engine word-confidence attributes: 368 pages / 82,452 words, mean 49.461. These are OCR-engine signals, not word-accuracy scores.

Related reports: [Archive intake](internet-archive-intake-2026-10-03.md), [automated quality and overlap audit](internet-archive-intake-quality-2026-10-04.md), [active dataset-quality roadmap](huggingface-dataset-quality-roadmap.md).
