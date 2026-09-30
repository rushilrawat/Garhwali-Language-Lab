# Garhwali Language Lab — final review report

## Current release status — v0.2.0 (2026-09-29)

The v0.2.0 package has been rebuilt locally and is **release-ready for the
rights-filtered public profile**. Hugging Face is updated at verified commit
[`cb631488`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cb6314880b8a28c3bf3dcc025d8ff9ebe062c927), and GitHub published the matching [v0.2.0 release](https://github.com/rushilrawat/Garhwali-Language-Lab/releases/tag/v0.2.0) from commit `e2fdf5b`.

### New Garhwali-only material

The four source intakes contribute 696 source rows and 180,043 characters.
Exact deduplication finds 673 values unique within the new intake and **671
net-new exact-unique texts** against the existing corpus. The intake is 632
LSI dialect-table rows (609 unique forms), nine LSI language specimens, five
Upreti (1894) sayings explicitly marked Garhwali, and 50 pinned Door43/TLF
Garhwali Open Bible Stories. The 50 story texts are CC BY-SA 4.0; the historical
LSI/Upreti extracts carry source-specific Public Domain Mark evidence. All rows
retain citations, checksums or page/revision locations, rights, and quality
status. 496 LSI table rows have OCR confidence below 60/100; all OCR and the
story translation remain unreviewed.

The canonical inventory now contains **31,790 source records from 46 files**,
**29,426 exact-unique parent texts**, and **9,325,936 characters**. The sentence
view has **122,391 occurrences / 115,785 exact-unique segments**. Counts are
not claims of 29,426 validated Garhwali lexical items: the corpus includes
historical forms, OCR excerpts, translated narratives, speech, and experimental
material with distinct quality labels.

### Package and checks

| v0.2.0 profile | Current result |
| --- | ---: |
| Complete local/access-controlled package | 260,199 rows across overlapping views; all collected text values retained |
| Rights-filtered public package | 150,065 rows across overlapping views |
| Public metadata-only reference index | 260,199 archive references; 600 sources; 283,752 record-to-source links |
| Public catalog values redacted for reuse rights | 24,565 |
| Structured records withheld from public content | 216 |
| Exact-new Garhwali-only texts in this intake | 671 |
| v0.2.0 release-time pytest | 607/607 passed |
| v0.2.0 release-time unittest | 605/605 passed |

Final release audit, public and all-data preflights, release-index validation,
and the compact bundle check pass. The uploaded Hub package has 34/34 file sizes
and hashes matching the release plan; the Hub lists all 15 split Parquet
conversions. All 15 split validity checks now return HTTP 200 with Viewer and
preview enabled, and a text sample preview loads. The audit reports zero public-rights
failures, zero hash failures, zero deleted/mutated rows, and zero configured
text/audio/speaker split overlap; it retains one XORQA upstream train/dev exact
repeat warning. The public profile is not the complete unrestricted archive:
24,565 catalog payloads and 216 structured records without compatible public
rights evidence remain out of public content tables. Their values remain in the
local/access-controlled all-data package. No blanket corpus license is claimed.

The source expansion and v0.2.0 process do not change benchmark status: native
language adjudication and dialect review remain deferred, and new OCR/story
material is not a native-validated benchmark. The GitHub v0.2.0 tag/release
is published. Detailed intake:
[`research/garhwali-data-expansion-2026-09-29.md`](research/garhwali-data-expansion-2026-09-29.md).

---

## Benchmark and research suite — current status (2026-09-29)

The public v0.2.0 **corpus** release is distinct from GarhwaliBench. The
benchmark remains a local draft, not a complete public benchmark or a validated
model. Its current adapter has eight views and **14,703 view rows** (3,847
external task rows, 112 ASR rows, 402 internal text rows, and recommended text
splits of 9,486/454/402). The internal-text and recommended-test views mirror
the same 402 examples, so the total is not a unique-example count. The adapter
manifest is SHA-256
`43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8` and the
contract validator reports zero errors. `public_upload_allowed=false` remains
set. The rights inventory finds 2,077 recommended-text rows with compatible
recorded source assessments, 8,265 with item-level rights status unrecorded,
and unresolved component review for external tasks and audio. No v0.2 row is
cleared for publication by the adapter.

The 402-row text test was aggregate-scored by the add-one character-bigram
baseline at perplexity 14.397995. The refreshed lineage audit verifies the
current IDs, normalized text, input hashes, and row-set fingerprint, and labels
the set historical/open. The exact overlap scan finds one source-split exact
text repeat (the known XORQA train/dev repeat), 402 intentional text cross-view
mirrors, and four same-split near-text candidates. Source-family grouping marks
29 cross-split families, including two broad URL groups that are not proof of
record duplication. All 10,342 recommended text IDs map to source segments
covering 3,246 parent-text hashes and 3,072 duplicate components with zero
split crossings; nine of 11 coarse ingestion-file pointers span splits, but
those point to multi-work collections and are not document identities. A
138-row XORQA diagnostic overlay remains; no rows were deleted. The shared
scorer now includes corpus and per-record ASR WER/CER; its validation-only
integration check reproduced the saved 269-row SraVaani aggregate exactly.
Semantic/paraphrase overlap and model pretraining exposure are not resolved.
Independent-final eligibility is **0/5**; model scores remain
historical or development diagnostics. Native-speaker review and dialect
annotation remain deferred at the owner's direction. The six candidate task
cards remain local-only pending rights clearance; their aggregate status is
documented in the [rights inventory](research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md).

The six workstreams were advanced in order: overlap/split refresh; v0.2
contract rebuild and validation; aggregate score-lineage correction; review of
existing uncertainty and failure analysis; six local draft task cards and
eligibility reconciliation; and a versioned maintenance procedure. Fresh
NLLB, dense-retrieval, and SraVaani inference still require local model/runtime
assets. This refresh ran no model inference, paid job, download, or upload.

Next gates are source/component rights and provenance review, unresolved
semantic/exposure checks, final metric and denominator contracts, missing run
manifests, and a genuinely fresh independent evaluation set. Public benchmark
payload publication is not authorized by the current draft. Detailed evidence
is in the [roadmap](research/benchmark-model-roadmap.md), [measured status](research/benchmark-research-status-2026-09-25.md), [draft schema contract](research/garhwali-bench-v0.2-schema-contract.md), [rights inventory](research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md), and [issue log](research/issues%26improvement%20plan.md). The six-card review pack remains local-only and is not linked for public download.

**Verification for this review:** `pytest -q` passed **622 tests** and
`python -m unittest discover -s tests -q` passed **620 tests**. These verify
code and automated data contracts; they do not certify Garhwali correctness,
rights, or independent model accuracy.

## Historical v0.1.1 review (2026-09-28)

**Review date:** 2026-09-28
**Reviewed package ID:** `garhwali-language-lab-v0.1.1`
**Decision:** **The public Hugging Face corpus now pairs a rights-filtered content profile with a complete metadata-reference index of the all-data archive.** Its reference tables cover every one of the 257,807 all-data rows; they do not contain the protected source text or media. The content profile still redacts 24,566 catalog values and omits the full payload of 216 structured records with unresolved reuse rights. Native-speaker review and dialect annotation are deferred, so the release is an automated candidate, not a native-validated corpus or gold benchmark.

## Project scope

Garhwali Language Lab is a provenance-preserving corpus and research pipeline for Garhwali (`gbm`). It brings together text, speech transcripts, lexicon, folklore, books, cultural and historical references, and research metadata; records source, quality, and rights evidence; and produces separate complete local and rights-filtered public profiles. The longer plan includes reviewed benchmarks, model baselines, an API, and community contribution tools. The production API, hosted service, leaderboard, and contribution platform are not implemented.

## v0.1.1 measured inventory (2026-09-28 snapshot)

Package row counts span overlapping configurations and are not counts of unique examples.

| Resource | Current state |
| --- | ---: |
| All-data package | 257,807 rows across 18 configurations; all 216 structured records retained |
| Public content profile | 146,684 rows across 12 config/split entries; 24,566 catalog values redacted and full content omitted for 216 rights-unresolved structured records |
| Public complete reference index | 257,807 archive-row references; 590 deduplicated sources; 277,637 record-to-source links |
| Reference rows with corresponding public content value | 122,118; reference rows are not additional training examples |
| Reference rows with no record-level rights status | 228,836; `not_recorded` is not reuse permission |
| Exact-unique parent texts | 28,755 |
| Prepared text segments | 114,064 |
| Public catalog text values redacted for rights | 24,566 |
| Human VAANI transcripts | 5,894 rows / 8.804 hours |
| Untranscribed VAANI source rows | 104,542; 104,534 unique audio hashes |
| Hugging Face speech status | 113,363 rows across public VAANI and Meta Omnilingual configs; 154.646 hours / 16.91 GiB source audio |
| SraVaani machine drafts | 104,534 rows; 34 empty, 1,083 high-risk, 98 source-label conflicts |
| Strict speaker-identified ASR comparison | 2,002 rows / 3.562 hours / 248 speakers |
| Lexicon and pronunciation candidates | 1,114; 293 with source phonetic segments |
| Derived TTS candidate pairs | 1,736 |
| Structured geography/history/literature/music/research records | 216; full payload remains local, names/titles and source metadata are in the public reference index |
| GarhwaliBench candidate | 3,847 external task records, 398 automated text rows, 112 speaker-safe ASR rows; one XORQA train/dev repeat flagged |

The text packages contain transcripts and metadata, not source audio. The separate Hugging Face speech package now contains VAANI and Meta Omnilingual audio in separate configs. Popular-song records are metadata and source pointers, not full lyrics or translations. Segmented folktale audio remains outside the public package.

## v0.1.1 release review — historical details

- Corrected the Creative Commons classifier so NC and ND licenses cannot pass as public-use licenses.
- Standardized structured-record provenance and quality fields; every source reference resolves to a URL or capture fingerprint. Rights were not inferred from public accessibility or from a URL.
- Kept the full content for all 216 structured records in local all-data and represented every record in the public metadata index. A source-specific web review records findings for the 186 previously unassessed geography, history, literature, and university records. Some cited sources have reuse terms, but no compatible whole-record basis was established for those mixed-source records; none was represented as rights-cleared.
- Reconciled public and all-data configuration inventories, profile-specific upload-plan targets, release index state, and package manifests.
- Recomputed benchmark artifact hashes/counts, split overlap, shard hashes, and content-derived identifiers in the release audit.
- Preserved the 7,490-row checksum-addressed recommended text-training view and set future IndicBERT/text-scaling defaults to use it.
- Added a root MIT `LICENSE` for repository code only. It does not license corpus values or override source-specific rights.
- Prepared release metadata as `garhwali-language-lab-v0.1.1`; the historical `v0.1.0` tag remains unchanged. The local annotated `v0.1.1` tag resolves to the reviewed release commit.
- Deferred native-speaker adjudication and dialect annotation from this release gate at the project owner's direction. Cards and reports identify the benchmark and language-quality results as automated candidates.
- Added and published the Meta Omnilingual speech config: 2,927 recordings / 19.136 hours, with exact audio and transcript overlap checks against VAANI. The new 50-shard upload is verified against local hashes in Hub commit `914eb221b6f58f88d85a8d5dd826acac827ee1c4`.
- Corrected the GarhwaliBench character-bigram default to use the 7,490-row recommended training split instead of the broad 106,915-row split. On the same 398-row candidate, perplexity is 14.122106 versus 17.000058 for the broad-view control; the training manifest hash is recorded in the benchmark and release index.
- Added exact primary-text, nested-field, cross-language-label, and source-page overlap audits across benchmark splits. The nested scan found 41 same-field long cross-split groups and zero long exact matches with recommended training text. A supplemental label-agnostic check found 50 short exact strings across English/Garhwali XORQA answer fields, with 10 spanning splits; all are 2–6 normalized characters and remain candidates, not confirmed leakage. A page-title check found 54 cross-split page families (134 rows), including 32 families with distinct context passages. The refreshed review-only usage overlay labels 138 retained records; repeated answer spans remain candidates. See the [nested-overlap review](research/benchmark-nested-overlap-review-2026-09-27.md), [cross-language exact-overlap review](research/benchmark-cross-language-exact-overlap-2026-09-28.md), and [source-page family review](research/benchmark-source-page-families-2026-09-28.md).
- Built the v0.2 local draft adapter for all eight views / 12,622 rows. It retains every legacy row, links the refreshed 67-row XORQA usage overlay, records separate raw/source/scoring values where available, and verifies export hashes/counts. Its output is ignored and local-only. QA exact-match/token-F1, summary ROUGE-L/chrF, and custom translation BLEU/chrF now have versioned scoring paths; translation and retrieval diagnostics include paired run manifests. The overall v0.2 contract remains a draft, with semantic/cross-language overlap, source-cluster uncertainty, and release eligibility open.
- Corrected a text split leak missed by the earlier exact-segment audit: 50 parent documents / 1,523 segments crossed historical splits. The builder now groups parent segments before duplicate reassignment and records source input hashes. A separate local candidate reports zero parent-document crossings and retains every segment; it has not replaced the v0.1.1 package. Its deterministic character-bigram diagnostic on already-scored open-test rows was not used for model selection. See the [parent-safe split audit](research/benchmark-parent-safe-split-audit-2026-09-28.md).
- Tightened the final audit to verify the recommended training manifest and recompute external benchmark overlap. It passes with six checked artifacts, zero artifact failures, zero measured internal train/evaluation overlap, and one explicit XORQA source-split warning.
- Fixed lineage-report regeneration so its row-level JSON ledger is explicitly documented as local-only because it contains VAANI speaker identifiers.
- Added a shared hash-linked run manifest to post-hoc SraVaani/Whisper validation scoring. It reproduces the existing 269-row validation metrics exactly and does not run inference or score held-out rows; details are in [the ASR manifest report](research/asr-validation-run-manifest-2026-09-27.md).
- Reconciled five saved SraVaani held-out runs against the same 112 audio hashes and cleaned references. The paired speaker-cluster WER/CER intervals all include zero or touch it; no fine-tune is supported as better by this already-scored test. No inference ran. See [the held-out lineage audit](research/asr-heldout-lineage-audit-2026-09-28.md).
- Traced the older 269-row SraVaani validation comparator to its saved 381-row prediction artifact; the selected validation rows reproduce 2,161 word and 3,282 character errors and match the manifested comparison row-for-row. The later greedy-sweep aggregate differs by 3 word / 4 character errors; its per-row output was not saved, so that small discrepancy remains open and both runs stay distinct.
- Added per-seed manifests for the three saved mT0 generation runs. All 390 prediction rows reconcile to 130 matching validation IDs per seed; the selected-ID digest matches the recorded model validation hash. Primary-reference diagnostics reproduce the saved report; current unreviewed alternate references raise chrF2 by 0.0019–0.0025, a sensitivity finding rather than an accuracy gain. No inference or test scoring ran. The original sampling parameters and per-seed adapter hashes are absent; details are in [the mT0 manifest report](research/mt0-validation-run-manifest-2026-09-27.md).
- Reconciled Phase 8 result eligibility. The lineage audit now labels test sets with saved predictions as historical-only and marks the exact 398-row text candidate historical because an aggregate baseline already scored it. CrossSum and Meta Omnilingual test exposure remains unresolved; no task is independent-final-eligible. See the [eligibility report](research/task-result-eligibility-2026-09-28.md) and [fresh lineage audit](research/model-accuracy-lineage-2026-09-28.md).

## Fresh verification required for each release commit

The refreshed local package audit reports 146,684 public content rows, 257,807 all-data rows, and a reference index with 257,807 archive-row entries, 590 sources, and 277,637 joins. The rights-filtered content audit reports zero rights failures; unresolved payloads remain out of those content tables. The v0.1.1 benchmark audit checks six artifacts and finds zero exact text/audio/speaker overlap; it separately warns about the single XORQA train/dev duplicate. A later parent-hash audit found 50 parent documents / 1,523 segments crossing splits in the historical text manifests; the corrected local candidate reports zero parent crossings and is not included in v0.1.1. Phase 2 verified 27 exact XORQA source-context groups and 54 exact source-page families across splits, spanning 134 rows; 32 page families contain distinct passages. The retained-row overlay labels 138 records open-diagnostic-only for independent source-generalization claims, and every row remains present. A nested-field audit found 41 same-field cross-split groups (27 contexts, 6 English answer spans, 5 English oracle questions, 2 Garhwali translated-answer spans, and 1 Garhwali question), zero same-label cross-field long groups, zero long cross-language-label groups, and zero long exact matches to recommended training text. A supplemental scan found 50 short exact English/Garhwali answer strings, 10 across splits (all 2–6 normalized characters); these remain candidates, not confirmed leakage. Repeated answer-span matches remain documented candidates and are not automatic leakage findings. Semantic and cross-language comparison remain open. Four same-split near-text pairs were reviewed and are documented in the benchmark adjudication report. The v0.2 validator passes its eight source views, and a deterministic adapter builds all eight views / 12,622 rows with zero dropped records. QA exact-match/token-F1, CrossSum ROUGE-L/chrF, and translation BLEU/chrF have tested, versioned scoring paths. Existing 997-row translation-memory dev predictions reproduce the saved custom baseline metrics exactly; a 2,000-resample paired record bootstrap estimates positive dev deltas over source-copy (BLEU +0.01892665, 95% CI [0.01411908, 0.02385223]; chrF2 +0.23002697, CI [0.22559907, 0.23435906]). This is a same-dev retrieval diagnostic, not independent language accuracy, and it lacks source-cluster resampling. A new ASR run manifest reconciles 269 validation audio hashes and reproduces the prior SraVaani/Whisper metrics exactly. Three mT0 seed manifests likewise reconcile 390 saved rows to the frozen 130-row validation selection and its recorded selected-ID hash; primary-reference metrics reproduce the saved report, while unreviewed alternate references shift chrF2 by +0.0019–0.0025 as reference sensitivity, not a quality gain. These were post-hoc audits; the parent-safe benchmark build also recomputed a deterministic character-bigram diagnostic on the already-scored 392-row open text test (perplexity 14.123460). It was not used for model selection, and no neural inference ran. The mT0 adapter hashes and original sampling parameters are unavailable. The CrossSum/XORQA scorer keeps the one XORQA dev row without a non-empty Garhwali reference in the output while excluding it from scores; preflight found 100/100 CrossSum and 499/500 XORQA dev references. No fresh neural-model scores were generated. The overall metric contract remains draft, and the export is local-only. Public and all-data package preflights pass. The release index validates as `release_ready_with_public_rights_filtered_export`. Phase 4 includes translation, NLLB, CrossSum/XORQA, BM25 retrieval, and post-hoc ASR and generation manifests; the 500-query retrieval dev run reconciles IDs and output hashes; a follow-up miss analysis confirms all 500 gold passages are in the fixed corpus, with 496 word-BM25 zero-score misses and 493 character-BM25 zero-score misses plus two ranked below 10 ([report](research/retrieval-miss-analysis-2026-09-28.md)). A validation-only mT0 output audit found no empty, prompt-copy, control-token, or selected Unicode-anomaly outputs, but flags repeated-answer concentration up to 23/29 in the Garhwali-to-English lexicon slice; this is a diagnostic signal, not a correctness judgment ([report](research/generation-output-diagnostics-2026-09-28.md)). NLLB inference remains blocked by its uncached checkpoint. At that 2026-09-28 snapshot, pytest passed 584/584 and the documented unittest runner passed 582/582. The exact command is `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`. The v0.1.1 compact bundle contains 131 files (2,585,212 bytes) with no hash/path errors. See `release/v0.1.1/final-audit.json`, `release/v0.1.1-manifest.json`, [`research/benchmark-model-roadmap.md`](research/benchmark-model-roadmap.md), [`research/benchmark-research-status-2026-09-25.md`](research/benchmark-research-status-2026-09-25.md), and [`research/garhwali-bench-v0.2-schema-contract.md`](research/garhwali-bench-v0.2-schema-contract.md) for machine-readable and measured evidence.

The complete all-data content package remains local/access-controlled; the public repo exposes compatible content and metadata references for the full 257,807-row inventory. Hugging Face status was checked on 2026-09-27. [`Garhwali Speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech) is public with 110,436 VAANI and 2,927 Meta Omnilingual rows in separate configs. All 50 newly uploaded shard hashes and sizes match the local package. Dataset Viewer checks for Speech return HTTP 200: both configs expose train/validation/test splits, the Viewer lists 267 Parquet shards, and the Meta validation preview loads. Card-only follow-up commit [`b64f0c4b914296c979947cf551ec976a0342d8af`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/b64f0c4b914296c979947cf551ec976a0342d8af) adds split-safety guidance. [`Garhwali Corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) is public at commit [`a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a49a3f0bf5087d3ad0a7c8c5d399f8b4b301bcb2); the Hub confirms all 15 splits, 15 Parquet files, and public visibility. Its size endpoint reports 682,718 rows across nine configs and overlapping views. All nine config previews, search, and filters validate; statistics work for seven configs, while the HF statistics service returns HTTP 500 for `text` and `sravaani_drafts` when it encounters constant-valued columns. Locally, `datasets` 5.0.1 loads all nine configs, and the release audit and release-index checks pass. The full archive count is not a unique-example count; source content without compatible reuse terms remains represented by metadata references rather than reproduced payload. Detailed source findings are in [`research/structured-rights-web-review-2026-09-23.md`](research/structured-rights-web-review-2026-09-23.md); review findings do not by themselves clear records for public release.

Before attaching a public release, rerun the package builders, public/all-data cloud preflights, final audit, release-index validation, complete tests, compilation/shell checks, and bundle check against the exact commit referenced by `v0.1.1`. Do not move the existing v0.1.0 tag.

## Remaining limitations and follow-up

### Language quality

No native-speaker adjudications are complete, and only 29 of 28,755 parent texts have an explicit dialect label. These activities are deferred, not silently treated as completed. GarhwaliBench is an automated candidate; WER/CER and text-model results inherit the quality and coverage limits of their references. Do not call the dataset native-validated or the benchmark gold.

### Rights and access

The 216 structured records are present in the public reference index, while their full source content remains outside the public content payload until compatible source-specific reuse evidence is documented. The public catalog also redacts 24,566 text values without a compatible public-rights basis. Keep the full all-data content package private/access-controlled. A source being online does not by itself grant republication rights.

### Model evidence

Historical tokenizer, language-model, translation, retrieval, and speech results refer to their recorded input snapshots. They are not interchangeable scores on one frozen benchmark. A source-page-cluster bootstrap now covers saved XORQA BM25 development predictions: character-vs-word Recall@10 differs by +0.2 percentage points (95% CI 0.0–0.6), an inconclusive result conditional on the fixed all-split retrieval corpus. Machine transcripts remain labeled experimental; model agreement is not human ground truth. Paid Hugging Face work is not active. See the [clustered retrieval report](research/retrieval-source-page-cluster-uncertainty-2026-09-28.md).

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
