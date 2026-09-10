# Online ingestion register

Snapshot dates: 2026-09-07 through 2026-09-09 (UTC). The collector records every attempted URL in
`requests.jsonl`; successful bodies are content addressed and pointed to by a
`*.metadata.json` file. A failed request remains in the log with its URL and
error. No credentials, paywalls, robots restrictions or access controls were
bypassed, and no remote audio or video was bulk downloaded.

## Material promoted into the project

| Layer | Source | Current quantity | Treatment |
| --- | --- | ---: | --- |
| `corpus/` | Meta Omnilingual ASR, `gbm_Deva` | 2,927 transcripts | CC BY 4.0 stated upstream; split, speaker, prompt and row provenance retained; audio remains referenced, not downloaded |
| `corpus/` | ASJP Garhwali | 91 concepts | CC BY 4.0; source/compiler citation retained |
| `corpus/` | Tatoeba detailed export | 36 sentences | CC BY 2.0 FR; missing contributor markers are explicit and records remain unreviewed |
| `corpus/` | Wikimedia Incubator Wikipedia test | 35 non-empty pages | CC BY-SA 4.0; raw wikitext, revision IDs and attribution links retained |
| `corpus/` | English Wiktionary | 56 pages | CC BY-SA 4.0; 54 Garhwali entries plus the Swadesh appendix, revision IDs retained |
| `corpus/` | Wikimedia Incubator Wiktionary test | 4 pages | CC BY-SA 4.0; scaffolding flag retained |
| `corpus/` | OPUS translatewiki `v2026-07-01` | 181 unique messages from 241 source lines | CC BY 3.0; repeated mono lines removed, English alignments retained when present |
| `corpus/` | South Asian Numerals Database v1.0 | 123 Garhwali forms | CC BY 4.0; IPA, concepts, segments and source references retained |
| `corpus/` | Chan Numerals v1.0.2 | 40 Garhwali forms | CC BY 4.0; only `garh1243-2` promoted; the separately classified Bangani rows were not mixed into Garhwali |
| `corpus/` | Special Numerals in South Asian Languages v1.0 | 67 translated examples | CC BY 4.0; 65 standalone values were catalogued but not separately ingested because they conceptually overlap SAND |
| `benchmarks/` | IndicGenBench Flores / XorQA / Crosssum | 2,009 / 1,139 / 699 | Evaluation-only; no benchmark row is training eligible, including upstream rows named `train` |
| `restricted/` | HinDialectClassification Garhwali label | 128 texts (83 train, 45 test) | CC BY-NC-SA upstream declaration; evaluation-only and outside `corpus/` |
| `restricted/` | Uttarakhand Open University CGL-101 through CGL-104 | 436 OCR pages / 695,677 characters | Site-wide CC BY-NC-SA 4.0 declaration; non-commercial research layer; quoted modern works require component review |
| `restricted/` | Uttarakhand Open University MAHL-204 and MAHL-611 selected Garhwali units | 156 OCR pages / 295,657 characters | Site-wide CC BY-NC-SA 4.0 declaration; MAHL-610 excluded because it duplicates the selected MAHL-204 units; machine OCR and component review flags retained |
| `restricted/` | Archive.org Garhwali folk-song thesis | 1 OCR document | Archive item declares CC BY-NC-SA 4.0; mixed-language and quoted-song review flags retained |
| `restricted/` | PanLex `gbm` filter | 13 forms | Current PanLex page declares CC BY-NC-SA 4.0; mirror's older CC0 statement was not relied on |
| `restricted/` | Garhwali Open Bible Stories | 50 complete stories | CC BY-NC-SA 4.0 catalog terms; illustrations excluded and item-level license-block absence flagged |
| `quarantine/` | MADLAD-400 `gbm` clean partition | 18 novel documents from 137 upstream documents | 119 exact DCAD duplicates skipped; ODC-BY database terms retained, but original page copyrights remain unresolved |
| `extracted/historical/` | LSI IX.4 OCR | 93 pages | Historical mixed-language OCR; page alignment and language segmentation remain review tasks |
| `extracted/historical/` | Proverbs & Folklore of Kumaun and Garhwal (1894) OCR | 440 pages | Historical mixed-language OCR; US public-domain evidence is saved, India status remains pending |
| `extracted/historical/` | Garhwali administrative manuscript (1865) | 1 manuscript image/OCR record | 1865 public-domain material; Archive item declares CC0; OCR is poor and needs human transcription |
| `extracted/historical/` | Hill Dialects of the Kumaun Division (1900) | 25 Garhwali section pages | Google Books full view marks the scan public domain; embedded OCR and mixed transliteration remain unreviewed |
| `extracted/historical/` | LSI CLDF v1.0 | 185 structured Garhwali forms | CC BY 4.0; retained as a structured derivative of the existing LSI OCR, not counted as an independent witness |
| `extracted/historical/` | Kellogg, *A Grammar of the Hindí Language* (1893) | 34 OCR pages mentioning Garhwali | Public Domain Mark 1.0; keyword-selected historical linguistic evidence, with LSI overlap flags |
| `extracted/historical/` | Walton, *British Garhwal: A Gazetteer* (1910) | 2 OCR pages | DLI item declares public domain; targeted language and dialect description only |
| `extracted/historical/` | Atkinson's six-part *Himalayan Gazetteer*, Crooke's two folklore volumes, and two Wikisource articles | 317 Garhwal cultural records / 1,501,195 characters | Public-domain historical research context; exact-deduplicated, keyword-selected, OCR and colonial-source flags retained |
| `research/` | Five rights-audited Garhwali scholarly works | 4 full PDFs plus 1 licensed catalogue record | Research evidence only; zero paper-prose corpus rows. The Heidelberg host returned an Anubis access challenge, which is recorded rather than mislabelled as the chapter |
| `research/` | Wikimedia Commons `Garhwali people` media index | 754 unique media records | Item URLs, authorship and licenses retained; binaries not bulk downloaded |
| `restricted/` + `research/` | Web thematic lexicon | 666 source records / 642 distinct normalized written forms | Birds, animals, insects, instruments, occupations, nature, food and regional cultural terms; source-level rights, confidence and native-review flags retained |
| Git-ignored `data/extracted/garhwali_idioms_dhyani/` | Balakrishna D. Dhyani, *Garhwali Muhavare Aur Kahavaten* | 99 exact-unique records | 69 standalone proverbs plus 30 Garhwali comparison entries; Hindi/English notes retained; no exact overlap across 33,807 existing text records |

