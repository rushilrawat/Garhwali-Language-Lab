# Garhwali corpus: first ingestion

This directory documents the project's initial openly licensed text sources; it
is not the full current corpus. The v0.2.0 release snapshot contains 29,426
exact-unique parent texts. The current public corpus release is v0.2.5 and
contains 32,072 exact-unique parent texts and 151,690 exact-unique segments,
with speech and experimental views plus separate rights-filtered exports. The
package is live on [Hugging Face](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
at payload commit [`46407fc`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/46407fcb623d7f51d3f401f5842f73209dbffc4c), with the latest root/versioned card at [`dc3308d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dc3308d4eb1d0eb619ab78071d0b34c2cbe8ac09). The 51 versioned files match their planned hashes and sizes; older release paths remain. V0.2.5 routes 1,308 core-text and 363 expansion rows with upstream held-out-source overlap to public `source_overlap` splits. All text values remain unchanged. The card declares merged schemas for `text_expansion` and `sravaani_drafts`; local validation loads all 13 affected shards. The latest Viewer check reports all capabilities enabled, all 25 splits and 25 Parquet outputs ready, and no pending or failed jobs. Row samples load from `text_expansion/train` (1,284 rows) and `sravaani_drafts/train` (104,534 rows). The 246-row `text_resources` view in v0.2.3 and the 1,647-row `text_expansion` view expose existing catalog values; v0.2.4 added attribution/history metadata. Internet Archive files acquired on 3–4 October remain local-only and are not yet part of this corpus. See the [v0.2.5 release report](../research/huggingface-corpus-v0.2.5-release-2026-10-05.md), [project overview](../README.md), and
[final review](../finalreport.md) for current counts, Hugging Face state, and
release limits. This folder's source files retain their own licenses and review
status.

Run `python3 scripts/ingest_open.py` from the project root. Standard-library Python and curl are sufficient. Raw responses and acquisition metadata live in `sources/web/`; subsequent runs verify their checksums and reuse them. Each importer replaces only its own JSONL file atomically, so repeated runs do not append duplicates or overwrite other sources.

## Current files

- `asjp.jsonl`: vocabulary forms in ASJP transcription, with English concept glosses. CC BY 4.0.
- `tatoeba.jsonl`: contributed sentences with contributor identifiers and sentence URLs. CC BY 2.0 FR; pending native review.
- `wikimedia.jsonl`: original revision wikitext, including markup, from the Garhwali Wikipedia test. CC BY-SA 4.0; pending markup extraction and language review.
- `sand_garhwali.jsonl`: 123 Garhwali numeral forms with concepts, IPA segmentation and source metadata. CC BY 4.0.
- `chan_numerals_garhwali.jsonl`: 40 source-specific Garhwali numeral variants. CC BY 4.0; Bangani rows remain excluded from this language layer.
- `mamta_southasia_examples.jsonl`: 67 Garhwali numeral phrases with English translations. CC BY 4.0.
- `ingestion-report.json`: actual counts, duplicate-text counts and download failures from the latest run.

These are openly licensed source records, not public-domain text or a validated model-training release. Every record retains its exact license, attribution, source checksum, retrieval time and raw-file path. The same normalized text may have multiple source records; shared text hashes identify overlap without discarding distinct attribution or licensing. Native-review status remains false until a speaker reviews the content.

Preserve these per-source licenses when redistributing. Wikimedia history URLs identify contributor attribution. ASJP attribution names its compiler, bibliographic source and database editors. Tatoeba attribution includes the contributor and sentence history link.

The earlier research inventory estimated ASJP at 40 items. Actual extraction yielded 91 concept records; use the ingestion report for current quantities. Wikimedia counts exclude redirects and count substantive source records rather than all discovered pages; individual pages can still contain scaffolding or non-Garhwali text.

The broader online pass is documented in [`sources/online/README.md`](../sources/online/README.md) and [`outputs/online-ingestion-2026-09-07/report.md`](../outputs/online-ingestion-2026-09-07/report.md). It adds Meta, English Wiktionary, Incubator Wiktionary, benchmark, restricted evaluation and historical OCR layers. Later work added user-supplied books, community and cultural material, research references, and structured language resources. Historical and restricted material stays distinguishable from this starter open-text layer. Existing snapshots remain content-addressed and are never silently refreshed.
