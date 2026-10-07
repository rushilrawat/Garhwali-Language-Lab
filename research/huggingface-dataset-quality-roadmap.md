# Hugging Face Dataset Quality Roadmap

**Started:** 2026-10-01
**Scope:** Make `rushilrawat/garhwali-corpus` and `rushilrawat/garhwali-speech` more useful, trustworthy, and easy to apply.
**Current public corpus release:** v0.2.8 (checked 2026-10-07). New releases remain additive; existing records and source evidence are preserved.

## Latest platform state — 2026-10-07

The live corpus page reports 963,484 displayed rows / 7.57 GB across 20
configs and 31 split views: 778,157 reference rows and 185,327 overlapping
content rows. The 1,841-row sentence-level candidate view and 110-row context
view are live; both re-index existing Meta-derived text and remain unreviewed.
The speech page reports 118,375 displayed rows / 36.5 GB: 113,363 audio/source
rows, 2,718 VAANI `asr_reference` rows, and 2,294 train-only Meta
`asr_meta_extra_train` rows. The audio is unchanged. The corpus's original
`asr` config remains a separate 2,002-row view. The current ASR references are
unadjudicated. See the [live metrics audit](current-platform-metrics-2026-10-07.md).

The public Kaggle text dataset is version 1 (1,841 candidate texts plus 110
context rows). The private Kaggle ASR dataset is version 2 (2,718 existing
VAANI audio/reference pairs); no unique data was added. The ASR notebook source
was saved as version 3 but has not been run. GitHub README and repository
metadata use Garhwali (`gbm`).

## Goal

Make Garhwali resources easy for developers and researchers to find, inspect,
filter, and reuse for clearly described purposes. Progress is measured by
quality-qualified content and reliable access—not by adding reference-table
rows to a headline total.

## Metrics and practical training status — 2026-10-06 baseline

The v0.2.7 corpus page reported 961,533 rows, but 778,157 (80.9%) were source and
reference-table rows, and all config totals overlap. The main text view contains
18,598 rows / 291,914 whitespace-separated words; zero currently pass the
project's general text-training recommendation flag. The 1,737 expansion and
475 supplementary text-resource rows also have zero recommended rows. The
14,988 PahariLI sentences are experimental language-identification material,
not a general LM corpus. The 2,002-row strict ASR view is unreviewed. The
speech repository has 113,363 rows and 154.65 hours of audio; its 104,500
non-empty SraVaani drafts remain machine hypotheses, not references.

This changes how phase progress is reported: file size, metadata rows, and
record catalog size are not content-quality milestones. Track usable text
words, rights/quality-qualified rows, reviewed ASR pairs, verified Garhwali
audio hours, and unique source-linked records separately. See the [current
metrics and utility audit](huggingface-current-metrics-and-utility-2026-10-06.md)
for definitions, local storage breakdown, and limits.

## Current closeout — text availability and source resolution

The v0.2.7 public corpus had 18 named configs and 29 config/split views. Its
latest recorded Viewer check found all 29 splits and Parquet exports available.
The text-availability audit found that 15,004 of 23,448 blank catalog values
already occur elsewhere in the public package, while 8,444 distinct texts are
not represented as text in any public config. All 8,444 remain in the local
all-data package with rights pending. Source locators are available for all:
7,675 rows carry inline URLs and 769 resolve through the public
`source_catalog`; some links identify only a source collection or dataset. The
public developer quick start contains the lookup recipe. See the
[gap audit](huggingface-corpus-gap-resolution-2026-10-06.md) for methods,
source groups, and the rights-resolution workflow.

The v0.2.7 phase notes below remain a historical closeout. The current
public-content work is
source/edition-specific rights evidence or permission, followed by an additive
package rebuild and complete preflight. PahariLI remains a labeled experimental
exception with unresolved sentence origins; it is not a reusable-rights or
language-quality precedent. Native review remains deferred. Historical phase
details below describe the release and checks at their recorded dates.

## Historical v0.2.6 work focus — Phase 8 release automation