The open corpus now contains 3,560 source records. The candidate sources
are kept in `quarantine/`: Indic Dialect ASR 7,823 rows, PahariLI 15,000,
hikinegi 53, DCAD 119, and 18 exact-novel MADLAD clean documents. Across every
layer there are 32,967 source records and 30,913 exact unique normalized texts;
see the machine-generated [dedup
report](../../outputs/online-ingestion-2026-09-07/dedup-report.json). No record
has native-speaker review yet; no record is a released training recommendation.

## Source inventory status

The prior 23-source inventory is preserved as `inventory_01` through
`inventory_23`. Their landing pages and rights evidence were fetched where
publicly available. The current status is:

* Meta, ASJP, both Wikimedia projects, English Wiktionary and Tatoeba are
  snapshotted or extracted as shown above.
* Vaani's official site and Hugging Face metadata are snapshotted. It reports
  110,410 recordings totaling 136.80 hours and 5,894 transcribed utterances
  totaling 8.80 hours. The mirror contains 5,893 Vaani rows, so one row remains
  to reconcile against the official manifest after approved access. Direct files
  are declared CC BY 4.0, while file access requires the project owner to accept
  the provider's contact-sharing agreement; no gate was bypassed.
* LSI and the 1894 book were downloaded as scans/OCR and kept in the historical
  layer. The LSI XML index-to-printed-page alignment is marked provisional.
* PahariLI, MADLAD, GlotCC, FineWeb-2, HPLT and DCAD were catalogued as
  discovery or quarantine sources. MADLAD's clean Garhwali partition has 137
  documents; 119 exactly duplicate DCAD, so only 18 novel documents were added.
  Their repository or database licenses do not automatically clear the underlying
  web pages, translations or recordings.
