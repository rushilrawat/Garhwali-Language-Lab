# Garhwali public-source search catalog

Verified through 2026-09-30. This is the durable record of the public-source search
performed for the language-lab corpus. A source is listed even when it was
catalogued but not copied into a training layer. Public visibility alone was
not treated as permission to redistribute text, audio, images, or user posts.

## Added or extracted

| Family | Source and access point | Result | Disposition |
| --- | --- | ---: | --- |
| Lexicon, V2 revalidation | [Jambu Garhwali reflex list](https://neojambu.herokuapp.com/languages/Garh) | 763 source rows / 738 distinct forms | `corpus/jambu_garhwali.jsonl` (Git-ignored); all 738 already occur in the current pre-refresh corpus, so **0** new rows this update. The earlier import contributed 710 forms novel versus non-Jambu sources; CC BY 4.0. |
| Lexicon, V2 addition | [Garhwali Language Library 1.0.0](https://github.com/infoakshatsinghbisht-eng/garhwali-language-library), pinned commit `46564fab21299512c104e7b0cbf8bd3064285efd` | 180 static entries / 180 unique strings; 16 exact overlaps / **164 net-new** | `corpus/garhwali_language_library.jsonl` (Git-ignored); words, phrases, proverbs and riddles under MIT. Generated inflections excluded; no native review and not recommended training data. |
| Speech transcripts | [Meta Omnilingual ASR](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus), `gbm_Deva` | 2,927 | `corpus/meta_omni.jsonl`, CC BY 4.0 claim retained |
| Speech aggregation | [Indic Dialect ASR](https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr), pinned revision `ca33c7c2e8ee72e9edc414cb37d1bf0903a3f9ae` | 7,823 | `experimental/indic_dialect_asr_gbm.jsonl`; 1,930 rows cite Meta and 5,893 cite Vaani; active for local experiments with component-lineage and consent flags retained |
| Official Vaani evidence | [Project Vaani](https://vaani.iisc.ac.in/), [full dataset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani), [transcription subset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part) | 110,410 main recordings plus 26 transcription-only recordings; 5,894 supervised utterances / 8.803724 hours | Access was approved and the pinned Garhwali collection was completed on 2026-09-09. All audio, referenced images, manifests, provenance and hashes are under ignored `data/vaani/`; see `research/vaani-collection-completion-2026-09-09.md` |
| Lexicon | [ASJP Garhwali](https://asjp.clld.org/languages/GARHWALI) | 91 concepts | `corpus/asjp.jsonl`, CC BY 4.0 |
| Numerals | [South Asian Numerals Database v1.0](https://zenodo.org/records/15463198) | 123 Garhwali forms | `corpus/sand_garhwali.jsonl`, CC BY 4.0; primary numeral source |
| Numerals | [Chan Numerals v1.0.2](https://zenodo.org/records/15654191) | 40 Garhwali forms | `corpus/chan_numerals_garhwali.jsonl`, CC BY 4.0; 41 Bangani rows excluded from the Garhwali layer |
| Numeral examples | [Special Numerals in South Asian Languages v1.0](https://zenodo.org/records/17985722) | 67 translated examples | `corpus/mamta_southasia_examples.jsonl`, CC BY 4.0; 65 overlapping standalone values catalogued without separate promotion |
| Parallel/evaluation | [IndicGenBench](https://huggingface.co/datasets/google/IndicGenBench_flores_in) Flores, XorQA, Crosssum | 3,847 | `benchmarks/`, evaluation-only |
| Community text | [Tatoeba](https://huggingface.co/datasets/Helsinki-NLP/tatoeba) | 36 | `corpus/tatoeba.jsonl`, CC BY 2.0 FR |
| Wikimedia | Incubator Wikipedia/Wiktionary and English Wiktionary Garhwali categories | 95 | `corpus/`, CC BY-SA 4.0, raw wikitext retained |
| Localization | [OPUS translatewiki](https://opus.nlpl.eu/datasets/translatewiki), `v2026-07-01` | 241 source lines / 181 exact unique messages; 200 aligned pairs | `corpus/opus_translatewiki_gbm.jsonl`; 60 repeated source lines removed, CC BY 3.0 per [translatewiki terms](https://translatewiki.net/wiki/Project:About) |
| Language identification | [PahariLI](https://github.com/rachanagusain/PahariLI) | 15,000 Garhwali labeled sentences | `experimental/paharili_gbm.jsonl`; active for local experiments, with the distinction between repository license and underlying sources retained |
| Phrase translations | [hikinegi Garhwali-Dataset](https://huggingface.co/datasets/hikinegi/Garhwali-Dataset) | 53 | `experimental/hikinegi_garhwali.jsonl`; active locally with missing license/authorship flags retained |
| Learning pages | [eUttaranchal lessons 1–3](https://www.euttaranchal.com/culture/learn-garhwali.php), [LanguagesHome](https://www.languageshome.com/English-Garhwali.htm), and [Omniglot](https://omniglot.com/writing/garhwali.htm) | 189 source rows / 139 additions after corpus-wide exact deduplication | `experimental/web_learning_garhwali.jsonl`; 185 Romanized and 4 Devanagari rows, source URLs and raw-response hashes retained, no open license stated |
| Web literature and folk-text candidates | [Uttarakhand e-Magazine Blogger feed](https://e-magazineofuttarakhand.blogspot.com/), [Jani Mayedi Tani Jayedi](https://uttarakhandkhabarsaar.in/jani-mayedi-tani-jayedi-a-garhwali-short-story/), [Khuded Bhajed](https://uttarakhandkhabarsaar.in/khuded-bhajed-a-garhwali-short-story/) | 6,844 Blogger feed entries scanned; 1,816 title-selected Blogger pages plus 2 story pages; 46 exact duplicate rows skipped; 1,772 exact-new page records / 6,758,808 source characters | `experimental/garhwali_web_goldmines.jsonl` (Git-ignored); local experimental only, rights unassessed, language not confirmed. Pipeline report: [`garhwali-web-goldmines-2026-09-30.md`](../../research/garhwali-web-goldmines-2026-09-30.md) |
| Web text | [DCAD-2000](https://huggingface.co/datasets/openbmb/DCAD-2000) Garhwali tree | 119 | `experimental/dcad_gbm.jsonl`; active locally with Common Crawl component-rights flags retained |
| Web text | [MADLAD-400](https://huggingface.co/datasets/allenai/MADLAD-400) `gbm` clean partition, pinned revision `9d886a76bd8fa69b294f2dd3843dacb8388ee5a5` | 137 upstream documents / 18 exact-novel | 119 DCAD duplicates skipped; novel documents stored in `experimental/madlad400_gbm_clean.jsonl`; source-rights flags remain attached |
| Lexicon | [PanLex mirror](https://huggingface.co/datasets/lbourdois/panlex), filtered `gbm` | 13 forms | `restricted/panlex_gbm.jsonl`; official current PanLex page is CC BY-NC-SA 4.0, applied conservatively |
| University texts | [Uttarakhand Open University CGL](https://uou.ac.in/progdetail?pid=CGL-21) | 436 OCR pages | `restricted/uou_cgl_pages.jsonl`, CC BY-NC-SA 4.0 terms |
| University texts | Uttarakhand Open University MAHL-204 and MAHL-611 | 156 targeted OCR pages / 295,657 characters | `restricted/uou_more_pages.jsonl`, CC BY-NC-SA 4.0 terms; MAHL-610 checksummed but excluded as a duplicate of selected MAHL-204 units |
| Open stories | [Garhwali Open Bible Stories](https://www.freebiblesindia.in/obs/) | 50 stories | `restricted/obs_garhwali.jsonl`, CC BY-NC-SA 4.0; text only, illustrations excluded |
| Open licensed scripture | [Garhwali New Testament](https://www.freebiblesindia.in/bible/gbm/index.html) | 27 books / 260 chapters documented | Source-specific CC BY-SA 4.0 license and download page saved; advertised ZIP currently returns 404 and the public reader presents an access challenge, so no chapter text was promoted |
| Historical book | [Hill Dialects of the Kumaun Division](https://books.google.com/books?id=veUTAAAAYAAJ), Upreti 1900 | 25 Garhwali section pages | `extracted/historical/hill_dialects_1900.jsonl`; Google Books marks the full view public domain; India rights memo remains pending |
| Historical books | [Linguistic Survey of India IX.4](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu), [Proverbs and Folklore](https://archive.org/details/cu31924089930774), 1894, and 1865 manuscript | 534 | `extracted/historical/`; OCR and language-mixture flags retained |
| Historical structured data | [LSI CLDF v1.0](https://zenodo.org/records/8361936) | 185 Garhwali forms | `extracted/historical/lsi_cldf_garhwali.jsonl`; structured derivative of the existing LSI witness |
| Historical grammar | [Kellogg, *A Grammar of the Hindí Language* (1893)](https://archive.org/details/grammarofhindl00kell) | 34 OCR pages mentioning Garhwali | `extracted/historical/kellogg_1893.jsonl`; Public Domain Mark 1.0 evidence saved, pages retain OCR and LSI-overlap flags |
| Historical gazetteer | [Walton, *British Garhwal: A Gazetteer* (1910)](https://archive.org/details/in.ernet.dli.2015.48008) | 2 language-description OCR pages | `extracted/historical/walton_gazetteer_1910.jsonl`; item metadata declares public domain |
| Scholarly research | [Garhwali scholarly guide](../../research/garhwali-scholarly-guide.md) | 5 rights-audited works; 4 full PDFs acquired | Research layer only and zero corpus rows; the fifth publisher served an access challenge, which is recorded explicitly |
| Cultural history and folklore | Atkinson's six-part *Himalayan Gazetteer*, Crooke's two Project Gutenberg folklore volumes, and two 1911 Wikisource articles | 317 exact-unique records / 1,501,195 characters | Public-domain historical cultural-reference layer; OCR, dated terminology and colonial-source flags retained |
| Open cultural media | Wikimedia Commons `Category:Garhwali people` | 754 unique item records | Complete paginated item metadata; media URLs and item-level licenses retained without bulk binary download |
| Thematic vocabulary | [Wiktionary Swadesh list](https://en.wiktionary.org/wiki/Appendix:Garhwali_Swadesh_list), two attributed animal/bird lists, GarhwaliLanguage dictionary, an attributed occupation list, [Mountain Voices](https://mountainvoices.org/i_glossary.html), and a Government of India Ramman source | 666 source records / 642 distinct normalized written forms | `research/garhwali-thematic-lexicon.json` plus a restricted JSONL; every entry is active experimentally with uncertainty and reuse terms retained |
| Idioms and proverbs | [Balakrishna D. Dhyani, *Garhwali Muhavare Aur Kahavaten*](https://sites.google.com/view/dhyani/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B3-%E0%A4%95%E0%A4%95%E0%A4%B7/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B2-%E0%A4%AE%E0%A4%B9%E0%A4%B5%E0%A4%B0-%E0%A4%94%E0%A4%B0-%E0%A4%95%E0%A4%B9%E0%A4%B5%E0%A4%A4) | 99 exact-unique Garhwali records: 69 credited standalone entries and 30 comparison entries | Raw HTML and structured JSONL stored under Git-ignored `data/`; translations and explanations retained; no open license recorded |
| Garhwali story translations | [Door43/TLF Garhwali Open Bible Stories](https://git.door43.org/OBS-TLF/gbm_obs) | 50 | `data/extracted/obs_tlf_v1/records.jsonl`; v1 pinned to revision `f08afc73e1770129fbcd3089181f2faf2abbf54d`; archive manifest and license checked as CC BY-SA 4.0; translation quality remains unreviewed |
| Historical Garhwali dialect table | [Linguistic Survey of India IX.4](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu) | 632 rows / 609 within-source exact-unique strings | `data/extracted/historical/lsi_1916_garhwali_dialect_table.jsonl`; explicitly labeled Standard, Rathi, and Tehri columns; 496 low-confidence OCR rows remain flagged |
| Historical Garhwali narrative specimens | [Linguistic Survey of India IX.4](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu) | 9 dialect specimens, including five newly extracted varieties | `data/extracted/historical/lsi_1916_garhwali_specimens.jsonl`; Srinagar, Tehri, Lohbya, Badhani, Dasaulya, Nagpuriya, and Salani; page-level OCR provenance retained |
| Historical explicitly Garhwali proverbs | [Upreti, *Proverbs & Folklore of Kumaun and Garhwal* (1894)](https://archive.org/details/cu31924089930774) | 5 | `data/extracted/folklore/upreti_1894_garhwali_proverbs.jsonl`; only sayings with explicit Garhwali labels are extracted; spelling and transliteration remain as printed |
| Social media | Public Reddit language discussions and Ghaseri YouTube folk-story pages | 12 exact-unique records / 3,494 characters; 6 additional profiles catalogued | Git-ignored `data/extracted/social_garhwali/`; community vocabulary requires native review; sampled YouTube videos expose no transcript |
| Popular music | [Garhwali popular-song catalog](../../research/garhwali-popular-song-catalog.json), eUttaranchal editorial lists, official/label YouTube channels, Apple Music, and classic-song references | 30 metadata records (16 added in the second pass); 21 include Narendra Singh Negi; 5 lyric-source pointers; 3 meaning/translation pointers; 6 checked videos had no public caption track | Tracked metadata and source links in `research/`; no full modern lyrics, third-party translations, or audio copied; reuse requires an explicit compatible license |
| Geography | [Garhwal Mandal official introduction](https://garhwal.uk.gov.in/about-department/introduction/), [Uttarakhand district portal](https://uttarakhand.s3waas.gov.in/), [Wikipedia Garhwal division](https://en.wikipedia.org/wiki/Garhwal_division), tehsil list, and OpenStreetMap lookup | 50 records: 36 settlements and 14 geographic/cultural features across all seven Garhwal districts | `research/garhwali-geography-catalog.json`; Hindi names, place types, district relationships, Wikipedia and map pointers retained; coordinates intentionally await authoritative gazetteer enrichment |
| Historical terms | [Garhwal Kingdom](https://en.wikipedia.org/wiki/Garhwal_kingdom), [Garhwal division](https://en.wikipedia.org/wiki/Garhwal_division), [Tehri district history](https://tehri.nic.in/history/), [Pauri district history](https://pauri.nic.in/history/), [Board of Revenue history](https://bor.uk.gov.in/content-category/history/), [UJALA Garhwal history study](https://ujala.uk.gov.in/files/HISTORY_OF_GARHWAL_REGION_OF_UTTARAKHAND_By_Ms._Anjali_benjwal%2C_Mr._Anoop_singh_bhakuni__Ms._Hina_kousar.pdf), and [Uttarkashi Census district history](https://censusindia.gov.in/nada/index.php/catalog/1327/download/4322/DH_2011_0501_PART_B_DCHB_UTTARKASHI.pdf) | 36 terms across 25 categories | `research/garhwali-historical-terms.json` and the reproducible extracted view; Hindi forms, periods, variants, and source-linked original summaries retained. This layer supplies historical context and does not relabel dialect evidence. |
| Poetry, plays, and literary history | [Garhwali poetry and plays inventory](../../research/garhwali-poetry-plays-inventory-2026-09-15.md), [structured literary-works catalog](../../research/garhwali-literary-works-catalog.json), [literary-people catalog](../../research/garhwali-literary-people-catalog.json), UOU literature/theatre units, Jeet Singh Negi and Chander Singh Rahi biographies, and the user-supplied Itihaas and writers lists | 66 named works, 26 named people, 3 oral genres, and 2 explicit untitled mentions | Five newly supplied works and all supplied people are visible; spelling and attribution conflicts remain explicit, and no untitled work receives an invented title |
| University and scholarly record | [University/research catalog](../../research/garhwali-university-research-catalog.json), HNBGU/INFLIBNET, Doon University, UOU, SGRR University, University of Kashmir, TUFS, and University of Burdwan | 8 deduplicated institutional records across 7 institutions | Thesis, curriculum, repository-book, syntax, ergativity, folklore, and idiom/proverb evidence is materialized with access-level metadata; the existing UOU extraction is linked instead of counted twice |

## Searched and catalogued without promotion

| Family | Sources checked | Why not copied |
| --- | --- | --- |
| Archives | [Internet Archive](https://archive.org/), Archive metadata/full-text search, Google Books, HathiTrust catalog, [Wayback CDX](https://web.archive.org/) | Archive/Wayback preservation does not grant a reuse license. Modern blogs, poetry, and periodicals were indexed, while author-rights material stayed discovery-only. |
| Wikimedia dumps | Wikimedia API, Incubator pages, Wikimedia dump/category paths | No standalone Garhwali Wikipedia exists in the checked dump inventory; the available Incubator and Wiktionary slices are already extracted above. |
| GitHub/GitLab | Garhwali, `gbm`, Pahari, UKC, GarhwaliLanguage, PahariLI repository searches | Code, model weights, applications, and cards are not linguistic text corpora. PahariLI is the only verified machine-readable Garhwali text source from this pass and is active in the experimental layer above. |
| Academic/institutional | Glottolog, CLDF Meta, Grambank, WALS, PHOIBLE, OLAC, UOU, CIIL/Bharatavani leads, Shodhganga, HimLingo, Hindwi, TUFS idiom lead | Catalog metadata and bibliographies were saved where reachable. No additional anonymous, rights-clear Garhwali text rows were found. HimLingo explicitly restricts scraping; institutional records require an export or permission. |
| Hugging Face mirrors | `VarunGumma/IGB_*`, `mteb/IndicGenBenchFloresBitextMining`, `mlexplorer008/hin_dialect_classification`, MMS ULAB mirrors, Omnilingual mirrors, Vaani derivatives, `somu9/gbm-tokenizer` | Mirrors or gated derivatives of already tracked sources. They were checked for duplication and not counted twice. The mlexplorer dataset mirrors the already retained 128 Garhwali HinDialect rows; the tokenizer is gated and exposes no training corpus. |
| Audio | Common Voice, FLEURS, MMS/ULAB, Vaani, `aoiandroid/mms-multilingual-audio-5to30min` | Vaani is now fully collected locally. Common Voice and FLEURS have no Garhwali config; MMS/YouTube derivatives require source-level duplication and rights review. |
| Kaggle | Indian Language Identification and Samanantar listings | Public listing pages were checked; no verified Garhwali subset with a downloadable rights statement was established in this pass, so no unauthenticated download was attempted. |
| Web scraping | GarhwaliLanguage, Garhwalii, Bol Pahadi, Pahadiaavaj, Vijay Madhur, Kavitakosh, StoryWeaver; Uttarakhand e-Magazine and Khabar Saar were sampled more deeply in wave ten | Wave ten added 1,772 exact-new local experimental page records from the e-Magazine and two Khabar Saar short stories. Their rights remain unassessed and Garhwali identity is unverified; they are not public-HF text. Other landing pages remain discovery references pending source-specific content and reuse review. |
| Gated corpora | [GlotLID corpus](https://huggingface.co/datasets/cis-lmu/glotlid-corpus), [Chaashini](https://huggingface.co/datasets/kapturecx/Chaashini) | Chaashini remains the sole verified VAANI-like gate and currently advertises only one 2.2-second Garhwali clip. GlotLID remains gated, but its current tree exposes no `gbm`/Garhwali payload. |
| Current research and models | [SraVaani 1.0](https://vaani.iisc.ac.in/models/sravaani), [Dhasmana et al. 2026](https://aclanthology.org/2026.vardial-1.12/), [Batra et al. 2026](https://arxiv.org/abs/2608.10670), [Garhwali-ASR repository](https://github.com/soodashima91/Garhwali-ASR) | SraVaani already supports Garhwali in a 65-language ASR model. The papers and reproducibility metadata use official gated VAANI splits or publish aggregate results, so they inform baseline design rather than adding independent training text. |
| Institutional text | [IGNCA oral-tradition volume](https://ignca.gov.in/eBooks/100007.pdf), [Central Hindi Directorate *Bhasha* 2019](https://www.chdpublication.education.gov.in/ebook/pdf/Bhasha%20Sep-Oct%202019.pdf) | Both contain valuable Garhwali linguistic or lexical material but no verified open text license. IGNCA was saved reference-only; the Directorate request timed out and remains catalog-only. |
| Institutional language corpus | [CIIL/LDC-IL released datasets](https://www.ldcil.org/releaseddataset) | Official catalogue explicitly lists “Garhwali Parallel Text Corpus: Linguistic Features and Structures”; no text ingested | The public catalogue establishes a product listing, not access to its Garhwali files, sample, price, or reuse terms. Treat as an acquisition request; do not scrape or infer permission. |
| Large web-corpus partitions | FineWeb-2, GlotCC V1, HPLT 2.0 Cleaned | Current split indexes (3,740 / 1,255 / 191 splits) exposed no separate `gbm`, `garh1243`, or Garhwali partition. |

## Exact deduplication

[`dedup-report.json`](../../outputs/online-ingestion-2026-09-07/dedup-report.json)
computes SHA-256 over each `text_normalized` value across all layers. The
2026-09-07 search snapshot had 33,156 source records and 31,052 exact unique
normalized texts. The 2,104 repeated rows were retained only where source provenance is
useful; the OPUS mono export's 60 repeated lines were removed before corpus
promotion. The largest cross-source overlap is the ASR aggregation: 1,903
unique texts overlap Meta, and one Tatoeba sentence overlaps PahariLI. Four
corpus-to-restricted and seven restricted-to-historical exact overlaps remain
as independently attributed source records. The web-learning addition contains
189 rows / 188 within-file unique texts and contributes 139 new canonical texts
after comparison with every input layer.

The fourth wave found one SAND, two Chan, and nine LSI CLDF exact-text overlaps
against prior or earlier fourth-wave records. The 67 translated numeral examples
and 50 Open Bible Stories had no exact prior match.

The v0.2.0 expansion pipeline reads 696 source rows from four Garhwali-only
outputs (180,043 characters), with 673 unique strings inside the intake and 671
exact-new strings versus the prior corpus layers. Its report is
[`garhwali-data-expansion-2026-09-29.md`](../../research/garhwali-data-expansion-2026-09-29.md)
and its ignored checksum/count artifact is produced by
`scripts/audit_garhwali_expansion.py`.

The 2026-09-30 tenth web wave scanned 6,844 Blogger feed entries and two
Garhwali-labelled short-story pages. It selected 1,818 candidate pages, skipped
46 exact duplicate rows, and added 1,772 exact-new records (6,758,808
characters) to the local all-data candidate pipeline. This is page-level
candidate volume, not a confirmed-Garhwali count: the automated language pass
keeps all 1,772 in low-confidence or unverified buckets. Rights are
unassessed, so the full text stays in the Git-ignored local experimental layer;
the public Hugging Face profile receives no new full-text rows. See the
[dated wave report](../../research/garhwali-web-goldmines-2026-09-30.md) for
source, deduplication, review, and pipeline details. Current corpus metrics
are generated in the repository [README](../../README.md).

## Rate limits and blocked endpoints

The request ledger is [`requests.jsonl`](requests.jsonl). Wiktionary's 429 was
resolved by bounded requests with a delay. The Hugging Face row viewer failed
after offset 200; range reads against the pinned Parquet shards recovered all
7,823 rows without downloading audio. Google Books' metadata API returned 429,
but the public full-view page provided a signed PDF download. PanLex API/filter,
OLAC, UKC ZIP paths, DCAD's license path, and several Wayback CDX endpoints
returned 404/500/503/DNS failures; those failures remain in the ledger and the
sources are not silently treated as complete. The third pass also recorded the
GlotLID manual-gate response and a Central Hindi Directorate timeout. Neither
was treated as a reason to cross an access boundary.
The Heidelberg scholarly-book host returned an Anubis JavaScript proof-of-work
page. Its CC BY-SA metadata was catalogued, but the response was not treated as
the chapter and the challenge was not automated around.

## Follow-up source sweep — 2026-09-30

| Lead checked | Verified public evidence | Corpus decision |
| --- | --- | --- |
| [LDC-IL Garhwali Parallel Text Corpus](https://www.ldcil.org/releaseddataset) | The Ministry of Education/CIIL catalogue lists a Garhwali parallel-text product; the public page does not expose its data payload or applicable component terms. | Acquisition lead only. Request sample, price, source provenance, and model-training/redistribution terms before importing. |
| [Uniyal English–Garhwali SMT study](https://www.pramanaresearch.org/gallery/prj-p431.pdf) and [HNBGU CV](https://www.hnbgu.ac.in/sites/default/files/2023-09/Arushi_Uniyal_CV_2023.pdf) | Research material describes 40,000 monolingual and 30,000 parallel examples / 70,000 digitized sentences; no dataset payload or license was located. | High-priority acquisition request. Deduplicate by source and text if authorized; do not treat paper counts as available rows. |
| [Hindwi Garhwali dictionary](https://www.hindwidictionary.com/garhwali) and [HimLingo dictionary](https://himlingo.com/dictionary/) | Public dictionary pages/catalogue describe Garhwali vocabulary. A machine-readable licensed export was not found; HimLingo's terms prohibit unauthorized scraping. | No scraping or text ingestion. Request permission/export; keep as source-discovery references. |
| [Garhwali UKC lexicon](https://datascientiafoundation.github.io/LiveLanguage/datasets/gbm-ukc-lexicon-/) | The catalogue reports one word/synset and a CC BY-NC-SA license, with Wiktionary/WordNet provenance. | Too small for breadth; noncommercial terms do not support this public release. No text copied. |
| [Community Garhwali/Kumaoni dictionary app claims](https://www.reddit.com/r/PahariTalks/comments/1w1pnrn/would_you_pay_199_for_one_time_for_a_garhwali/) | A developer post claims a 20,000-plus mixed Garhwali/Kumaoni vocabulary and literary items, but exposes no dataset download, provenance, or license. | Unverified acquisition lead. Request source-level data and rights; do not count claims as records. |
| [LibreOffice Weblate Garhwali project](https://translations.documentfoundation.org/projects/libo_ui-26-2/dictionarieste_in/gbm/) | The live project has one string and 0% translated; it is not a substantive Garhwali text corpus. | No useful language text to ingest. |
| [Endangered Languages Project Garhwali profile](https://elcat.colo.hawaii.edu/lang/5632) | Search listings expose language status, dialect labels, and bibliographic metadata, not Garhwali sentence or lexicon payloads; the live profile timed out during direct access. | Reference/metadata lead only; no corpus text ingested. |

This sweep found no second downloadable source with both verifiable Garhwali
text and terms compatible with public redistribution. The only net-new
machine-readable source in this refresh remains the 164-string Garhwali
Language Library addition above. The 53 Hikinegi translation pairs were
rechecked at pinned revision `1f4c1f45d5dd788b82a153510cd2cb2bade7a6`:
all 53 target strings already occur in the corpus and its Hub card has no
license statement, so it contributes zero new public rows.

The claim-level evidence, confidence and remaining gaps are in
[`source-audit-2026-09-08.md`](source-audit-2026-09-08.md).
