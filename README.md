<div align="center">

# 🏔️ Garhwali Language Lab

**A provenance-preserving research corpus and model-development pipeline for Garhwali (gbm).**

*Public sources, community material, historical texts, and speech in. Auditable
language resources, review queues, and reproducible model datasets out.*

[![python](https://img.shields.io/badge/python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![langgraph](https://img.shields.io/badge/orchestration-LangGraph-1C3C3C.svg)](PIPELINE.md)
[![tests](https://img.shields.io/badge/tests-247%20passing-success.svg)](research/corpus-preparation-status.md)
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
├── GarhwaliBench        frozen, native-reviewed, dialect-aware evaluation
├── Research Suite       tokenizer, quality, transfer, scaling, and ablations
├── Garhwali Models      LM, translation, retrieval, ASR, and TTS baselines
├── Community Layer      transcription, correction, and dialect contribution
└── Public Infrastructure
                         datasets, model cards, leaderboard, API, and demos
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
  human transcripts and all 104,542 previously untranscribed rows now have
  revision-pinned SraVaani experimental drafts.
- **363 identified speaker IDs**, with district, gender, and speaker-status fields
  preserved; current VAANI coverage is Uttarkashi and Tehri Garhwal.
- **25,343 likely Garhwali text candidates**, 1,468 source-declared mixed-language
  records, 859 unresolved records, and 317 non-Garhwali cultural-context records.
- **1,124 lexicon candidates**, 446 unique English–Garhwali pairs, and 1,187
  grammar-source candidates.
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
- **GarhwaliBench v0.1:** 3,847 external task records, 2,492 held-out text
  segments, and 112 speaker-safe ASR rows, with zero measured training overlap.
- **Character bigram floor:** 16.464 held-out perplexity and 0.000498% character
  OOV rate for reproducible comparison with later language models.
- **Multilingual tokenizer audit:** IndicBERTv2 leads five candidates at 1.532
  tokens per Garhwali word; the Garhwali OpenLLaMA adapter tokenizer needs 5.327.
- **IndicBERTv2 baseline:** 17.79% masked-token accuracy on 506 deterministic
  masks from 128 held-out records, with no truncation.
- **Controlled continuation:** a 1,024-step, three-seed IndicBERTv2 LoRA run
  lowers mean validation cross-entropy from 6.678 to 5.624.
- **Instruction resource:** 2,518 split-safe Garhwali translation and lexicon
  instructions; a first three-seed mT5 LoRA baseline improves validation
  loss but remains unfit for generation.
- **Accuracy continuation:** mT0-small reaches **4.961989** mean validation and
  **5.019603** mean new-test cross-entropy after 256-step three-seed LoRA; all
  seeds improve the held-out loss, while exact-match generation remains 0%.
- **104,542 SraVaani machine drafts** cover 104,534 unique recordings. Automated
  quality analysis marks 103,354 standard and 1,188 flagged rows while retaining
  every source row in the active experimental view.
- **1,188 confidence-scored recovery alternatives** are integrated beside their
  immutable SraVaani originals: 30 medium, 35 low, and 1,123 very-low review
  confidence, with no quarantine or automatic promotion.
- **106,155-row confidence-aware ASR curriculum:** 1,621 human references plus
  all 104,534 unique machine-labelled recordings, with human-only validation and
  test sets, zero audio leakage, and zero empty targets.
- **Full curriculum trainer dry run:** all 106,155 training rows and 269
  validation rows resolve to local audio, with zero empty targets, duplicate
  training hashes, or missing files and 3,241.999999 total effective loss mass.
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
- **247 automated tests** and **365 immutable source snapshots** verified, with 43 public source URLs covered
  by a scheduled freshness audit.

These figures describe the preparation snapshot updated on 2026-09-14. Raw
downloads, VAANI audio, generated JSONL, caches, and model artifacts stay outside
Git through `.gitignore`.

## 📈 Corpus scale

<div align="center">

| `~34 GB` | `110,436` | `135.5 h` | `27,987` |
| --- | ---: | ---: | ---: |
| local corpus data | recordings | audio duration | unique text lines |

| `7.39M` | `1.44M` | `86,215` | `1,124` |
| ---: | ---: | ---: | ---: |
| text characters | whitespace tokens* | unique segments | lexicon candidates |

| `446` | `1,187` | `5,894` | `104,542` |
| ---: | ---: | ---: | ---: |
| English–Garhwali pairs | grammar-source candidates | supervised transcripts | untranscribed clips |

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
| `restricted/` | Useful data with limited or non-commercial terms | UOU OCR, Open Bible Stories, PanLex, thematic vocabulary |
| `experimental/` | Active local data with unresolved rights or quality signals | PahariLI, Indic Dialect ASR, web documents, community datasets |
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
  OCR, spelling, language-ambiguity, and dialect-evidence proposals to all 27,987
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
- [x] Build 1,124 pronunciation candidates, including 293 with source phonetic
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
- [x] Build 2,518 provenance-preserving instruction records with parent-disjoint
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
- [ ] Run the 102-step SraVaani adaptation pilot once the separate NeMo checkpoint
  and a CUDA NVIDIA GPU with approximately 16 GB VRAM are available.

### 9. Testing and review — High

- [x] Run unit tests and data-quality checks.
- [x] Audit licensing, attribution, source hashes, and unresolved rights.
- [x] Track unresolved language, dialect, OCR, audio, and transcript records.
- [x] Verify source snapshots and release-manifest line counts.
- [x] Make the two-pass native workflow available as an optional future quality
  upgrade without blocking the current release.
- [x] Freeze held-out, automatically screened evaluation candidates before tuning.
- [x] Add an intensive evidence-based quality gate across all text, supervised
  speech, and SraVaani drafts; preserve every value and attach explicit tier reasons.
- [x] Refine all 1,818 public Garhwali text candidates with genre-aware surface
  checks; identify 529 concrete review targets without guessing linguistic fixes.
- [ ] Correct and re-review the quality-gate queues, beginning with public
  Garhwali text candidates, 13 supervised transcripts, and 1,188 risky drafts.
- [x] Publish a transparency catalog for every collected text record; rights-pending
  rows expose provenance and quality metadata while only the protected text is redacted.

### 10. Release — Medium

- [x] Create and push GitHub checkpoint commits to the project remote.
- [x] Keep raw sources, caches, large datasets, and audio out of Git.
- [x] Publish preparation, source, folklore, social-media, VAANI, and language-
  quality documentation.
- [x] Generate a versioned local release manifest.
- [x] Document the redistribution and model-use policy.
- [x] Publish a dataset card with license treatment, attribution, consent scope,
  exclusions, review status, and reproducibility commands.

## 🔭 Research platform roadmap

| Stage | Primary artifact | Success condition |
| --- | --- | --- |
| **1. Corpus v1.0** | `GarhwaliCorpus` | Clean, deduplicated, rights-aware, source-versioned text and audio with raw and normalized forms |
| **2. Benchmark v1.0** | `GarhwaliBench` | Frozen, checksum-addressed experimental evaluation for language quality, translation, generation, dialects, code-switching, retrieval, and speech; later corrections are versioned |
| **3. Baseline audit** | `Garhwali Model Report` | Evaluate current multilingual, Indic, MT, tokenizer, retrieval, and speech systems before selecting new training runs |
| **4. Controlled modeling** | `GarhwaliGPT` plus adapted models | Treat a small scratch LM as a scientific control; build practical systems through multilingual continued pretraining, translation, retrieval, and speech adaptation |
| **5. Research experiments** | Reproducible ablation suite | Quantify which changes survive multiple seeds and which apparent gains disappear |
| **6. Community expansion** | Corpus v1.x/v2 | Native corrections, additional varieties and districts, conversations, parallel data, and corrected historical text |
| **7. Public platform** | Dataset, models, leaderboard, API, explorer | Reproducible releases another researcher can inspect, run, compare, and extend |

### Next execution cycle

1. [x] **Model-assisted text cleanup — High:** 27,987 immutable originals now
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
6. [x] **Targeted transcript re-decoding — High:** the complete 1,188-record
   recovery queue has local Whisper alternatives with exact hash coverage and
   corpus-level failure checks. The comparison finds 1,154 structurally lower-risk
   alternatives and retains the original as the structural preference for 34.
   Nothing is automatically promoted; accuracy still requires human references.
7. [x] **Recovery confidence calibration — High:** 381 human-referenced,
   training-disjoint recordings show SraVaani has lower row-level CER on 369,
   Whisper on 8, with 4 ties. All 1,188 recovery rows now map to an observed
   agreement band; no row is promoted or removed.
8. [x] **Confidence-aware manifest integration — Medium:** all 104,542 source
   drafts remain active, with confidence evidence attached to exactly 1,188.
   The local transcript package exports all 104,534 unique audios without raw
   paths or audio files and preserves duplicate-source counts.
9. [x] **Confidence-aware ASR curriculum — High:** the 106,155-row training view
   combines 1,621 human references with all 104,534 unique machine-labelled
   recordings across five stages. Machine loss mass equals the human-reference
   mass; validation and test remain human-only, with zero audio leakage and zero
   empty targets.
10. [x] **Weighted trainer dry run — High:** stage selection, positive sample
    weights, stage-to-stage checkpoint validation, and legacy strict-split
    compatibility are implemented. The complete stage-4 dry run passes with no
    missing audio, empty targets, or duplicate training hashes; curriculum runs
    use human-only validation by default and reserve the final test split.
11. [x] **Stage-0 checkpoint selection — High:** curriculum stage 0 exactly
    matches the original 1,621 human training records. The existing `v0.2`
    checkpoint beats `v0.1` on the 269-row validation split and passes the full
    104,967-row stage-1 resume dry run without copying weights.
12. [x] **Stage-1 machine-label pilot — Xhigh:** 32 human anchors and 2,048
    standard SraVaani labels completed 2,080 Metal updates and evaluation on all
    269 validation records. WER worsened by 0.003614 and CER by 0.000058, so the
    run is registered as rejected, the human-only checkpoint stays selected, and
    stage 2 remains locked.
13. [x] **Weighted-batch redesign and ablation — Xhigh:** the same data now forms
    32 deterministic batches with one human and 64 machine records per normalized
    optimizer update. Aggregate validation still worsens to 0.788153 WER and
    0.463672 CER. The result is rejected and the full machine-label curriculum is
    stopped under this recipe.
14. [x] **SraVaani adaptation readiness — Xhigh:** all 1,621 train, 269 validation,
    and 112 held-out test clips are exported in deterministic official NeMo
    tar/manifest format. Every source hash and PCM property passes, all rows are
    CC BY 4.0, and audio/speaker leakage is zero. The guarded two-epoch,
    decoder-only 102-step launcher is ready.
15. [ ] **SraVaani human-reference training — Xhigh:** execution requires the
    separate 1.7 GB `SraVaani-nemo-checkpoint.nemo` and CUDA NVIDIA hardware. The
    Hugging Face inference repository supplies a 909 MB TorchScript graph and
    does not contain the trainable NeMo checkpoint.

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
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
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
.venv/bin/python scripts/audit_final_release.py
git diff --check
```

The final audit checks the tracked release index against every generated Hugging
Face shard, including actual row counts, provenance, transcript/source/license
metadata, draft coverage, and cross-split text, audio, and speaker leakage. Its
machine-readable result is [`release/final-audit.json`](release/final-audit.json).
The current verification result is **247 passing tests**, **365 verified source
snapshots**, and zero release-index, export-count, provenance, or leakage errors.

## 🤗 Hugging Face release

`scripts/build_huggingface_dataset.py` creates an upload-ready multi-config
transcript dataset with Garhwali text, human VAANI transcripts, SraVaani machine
drafts, lexicon, and instruction splits. The public profile includes only records
with explicit compatible redistribution evidence and Garhwali language scope.
It omits audio, original audio filenames, and raw speaker identifiers.

```bash
# Build and audit the transcript-only package
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py \
  --output data/huggingface/garhwali-language-lab
.venv/bin/python scripts/audit_final_release.py

# Run after explicitly approving public transcript publication
HF_HOME=.cache/huggingface hf upload rushilrawat/garhwali-language-lab \
  data/huggingface/garhwali-language-lab . --repo-type dataset
```

The generated `README.md` is the Hugging Face dataset card, while
`manifest.json` records configuration counts, shard names, draft completeness,
and whether audio was included. The complete experimental profile remains local
because source access does not automatically grant public redistribution rights.
The published rights-filtered release is versioned as `v0.1.0`; its tracked
index is [`release/v0.1.0-manifest.json`](release/v0.1.0-manifest.json). Compact
generated reports and visual evidence are tracked under
[`release/v0.1.0/`](release/v0.1.0/README.md).

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
