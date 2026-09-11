# GarhwaliCorpus source inventory — research note

Verified through: 2026-09-09

## Scope and admission rule

This review looks for Garhwali text and speech that can support a publishable, provenance-rich corpus. A public webpage is not treated as reusable merely because it is accessible. Every admitted record needs a traceable open license, a defensible public-domain memo, or written permission. License-constrained material is separated into compatible layers rather than covered by one blanket corpus license.

## Bottom line

The immediately usable open sources are [Meta's Omnilingual ASR Corpus](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus), the 91-entry [ASJP Garhwali list](https://asjp.clld.org/languages/GARHWALI), the public-domain Garhwali section of the [Linguistic Survey of India](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu), the 25-page Garhwali section of Upreti's 1900 [Hill Dialects](https://books.google.com/books?id=veUTAAAAYAAJ), the 181 exact-unique [OPUS translatewiki](https://opus.nlpl.eu/translatewiki/) messages, and small Wikimedia/Tatoeba slices. [Project Vaani](https://vaani.iisc.ac.in/) is the strongest modern expansion source: the provider now clearly states CC BY 4.0, while Hugging Face file access still requires the project owner to accept the contact-sharing conditions. Together these support an initial provenance-rich corpus with modern speech, historical text, basic vocabulary and localization text.

The largest text datasets have mixed source terms. PahariLI contains 15,000 Garhwali sentences, while its paper describes underlying blogs and a translated New Testament. MADLAD-400's ODC-BY license covers database rights while source-page copyrights can remain. Its clean `gbm` split has 137 documents; 119 exactly match the existing DCAD extract, so 18 novel documents were added to the active experimental layer. Both families retain source-level rights flags while remaining usable in local experiments.

The most valuable partnership lead is [HimLingo](https://himlingo.com/), which reports 4,206 words across 13 dialects. Its [terms](https://himlingo.com/terms-of-services/) prohibit scraping without permission and say contributors retain ownership, so the correct path is a separately licensed export plus a contributor-sublicense audit.

## Evidence reconciliation

- Meta's official `gbm_Deva` dataset configuration reports 2,927 utterances. A pinned revision of the community `indic-dialect-asr` mirror was range-read without downloading audio and yielded 7,823 rows: 1,930 rows cite Meta and 5,893 cite Vaani. Exact normalized-text comparison found 1,903 unique texts overlapping Meta; these rows remain active in local experiments with component-lineage, consent, and duplication flags.
- A pinned row-level audit of Vaani's official `Garhwali` configuration found 110,410 recordings whose current `duration` values sum to 135.473036 hours; the dataset card still reports 136.80 hours. The main repository contains 5,868 transcript-bearing WAVs (8.766993 hours). The separate transcription repository has 5,894 rows split 4,778/666/450: all 5,868 main transcript WAVs plus 26 WAVs absent from the current main config. The community ASR mirror has 5,893 Vaani-labeled rows and still requires a separate filename-level comparison.
- Tatoeba's current detailed Garhwali export contains 36 sentences. The license is usable, but the tiny set needs complete native-speaker review before training or evaluation use.
- The Wikimedia Incubator counts were reproduced through the public API: 37 Garhwali Wikipedia-test pages and 4 Wiktionary-test pages. Raw wikitext counts include templates/navigation and therefore overstate clean linguistic yield.
- OPUS's public translatewiki snapshot contained 241 Garhwali mono lines and 200 aligned English–Garhwali pairs. Sixty repeated mono lines were removed, leaving 181 unique messages; the source terms state CC BY 3.0.
- The current cross-layer snapshot contains 32,967 records and 30,913 exact unique normalized texts. The latest waves added 123 SAND numeral forms, 40 Chan variants, 67 translated numeral examples, 50 restricted Garhwali Open Bible Stories, 185 structured historical LSI forms, 34 Kellogg pages, two Walton language-description pages, 156 targeted UOU MAHL OCR pages, 317 public-domain Garhwal cultural-reference records, and 666 source-level thematic vocabulary records representing 642 distinct normalized written forms. The full pairwise overlap and duplicate-row accounting is in the [deduplication report](outputs/online-ingestion-2026-09-07/dedup-report.json), the [deep-search catalog](sources/online/deep-search-catalog.md), and the [third-pass source audit](sources/online/source-audit-2026-09-08.md).
- The [thematic lexicon](research/garhwali-thematic-lexicon.json) covers animals, birds, insects, instruments, occupations, natural features, food, household objects and regional cultural terminology. Entries preserve variants and disagreements, and remain review-gated because several community sources do not state reusable-content terms.
- The cultural-media register contains 754 unique Wikimedia Commons items with item-level attribution and licenses. The [cultural ingestion report](research/cultural-ingestion-report.md) documents coverage, cultural genres, excluded copyrighted works, and permission targets.
- Five directly relevant scholarly works now have a rights-audited research manifest. Four full PDFs were acquired; Heidelberg's CC BY-SA chapter remains metadata-only because its server returned an Anubis JavaScript challenge. No paper prose entered the language corpus. The [scholarly guide](research/garhwali-scholarly-guide.md) translates the findings into annotation, evaluation, OCR, dialect and code-switching requirements.
- `Proverbs & Folklore of Kumaun and Garhwal` is a high-yield 1894 scan, but it mixes Kumauni and Garhwali. The US public-domain case is straightforward for a pre-1931 publication; an India distribution memo should still confirm author-death evidence under [Section 22](https://copyright.gov.in/Copyright_Act_1957/chapter_v.html).
- `Himalayan Folklore` is public domain in India but likely remains protected in the United States through 2031 because of copyright restoration. It is also mostly English translation, so it is classified as a reference rather than a current Garhwali core source.

## Recommended build sequence

1. Keep Meta's open speech source as the current speech baseline; retain the acquired CC BY 4.0 Vaani manifests and resolve the 1.326964-hour card-versus-row duration discrepancy before promotion.
2. Add ASJP and Wikimedia lexical material, deduplicating concepts while keeping source-specific forms.
3. OCR the LSI Garhwali pages with page-level provenance and a `historical=true` flag; retain both original transliteration and a separately reviewed Devanagari normalization.
4. Native-review all Tatoeba sentences and Incubator pages before promotion from raw to reviewed.
5. Complete the 1894 proverb-book rights memo, then segment Kumauni and Garhwali by page and entry.
6. Run permission outreach in parallel for HimLingo, Hindwi, the TUFS idiom collection, early periodical archives and the Garhwali New Testament rights holder.

## Rights framework

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) material can be shared and adapted, including commercially, with attribution, a license link and change notice. [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) material should remain in a separate share-alike-compatible layer. ODC-BY sources require an additional document-level copyright check. Indian literary works generally use life plus 60 years under Section 22, while government works have a separate term under Section 28; a `.gov.in` host is not automatically public domain.

## Unresolved items

- Locate authoritative scans and bibliographic records for `Sadei` and `Garhwali Kavitavali`.
- Confirm the 1894 proverb compiler's death date and the intended release jurisdictions.
- Obtain provenance and content-license statements for PahariLI before any redistribution.
- Audit speaker consent and demographic balance in each open speech source before release.
- Confirm whether BhashaDaan offers a current Garhwali export; its CC0 contribution terms make it promising as a future collection channel, not a verified current source.
- Preserve the rights and consent flags for the 5,893 Vaani-derived aggregation rows and 15,000 PahariLI sentences in every derived model and release manifest.
- Reconcile the mirror's 5,893 Vaani rows against the acquired official 5,894-row transcription manifest by WAV filename.
