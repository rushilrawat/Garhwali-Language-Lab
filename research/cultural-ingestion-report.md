# Garhwali cultural-source ingestion report

Updated 2026-09-10. This pass used live web discovery, publisher and repository
records, Internet Archive metadata, Project Gutenberg, Wikisource and Wikimedia
Commons. It separates openly reusable evidence from material that is merely
publicly visible.

## Ingested material

| Source | Rights evidence | Result | Treatment |
| --- | --- | ---: | --- |
| Edwin T. Atkinson, *The Himalayan Districts of the North-Western Provinces of India* / *Himalayan Gazetteer*, six parts (1882–1886) | Internet Archive item metadata identifies the original editions and public-domain status; see the [1882 volume record](https://archive.org/details/1882himalayangazetteervol1pt1) | 302 exact-unique Garhwal-relevant OCR chunks | `extracted/historical/cultural_references.jsonl`; English historical context, OCR and colonial-source flags |
| William Crooke, *The Popular Religion and Folk-Lore of Northern India*, volumes 1–2 (1896) | [Project Gutenberg volume 1](https://www.gutenberg.org/ebooks/43681) and [volume 2](https://www.gutenberg.org/ebooks/43682) mark the works public domain in the United States | 13 exact-unique Garhwal passages | Same cultural-reference file; research context only |
| 1911 *Encyclopædia Britannica*, [“Garhwal”](https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Garhwal) and [“Pahari”](https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Pahari) | Public-domain source editions on Wikisource | 2 articles | Same cultural-reference file; dated-terminology flag |
| Wikimedia Commons, `Category:Garhwali people` | Item-level API metadata | 754 unique media records: 744 CC BY-SA 4.0, 8 CC0, 1 CC BY-SA 3.0 and 1 public domain | URLs, attribution and license metadata stored in `research/garhwali-cultural-media.json`; media binaries were not bulk downloaded |

The 317 text records contain 1,501,195 normalized characters. Automatic
multi-label indexing found 91 folk-narrative, 46 performance, 138
ritual/religion, 150 social-custom, 137 material-culture, 26
language/literature and 299 place-history associations. Labels overlap because
a passage may describe several subjects. These are discovery labels and require
human review.

The project now contains 32,301 source records and 30,274 exact-unique
normalized texts across all layers. This pass introduced no new exact duplicate
row. The verifier checks 358 immutable source snapshots.

## Cultural material already present

The existing Uttarakhand Open University CGL-101 through CGL-104 and selected
MAHL-204/611 pages already cover Garhwali poetry, prose, grammar, folk songs,
ballads, folktales, theatre history and short dramatic extracts. They remain in
the CC BY-NC-SA restricted layer because the university's site terms are
noncommercial and quoted modern works may have separate component rights. The
[current CGL programme](https://uou.ac.in/progdetail?pid=CGL-21) identifies its
four books as selected poetry, selected prose, grammar/vocabulary and Garhwali
folk literature.

Following user authorization for local, Git-ignored research ingestion, two
complete Internet Archive/Digital Library of India scans were added: Govind
Chatak's *Gadwali Lokgeet* (1956) and Shanti Chaudhary's *Garhwali Lokkala Aur
Loksahitya Ka Tulnatmak Anusilan* (1994). Their 668 page-level records contain
761,404 OCR characters and no mutual exact duplicates. The official *Garhwali
Folktales* RSS feed and all 66 exposed audio episodes were also archived with
checksums. These payloads retain rights-pending markers and live only under the
ignored `data/` tree.

## Public discoveries retained as rights leads

The machine-readable register is
[`cultural-source-leads.json`](cultural-source-leads.json). Highlights include:

- The [Garhwali Folktales podcast](https://podcasts.apple.com/us/podcast/garhwali-folktales/id1536704188) lists 66 narrated stories but explicitly identifies the creator's copyright. Episode audio was not copied.
- Tokyo University of Foreign Studies catalogues [Govind Chatak's *Garhwali Lokgeet*](https://tufs.repo.nii.ac.jp/records/24025) and a [Garhwali idiom/proverb collection](https://tufs.repo.nii.ac.jp/records/17829), but only cover and contents files are exposed and no open license is shown.
- Modern Garhwali plays named in UOU study material remain bibliographic leads. A study-material license cannot sublicense the complete underlying plays.
- Tara Dutt Gairola's *Sadei* and *Garhwali Kavitavali* are likely public domain in India because Gairola died in 1940, but works still protected on the 1996 United States restoration date may remain protected there through 2031. No global corpus promotion was made.
- [Himalayan Folklore](https://uttarakhandhub.com/library/himalayan-folklore) is similarly public domain in India while its likely United States term continues through 2031.
- [StoryWeaver](https://storyweaver.org.in/en/open-content) uses CC BY 4.0 for stories, but the checked public source repository exposes no Garhwali language directory. It remains a high-priority recheck source.

## Quality and interpretation limits

The historical English sources were written through nineteenth- and early
twentieth-century colonial frameworks. They preserve useful names, practices,
beliefs and local references, but their classifications and descriptions need
comparison with contemporary Garhwali scholarship and community testimony.
Machine OCR can merge pages and damage names. Records are therefore
`historical: true`, `training_eligible: false`, and marked for native and
historical review.

The cultural-media index stores attribution fragments exactly as returned by
Wikimedia's API. Any later media download must preserve its item-level author,
license URL and description page.

## Next acquisition targets

1. Find surviving scans of the 1905–1951 *Garhwali* periodical through state,
   university and national-library catalogues; clear issue-level rights before OCR.
2. Seek permissioned digital editions of *Sadei*, *Garhwali Kavitavali*, classic
   plays and Govind Chatak's folklore collections.
3. Ask the Garhwali Folktales podcast creator for a research transcript export,
   speaker consent terms and an explicit dataset license.
4. Recheck StoryWeaver and other CC repositories for newly added `gbm` translations.
5. Pair historical passages with contemporary consented oral-history interviews.
