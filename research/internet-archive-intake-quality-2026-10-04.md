# Internet Archive Intake Quality Audit — 2026-10-04

## Decision

The new Internet Archive intake is **not ingested as Archive-sourced records
in the canonical corpus or either public Hugging Face dataset**. It remains in
Git-ignored local download and extraction folders. Two page texts exactly
match existing Walton gazetteer records, as detailed in the overlap audit. This
review screens the intake without modifying original source files or promoting
new records. The GitHub update publishes audit code and findings, not the
6.01 GB of downloaded PDFs, OCR payloads, audio, or video.

The intake and first follow-up gates—source-by-source disposition,
non-destructive candidate views, canonical-text comparison, priority-work
language/genre evidence, and five-item bibliographic/rights research—are
complete. See the [priority-language and rights evidence review](internet-archive-priority-language-rights-review-2026-10-04.md).
Page-level Garhwali identity, OCR accuracy, broader text-layer overlap, legal
reuse authority, and media contents remain unverified. Native-speaker review
remains deferred.

## Intake and quality profile

| Measure | Result |
| --- | ---: |
| Downloaded payload files | 119 |
| Downloaded payload size | 6,005,077,831 bytes (6.005 GB / 5.59 GiB) |
| Original OCR JSONL page indexes | 20 |
| Consolidated review-view page objects | 4,011 |
| Non-empty OCR rows / empty OCR rows | 3,983 / 28 |
| Exact-unique source-normalized non-empty OCR texts | 3,982 |
| Distinct non-empty values after NFKC/case-fold/punctuation normalization | 3,981 |
| Repeated non-empty OCR text rows / duplicate groups | 1 / 1 group (2 rows) |
| Missing record IDs / source IDs / text hashes | 0 / 0 / 0 |
| JSONL parse errors | 0 |
| Characters in profiled OCR text fields | 5,895,767 |
| Pages mostly Devanagari / mostly Latin / mixed script / no letters | 1,194 / 1,485 / 1,302 / 30 |
| 39 media files readable by `ffprobe` | 39; 0 failures |
| Media playback duration | 50,965.531 sec (14:09:25.531) |
| Rows flagged training-eligible / public-redistribution-eligible | 0 / 0 |

The page candidate groups include 920 pages from three Garhwali-focused
language or folklore studies; 432 pages from translated-folklore sources; 61
pages from an alternate 1959 *Gadwali Bhasha* scan already represented by the
supplied book; 2,570 regional reference pages; and 28 empty OCR pages. These
are source-level descriptions and review queues, **not** verified page-language
labels. The full item/page breakdown is in the
[source disposition report](internet-archive-source-disposition-2026-10-04.md).
Script does not identify language: Devanagari can be Hindi or Garhwali, and
Latin-script pages in this intake are generally English contextual material.

## Duplicate screening

The source extractors previously reported no exact matches in the project
source/extraction layers they scanned. That check did **not** include the
canonical `data/processed/model_ready/cleaned/text.jsonl` view. The earlier
unqualified “zero exact overlap with existing project JSONL” wording was too
broad; current status documents now name the compared layers.

The reproducible comparison normalizes Unicode with NFKC, case-folds, keeps
letters/marks/numbers, and collapses punctuation and whitespace. It compared
all 4,011 Archive page objects with all 32,072 rows in the cleaned parent-text
view:

- **Exact normalized overlaps:** 2 page rows, both already represented as
  `walton_gazetteer_1910:scan-page-90/91` under
  `public_domain_india_government_work_term_expired` provenance.
- **Near-duplicate candidates at character 5-gram Jaccard ≥ 0.85:** 0 of
  1,910,194 length-compatible pairs scored.
- **Within-intake normalized duplicate:** 1 group across 2 page rows.
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

Transparent heuristic flags mark 274 pages with a high digit ratio, 226 with a
repeated-character run, and one with a high symbol ratio. Flags can overlap and
are review signals, not OCR-error diagnoses or word-accuracy estimates. OCR
word-confidence attributes are available only from the *Himalayan Folklore:
Kumaon and West Nepal* DjVu XML: 368 pages, 82,452 words, weighted mean 49.461.
These are engine signals, not measured word accuracy. The profile also counted
3,701 zero-width joiner/non-joiner characters; these orthographic characters
are preserved and are not classified as OCR defects.

All 39 MP3/MP4 files pass container/stream probing. Their combined 14:09:25.531
duration is **not Garhwali speech duration**. `ffprobe` does not reveal whether
media contains Garhwali, Hindi, Kumaoni, music, lecture, usable speech, or
reliable transcripts. Local ASR and language-identification runtimes were not
available during this pass, so neither transcript generation nor audio
language classification was performed.

## Recorded rights states

Every one of the 4,011 page records remains non-eligible for training and
public redistribution. Captured item-level license and rights fields are
source claims, not independent legal determinations. The 55-item register
records those claims, one conflicting metadata pair, and the per-work decision
in the [source disposition report](internet-archive-source-disposition-2026-10-04.md).

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
PYTHONPATH=scripts .venv/bin/python scripts/build_archive_source_disposition.py
```

The machine-readable outputs are under Git-ignored
`data/extracted/research/`:

- `internet_archive_quality_audit_2026-10-04.json`
- `internet_archive_corpus_overlap_2026-10-04.json`

The full acquisition ledger and source checksums are in the
[Internet Archive intake report](internet-archive-intake-2026-10-03.md). The
source-by-source decision register is in
[`internet-archive-source-disposition-2026-10-04.json`](internet-archive-source-disposition-2026-10-04.json)
and its [readable report](internet-archive-source-disposition-2026-10-04.md).
The extracted page/media candidate JSONL stays in Git-ignored
`data/extracted/research/internet_archive_candidate_views_2026-10-04/`.

The repository's full configured unittest suite passes **718/718** after these
audit changes. These checks validate the reproducible code path and data
contracts; they do not validate Garhwali language content or rights.
