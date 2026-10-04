# Internet Archive Intake Quality Audit — 2026-10-04

## Decision

The Internet Archive intake is **not in the canonical corpus or either public
Hugging Face dataset**. It remains in Git-ignored local download and extraction
folders. This audit screens it without modifying source files or promoting
records. The GitHub update publishes the audit code and findings, not the
6.01 GB of downloaded PDFs, OCR payloads, audio, or video.

The next pipeline gate, Phase 6 of the
[Hugging Face dataset-quality roadmap](huggingface-dataset-quality-roadmap.md),
is automated source/language/rights triage before any content is promoted. The
cross-corpus exact and high-similarity comparison is now complete for the
32,072-row cleaned parent-text view. Page-level Garhwali language identity,
OCR accuracy, broader text layers, and media contents remain unverified.
Native-speaker review remains deferred.

## Intake and quality profile

| Measure | Result |
| --- | ---: |
| Downloaded payload files | 119 |
| Downloaded payload size | 6,005,077,831 bytes (6.005 GB / 5.59 GiB) |
| OCR JSONL files | 20 |
| Non-empty OCR page rows | 3,369 |
| Exact-unique normalized OCR texts | 3,368 |
| Repeated OCR text rows within intake | 1 |
| Missing record IDs / source IDs / text hashes | 0 / 0 / 0 |
| Empty OCR rows / JSONL parse errors | 0 / 0 |
| Normalized OCR characters | 4,960,578 |
| Pages with mostly Devanagari / mostly Latin / mixed script / no letters | 1,194 / 871 / 1,302 / 2 |
| 39 media files readable by `ffprobe` | 39; 0 failures |
| Media playback duration | 50,965.531 sec (14:09:25.531) |
| Rows flagged training-eligible / public-redistribution-eligible | 0 / 0 |

The OCR index has 981 pages from four Garhwali-focused language or folklore
works: 443 pages from Haridatta Bhatta’s *Garhwali Bhasha Aur Uska Sahitya*,
276 from Govind Chatak’s *Gadwali Lok Gathayen*, 201 from Gunanand Juyal’s
multilingual Garhwali/Kumauni/Hindi study, and 61 pages from an alternate
1959 *Gadwali Bhasha* scan already represented by the supplied book. These
are source-level descriptions, **not** 981 verified Garhwali pages. The other
2,388 pages are English, Hindi, or uncertain regional, historical,
geographical, ethnographic, and botanical references. Script does not identify
language: Devanagari pages can be Hindi or Garhwali, and Latin-script pages
are generally English contextual references in this intake.

## Duplicate screening

The source extractors previously reported no exact matches in the project
source/extraction layers they scanned. That check did **not** include the
canonical `data/processed/model_ready/cleaned/text.jsonl` view. The earlier
unqualified “zero exact overlap with existing project JSONL” wording was too
broad; current status documents now name the compared layers.

The new reproducible comparison normalizes Unicode with NFKC, case-folds,
keeps letters/marks/numbers, and collapses punctuation and whitespace. It
compared all 3,369 Archive OCR rows with all 32,072 rows in the cleaned
parent-text view:

- **Exact normalized overlaps:** 0.
- **Near-duplicate candidates at character 5-gram Jaccard ≥ 0.85:** 0 of
  1,647,488 length-compatible pairs scored.
- **Within-intake exact-duplicate text rows:** 1.
- A 61-page alternate 1959 grammar scan is a known work-level duplicate of
  the supplied book and remains marked as such.

Near-duplicate candidate generation uses only Archive n-grams occurring in at
most 100 Archive rows, and it skips pairs whose n-gram set lengths cannot
possibly reach the threshold. Thus zero candidates is evidence for this
defined comparison, not proof against lower-similarity paraphrases, scans,
shared-source relationships, overlaps with sentence segments/transcripts, or
matches missed by the rare-gram candidate rule. The report stores IDs, hashes,
and scores rather than text; it changes no records.

## OCR signals and media limits

Transparent heuristic flags mark 261 pages with a high digit ratio, 219 with a
repeated-character run, and one with a high symbol ratio. Flags can overlap and
are review signals, not OCR-error diagnoses or word-accuracy estimates. The
Archive sidecars have no comparable page-level OCR-confidence field. The
profile also counted 3,701 zero-width joiner/non-joiner characters; these
orthographic characters are preserved and are not classified as OCR defects.

All 39 MP3/MP4 files pass container/stream probing. Their combined 14:09:25.531
duration is **not Garhwali speech duration**. `ffprobe` does not reveal whether
media contains Garhwali, Hindi, Kumaoni, music, lecture, usable speech, or
reliable transcripts. Local ASR and language-identification runtimes were not
available during this pass, so neither transcript generation nor audio
language classification was performed.

## Recorded rights states

Every one of the 3,369 page records remains non-eligible for training and
public redistribution. The page-level catalog repeats each source’s recorded
rights state; these counts are source claims/evidence labels, not independent
legal determinations.

| Recorded source rights state | Page rows |
| --- | ---: |
| Unverified uploader license claim | 1,815 |
| No explicit reuse license recorded | 1,232 |
| Unverified Archive Public Domain Mark claim | 96 |
| Unverified uploader CC BY-NC 4.0 claim | 81 |
| Printed all-rights-reserved notice | 64 |
| Archive “not in copyright” claim recorded | 57 |
| Archive CC BY-NC 4.0 license recorded | 24 |
| **Total** | **3,369** |

An Archive item being publicly readable or downloadable does not itself make
the scanned work reusable. Preserve all source and OCR material locally with
its attribution and rights evidence; do not label it as public training text
or upload expressive content based only on an uploader or Archive statement.

## Reproduction

Run the read-only intake quality profile and the canonical-text overlap audit
from the project root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_intake_quality.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_corpus_overlap.py
```

The machine-readable outputs are under Git-ignored
`data/extracted/research/`:

- `internet_archive_quality_audit_2026-10-04.json`
- `internet_archive_corpus_overlap_2026-10-04.json`

The full acquisition ledger, source checksums, titles, and item-level
dispositions are in the
[Internet Archive intake report](internet-archive-intake-2026-10-03.md).

The repository's full configured unittest suite passed **707/707** after these
audit changes. This validates the reproducible code path and existing data
contracts; it does not validate Garhwali language content or rights.
