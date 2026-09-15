# Garhwali Language Lab v0.1.0

This directory preserves the compact generated evidence for release `v0.1.0`:
evaluation reports, preparation reports, ingestion summaries, visual inventory
artifacts, and the transcript-only Hugging Face card and manifest.

Row-level datasets, audio, caches, and model weights remain outside Git. The
public transcript dataset is published separately on Hugging Face, while the
complete local corpus retains every collected record under its original rights
and quality metadata.

The current transcript-only package contains **145,359 rows**. Its catalog
accounts for all **27,987 exact-unique texts**: 4,193 have a named public rights
basis and 23,794 retain redacted text with full source and review evidence. The
source audit also records 1,910 exact duplicates with both open and blocked
provenance instead of discarding either history.

Run `python3 scripts/build_release_bundle.py` to rebuild `artifacts/` and its
SHA-256 index.

See [`research/text-source-rights-audit-2026-09-15.md`](../../research/text-source-rights-audit-2026-09-15.md)
for the exact-duplicate rights rule, remaining source groups, and reproduction
commands.
