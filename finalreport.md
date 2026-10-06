# Garhwali Language Lab — final review report

## Quality-first Hugging Face and Kaggle follow-up — 2026-10-06 (latest)

An additive, screened transcript-text release is prepared locally from the
v0.2.7 source package. It contains **1,841 sentence-length training rows**
(47,566 words) and a separate **110-row short-utterance context view**. The
main training view has zero blank rows and zero normalized duplicate values;
one punctuation-only duplicate was excluded with both record IDs logged. The
deduplication key preserves Unicode combining marks so distinct Devanagari
vowel forms do not collapse. Every included row has exact Meta provenance,
CC BY 4.0 attribution and rights evidence, upstream train-only scope, and
automated quality labels. None has native-speaker review. The additive
Hugging Face card and matching Kaggle CSV package pass local schema, parsing,
hash, row-parity, and deterministic-rebuild checks. The Hugging Face update is
live as additive v0.2.8 paths at [data commit
`48f9107d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/48f9107d0285b3b3ec3c893303efb8a997cfc49b).
After identifying stale overview counts, the corrected card was published
and read back at [commit `cf60b2175`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cf60b217d9d3de045d81fb41d82514e29db2bf33); it reports 963,484 displayed
rows, including 778,157 reference rows and 185,327 overlapping content-view
rows across 20 named configurations.
Both configs load online with 1,841 and 110 rows and pass blank/duplicate
checks. Kaggle remains unpublished: the user approved enabling file-URL access,
but a Chrome security restriction requires the setting to be toggled manually.
See the [quality-release report](research/quality-screened-text-release-report-2026-10-06.md),
[roadmap](research/huggingface-kaggle-quality-release-roadmap-2026-10-06.md),
and [Meta rights decision](research/meta-omnilingual-training-rights-decision-2026-10-06.md).
The full project test suite passes **827/827** tests.

## Metrics correction — 2026-10-06

The earlier presentation of Hugging Face's 961,533 corpus rows could be read
as a count of usable language examples; it is not. The live corpus page shows
778,157 reference/index rows (80.9%) and 183,376 overlapping content-config
views. The main `text` config has 18,598 rows / 291,914 whitespace-separated
words, but **zero rows are currently marked recommended for general text
training**. `text_expansion` and `text_resources` also have zero recommended
rows. The 14,988 PahariLI sentences are experimental, with unresolved origins
and unreviewed labels. Speech has substantial audio, but not one supervised
pair per recording: only 2,002 strict speaker-disjoint references are in the
linked ASR view, and they remain unreviewed. Machine drafts are not gold text.

A fresh local inventory finds about **119.93 GiB allocated** under `data/`;
the 171.25 GB sum of file-path sizes includes hard-linked release snapshots,
source/audio, model/evaluation artifacts, and downloads. It is not unique
Garhwali language content. The old 77 GB headline used a different or partial
scope and should not be used as the project total. Detailed live/local metrics,
definitions, and measurement methods are in the [6 October Hugging Face metrics
and utility audit](research/huggingface-current-metrics-and-utility-2026-10-06.md).
No data payload changed in this correction.

## Kaggle packaging follow-up — 2026-10-06

After the v0.2.7 closeout snapshot below, I prepared reproducible Kaggle
exports without adding or deleting source records. The generated corpus package
contains 17 configs / 946,545 overlapping config and reference rows, and a
content-free index for 14,988 PahariLI sentence records. The speech companion
contains 113,363 transcript/metadata rows and no audio bytes. The Kaggle files
are local-only under ignored `data/kaggle/`; no Kaggle upload or public release
has occurred yet. See the [Kaggle release audit](research/kaggle-release-readiness-2026-10-06.md)
for scope, hashes, exact-overlap checks, and test evidence.

The release review also caught no new source records; the principal gaps remain
the 8,444 item-level rights decisions, unreviewed machine transcript drafts,
benchmark rights/independence, and deferred native-speaker validation. The
root test badge now reflects **820/820** passing tests after adding two focused
Kaggle exporter regression tests.

## Project closeout snapshot — 2026-10-06

This is the current handoff and the point where active project work is being
closed for now. It supersedes the older “current release” paragraphs and
status counts preserved below. Dated release, experiment, and source-audit
sections remain historical evidence for the exact snapshot they describe.

### What is available now

- **GitHub:** the project repository and its source, pipeline, schemas, and
  documentation are public. The source tree does not contain the ignored raw
  downloads, source PDFs, VAANI audio cache, or complete all-data package.
- **Hugging Face corpus:** public release **v0.2.7** at [commit
  `1f7b2ce`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/1f7b2ceed1b743412b75d6288757e1d2cadac9c4),
  with 18 named configs, 29 config/split views, 183,376 overlapping content
  rows, and 778,157 overlapping reference-table rows. These are view counts,
  not unique examples. The live Hub page currently reports 961,533 rows and
  7.56 GB. The detailed 29-split / Parquet readiness check remains documented
  in the dated v0.2.7 release report.
- **Hugging Face speech:** public **v0.2.1**, separate from the text corpus,
  with 113,363 rows, 113,350 unique audio hashes, and about 154.65 hours. It
  includes source/provider transcripts and a separate 104,534-row deduplicated
  SraVaani-draft view; 104,500 drafts are non-empty and remain unreviewed. The
  live Hub page reports a 36.5 GB repository file size.
- **Text training recommendation:** 0 of 18,598 main text rows, 0 of 1,737
  expansion rows, and 0 of 475 supplementary-resource rows are currently
  recommended for general text-model training. The `asr` config has 2,002
  unreviewed speaker-disjoint reference rows; the PahariLI config remains
  experimental and unresolved.
- **Automated checks:** the full project suite passes **820/820** tests after
  the closeout and next-version-default fixes. These tests check software and
  data contracts, not linguistic correctness.

### The actual content gap

The public `catalog` config has 23,448 blank text fields. A cross-config scan
found 15,004 corresponding values elsewhere in public JSONL fields; that
visibility does not itself grant reuse rights or make every match a suitable
training example. The other **8,444 distinct full texts** (2,936,664
whitespace-separated words; 16,388,267 characters) remain in the local
all-data package with `rights_pending` / `not_cleared`. Each has a source
locator: 7,675 rows carry an inline URL and 769 resolve a URL through the
public `source_catalog`. Some locators identify a collection or dataset rather
than the exact work or page. The local
quick-start now shows that lookup, and the source-group clearance queue and
method are in the [closeout gap audit](research/huggingface-corpus-gap-resolution-2026-10-06.md).
No text payload or rights status changed in this documentation closeout.

The v0.2.7 `paharili_gbm` config is available as an explicitly experimental
exception. PahariLI declares Apache-2.0 for its repository, but the row-level
sentence origins are unidentified and Garhwali labels are unreviewed. It must
not be called rights-cleared, native-validated, a general LM-training set, or
an independent evaluation set.

### What this project has and has not established

The project has a versioned, provenance-preserving public corpus; separate
speech resources; source and quality metadata; reproducible preparation and
release checks; vocabulary access examples; and local benchmark/model research
artifacts. It has **not** established comprehensive coverage of Garhwali, a
native-validated dataset, a gold benchmark, or independent-final accuracy
claims. GarhwaliBench remains local and uncleared for public upload; independent
evaluation eligibility is 0/5 task areas. Native review and dialect
annotation remain deferred. The API, hosted service, leaderboard, and
community review layer were not built.

### Closeout decision and remaining gap-resolution path

Active source ingestion stops at v0.2.7 here. No data was archived, deleted,
or overwritten. The public datasets remain available for clearly scoped
research and development. To expand the public text content later, resolve
rights by source/edition using authoritative licenses, written permission, or
edition-specific public-domain evidence; rebuild the additive package; then
rerun rights, quality, continuity, and Viewer checks. Keep all other records
discoverable through source metadata while their reuse basis remains unknown.
Linguistic review is a separate later workstream and is not asserted complete.

For developers, start at [`README.md`](README.md) and
[`docs/DEVELOPER_QUICKSTART.md`](docs/DEVELOPER_QUICKSTART.md). The indexed
current documentation and historical-snapshot policy are in
[`docs/README.md`](docs/README.md).

## Prior v0.2.6 status snapshot — 2026-10-05 (superseded)

The next section is retained as the v0.2.6 and 5 October audit snapshot. Its
use of “current” refers to that dated state; use the closeout above for present
release and availability counts.

The current public corpus release is **v0.2.6**, with data at
[commit `bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1).
The latest root/versioned cards are at metadata-only
[commit `cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e).
The 53 planned release paths match remote sizes and hashes (19 LFS SHA-256
and 34 Git blob SHA-1 checks); all 348 prior paths remain. The `.gitattributes`
change adds 19 LFS rules for the new shards and removes no earlier rule. The
additive release contains 36,105 parent catalog records, 12,657 public
full-text catalog records, 23,448 metadata-only catalog records, and 18,598
rows in the segment-oriented `text` view. Its 945,926 preflight rows span
overlapping configs and reference tables; they are not unique examples.

The local package preflight reports zero errors, zero missing source-traceability
rows, zero deleted or mutated records, and zero remaining identity leakage
across its configured splits. All v0.2.5 unique text values remain represented.
The current full suite passes **814/814** tests. The Viewer initially identified a
schema-inference error for `text` and `text_resources`; the cards now declare
stable schemas and all three metadata-reference configs, and their remote
hashes match local files. The final live check confirms **26/26 splits** and
**26/26 Parquet outputs**, with no pending or failed jobs. Preview, viewer,
search, and filter capabilities are enabled. Sample rows load for `text`,
`text_resources`, `record_index`, `source_catalog`, and `record_sources`;
Viewer statistics remain unavailable. Hugging Face publication and the
Dataset Viewer release check are complete.
See the [v0.2.6 publication report](research/huggingface-corpus-v0.2.6-release-2026-10-05.md),
[schema hotfix report](research/huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md),
and [remote verification JSON](research/huggingface-v0.2.6-remote-file-verification-2026-10-05.json).

A same-contract rerun now compares the v0.2.5 and v0.2.6 local package
preflights. It verifies matching schema version, validator SHA-256, and metric
definitions across 25 shared config/splits; v0.2.6 adds one 190-row
`text_resources/source_overlap` view, removes no view, and reports zero
deleted or mutated records. Aggregate view rows rise from 827,450 to 945,926
(+118,476), a total across overlapping configs and reference tables—not new
unique text or an accuracy gain. See the [comparison report](research/huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.md)
and its [machine-readable result](research/huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.json).

The separate speech repository remains at v0.2.1. The current training audit
reports zero recommendation mismatches and zero text rows recommended for
training; see its [report](research/huggingface-training-eligibility-audit-2026-10-05.md).
The earlier v0.2.5 publication and its successful Viewer check remain in the
[historical v0.2.5 release report](research/huggingface-corpus-v0.2.5-release-2026-10-05.md).

The 3–4 October Internet Archive search and acquisition added **119 local
payload files (6,005,077,831 bytes)**. The initial 3,369-page index was
expanded with two already-downloaded DjVu sidecars to **4,011 OCR page
objects**: 3,983 contain OCR, 3,982 remain non-empty after normalization, and
3,981 are distinct normalized values. One normalized duplicate group covers
two page rows; one non-empty OCR row normalizes to no letters or numbers. A
comparison against all **32,072 canonical cleaned parent texts** found 2
exact page matches (both already represented as Walton gazetteer pages) and 0
5-gram Jaccard candidates at ≥0.85 among 1,910,194 scored pairs. This is not a
guarantee against semantic or untested-layer overlap. Page language and OCR
accuracy are unverified, and none of the 4,011 pages has been newly cleared
for training or redistribution. The 39 local audio/video files total
14:09:25.531 of playback, not verified Garhwali speech time. All payloads
remain Git-ignored; no Archive acquisition files or new extracted rows are in
GitHub or Hugging Face dataset releases. The two exact page matches were
already represented by Walton gazetteer records. See the [source intake report](research/internet-archive-intake-2026-10-03.md),
[source-by-source disposition](research/internet-archive-source-disposition-2026-10-04.md),
and [quality and overlap audit](research/internet-archive-intake-quality-2026-10-04.md).

A separate technical media first pass re-hashed and reconciled all 39 files
against the source-linked candidate and `ffprobe` records: 39/39 passed, with
15 audio-only files, 24 videos with audio, and zero exact duplicate file
hashes. Combined size is 4.38 GB (4.08 GiB). All files remain unreviewed;
14:09:25.531 is playback duration, not verified Garhwali speech. One separate
27.481-second local pilot created a repetitive machine draft with no reference
for scoring. The saved model's existing test WER/CER are 74.3% / 40.4%, so it
was not used for bulk transcription. No content or rights state changed. See
the [media first-pass report](research/internet-archive-media-first-pass-2026-10-04.md).
The captured listings for all 31 items (1,047 file entries) and local folders
contain no transcript/caption sidecars. Six item language fields claim
Garhwali, but no recording was language-reviewed.

The priority follow-up distinguishes 920 page objects from three Garhwali
language/folklore studies and 440 page objects from two translated/contextual
folklore books (432 non-empty; 8 empty). There are 1,350 distinct normalized
non-empty values, one duplicate pair containing only a repeated digitizer
footer, and one row that normalizes to empty. Scholarly evidence confirms
Garhwali epic content in Chatak's book at work level; page-level language and
OCR accuracy remain unverified. The follow-up found a 1977-versus-1935 edition
mismatch for *Himalayan Folklore*, a Juyal CC0/all-rights-reserved conflict,
and no independently verified authority for the Shailesh CC0 claim. No
Archive expressive text entered GitHub or Hugging Face. Full findings and
source citations are in the [priority language and rights review](research/internet-archive-priority-language-rights-review-2026-10-04.md).

The local quality pass now maps all 722 Chatak/Shailesh scan pages. Shailesh's
contents page supplies 15 ranges covering 416 scans; a +13 printed-to-scan
offset was checked at the start, middle, and end of the numbered sequence.
Pages 63–64 are a contents gap, and Chatak still has no edition-specific
section map. A separate Hindi OCR covers the 29 flagged/empty pages; one
previously empty page yielded text and two remain empty. The alternate has
3,796 more characters than the prior OCR, which is not evidence of accuracy.
A text-free comparison triaged the pages as 11 high, 3 medium, and 15 low
priority for visual inspection. Inspecting all 14 high/medium pages found
several administrative or blank scans and two unresolved language-text
candidates; no transcription or OCR correction was promoted. Against the
32,072-row cleaned parent-text view, the alternates have zero exact matches
and zero ≥0.85 5-gram near-duplicate candidates (17,924 pairs scored). All
source OCR remains local; rights and linguistic accuracy are unresolved. See
the detailed review linked above.

## VAANI official-split lineage and ASR diagnostic — 2026-10-04

The prepared 5,894-row VAANI transcript manifest reconciles exactly to the
official 4,778/666/450 train/validation/test counts, with 5,894 unique audio
hashes and no cross-split hash duplicates. The strict project views (1,621 /
269 / 112) are exact subsets of those respective official splits. The expanded
human SraVaani training view is not safe for a full official-split evaluation:
it trained on 397 official validation rows and 338 official test rows outside
the project's smaller fixed evaluation manifests. Its previously recorded
fixed-112 test result is a separate historical slice.

The remaining 338 official-test rows were scored once with the local
Whisper-tiny v0.2 checkpoint: **83.249% WER** (3,449/4,143 words) and
**48.468% CER** (7,356/15,177 characters). All 338 audio files and prepared
references are present; a separate verification matched every audio hash and
reference and recomputed all per-row and aggregate metric counts. The score is
open-test diagnostic evidence, not independent accuracy: the official split
has been publicly evaluated by other researchers, our checkpoint was already
scored on the related 112-row subset, and speaker IDs are present for only 5
of these 338 rows. The checkpoint has no direct training-audio overlap with
the remainder, but the unidentified speakers prevent a speaker-independent
claim. See the [lineage and score report](research/vaani-official-split-lineage-2026-10-04.md).

The 2026 study [*Seeds Before Objectives*](https://arxiv.org/abs/2608.10670)
reports a five-seed, official-split w2v-BERT 2.0 standard-CTC mean of 47.0%
WER. Its method supports reporting seed variation; it is not a like-for-like
comparison to this single Whisper-tiny remainder score or an independent test
for this project. The v0.2.6 publication-era suite passed **802/802** tests
after the provenance and Viewer-schema work. Phase 8's read-only dry-run test
brought the suite to **803/803**. The additive-upload preflight/version guard
and four regression cases plus two provenance cases brought the suite at that
checkpoint to **809/809** (the repository CI unittest discovery command). Five
release-comparison regression tests bring the current suite to **814/814**.

## Meta Omnilingual ASR validation — 2026-10-04 to 2026-10-05

The new offline ASR preparation reconciled all 2,927 Meta Parquet rows against
the pinned source and transcript manifests, preserving 70 unsafe rows with
exclusion reasons. It produced 2,294 safe train, 271 safe validation, and 292
safe test rows; every derived WAV was hash- and format-checked. Local
Whisper-tiny Garhwali v0.2 scored **93.900% WER / 72.918% CER** on the safe
validation view. Beam-5 reduced WER by 0.4543 percentage points but raised CER
by 0.0325 points, so greedy decoding remains selected under the no-CER-
regression rule. The result is poor development evidence, not independent
accuracy. The base Whisper-tiny/SraVaani comparison is unavailable because
the necessary local artifacts/runtime are missing; Meta test was not scored.
Full hashes, slices, paired counts, and limits are in the [Meta ASR report](research/meta-omnilingual-asr-validation-2026-10-04.md).

## Meta Whisper adaptation — 2026-10-05

The Whisper-compatible view contains 1,793 train and 241 validation rows from
the safe Meta manifests. The 531 rows outside this checkpoint's 30-second or
448-token limits remain preserved in their source manifests and are logged in
a row-level exclusion ledger. One local training epoch lowered WER on the
paired validation view from **93.444% to 89.318%** and CER from **70.522% to
68.502%**. Both metrics improved for each of the two available validation
speakers. Seeds 17 and 29 produced byte-identical checkpoints and predictions
because the recipe was deterministic; this is a reproducibility check, not a
multi-seed uncertainty estimate. This is promising in-domain development
evidence, not independent or native-validated accuracy. References remain
unadjudicated, broad model exposure is incompletely known, and Meta test remains
unscored. The 219-row long-reference slice still has 89.366% WER after
adaptation; the two-row 3–8 second slice is too small to interpret. See the
[full adaptation report](research/meta-omnilingual-asr-adaptation-2026-10-05.md).
An older local Whisper-tiny v0.1 checkpoint scored 95.370% WER / 71.878% CER
on the same 241 rows, so the adaptation also outperforms that same-family
historical checkpoint. This comparison is still development-only and does not
resolve the two-speaker, unreviewed-reference, or upstream-exposure limits.

## Model lineage coverage refresh — 2026-10-05

The lineage auditor now includes the exact 1,793-row Whisper-compatible Meta
training manifest, its 241-row validation manifest, and the adapted
checkpoint's saved predictions. Its declared training and evaluation
manifest paths, hashes, and row counts match the local files. All 241
predictions map to the compatible validation rows, so that view is explicitly
`development_only` and previously scored. Compatible train and validation
have zero exact audio-hash, transcript-hash, or known-speaker crossings; the
strict VAANI training view also has zero exact audio/text/speaker overlap with
this validation view.

The adapted training transcripts nevertheless share **31 exact-hash groups
with 31 rows in each** of the current text validation and test views. These
are cross-task exposure matches for any text-task evaluation using this
checkpoint; they do not prove semantic leakage or Meta audio overlap. All rows
remain preserved. The 292 safe Meta test rows remain unscored, and independent
final-evidence eligibility stays **0/5**. The row-level ledger is Git-ignored;
aggregate findings and hashes are in the [lineage refresh](research/model-lineage-refresh-2026-10-05.md).

The earlier v0.2.4 audit recorded **776/776** unittest cases; the v0.2.5
split-safety milestone raised this to **791/791**, and the v0.2.6 provenance
and Viewer-schema additions brought the suite to **802/802**. Phase 8's
read-only dry-run regression test brought that to **803/803**. The additive-
upload preflight/version checks and four regression cases brought the suite to
**807/807**. Two source/code-provenance cases brought that checkpoint to
**809/809**; five release-comparison tests bring the current suite to
**814/814**. The
`validate_release_index.py` check still passes for release snapshot v0.1.1. Its compact
artifact hashes and paths also pass when checked without comparing against
the current source tree. The stricter local `build_release_bundle.py --check`
reports **60 stale-source entries** (36 selected current files absent from
that frozen bundle and 24 changed). The missing paths include generated Meta
ASR evidence and newer local reports; changed paths are current corpus and
derived-data indexes. The v0.1.1 bundle was not rewritten because it is a
historical snapshot. A future current-version release must regenerate a
versioned bundle from its frozen inputs before publication.

## GarhwaliBench rights and provenance audit — 2026-10-05

The frozen v0.2 benchmark manifest remains `43ba82ee2940c7f00115a059fdd4b895d81d2fbdeddf7aeacc17cbbd9e34d9e8`. Its eight views contain 14,703 view rows; the structural validator passes, but all rows still have `public_upload_allowed=false` and `public_release_cleared=false`. This pass changed neither payloads nor release gates.

The audit verified source IDs, attribution, source snapshot URLs, hashes, and retrieval dates across all 3,847 external rows. Provider use labels keep all of those records out of model-training eligibility. It substantiated source-level evidence for 1,793 Garhwali Open Bible Stories components under CC BY-SA 4.0 and 284 1916 LSI components identified as public domain; those can be prepared as separate condition-specific exports after attribution and modification notices are added. Another 8,265 recommended text rows still have `not_recorded` component decisions, including 36 Tatoeba rows with sentence IDs but no contributor names. The internal 112-row VAANI view still contains local audio locators and IDs. No row was removed or redacted. The exact source dispositions and machine counts are in the [rights/provenance report](research/benchmark-rights-provenance-audit-2026-10-05.md) and [JSON audit](research/benchmark-rights-provenance-audit-2026-10-05.json).

## Hugging Face quality release v0.2.2 — 2026-10-01 (historical review)

At the time of this 1 October snapshot, the public corpus was v0.2.2, with its corrective [Hub commit `b18933b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b18933bb2e98f091add0b1889e70587448d9891f); the speech repository was at v0.2.1. The additive v0.2.2
release adds a dedicated train-only `text_expansion` config with **1,647**
strict-tier Garhwali values already present in the catalog. These are net-new
relative to the existing text, ASR, machine-draft, instruction, and lexicon
text values, but are not newly ingested source texts; catalog overlap is
intentional. The candidate has **826,986** total package rows (164,141
content/config plus 662,845 reference/join rows) and passes preflight with zero
errors, zero missing source locators, zero deleted/mutated rows, and no reported
within-config identity duplicates. All 1,647 additions have recorded public
rights-basis fields and automated strict-tier labels; this does not establish
native-verified linguistic quality or source-page-family isolation. The
release preserves earlier versioned files; the remote head and package
manifest hash were verified after the corrective upload. A local schema fix
replaces null `speaker_id` values with empty strings so Viewer Parquet inference
does not hit the string-to-null cast error. The Dataset Viewer is now returning
HTTP 500 “server is busier than usual”; post-fix global validity and Parquet
checks remain pending.
The full configured unittest suite passes **698/698**; `git diff --check` passes.
The exact config-level result is in
[`research/huggingface-quality-candidate-preflight-2026-10-01.json`](research/huggingface-quality-candidate-preflight-2026-10-01.json).

