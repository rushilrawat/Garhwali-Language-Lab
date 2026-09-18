# Garhwali Language Lab v0.1.0

This directory preserves the compact generated evidence for release `v0.1.0`:
evaluation reports, preparation reports, ingestion summaries, visual inventory
artifacts, and the transcript-only Hugging Face card and manifest.

Row-level datasets, audio, caches, and model weights remain outside Git. The
public transcript dataset is published separately on Hugging Face. The complete
all-data package contains every collected text value with its original source,
rights, and quality metadata.

The complete transcript-only all-data package contains **257,145 rows**. Its
catalog includes all **28,755 exact-unique texts with zero redactions** and six
structured knowledge configurations containing **216 place, history, literary,
music, and university-research records**. The separate **146,482-row public
redistribution package** exposes full text for the
4,195 records with a named public rights basis and preserves catalog metadata for
the remaining 24,560. The
source audit also records 1,913 exact duplicates with both open and blocked
provenance instead of discarding either history. Source-grounded cleanup reduced
the public text review queue from 628 to 176 while preserving every original.

Run `python3 scripts/build_release_bundle.py` to rebuild `artifacts/` and its
SHA-256 index.

Run `python3 scripts/sync_release_index.py` after rebuilding both Hugging Face
profiles so the tracked release index cannot retain stale row counts.

See [`research/text-source-rights-audit-2026-09-15.md`](../../research/text-source-rights-audit-2026-09-15.md)
for the exact-duplicate rights rule, remaining source groups, and reproduction
commands.

See [`research/text-accuracy-review-2026-09-15.md`](../../research/text-accuracy-review-2026-09-15.md)
for the structured Wiktionary/Wikimedia extraction, scholarly-transcription
treatment, and exact remaining review boundary.
