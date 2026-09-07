# Garhwali corpus: first ingestion

Run `python3 scripts/ingest_open.py` from the project root. Standard-library Python and curl are sufficient. Raw responses and acquisition metadata live in `sources/web/`; subsequent runs verify their checksums and reuse them. Each importer replaces only its own JSONL file atomically, so repeated runs do not append duplicates or overwrite other sources.

## Current files

- `asjp.jsonl`: vocabulary forms in ASJP transcription, with English concept glosses. CC BY 4.0.
- `tatoeba.jsonl`: contributed sentences with contributor identifiers and sentence URLs. CC BY 2.0 FR; pending native review.
- `wikimedia.jsonl`: original revision wikitext, including markup, from the Garhwali Wikipedia test. CC BY-SA 4.0; pending markup extraction and language review.
- `ingestion-report.json`: actual counts, duplicate-text counts and download failures from the latest run.

These are openly licensed source records, not public-domain text or a validated model-training release. Every record retains its exact license, attribution, source checksum, retrieval time and raw-file path. The same normalized text may have multiple source records; shared text hashes identify overlap without discarding distinct attribution or licensing. Native-review status remains false until a speaker reviews the content.

Preserve these per-source licenses when redistributing. Wikimedia history URLs identify contributor attribution. ASJP attribution names its compiler, bibliographic source and database editors. Tatoeba attribution includes the contributor and sentence history link.

The earlier research inventory estimated ASJP at 40 items. Actual extraction yielded 91 concept records; use the ingestion report for current quantities. Wikimedia counts exclude redirects and count substantive source records rather than all discovered pages; individual pages can still contain scaffolding or non-Garhwali text.

This initial importer takes a reproducible snapshot. Live refresh and PDF ingestion are not yet implemented. Add future PDF files under `sources/pdfs/`, ideally accompanied by their original download URLs.
