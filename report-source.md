# GarhwaliCorpus source inventory — research note

Verified: 2026-09-07

## Scope and admission rule

This review looks for Garhwali text and speech that can support a publishable, provenance-rich corpus. A public webpage is not treated as reusable merely because it is accessible. Every admitted record needs a traceable open license, a defensible public-domain memo, or written permission. License-constrained material is separated into compatible layers rather than covered by one blanket corpus license.

## Bottom line

The best immediately usable sources are [Meta's Omnilingual ASR Corpus](https://huggingface.co/datasets/facebook/omnilingual-asr-corpus), [Project Vaani](https://vaani.iisc.ac.in/), the [ASJP Garhwali list](https://asjp.clld.org/languages/GARHWALI), the public-domain Garhwali section of the [Linguistic Survey of India](https://commons.wikimedia.org/wiki/File:Linguistic_Survey_of_India_Vol_9_Part_4.djvu), and small Wikimedia/Tatoeba slices. Together they support an initial corpus with modern speech, historical text, basic vocabulary and a small amount of contemporary community text.

The largest tempting text datasets are not automatically safe. PahariLI contains 15,000 Garhwali sentences, but its paper describes underlying blogs and a translated New Testament; an Apache repository license does not by itself sublicense those works. MADLAD-400's ODC-BY license covers database rights, while source-page copyrights can remain. Both belong in a quarantine/reference layer until source-level rights are verified.

The most valuable partnership lead is [HimLingo](https://himlingo.com/), which reports 4,206 words across 13 dialects. Its [terms](https://himlingo.com/terms-of-services/) prohibit scraping without permission and say contributors retain ownership, so the correct path is a separately licensed export plus a contributor-sublicense audit.

## Evidence reconciliation

- Meta's official `gbm_Deva` dataset configuration reports 2,927 utterances. A community `indic-dialect-asr` mirror reports 7,823 Garhwali rows and samples cite the Meta corpus, but the additions and transformations are undocumented. The inventory therefore selects the upstream Meta source and excludes the mirror unless its provenance is clarified.
- Vaani reports 136.80 recorded Garhwali hours, while its explicitly transcribed Garhwali subset is 8.80 hours. These are not contradictory: the larger figure is collected audio and the smaller figure is the released transcription subset.
- Tatoeba's current detailed Garhwali export contains 36 sentences. The license is usable, but the tiny set needs complete native-speaker review before training or evaluation use.
- The Wikimedia Incubator counts were reproduced through the public API: 37 Garhwali Wikipedia-test pages and 4 Wiktionary-test pages. Raw wikitext counts include templates/navigation and therefore overstate clean linguistic yield.
- `Proverbs & Folklore of Kumaun and Garhwal` is a high-yield 1894 scan, but it mixes Kumauni and Garhwali. The US public-domain case is straightforward for a pre-1931 publication; an India distribution memo should still confirm author-death evidence under [Section 22](https://copyright.gov.in/Copyright_Act_1957/chapter_v.html).
- `Himalayan Folklore` is public domain in India but likely remains protected in the United States through 2031 because of copyright restoration. It is also mostly English translation, so it is classified as a reference rather than a current Garhwali core source.

## Recommended build sequence

1. Ingest the two modern open speech sources from their upstream publishers, preserving speaker, prompt, district, split and attribution metadata.
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
