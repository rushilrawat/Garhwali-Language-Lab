# Garhwali Language Lab — final review report

**Review date:** 2026-09-23
**Reviewed package ID:** `garhwali-language-lab-v0.1.1`
**Decision:** **The rights-filtered automated public-profile candidate is release-ready.** Annotated tag `v0.1.1` identifies the reviewed release state. Native-speaker review and dialect annotation are explicitly deferred; this release must be described as an automated candidate, not a native-validated corpus or gold benchmark. No remote upload was performed.

## Project scope

Garhwali Language Lab is a provenance-preserving corpus and research pipeline for Garhwali (`gbm`). It brings together text, speech transcripts, lexicon, folklore, books, cultural and historical references, and research metadata; records source, quality, and rights evidence; and produces separate complete local and rights-filtered public profiles. The longer plan includes reviewed benchmarks, model baselines, an API, and community contribution tools. The production API, hosted service, leaderboard, and contribution platform are not implemented.

## Current measured inventory

Package row counts span overlapping configurations and are not counts of unique examples.

| Resource | Current state |
| --- | ---: |
| All-data package | 257,807 rows across 18 configurations; all 216 structured records retained |
| Public-profile package | 146,684 rows across 12 configurations; excludes 216 structured records without a compatible public-rights basis |
| Exact-unique parent texts | 28,755 |
| Prepared text segments | 114,064 |
| Public catalog text values redacted for rights | 24,566 |
| Human VAANI transcripts | 5,894 rows / 8.804 hours |
| Untranscribed VAANI source rows | 104,542; 104,534 unique audio hashes |
| SraVaani machine drafts | 104,534 rows; 34 empty, 1,083 high-risk, 98 source-label conflicts |
| Strict speaker-identified ASR comparison | 2,002 rows / 3.562 hours / 248 speakers |
| Lexicon and pronunciation candidates | 1,114; 293 with source phonetic segments |
| Derived TTS candidate pairs | 1,736 |
| Structured geography/history/literature/music/research records | 216, all present in local all-data |
| GarhwaliBench candidate | 398 automated text rows and 112 speaker-safe ASR rows |

The packages contain transcripts and metadata, not source audio. Popular-song records are metadata and source pointers, not full lyrics or translations. Segmented folktale audio remains outside the public package.

## Fixes completed in this review

- Corrected the Creative Commons classifier so NC and ND licenses cannot pass as public-use licenses.
- Standardized structured-record provenance and quality fields; every source reference resolves to a URL or capture fingerprint. Rights were not inferred from public accessibility or from a URL.
- Kept all 216 structured records in the local all-data package while filtering them from the public profile. The public export now has zero structured-rights failures; 186 records still have unassessed rights status and none is represented as rights-cleared.
- Reconciled public and all-data configuration inventories, profile-specific upload-plan targets, release index state, and package manifests.
- Recomputed benchmark artifact hashes/counts, split overlap, shard hashes, and content-derived identifiers in the release audit.
- Preserved the 7,490-row checksum-addressed recommended text-training view and set future IndicBERT/text-scaling defaults to use it.
- Added a root MIT `LICENSE` for repository code only. It does not license corpus values or override source-specific rights.
- Prepared release metadata as `garhwali-language-lab-v0.1.1`; the historical `v0.1.0` tag remains unchanged. The local annotated `v0.1.1` tag resolves to the reviewed release commit.
- Deferred native-speaker adjudication and dialect annotation from this release gate at the project owner's direction. Cards and reports identify the benchmark and language-quality results as automated candidates.

## Fresh verification required for each release commit

The latest local package build and final audit report 146,684 public rows, 257,807 all-data rows, 12 public configurations, 18 all-data configurations, zero public text-rights failures, zero structured records included without public rights evidence, and zero benchmark hash/leakage failures. Public and all-data package preflights pass. The release index validates as `release_ready_with_public_rights_filtered_export`. The current full suite passes **435 tests**. The compact bundle contains 131 files (2,582,257 bytes). See `release/v0.1.1/final-audit.json`, `release/v0.1.1-manifest.json`, and `release/v0.1.1/` for machine-readable evidence.

The all-data package is a local research artifact containing rights-pending material; it is not the public package and must remain access-controlled. The public package is a rights-filtered subset, not a claim that all collected data has redistribution rights. No Hugging Face upload or paid job was started.

Before attaching a public release, rerun the package builders, public/all-data cloud preflights, final audit, release-index validation, complete tests, compilation/shell checks, and bundle check against the exact commit referenced by `v0.1.1`. Do not move the existing v0.1.0 tag.

## Remaining limitations and follow-up

### Language quality

No native-speaker adjudications are complete, and only 29 of 28,755 parent texts have an explicit dialect label. These activities are deferred, not silently treated as completed. GarhwaliBench is an automated candidate; WER/CER and text-model results inherit the quality and coverage limits of their references. Do not call the dataset native-validated or the benchmark gold.

### Rights and access

The 216 structured records remain in all-data and are omitted from the public export until compatible source-specific reuse evidence is documented. The public catalog also redacts 24,566 text values without a compatible public-rights basis. Keep all-data private/access-controlled. A source being online does not by itself grant republication rights.

### Model evidence

Historical tokenizer, language-model, translation, retrieval, and speech results refer to their recorded input snapshots. They are not interchangeable scores on one frozen benchmark. Machine transcripts remain labeled experimental; model agreement is not human ground truth. Paid Hugging Face work is not active.

### Reproducibility

Raw downloads, scans, VAANI audio, caches, and model artifacts remain gitignored. Reproduction from a clean clone requires the separately preserved source snapshots and acquisition metadata. Back up those assets and do not commit credentials, raw audio, restricted scans, or private speaker information.

### Product roadmap

The API, billing, hosted inference/search, leaderboard, and community review platform remain future work. They should follow a frozen dataset policy, tested access controls, and stronger native-language evaluation.

## Reproduction and release checks

```bash
bash scripts/finalize_local_release.sh
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/validate_release_index.py
.venv/bin/python scripts/build_release_bundle.py --check
python3 -m compileall -q scripts tests
bash -n scripts/*.sh
git diff --check
```
