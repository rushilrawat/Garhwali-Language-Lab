# Garhwali-only data expansion for v0.2.0

**Checked:** 2026-09-29
**Goal:** add source-traceable Garhwali language material, count exact novelty, and separate readable text from noisy OCR and acquisition-only leads.

## Intake result

The four ingested sources produced **696 text-bearing source rows** and **180,043 characters**. They contain **673 exact-unique strings within this intake**; **671 are exact-new against the existing source layers** and two were already present. No row failed the `iso_639_3=gbm` and `language=Garhwali` check. The generated machine-readable audit is `data/extracted/expansion_audit/v0.2.0.json` (ignored, reproducible with `scripts/audit_garhwali_expansion.py`).

| Workstream | Intake | Exact novelty and quality |
| --- | ---: | --- |
| LSI dialect table | 632 rows, 609 within-source unique strings, 8,663 characters | Standard, Rathi, and Tehri; all marked historical OCR/unreviewed; 496 rows have OCR confidence below 60. The 632 source rows yield 609 unique strings. |
| LSI narrative specimens | 9 records, 23,532 characters | Srinagar (2), Tehri (2), Lohbya, Badhani, Dasaulya, Nagpuriya, and Salani. The five new dialect examples are kept as explicitly labeled Garhwali; text is OCR-derived, not corrected or native-reviewed. |
| Upreti 1894 proverbs | 5 records, 171 characters | Only sayings whose printed context explicitly identifies them as Garhwali; historical Latin forms and source glosses are preserved separately. |
| Door43/TLF Garhwali Open Bible Stories | 50 records, 147,677 characters | Pinned v1 archive at revision `f08afc73e1770129fbcd3089181f2faf2abbf54d`, manifest/license checked as CC BY-SA 4.0; story translation quality is unreviewed. |
| Source expansion and reconciliation | Existing ASJP, Tatoeba, Wikimedia, OPUS, and PahariLI sources rechecked against the source catalog | Existing data/mirrors were not counted again. CIIL lists a Garhwali parallel-text corpus; no Garhwali file or usable license/price terms were verified from the accessible public page, so it remains an acquisition lead, not ingested text. |

## Rights and release treatment

The new material is not a single quality class. Door43 contributes 50 versioned CC BY-SA 4.0 stories. The historical LSI and Upreti rows carry source-specific public-domain evidence, attribution, and page references. Those rights findings apply only to those cited editions. The LSI text has not been corrected; 496 of the 632 lexical-table rows are below the local OCR-confidence threshold, and all nine narrative records are marked unreviewed. Preserve these labels in every export and do not describe the OCR as native-verified or model-ready.

The seven user-supplied PDFs remain in their existing local/experimental layer with the source-specific rights and OCR notices recorded in the PDF ingestion report. They are not part of this rights-cleared expansion intake.

## Reproduction

```sh
PYTHONPATH=scripts python scripts/ingest_obs_tlf.py
PYTHONPATH=scripts python scripts/ingest_upreti_1894_garhwali.py
PYTHONPATH=scripts python scripts/ingest_lsi_garhwali_table.py
PYTHONPATH=scripts python scripts/ingest_lsi_garhwali_specimens.py
PYTHONPATH=scripts python scripts/audit_garhwali_expansion.py
PYTHONPATH=scripts python scripts/prepare_text_corpus.py
```

The generated JSONL files and audit report live below ignored `data/extracted/`. The ingestion recipes, tests, source metadata, and this summary are tracked. The complete preparation pipeline invokes the ingesters before corpus construction.

## Limits of this pass

- The large LDC-IL Garhwali parallel corpus is not publicly downloadable from the verified product listing. Request the Garhwali component and its redistribution terms from CIIL before acquisition; do not infer rights from the listing.
- Previously ingested ASJP/Tatoeba/Wikimedia/OPUS/PahariLI material is not a new-data count. Repository mirrors do not create independent language evidence.
- No manual/native corrections were made. The current net gain is 671 exact-new strings, not 671 validated vocabulary items; unique strings include short historical forms and full translated stories, whose uses differ.
