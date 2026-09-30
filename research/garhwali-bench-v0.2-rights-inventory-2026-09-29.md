# GarhwaliBench v0.2 rights inventory

**Reviewed:** 2026-09-29
**Scope:** current local v0.2 draft, eight views / 14,703 view rows
**Status:** inventory of recorded evidence; not a legal opinion or publication clearance

This audit distinguishes an upstream license label from a decision that the
adapted benchmark payload may be redistributed. The builder deliberately leaves
`public_release_cleared=false` and `public_upload_allowed=false` unless the
component-level basis has been assessed for this specific export. No content was
removed or uploaded during this review.

## Inventory

| View/component | Rows | Recorded basis | Remaining distribution question |
| --- | ---: | --- | --- |
| IndicGenBench CrossSum | 699 | Upstream card declares CC BY-NC-SA 4.0 | Rows include English article text and source URLs. The card's dataset label does not itself resolve third-party article text rights; noncommercial/share-alike terms also do not support a commercial API without additional permission. |
| IndicGenBench FLORES | 2,009 | Upstream card declares CC BY-SA 4.0 | Verify attribution, adaptation, and share-alike obligations for this extracted task subset and the exported package. |
| IndicGenBench XORQA | 1,139 | Upstream card declares MIT | The card identifies several source datasets and contains source contexts. Review rights of those underlying passages and translations separately from the repository's MIT declaration. |
| VAANI ASR candidate | 112 | Source card declares CC BY 4.0 | Every row contains a local audio locator and local identifiers in the candidate manifest. Check the gated terms and speaker/recording permissions before any public audio or transcript release. |
| Recommended text train/validation/test | 10,342 | 2,077 rows have all recorded components marked `rights_assessed_compatible`; 8,265 rows have `rights_status=not_recorded` | The 2,077 are candidates for a rights-reviewed export, not already cleared benchmark records. The remaining 8,265 have license identifiers recorded, but an item-level rights assessment is absent. |
| Internal text candidate | 402 | Its 641 parent-component entries include 10 marked rights-compatible, 404 `not_recorded`, and 227 with source/component/consent review pending | These text rows mirror the recommended test view; keep the mirror explicit and avoid counting it as new examples. No internal-text row is cleared for benchmark redistribution. |
| **Total view rows** | **14,703** | **All rows currently have `public_release_cleared=false`; all have `public_upload_allowed=false`.** | **Do not publish this combined draft yet.** |

The recommended split's 2,077 compatible-status rows consist of 1,793 Open Bible
Stories records with CC BY-SA 4.0 metadata and 284 1916 Linguistic Survey of
India specimens marked Public Domain Mark 1.0. The 8,265 `not_recorded` rows are
7,931 Meta Omnilingual rows, 36 Tatoeba rows, 78 Wikimedia rows, 49
Wiktionary-English-only rows, 155 Wiktionary-Swadesh-only rows, 10 rows with
both Wiktionary source families, and 6 Incubator-WT rows. These source groups
are record-level and sum to 8,265 without double-counting.

The 402-row `internal/text` view is a second representation of the same text
examples as `text_recommended/test`. The eight-view total therefore contains
402 intentional cross-view mirrors; it is a view-row count, not a unique-example
count.

## Source evidence checked

- The [CrossSum-IN card](https://huggingface.co/datasets/google/IndicGenBench_crosssum_in)
  declares CC BY-NC-SA 4.0 and its examples carry source and target article URLs.
- The [FLORES-IN card](https://huggingface.co/datasets/google/IndicGenBench_flores_in)
  declares CC BY-SA 4.0.
- The [XORQA-IN card](https://huggingface.co/datasets/google/IndicGenBench_xorqa_in)
  declares MIT, names source datasets, and says the benchmark data should not be
  included in LLM pretraining. Its card also records that the Garhwali question
  and translated-answer annotations were produced by professional native
  annotators; that does not mean this project's adapted rows were reviewed by
  local Garhwali speakers.
- The [VAANI card](https://huggingface.co/datasets/ARTPARK-IISc/Vaani)
  declares CC BY 4.0; access is gated. The local benchmark includes references
  to audio and speaker metadata, so a dataset-card license label alone does not
  settle redistribution or privacy questions.

These cards support recording the upstream declarations. They do not establish
that every underlying article, recording, mixed-source text segment, or local
adaptation may be republished under one umbrella license.

## Release actions

1. Keep the current combined draft local and retain every source record in the
   local package.
2. Resolve the 8,265 `not_recorded` recommended-text rows against their exact
   source snapshots and source-specific terms; a repository-level license is
   not a substitute for item-level evidence.
3. Review CrossSum article text and XORQA contexts against their underlying
   publishers/source datasets. Obtain permission or publish only fields that
   have a documented basis while preserving local originals and provenance.
4. Review VAANI's accepted terms, audio consent, identifiers, and local media
   locators before preparing a public speech benchmark.
5. Only after per-component review, generate separate license-homogeneous
   exports with attribution and share-alike notices where required. Keep this
   mixed-license benchmark from being labeled under a single permissive license.
6. Freeze metric contracts and generate cards from the final component map.
   ASR corpus/per-record WER/CER is now implemented in the shared scorer; this
   does not clear rights or make old scores independent/native-validated.

## Local verification

The source JSONL inventory was read without printing example text. Counts were
reconciled directly from the draft rows and their top-level rights/provenance
metadata. The builder reports `public_upload_allowed=false`; the draft
validator passes structurally, which is separate from rights clearance. The
ASR scoring integration and exact-row manifest are verified in the project
test suite and the current benchmark schema contract.

Reproduce the machine-readable inventory with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_benchmark_v02_rights.py
```