Phase 1 (scorecard) is complete. The fast-tracked text view now has cross-config
normalized-string and held-out source-record checks; source-page-family
isolation and broader source-by-source rights reconciliation remain active.
The roadmap, frozen baseline, machine-readable candidate preflight, and text
expansion audit are linked from
[`research/huggingface-dataset-quality-roadmap.md`](research/huggingface-dataset-quality-roadmap.md).
The exact selection and overlap audit is in
[`research/huggingface-text-expansion-audit-2026-10-01.md`](research/huggingface-text-expansion-audit-2026-10-01.md).

## Developer access and Hugging Face v0.2.1 release — 2026-10-01

Both public Hugging Face repositories now have additive v0.2.1 releases. The
[corpus commit `7cae908`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/7cae908fee51acd2e1e47955acaa9ee035c9bfbc)
adds the versioned text/reference package and chronological card; the
[speech commit `9da266e`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/9da266e23bfc198f70784a6e81edbf32f946102f)
adds the versioned speech package and chronological card. Earlier files were
preserved. A follow-up
[corpus documentation commit `0a76bc6`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/0a76bc6a1f403b2ba460ef0ece464050c178c189)
corrects the versioned quick-start to match the public release. The cards now
explain the project history, package scope, data lineage, use limits, and
copy-paste access in order. After this review caught incorrect `v2.x` labels,
the corpus card and manifests were corrected at
[commit `a2d8716`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a2d8716d0dfdc49e5bce440b22312be4b94f9b98), and the speech card at
[commit `1a9cf07`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/1a9cf07176bc5a2dc4598dc3e0fa7321b8f982e5). A speech-card follow-up at
[commit `2808ad7`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/2808ad7d4c59becbd842f76ed38af1ee06274ba8) clarifies that the VAANI split counts cover all 110,436 audio rows, distinguishes the 5,894 provider-transcribed rows and 2,002 strict ASR rows, and labels SraVaani outputs as unreviewed drafts. It changes no audio or Parquet payloads. These metadata-only updates preserve the existing file paths and data payloads. Both packages carry the
versioned v1.0.0 record envelope for rights, reuse scope, license labels,
quality status, and quality flags; the text package also includes exact config
counts, Hugging Face Datasets/pandas/DuckDB examples, schema documentation, and
a searchable lexicon example. The linked schema, quick-start, license policy,
and rights-resolution log were aligned to v0.2.1 at corpus commit
[`796b5c4`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/796b5c45e6395c1d2559fbbc12cb2f795d0138fc).

