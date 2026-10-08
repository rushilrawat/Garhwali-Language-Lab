# Garhwali source expansion included in v0.2.1 (2026-09-30)

This filename is kept for link compatibility; **v0.2.1** is the project release
identifier.

## What changed

The v0.2.1 refresh pins and re-runs two attributable Garhwali lexical sources through
the existing canonicalization, quality, split, export, and report pipeline. The
intake comparison is deliberately based on exact normalized text hashes; source
rows and their provenance remain available even when their text duplicates an
existing form.

| Source | Source rows | Distinct source strings | Already represented | Exact-new in this update | Treatment |
| --- | ---: | ---: | ---: | ---: | --- |
| [Jambu Garhwali reflex list](https://neojambu.herokuapp.com/languages/Garh) | 763 | 738 | 738 | 0 | Previously included in the local corpus; v0.2.1 revalidates the pinned snapshot. CC BY 4.0. |
| [Garhwali Language Library 1.0.0](https://github.com/infoakshatsinghbisht-eng/garhwali-language-library) | 180 | 180 | 16 | 164 | Newly integrated static words, phrases, proverbs, and riddles. MIT is recorded; upstream language labels and glosses are not native-reviewed. |

The Jambu source's original comparison found 28 forms overlapping other source
families and 710 forms not found in those families. Those 710 were already part
of the prior local corpus: counting them again as a new v0.2.1 addition would be
incorrect. Jambu and the static Language Library files have zero exact matches
to one another. The Language Library's 16 matches retain both source histories
but do not inflate the unique-text total.

Only the four static upstream JSON files are ingested from the Language
Library. Its code can generate large inflection lists, but generated forms are
not independent observations, are not counted as collected language examples,
and are not added to the recommended training set. All 180 rows remain tagged
experimental and ineligible for recommended training pending linguistic review.

The local pipeline's pre-refresh `canonical.jsonl` reported 31,908 exact-unique
parent texts. The 164 exact-new library strings therefore imply 32,072 after
rebuild if no unrelated inputs change. The generated v0.2.1 metrics and package
manifests are the authoritative post-build counts; see
`data/extracted/current_corpus_metrics.json` (local generated file)
and the root [README](../README.md). Package row totals overlap across configs
and must not be presented as unique examples.

## Internet and institutional-source review

The additional targeted search covered official Indian-language corpus
catalogues, Garhwali machine-translation research, university CVs, cultural
publisher listings, Hugging Face/GitHub dataset discovery, and exact overlap
against the already-collected project sources. No other new public Garhwali
text payload with both verified language scope and compatible redistribution
terms was found in this pass. Several high-value acquisition leads now have
explicit records in [`cultural-source-leads.json`](cultural-source-leads.json):

| Lead | What the public record establishes | Why no text was copied | Next useful action |
| --- | --- | --- | --- |
| [LDC-IL released-dataset catalogue](https://www.ldcil.org/releaseddataset) | The official catalogue lists a **Garhwali Parallel Text Corpus: Linguistic Features and Structures**. | The catalogue entry is not the corpus payload or an open reuse grant. LDC-IL distributes datasets under separate terms. | Request the exact Garhwali sample, cost, and model-training/redistribution conditions; then hash-deduplicate an authorized export. |
| [LDC-IL Are Parallel Text Corpus](https://data.ldcil.org/are-parallel-text-corpus-linguistic-features-and-structures) | Its 2026 product page describes 5,332 sentences/phrases per language across 146 mother tongues and a fee per language component. | The page does not establish that Garhwali is part of this particular product or expose its Garhwali rows. | Confirm language coverage, price, sample, and terms before acquisition. |
| [Uniyal, 2019 English–Garhwali SMT study](https://www.pramanaresearch.org/gallery/prj-p431.pdf), and [HNBGU CV](https://www.hnbgu.ac.in/sites/default/files/2023-09/Arushi_Uniyal_CV_2023.pdf) | The paper describes 40,000 Garhwali monolingual sentences and 30,000 English–Garhwali parallel examples; the CV says 70,000 sentences were digitized. The paper names magazine OCR, Bible excerpts, and web blogs as monolingual sources. | The paper and CV describe a dataset but do not publish its payload or a reuse license. Overlap with existing magazine, web, and scripture material could be high. | Ask the researcher/university for the source files, pair alignment, source-level lineage, license, and permission; compare exact and fuzzy duplicates before any ingestion. No outreach was sent. |
| [Creative Uttarakhand publications](https://creativeuttarakhand.aipan.org/initiatives/publications/) | The catalogue identifies *Ghuguti Basuti — Bhag 2* as Garhwali children's songs and lists *Nyauli Sankalan*; digital copies are requestable. | No public full-text payload or compatible dataset license appears on the catalogue page. | Request authorized copies and explicit digitization, model-training, and redistribution terms. |
| [PahariLI](https://github.com/rachanagusain/PahariLI) | A four-language labelled classification corpus; its train/test totals cover Dogri, Garhwali, Kumaoni, and Nepali. | Its 15,000 Garhwali rows are already present in this project (`experimental/paharili_gbm.jsonl`); importing the same partition again would duplicate data. The repository declares Apache-2.0; upstream content lineage remains attached. | Keep current rows and their source split; rerun hash checks if upstream revision changes. |

The additional 2026-09-30 source sweep also rechecked the public Garhwali
dictionary and community-resource ecosystem. Hindwi exposes a dictionary but no
licensed machine-readable export; HimLingo's terms prohibit unauthorized
scraping. A community developer claims a 20,000-plus mixed Garhwali/Kumaoni
dictionary, but no downloadable data, provenance, or license is public. The
Garhwali UKC lexicon advertises only one word/synset under CC BY-NC-SA, and the
LibreOffice Weblate Garhwali project currently has no translated strings. The
Endangered Languages Project profile exposes metadata/bibliography rather than
language examples and timed out on direct fetch. None supplied net-new corpus
text; exact URLs and acquisition actions are recorded in
[`deep-search-catalog.md`](../sources/online/deep-search-catalog.md) and
[`cultural-source-leads.json`](cultural-source-leads.json).

The current search tooling did not provide an enabled Hugging Face dataset
search endpoint, so public web search and repository pages were used for
discovery. Mirrors and derivatives already inventoried in
[`deep-search-catalog.md`](../sources/online/deep-search-catalog.md) were not
counted again. A source listing, public URL, library package, or paper is not
treated as permission for data that it does not actually license or expose.

## Repeatable processing

From the repository root, run:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/refresh_corpus_after_ingestion.py
```

This command verifies the pinned Jambu snapshot offline and the four pinned
Language Library file hashes, checks source ingestion, exact-deduplicates while
preserving provenance, regenerates normalized/cleaned/quality/split/language
and benchmark views, rebuilds v0.2.1 local and public-profile package previews,
refreshes the Hugging Face reference index, updates the current README metric
block, and regenerates [`PROJECT_FILE_MAP.md`](../PROJECT_FILE_MAP.md). It
stops on the first failed stage and does not upload anything. Live web
acquisition remains a separate, explicit LangGraph intake step so a routine
refresh cannot unexpectedly recrawl sites or silently change a pinned source.

Tests verify source snapshot checksums, required fields and stable row counts,
overlap accounting, package rights filtering, and pipeline order. The full
suite and the v0.2.1 package's hash/rights preflight are recorded in the current
corpus-preparation status and source-expansion report.

## v0.2.1 publication boundary

The v0.2.1 public-profile package includes only records that pass the existing
row-level rights filter. Jambu and the MIT-labelled static Language Library
source can be represented with attribution; the new Library rows remain
marked unreviewed and experimental. Rights-unassessed blog pages, restricted
book text, machine-generated forms, and noncommercial-only sources remain out
of public full-text tables. No old release or source rows are deleted. The
initial payload remains at the original Hub storage path `releases/v2.0.0/`;
the complete current project release is v0.2.1.