The v0.2.6 data package is live at
[Hub commit `bddb006`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/bddb00665a7d6452a9e94c4484e9165d5b2d39b1).
All 53 planned release paths and sizes match, 19 LFS SHA-256 values and 34 Git
blob SHA-1 values match, and all 348 earlier paths remain. A metadata-only
card updates at [`dc2bab7`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dc2bab784c725d88d89541a27dcfb1084f5ec886)
and [`cd43e9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cd43e9e505ba0632cf2cbad87ff67f33bf40469e)
add stable whole-config schemas for `text` and `text_resources` and restore
the three metadata reference configs. A final live check confirms all 26/26
split views and 26/26 Parquet outputs with no pending or failed jobs. The
preview, viewer, search, and filter capabilities are enabled; sample rows load
for text, text resources, and the three reference tables. Statistics are not
available from the Hub endpoint. All 814 project tests pass and local package
preflight reports zero errors. Phase 7 is complete; Phase 8 is active, with the
refresh dry-run, additive-upload preflight/version gate, source/code provenance,
and same-contract release comparison implemented. The v0.2.5-to-v0.2.6 audit
compares 827,450 to 945,926 overlapping-view rows (+118,476), adds one
190-row `text_resources/source_overlap` view, and records zero deletions or
mutations. This is not a unique-text increase or accuracy gain. See the
[comparison report](huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.md),
[release report](huggingface-corpus-v0.2.6-release-2026-10-05.md),
[schema/card fix report](huggingface-v0.2.6-viewer-schema-hotfix-2026-10-05.md),
and [remote verification JSON](huggingface-v0.2.6-remote-file-verification-2026-10-05.json).

The release retains all v0.2.5 unique text values and routes upstream held-out
source overlaps outside default training. The package has 945,926
overlapping-view rows in its full preflight; this is not a unique-example
count. No text row currently passes the project's training recommendation
rule.
**Phase 2 source-family pass started — 2026-10-05:** the first primary-source
review confirms CC BY 4.0 evidence for the Meta and VAANI transcripts, CC
BY-SA 4.0 for Garhwali Open Bible Stories, and public-domain evidence for the
1916 LSI scan. It also found a material HinDialect license-scope conflict:
MTEB's card frontmatter says CC BY-SA 4.0 while its citation for the underlying
LINDAT source says CC BY-NC-SA 4.0; the 128 Garhwali lookup rows therefore keep
the more restrictive noncommercial share-alike scope. The accompanying
[rights and lineage audit](huggingface-phase2-source-rights-lineage-audit-2026-10-05.md)
records source terms and row counts without changing any rights or training
flags.

**Updated 5 October:** the v0.2.6 rebuild maps the VAANI test remainder to its actual canonical transcript source, `ARTPARK-IISc/Vaani-transcription-part`, and preserves its CC BY 4.0 evidence and `transcription_split=test` on all 338 records. Matching train-view rows are routed to `source_overlap`; no source text is deleted.

The source-lineage audit finds all 7,823 Indic-Dialect records in cleaned parents and the public catalog, and all 2,927 Meta records in both views. The segment-oriented public `text` config directly links 7,476 Indic-Dialect IDs (347 are still represented as catalog text) and 2,915 Meta IDs (12 are still represented as catalog text). This view distinction is documented rather than counted as source-record deletion.

The [v0.2.6 preflight](huggingface-v0.2.6-candidate-preflight-2026-10-05.json) passes all 26 configs: 945,926 overlapping-view rows, zero missing source traceability, zero deleted or mutated records, and zero remaining cross-split identity leakage. The [continuity audit](huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json) represents all 18,934 prior unique text values: 18,902 exact matches, 32 contained in linked catalog parents, and zero unrepresented. The 53-file additive release (907,215,611 bytes) is live at `bddb006`, with schemas and reference-table configs at `dc2bab7` and `cd43e9e`. Hub file and card hashes are verified; the final live Viewer check confirms all 26 splits and Parquet outputs, with sampled previews working. HinDialect license scope and direct segment-view lineage gaps remain documented. Keep training flags false until source, quality, and split gates pass. The original [training eligibility audit](huggingface-training-eligibility-audit-2026-10-05.md) remains the scorecard for that recommendation rule.

Phase 6 has completed automated intake profiling, source-by-source metadata
disposition, non-destructive candidate views, and cross-deduplication against
the canonical cleaned parent-text view. The original 3,369-page index is now
reconciled with 642 pages from two already-downloaded DjVu sidecars, for 4,011
page objects total: 3,983 have OCR text, 3,982 remain non-empty after
normalization, and 3,981 are distinct normalized values. Two page rows exactly
match records already represented in the 32,072-row cleaned corpus; there are
zero 5-gram Jaccard candidates at ≥0.85 among 1,910,194 scored pairs. This is a
defined text-layer check, not a semantic or all-layer guarantee. The profile
verified 39/39 media files are technically readable. A subsequent file audit
matched all 39 hashes, sizes, durations, and stream metadata and found no exact
duplicate file hashes. The files total 4.38 GB and 14:09:25.531 playback, not
measured Garhwali speech time. No local language-identification runtime is
available for classification. A pinned local ASR runtime was later used for
one pilot described below. It reports 1,194 mostly-Devanagari pages, 1,485 mostly-Latin pages,
1,302 mixed-script pages, and 30 with no letters. These are script signals,
not language identification: the audit cannot distinguish Garhwali from
Hindi. No page or media content was newly cleared for training or public
redistribution. See the
[`Internet Archive intake report`](internet-archive-intake-2026-10-03.md).
The quality results and limits are in the
[`intake quality audit`](internet-archive-intake-quality-2026-10-04.md).
All 55 item decisions and source-linked page/media candidate-view details are
in the [`source disposition report`](internet-archive-source-disposition-2026-10-04.md).
The follow-up [priority-language and rights evidence review](internet-archive-priority-language-rights-review-2026-10-04.md)
maps the five strongest works and documents edition and license-claim issues.

## Metric contract

Use these terms consistently in reports and dataset cards:

- **Package rows:** every row across every configuration. Configurations can
  overlap, and reference/join tables are included in this total.
- **Content rows:** rows that carry text, a lexical entry, a transcript, audio,
  or a factual/bibliographic record. This still does not mean every row is a
  unique training example.
- **Unique content units:** deduplicated at a named grain: parent text, text
  segment, lexicon form, transcript/audio hash, or fact. Never combine these
  units into one total.
- **Use-eligible units:** non-empty, identity-stable, source-traceable records
  with a reuse basis suitable for the stated use, an explicit quality/review
  status, and no task-specific split leakage. Report this separately for each
  use: lookup, research, training, or evaluation.
- **Quality evidence:** distinguish a status label (for example,
  `automated_quality_assessed_unreviewed`) from detailed evidence, a native
  adjudication, and a model metric. They are not interchangeable.
- **New data:** report extracted rows, exact-new units, near-duplicate groups,
  rights-cleared units, and use-eligible units separately for every source
  intake. Do not set a raw-row growth target.

## Historical v0.2.6 verified release state — 2026-10-05

The 1 October baseline and its definitions are in
[`huggingface-quality-baseline-2026-10-01.md`](huggingface-quality-baseline-2026-10-01.md).
The live Hub is v0.2.6; its payload is hash-verified and the final Viewer check
lists 26/26 splits and 26/26 Parquet outputs, with previews available for the
core text and reference-table configs. The public release has 36,105 parent catalog records: 12,657 public
full-text entries and 23,448 metadata-only entries under current source-use
decisions. Its `text` view has 18,598 rows (15,664 train, 1,305
source-overlap, 884 validation, and 745 test); `text_expansion` has 1,737 rows
(1,283 train and 454 source-overlap); and `text_resources` has 475 (285 train,
190 source-overlap). The public content configs total 168,388 overlapping-view
rows, while the metadata/reference index has 355,537 rows. These totals include
overlapping views, not unique examples. The additive upload plan has 53 files
and totals 907,215,611 bytes. See the [v0.2.6 Phase 2 audit](huggingface-phase2-source-rights-lineage-audit-2026-10-05.md),
[candidate preflight](huggingface-v0.2.6-candidate-preflight-2026-10-05.json),
and [continuity report](huggingface-release-continuity-v0.2.5-v0.2.6-2026-10-05.json).
The separate speech dataset remains v0.2.1 with 113,363 audio rows and 154.645
hours. Historical v0.2.5 publication details remain in the [release
report](huggingface-corpus-v0.2.5-release-2026-10-05.md).

The shared v1.0.0 record envelope is present across the package. Important gaps
remain in the *meaning* of some aggregate audit metrics: the current preflight
counts only selected provenance/quality field shapes, and its
`rows_with_quality_metadata` label can be mistaken for complete quality
coverage. Phase 1 now adds per-config source traceability and separates the
quality-status and quality-evidence signals. The v0.2.2 package has been
reconciled against the frozen v0.2.1 package. Its additional text view has no
normalized exact-string collisions with existing text, ASR transcripts,
machine drafts, instruction/response strings, or lexicon forms, and no source-
record-ID overlap with frozen benchmark validation/test. Source-page-family
independence is still not established. The release was published additively
at [Hub commit `b18933b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b18933bb2e98f091add0b1889e70587448d9891f).

