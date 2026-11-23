# Rights clearance triage for the 8,444 rights-pending texts — 2026-11-09

This pass takes the 8,444 distinct full texts that sit only in the local
all-data package (see the [6 October availability audit](huggingface-corpus-gap-resolution-2026-10-06.md))
and records a decision for every source behind them. The machine-readable
ledger is [`rights-clearance-decisions-2026-11-09.json`](rights-clearance-decisions-2026-11-09.json).
A row-level queue (record ID, source, tier, decision) is kept local under
`data/review/rights-clearance-queue-v0.1/queue.csv`.

**Owner decisions, 2026-11-10:** Tier A is signed off for release in corpus
v0.2.9 and is wired into the builder (`SIGNED_OFF_PUBLIC_DOMAIN_SOURCES` in
`scripts/build_huggingface_dataset.py`), which also corrects the Bhotias
attribution to C. A. Sherring, 1906. Sankrityayan stays local while it is
protected in the US.

**No public data changed.** Decisions marked "clear" are complete on the
evidence. They still need owner sign-off before they are wired into the
builders and released in a new corpus version.

## Method

1. Rebuilt the unmatched set from the local v0.2.7 packages: all-data catalog
   texts whose NFKC, case-folded, whitespace-collapsed value appears nowhere
   in the public v0.2.7 staging package. The result matches the audit exactly:
   8,444 distinct texts, 2,936,664 whitespace words, 49 sources.
2. Grouped by the first provenance source and checked each group against
   existing project findings, the scan's own title page, and new web research
   on publication dates, government-work status, and author death dates.
3. Applied a two-jurisdiction rule, because the material originates in India
   and is hosted in the US by Hugging Face:
   - **India:** Copyright Act 1957 — life + 60 years for named authors (s.22);
     60 years from publication for government and anonymous works (ss.23, 28).
     Terms that had already expired under the earlier life + 50 rule were not
     revived by the 1992 amendment, so any author who died before 1941 is
     public domain.
   - **US:** works published before 1931 are public domain as of 1 January
     2026. Later foreign works were restored under the URAA if they were still
     protected in India on 1 January 1996, and then run 95 years from
     publication.

## Result

| Tier | Sources | Records | Words | What it means |
| --- | ---: | ---: | ---: | --- |
| A — public domain in India and the US | 4 | 451 | 149,251 | Clear; ready to release after sign-off |
| B1 — US public domain; India needs an author death date | 2 | 234 | 62,401 | Clear if the author died before 1966 |
| B2 — India public domain; US protected or unresolved | 3 | 769 | 203,177 | Owner decision on jurisdiction, or more evidence |
| C — open license with conditions (CC BY-NC-SA) | 3 | 593 | 186,645 | Noncommercial release after screening out quoted works |
| D — copyright subsists; needs written permission | 25 | 5,988 | 2,234,680 | Outreach to authors, estates, publishers |
| E — unlicensed web pages and web-crawl datasets | 12 | 409 | 100,510 | Keep local; effectively unclearable |
| **Total** | **49** | **8,444** | **2,936,664** | |

### The catch: what is clearable is mostly English

Every Tier A and B1 source is an English-language colonial-era reference
(gazetteer, botanical catalogue, missionary account, ethnographic memoir).
Their own records already flag them as `not Garhwali text` or
`page_language_unverified`. Releasing them adds public historical context with
Garhwali place names, plant names, and terms. It does **not** add Garhwali
language-model training text. Most of the actual Garhwali in the queue is in
Tier D: the E-Magazine of Uttarakhand, Chatak's folk-song collections, and the
dictionaries.

## Tier A — clear in both jurisdictions

