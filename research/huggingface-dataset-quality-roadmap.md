# Hugging Face Dataset Quality Roadmap

**Started:** 2026-10-01
**Scope:** Make `rushilrawat/garhwali-corpus` and `rushilrawat/garhwali-speech` more useful, trustworthy, and easy to apply.
**Current public release:** v0.2.3. New releases remain additive; existing records and source evidence are preserved.

## Goal

Make Garhwali resources easy for developers and researchers to find, inspect,
filter, and reuse for clearly described purposes. Progress is measured by
quality-qualified content and reliable access—not by adding reference-table
rows to a headline total.

## Current work focus — Phase 6 source disposition and candidate triage

Phase 7's latest release is published as v0.2.3. The v0.2.2 and v0.2.3
releases added access views over catalog values; neither collected new source
material. Published v0.2.3 adds a separate `text_resources` view for 246
normalized-unique Garhwali records (40,759 whitespace-delimited words;
183,484 characters) already in the corpus. None passes the current training
recommendation rule, so this is a lookup/research view, not a training-ready or
evaluation set.

Phase 6 has completed automated intake profiling, source-by-source metadata
disposition, non-destructive candidate views, and cross-deduplication against
the canonical cleaned parent-text view. The original 3,369-page index is now
reconciled with 642 pages from two already-downloaded DjVu sidecars, for 4,011
page objects total: 3,983 have OCR text, 3,982 remain non-empty after
normalization, and 3,981 are distinct normalized values. Two page rows exactly
match records already represented in the 32,072-row cleaned corpus; there are
zero 5-gram Jaccard candidates at ≥0.85 among 1,910,194 scored pairs. This is a
defined text-layer check, not a semantic or all-layer guarantee. The profile
verified 39/39 media files are technically readable. It reports 1,194
mostly-Devanagari pages, 1,485 mostly-Latin pages, 1,302 mixed-script pages,
and 30 with no letters. These are script signals, not language
identification: the audit cannot distinguish Garhwali from Hindi. Media totals
14:09:25.531, not verified Garhwali speech time. No page or media content was
newly cleared for training or public redistribution. See the
[`Internet Archive intake report`](internet-archive-intake-2026-10-03.md).
The quality results and limits are in the
[`intake quality audit`](internet-archive-intake-quality-2026-10-04.md).
All 55 item decisions and source-linked page/media candidate-view details are
in the [`source disposition report`](internet-archive-source-disposition-2026-10-04.md).

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

## Current verified release state

The 1 October baseline and its definitions are in
[`huggingface-quality-baseline-2026-10-01.md`](huggingface-quality-baseline-2026-10-01.md).
The published v0.2.2 release's config-level machine preflight is in
[`huggingface-quality-candidate-preflight-2026-10-01.json`](huggingface-quality-candidate-preflight-2026-10-01.json).
The current v0.2.3 corpus package has **827,450** overlapping-view rows:
164,387 content/config rows and 663,063 reference/join rows. The
`text_resources/train` config exposes **246** already-catalogued records; the
earlier `text_expansion/train` config exposes **1,647** values. Neither view
adds newly collected source texts. The public `text` config remains 18,949
rows; the separate speech dataset has 113,363 audio rows and 154.645 hours.
The current release preflight has zero errors; its Viewer/Parquet check remains
pending after an HTTP 500.

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

**Next action:** the initial page-level triage now records script composition and OCR-warning signals for every candidate. Add stronger language/genre candidate evidence for the 920 priority language-study pages and 432 translated-folklore pages, then investigate item-level reuse evidence for works that contain Garhwali-language material. Keep all automated output as a review signal, not a verified language label; preserve every original page and exclude no candidate from the local inventory. Media language and transcript review is a separate later workstream. Re-run the additive release pipeline only for content with an evidenced compatible use basis.

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

### Phase 7 — Publish purpose-built, stable Hugging Face views — active

- Keep text, lexicon, provider ASR, machine drafts, speech, factual knowledge,
  and source references clearly separated and documented.
- For each config, publish exact counts, field definitions, intended use,
  exclusions/flags, license scope, and a small loading example.
- Check Dataset Viewer configs/splits, Parquet previews, file hashes, and
  end-to-end `datasets` loading before every additive release.
- Preserve prior release paths; do not upload local caches, secrets, or
  unreviewed expressive text.

**Targets:** zero package/preflight errors; zero undocumented config changes;
every card count matches its manifest; the documented quick-start works from a
fresh environment.

### Phase 8 — Make ingestion and release repeatable

- Extend the existing refresh pipeline with a dry-run report, pinned inputs,
  checkpoints, idempotent deduplication, per-config quality scorecards, and
  release preflight.
- Require successful tests, rights checks, overlap checks, and card/manifest
  reconciliation before any Hub upload.
- Compare each release against its predecessor using the same metric contract.

**Targets:** one documented command produces a reproducible candidate package
and audit; rerunning it makes no unexplained changes; every release has a
versioned manifest and comparable metrics.

## Release gates and guardrails

- Keep all source records and variants; make exclusions through named,
  reversible views and flags rather than deletion.
- Do not count archive indexes, joins, drafts, or redacted metadata as clean
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
| 1. Quality scorecard | Complete | Published v0.2.2: 826,986/826,986 package rows traceable by config-specific rule; zero preflight errors |
| 2. Rights/provenance | Active | Per-config rights/status metrics implemented; source-by-source reuse-scope reconciliation next |
| 3. Dedup/splits | Partial | `text_expansion` exact-string dedupe is cross-config; complete document-family leakage report remains |
| 4. Text/lexicon | Active | 246-row supplementary view is public; quality remains mixed, with no training/evaluation promotion |
| 5. Speech/transcripts | Existing partial audits | Explicit labeled/empty/draft counts and split-safe manifests |
| 6. Coverage expansion | Active — intake, source disposition, and initial script/OCR triage complete | 119 local payloads; 4,011 OCR pages; 3,981 normalized unique non-empty texts; 2 exact / 0 ≥0.85 near candidates against 32,072 cleaned parent texts; 55 item dispositions; stronger page-language evidence, rights review, and media-content review remain |
| 7. HF release views | v0.2.3 live | Upload at `76dac8d`; direct stream verified at 246 rows; retry Viewer/Parquet when the Hub endpoint recovers |
| 8. Automation | Existing refresh command | Quality-gated, repeatable end-to-end release run |