The corpus package validates across **821,083 overlapping view rows** in 15
configs; the all-data package validates across **300,915 source-record views**.
The speech release has **113,363 rows**, **113,350 unique audio hashes**, and
**154.645 hours** across 267 Parquet shards. These are package and engineering
counts, not unique reusable training examples or claims of linguistic
accuracy. The Dataset Viewer API returned a temporary HTTP 500 busy response
after upload; repository visibility, cards, commit revisions, and file trees
were verified. The complete test and package-validation results are in the
latest entry of
[`research/corpus-preparation-status.md`](research/corpus-preparation-status.md).

## v0.2.1 rights-resolution update — 2026-10-01

The published release preserves **32,072 exact-unique text values** in
all-data and exposes **12,606** in the public catalog under distinct bases:
12,258 values with compatible open-license or work-specific public-domain
evidence, 134 CC BY-NC-SA 4.0 values, 198 source-policy values (5 PIB facts and
193 Mountain Voices headwords), and 16 isolated single-word facts. **19,466
full text values remain redacted** because compatible redistribution terms or
a fact-only projection are not established. This reduces redactions by 6,864
against the earlier source-expansion snapshot. The rights-resolved profile was
first uploaded as an interim package at
[`53c1ce9`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53c1ce9baa07e6fb05722e5a1ed750f33096124b); earlier releases remain available.
The corpus repository is public, so external users can access the rights-filtered
Hub revisions; unresolved expressive text remains outside the public content.

