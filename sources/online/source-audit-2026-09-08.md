# Garhwali source audit — started 2026-09-08, updated 2026-09-09

This audit records the third public-source pass and connects each decision to
primary evidence. `Accessible` means an anonymous request succeeded. It does
not mean the material is safe to redistribute or train on. All additions remain
`native_reviewed: false` and `training_eligible: false`.

## Decision register

| Source | Verified finding | Rights/access finding | Duplication and quality result | Disposition | Confidence |
| --- | --- | --- | --- | --- | --- |
| [Project VAANI](https://vaani.iisc.ac.in/) and [official transcription subset](https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part) | The full Garhwali configuration has 110,410 recordings / 136.80 hours; the contained transcription subset has 5,894 utterances / 8.80 hours with official splits 4,778/666/450. | Both official cards declare CC BY 4.0 but require login and a contact-sharing agreement before file access. | The community mirror contains 5,893 Vaani-labeled rows, one fewer than the official count. Exact row reconciliation needs the approved official manifest. District configurations overlap the full language aggregate and must not be added as separate data. | Metadata and discrepancy documented; no gated content accessed. | High |
| [MADLAD-400](https://huggingface.co/datasets/allenai/MADLAD-400), revision `9d886a76bd8fa69b294f2dd3843dacb8388ee5a5` | A dedicated `gbm` clean file contains 137 document-level rows. The paper supplement reports 137 clean documents and manually audits `gbm` as “ok.” | Dataset card declares ODC-BY. This covers database rights and does not establish permission for each underlying Common Crawl page. | SHA-256 comparison found 119 exact matches in `experimental/dcad_gbm.jsonl`; they were skipped. The 18 novel documents contain 64,821 characters, each has a 0.6905–0.9642 Devanagari share of non-space characters, and 7 contain explicit copyright markers. | Raw clean split checksummed; 18 novel documents added to `experimental/madlad400_gbm_clean.jsonl`. The noisy split was deliberately excluded. | High for count and overlap; active locally with source flags |
| [GlotLID corpus](https://huggingface.co/datasets/cis-lmu/glotlid-corpus), revision `63784da4399bb3ea4d04821f7105b31d61ec98bc` | Current metadata, source inventory and v3 language table were saved. | Manual access gate. The card says only metadata and annotations are CC0; text keeps source-specific licenses and some sources cannot be redistributed. The direct card-file request returned 404/401 and was not retried with credentials. | No current public `gbm` file was exposed through the anonymous tree or metadata listing. | Metadata-only lead; zero corpus records. | High |
| [Chaashini](https://huggingface.co/datasets/kapturecx/Chaashini), revision `65839dd883a095c7d477aee9a302d07c9fca0647` | The live card reports one 2.2-second Garhwali clip with an average quality score of 3.28. | Apache-2.0 is declared, but the repository is manually gated and its clips derive from public spoken-word recordings. | Too small to affect current coverage and unavailable anonymously. | Metadata-only lead; zero corpus records and no gate bypass. | High for current card state |
| [Garhwali-ASR research repository](https://github.com/soodashima91/Garhwali-ASR), revision `827942102590caf0184dcfa5defaab7f73109974` | Public code, a 66-token vocabulary, official VAANI split sizes (4,778/666/450), and aggregate per-seed results are available. The repository does not include VAANI transcripts or audio. | The repository API reports no license. VAANI itself remains access-gated. | Results and code are useful for reproducible evaluation design, but adding hypotheses or references to training data would contaminate the benchmark. | Repository metadata, tree, README and data note saved as research evidence; zero corpus records. | High |
| [Dhasmana et al., VarDial 2026](https://aclanthology.org/2026.vardial-1.12/) | Peer-reviewed Garhwali case study over spontaneous, noisy and code-mixed VAANI speech. | ACL publications from 2016 onward are CC BY 4.0. The paper does not release the underlying gated speech. | Adds methodology and error-analysis evidence, not an independent corpus. | Landing page and PDF saved as reference material. | High |
| [Batra et al., 2026](https://arxiv.org/abs/2608.10670) | Reproducible five-seed Garhwali ASR benchmark on official VAANI splits; links to the repository above. | Paper is public on arXiv; underlying VAANI data remains gated. Repository has no declared license. | Confirms that apparent single-run gains can be unstable and supplies aggregate results only. | Landing page and PDF saved as reference material. | High |
| [IGNCA, *Primal Elements: The Oral Tradition*](https://ignca.gov.in/eBooks/100007.pdf) | Institutional volume contains a Garhwali/Garhwal aesthetic-word and idiom discussion with lexical examples. | The volume has an explicit copyright notice and no verified open-content license. | High scholarly value, but extraction would copy modern authored text. | Landing page and PDF saved locally as reference-only; no text rows extracted. | High |
| [Central Hindi Directorate, *Bhasha*, Sep–Oct 2019](https://www.chdpublication.education.gov.in/ebook/pdf/Bhasha%20Sep-Oct%202019.pdf) | Government-hosted journal contains an article on features and history of Garhwali with linguistic examples. | A government host is not itself an open license. No reusable-content license was found. | The collector's direct PDF request timed out; search-index evidence remains available. | Catalog-only; no text rows extracted. Retry only for reference archiving, not corpus promotion. | Medium-high |
| FineWeb-2, GlotCC V1 and HPLT 2.0 Cleaned | Current Hugging Face split indexes were checked for `gbm`, `garh1243`, and “Garhwali.” | Public dataset cards vary by source; source-page rights still require review. | No dedicated Garhwali partition appeared in 3,740 FineWeb-2, 1,255 GlotCC, or 191 HPLT split entries. Broad language-ID scraping would have lower precision than the audited MADLAD partition. | Catalogued as searched; zero records. | High for dedicated-split absence |
| [SAND v1.0](https://zenodo.org/records/15463198) | 123 Garhwali numeral forms were verified from the release-pinned CLDF table. | CC BY 4.0 release metadata was snapshotted. | One exact overlap with earlier material; source-specific phonetic and concept metadata retained. | Added to `corpus/sand_garhwali.jsonl`. | High |
| [Chan Numerals v1.0.2](https://zenodo.org/records/15654191) | 40 rows use the Garhwali source variety `garh1243-2`; 41 `garh1243-1` Bangani rows were identified separately. | CC BY 4.0 release metadata was snapshotted. | Two exact overlaps; Bangani was not mixed into the Garhwali file because current Glottolog classifies it separately. | Added 40 rows to `corpus/chan_numerals_garhwali.jsonl`. | High |
| [Special Numerals in South Asian Languages v1.0](https://zenodo.org/records/17985722) | 65 Garhwali values and 67 translated examples were verified. | CC BY 4.0 release metadata was snapshotted. | Values conceptually overlap SAND; all 67 examples are exact-novel against existing layers. | Added examples only to `corpus/mamta_southasia_examples.jsonl`; values remain catalogued snapshots. | High |
| [Garhwali Open Bible Stories](https://www.freebiblesindia.in/obs/) | All 50 story pages were retrieved and extracted as text-only records. | Catalog footer declares CC BY-NC-SA 4.0; individual story pages do not repeat the license. | No exact prior text match; illustrations excluded and quality remains unreviewed. | Added to `restricted/obs_garhwali.jsonl`. | High for retrieval and license family; medium-high for item-level application |
| [LSI CLDF v1.0](https://zenodo.org/records/8361936) | 185 structured Garhwali forms were verified. | CC BY 4.0 release metadata was snapshotted. | Nine exact overlaps; the whole table derives from the LSI witness already represented as OCR. | Added to the historical layer with derivative flags. | High |
| [Kellogg, *A Grammar of the Hindí Language* (1893)](https://archive.org/details/grammarofhindl00kell) | The 662-page OCR contains 34 pages that explicitly mention Garhwali, including comparative grammar and paradigm evidence. | Wikimedia Commons applies Public Domain Mark 1.0; the rights page and IA OCR are snapshotted. | LSI cites and incorporates Kellogg, so overlap is expected; OCR remains uncorrected and mixed-language. | Added 34 page records to the historical layer. | High |
| [Walton, *British Garhwal: A Gazetteer* (1910)](https://archive.org/details/in.ernet.dli.2015.48008) | Two consecutive scan pages contain the Garhwali language and dialect description. | DLI/IA metadata states “In Public Domain.” | Predominantly English historical description; targeted pages avoid importing the full gazetteer. | Added two page records to the historical layer. | High |
| Uttarakhand Open University MAHL-204, MAHL-610, and MAHL-611 | Targeted Garhwali literature and language units were located in the official study-material PDFs. | UOU's site terms declare study learning material CC BY-NC-SA 4.0; quoted works still need component review. | 156 nonempty pages from MAHL-204 and MAHL-611 produced 295,657 OCR characters. MAHL-610 was excluded because the selected units duplicate MAHL-204. | Added 156 machine-OCR records to `restricted/uou_more_pages.jsonl`; no duplicate course copy added. | High |
| Five open-license scholarly works | ACL, Heidelberg, Asian Research Association, Research Publish and *Linguistics and Oriental Studies from Poznań* supplied directly relevant Garhwali research with explicit CC terms. | Two works are CC BY, one CC BY-SA, one CC BY-NC, and one CC BY-NC-ND. Heidelberg served an Anubis access challenge to the collector, so only its metadata/license record was acquired. | Four full PDFs were checksummed. Scholarly prose was kept outside all language-data layers; NC and ND limits are explicit. | Added five records to `research/scholarly-open-sources.json`, zero corpus rows, and a research synthesis. | High |
| Public-domain cultural sources and open media | Six Atkinson gazetteer parts, two Crooke folklore volumes, two 1911 Wikisource articles and the complete paginated Commons `Garhwali people` file category were acquired through public APIs/downloads. | Atkinson and the 1911 articles are public domain; Project Gutenberg supplies its public-domain terms; every Commons record retains its item-level license. | 317 exact-unique Garhwal text records and 754 unique media metadata records. No media binaries were bulk downloaded. | Historical cultural-reference layer plus a separate media index; all text is active experimentally with its source-language labels retained. | High |

All retrieved URLs, revisions, and checksums are stored in the content-addressed
metadata files and `requests.jsonl`.

## Admission decision

MADLAD supplied substantial anonymous web text, but its ODC-BY declaration is
not enough to promote source-page prose into the open corpus. Exact
deduplication before extraction avoids adding the 119 documents already present
through DCAD. The later CLDF, Open Bible Stories, Kellogg, and Walton additions
have clearer source-level rights and therefore entered their compatible open,
restricted, or historical layers.

The research papers, repository and institutional volumes improve evaluation,
language-history and source discovery. They do not increase the training pool.
GlotLID and Chaashini remain recheck candidates because their live state may
change, but access conditions must be accepted by a person or institution; the
collector does not submit forms or use account tokens.

## Remaining high-value gaps

| Gap | Evidence needed before ingestion | Next safe action |
| --- | --- | --- |
| VAANI Garhwali speech | Provider-approved access, redistribution terms, speaker-consent scope, and stable row provenance | Request a research export and written release terms from Project VAANI |
| HimLingo lexicon | Export license and proof that contributor terms permit redistribution and model training | Seek a licensed database export from the maintainers |
| MADLAD/DCAD web documents | Original URLs or WARC references plus page-level licenses or permissions | Resolve lineage for the 137 clean documents; promote only cleared components |
| Modern dictionaries, literature and periodicals | Author/publisher permission or an explicit open license | Maintain metadata-only records and conduct targeted rights outreach |
| Historical Garhwali books | Stable scans, bibliographic identity, author death dates, and jurisdiction memo | Continue library/archive searches and document public-domain reasoning per item |
| Community speech | Consent terms, speaker demographics, dialect labels and audio-text alignment | Design a consent-first collection effort rather than reusing opaque web audio |

## Reproduction evidence

- Source snapshots are under `sources/online/` and are verified by SHA-256.
- `requests.jsonl` preserves both successes and failures, including the GlotLID
  gate response and Central Hindi Directorate timeout.
- `scripts/collect_online.py third_wave_extract` deterministically recreates the
  18-record MADLAD experimental file after comparing every existing layer.
- `fourth_wave_extract` through `eighth_wave_extract` recreate the CLDF,
  stories, targeted historical, UOU, scholarly-manifest and cultural-reference
  outputs from their checksummed source snapshots.
- `scripts/ingestion_graph.py` checkpoints acquisition, extraction,
  deduplication, and verification in SQLite and supports resuming by run ID.
- `outputs/online-ingestion-2026-09-07/dedup-report.json` records the resulting
  project-wide exact-text overlaps.