* GlotLID's current corpus is manually gated and says only its metadata and
  annotations are CC0. Chaashini is also manually gated and currently reports
  one Garhwali clip. Their public cards and source inventories are saved; no
  access gate was crossed and no content was counted.
* Two 2026 ASR studies were added to the evidence register. The ACL VarDial
  study evaluates noisy, spontaneous VAANI speech, while the Garhwali-ASR
  repository publishes code, split counts and aggregate per-seed results but
  excludes gated VAANI transcripts and audio.
* IGNCA's 1995 oral-tradition volume and the Central Hindi Directorate's 2019
  Garhwali linguistics article were verified as institutional references. They
  lack a verified open text license, so they were catalogued without extracting
  their Garhwali passages into a corpus layer.
* HimLingo, Hindwi, TUFS, modern literary pages, the Garhwali periodical lead
  and the Bible translation remain permission or provenance leads. Public web
  visibility was not treated as redistribution permission.
* BhashaDaan and Common Voice are collection channels, not verified existing
  Garhwali datasets in this snapshot.
* The Garhwali New Testament's source-specific page verifies CC BY-SA 4.0, but
  the publisher's advertised desktop ZIP currently returns 404. Its rights and
  download pages are snapshotted; chapter text has not been reconstructed from
  search caches or an access challenge.

Additional discovery was performed over Hugging Face dataset search, GitHub
repository search, Internet Archive full-text metadata, PanLex, OPUS, UKC
LiveLanguage, Kaikki, StoryWeaver, Common Voice, GlotCC, FineWeb-2, HPLT,
Kaggle listings and related benchmark mirrors. Mirrors of Meta, MMS ULAB,
Vaani and IndicGenBench were logged as mirrors and were not duplicated. The
GitHub search returned 41 repositories; repository metadata is retained, but
code, lyrics, applications and unlicensed dictionaries were not silently
promoted into the corpus. The complete family-by-family status is in
[deep-search-catalog.md](deep-search-catalog.md).

The third pass has a claim-level rights and quality matrix in
[source-audit-2026-09-08.md](source-audit-2026-09-08.md).

The scholarly synthesis and its concrete annotation recommendations are in
[`research/garhwali-scholarly-guide.md`](../../research/garhwali-scholarly-guide.md).
The cultural-source results and rights leads are in
[`research/cultural-ingestion-report.md`](../../research/cultural-ingestion-report.md).

The third-wave evidence and remaining gaps are mapped claim by claim in
[source-audit-2026-09-08.md](source-audit-2026-09-08.md).

## Archive and Wayback pass

The Internet Archive metadata search was expanded to 87 text items. One
unambiguously historical item, an 1865 Garhwali administrative manuscript, was
downloaded with its PDF and OCR. Visual inspection found one manuscript image
plus modern collection-context pages, so only the manuscript page remains in
the historical extraction. A CC BY-NC-SA folk-song thesis OCR was retained in
the restricted layer. Later books from 1939-1994 remain discovery records when
author death, uploader authority or an item-level content license is unclear.

Wayback CDX inventories were saved for nine known Garhwali-content domains.
Observed unique HTML capture rows were: Bol Pahadi 10,000 (the configured cap),
Uttarakhand e-magazine 10,000 (cap), GarhwaliLanguage 1,219, Garhwalii 400,
Pahadiaavaj 55, and Vijay Madhur 15. Two CDX domain queries returned 503 and
one returned zero rows. The archived pages are a provenance/discovery index,
not an open corpus: sampled sites explicitly assert author/poet copyright, and
Wayback preservation does not grant redistribution rights.

The UOU archival/educational search produced the most useful new ingestible
family. Its official programme page links four complete Garhwali books and its
terms license all study learning material under CC BY-NC-SA 4.0. Their embedded
legacy-font text was unusable, so all 436 pages were rendered at 180 DPI and
OCRed with Tesseract's Hindi and English models. The resulting 695,677
characters are Unicode Devanagari with explicit machine-OCR flags. Visual checks
covered a representative page from every volume.

The next UOU pass added 156 targeted pages from MAHL-204 and MAHL-611,
producing 295,657 OCR characters. MAHL-610 was acquired and checksummed but
excluded because its selected units duplicate MAHL-204. This wave ran through
the checkpointed LangGraph coordinator, including acquisition, extraction,
deduplication, and verification.