| Source | Records | Words | Basis |
| --- | ---: | ---: | --- |
| Walton, *British Garhwal* gazetteer (1910) | 246 | 89,945 | Government work: the India s.28 term ended 1970. The project already applies this basis to Walton scan pages 90–91. Published before 1931 (US). |
| Strachey & Duthie, *Catalogue of the Plants of Kumaon…* (1906) | 124 | 28,680 | Last author Duthie died 23 Feb 1922, so the India term ended 1972. Published 1906 (US). |
| Oakley, *Holy Himalaya* (1905) | 57 | 16,902 | Author died 1934/35, so the India term ended by 1985. Published 1905 (US). |
| Sherring, *Notes on the Bhotias of Almora and British Garhwal* (1906) | 24 | 13,724 | Author died 8 Oct 1940, so the India term ended 31 Dec 1990, before the 1992 extension. Published 1906 (US). |

Each local scan's title page was checked against the claimed edition, and
none shows later-edition matter. The Bhotias catalog entry should be corrected
to author **C. A. Sherring** and year **1906**: it currently says "not
identified" and 1905. The Archive uploader's CC BY-NC 4.0 label on that item
covers the scan, not the 1906 text.

## Tier B — one fact or one decision away

- **Pati Ram, *Garhwal: Ancient and Modern* (1916), 185 records; Joshi, *Notes
  on the Garhwal District* (1910), 49 records.** Both are public domain in the
  US. In India they are public domain if the author died before 1966. No death
  date was found in this pass. Pati Ram's book also has an introduction by a
  second writer, who needs the same check.
- **Sankrityayan, *Himalaya Parichay: Garhwal* (1953), 305 records.** The author
  died 14 April 1963, so the book has been public domain in India since 2024.
  It is protected in the US until the end of 2048 because of URAA restoration.
  Releasing it on a US host is the owner's call.
- ***Himalayan Folklore* (1935; scan is the 1977 reprint), 368 records.** Sources
  conflict on Gairola's death: 1940 (Wikipedia/Wikidata) or 1950 (a regional
  literature article). If 1940, the book is public domain in both India and
  the US. If 1950, it is public domain in India and protected in the US until
  the end of 2030. In both cases, the reprint's added introduction pages must
  be excluded.
- **Barthwal, *Garhwal Me Kon Kahan Se* (1938), 96 records.** The Archive's
  public-domain mark is unverified, and the author's death date is unknown.

## Tier C — licensed, with conditions

The Uttarakhand Open University modules (CGL 436 and MAHL 156 records) and one
Archive thesis declare CC BY-NC-SA 4.0. They quote poems and prose by other
Garhwali writers, which the licensor cannot relicense. The route is to screen
out pages dominated by quoted works, then publish the remainder in a
noncommercial/share-alike config, as the project already does for HinDialect.

## Tier D — permission targets, by size

| Target | Records | Words | Notes |
| --- | ---: | ---: | --- |
| E-Magazine of Uttarakhand (Bhishma Kukreti and contributors) | 1,860 | 1,119,327 | 38% of all queued words. One permission from the editor covers his own articles; contributed pieces need their authors. |
| Shiv Prasad Dabral estate (5 works) | 978 | 241,920 | Author died 1999; protected in India until the end of 2059 |
| Govind Chatak estate (5 works) | 929 | 223,579 | Folk-song and folk-ballad collections plus language studies |
| Haridatta Bhatta 'Shailesh' (1976) | 443 | 116,912 | Author reported died 2011 |
| Dictionaries (Purohit/Benjwal; Jakhmola; derived site lists) | 526 | 176,387 | Selection and definitions are protected compilations |
| Shanti Chaudhary (1994) | 298 | 80,294 | |
| Tehri Garhwal District Gazetteer (1971) | 253 | 92,854 | Government work: India term runs to the end of 2031 (US to 2066). Seek state permission or wait. |
| Juyal (1967) | 200 | 60,120 | The scan says "all rights reserved"; the Archive's CC0 claim conflicts |
| Others (Krishna Kumar, Chandola, *Gadwali Sahitya*, Babicz, Bhandari) | 501 | 123,287 | |

Draft request templates are in [`outreach-drafts.md`](outreach-drafts.md). Each
request should cover redistribution and model training, and name the exact
works and editions.

## Tier E — keep local

Web-crawl datasets (DCAD-2000, MADLAD-400) license only the database, not the
underlying pages. The remaining sources are small web pages, a YouTube
comment set, and an unlicensed Hugging Face dataset. Together they are 409
records. Clear individual sites only if a site owner grants permission.

