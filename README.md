<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-preserving research corpus and model-development pipeline for Garhwali (gbm).**

*Public sources, community material, historical texts, and speech in. Auditable
language resources, review queues, and reproducible model datasets out.*

[![python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![langgraph](https://img.shields.io/badge/orchestration-LangGraph-1C3C3C.svg)](PIPELINE.md)
[![tests](https://img.shields.io/badge/tests-432%20passing-success.svg)](research/corpus-preparation-status.md)
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

1. **A complete experimental view** containing every collected record, including
   restricted and unresolved material, so useful evidence is not silently discarded.
2. **Separated candidate views** for likely Garhwali, mixed-language material,
   non-Garhwali cultural context, and records requiring review.

The pipeline does not infer a dialect from a district name, treat a downloadable
page as automatically licensed, or silently correct a spelling variant. Those
decisions remain visible and reversible.

## 🧭 North star

> **Build an open, reproducible, dialect-aware, and native-validated foundation
> for Garhwali language technology, spanning corpus construction, evaluation,
> language modeling, translation, speech, and retrieval, while experimentally
> determining what works when data is extremely scarce.**

The finished contribution is a research platform rather than a single model:

```text
Garhwali Language Lab
├── GarhwaliCorpus       rights-cleared, versioned, provenance-preserving data
├── GarhwaliBench        strict automated candidate; native/dialect review pending
├── Research Suite       tokenizer, quality, transfer, scaling, and ablations
├── Garhwali Models      LM, translation, retrieval, ASR, and TTS baselines
├── Community Layer      transcription, correction, and dialect contribution
├── Garhwali API         search, lexicon, normalization, culture, and model access
└── Public Infrastructure
                         datasets, model cards, leaderboard, explorer, and demos
```

This direction reflects the current field. [SraVaani 1.0](https://vaani.iisc.ac.in/models/sravaani)
supports Garhwali in a 65-language ASR model and reaches 42.761% WER / 17.606%
CER on this lab's fixed 112-record comparison. A
[2026 VarDial study](https://aclanthology.org/2026.vardial-1.12/) directly examines
Garhwali ASR transfer and pretraining-language bias. Garhwali also appears in
[IndicGenBench](https://aclanthology.org/2024.acl-long.595/). The lab therefore
uses ASR as one controlled research track and places equal weight on corpus
quality, native evaluation, translation, dialect robustness, and retrieval.

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
| **Words in daily life** | 1,114 lexicon candidates; 666 thematic vocabulary records covering animals, birds, plants, food, tools, occupations, instruments, kinship, land, and ritual life; 99 idiom/proverb records | Local words carry the environment, work, humour, relationships, and worldview of Garhwal. |
| **Poetry, plays, and performance** | 370 OCR pages from Govind Chatak’s *Gadwali Lokgeet*; 298 pages from Shanti Chaudhary’s folk-art study; 592 UOU pages on poetry, prose, folk songs, ballads, tales, literature, and theatre; 66 narrated folktale episodes; 30 famous and classic song metadata records; 66 named literary, periodical, linguistic, and language-resource works; 26 named writers, historians, translators, and playwrights | Songs, poems, and plays preserve memory, metaphor, history, and forms of speech that ordinary sentence datasets miss. |
| **Stories and cultural memory** | 440 pages from Upreti’s *Proverbs & Folklore*; 317 public-domain historical cultural-reference records; 50 Garhwali Open Bible Stories | Historical and translated narratives provide context, while their source and language status stay explicit. |
| **Community usage** | Learning pages, Reddit and YouTube records, social vocabulary, and web idioms with URLs and review flags | Community material captures living spellings and new usage, including Romanized and mixed-language forms. |
| **Places and landscape** | 50 Garhwal place and feature records: 36 settlements plus 14 rivers, peaks, parks, protected areas, reservoirs, and pilgrimage sites, with Hindi names and map/Wikipedia pointers | Geography grounds place-based vocabulary, migration references, folklore, songs, and dialect evidence without turning a district into a dialect label. |
| **History and historical terms** | 36 historical terms across 25 categories: old region names, kingdoms, capitals, dynasties, administrative and labour institutions, political events, movements, military and ritual traditions | Historical vocabulary lets models interpret references in songs, folklore, poetry, plays, and place narratives while keeping period and source context attached. |
| **University and research record** | 8 deduplicated institutional records from HNBGU, Doon University, UOU, SGRR University, the University of Kashmir, TUFS, and the University of Burdwan, spanning theses, curricula, syntax, ergativity, folklore, idioms, and proverbs | Scholarship supplies linguistic analysis and an acquisition map without pretending that a catalogue entry contains a complete book or thesis. |

These materials do not all have the same status. Some are open and ready for
research use; some are restricted, rights-pending, experimental, or awaiting a
native-speaker decision. Keeping those differences visible is part of the work,
not a defect in the dataset.

## ✨ Current snapshot

See [`finalreport.md`](finalreport.md) for the current release decision, verified
counts, audit gaps, and remaining work.

- **31,094 source text records** from 42 files, deduplicated to **28,755 unique
  texts** and 9,145,955 characters.
- **119,679 sentence-like occurrences** exposed from page-sized and long records,
  producing **114,064 exact-unique segments** with parent provenance retained.
- **769 active page records from six newly supplied PDFs**, including two
  dictionaries, grammar and syntax research, literature, and cultural material;
  one exact duplicate PDF reuses its existing 370-record extraction.
- **110,436 VAANI Garhwali recordings** totaling **135.509 hours**; 5,894 have
  human transcripts and all 104,542 previously untranscribed rows now have
  revision-pinned SraVaani experimental drafts.
- **363 identified speaker IDs**, with district, gender, and speaker-status fields
  preserved; current VAANI coverage is Uttarkashi and Tehri Garhwal.
- **25,341 likely Garhwali text candidates**, 2,237 mixed-language
  records, 860 review records, and 317 non-Garhwali cultural-context records.
- **4,195 exact-unique texts with a public rights basis**, including 3,559 strict
  public candidates; 1,748 additional high-quality candidates remain active with
  rights-pending provenance.
- **1,913 mixed-rights exact duplicates** retain every source warning; 1,906
  strict records are publishable through a separately retained open copy.
- **1,114 structured lexicon candidates**, 455 parallel examples, and 1,187
  grammar-source candidates.
- **66 named works and 26 literary people** are now visible in deduplicated
  catalogs; uncertain spellings and the `Khigtaat` attribution conflict remain
  explicit instead of being silently merged.
- **8 university and research records** preserve institution, access level,
  topics, and deduplication status; the existing UOU materials are linked rather
  than ingested twice.
- **257,807 local all-data rows** span text, human and machine speech
  transcripts, lexicon, instructions, and six structured knowledge
  configurations. The rights-filtered public package contains **146,684
  rows** and omits 216 structured records without compatible public-rights evidence.
- **2,002 strict speaker-identified ASR/TTS candidates** across 248 speakers,
  totaling 3.562 hours with zero identified-speaker split leakage.
- **1,736 normalized derived WAVs** rendered from unflagged strict candidates;
  **266 peak-safe flagged copies** retain their signal metadata and are active in
  the complete experimental view.
- **1,204 clips / 8.93 hours** derived from 66 archived Garhwali folktale
  episodes, with source rights and review gates retained.
- **Speaker-safe ASR comparison:** SraVaani leads at 0.428 WER / 0.176 CER,
  ahead of the controlled Whisper-tiny fine-tune at 0.743 / 0.404 on the same
  112 recordings.
- **GarhwaliBench v0.1 candidate:** 3,847 external task records, 398 strict
  automated held-out text segments, and 112 speaker-safe ASR rows, with zero
  measured training overlap. It is not yet native-reviewed or dialect-aware.
- **Current character bigram floor:** 17.000058 held-out perplexity and zero
  observed character OOV on the 398-record candidate benchmark.
- **Multilingual tokenizer audit:** IndicBERTv2 leads five candidates at 1.532
  tokens per Garhwali word; the Garhwali OpenLLaMA adapter tokenizer needs 5.327.
- **IndicBERTv2 baseline:** 17.79% masked-token accuracy on 506 deterministic
  masks from 128 held-out records, with no truncation.
- **Controlled continuation:** a 1,024-step, three-seed IndicBERTv2 LoRA run
  lowers mean validation cross-entropy from 6.678 to 5.624.
- **Instruction resource:** 3,230 split-safe Garhwali translation and lexicon
  instructions; a first three-seed mT5 LoRA baseline improves validation
  loss but remains unfit for generation.
- **Accuracy continuation:** mT0-small reaches **4.961989** mean validation and
  **5.019603** mean new-test cross-entropy after 256-step three-seed LoRA; all
  seeds improve the held-out loss, while exact-match generation remains 0%.
- **104,542 SraVaani machine drafts** cover 104,534 unique recordings. Automated
  quality analysis marks 103,354 standard and 1,188 flagged rows. A cross-layer
  audit links 98 flagged drafts and 8 human transcripts to one repeated Bengali-
  script source-label conflict; all 106 records remain visible for source analysis.
- **65,000 independent Whisper-large-v3-turbo checks** are attached to the
  corresponding machine drafts as evidence, including 157 exact agreements;
  no source or machine transcript was overwritten.
- **659 incoming PDF pages** completed four-layout OCR comparison. The process
  retained 69 reversible same-engine layout-consensus variants beside each
  original OCR value, page identity, source hash, and confidence signal. These
  variants are not human-validated corrections.
- **1,188 confidence-scored recovery alternatives** are integrated beside their
  immutable SraVaani originals: 30 medium, 35 low, and 1,123 very-low review
  confidence, with no quarantine or automatic promotion.
- **1,090 three-checkpoint review records** now compare SraVaani and two local
  Garhwali Whisper checkpoints. The pass yields 325 clean related-checkpoint
  consensus proposals, 730 clean low-consensus proposals, and 35 structurally
  unresolved records; every original remains preserved and none is promoted to
  human ground truth.
- **35 audio-grounded outlier reviews** add deterministic re-decoding, calibrated
  score percentiles, and waveform activity: 11 common short-form spot checks,
  17 decoder loops, three decoding corruptions, one empty output, and three other
  unresolved cases. Machine review is complete; listening remains required.
- **106,057-row confidence-aware ASR curriculum:** 1,621 human references plus
  104,436 machine-labelled recordings; the 98 source-conflict drafts remain in
  the dataset but contribute no Garhwali training loss.
- **Full curriculum trainer dry run:** all 106,057 training rows and 269
  validation rows resolve to local audio, with zero empty targets, duplicate
  training hashes, or missing files and 3,241.999996 total effective loss mass.
- **Stage-0 checkpoint:** the stronger human-only Whisper-tiny `v0.2` scores
  0.781 WER / 0.463 CER on all 269 validation rows and is registered for stage 1
  without copying its weights; SraVaani remains ahead at 0.434 / 0.189.
- **Stage-1 pilot:** a bounded 32-human + 2,048-machine-label run completed all
  2,080 updates, but validation WER rose from 0.780522 to 0.784137 and CER from
  0.462980 to 0.463038. The configuration was rejected and stage 2 remains locked.
- **Weighted-batch ablation:** the same examples were regrouped into 32 normalized
  65-record human/machine updates. WER rose further to 0.788153 and CER to
  0.463672, so the current machine-label curriculum recipe is closed.
- **SraVaani adaptation package:** 2,002 human-reference clips are packaged into
  deterministic NeMo train, validation, and held-out test archives totaling
  412,037,120 bytes, with all audio hashes verified and zero split leakage.
- **SraVaani adaptation result:** the 102-step human-reference run scores 43.528%
  WER / 17.452% CER on the frozen 112-record test. Original SraVaani remains
  preferred at 42.761% / 17.606% because WER is the primary metric.
- **432 automated tests** and **367 immutable source snapshots** verified, with 43 public source URLs covered
  by a scheduled freshness audit.

These figures describe the preparation snapshot updated on 2026-09-23. Raw
downloads, VAANI audio, generated JSONL, caches, and model artifacts stay outside
Git through `.gitignore`.

## 📈 Corpus scale

<div align="center">

| `~34 GB` | `110,436` | `135.5 h` | `28,755` |
| --- | ---: | ---: | ---: |
| local corpus data | recordings | audio duration | unique text lines |

| `9.15M` | `1.76M` | `114,064` | `1,114` |
| ---: | ---: | ---: | ---: |
| text characters | whitespace tokens* | unique segments | lexicon candidates |

| `455` | `1,187` | `5,894` | `104,542` |
| ---: | ---: | ---: | ---: |
| English–Garhwali pairs | grammar-source candidates | supervised transcripts | untranscribed clips |

| `257,807` | `146,684` | `216` | `435` |
| ---: | ---: | ---: | ---: |
| all-data package rows | rights-filtered public rows | local structured records | passing tests |

</div>

The storage figure combines the measured 30.1 GiB VAANI directory, 3.1 GiB of
processed views, and about 0.3 GiB of downloads. *Whitespace tokens are an engineering count
from the canonical text view, not a linguistic tokenization.*

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
| `restricted/` | Source layer with limited/non-commercial or component-review terms; included in the complete local all-data research package, not cleared for public redistribution | UOU OCR, Open Bible Stories, PanLex, thematic vocabulary |
| `experimental/` | Active local data with unresolved rights or quality signals | PahariLI, Indic Dialect ASR, web documents, community datasets |
| `extracted/historical/` | Historical OCR and structured linguistic evidence | LSI, Upreti, Kellogg, Walton, historical folklore |
| `data/vaani/` | Local VAANI metadata, audio, images, and manifests | Git-ignored; never commit raw audio or cache files |
| `data/processed/` | Generated canonical, cleaned, tagged, segmented, and model views | Git-ignored JSONL and reports |
| `research/` | Source audits, gap plans, reports, and decisions | Human-readable provenance and limitations |

The complete source inventory is [`sources/online/deep-search-catalog.md`](sources/online/deep-search-catalog.md). The current workspace scan found no directory or package configuration named quarantine, hold, or unusable. All 1,450 nonempty text rows in the ignored `restricted/` input layer match canonical corpus content by normalized hash; the all-data text split retains 16,375 segments with restricted-source provenance. These source files remain Git-ignored and are not uploaded anywhere; the public profile still fails its rights gate.
The catalog records sources that were inspected but not promoted, including blocked,
gated, mirrored, copyrighted, and permission-dependent material.

## 🚀 Quickstart

### Install the reproducible pipeline

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pipeline.txt
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
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
PYTHONPATH=scripts .venv/bin/python scripts/analyze_sravaani_drafts.py
.venv/bin/python scripts/audit_audio_quality.py --untranscribed data/processed/vaani/untranscribed.jsonl
.venv/bin/python scripts/prepare_audio_normalization.py
.venv/bin/python scripts/render_normalized_audio.py --render-flagged-review
.venv/bin/python scripts/segment_text_corpus.py
.venv/bin/python scripts/tag_language_quality.py
.venv/bin/python scripts/build_dataset_splits.py
.venv/bin/python scripts/build_language_resources.py
.venv/bin/python scripts/build_garhwali_benchmark.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/audit_multilingual_tokenizers.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_masked_lm_baseline.py
.venv/bin/python scripts/run_translation_baseline.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_nllb_translation_baseline.py --max-records 32 --max-new-tokens 64 --device cpu
.venv/bin/python scripts/run_retrieval_baseline.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_indicbert_retrieval_baseline.py --max-records 0 --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --device cpu
.venv/bin/python scripts/build_review_queues.py
.venv/bin/python scripts/native_review_workflow.py
.venv/bin/python scripts/segment_long_audio.py
.venv/bin/python scripts/build_release_manifest.py
.venv/bin/python scripts/validate_release_index.py
```

ASR experiments use the separately pinned `requirements-asr.txt`. Generated
checkpoints and review-only machine drafts remain Git-ignored:

```bash
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/train_whisper_garhwali.py --device mps
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/transcribe_vaani_drafts.py --device mps --max-records 100
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
Devanagari vocabulary. Optional diagnostic queues are in `data/processed/review/`;
they do not block any record from the complete experimental datasets. The full
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
- [x] Freeze a checksum-addressed integrated experimental release.
- [x] Keep public-redistribution rights separate from local experimental use.

### 2. Text cleanup — Xhigh

- [x] Normalize Unicode and whitespace.
- [x] Remove empty and malformed records.
- [x] Strip recoverable markup, speech annotations, and truncation markers into
  reversible cleaned fields.
- [x] Segment page-sized and long text into sentence-like units.
- [x] Apply deterministic OCR cleanup while retaining page provenance and flags.
- [x] Keep spelling, meaning, and dialect uncertainty as metadata rather than a
  data exclusion gate; later native corrections can be merged non-destructively.
- [x] Score 4,096 priority texts with pinned IndicBERTv2 and attach reversible
  OCR, spelling, language-ambiguity, and dialect-evidence proposals to all 28,755
  parent texts without excluding or overwriting any record.
- [x] Ablate mechanical and bulk spelling variants on the fixed document split;
  neither variant was promoted into canonical text.

### 3. Audio cleanup — High

- [x] Audit all VAANI WAV headers and signal metrics.
- [x] Identify clipped, quiet, loud, DC-offset, and projected-clipping files.
- [x] Generate normalization recommendations and training manifests.
- [x] Render normalized derived copies for 1,736 unflagged strict ASR/TTS files;
  source VAANI audio remains unchanged.
- [x] Render peak-safe copies for all 266 flagged strict files and retain their
  signal flags in the active experimental manifests.
- [x] Audit the broader 4,112-record signal set automatically and preserve its
  measurements for filtering or ablation experiments.
- [x] Segment all 66 locally archived folktale episodes into 1,204 clips / 8.93
  hours; retain creator-copyright and transcript-review gates.

### 4. Transcript improvement — Xhigh

- [x] Reconcile the main VAANI and transcription-part repositories.
- [x] Flag Bengali-script and annotated transcript rows while retaining them in
  the active experimental corpus.
- [x] Create a 105-batch queue for untranscribed VAANI audio.
- [x] Fine-tune a speaker-safe Whisper baseline and implement resumable,
  confidence-bearing, review-only draft transcription.
- [x] Run a 100-record end-to-end draft pilot and expose every draft as a noisy
  experimental label with its confidence retained.
- [x] Transcribe all 104,542 unlabelled source rows with pinned SraVaani 1.0,
  covering 104,534 unique audio hashes with zero missing recordings.
- [x] Attach reversible script, repetition, duration-rate, and repeated-hypothesis
  quality signals while keeping every draft active experimentally.
- [x] Activate all 104,542 unlabelled recordings for audio-only learning and place
  them in 105 resumable automatic-transcription batches.
- [x] Align every available transcript to its audio identity and retain transcript,
  language, and signal confidence fields.
- [x] Add a two-pass transcript acceptance, correction, disagreement, and
  materialization workflow.
- [x] Make later native corrections optional, versioned improvements rather than
  a requirement placed on the project owner.

### 5. Language quality — High

- [x] Tag script, source-backed language identity, genre, and speaker metadata.
- [x] Separate likely Garhwali, mixed-language, context, and unresolved views.
- [x] Preserve explicit dialect labels and geographic hints independently.
- [x] Build vocabulary, English–Garhwali, and grammar-source candidates.
- [x] Retain confidence and Romanized-spelling uncertainty on 18,462 records while
  keeping all records active experimentally.
- [x] Preserve explicit dialect evidence and leave unknown dialects unknown rather
  than excluding 10,873 prioritized records.

### 6. Dataset splits — High

- [x] Preserve official VAANI train/validation/test partitions.
- [x] Verify no identified VAANI speaker crosses official partitions.
- [x] Create a complete experimental all-data view.
- [x] Prevent exact duplicate segments from receiving different provisional segment
  hashes.
- [x] Resolve all 332 cross-document segment conflicts with connected-component,
  document-aware splitting; zero exact segments now cross splits.
- [x] Publish deterministic document-aware text splits and preserve the official
  speaker-disjoint VAANI ASR partitions.
- [x] Publish strict ASR/TTS candidate splits for 2,002 clean rows from 248
  identified speakers; placeholder-speaker rows remain in the broader manifests.
- [x] Freeze checksum-addressed, automatically screened text and ASR evaluation
  candidates with zero measured split leakage.

See the [`dataset split status`](research/dataset-splits-2026-09-10.md) for exact
selection rules, exclusions, counts, and leakage checks.

### 7. Pipeline engineering — Medium

- [x] Add reproducible ingestion and preparation commands.
- [x] Add LangGraph checkpoints, retry policies, and resumable runs.
- [x] Add source hashes, provenance, validation, deduplication, and release reports.
- [x] Keep raw data, caches, generated datasets, and audio ignored by Git.
- [x] Add scheduled freshness checks for source pages and dataset revisions.
- [x] Add CI that runs the test suite and validates release-manifest counts.

### 8. Model preparation — High

- [x] Export cleaned text and sentence segments.
- [x] Export ASR supervised and untranscribed manifests.
- [x] Export lexicon and parallel-example candidates.
- [x] Run and document a zero-shot ASR baseline.
- [x] Build a 332-symbol Unicode tokenizer resource from train-only text.
- [x] Build 1,114 pronunciation candidates, including 293 with source phonetic
  evidence; native pronunciation validation remains pending.
- [x] Prepare 1,736 normalized, speaker-safe TTS candidate pairs; public TTS use
  remains gated on transcript review and voice consent.
- [x] Fine-tune and evaluate a Garhwali Whisper baseline on speaker-safe splits;
  the best controlled run scores 0.743 WER / 0.404 CER and remains experimental.
- [x] Build GarhwaliBench v0.1 and run a dependency-free character-language-model
  baseline with explicit contamination checks.
- [x] Audit five pinned multilingual tokenizers and run the first full
  IndicBERTv2 masked-language baseline.
- [x] Establish Garhwali-to-English translation floors on all 1,012 FLORES test
  pairs and compare pinned base NLLB with a community Garhwali adapter on the
  same deterministic 32-record pilot.
- [x] Establish XORQA passage-retrieval floors on all 1,039 dev/test questions
  and evaluate pinned IndicBERTv2 semantic retrieval on all 539 test questions.
- [x] Compare zero-shot Whisper-tiny, zero-shot Whisper-small, and both local
  fine-tuned checkpoints on the identical 112-row speaker-safe test set.
- [x] Build 3,230 provenance-preserving instruction records with parent- and prompt-disjoint
  splits and run three-seed mT5 LoRA instruction tuning.
- [x] Extend IndicBERTv2 LoRA continuation to 1,024 steps per seed and evaluate
  the full instruction-tuning seed set after validation selection.
- [x] Build a five-stage, confidence-weighted ASR curriculum that retains every
  unique machine-labelled recording while capping total machine loss mass at the
  human-reference training mass.
- [x] Teach the Whisper trainer to select curriculum stages, optimize weighted
  per-record loss, verify predecessor checkpoints, and run without model
  dependencies in validation-only mode.
- [x] Verify the existing human-only checkpoints against the exact stage-0 data,
  select `v0.2` on all 269 validation records, and register it as the stage-1
  predecessor without duplicating model weights.
- [x] Run a bounded stage-1 machine-label pilot, verify all 269 saved predictions,
  and reject the configuration after both validation WER and CER worsened.
- [x] Replace nominal one-record weighting with stratified normalized gradient
  accumulation, repeat the fixed pilot, and reject it after accuracy worsened.
- [x] Package all strict human-reference speech for official SraVaani NeMo
  adaptation and add a CUDA-guarded decoder/joint training launcher.
- [x] Complete and evaluate the 102-step SraVaani adaptation pilot. Hugging Face Job
  [`6aa9e33af76d6a098a70ec01`](https://huggingface.co/jobs/rushilrawat/6aa9e33af76d6a098a70ec01)
  produced a valid checkpoint; the closed test scores 43.528% WER / 17.452% CER.
  Its higher WER keeps the original SraVaani checkpoint preferred.

### 9. Testing and review — High

- [x] Run unit tests and data-quality checks.
- [x] Audit licensing, attribution, source hashes, and unresolved rights.
- [x] Track unresolved language, dialect, OCR, audio, and transcript records.
- [x] Verify source snapshots and release-manifest line counts.
- [x] Provide a two-pass native-review workflow and ready-to-fill packets. Native
  decisions remain absent, so the benchmark is still an automated candidate and
  the release is not represented as native-validated.
- [x] Package all 176 remaining text-accuracy cases and all 113 transcript-review
  cases as JSONL plus flat two-reviewer CSV templates; include English alignments
  for 172 Translatewiki rows and two model hypotheses for five ambiguous human
  transcripts.
- [x] Freeze held-out, automatically screened evaluation candidates before tuning.
- [x] Add an intensive evidence-based quality gate across all text, supervised
  speech, and SraVaani drafts; preserve every value and attach explicit tier reasons.
- [x] Refine all 3,735 public Garhwali text candidates with genre-aware surface
  checks; preserve originals, remove seven unambiguous markup residues, normalize
  29 double-period pause markers, and yield 3,559 strict public candidates.
- [x] Replace the coarse public-text confidence queue with separate language,
  orthography, alignment, source, and surface evidence; rank all 176 unresolved
  records without discarding or guessing any value.
- [x] Audit all 28,755 exact-unique texts by source; restore lost license IDs,
  normalize rights-warning syntax, and attach an explicit public rights basis to
  1,913 mixed-rights exact duplicates without dropping blocked provenance.
- [x] Replace 56 flattened Wiktionary page blobs with 77 structured Garhwali
  lemmas, alternative forms, and examples; remove MediaWiki scaffolding from
  cached Wikimedia sources and recognize 392 source-attested linguistic
  transcriptions without inventing Devanagari spellings.
- [x] Re-decode all five ambiguous human transcripts with the two strongest local
  Garhwali Whisper checkpoints; preserve every reference, attach both hypotheses,
  and remove two unambiguous stray opening parentheses from release proposals.
- [ ] Complete human adjudication for the remaining 176 public text candidates
  (172 Translatewiki and four PanLex), five ambiguous supervised
  transcripts, and risky drafts. The complete three-checkpoint machine review is
  attached to all 1,090 Garhwali recovery records; audio-grounded human review
  remains. Eight additional supervised rows are already isolated as Bengali-
  script source-label conflicts.
- [x] Build the complete all-data package with every one of the 28,755 collected
  text values present and active for quality work; zero catalog texts are redacted.
- [x] Keep a separate public redistribution catalog with provenance and quality
  metadata for records whose source terms remain unresolved.

### 10. Release — Medium

- [x] Create and push GitHub checkpoint commits to the project remote.
- [x] Keep raw sources, caches, large datasets, and audio out of Git.
- [x] Publish preparation, source, folklore, social-media, VAANI, and language-
  quality documentation.
- [x] Generate a versioned local release manifest.
- [x] Document the redistribution and model-use policy.
- [x] Prepare a dataset card with license treatment, attribution, consent scope,
  exclusions, review status, and reproducibility commands.

## 🔭 Research platform roadmap

| Stage | Status | Primary artifact | Remaining success condition |
| --- | --- | --- | --- |
| **1. Corpus v0.1 candidate** | Rights-filtered public build passes automated audit; 216 rights-pending structured records stay in all-data only | `GarhwaliCorpus` | Align release version/tag, then publish the rights-filtered package when requested |
| **2. Benchmark candidate** | Automated 398-text / 112-ASR candidate built; native/dialect review deferred | `GarhwaliBench` | Keep review deferred and label every benchmark/model result as an automated candidate |
| **3. Baseline audit** | Historical experiment suite complete | `Garhwali Model Report` | Reevaluate advertised scores against a versioned final benchmark |
| **4. Controlled modeling** | Current experiments complete; no active paid job | `GarhwaliGPT` plus adapted models | Keep unpromoted checkpoints experimental; rerun only against the frozen release benchmark |
| **5. Research experiments** | Core automated experiments complete | Reproducible ablation suite | Add further transfer and scaling work after the corpus and benchmark versions are settled |
| **6. Community expansion** | Planned | Corpus v1.x/v2 | Add native corrections, more varieties and districts, conversations, parallel data, and corrected historical text |
| **7. Public platform** | Planned | Dataset, models, leaderboard, versioned API, explorer | Upload the final dataset, then ship stable search, lexicon, normalization, transliteration, and cultural endpoints |

### Garhwali API and commercial path

The first useful API should expose the strongest reviewed assets before offering
generation as if it were solved. The planned text-first MVP is:

1. `GET /v1/search` — provenance-backed corpus and cultural search.
2. `GET /v1/lexicon` — Garhwali forms, variants, meanings, examples, dialect
   evidence, sources, and confidence.
3. `POST /v1/normalize` — reversible Unicode, punctuation, and spelling
   normalization with every change returned.
4. `POST /v1/transliterate` — Devanagari/Roman conversion with alternatives.
5. `GET /v1/culture` — cited people, works, places, history, folklore, and
   university-research records.
6. `POST /v1/asr` and `POST /v1/translate` — beta endpoints only after their
   frozen evaluations meet published quality thresholds.

The service plan includes API keys, per-key quotas, usage metering, versioned
responses, confidence fields, source citations, a correction endpoint, privacy
controls, and a small free tier. Paid plans can sell hosted search, normalization,
and model inference. Raw third-party PDFs, audio, and other source payloads stay
governed by their own terms; the API returns licensed data or derived results
with provenance.

### Realistic delivery horizon

| Deliverable | Focused effort from the current state | Main dependency |
| --- | ---: | --- |
| Literary, cultural, and university additions | Complete | Automated validation |
| Local corpus package candidate | Automated build complete: 257,807 all-data / 146,684 public-profile rows | Public profile excludes 216 structured records without compatible rights evidence; local v0.1.1 tag matches reviewed commit |
| SraVaani refined sweep and integration | Complete; base checkpoint remains preferred | Further paid Hugging Face runs are paused by project direction |
| Hugging Face dataset publication | Not active; no upload made | Current project direction is local work; do not publish until rights and release gates are resolved |
| Quality-focused dataset and benchmark release | Automated candidate is prepared | Native review and dialect annotation are deferred; do not claim native-validated quality |
| Sellable text-first API MVP | 30–60 additional hours / 1–2 weeks | Dataset freeze, hosting, authentication, billing, monitoring |
| Translation and ASR beta | 2–6 additional weeks | Better native references and measured quality gains |
| Full corpus, benchmark, models, community layer, API, and demos | 2–4 months of sustained work | Native participation, evaluation, and production operations |

“Finished” for the first public release means a reproducible dataset, a frozen
benchmark, and documentation. A text-first API is a later product stage. Strong
production speech, translation, and TTS also remain later releases because their
accuracy cannot be established from machine scores alone.

### Next execution cycle

1. [x] **Model-assisted text cleanup — High:** the historical 27,987-record run
   carry reversible proposals; 4,096 priority records have pinned-model scores.
2. [x] **Cleanup ablation — Medium:** fixed-split evaluation rejected automatic
   promotion of both mechanical and bulk spelling variants.
3. [x] **Controlled modeling — Xhigh:** scaling, head transfer, 1,024-step
   encoder-LoRA continuation, split-safe instruction construction, and
   multi-seed mT5/mT0 tuning are complete. mT0 is the current accuracy baseline;
   exact-match generation and native-reference review remain open.
4. [x] **SraVaani comparison — High:** the provider-approved, revision-pinned
   model scores 42.761% WER / 17.606% CER on the same 112-row ASR manifest,
   reducing WER by 42.45% relative to the best local Whisper checkpoint. The
   resumable full pass produced drafts for all 104,542 untranscribed source rows,
   covering 104,534 unique recordings with zero missing audio hashes.
5. [x] **Transcript recovery routing — High:** all 1,188 flagged drafts now have
   deterministic recovery actions; originals remain active, no rows are
   quarantined, and 17 repetition repairs are stored only as reversible candidates.
6. [x] **Source-grounded text accuracy — Xhigh:** structured Wiktionary and
   Wikimedia extraction plus source-aware linguistic notation reduced the public
   review queue from 628 to 176 without automatic spelling or translation guesses.
   All 176 cases and the five ambiguous supervised transcripts now have flat,
   independently fillable review templates with source and model context.
7. [x] **Targeted transcript re-decoding — High:** the complete 1,188-record
   recovery queue has local Whisper alternatives with exact hash coverage and
   corpus-level failure checks. The comparison finds 1,154 structurally lower-risk
   alternatives and retains the original as the structural preference for 34.
   Nothing is automatically promoted; accuracy still requires human references.
8. [x] **Recovery confidence calibration — High:** 381 human-referenced,
   training-disjoint recordings show SraVaani has lower row-level CER on 369,
   Whisper on 8, with 4 ties. All 1,188 recovery rows now map to an observed
   agreement band; no row is promoted or removed.
9. [x] **Confidence-aware manifest integration — Medium:** all 104,542 source
   drafts remain preserved, with confidence evidence attached to exactly 1,188.
   The local transcript package exports all 104,534 unique audios without raw
   paths or audio files and preserves duplicate-source counts.
10. [x] **Source-label conflict isolation — High:** eight human Bengali-script
   transcripts and 98 machine drafts resolve to one source speaker key. All 106
   records remain visible, while the 98 drafts are ineligible for Garhwali loss.
11. [x] **Confidence-aware ASR curriculum — High:** the 106,057-row training view
   combines 1,621 human references with 104,436 eligible machine-labelled
   recordings across five stages. Machine loss mass equals the human-reference
   mass; validation and test remain human-only, with zero audio leakage and zero
   empty targets.
12. [x] **Weighted trainer dry run — High:** stage selection, positive sample
    weights, stage-to-stage checkpoint validation, and legacy strict-split
    compatibility are implemented. The complete stage-4 dry run passes with no
    missing audio, empty targets, or duplicate training hashes; curriculum runs
    use human-only validation by default and reserve the final test split.
13. [x] **Stage-0 checkpoint selection — High:** curriculum stage 0 exactly
    matches the original 1,621 human training records. The existing `v0.2`
    checkpoint beats `v0.1` on the 269-row validation split and passes the full
    104,967-row stage-1 resume dry run without copying weights.
14. [x] **Stage-1 machine-label pilot — Xhigh:** 32 human anchors and 2,048
    standard SraVaani labels completed 2,080 Metal updates and evaluation on all
    269 validation records. WER worsened by 0.003614 and CER by 0.000058, so the
    run is registered as rejected, the human-only checkpoint stays selected, and
    stage 2 remains locked.
15. [x] **Weighted-batch redesign and ablation — Xhigh:** the same data now forms
    32 deterministic batches with one human and 64 machine records per normalized
    optimizer update. Aggregate validation still worsens to 0.788153 WER and
    0.463672 CER. The result is rejected and the full machine-label curriculum is
    stopped under this recipe.
16. [x] **SraVaani adaptation readiness — Xhigh:** all 1,621 train, 269 validation,
    and 112 held-out test clips are exported in deterministic official NeMo
    tar/manifest format. Every source hash and PCM property passes, all rows are
    CC BY 4.0, and audio/speaker leakage is zero. The guarded two-epoch,
    decoder-only 102-step launcher is ready.
17. [x] **Risky-draft three-checkpoint review — High:** a complete local pass
    compares SraVaani with Garhwali Whisper `v0.1` and `v0.2` for all 1,090
    eligible recovery recordings. It ranks reversible proposals, leaves only 35
    with structural flags, preserves every original, and makes zero unsupported
    accuracy or training promotions.
18. [x] **Structural-outlier audio evidence — High:** all 35 remaining outliers
    have exact stronger-checkpoint re-decodes, waveform activity measurements,
    and scores calibrated on 112 human-referenced clips. Raw confidence is only
    weakly related to CER, so every case remains pending listening review.
19. [x] **SraVaani human-reference training — Xhigh:** Hugging Face Job
    [`6aa9e33af76d6a098a70ec01`](https://huggingface.co/jobs/rushilrawat/6aa9e33af76d6a098a70ec01)
    completed the 102-step decoder/joint adaptation on `l4x1`. The one-time
    112-record test scores 43.528% WER / 17.452% CER versus the base model's
    42.761% / 17.606%. The experimental checkpoint is retained but not promoted.
20. [x] **Structured knowledge packaging — Medium:** geography, historical terms,
    literary people, literary works, popular songs, and university research are
    first-class Hugging Face configurations with 216 records and stable IDs.
21. [x] **Release reconciliation — High:** the 257,807-row all-data package and
    146,684-row public package are rebuilt, the tracked release index is synced,
    and the rights-filtered public export passes provenance, count, rights, and
    leakage checks. The omitted 216 records remain in the local all-data package.
22. [x] **Refined SraVaani decision — Xhigh:** Job
    [`6aaa1726f76d6a098a70f768`](https://huggingface.co/jobs/rushilrawat/6aaa1726f76d6a098a70f768)
    completed all 61 trials. The selected checkpoint improved validation WER to
    42.711% but worsened frozen-test WER to 43.528% versus the base model's
    42.761%, so it is retained for research and not promoted.
23. [x] **Expanded human-transcript SraVaani — Xhigh:** train on 5,513 human
    transcripts (8.112 hours) after excluding every fixed validation/test audio
    hash and every known benchmark speaker; select on the unchanged 269-record
    validation set and evaluate the frozen 112-record test at most once. Job
    [`6aaaa754f76d6a098a70f2f`](https://huggingface.co/jobs/rushilrawat/6aaaa754f76d6a098a70f2f)
    completed 346 steps. Validation WER improved to 42.209%, but frozen-test WER
    was 43.289% versus base SraVaani's 42.761%; the checkpoint remains experimental.
24. [x] **IndicBERTv2 continuation — Xhigh:** Job
    [`6aaaad62f76d6a098a71100f`](https://huggingface.co/jobs/rushilrawat/6aaaad62f76d6a098a71100f)
    completed three 4,096-step seeds against the current 106,804-record training
    split. Mean validation cross-entropy improved from 6.395484 to 5.089108 and
    masked-token accuracy rose from 24.299% to 28.287%; the test split stayed closed.
25. [x] **Longer mT0 instruction continuation — Xhigh:** Job
    [`6aaab2465527934177eea964`](https://huggingface.co/jobs/rushilrawat/6aaab2465527934177eea964)
    completed three validation-only 2,048-step seeds on `l4x1`. All seeds beat
    the current base validation loss; seed 29 reached 4.625628 and the fixed
    test remained unopened.
26. [x] **Extended mT0 generation evaluation — Xhigh:** three 8,192-step seeds
    reduced best validation cross-entropy to 4.476975 and achieved the first
    nonzero exact matches (up to 2.308%). chrF2 remains below the zero-shot base,
    and the fixed test stayed closed.
27. [x] **PDF-domain IndicBERT continuation — Xhigh:** Job
    [`6aaabf3e5527934177eeac89`](https://huggingface.co/jobs/rushilrawat/6aaabf3e5527934177eeac89)
    trained only on 25,983 incoming-book segments and selected on 615 book
    validation segments. Mean loss fell from 6.190638 to 4.665097 and masked-token
    accuracy rose from 25.198% to 33.920%; all 1,328 PDF test segments stayed closed.
28. [x] **Extended PDF-domain continuation — Xhigh:** all three 32,768-step seeds
    covered the full training pool. Mean validation loss improved to 4.553516
    and accuracy to 35.605%; the PDF test split remained unopened.
29. [x] **Balanced text/book continuation — Xhigh:** every seed improved both
    validation domains. General loss fell from 6.729359 to a 5.316585 mean;
    PDF-domain accuracy rose from 24.473% to approximately 32.29%.
30. [x] **Semantic duplicate and leakage audit — High:** the complete
    pre-OCR-correction segment snapshot was embedded. Cross-encoder refinement
    found 29,903 candidate pairs. The earlier split had 92 supported pairs
    crossing partitions; the rebuilt split groups supported semantic edges,
    reassigns 120 records, and reports zero supported-edge leakage. No source
    text was changed or deleted.
31. [x] **Release metadata completeness — High:** profile all 114,064 current split rows,
    restore stable source identifiers for 9,774 segments from their originating
    filenames, rebuild the package, and verify zero empty text, duplicate IDs,
    exact cross-split overlap, or missing source identifiers. Missing rights
    assertions are now represented explicitly as `not_recorded` rather than null.
32. [x] **Model-backed text noise audit — High:** pinned IndicBERTv2 scored all
    28,755 canonical texts, yielding 2,876 model/source disagreements, 2,987
    OCR priorities, and 47,165 reversible spelling candidates without changing
    or excluding any original record.
33. [x] **OCR proposal validation — High:** one deterministic mask seed scored
    10,856 candidate-bearing records: 2,431 supported, 3,079 rejected, and 5,346
    inconclusive. Three-seed consensus narrows this to 1,781 supported, 2,448
    rejected, and 6,627 inconclusive; nothing is auto-applied.
    The book-adapted three-seed audit further narrows OCR-source material to 103
    supported, 491 rejected, and 1,300 inconclusive correction records.
34. [x] **Final mT0 continuation — Xhigh:** three 16,384-step seeds reduced the
    best validation cross-entropy from 4.476975 to 4.315077. Seed 43 reached
    2.308% exact match and 0.073709 chrF2, but adapted chrF2 remains below the
    base model; the fixed test stayed closed.
35. [x] **Semantic candidate refinement — High:** a multilingual cross-encoder
    re-scored all 29,903 embedding candidates, supporting 1,624 near-duplicate
    pairs and narrowing cross-split review to 92 supported pairs. No record was
    automatically removed or changed.
36. [x] **Budget-bounded 32,768-step mT0 continuation — Xhigh:** seeds 17 and
    29 completed and improved validation cross-entropy to 4.266280 and 4.219282.
    Seed 43 and the combined generation diagnostics were stopped when the
    reported Hugging Face balance became insufficient; the fixed test stayed closed.
37. [ ] **Final dataset publication — High:** rebuild the manifests after the
    model decision, run the final audit again, and upload the selected all-data
    package and its dataset card to Hugging Face.
38. [ ] **Text-first API MVP — High:** implement versioned search, lexicon,
    normalization, transliteration, and cultural-record endpoints with API keys,
    quotas, citations, confidence, and correction intake.

The first benchmark index and deterministic character baseline are complete. See
[`research/garhwali-bench-v0.1-2026-09-11.md`](research/garhwali-bench-v0.1-2026-09-11.md).
The multilingual tokenizer and IndicBERTv2 findings are in
[`research/multilingual-model-audit-2026-09-11.md`](research/multilingual-model-audit-2026-09-11.md).
The Garhwali-to-English floors and NLLB comparison are in
[`research/translation-baseline-2026-09-11.md`](research/translation-baseline-2026-09-11.md).
The XORQA lexical and IndicBERTv2 results are in
[`research/retrieval-baseline-2026-09-11.md`](research/retrieval-baseline-2026-09-11.md).
The complete local ASR comparison and SraVaani access status are in
[`research/speech-baseline-comparison-2026-09-11.md`](research/speech-baseline-comparison-2026-09-11.md).
The flagged-draft recovery plan and exact action counts are in
[`research/sravaani-transcript-recovery-2026-09-13.md`](research/sravaani-transcript-recovery-2026-09-13.md).
The human-reference audit, agreement calibration, and recovery confidence bands
are in [`research/sravaani-recovery-confidence-2026-09-13.md`](research/sravaani-recovery-confidence-2026-09-13.md).
The complete-draft merge and local package audit are in
[`research/sravaani-confidence-integration-2026-09-14.md`](research/sravaani-confidence-integration-2026-09-14.md).
The three-checkpoint risky-draft review and calibration boundary are in
[`research/sravaani-recovery-adjudication-2026-09-14.md`](research/sravaani-recovery-adjudication-2026-09-14.md).
The 35-record waveform and audio-score review is in
[`research/sravaani-audio-grounded-review-2026-09-14.md`](research/sravaani-audio-grounded-review-2026-09-14.md).
The staged selection, weight budget, and leakage audit are in
[`research/asr-training-curriculum-2026-09-14.md`](research/asr-training-curriculum-2026-09-14.md).
The trainer behavior and full dependency-free dry run are in
[`research/asr-weighted-trainer-2026-09-14.md`](research/asr-weighted-trainer-2026-09-14.md).
The stage-0 equivalence proof and checkpoint comparison are in
[`research/asr-curriculum-stage0-2026-09-14.md`](research/asr-curriculum-stage0-2026-09-14.md).
The bounded machine-label ablation and rejection decision are in
[`research/asr-curriculum-stage1-pilot-2026-09-14.md`](research/asr-curriculum-stage1-pilot-2026-09-14.md).
The normalized weighted-batch redesign and second rejection are in
[`research/asr-weighted-batch-ablation-2026-09-14.md`](research/asr-weighted-batch-ablation-2026-09-14.md).
The SraVaani training-package audit and exact external requirements are in
[`research/sravaani-adaptation-readiness-2026-09-14.md`](research/sravaani-adaptation-readiness-2026-09-14.md).
The reversible cleanup proposals and fixed-split ablation are in
[`research/model-assisted-text-cleanup-2026-09-11.md`](research/model-assisted-text-cleanup-2026-09-11.md).
The structured source extraction and remaining 176-record accuracy boundary are
in [`research/text-accuracy-review-2026-09-15.md`](research/text-accuracy-review-2026-09-15.md).
The independently fillable review packets and import path are in
[`research/native-reference-review-readiness-2026-09-15.md`](research/native-reference-review-readiness-2026-09-15.md).
The first controlled data-scaling curve is in
[`research/controlled-text-scaling-2026-09-11.md`](research/controlled-text-scaling-2026-09-11.md).
The longer continuation and instruction-tuning results are in
[`research/controlled-modeling-2026-09-12.md`](research/controlled-modeling-2026-09-12.md).

`GarhwaliBench` should complement existing generation benchmarks by measuring
things that require Garhwali knowledge: Garhwali–Hindi–English translation,
meaning preservation, morphology, idioms, Hindi/Garhwali discrimination,
code-switching, Devanagari and Romanized text, historical and contemporary usage,
dialect robustness, cultural QA, retrieval, and multi-reference ASR. Native
speakers define accepted language; model-assisted review can prioritize work but
cannot establish ground truth.

### Controlled research questions

| Experiment | Question |
| --- | --- |
| Data scaling | What changes at 100K, 500K, 1M, 2M, and 5M clean tokens? |
| Quality vs. quantity | Does a smaller reviewed corpus outperform a larger noisy corpus? |
| OCR corruption | At what character-error rate does historical OCR become harmful? |
| Hindi transfer | When does Hindi help Garhwali, and when does it produce Hindi-like output? |
| Parallel data | How much value comes from native-reviewed Garhwali–Hindi–English alignment? |
| Code-switching | Does natural mixing improve transfer or obscure Garhwali competence? |
| Tokenization | Does lower token fertility improve downstream quality? |
| Dialect balance | Does balanced sampling protect less represented varieties? |
| Synthetic data | At what synthetic-to-human ratio do gains stop or reverse? |
| CPT vs. SFT | Which capabilities come from language exposure and which from instruction tuning? |
| Forgetting | Does Garhwali adaptation degrade Hindi, English, or general capabilities? |
| RAG vs. CPT | Are cultural facts better served by cited retrieval than by model weights? |
| Abstention | Can a system identify an unknown Garhwali fact or word instead of inventing one? |

Translation and retrieval are first-class near-term tracks. A native-reviewed
`GarhwaliParallel` resource should align Garhwali, Hindi, and English, while
`GarhwaliRAG` should answer from trusted corpus passages and expose source, page
or speaker, date, dialect evidence, and confidence. Speech experiments should
measure generalization across speakers, districts, code-switching, and spelling
variation with multiple seeds and speaker-safe evaluation.

The project is complete when another researcher can obtain a documented corpus,
reproduce its preparation, evaluate against a frozen native-reviewed benchmark,
compare strong baselines by source and variety, and trace every result to its
evidence. A Garhwali speaker should also be able to contribute, correct, search,
translate, and see where the system's answers came from.

The detailed gap plan is [`research/gap-closure-plan.md`](research/gap-closure-plan.md),
and the known access blockers are [`research/garhwali-access-blockers-2026-09-10.md`](research/garhwali-access-blockers-2026-09-10.md).

## 🧪 Verification commands

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
.venv/bin/python scripts/dedup_report.py
.venv/bin/python scripts/verify_ingestion.py
.venv/bin/python scripts/build_huggingface_dataset.py
.venv/bin/python scripts/build_asr_training_curriculum.py
.venv/bin/python scripts/train_whisper_garhwali.py --curriculum-stage 4 --dry-run
.venv/bin/python scripts/register_asr_stage0.py
.venv/bin/python scripts/register_asr_stage1_pilot.py
.venv/bin/python scripts/register_asr_stage1_weighted_batch_pilot.py
.venv/bin/python scripts/prepare_sravaani_finetune.py
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/train_sravaani_garhwali.py
bash -n scripts/run_sravaani_hf_job.sh
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/redecode_supervised_review.py
.venv/bin/python scripts/audit_final_release.py
git diff --check
```

The public package now excludes the 216 structured records without compatible
rights evidence; all remain intact in the complete all-data package. The public
preflight and final audit pass with zero rights failures. The all-data package
also passes preflight and retains all 28,755 collected text values with zero
catalog redactions. Native-speaker review and dialect annotation are deferred;
the benchmark remains explicitly an automated candidate. Every structured
source reference resolves to a source URL or capture fingerprint, but that
traceability alone does not grant reuse rights. The audit reopens all five
benchmark artifacts and verifies package shard hashes and content-derived text IDs. See
[`finalreport.md`](finalreport.md) and
[`DEEP_DIVE_FINAL_AUDIT.md`](DEEP_DIVE_FINAL_AUDIT.md) for details. The
The current complete suite passes **435 tests**. The pipeline tracks **367 source snapshots**.

## Local dataset packages

Future PDFs go in `incoming/pdfs/` with a same-name JSON metadata sidecar. Run
`bash scripts/refresh_incoming_pdfs.sh` to hash and deduplicate the files,
extract embedded text or OCR scan pages, rebuild cleaned and segmented corpus
views, and regenerate the local all-data package. This local pipeline does not
consume Hugging Face GPU credit. No dataset upload or paid Hugging Face job is
currently part of the project work.

`scripts/build_huggingface_dataset.py` creates two local multi-config
datasets with Garhwali text, human VAANI transcripts, SraVaani machine drafts,
lexicon, instruction splits, geography, historical terms, literary people,
literary works, popular-song metadata, and university research. The **all-data
profile is the complete local research package**: it contains **257,807 rows**,
including every collected text value and all **216 structured cultural and
scholarly records**. Those structured records now carry standardized
provenance and quality fields. The **146,684-row public profile** omits the 216
structured records that lack compatible rights evidence. The rights-filtered
package audit passes; this does not clear the omitted records themselves. Both
profiles omit original audio filenames and raw speaker identifiers. Native-
speaker review and dialect annotation are deferred, so the benchmark remains an
automated candidate. See [`finalreport.md`](finalreport.md) before any release.

```bash
# Build the complete transcript-only all-data package (257,807 rows)
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py \
  --profile all-data

# Build the rights-filtered public-profile candidate
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py \
  --profile public \
  --output data/huggingface/garhwali-language-lab
.venv/bin/python scripts/audit_final_release.py
```

The all-data package is for local or access-controlled research. It contains
rights-pending and restricted components. The public profile excludes all 216
structured records without compatible public-rights evidence. The package
audit passes for this filtered profile; no package has been uploaded.

The generated `README.md` is the Hugging Face dataset card, while
`manifest.json` records configuration counts, shard names, draft completeness,
and whether audio was included. The all-data catalog includes all **28,755**
exact-unique text values with **zero redactions**. The package also contains all
**114,064** prepared text segments, **1,114** lexicon rows, and **3,230**
instruction rows. The public catalog remains a transparent redistribution view.
When an exact duplicate has both open and blocked provenance,
`public_rights_basis` identifies the open copy while retaining both source
histories. The source-level audit is documented in
[`research/text-source-rights-audit-2026-09-15.md`](research/text-source-rights-audit-2026-09-15.md).
The current all-data package report is
[`research/all-data-package-2026-09-19.md`](research/all-data-package-2026-09-19.md).
The generated package snapshot carries release ID `v0.1.1`. The historical
`v0.1.0` tag remains unchanged; local annotated tag `v0.1.1` resolves to
the reviewed release commit. The index is
[`release/v0.1.1-manifest.json`](release/v0.1.1-manifest.json). Compact
generated reports and visual evidence are tracked under
[`release/v0.1.1/`](release/v0.1.1/README.md). No remote upload has occurred.

## 🤝 Contributing

Contributions should preserve the record’s source URL, raw snapshot hash, license
or rights status, attribution, language scope, quality flags, and transformation
steps. Add a focused failing test before changing a collector or quality rule.
Do not commit credentials, Hugging Face caches, raw audio, PDFs, generated JSONL,
or private speaker information. New source families belong in the source catalog
even when they are discovered but cannot yet be promoted.

## ⚖️ Data and ethics

The project owner has directed the lab to use every collected record in local
experimental research. That instruction is represented by the all-data view and
explicit `usage`/`rights_status` fields. It does not erase the original source
terms or make an unresolved source suitable for public redistribution. A public
release must carry its own license matrix, attribution, consent scope, and
exclusion policy.

The lab is designed to support Garhwali speakers and researchers: preserve variants,
credit contributors, protect personal information, and let native reviewers correct
the system before a model is treated as authoritative.
