# Automated Pre-release Quality Plan

**Status:** local automated release pass completed 2026-09-18
**Scope:** strongest practical corpus cleanup and verification before the first proper release, excluding human review
**Release rule:** preserve every source record and original value; publish quality tiers and corrected derivatives instead of hiding data

## Target

Produce a reproducible Garhwali release in which:

- all **257,145 packaged records** pass structural and provenance validation;
- **65,000 unique SraVaani recordings** have independent Whisper-large-v3-turbo agreement evidence; the unfunded remainder stays unchanged;
- every OCR-derived record retains its original text, corrected text, page identity, source, and correction history;
- exact and semantic duplicates are grouped without losing source attribution;
- text, audio, and transcript confidence is explicit and usable for dataset filtering;
- train, validation, and test identities remain disjoint.

## Execution order

### 1. Audio transcript verification — Completed within the final paid run

- [x] Prepare 103,346 unique, disjoint SraVaani candidates.
- [x] Verify the first 5,000 recordings with Whisper-large-v3-turbo.
- [x] Complete four additional 15,000-record batches for 65,000 total unique recordings.
- [x] Stop paid processing when Hugging Face work was discontinued.
- [x] Aggregate and attach agreement evidence, including 157 exact agreements.
- [x] Keep model agreement as evidence; do not automatically treat it as ground truth.

**Acceptance:** every completed prediction maps to one audio SHA-256; no cross-batch duplicate hashes; no silent record deletion.

### 2. OCR reprocessing — Complete

- [x] Rank pages by OCR confidence, script anomalies, language-model disagreement, malformed spacing, and replacement characters.
- [x] Re-run a 20-page weak-page pilot with four OCR layouts at 300 DPI.
- [x] Re-run all 659 incoming machine-OCR pages with the validated multi-layout pipeline.
- [x] Compare candidates using layout agreement, confidence, script evidence, and length stability.
- [x] Apply 69 high-confidence consensus corrections automatically.
- [x] Retain the original OCR, corrected text, confidence, page identity, source hash, and layout evidence.

**Acceptance:** no source text is overwritten; every automated change is reversible and attributable; unchanged and unresolved pages remain available.

### 3. Text normalization and noise reduction

- [x] Normalize Unicode, punctuation, whitespace, broken line joins, and repeated page furniture.
- [x] Detect truncated, empty, markup-heavy, number-heavy, and implausibly repetitive records.
- [x] Correct high-confidence OCR substitutions with source-aware rules.
- [x] Recompute language, script, surface-quality, and spelling evidence after correction.
- [x] Preserve mixed Garhwali/Hindi/English records with explicit mixture tags.

**Acceptance:** all transformations are deterministic; record counts reconcile before and after processing; originals remain linked.

### 4. Duplicate and contamination control

- [x] Re-run exact hashes and normalized-text hashes across every text layer.
- [x] Rebuild duplicate groups across PDFs, websites, dictionaries, and derived segments.
- [x] Choose canonical training views while retaining every source occurrence and citation.
- [x] Remove identity and content leakage from strict train, validation, and test views.
- [x] Keep an all-data view separate from strict evaluation views.

**Acceptance:** zero identity overlap across strict splits; duplicate groups retain all provenance edges; no underlying source record is discarded.

### 5. Confidence tiers

- [x] Assign each record a reproducible release tier.
- [x] Derive tiers from documented evidence rather than source-name shortcuts.
- [x] Store the available OCR, language, surface-quality, provenance, duplication, and transcript-agreement evidence.
- [x] Export filterable manifests for text, ASR, TTS, lexicon, literature, geography, history, and cultural records.

**Acceptance:** every record has a tier and supporting evidence; tier assignment is reproducible from versioned inputs.

### 6. Full automated release audit

- [x] Validate JSON parsing, schemas, manifest counts, file hashes, and stable identities.
- [x] Check empty content, script distributions, provenance coverage, quality metadata, and missing files.
- [x] Verify all strict split isolation and audio/text deduplication rules.
- [x] Run focused tests, the full test suite, release audit, and `git diff --check`.
- [x] Generate final statistics, limitations, source cards, model cards, and the Hugging Face dataset card.

**Acceptance:** all blocking checks pass; remaining uncertainty is documented per record or source; release artifacts reproduce from committed code and manifests.

## Release outputs

- **GarhwaliCorpus:** complete provenance-preserving data and quality-tiered views.
- **GarhwaliBench:** frozen strict evaluation data with contamination checks.
- **Audio manifests:** human transcripts and machine transcripts clearly separated.
- **OCR corpus:** original and corrected text paired at page and segment level.
- **Hugging Face package:** all records included, with filters that let users select appropriate quality levels.
- **Quality report:** counts, corrections, unresolved issues, coverage, limitations, and reproducibility commands.

## What does not block this release

Native-speaker review remains valuable, but it is not required for this automated release. Records that cannot be resolved confidently remain included with lower confidence and explicit evidence rather than being hidden, deleted, or silently corrected.