All **216 structured entries** are included in the v0.2.1 public profile
in six metadata-only configurations; only names, titles, dates,
categories, identifiers, and citations are exposed. Pending text is still
present in the local all-data package (zero catalog redactions); that full
all-data package is not public. The
source-by-source evidence, overlapping source queue, and exact decisions are
in [`research/text-rights-resolution-2026-09-30.md`](research/text-rights-resolution-2026-09-30.md). A documentation-only Hub amendment followed at
[`f2def9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/f2def9e717390008ebf7aac05decebf1c264fa98); it did not alter that interim data payload.

The project's requested “release unless explicitly marked private” rule cannot
be used as a legal clearance test: the Indian Copyright Office says copyright
arises automatically without formality, and a publicly accessible site is not
a redistribution license. This review
therefore maximizes factual metadata and source discovery while keeping
uncleared expressive text in all-data. The v0.2.1 package preflights pass with
zero errors; the release passes the 216-record factual-field allowlist scan,
and the catalog audit found zero pending-text payloads exposed publicly. The
updated tests and package verification are recorded in the rights-resolution
log. The Dataset Viewer/parquet endpoint returned HTTP 500 on both the first
request and one retry; preview availability remains unverified, while the
uploaded file tree and commit were verified separately.

## Source expansion checkpoint incorporated into v0.2.1 — 2026-09-30

The ordered post-ingestion pipeline has rebuilt the local corpus from **49
source files / 34,505 source records** into **32,072 exact-unique parent texts**
(+164 over the pre-refresh 31,908), **16,089,764 characters**, **2,935,379
whitespace-separated tokens**, and **151,690 exact-unique segments**. Exact
segment overlap across the text splits is zero. The local all-data package has
300,915 rows across overlapping views; the rights-filtered public profile has
155,516 rows, including 129,186 content rows, and its metadata-only index
covers 300,915 records, 4,911 sources, and 328,728 links. Automated quality
tiers and all privacy, licensing, and accuracy limits are detailed in the
[source-expansion report](research/v2.0-release-report-2026-09-30.md).

The pinned Garhwali Language Library contributed 164 net-new lexical strings;
Jambu contributed zero after exact deduplication. The existing 1,772 web-page
candidates remain rights-unassessed and experimental, with no public full-text
release. The rights-filtered package was first published under its original
Hub storage path `releases/v2.0.0/` at
[payload commit `5db2673`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/5db26737c4dcb4bd3e6a3750d30c2d9cae3048c1); the corrected cards are at
[commit `53a0aff`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53a0aff5ebaf7e676954065d86e2d78c0ff70504). Uploads were additive and did not delete older data or release files. The
GitHub `main` now contains the code, reports, tests, and refresh pipeline at
commit [`5f8636d`](https://github.com/rushilrawat/Garhwali-Language-Lab/commit/5f8636dc624e979a866f52764f2222c6fc615be2). GitHub Actions CI run [67](https://github.com/rushilrawat/Garhwali-Language-Lab/actions/runs/36765092886) passed.

This is a corpus and pipeline update, not a language-accuracy or model-score
release. No new model inference occurred. Native-speaker validation and dialect
annotation remain deferred at the owner's direction, and GarhwaliBench remains
a local research draft with independent-result eligibility at 0/5.

## Published release snapshot — v0.2.0 (2026-09-29)

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

## Interim local experimental expansion before the v0.2.1 refresh — 2026-09-30

This is the checkpoint immediately before the v0.2.1 lexical refresh below, not
the current working-tree count.

After the frozen v0.2.0 release, the tenth web wave scanned 6,844 Blogger feed
entries and two Garhwali-labelled short-story pages. It selected 1,818
candidate pages, skipped 46 exact duplicate rows, and added **1,772 exact-new
page records / 6,758,808 source characters** to the local experimental
pipeline. This is an increase in collected candidate pages, not a claim of
1,772 verified Garhwali texts. Automatic language review marked 1,147
mixed-script, 543 Romanized Garhwali candidates, and 82 scope-unverified rows;
none has native review.

All 1,772 rows retain rights-unassessed status and remain in the Git-ignored
local experimental/all-data view. The public Hugging Face content profile
received zero new full-text rows, and its published v0.2.0 commit is unchanged.
Current local working-tree figures are **31,198 exact-unique parent texts**,
**16,084,744 characters**, and **150,814 exact-unique segments**. The local
all-data development package contains **297,000 overlapping-view rows**. The
local public-profile preview has **151,812 rows including redacted catalog
entries**, of which 125,475 contain public-profile content; its content-free
reference index has 297,000 rows, 4,144 source entries, and 324,338
record/source links. All 1,772 new texts are preserved in the local all-data
preview and redacted from the local public preview. The package previews and
reference index were regenerated, but were not uploaded.
The pre-refresh working-tree test runs passed **635/635 pytest** and
**633/633 unittest** tests. The later rights-review snapshot passed **671/671
pytest** and **669/669 unittest** tests. The current v0.2.1 working tree passes
**684/684 configured-environment tests**. These checks validate package/code contracts; they
do not validate linguistic correctness or grant reuse rights to pending sources.
See the [wave report](research/garhwali-web-goldmines-2026-09-30.md) and the
auto-updated README metrics table for the working-tree counts.

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

## Historical v0.1.1 review snapshot (2026-09-28)

**Review date:** 2026-09-28
**Reviewed package ID:** `garhwali-language-lab-v0.1.1`
**Historical decision at that review date:** the then-current public Hugging Face corpus paired a rights-filtered content profile with a metadata-reference index of the 257,807-row all-data archive. Its figures and rights state were superseded by the later source-expansion and rights-resolution updates summarized above; they are retained here only as release history.

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

## Historical v0.2.1 limitations (superseded by the closeout snapshot above)

### Language quality

No native-speaker adjudications are complete, and only 29 of 28,755 parent texts have an explicit dialect label. These activities are deferred, not silently treated as completed. GarhwaliBench is an automated candidate; WER/CER and text-model results inherit the quality and coverage limits of their references. Do not call the dataset native-validated or the benchmark gold.

### Rights and access

The current v0.2.1 public profile includes factual/bibliographic
projections for all 216 structured records and redacts 19,466 of 32,072 unique
catalog values. All 32,072 texts remain in local all-data. Hugging Face serves
the interim rights-resolution package at commit `53c1ce9`. A source being online or lacking a visible copyright notice does not
by itself grant republication rights; do not upload the all-data payload.

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
