# Garhwali Language Lab v0.1.1

This directory contains local verification evidence and a compact bundle for
`garhwali-language-lab-v0.1.1`. The rights-filtered text-only corpus profile is
now publicly downloadable from the [official GitHub release](https://github.com/rushilrawat/Garhwali-Language-Lab/releases/tag/v0.1.1)
as a compressed archive with a SHA-256 checksum. It is not uploaded as a
Hugging Face dataset. The companion speech repository is public; the text
repository remains owner-private.

The rights-filtered public profile contains 146,684 rows across six named
configurations (12 config/split entries). It redacts 24,566 catalog text values
whose source terms do not permit redistribution. It excludes 216 structured
geography, history, literature, music, and university-research records without compatible public-rights
evidence. All 216 remain in the 257,807-row local all-data package, which has 12
named configurations (18 config/split entries). The
all-data package contains rights-pending source material and must remain
private or access-controlled. This profile has no blanket dataset license; use
the per-record provenance and source-specific terms included in the archive.

Native-speaker review and dialect annotation are deferred. Language-quality
claims and GarhwaliBench are automated candidates, not native-validated or
gold results. The repository's MIT license applies to code only; source data
retains its own rights and attribution requirements.

The compact evidence bundle is under `artifacts/`. Release readiness refers to
the local automated package audit, not public publication or linguistic
validation. Annotated tag `v0.1.1` resolves to the reviewed release commit; the
historical v0.1.0 tag remains unchanged. Current stage and model diagnostics are
in the [project README](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/README.md).