## Next steps

1. **Owner sign-off on Tier A.** Then add the four source decisions to the
   ingestion scripts using the existing `TERRITORIAL_PUBLIC_DOMAIN_EVIDENCE`
   mechanism in `scripts/build_huggingface_dataset.py`, rebuild with
   `GARHWALI_RELEASE_VERSION=0.2.9`, and run the usual gates.
2. Decide the jurisdiction question for Sankrityayan (India-only public domain).
3. Find death dates for Pati Ram, Dharmanand Joshi, and Barthwal, and a primary
   record for Gairola.
4. Screen the UOU pages for quoted works.
5. Send the E-Magazine permission request first: it is the largest block of
   actual Garhwali in the queue.

## Follow-up review — 2026-11-23

This pass worked the open items from the next-steps list above. Findings are
recorded per source under `review_2026_11_23` in the
[decision ledger](rights-clearance-decisions-2026-11-09.json). **No public data
changed and no one was contacted.**

### Death-date and edition checks

| Source | Records | Finding | Status |
| --- | ---: | --- | --- |
| Pati Ram, *Garhwal: Ancient and Modern* (1916) | 185 | The foreword is by J. M. Clay, Deputy Commissioner of Garhwal (death date not found), so those pages are a separate layer. Pati Ram had retired after a lifelong career and had a graduate son by 1916, so he was almost certainly born before about 1866. No death record found. | Owner decision: accept the age inference and release without the foreword, or wait |
| Joshi, *Notes on the Garhwal District* (1910) | 49 | No death date. Already a Rai Bahadur in 1910, which points to an older author, but the inference is weaker than for Pati Ram. | Pending; owner may accept the inference |
| *Himalayan Folklore* (1935 text; 1977 reprint scan) | 368 | Gairola's death in May 1940 is now given by two independent secondary sources (Wikipedia and a 2025 article by historian Yogesh Dhasmana). Only the 2009 E-Magazine post gives 1950. Still no primary record. | Owner decision: accept 1940 (then public domain in India and the US), excluding the 1977 introduction |
| Barthwal, *Garhwal Me Kon Kahan Se* (1938) | 96 | The Archive Public Domain Mark was added by the uploader with no basis. No death date found. | Pending |
| Juyal (1967) | 200 | The CC0 label was applied by a digitizing foundation (uploaded February 2026), not the rights holder. The book's own "all rights reserved" notice governs. | Conflict closed: needs permission |
| Govind Chatak (5 works) | 929 | Chatak was born 13 December 1933 and died June 2007, so his works are protected in India until the end of 2067. | Needs estate permission |
| E-Magazine of Uttarakhand | 1,860 | Posts carry "Copyright @ Bhishma Kukreti" and no open license. | Needs permission |

If the owner accepts both inferences and the Gairola date, 602 records
(Pati Ram 185, Joshi 49, *Himalayan Folklore* 368) could move to Tier A. All
three are English-language references, so they would add historical context
but no Garhwali training text, like the Tier A releases.

### Published exception: `paharili_gbm`

AIKosh lists PahariLI under Apache 2.0, but its description also says
ownership and intellectual property rights remain with the original authors.
Neither AIKosh nor the paper's public page says where the Garhwali sentences
came from (the paper's footnotes point to news articles; its data section is
paywalled). The config stays labelled experimental and not rights-cleared.
Whether to keep it published, ask the authors for their sources, or withdraw it
from the next release is an owner decision. Citation: Gusain, Dash, Parida and
Jha, *Language Resources and Evaluation* 57 (2023), 1361–1387,
doi:10.1007/s10579-023-09651-6.

### Not done in this pass

- **UOU quote screening (592 records).** This needs the local all-data text on
  the owner's Mac; it was not run here.
- **Outreach.** The permission targets, in priority order, are listed in
  [`outreach-drafts.md`](outreach-drafts.md#permission-targets-2026-11-23).
  Nothing has been sent.
