# Garhwali online ingestion report

The public-source and archive pass now covers the sources that could be
retrieved anonymously or through an explicitly public download through 2026-09-09.
It is an auditable snapshot, not a claim that every page on the internet was
found. The project contains 32,967 source records: 3,560 in the open text
layer, 3,847 benchmark examples kept evaluation-only, 1,450 non-commercial
records in a restricted layer, 23,013 quarantine records, and 1,097 historical
records. Exact normalized-text deduplication leaves 30,913 unique texts.

The request log contains 403 events across the source families. It includes
401, 403, 404, 429, timeout, DNS and 500/503 responses instead of hiding them.
Wiktionary's 429 was handled; the ASR viewer failed after offset 200 but the
11 pinned Parquet shards were recovered with range reads; Google Books' API
429 was bypassed only by using its public full-view download page. Remaining
endpoint failures are listed in `sources/online/README.md` and the full search
catalog.

Exact deduplication found 1,903 unique Meta/ASR overlaps, one
Tatoeba/PahariLI overlap, and one ASJP/PanLex form collision; these remain
source-separated so provenance and license terms are not lost.

The final verifier checked 365 content-addressed snapshots, unique record IDs,
required rights metadata, and all training gates. The UOU OCR is 72% Devanagari
characters overall; all OCR and newly extracted historical text remain machine
generated and need native review.

## Release boundaries

`corpus/` contains only source records with an explicit upstream license claim
or a documented open database license. Every row is still
`native_reviewed: false` and `training_eligible: false`; this is an ingestion
snapshot, not a finished training release. Benchmark, non-commercial and
historical records live outside that layer. OCR text is uncorrected and may mix
Garhwali, Kumaoni, Hindi and English.

The archive-specific follow-up added four complete Uttarakhand Open University
Garhwali course books (436 OCR pages), the Garhwali sections of Upreti's 1900
*Hill Dialects* scan (25 pages), a one-page 1865 administrative manuscript, and
an openly licensed folk-song thesis record. It also saved Wayback indexes for
nine Garhwali-content domains. Archived modern blog and poetry pages were not
copied into the corpus because sampled pages assert author copyright and
archival availability does not provide a reuse license. The ASR aggregation,
PahariLI, hikinegi and DCAD extracts are quarantined because their source-level
rights or consent remain incomplete.

The third source pass added MADLAD-400's pinned Garhwali clean partition. Of
137 documents, 119 exactly matched the existing DCAD quarantine file and were
skipped before extraction. The remaining 18 documents add 64,821 characters;
seven contain explicit copyright markers, so all remain quarantine-only. The
same pass saved public metadata or reference snapshots for GlotLID, Chaashini,
two current Garhwali ASR studies, their reproducibility repository, and an
IGNCA oral-tradition volume. Gated content was not accessed, and the Central
Hindi Directorate journal remains catalog-only after a timeout.

The fourth wave added three current CC BY 4.0 CLDF families: 123 SAND numeral
forms, 40 Chan Garhwali variants, and 67 translated examples from Special
Numerals in South Asian Languages. Sixty-five standalone values from the last
source were catalogued but not separately ingested because they conceptually
overlap SAND. It also added 50 complete Garhwali Open Bible Stories to the
CC BY-NC-SA restricted layer and 185 LSI CLDF forms to the historical layer as
a structured derivative of the existing LSI OCR. Exact comparison found 12
overlaps across these additions and earlier layers; provenance-specific rows
were retained. The Garhwali New Testament license and download pages were
saved, but its advertised desktop ZIP currently returns 404.

The fifth wave added 34 keyword-selected OCR pages from Kellogg's 1893 grammar
and the two-page Garhwali language passage from Walton's 1910 gazetteer. Both
remain historical, mixed-language, uncorrected OCR records. Their complete OCR
and rights evidence are retained as immutable source snapshots.

The sixth wave added 156 targeted OCR pages from UOU MAHL-204 and MAHL-611,
totalling 295,657 characters in the restricted CC BY-NC-SA layer. MAHL-610 was
downloaded and checksummed but excluded because it duplicates the selected
MAHL-204 units. The wave completed through the checkpointed LangGraph workflow,
which can resume the same run ID after an interruption without duplicating rows.

The seventh wave added a rights-audited research register for five Garhwali
scholarly works. Four full PDFs were acquired and checked; Heidelberg's
CC BY-SA chapter remains a licensed catalogue record because its host returned
an Anubis JavaScript access challenge. Scholarly prose added zero language-data
rows. The resulting guide defines dialect, orthography, code-switching, case,
aspect, provenance and evaluation requirements for the cleanup phase.

The eighth wave used live discovery to add 317 exact-unique public-domain
Garhwal cultural-reference records from Atkinson's six-part *Himalayan
Gazetteer*, Crooke's two folklore volumes, and two 1911 Wikisource articles.
It also completed the paginated Wikimedia Commons `Garhwali people` category:
754 unique media records retain item URLs, creators and licenses without bulk
binary downloads. Modern plays, poetry, podcasts, blogs and books with unclear
or active copyright remain documented rights leads.

## Evidence and files

* [online source register](../../sources/online/README.md)
* [request event log](../../sources/online/requests.jsonl)
* [open-layer counts](../../corpus/ingestion-report.json)
* [collector](../../scripts/collect_online.py)
* [collector tests](../../scripts/test_collect_online.py)
* [legacy importer tests](../../scripts/test_ingest_open.py)
* [full ingestion verifier](../../scripts/verify_ingestion.py)
* [checkpointed ingestion graph](../../scripts/ingestion_graph.py)
* [pipeline and resume guide](../../PIPELINE.md)
* [exact deduplication report](dedup-report.json)
* [deep-search source catalog](../../sources/online/deep-search-catalog.md)
* [third-pass source audit](../../sources/online/source-audit-2026-09-08.md)
* [Garhwali scholarly guide](../../research/garhwali-scholarly-guide.md)
* [cultural ingestion report](../../research/cultural-ingestion-report.md)
* [cultural source leads](../../research/cultural-source-leads.json)

The source inventory workbook remains available at
`outputs/garhwali-corpus-inventory-2026-09-07/GarhwaliCorpus-source-inventory.xlsx`.