The second historical wave added the full-view 1900 Upreti scan. Only scan
pages 79-103, whose headings identify Srinagar, Tihri, Lohba and Malla Dasoli
Garhwali, were extracted; the following Marchha section was left out.

## Known incomplete or blocked endpoints

* Wiktionary returned HTTP 429 during an early recursive category walk. The
  collector was changed to use the two root Garhwali categories, waited between
  requests, and completed the 56-page extraction. The 429 events remain in the
  request log as history, not as a reason to omit the source.
* PanLex's public language catalogue was saved and identifies `gbm-000`. The
  generated four-part Parquet mirror was downloaded and filtered to 13 unique
  Garhwali forms. The official current license page declares CC BY-NC-SA 4.0,
  which is the conservative license applied to the extract.
* UKC's documented Garhwali ZIP URLs returned 404. Its dataset card and GitHub
  repository tree were saved so the resource path can be corrected by the
  maintainer.
* The LINDAT binary bitstream URL returned 404. The MTEB Parquet snapshots were
  available and yielded the 128 restricted rows above.
* DCAD's advertised LICENSE path returned 404. Its Garhwali tree metadata was
  saved, but its Common Crawl-derived text was not promoted without source-level
  rights evidence.
* GlotLID and Chaashini require manual agreement to share contact information.
  Their public metadata was saved, while file requests stopped at the gate.
* The Central Hindi Directorate journal PDF timed out during the collector run.
  Its official indexed article remains in the catalog, with no extracted text.
* The Hugging Face row viewer for the pinned Indic Dialect ASR mirror returned
  502/500 after offset 200. The collector recovered all 11 Parquet shards with
  HTTP range reads over the sentence/language/source columns only; no audio was
  downloaded, and the resulting 7,823 rows remain quarantined.
* Google Books' metadata API returned 429 while resolving the 1900 Upreti
  record. The public full-view page exposed a signed scan download, so the
  135-page PDF was acquired from that page and only the Garhwali section was
  extracted. Translatewiki's normal page returned 403; its public API was used
  for the license text instead.
* Kaikki's Garhwali root returned 404; its English-to-Garhwali category landing
  page was saved. Wiktionary itself is the successful lexical source here.

## Reproduction

```text
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/ingest_open.py
python3 scripts/collect_online.py meta
python3 scripts/collect_online.py wiktionary
python3 scripts/collect_online.py extract
PYTHONPATH=/private/tmp/garhwali-parquet python3 scripts/collect_online.py restricted
python3 scripts/collect_online.py uou
python3 scripts/ocr_uou.py
python3 scripts/collect_online.py wayback
python3 scripts/collect_online.py archive_open
python3 scripts/collect_online.py archive_extract
python3 scripts/collect_online.py historical_more_acquire
PYTHONPATH=/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/dependencies/python python3 scripts/collect_online.py historical_more_extract
python3 scripts/collect_online.py opus_acquire
python3 scripts/collect_online.py opus_extract
PYTHONPATH=/private/tmp/garhwali-parquet python3 scripts/collect_online.py indic_asr_range_acquire
python3 scripts/collect_online.py indic_asr_extract
python3 scripts/collect_online.py third_wave_acquire
python3 scripts/collect_online.py third_wave_extract
python3 scripts/collect_online.py fourth_wave_acquire
python3 scripts/collect_online.py fourth_wave_extract
python3 scripts/collect_online.py fifth_wave_acquire
python3 scripts/collect_online.py fifth_wave_extract
.venv/bin/python scripts/ingestion_graph.py run --wave sixth --run-id uou-more-2026-09-08
.venv/bin/python scripts/ingestion_graph.py status --run-id uou-more-2026-09-08
.venv/bin/python scripts/dedup_report.py
.venv/bin/python scripts/verify_ingestion.py
```

The LangGraph workflow, retry rules, checkpoint location, and resume command are
documented in [`PIPELINE.md`](../../PIPELINE.md).

`collect_online.py` never replaces a snapshot whose URL or checksum differs.
Extraction writes through a temporary file and refuses empty or duplicate-ID
outputs. The complete event trail, including failures, is `requests.jsonl`.
