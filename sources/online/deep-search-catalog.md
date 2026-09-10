# Garhwali public-source search catalog

Verified through 2026-09-10. This is the durable record of the public-source search
performed for the language-lab corpus. A source is listed even when it was
catalogued but not copied into a training layer. Public visibility alone was
not treated as permission to redistribute text, audio, images, or user posts.

## Added or extracted

| Family | Source and access point | Result | Disposition |
| --- | --- | ---: | --- |
| Speech transcripts | [Meta Omnilingual ASR](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus), `gbm_Deva` | 2,927 | `corpus/meta_omni.jsonl`, CC BY 4.0 claim retained |
| Speech aggregation | [Indic Dialect ASR](https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr), pinned revision `ca33c7c2e8ee72e9edc414cb37d1bf0903a3f9ae` | 7,823 | `quarantine/indic_dialect_asr_gbm.jsonl`; 1,930 rows cite Meta and 5,893 cite Vaani; all remain quarantine until component lineage and consent are reviewed |
| Official Vaani evidence | [Project Vaani](https://vaani.iisc.ac.in/), [full dataset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani), [transcription subset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part) | 110,410 main recordings plus 26 transcription-only recordings; 5,894 supervised utterances / 8.803724 hours | Access was approved and the pinned Garhwali collection was completed on 2026-09-09. All audio, referenced images, manifests, provenance and hashes are under ignored `data/vaani/`; see `research/vaani-collection-completion-2026-09-09.md` |
| Lexicon | [ASJP Garhwali](https://asjp.clld.org/languages/GARHWALI) | 91 concepts | `corpus/asjp.jsonl`, CC BY 4.0 |
| Numerals | [South Asian Numerals Database v1.0](https://zenodo.org/records/15463198) | 123 Garhwali forms | `corpus/sand_garhwali.jsonl`, CC BY 4.0; primary numeral source |
| Numerals | [Chan Numerals v1.0.2](https://zenodo.org/records/15654191) | 40 Garhwali forms | `corpus/chan_numerals_garhwali.jsonl`, CC BY 4.0; 41 Bangani rows excluded from the Garhwali layer |
| Numeral examples | [Special Numerals in South Asian Languages v1.0](https://zenodo.org/records/17985722) | 67 translated examples | `corpus/mamta_southasia_examples.jsonl`, CC BY 4.0; 65 overlapping standalone values catalogued without separate promotion |
| Parallel/evaluation | [IndicGenBench](https://huggingface.co/datasets/google/IndicGenBench_flores_in) Flores, XorQA, Crosssum | 3,847 | `benchmarks/`, evaluation-only |
| Community text | [Tatoeba](https://huggingface.co/datasets/Helsinki-NLP/tatoeba) | 36 | `corpus/tatoeba.jsonl`, CC BY 2.0 FR |
| Wikimedia | Incubator Wikipedia/Wiktionary and English Wiktionary Garhwali categories | 95 | `corpus/`, CC BY-SA 4.0, raw wikitext retained |
| Localization | [OPUS translatewiki](https://opus.nlpl.eu/translatewiki/), `v2026-07-01` | 241 source lines / 181 exact unique messages; 200 aligned pairs | `corpus/opus_translatewiki_gbm.jsonl`; 60 repeated source lines removed, CC BY 3.0 per [translatewiki terms](https://translatewiki.net/wiki/Project:About) |
| Language identification | [PahariLI](https://github.com/rachanagusain/PahariLI) | 15,000 Garhwali labeled sentences | `quarantine/paharili_gbm.jsonl`; Apache repository license does not clear underlying blogs or translated scripture |
| Phrase translations | [hikinegi Garhwali-Dataset](https://huggingface.co/datasets/hikinegi/Garhwali-Dataset) | 53 | `quarantine/hikinegi_garhwali.jsonl`; no license or authorship statement |
| Learning pages | [eUttaranchal lessons 1–3](https://www.euttaranchal.com/culture/learn-garhwali.php), [LanguagesHome](https://www.languageshome.com/English-Garhwali.htm), and [Omniglot](https://omniglot.com/writing/garhwali.htm) | 189 source rows / 139 additions after corpus-wide exact deduplication | `quarantine/web_learning_garhwali.jsonl`; 185 Romanized and 4 Devanagari rows, source URLs and raw-response hashes retained, no open license stated |
| Web text | [DCAD-2000](https://huggingface.co/datasets/openbmb/DCAD-2000) Garhwali tree | 119 | `quarantine/dcad_gbm.jsonl`; Common Crawl component rights are unresolved and the advertised license file is missing |
| Web text | [MADLAD-400](https://huggingface.co/datasets/allenai/MADLAD-400) `gbm` clean partition, pinned revision `9d886a76bd8fa69b294f2dd3843dacb8388ee5a5` | 137 upstream documents / 18 exact-novel | 119 DCAD duplicates skipped; novel documents stored in `quarantine/madlad400_gbm_clean.jsonl`; ODC-BY database terms do not clear underlying page copyrights |
| Lexicon | [PanLex mirror](https://huggingface.co/datasets/lbourdois/panlex), filtered `gbm` | 13 forms | `restricted/panlex_gbm.jsonl`; official current PanLex page is CC BY-NC-SA 4.0, applied conservatively |
| University texts | [Uttarakhand Open University CGL](https://uou.ac.in/progdetail?pid=CGL-21) | 436 OCR pages | `restricted/uou_cgl_pages.jsonl`, CC BY-NC-SA 4.0 terms |
| University texts | Uttarakhand Open University MAHL-204 and MAHL-611 | 156 targeted OCR pages / 295,657 characters | `restricted/uou_more_pages.jsonl`, CC BY-NC-SA 4.0 terms; MAHL-610 checksummed but excluded as a duplicate of selected MAHL-204 units |
| Open stories | [Garhwali Open Bible Stories](https://www.freebiblesindia.in/obs/) | 50 stories | `restricted/obs_garhwali.jsonl`, CC BY-NC-SA 4.0; text only, illustrations excluded |
| Open licensed scripture | [Garhwali New Testament](https://www.freebiblesindia.in/bible/gbm/index.html) | 27 books / 260 chapters documented | Source-specific CC BY-SA 4.0 license and download page saved; advertised ZIP currently returns 404 and the public reader presents an access challenge, so no chapter text was promoted |
| Historical book | [Hill Dialects of the Kumaun Division](https://books.google.com/books?id=veUTAAAAYAAJ), Upreti 1900 | 25 Garhwali section pages | `extracted/historical/hill_dialects_1900.jsonl`; Google Books marks the full view public domain; India rights memo remains pending |
| Historical books | [Linguistic Survey of India IX.4](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4_djvu), [Proverbs and Folklore](https://archive.org/details/cu31924089930774), 1894, and 1865 manuscript | 534 | `extracted/historical/`; OCR and language-mixture flags retained |
| Historical structured data | [LSI CLDF v1.0](https://zenodo.org/records/8361936) | 185 Garhwali forms | `extracted/historical/lsi_cldf_garhwali.jsonl`; structured derivative of the existing LSI witness |
| Historical grammar | [Kellogg, *A Grammar of the Hindí Language* (1893)](https://archive.org/details/grammarofhindl00kell) | 34 OCR pages mentioning Garhwali | `extracted/historical/kellogg_1893.jsonl`; Public Domain Mark 1.0 evidence saved, pages retain OCR and LSI-overlap flags |
| Historical gazetteer | [Walton, *British Garhwal: A Gazetteer* (1910)](https://archive.org/details/in.ernet.dli.2015.48008) | 2 language-description OCR pages | `extracted/historical/walton_gazetteer_1910.jsonl`; item metadata declares public domain |
| Scholarly research | [Garhwali scholarly guide](../../research/garhwali-scholarly-guide.md) | 5 rights-audited works; 4 full PDFs acquired | Research layer only and zero corpus rows; the fifth publisher served an access challenge, which is recorded explicitly |
| Cultural history and folklore | Atkinson's six-part *Himalayan Gazetteer*, Crooke's two Project Gutenberg folklore volumes, and two 1911 Wikisource articles | 317 exact-unique records / 1,501,195 characters | Public-domain historical cultural-reference layer; OCR, dated terminology and colonial-source flags retained |
| Open cultural media | Wikimedia Commons `Category:Garhwali people` | 754 unique item records | Complete paginated item metadata; media URLs and item-level licenses retained without bulk binary download |
| Thematic vocabulary | [Wiktionary Swadesh list](https://en.wiktionary.org/wiki/Appendix:Garhwali_Swadesh_list), two attributed animal/bird lists, GarhwaliLanguage dictionary, an attributed occupation list, [Mountain Voices](https://mountainvoices.org/i_glossary.html), and a Government of India Ramman source | 666 source records / 642 distinct normalized written forms | `research/garhwali-thematic-lexicon.json` plus a restricted JSONL; all entries await native review and sources without reuse terms stay outside the open corpus |
| Idioms and proverbs | [Balakrishna D. Dhyani, *Garhwali Muhavare Aur Kahavaten*](https://sites.google.com/view/dhyani/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B3-%E0%A4%95%E0%A4%95%E0%A4%B7/%E0%A4%97%E0%A4%A2%E0%A4%B5%E0%A4%B2-%E0%A4%AE%E0%A4%B9%E0%A4%B5%E0%A4%B0-%E0%A4%94%E0%A4%B0-%E0%A4%95%E0%A4%B9%E0%A4%B5%E0%A4%A4) | 99 exact-unique Garhwali records: 69 credited standalone entries and 30 comparison entries | Raw HTML and structured JSONL stored under Git-ignored `data/`; translations and explanations retained; no open license recorded |
| Social media | Public Reddit language discussions and Ghaseri YouTube folk-story pages | 12 exact-unique records / 3,494 characters; 6 additional profiles catalogued | Git-ignored `data/extracted/social_garhwali/`; community vocabulary requires native review; sampled YouTube videos expose no transcript |

## Searched and catalogued without promotion

| Family | Sources checked | Why not copied |
| --- | --- | --- |
| Archives | [Internet Archive](https://archive.org/), Archive metadata/full-text search, Google Books, HathiTrust catalog, [Wayback CDX](https://web.archive.org/) | Archive/Wayback preservation does not grant a reuse license. Modern blogs, poetry, and periodicals were indexed, while author-rights material stayed discovery-only. |
| Wikimedia dumps | Wikimedia API, Incubator pages, Wikimedia dump/category paths | No standalone Garhwali Wikipedia exists in the checked dump inventory; the available Incubator and Wiktionary slices are already extracted above. |
| GitHub/GitLab | Garhwali, `gbm`, Pahari, UKC, GarhwaliLanguage, PahariLI repository searches | Code, model weights, applications, and cards are not linguistic text corpora. PahariLI is the only verified machine-readable Garhwali text source from this pass and is quarantined above. |
| Academic/institutional | Glottolog, CLDF Meta, Grambank, WALS, PHOIBLE, OLAC, UOU, CIIL/Bharatavani leads, Shodhganga, HimLingo, Hindwi, TUFS idiom lead | Catalog metadata and bibliographies were saved where reachable. No additional anonymous, rights-clear Garhwali text rows were found. HimLingo explicitly restricts scraping; institutional records require an export or permission. |
| Hugging Face mirrors | `VarunGumma/IGB_*`, `mteb/IndicGenBenchFloresBitextMining`, `mlexplorer008/hin_dialect_classification`, MMS ULAB mirrors, Omnilingual mirrors, Vaani derivatives, `somu9/gbm-tokenizer` | Mirrors or gated derivatives of already tracked sources. They were checked for duplication and not counted twice. The mlexplorer dataset mirrors the already retained 128 Garhwali HinDialect rows; the tokenizer is gated and exposes no training corpus. |
| Audio | Common Voice, FLEURS, MMS/ULAB, Vaani, `aoiandroid/mms-multilingual-audio-5to30min` | Vaani is now fully collected locally. Common Voice and FLEURS have no Garhwali config; MMS/YouTube derivatives require source-level duplication and rights review. |
| Kaggle | Indian Language Identification and Samanantar listings | Public listing pages were checked; no verified Garhwali subset with a downloadable rights statement was established in this pass, so no unauthenticated download was attempted. |
| Web scraping | GarhwaliLanguage, Garhwalii, Bol Pahadi, Pahadiaavaj, Uttarakhand e-magazine, Vijay Madhur, Kavitakosh, StoryWeaver | Wayback/CDX inventories and landing pages are saved. Sampled pages assert author or poet copyright; they remain discovery references pending permission. |
| Gated corpora | [GlotLID corpus](https://huggingface.co/datasets/cis-lmu/glotlid-corpus), [Chaashini](https://huggingface.co/datasets/kapturecx/Chaashini) | Chaashini remains the sole verified VAANI-like gate and currently advertises only one 2.2-second Garhwali clip. GlotLID remains gated, but its current tree exposes no `gbm`/Garhwali payload. |
| Current research | [Dhasmana et al. 2026](https://aclanthology.org/2026.vardial-1.12/), [Batra et al. 2026](https://arxiv.org/abs/2608.10670), [Garhwali-ASR repository](https://github.com/soodashima91/Garhwali-ASR) | Papers and reproducibility metadata were saved. They use official gated VAANI splits or publish aggregate results, so they add evaluation evidence rather than independent training text. |
| Institutional text | [IGNCA oral-tradition volume](https://ignca.gov.in/eBooks/100007.pdf), [Central Hindi Directorate *Bhasha* 2019](https://www.chdpublication.education.gov.in/ebook/pdf/Bhasha%20Sep-Oct%202019.pdf) | Both contain valuable Garhwali linguistic or lexical material but no verified open text license. IGNCA was saved reference-only; the Directorate request timed out and remains catalog-only. |
| Large web-corpus partitions | FineWeb-2, GlotCC V1, HPLT 2.0 Cleaned | Current split indexes (3,740 / 1,255 / 191 splits) exposed no separate `gbm`, `garh1243`, or Garhwali partition. |

## Exact deduplication

[`dedup-report.json`](../../outputs/online-ingestion-2026-09-07/dedup-report.json)
computes SHA-256 over each `text_normalized` value across all layers. The
current snapshot has 33,156 source records and 31,052 exact unique normalized
texts. The 2,104 repeated rows are retained only where source provenance is
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

The claim-level evidence, confidence and remaining gaps are in
[`source-audit-2026-09-08.md`](source-audit-2026-09-08.md).
