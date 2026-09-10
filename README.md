<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-preserving research corpus and model-development pipeline for Garhwali (gbm).**

*Public sources, community material, historical texts, and speech in. Auditable
language resources, review queues, and reproducible model datasets out.*

[![python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![langgraph](https://img.shields.io/badge/orchestration-LangGraph-1C3C3C.svg)](PIPELINE.md)
[![tests](https://img.shields.io/badge/tests-84%20passing-success.svg)](research/language-quality-status-2026-09-10.md)
[![language](https://img.shields.io/badge/language-Garhwali%20%7C%20gbm-orange.svg)](https://glottolog.org/resource/languoid/id/gadh1239)

</div>

---

## 🎯 The project goal

Garhwali has valuable speech, vocabulary, folklore, scholarship, and community
writing spread across datasets, books, archives, websites, and local collections.
The lab turns those fragments into research-grade resources while retaining the
source, rights status, dialect evidence, quality flags, and transformation history
for every record.

The project keeps two views by design:

1. **A complete experimental view** containing approved, restricted, quarantine,
   and unresolved records so useful evidence is not silently discarded.
2. **Separated candidate views** for likely Garhwali, mixed-language material,
   non-Garhwali cultural context, and records requiring review.

The pipeline does not infer a dialect from a district name, treat a downloadable
page as automatically licensed, or silently correct a spelling variant. Those
decisions remain visible and reversible.

## ❤️ Why this lab exists

Garhwali is not just a language code or a list of translations. It lives in a
grandparent’s story, a song remembered at a wedding, a proverb used to make a
point, a word for a bird or a tool, a village pronunciation, and a speaker’s
ordinary conversation. Much of that knowledge is scattered across recordings,
old books, university lessons, community pages, archives, and people’s memories.

This lab brings those fragments together so Garhwali can be read, heard, studied,
and used in language technology without flattening it into one “correct” voice.
The purpose is practical and cultural at the same time: build useful ASR, text,
lexicon, and TTS resources; preserve dialect and genre variation; make sources
traceable; and give native speakers the final say over language quality.

The corpus is being built for the people who speak Garhwali, for researchers who
need evidence they can inspect, and for future tools that should understand the
language as it is actually used.

## 🎶 What the corpus carries

| Living part of Garhwali | What is represented now | Why it matters |
| --- | --- | --- |
| **Voices** | 110,436 VAANI recordings, 135.5 hours, 5,894 supervised transcripts, and speaker/district metadata | Speech gives models pronunciation, rhythm, variation, and everyday language that books cannot provide. |
| **Words in daily life** | 1,124 lexicon candidates; 666 thematic vocabulary records covering animals, birds, plants, food, tools, occupations, instruments, kinship, land, and ritual life; 99 idiom/proverb records | Local words carry the environment, work, humour, relationships, and worldview of Garhwal. |
| **Folklore, songs, and performance** | 370 OCR pages from Govind Chatak’s *Gadwali Lokgeet*; 298 pages from Shanti Chaudhary’s folk-art study; 592 UOU pages on folk songs, ballads, tales, literature, and theatre; 66 narrated folktale episodes catalogued | Songs and stories preserve memory, metaphor, history, and forms of speech that ordinary sentence datasets miss. |
| **Stories and cultural memory** | 440 pages from Upreti’s *Proverbs & Folklore*; 317 public-domain historical cultural-reference records; 50 Garhwali Open Bible Stories | Historical and translated narratives provide context, while their source and language status stay explicit. |
| **Community usage** | Learning pages, Reddit and YouTube records, social vocabulary, and web idioms with URLs and review flags | Community material captures living spellings and new usage, including Romanized and mixed-language forms. |

These materials do not all have the same status. Some are open and ready for
research use; some are restricted, rights-pending, experimental, or awaiting a
native-speaker decision. Keeping those differences visible is part of the work,
not a defect in the dataset.

## ✨ Current snapshot

- **30,088 source text records** from 35 files, deduplicated to **27,987 unique
  texts** and 7.39 million characters.
- **91,536 sentence-like occurrences** exposed from page-sized and long records,
  producing **86,215 exact-unique segments** with parent provenance retained.
- **110,436 VAANI Garhwali recordings** totaling **135.509 hours**; 5,894 have
  transcripts and 104,542 are queued for transcription.
- **363 identified speaker IDs**, with district, gender, and speaker-status fields
  preserved; current VAANI coverage is Uttarkashi and Tehri Garhwal.
- **25,343 likely Garhwali text candidates**, 1,468 source-declared mixed-language
  records, 859 unresolved records, and 317 non-Garhwali cultural-context records.
- **1,124 lexicon candidates**, 446 unique English–Garhwali pairs, and 1,187
  grammar-source candidates.
- **84 automated tests** and **365 immutable source snapshots** verified.

These figures describe the preparation snapshot generated on 2026-09-10. Raw
downloads, VAANI audio, generated JSONL, caches, and model artifacts stay outside
Git through `.gitignore`.

## 📈 Corpus scale

<div align="center">

| `~30 GB` | `110,436` | `135.5 h` | `27,987` |
| --- | ---: | ---: | ---: |
| local VAANI audio | recordings | audio duration | unique text lines |

| `7.39M` | `1.44M` | `86,215` | `1,124` |
| ---: | ---: | ---: | ---: |
| text characters | whitespace tokens* | unique segments | lexicon candidates |

| `446` | `1,187` | `5,894` | `104,542` |
| ---: | ---: | ---: | ---: |
| English–Garhwali pairs | grammar-source candidates | supervised transcripts | untranscribed clips |

</div>

The storage figure is the measured local VAANI directory size; processed views add
about 1.4 GB. *Whitespace tokens are an engineering count from the canonical text
view, not a linguistic tokenization.*

## 🧱 How the pipeline fits together

```text
 VAANI / Hugging Face / web pages / books / archives / community sources
                              │
                              ▼
       bounded acquisition + raw snapshot + checksum + rights metadata
                              │
                              ▼
       canonical text/audio manifests + exact SHA-256 deduplication
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
   reversible text cleanup              WAV signal audit
   OCR and markup flags                 RMS, peak, DC, clipping
             │                                 │
             └────────────────┬────────────────┘
                              ▼
       sentence segmentation + language/script/genre/dialect/speaker tags
                              │
             ┌────────────────┴────────────────┐
             ▼                                 ▼
     native-review queues                 model-ready exports
     language and dialect                 LM / ASR / TTS / lexicon
                              │
                              ▼
       speaker-safe splits + evaluation + provenance and release manifest
```

The deterministic collectors own source acquisition and extraction. LangGraph
coordinates resumable waves, retries transient network failures, and checkpoints
progress in the ignored cache. See [`PIPELINE.md`](PIPELINE.md).

## 📚 Data layers

| Layer | Purpose | Typical contents |
| --- | --- | --- |
| `corpus/` | Open or source-licensed text | ASJP, Tatoeba, Meta Omnilingual, Wikimedia, numerals, localization |
| `benchmarks/` | Evaluation-only material | IndicGenBench Flores, XorQA, Crosssum |
| `restricted/` | Useful data with limited or non-commercial terms | UOU OCR, Open Bible Stories, PanLex, thematic vocabulary |
| `quarantine/` | Experimental or unresolved rights/quality | PahariLI, Indic Dialect ASR, web documents, community datasets |
| `extracted/historical/` | Historical OCR and structured linguistic evidence | LSI, Upreti, Kellogg, Walton, historical folklore |
| `data/vaani/` | Local VAANI metadata, audio, images, and manifests | Git-ignored; never commit raw audio or cache files |
| `data/processed/` | Generated canonical, cleaned, tagged, segmented, and model views | Git-ignored JSONL and reports |
| `research/` | Source audits, gap plans, reports, and decisions | Human-readable provenance and limitations |

The complete source inventory is [`sources/online/deep-search-catalog.md`](sources/online/deep-search-catalog.md).
The catalog records sources that were inspected but not promoted, including blocked,
gated, mirrored, copyrighted, and permission-dependent material.

## 🚀 Quickstart

### Install the reproducible pipeline

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pipeline.txt
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
```

### Rebuild the prepared text and audio views

```bash
.venv/bin/python scripts/prepare_text_corpus.py
.venv/bin/python scripts/build_all_data_view.py
.venv/bin/python scripts/clean_text_corpus.py
.venv/bin/python scripts/prepare_vaani_supervised.py
.venv/bin/python scripts/build_audio_training_manifests.py
.venv/bin/python scripts/prepare_transcripts.py
.venv/bin/python scripts/deep_cleanup.py
.venv/bin/python scripts/audit_audio_quality.py --untranscribed data/processed/vaani/untranscribed.jsonl
.venv/bin/python scripts/prepare_audio_normalization.py
.venv/bin/python scripts/segment_text_corpus.py
.venv/bin/python scripts/tag_language_quality.py
.venv/bin/python scripts/build_review_queues.py
.venv/bin/python scripts/build_release_manifest.py
```

### Use the checkpointed ingestion graph

```bash
.venv/bin/python scripts/ingestion_graph.py run --wave ninth --run-id thematic-vocabulary-2026-09-09
.venv/bin/python scripts/ingestion_graph.py status --run-id thematic-vocabulary-2026-09-09
.venv/bin/python scripts/ingestion_graph.py resume --run-id thematic-vocabulary-2026-09-09
```

The graph retries HTTP 429 and transient 5xx, timeout, and connection-reset
failures. Confirmed 403, 404, schema, and rights failures remain documented rather
than being bypassed.

## 🔬 Quality and review

The language-quality pass attaches conservative labels to every prepared text and
VAANI utterance:

- Unicode script profile: Devanagari, Latin transliteration, Bengali, mixed, or
  unsupported script;
- source-backed language identity and confidence;
- explicit genre plus narrow fallback rules for older extractions;
- explicit dialect labels kept separate from district geography;
- speaker identification, gender, language-known, and coverage metadata;
- lexicon, parallel-example, and grammar-source candidate views.

The rules intentionally do not decide Hindi versus Garhwali from shared
Devanagari vocabulary. Review queues are in `data/processed/review/` and the full
analysis is in [`research/language-quality-status-2026-09-10.md`](research/language-quality-status-2026-09-10.md).

## 🗺️ Full development plan

Effort labels describe the expected engineering and review effort: **Low** is a
small deterministic change, **Medium** is a contained pipeline task, **High** is a
multi-source or model-preparation task, and **Xhigh** requires substantial compute,
OCR, transcription, or native-speaker review.

### 1. Data finalization — High

- [x] Merge approved and experimental views.
- [x] Preserve source, rights, quality, and dialect metadata.
- [x] Deduplicate across all layers.
- [ ] Freeze a named corpus release after native review and rights decisions.

### 2. Text cleanup — Xhigh

- [x] Normalize Unicode and whitespace.
- [x] Remove empty and malformed records.
- [x] Strip recoverable markup, speech annotations, and truncation markers into
  reversible cleaned fields.
- [x] Segment page-sized and long text into sentence-like units.
- [ ] Correct OCR errors with page-level provenance.
- [ ] Native-speaker review of spelling, meaning, and dialect variants.

### 3. Audio cleanup — High

- [x] Audit all VAANI WAV headers and signal metrics.
- [x] Identify clipped, quiet, loud, DC-offset, and projected-clipping files.
- [x] Generate normalization recommendations and training manifests.
- [ ] Apply reviewed loudness and DC correction to derived audio copies.
- [ ] Segment any future long-form recordings.

### 4. Transcript improvement — Xhigh

- [x] Reconcile the main VAANI and transcription-part repositories.
- [x] Review and quarantine Bengali-script and annotated transcript rows.
- [x] Create a 105-batch queue for untranscribed VAANI audio.
- [ ] Transcribe the 104,542 unlabelled recordings.
- [ ] Align reviewed transcripts to audio and retain alignment confidence.
- [ ] Add native-speaker transcript acceptance and correction decisions.

### 5. Language quality — High

- [x] Tag script, source-backed language identity, genre, and speaker metadata.
- [x] Separate likely Garhwali, mixed-language, context, and unresolved views.
- [x] Preserve explicit dialect labels and geographic hints independently.
- [x] Build vocabulary, English–Garhwali, and grammar-source candidates.
- [ ] Native-review language identity and Romanized spelling.
- [ ] Add dialect labels across the prioritized review queue.

### 6. Dataset splits — High

- [x] Preserve official VAANI train/validation/test partitions.
- [x] Verify no identified VAANI speaker crosses official partitions.
- [x] Create a complete experimental all-data view.
- [x] Prevent exact duplicate segments from receiving different provisional segment
  hashes.
- [ ] Resolve the 332 cross-document segment conflicts with connected-component,
  document-aware splitting.
- [ ] Publish immutable speaker-disjoint text, ASR, TTS, and evaluation splits.

### 7. Pipeline engineering — Medium

- [x] Add reproducible ingestion and preparation commands.
- [x] Add LangGraph checkpoints, retry policies, and resumable runs.
- [x] Add source hashes, provenance, validation, deduplication, and release reports.
- [x] Keep raw data, caches, generated datasets, and audio ignored by Git.
- [ ] Add scheduled freshness checks for source pages and dataset revisions.
- [ ] Add CI that runs the test suite and validates release-manifest counts.

### 8. Model preparation — High

- [x] Export cleaned text and sentence segments.
- [x] Export ASR supervised and untranscribed manifests.
- [x] Export lexicon and parallel-example candidates.
- [x] Run and document a zero-shot ASR baseline.
- [ ] Build a Garhwali language model/tokenizer resource.
- [ ] Build pronunciation and grapheme-to-phoneme resources.
- [ ] Prepare TTS text/audio pairs after transcript and speaker review.
- [ ] Fine-tune and evaluate Garhwali ASR using speaker-safe splits.

### 9. Testing and review — High

- [x] Run unit tests and data-quality checks.
- [x] Audit licensing, attribution, source hashes, and unresolved rights.
- [x] Track unresolved language, dialect, OCR, audio, and transcript records.
- [x] Verify source snapshots and release-manifest line counts.
- [ ] Conduct two-pass native-speaker review for evaluation and lexicon data.
- [ ] Freeze a held-out native evaluation set before model tuning.

### 10. Release — Medium

- [ ] Create the first GitHub checkpoint commit and push it to the project remote.
- [x] Keep raw sources, caches, large datasets, and audio out of Git.
- [x] Publish preparation, source, folklore, social-media, VAANI, and language-
  quality documentation.
- [x] Generate a versioned local release manifest.
- [ ] Choose and document the final redistribution and model-use policy.
- [ ] Publish a dataset card with license matrix, attribution, consent scope,
  exclusions, review status, and reproducibility commands.

## 🧭 The broader collection and research plan

The full project continues beyond the current snapshot:

1. **Finish VAANI’s value:** transcribe representative batches first, balance
   Uttarkashi and Tehri Garhwal, review speaker metadata, and then expand to the
   full untranscribed queue.
2. **Native-led language review:** recruit reviewers from multiple Garhwali
   regions; record accepted form, alternative form, gloss, example, dialect,
   reviewer ID, timestamp, and disagreement resolution.
3. **Dialect coverage:** add consensual recordings and vocabulary from additional
   districts, ages, genders, and speaking contexts. Never infer a dialect solely
   from residence.
4. **Licensed dictionary work:** request a versioned Garhwali-only HimLingo export
   with contributor consent and explicit redistribution/model-training rights.
5. **Archives and books:** obtain permission or verify public-domain status for
   historical periodicals, folk literature, grammars, plays, novels, and local
   stories; OCR page by page and keep original and corrected text separate.
6. **Community speech:** collect prompted speech, natural conversation, stories,
   songs, jagar, mangal, theatre, and procedural explanations with consent and
   performer/speaker rights recorded separately.
7. **Model baselines:** train a tokenizer, language model, ASR model, and TTS
   baseline only after the split and review gates are frozen.
8. **Public release:** publish only the subset whose source terms, consent,
   attribution, and review state support the selected use; retain an auditable
   internal experimental view for research decisions.

The detailed gap plan is [`research/gap-closure-plan.md`](research/gap-closure-plan.md),
and the known access blockers are [`research/garhwali-access-blockers-2026-09-10.md`](research/garhwali-access-blockers-2026-09-10.md).

## 🧪 Verification commands

```bash
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
.venv/bin/python scripts/dedup_report.py
.venv/bin/python scripts/verify_ingestion.py
git diff --check
```

The current local verification result is **84 passing tests**, **365 source
snapshots verified**, and zero release-manifest count mismatches.

## 🤝 Contributing

Contributions should preserve the record’s source URL, raw snapshot hash, license
or rights status, attribution, language scope, quality flags, and transformation
steps. Add a focused failing test before changing a collector or quality rule.
Do not commit credentials, Hugging Face caches, raw audio, PDFs, generated JSONL,
or private speaker information. New source families belong in the source catalog
even when they are discovered but cannot yet be promoted.

## ⚖️ Data and ethics

The project owner has directed the lab to retain quarantine and restricted material
for experimental research. That instruction is represented by the all-data view and
explicit `usage`/`rights_status` fields. It does not erase the original source
terms or make an unresolved source suitable for public redistribution. A public
release must carry its own license matrix, attribution, consent scope, and
exclusion policy.

The lab is designed to support Garhwali speakers and researchers: preserve variants,
credit contributors, protect personal information, and let native reviewers correct
the system before a model is treated as authoritative.