The published v0.2.3 release adds a separate 246-row `text_resources/train` view. It
selects Garhwali-only source labels with a recorded redistribution basis,
excludes normalized duplicates across existing text, ASR, machine drafts,
instructions, lexicon, and `text_expansion`, and excludes source records used
by held-out evaluation. The complete v0.2.3 per-config preflight is in
[`huggingface-quality-candidate-preflight-2026-10-02.json`](huggingface-quality-candidate-preflight-2026-10-02.json).

**Published 2 October 2026** at [Hub commit `76dac8d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76dac8de70d37595c7af9a3c642c81ece615ec5d). The new config streams through `datasets.load_dataset` with 246 records. The Dataset Viewer Parquet endpoint returned HTTP 500 twice; preview remains unverified. Full selection details are in the [existing-corpus expansion audit](huggingface-existing-corpus-expansion-audit-2026-10-02.md).

**Published 5 October 2026 — v0.2.4:** recovered Tatoeba contributor
attribution and immutable revision/history URLs for Wikimedia/Wiktionary
sources, then rebuilt and uploaded additively. The 48 planned files match
remote hashes and sizes; prior release paths remain. No source text was added,
removed, or changed. The public text views now report zero rows recommended for
training because explicit source eligibility and split rules are applied.
Streaming access works for `text` and `lexicon`; Viewer/Parquet indexing is
still pending. Exact results are in the [release verification](huggingface-corpus-v0.2.4-release-2026-10-05.md)
and [candidate preflight](huggingface-quality-candidate-preflight-2026-10-05.json).

**Completed 2026-10-04:** added source-specific language/genre evidence for the 920 priority pages and the translated-folklore group (440 page objects: 432 non-empty, 8 empty), then checked item-level bibliographic and rights evidence for all five works. The priority group has 919 distinct normalized values; the translated group has 431 distinct non-empty normalized values, plus one OCR row that normalizes empty. A duplicated Juyal footer pair is preserved but is not useful language content. The review confirms a 1977 reprint mismatch and two unresolved uploader CC0 claims; the Juyal claim conflicts with an original “all rights reserved” page. No new content was cleared for training or public redistribution; no original page was deleted. See the [priority-language and rights evidence review](internet-archive-priority-language-rights-review-2026-10-04.md).

**Completed 2026-10-04:** mapped Shailesh's 15 visually checked contents ranges to 416 physical scan pages using a +13 offset verified at three positions; left the printed-page gap, preliminaries, and suffix unassigned. Compared all 29 original/alternate OCR pairs without including text in the report, then visually inspected the 14 high/medium triage pages. Several were library/title/index matter or blank; Shailesh's literary page remains unresolved. A full-resolution check corrected the Chatak page reference: scan page 144 has the existing sparse heading OCR; scan page 145 is blank. No OCR was corrected or promoted. The overlap audit found no exact or ≥0.85 5-gram matches against the 32,072-row cleaned text view.

**Completed 2026-10-04:** searched source-specific author-life, edition, and first-owner evidence for the five priority works. Secondary dates and the Indian Copyright Act produce conditional term scenarios, including a possible India-only public-domain lead for the original 1935 *Himalayan Folklore* body. Conflicting/unverified dates, the mixed 1977 reprint introduction, and worldwide reuse remain unresolved, so no rights state changed. See the [rights evidence review](internet-archive-priority-language-rights-review-2026-10-04.md).

**Completed 2026-10-04:** the first technical media pass verified file hashes,
sizes, durations, and streams for all 39 assets; zero exact file-hash duplicates
were found. It confirms 15 audio-only files, 24 video-with-audio files, and
14:09:25.531 combined playback across 31 Archive items. No local
language-identification runtime is installed. See the
[reproducible media first-pass report](internet-archive-media-first-pass-2026-10-04.md).

**Completed 2026-10-04:** scanned 31 captured Archive metadata snapshots
covering 1,047 listed files, plus the local item folders. No filename/format
caption or transcript candidates and no matching local sidecars were found.
Six catalog language fields explicitly include Garhwali, but these remain
unverified item-level claims. The sidecar scan is included in the
[reproducible media audit](internet-archive-media-first-pass-2026-10-04.md).

**Completed 2026-10-04:** installed the already-pinned optional ASR requirements
locally and ran a 27.481-second media pilot with the existing Whisper-tiny
Garhwali checkpoint. It produced a repetitive, unreviewed machine draft with
no reference for scoring. The checkpoint's existing 112-row test report has
74.3% WER / 40.4% CER, so it is not suitable for bulk transcription as a
quality improvement. No alternative general Whisper-tiny checkpoint is cached;
no new weights or hosted compute were used. One local draft is kept in the
ignored research output, and no rights/language/training status changed. See
the [pilot findings](internet-archive-media-first-pass-2026-10-04.md).

**Next action:** compare available no-cost local ASR candidates only if a
checkpoint can be independently evaluated on the frozen Garhwali validation
set. Until then, retain the single draft as experimental evidence and do not
bulk-generate low-accuracy transcripts. Keep measured Garhwali speech hours
separate from total playback; metadata and model output do not verify language.

## Ordered phases

### Phase 0 — Freeze the baseline and metric definitions — complete

- Record the exact package revision, command, and file hashes.
- Separate content, unique-content, reference, and use-eligible counts.
- Record text, lexicon, speech, transcript, metadata, rights, and split metrics
  independently.
- Mark the denominator and field rules for every percentage.

**Exit gate:** another run from the same package reproduces the baseline; no
headline combines unlike grains.

### Phase 1 — Build an honest, per-config quality scorecard — complete

- Split schema-envelope completeness from non-empty quality flags, detailed
  quality evidence, and source traceability.
- Define traceability by configuration: text/lexicon provenance, audio hash and
  upstream row for speech, and record/source joins for reference tables.
- Report null/empty content, stable-ID completeness, rights-state counts,
  script/language labels, review status, duplicate groups, and split leakage.
- Keep the old preflight output interpretable; document any metric-key changes.

**Completed in v0.2.2:** the preflight separates rows with
a non-empty `quality_status`, rows where a detailed quality field is present,
and rows where at least one such field has a non-empty value. It reports
config-aware source traceability, recorded rights-status and reuse-scope
distributions, license-label counts, and rights-basis field presence. Legacy
metric keys remain available with explicit compatibility definitions. All
826,986 package rows meet their configuration-specific minimum
traceability rule, including 32,072/32,072 catalog entries and 5,019/5,019
source references. This is locator coverage, not rights clearance or language
accuracy. The current scorecard shows 159,420 rows with at least one
configured quality-detail key and 140,009 with a non-empty detail value; those
counts are not review or correctness rates.

**Targets:** 100% of packaged records conform to their declared schema; 100% of
content records have an explicit quality/review status and a configuration-
appropriate identity; every reported coverage number has a defined denominator.
Unknown source or rights evidence stays marked unknown rather than being counted
as cleared.

### Phase 2 — Rights and provenance resolution — active

- Resolve source-catalog and record/source joins for public content; distinguish
  redistribution, research, commercial, and metadata-only permissions.
- Keep source URLs, snapshots/hashes, attribution, license evidence, and
  transformation lineage attached to each record or stable join.
- Preserve unresolved material and its catalog reference; keep its expressive
  content out of public training-ready views until a compatible basis is
  established.
- Resolve the new per-config scorecard into distinct decisions for public
  viewing, citation/research, redistribution, model training, and commercial
  use. Do not promote a source-level term to an item unless its scope matches
  that item.

**Started:** the preflight now publishes recorded rights-status, reuse-scope,
license-label, and rights-basis-presence counts separately for every config
and split. It explicitly counts recorded labels as-is and does not infer
permission from a URL, label, or field's presence. Next: reconcile each public
content config against its linked source evidence and flag conflicting or
unassessed terms at the record level.

**First source-level training-gate audit — 2026-10-05:** the recommendation
rule was independently recomputed for all 20,842 rows in the public
`text`, `text_expansion`, and `text_resources` configs; stored values match,
but no row is currently recommended for training. All rows have at least one
source-level `training_eligible: false` and at least one experimental-eligibility
signal; the latter does not override the ordinary flag or resolve rights. A
simulation that changed only those false values in memory (leaving splits,
rights, and quality flags untouched) would allow 1,731 core train rows and 263
expansion train rows through the existing gate. It admits no supplementary resource
rows. This is a diagnostic, not authorization: the [audit report](huggingface-training-eligibility-audit-2026-10-05.md)
lists source counts and blockers. Next, investigate the highest-count source
families (`indic_dialect_asr_gbm`, `meta_omni`, OBS, LSI) against primary terms
and component lineage; record training, redistribution, commercial, research,
and attribution decisions separately. Do not change flags solely to increase a
training count.

**Targets:** zero public training-content rows with unresolved reuse terms;
100% of public content rows have traceable source evidence and a recorded
reuse-scope decision. A metadata reference is never counted as a published
text example.

### Phase 3 — Deduplication and task-safe splits

- Recompute exact, normalized, audio-hash, parent-document, and supported
  near-duplicate matches across configurations.
- Mark cross-config overlaps and conflicting source variants; do not delete
  originals.
- Rebuild task-specific train/validation/test manifests at the correct grain:
  parent/document for text, audio and speaker for ASR, and source groups for
  retrieval or generation.

**Completed release safeguard — 2026-10-05:** v0.2.5 routes 1,308 core-text
rows and 363 catalog-expansion rows carrying direct Meta development/test IDs
or normalized transcript matches to held-out Meta/VAANI material into a public
`source_overlap` split. The IDs and text values match v0.2.4; no values were
deleted or rewritten. Cross-split identity checks pass. This resolves the
identified source-record/text-match cases only; parent-document,
audio/speaker, semantic, and broader source-page-family leakage reviews remain.

**Targets:** zero exact identity or speaker/document crossings in each
training/evaluation view; every detected cross-config duplicate group is
counted and marked; semantic candidates remain explicitly unadjudicated.

### Phase 4 — Improve text and lexicon usefulness

- Profile by source, script, genre, length, text origin, and quality tier.
- Fix deterministic extraction defects and OCR layout problems while retaining
  originals and recording every transformation.
- Separate reusable clean text, source-faithful transcription, mixed-language
  context, machine proposals, and lexicon entries into purpose-labeled views.
- Prioritize missing practical vocabulary and source families by evidence and
  coverage gaps, not by volume alone.

**Targets:** no empty or malformed records in a training-eligible view; 100% of
automated edits have a reversible link to their source value; publish exact
counts by script, source family, and quality/review state. No automated score
is described as native validation.

**Completed in published v0.2.3:** 246 additional existing catalog texts
are exposed in the separate `text_resources` view after normalized
cross-config deduplication and evaluation-source exclusion. Quality varies;
none is recommended for training or evaluation. Each row keeps its source,
rights, quality, and attribution fields. This improves access, not source
coverage or verified language accuracy.

### Phase 5 — Improve speech and transcript usability

- Keep raw audio immutable; validate hashes, decode/readability, duration,
  silence/clipping flags, and duplicates.
- Keep provider references, human corrections, machine drafts, and audio-only
  rows distinct. Retain empty machine outputs for audit, but exclude them from
  text-training views.
- Track usable labeled hours and rows by source, speaker coverage, split, and
  transcript status. Do not promote SraVaani hypotheses to reference text.

**Targets:** zero empty transcripts in supervised ASR views; zero audio-hash or
speaker leakage across the frozen evaluation split; 100% of draft rows labeled
as machine-generated and review state explicit.

### Phase 6 — Expand verified Garhwali coverage — active

- Revisit credible archives, dictionaries, university work, local publications,
  and openly usable speech/text sources.
- Pin source revisions and rights evidence before ingestion; use the existing
  resumable pipeline and overlap audit.
- Prioritize underrepresented vocabulary domains, genres, places, and source
  families. Keep “discovered,” “ingested,” “unique,” “publicly reusable,” and
  “training-eligible” counts separate.

**Updated 2026-10-04:** title-focused Archive queries screened text, audio and
video candidates; the complete local acquisition has 119 unique payload hashes
and a 4,011-page view, including 642 rows from two supplemental local DjVu
sidecars. There are 3,983 non-empty OCR rows, 3,981 distinct non-empty
normalized values, 2 canonical exact matches, and zero ≥0.85 5-gram candidates
against 32,072 cleaned parent texts. All 4,011 rows have stable record/source
identifiers and text fingerprints. Automated screening reports OCR warnings
but does not identify Garhwali versus Hindi. All 39 media files pass
`ffprobe`, but media language and speech content are unmeasured. Full results
and each item’s disposition are in the
[intake quality audit](internet-archive-intake-quality-2026-10-04.md). New
files remain outside the published package.

**Targets:** every intake reports gross rows, exact-new units, near-duplicate
groups, rights outcomes, and eligible yield; no source is described as added
until its output is reconciled against the existing corpus.

### Phase 7 — Publish purpose-built, stable Hugging Face views — complete for v0.2.6

- Keep text, lexicon, provider ASR, machine drafts, speech, factual knowledge,
  and source references clearly separated and documented.
- For each config, publish exact counts, field definitions, intended use,
  exclusions/flags, license scope, and a small loading example.
- Check Dataset Viewer configs/splits, Parquet previews, file hashes, and
  end-to-end `datasets` loading before every additive release.
- Preserve prior release paths; do not upload local caches, secrets, or
  unreviewed expressive text.

**v0.2.6 result:** zero package/preflight errors; all 26 expected splits and
Parquet outputs load, required previews work, and the card schemas match the
release manifest. Statistics remain unavailable from the Hub endpoint.

**Targets:** zero package/preflight errors; zero undocumented config changes;
every card count matches its manifest; the documented quick-start works from a
fresh environment.

### Phase 8 — Make ingestion and release repeatable

- **Complete:** `refresh_corpus_after_ingestion.py --dry-run` prints the exact
  ordered commands and output paths, checks that each script exists, and
  writes nothing. At the time of the v0.2.6 snapshot, its default staging
  paths followed that schema version; a regression test covers the planned
  command list. Current next-candidate defaults are v0.2.8.
- **Complete:** the additive upload preparer runs the full record-level
  validator before staging, requires the manifest version to match
  `releases/vX.Y.Z`, and writes nothing if validation fails. Its upload plan
  pins the input-manifest SHA-256, schema version, preflight run ID, and
  preflight-report SHA-256. A real v0.2.6 package passes this path across all
  26 configs; malformed-package and version-mismatch cases are covered by tests.
- **Complete:** the dry-run fingerprints Git revision/tracked diff and all
  pipeline scripts; it also hashes every discovered text JSONL input, source
  manifest, and online snapshot pointer. A real refresh captures those inputs
  after its pinned source-ingestion steps and stores the inventory alongside
  the metrics. The current dry-run resolves 455 input files, including 75 text
  JSONL files (212,625,108 bytes), with all required manifests present.
- **Complete — same-contract release comparison:**
  `compare_hf_release_metrics.py` accepts two passing preflight reports and
  refuses mismatched record-schema versions, validator hashes/contracts, or
  metric definitions. Fresh preflights for v0.2.5 and v0.2.6 produce the
  [JSON](huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.json) and
  [Markdown](huggingface-release-metrics-v0.2.5-to-v0.2.6-2026-10-05.md)
  comparison. Both have zero errors; the same validator SHA-256 and metric
  definitions were verified. The comparison covers 25 shared config/splits,
  one added view, no removed views, and zero reported deleted/mutated rows.
  Its 118,476 aggregate-row increase sums overlapping views and reference
  tables; it is not a count of new unique texts.
- For future releases, run the same comparison after candidate preflight and
  include both preflight reports and the comparison in the release audit.
  Keep the checkpointed LangGraph ingest, deterministic deduplication,
  per-config scorecards, and source audits in the flow.
- Require successful tests, rights checks, overlap checks, and card/manifest
  reconciliation before any Hub upload.
- Compare each release against its predecessor using the same metric contract.

**Targets:** one documented command produces a reproducible candidate package
and audit; rerunning it makes no unexplained changes; every release has a
versioned manifest and comparable metrics.

## Release gates and guardrails

- Keep all source records and variants; make exclusions through named,
  reversible views and flags rather than deletion.
- Do not count archive indexes, joins, drafts, or metadata-only records as clean
  training text.
- Do not state a corpus-wide reuse license when sources differ.
- Native-speaker review and dialect annotation remain deferred. The dataset may
  improve automatically, but those claims remain unverified until reviewers
  participate.
- Keep newly ingested or newly redistributable source payloads behind Phases
  1–3 and relevant modality checks in Phases 4–5. A narrow additive view of
  values already exposed in the public catalog may be released when it adds no
  source text, every row passes the existing rights-basis filter, and its
  training/evaluation and overlap limits are explicit. v0.2.2 and v0.2.3 used
  this exception; neither view asserts independent evaluation or native review.

## Work tracking

| Phase | Status | Current proof / next deliverable |
| --- | --- | --- |
| 0. Baseline | Complete | [1 Oct baseline](huggingface-quality-baseline-2026-10-01.md) |
| 1. Quality scorecard | Complete for published package checks | v0.2.7 preflight passed; latest recorded Viewer check lists 29 splits and Parquet exports. These are integrity checks, not linguistic accuracy. |
| 2. Rights/provenance | Closed at the current release; clearance gap documented | v0.2.7 closeout: 15,004 of 23,448 blank catalog values occur elsewhere in the public package; 8,444 distinct full texts remain local with rights pending. PahariLI sentence origins also remain unresolved. |
| 3. Dedup/splits | Partial | v0.2.7 isolates four PahariLI source-overlap groups; earlier preflight found zero identity leakage for its tested views. Source-family, semantic, audio, and speaker review remain incomplete. |
| 4. Text/lexicon | Closed for this project stage | The public views contain 1,737 expansion and 475 resource rows; no text row currently meets the conservative model-training recommendation. |
| 5. Speech/transcripts | Existing partial audits | Explicit labeled/empty/draft counts and split-safe manifests |
| 6. Coverage expansion | Closed at v0.2.7; Archive intake remains local | 119 local payloads, 4,011 OCR pages, 722-page Chatak/Shailesh map, and 39 media files were not newly cleared or published. No verified Garhwali rows were promoted from this intake. |
| 7. HF release views | Complete for v0.2.7 | Data at `1f7b2ce`; 18 named configs, 29 config/split views; prior release paths retained; latest recorded live Viewer check lists 29/29 splits and Parquet outputs |
| 8. Automation | Local preparation automated; publication remains deliberate | Ingestion/refresh graph, provenance, package preflight, and additive upload-plan gates exist. HF uploads remain explicit; the next default candidate is v0.2.8. |
