# Garhwali Language Lab v0.1.1

This directory contains local verification evidence and a compact bundle for
`garhwali-language-lab-v0.1.1`. The rights-filtered text-only corpus profile is
publicly downloadable from the [official GitHub release](https://github.com/rushilrawat/Garhwali-Language-Lab/releases/tag/v0.1.1)
as a compressed archive with a SHA-256 checksum. The linked Hugging Face
[Garhwali Corpus](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
and [Garhwali Speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
repositories are public. The corpus dataset pairs rights-filtered content with
metadata-reference tables covering the complete all-data archive.

The public content profile contains 146,684 rows across six named
configurations (12 config/split entries). It redacts 24,566 catalog text values
and withholds full payloads for 216 structured geography, history, literature,
music, and university-research records without a compatible public-rights
basis. The public reference tables cover all 257,807 rows in the all-data
archive, with 590 deduplicated sources and 277,637 record-to-source links; they
contain metadata and source pointers, not the protected works. Rights are
`not_recorded` at row level for 228,836 references, so those records are not
cleared for reuse. The all-data content package remains local or
access-controlled. There is no blanket dataset license; use per-record
provenance and source-specific terms.

Native-speaker review and dialect annotation are deferred. Language-quality
claims and GarhwaliBench are automated candidates, not native-validated or
gold results. The repository's MIT license applies to code only; source data
retains its own rights and attribution requirements.

The compact evidence bundle is under `artifacts/`. Release readiness refers to
the local automated package audit, not linguistic validation. The corpus was
updated in Hugging Face commit
[`a49a3f0`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2).
Local `datasets` 5.0.1 loads all nine configs. The Hub exposes all 15 splits
and 15 Parquet files, and previews/search/filter work across the configs.
Statistics work for seven configs; the Hub statistics service returns HTTP 500
for `text` and `sravaani_drafts` because it fails to histogram constant-valued
columns. Annotated tag
`v0.1.1` resolves to the reviewed release commit; the historical v0.1.0 tag
remains unchanged. Current stage and model diagnostics are in the
[project README](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/README.md).
