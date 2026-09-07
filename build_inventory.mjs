import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "/Users/rushilrawat/Documents/ChatGPT/Garhwali/outputs/garhwali-corpus-inventory-2026-09-07";
const outputPath = `${outputDir}/GarhwaliCorpus-source-inventory.xlsx`;
const fontFamily = "Arial";

const inventoryHeaders = [
  "Priority", "Source", "Decision", "Corpus layer", "Source type",
  "Verified Garhwali amount", "Format / access", "License / rights basis",
  "Rights confidence", "Dialect / coverage", "Extraction difficulty",
  "Quality / legal risk", "Recommended next action", "Source URL",
  "Rights evidence URL", "Evidence note", "Verified date"
];

const inventory = [
  [1, "Meta Omnilingual ASR Corpus — gbm_Deva", "Ingest now", "Core-open", "Speech + transcript", "2,927 utterances: 2,329 train, 298 dev, 300 test", "Parquet; 16 kHz audio and transcripts via Hugging Face", "CC BY 4.0 stated by upstream publisher", "High", "Garhwali, Devanagari; spontaneous prompted speech", "Easy", "Prompt-driven domain; inspect speaker balance and code-switching", "Ingest from Meta's upstream config; preserve split, prompt, speaker and attribution metadata", "https://huggingface.co/datasets/facebook/omnilingual-asr-corpus", "https://creativecommons.org/licenses/by/4.0/", "Official upstream is preferable to community mirrors", "2026-09-07"],
  [1, "Project Vaani — transcribed Garhwali subset", "Ingest now", "Core-open", "Speech + transcript", "8.80 hours of Garhwali transcription", "Hugging Face dataset; CC acceptance page may apply", "CC BY 4.0", "High", "Uttarakhand districts; language metadata supports filtering", "Medium", "Validate language labels, transcript conventions and district balance", "Download the transcription subset; keep district, speaker and audio provenance", "https://huggingface.co/datasets/ARTPARK-IISc/Vaani-transcription-part", "https://creativecommons.org/licenses/by/4.0/", "Official dataset card reports the Garhwali transcription duration", "2026-09-07"],
  [1, "Project Vaani — full Garhwali recordings", "Ingest now", "Core-open", "Speech, partly transcribed", "136.80 recorded hours reported for Garhwali; only a subset is transcribed", "Gated Hugging Face dataset; district configurations include Tehri Garhwal and Uttarkashi", "CC BY 4.0", "High", "Multiple Uttarakhand districts; modern spoken Garhwali", "Medium", "Gated access; most audio may need transcription; audit consent metadata", "Accept access terms, filter by language metadata, and create a transcription backlog", "https://vaani.iisc.ac.in/", "https://creativecommons.org/licenses/by/4.0/", "Homepage reports Uttarakhand totals and Garhwali recorded hours", "2026-09-07"],
  [1, "Linguistic Survey of India, Vol. 9 Part 4", "Ingest now", "Core-PD historical", "Grammar, lexicon, specimens", "About 74 Garhwali-section pages beginning around page 279", "DJVU/PDF scan with OCR options on Wikimedia Commons", "Public domain scan; 1916 publication", "High", "Historical Garhwali with named regional varieties such as Tehri/Garkapariya", "High", "Old orthography, transliteration, OCR noise and dated labels", "Extract page-by-page; preserve scan page, printed page, transliteration and historical flag", "https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu", "https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu", "Commons marks the scan free of known copyright restrictions", "2026-09-07"],
  [1, "ASJP Garhwali word list", "Ingest now", "Core-open lexicon", "Basic lexicon", "91 extracted concept records", "JSON, RDF and ASJP text download", "CC BY 4.0", "High", "Garhwali / ISO 639-3 gbm", "Easy", "Tiny; romanized coding requires mapping to preferred script conventions", "Ingest with original ASJP form, concept ID, source citation and a separate normalized form", "https://asjp.clld.org/languages/GARHWALI", "https://creativecommons.org/licenses/by/4.0/", "Current ASJP text export yielded 91 records; compiled by Viktoria Smirnova from Kogan 2017", "2026-09-07"],
  [2, "Wikimedia Incubator — Garhwali Wikipedia test", "Ingest now", "Extended-SA", "Encyclopedic text", "35 substantive records from 37 discovered pages; 25,473 raw wikitext characters and about 3,402 whitespace words", "MediaWiki API / XML dump workflow", "CC BY-SA 4.0 plus GFDL", "High", "Mixed modern written Garhwali; likely contributor and translation variation", "Medium", "Templates, navigation, Hindi leakage, short stubs and translated duplicates", "Extract revisions and attribution; strip templates; native-review language purity; keep in share-alike layer", "https://incubator.wikimedia.org/wiki/Wp/gbm", "https://creativecommons.org/licenses/by-sa/4.0/", "Current importer excludes empty pages and redirects; counts reproduced through the public MediaWiki API", "2026-09-07"],
  [2, "English Wiktionary — Garhwali entries and Swadesh appendix", "Ingest now", "Extended-SA lexicon", "Dictionary / concept list", "54 Garhwali lemma pages plus 94 filled Swadesh concepts", "MediaWiki pages and API", "CC BY-SA 4.0 plus GFDL", "High", "Garhwali lemmas; dialect labeling varies by contributor", "Medium", "Overlap with ASJP; entry structure and transliteration are inconsistent", "Extract lemma, sense, transliteration and concept; deduplicate against ASJP; retain revision attribution", "https://en.wiktionary.org/wiki/Category:Garhwali_language", "https://creativecommons.org/licenses/by-sa/4.0/", "Swadesh appendix is a second, partially overlapping source within Wiktionary", "2026-09-07"],
  [3, "Wikimedia Incubator — Garhwali Wiktionary test", "Ingest now", "Extended-SA lexicon", "Dictionary test wiki", "4 prefixed pages; about 1,824 raw characters / 217 whitespace words", "MediaWiki API", "CC BY-SA 4.0 plus GFDL", "High", "Garhwali test project", "Easy", "Mostly scaffolding; minimal lexical yield", "Ingest only substantive entries after excluding interface and navigation content", "https://incubator.wikimedia.org/wiki/Wt/gbm/Main_Page", "https://creativecommons.org/licenses/by-sa/4.0/", "Useful mainly for completeness and contributor discovery", "2026-09-07"],
  [3, "Tatoeba — gbm export", "Ingest after review", "Extended-attribution", "Sentences / parallel links", "36 Garhwali sentences in the detailed export", "TSV exports; sentence and link files", "CC BY 2.0 FR for contributed sentence text", "High", "Unspecified; contributor-level variation", "Easy", "Very small; examples appear unadopted and need native validation", "Quarantine first; native-review every sentence; retain sentence/contributor/license attribution and English links", "https://downloads.tatoeba.org/exports/per_language/gbm/", "https://creativecommons.org/licenses/by/2.0/fr/", "Exact count reproduced from the detailed per-language export", "2026-09-07"],
  [1, "Proverbs & Folklore of Kumaun and Garhwal (1894)", "Ingest after review", "Candidate PD", "Proverbs, translations, notes", "About 1,500 mixed Kumauni/Garhwali proverbs in 413 scanned pages; Garhwali share not yet isolated", "Internet Archive / Open Library / Google Books scan and OCR", "Pre-1931 publication is public domain in the US; India status needs author-death confirmation", "Medium", "Mixed Kumauni and Garhwali; historical varieties", "High", "Language separation, OCR, historic spelling and jurisdiction memo needed", "Locate author death evidence; then segment by language and verify Devanagari against page images", "https://openlibrary.org/books/OL24188813M/Proverbs_folklore_of_Kumaun_and_Garhwal", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html", "Use the 1894 scan, not a modern reprint", "2026-09-07"],
  [2, "Sadei by Tara Dutt Gairola", "Ingest after review", "Candidate PD", "Long narrative poem / folklore", "One book-length Garhwali poem; reliable full scan not located in this search", "Archive or physical-copy digitization needed", "Author died 1940; public domain in India from 2001; pre-1931 publication would also be PD-US", "Medium", "Historical literary Garhwali", "High", "No verified source scan; blog transcriptions may carry site-specific rights or errors", "Locate a dated scan or physical copy, verify edition, then OCR and double-key the poem", "https://e-magazineofuttarakhand.blogspot.com/2013/06/sadei-poetic-folktale-about-unique.html", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html", "The linked page is a discovery lead, not the text source to ingest", "2026-09-07"],
  [2, "Garhwali Kavitavali, edited by Tara Dutt Gairola", "Ingest after review", "Rights audit", "Poetry anthology", "Early anthology; exact edition and digitized page count not verified", "Archive / library search required", "Per-poem author and publication-date audit required", "Low", "Multiple early Garhwali poets and literary registers", "High", "Editor death does not clear copyright in every contributor's poem", "Build a contents-level author/date ledger before digitizing any poem", "https://en.wikipedia.org/wiki/Taradutt_Gairola", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html", "Bibliographic lead only; replace with catalog and scan evidence when located", "2026-09-07"],
  [3, "Himalayan Folklore (1935)", "Reference only", "Metadata / rights hold", "English translations of oral ballads", "Full 1935 book; Garhwali source-language yield appears limited", "Internet Archive / Indian Culture links through UttarakhandHub", "Public domain in India; likely US copyright through 2031 under URAA", "Medium", "Kumaon, Garhwal and West Nepal; mostly English rendering", "Medium", "Global redistribution risk; not a large Garhwali text source", "Use as cultural metadata and source-finding aid; do not redistribute the full text globally before rights clear", "https://uttarakhandhub.com/library/himalayan-folklore", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html", "A jurisdiction-specific rights exception, not a core Garhwali corpus source", "2026-09-07"],
  [1, "PahariLI", "Reference only", "Quarantine", "Language-ID sentence corpus", "15,000 Garhwali sentences; paper reports 237,534 words and 27,243 types", "GitHub train/test text files", "Repository says Apache 2.0, but underlying blogs and translated New Testament are not shown as cleared", "Low", "Mixed web genres plus 5,000 translated New Testament sentences", "Easy", "Software/repository license may not sublicense underlying copyrighted text", "Use for source discovery or private evaluation only; obtain a provenance/rights statement or rebuild from cleared originals", "https://github.com/rachanagusain/PahariLI", "https://github.com/rachanagusain/PahariLI/blob/main/LICENSE", "Do not place in the rights-cleared release solely because the repository has an Apache license", "2026-09-07"],
  [2, "MADLAD-400 — Garhwali clean split", "Reference only", "Quarantine", "Web text crawl", "137 clean documents; about 499.6K clean characters and 99.7K clean words in the dataset audit", "Hugging Face / Common Crawl-derived text", "ODC-BY for the database; underlying page copyrights can persist", "Medium", "Web-derived Garhwali, dialect and language-ID quality uncertain", "Easy", "Database license is not blanket clearance for every crawled work", "Use as a URL discovery and dedup/reference set; only promote documents with source-level licenses", "https://huggingface.co/datasets/allenai/MADLAD-400", "https://opendatacommons.org/licenses/by/1-0/", "Useful scale signal, not a rights-cleared core by default", "2026-09-07"],
  [3, "indic-dialect-asr — Garhwali mirror", "Exclude duplicate", "Do not ingest", "Speech + transcript mirror", "7,823 rows / about 2.31 GB Parquet in the mirror", "Hugging Face community dataset", "Mirror declares CC BY 4.0; sample rows cite facebook/omnilingual-asr-corpus", "Medium", "Garhwali label; exact additions beyond upstream were not documented", "Easy", "Row count differs from Meta's official 2,927-item gbm_Deva config; provenance transformation unclear", "Ingest Meta upstream directly; reconsider mirror only after the maintainer documents every added source and transform", "https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr", "https://huggingface.co/datasets/facebook/omnilingual-asr-corpus", "Avoid duplicate audio and ambiguous attribution", "2026-09-07"],
  [1, "HimLingo Garhwali dictionary", "Permission required", "Partnership lead", "Community dictionary", "4,206 Garhwali words across 13 dialects reported on site", "Website; no authorized bulk export located", "All rights reserved / terms prohibit scraping without permission", "High", "Strong modern dialect coverage", "Medium", "Contributor ownership; site receives only a non-exclusive contributor license", "Request a separately licensed export, contributor-sublicense warranty and provenance fields; do not scrape", "https://himlingo.com/", "https://himlingo.com/terms-of-services/", "Highest-value permission outreach lead", "2026-09-07"],
  [2, "Hindwi Garhwali Dictionary", "Permission required", "Partnership lead", "Online dictionary", "Quantity not verified; Garhwali search portal exists", "Website search interface", "No open license found", "Low", "Modern lexical content", "Medium", "No redistribution grant; automated access may be blocked", "Ask the publisher for a licensed data export and attribution requirements", "https://www.hindwidictionary.com/garhwali", "https://www.hindwidictionary.com/garhwali", "Do not infer permission from public web access", "2026-09-07"],
  [2, "TUFS repository — Garhwali idioms/proverbs collection", "Permission required", "Partnership lead", "Idioms and proverbs", "Record and table-of-contents files located; full usable text amount not verified", "Institutional repository record", "No reuse license found on the record", "Low", "Garhwali phraseology", "Medium", "Modern compilation rights; repository access is not reuse permission", "Contact author/repository for a machine-readable export and explicit corpus license", "https://tufs.repo.nii.ac.jp/records/17829", "https://tufs.repo.nii.ac.jp/records/17829", "Potentially high linguistic value if licensed", "2026-09-07"],
  [2, "Garhwali periodical / newspaper archive (founded 1905)", "Permission required", "Archive hunt", "Periodical prose", "No rights-cleared digitized run located", "Library, archive or publisher holdings", "Issue- and contributor-level rights audit required", "Low", "Historical public prose and literary Garhwali", "High", "Anonymous/pseudonymous items, later issues, photos and advertisements have different terms", "Identify holdings and digitize issue-by-issue with a contributor/date rights ledger", "https://en.wikipedia.org/wiki/Garhwali_language", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html", "High upside but not ready for ingestion", "2026-09-07"],
  [1, "Garhwali New Testament / Bible translation", "Permission required", "Do not ingest", "Parallel religious text", "PahariLI reports 5,000 sentences derived from a translated New Testament", "Web/app text and derived corpus", "No open text license confirmed for the Garhwali translation", "Low", "Religious translation register", "Easy", "Modern translation copyright; presence in another corpus does not clear redistribution", "Seek written permission from the translation rights holder or exclude", "https://www.bible.com/languages/gbm", "https://www.bible.com/terms", "Rights issue likely explains a large portion of PahariLI risk", "2026-09-07"],
  [3, "BhashaDaan / BHASHINI contribution channel", "Collection channel", "Future CC0", "Crowdsourced speech/text", "No specific existing Garhwali release confirmed", "Government collection portal", "Contribution terms state CC0 1.0 for contributed data", "Medium", "Can be configured for community Garhwali collection", "Medium", "Confirm consent flow, moderation and export availability before launch", "Use as a future native-speaker collection pipeline; verify catalog and export mechanics first", "https://bhashini.gov.in/bhashadaan/", "https://bhashini.gov.in/bhashadaan/or/terms-and-conditions", "Channel, not a verified current Garhwali dataset", "2026-09-07"],
  [3, "Mozilla Common Voice", "Collection channel", "Future CC0", "Crowdsourced speech", "No Garhwali locale found in the current dataset catalog", "Mozilla Data Collective", "CC0 1.0 for Common Voice datasets", "High", "Potential modern community speech", "High", "Requires locale onboarding, prompt creation and sustained validation community", "Treat as a future collection program, not an existing source", "https://commonvoice.mozilla.org/en/datasets", "https://creativecommons.org/publicdomain/zero/1.0/", "Current catalog check found no Garhwali dataset", "2026-09-07"]
];

const rightsHeaders = ["Rights class", "Redistribute?", "Corpus treatment", "Required controls", "Primary failure mode", "Authority / license URL"];
const rightsRows = [
  ["CC0 1.0", "Yes", "Core-open", "Store source and release version even though attribution is not required", "Dataset may still contain privacy or consent defects", "https://creativecommons.org/publicdomain/zero/1.0/"],
  ["CC BY 4.0", "Yes", "Core-open", "Attribution, license link and modification notice; preserve item/source metadata", "Losing contributor or source attribution during normalization", "https://creativecommons.org/licenses/by/4.0/"],
  ["CC BY-SA 4.0", "Yes, under compatible share-alike terms", "Extended-SA", "Separate release layer; attribution, license link, modification notice and share-alike compliance", "Mixing share-alike text into a corpus promised under a more permissive blanket license", "https://creativecommons.org/licenses/by-sa/4.0/"],
  ["CC BY 2.0 FR", "Yes", "Extended-attribution", "Retain the exact license version/jurisdiction, contributor and sentence ID", "Collapsing it to generic 'CC BY' and losing version-specific notice", "https://creativecommons.org/licenses/by/2.0/fr/"],
  ["Public domain", "Yes after jurisdiction check", "Core-PD", "Record author death/publication dates, edition, scan rights and jurisdictions", "Assuming 'old' or 'digitized by a library' automatically means public domain everywhere", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html"],
  ["ODC-BY database", "Database reuse may be allowed", "Quarantine until item-level audit", "Track source URLs and the copyright/license of each underlying document", "Treating database rights as copyright clearance for crawled works", "https://opendatacommons.org/licenses/by/1-0/"],
  ["Software/repository license only", "Not enough for content", "Quarantine", "Obtain an explicit data/content license plus source-provenance schedule", "Apache/MIT on code is mistakenly applied to blogs, books or translations bundled as data", "https://www.apache.org/licenses/LICENSE-2.0"],
  ["No license / all rights reserved", "No", "Permission required", "Written export license, sublicense authority, contributor consent and attribution terms", "Public accessibility is mistaken for permission to scrape and redistribute", "https://copyright.gov.in/Copyright_Act_1957/chapter_v.html"],
  ["Indian government publication", "Not automatically", "Rights audit", "Check Section 28 term, first-publication date and any stated open-data license", "A .gov.in host is incorrectly treated as public domain", "https://www.indiacode.nic.in/bitstream/123456789/15356/1/the_copyright_act%2C_1957.pdf"]
];

const schemaHeaders = ["Field", "Type", "Required", "Purpose", "Example / rule", "Validation"];
const schemaRows = [
  ["record_id", "string", "Yes", "Stable internal identifier", "gbm_meta_000001", "Unique, immutable"],
  ["text_original", "string", "For text", "Verbatim source text", "Preserve punctuation and spelling", "Never silently overwrite"],
  ["text_normalized", "string", "Recommended", "Search/training normalization", "Unicode NFC; documented punctuation policy", "Transformation version required"],
  ["script", "string", "Yes", "Writing system", "Deva or Latn", "ISO 15924"],
  ["iso_639_3", "string", "Yes", "Language identity", "gbm", "Fixed to gbm unless a mixed-language flag applies"],
  ["language_confidence", "number", "Recommended", "Language-ID certainty", "0.98", "0 to 1; native review overrides model score"],
  ["source_id", "string", "Yes", "Joins to source inventory", "meta_omni_gbm", "Controlled vocabulary"],
  ["source_url", "string", "Yes", "Source-level provenance", "Dataset homepage", "HTTPS URL or archival catalog ID"],
  ["item_url", "string", "When available", "Record-level provenance", "Wiki revision or sentence URL", "Prefer immutable/permalink URL"],
  ["retrieval_date", "date", "Yes", "Reproducibility", "2026-09-07", "ISO 8601 date"],
  ["source_title", "string", "Yes", "Human-readable citation", "Omnilingual ASR Corpus", "Non-empty"],
  ["creator", "string", "When known", "Attribution and rights", "Contributor, author or institution", "Do not collapse multiple creators"],
  ["publication_date", "date/string", "When known", "Rights and historical analysis", "1916 or 2025-11-10", "Precision flag if year-only"],
  ["rights_status", "string", "Yes", "Machine-actionable release gate", "cc_by_4 / pd_verified / permission / quarantine", "Controlled vocabulary"],
  ["license_id", "string", "Yes", "Exact license label", "CC-BY-4.0", "SPDX where possible"],
  ["license_url", "string", "Yes", "License evidence", "Canonical deed/legal URL", "Must match license_id"],
  ["rights_jurisdiction", "string", "For PD/complex", "Jurisdiction scope", "IN; US", "Controlled ISO country codes"],
  ["rights_evidence", "string", "Yes", "Audit trail", "Dataset card statement or dated rights memo", "Quote sparingly; store URL and access date"],
  ["attribution_text", "string", "For attributed sources", "Ready-to-publish credit", "Source, creator, license, changes", "Release-builder check"],
  ["modifications", "string", "Recommended", "License compliance", "OCR corrected; punctuation normalized", "Enumerate material transforms"],
  ["corpus_layer", "string", "Yes", "License-compatible packaging", "core_open / core_pd / extended_sa / quarantine", "Controlled vocabulary"],
  ["dialect", "string", "Recommended", "Dialect-aware modeling", "Tehri Garhwali", "Use source label plus normalized label"],
  ["location", "string", "When available", "Geographic coverage", "Uttarkashi district", "Use stable gazetteer identifiers when possible"],
  ["genre", "string", "Yes", "Balance and evaluation", "conversation / proverb / encyclopedia / poetry", "Controlled vocabulary"],
  ["modality", "string", "Yes", "Text/audio handling", "text / speech / aligned", "Controlled vocabulary"],
  ["audio_id", "string", "For speech", "Audio-text join", "gbm_meta_spk02_s01", "Unique within source"],
  ["speaker_id", "string", "For speech", "Speaker-disjoint splits", "Hashed source speaker ID", "No direct personal identifiers"],
  ["speaker_consent_basis", "string", "For collected speech", "Ethics and reuse audit", "Dataset consent protocol ID", "Required before public release"],
  ["quality_status", "string", "Yes", "Curation gate", "raw / auto_checked / native_reviewed / rejected", "Controlled vocabulary"],
  ["native_reviewed", "boolean", "Recommended", "Human-language validation", "TRUE", "Reviewer log required when true"],
  ["historical", "boolean", "Yes", "Separate historical and modern text", "TRUE for LSI", "Boolean"],
  ["sensitive_content", "string", "Recommended", "Safety and community review", "none / personal / sacred / restricted", "Controlled vocabulary; escalate non-none"],
  ["duplicate_group", "string", "Recommended", "Cross-source deduplication", "dup_000042", "Same value for exact/near duplicates"],
  ["split", "string", "For model-ready release", "Leakage control", "train / validation / test", "Speaker/document disjoint as applicable"],
  ["checksum_sha256", "string", "Yes", "Integrity and reproducibility", "64-hex digest", "Recompute after material change"]
];

const wb = Workbook.create();
const inventorySheet = wb.worksheets.add("Inventory");
const rightsSheet = wb.worksheets.add("Rights guide");
const schemaSheet = wb.worksheets.add("Corpus schema");

for (const sheet of [inventorySheet, rightsSheet, schemaSheet]) {
  sheet.showGridLines = false;
}
inventorySheet.tabColor = "#1D4ED8";
rightsSheet.tabColor = "#7C3AED";
schemaSheet.tabColor = "#0F766E";

// Inventory sheet
inventorySheet.getRange("A2:Q2").format.font = { name: fontFamily, size: 14, bold: true, color: "#111827" };
inventorySheet.getRange("A2").values = [["GarhwaliCorpus source inventory"]];
inventorySheet.getRange("A3").values = [["Rights-first inventory for a publishable Garhwali corpus • Evidence verified 2026-09-07 • Core and license-constrained layers kept separate"]];
inventorySheet.getRange("A3:Q3").format.font = { name: fontFamily, size: 10, italic: true, color: "#4B5563" };
inventorySheet.getRange("A4:Q4").format.borders = { bottom: { style: "thin", color: "#CBD5E1" } };

inventorySheet.getRange("A5:N5").values = [["Ingest now", null, null, "After review", null, null, "Permission needed", null, null, "Reference / excluded", null, null, "Collection channels", null]];
inventorySheet.getRange("A6:N6").formulas = [[
  `=COUNTIF($C$9:$C$${inventory.length + 8},"Ingest now")`, null, null,
  `=COUNTIF($C$9:$C$${inventory.length + 8},"Ingest after review")`, null, null,
  `=COUNTIF($C$9:$C$${inventory.length + 8},"Permission required")`, null, null,
  `=COUNTIF($C$9:$C$${inventory.length + 8},"Reference only")+COUNTIF($C$9:$C$${inventory.length + 8},"Exclude duplicate")`, null, null,
  `=COUNTIF($C$9:$C$${inventory.length + 8},"Collection channel")`, null
]];
for (const cell of ["A5:B6", "D5:E6", "G5:H6", "J5:K6", "M5:N6"]) {
  inventorySheet.getRange(cell).format = {
    fill: "#F8FAFC",
    font: { name: fontFamily, size: 10, color: "#334155" },
    borders: { preset: "outside", style: "thin", color: "#CBD5E1" },
    verticalAlignment: "center"
  };
}
inventorySheet.getRange("A6:N6").format.font = { name: fontFamily, size: 13, bold: true, color: "#0F172A" };
inventorySheet.getRange("A7").values = [["Decision rule: no public-web text enters the rights-cleared core without a traceable license, public-domain memo, or written permission."]];
inventorySheet.getRange("A7:Q7").format.font = { name: fontFamily, size: 10, italic: true, color: "#9A3412" };

inventorySheet.getRange("A8:Q8").values = [inventoryHeaders];
inventorySheet.getRange(`A9:Q${inventory.length + 8}`).values = inventory;
const inventoryTable = inventorySheet.tables.add(`A8:Q${inventory.length + 8}`, true, "GarhwaliSourceInventory");
inventoryTable.style = "TableStyleMedium2";
inventoryTable.showBandedColumns = false;
inventoryTable.showFilterButton = true;
inventorySheet.getRange("A8:Q8").format = {
  fill: "#1E3A8A",
  font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { insideVertical: { style: "thin", color: "#FFFFFF" }, bottom: { style: "medium", color: "#1E3A8A" } }
};
inventorySheet.getRange(`A9:Q${inventory.length + 8}`).format = {
  font: { name: fontFamily, size: 9, color: "#111827" },
  verticalAlignment: "top",
  wrapText: true
};
inventorySheet.getRange(`A9:A${inventory.length + 8}`).format.horizontalAlignment = "center";
inventorySheet.getRange(`I9:K${inventory.length + 8}`).format.horizontalAlignment = "center";
inventorySheet.getRange(`Q9:Q${inventory.length + 8}`).setNumberFormat("yyyy-mm-dd");
inventorySheet.getRange(`N9:O${inventory.length + 8}`).format = { font: { name: fontFamily, size: 9, color: "#1D4ED8", underline: true }, wrapText: false, verticalAlignment: "top" };

const decisionRange = inventorySheet.getRange(`C9:C${inventory.length + 8}`);
decisionRange.conditionalFormats.add("containsText", { text: "Ingest now", format: { fill: "#DCFCE7", font: { color: "#166534", bold: true } } });
decisionRange.conditionalFormats.add("containsText", { text: "Ingest after review", format: { fill: "#FEF3C7", font: { color: "#92400E", bold: true } } });
decisionRange.conditionalFormats.add("containsText", { text: "Permission required", format: { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } } });
decisionRange.conditionalFormats.add("containsText", { text: "Reference only", format: { fill: "#EDE9FE", font: { color: "#5B21B6", bold: true } } });
decisionRange.conditionalFormats.add("containsText", { text: "Exclude duplicate", format: { fill: "#E5E7EB", font: { color: "#374151", bold: true } } });
decisionRange.conditionalFormats.add("containsText", { text: "Collection channel", format: { fill: "#DBEAFE", font: { color: "#1E40AF", bold: true } } });

const invWidths = [56, 190, 118, 108, 112, 185, 170, 175, 86, 150, 86, 210, 230, 165, 165, 205, 84];
invWidths.forEach((w, i) => inventorySheet.getRangeByIndexes(0, i, inventory.length + 8, 1).format.columnWidthPx = w);
inventorySheet.getRange("1:1").format.rowHeightPx = 10;
inventorySheet.getRange("2:2").format.rowHeightPx = 26;
inventorySheet.getRange("3:3").format.rowHeightPx = 20;
inventorySheet.getRange("5:6").format.rowHeightPx = 22;
inventorySheet.getRange("8:8").format.rowHeightPx = 34;
inventorySheet.getRange(`9:${inventory.length + 8}`).format.rowHeightPx = 64;
inventorySheet.freezePanes.freezeRows(8);
inventorySheet.freezePanes.freezeColumns(3);

// Rights guide
rightsSheet.getRange("A2:F2").format.font = { name: fontFamily, size: 14, bold: true, color: "#111827" };
rightsSheet.getRange("A2").values = [["Rights guide for corpus admission"]];
rightsSheet.getRange("A3").values = [["Operational guidance, not legal advice. A source is admitted only when the rights class and evidence are stored at source and item level."]];
rightsSheet.getRange("A3:F3").format.font = { name: fontFamily, size: 10, italic: true, color: "#4B5563" };
rightsSheet.getRange("A4:F4").format.borders = { bottom: { style: "thin", color: "#CBD5E1" } };
rightsSheet.getRange("A5:F5").values = [rightsHeaders];
rightsSheet.getRange(`A6:F${rightsRows.length + 5}`).values = rightsRows;
const rightsTable = rightsSheet.tables.add(`A5:F${rightsRows.length + 5}`, true, "RightsDecisionGuide");
rightsTable.style = "TableStyleMedium4";
rightsSheet.getRange("A5:F5").format = { fill: "#5B21B6", font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true, borders: { insideVertical: { style: "thin", color: "#FFFFFF" } } };
rightsSheet.getRange(`A6:F${rightsRows.length + 5}`).format = { font: { name: fontFamily, size: 10, color: "#111827" }, verticalAlignment: "top", wrapText: true };
rightsSheet.getRange(`F6:F${rightsRows.length + 5}`).format = { font: { name: fontFamily, size: 10, color: "#1D4ED8", underline: true }, verticalAlignment: "top", wrapText: false };
[150, 100, 135, 235, 235, 190].forEach((w, i) => rightsSheet.getRangeByIndexes(0, i, rightsRows.length + 5, 1).format.columnWidthPx = w);
rightsSheet.getRange("1:1").format.rowHeightPx = 10;
rightsSheet.getRange("5:5").format.rowHeightPx = 32;
rightsSheet.getRange(`6:${rightsRows.length + 5}`).format.rowHeightPx = 58;
rightsSheet.freezePanes.freezeRows(5);

// Corpus schema
schemaSheet.getRange("A2:F2").format.font = { name: fontFamily, size: 14, bold: true, color: "#111827" };
schemaSheet.getRange("A2").values = [["Minimum provenance schema"]];
schemaSheet.getRange("A3").values = [["One record per text unit or audio segment. Preserve originals; normalization and rights decisions are explicit fields, never destructive edits."]];
schemaSheet.getRange("A3:F3").format.font = { name: fontFamily, size: 10, italic: true, color: "#4B5563" };
schemaSheet.getRange("A4:F4").format.borders = { bottom: { style: "thin", color: "#CBD5E1" } };
schemaSheet.getRange("A5:F5").values = [schemaHeaders];
schemaSheet.getRange(`A6:F${schemaRows.length + 5}`).values = schemaRows;
const schemaTable = schemaSheet.tables.add(`A5:F${schemaRows.length + 5}`, true, "CorpusProvenanceSchema");
schemaTable.style = "TableStyleMedium9";
schemaSheet.getRange("A5:F5").format = { fill: "#0F766E", font: { name: fontFamily, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true, borders: { insideVertical: { style: "thin", color: "#FFFFFF" } } };
schemaSheet.getRange(`A6:F${schemaRows.length + 5}`).format = { font: { name: fontFamily, size: 10, color: "#111827" }, verticalAlignment: "top", wrapText: true };
[150, 90, 95, 210, 250, 210].forEach((w, i) => schemaSheet.getRangeByIndexes(0, i, schemaRows.length + 5, 1).format.columnWidthPx = w);
schemaSheet.getRange("1:1").format.rowHeightPx = 10;
schemaSheet.getRange("5:5").format.rowHeightPx = 32;
schemaSheet.getRange(`6:${schemaRows.length + 5}`).format.rowHeightPx = 42;
schemaSheet.freezePanes.freezeRows(5);

wb.recalculate();
await fs.mkdir(outputDir, { recursive: true });

const inspect = await wb.inspect({ kind: "workbook,sheet,table", maxChars: 6000, tableMaxRows: 5, tableMaxCols: 8, tableMaxCellChars: 80 });
await fs.writeFile(`${outputDir}/inspection.txt`, inspect.ndjson ?? String(inspect), "utf8");

for (const sheetName of ["Inventory", "Rights guide", "Corpus schema"]) {
  const preview = await wb.render({ sheetName, autoCrop: "all", scale: 1, format: "png" });
  const safeName = sheetName.toLowerCase().replaceAll(" ", "-");
  await fs.writeFile(`${outputDir}/${safeName}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(outputPath);

console.log(JSON.stringify({ outputPath, rows: inventory.length, rightsRows: rightsRows.length, schemaRows: schemaRows.length }));
