# Script layout

`scripts/` contains executable pipeline and research commands. Run Python
commands from the repository root so their paths and generated manifests stay
stable.

The current pipeline uses Python 3.12, deterministic source-specific collectors,
and checksum-addressed builders. LangGraph is used for resumable ingestion
checkpoints; model scoring and benchmark selection stay in task-specific Python
scripts. LangChain is not currently used. See [`PIPELINE.md`](../PIPELINE.md) for
the architecture and
[`README.md`](../README.md) for the current data and runtime status.

- `ingest_*`, `collect_*`, `download_*`, and `extract_*`: source acquisition
- `prepare_*`, `clean_*`, `refine_*`, and `segment_*`: corpus preparation
- `build_*`, `register_*`, and `export_*`: datasets and release artifacts
- `audit_*`, `validate_*`, `verify_*`, and `check_*`: quality gates
- `train_*`, `run_*`, `evaluate_*`, and `sweep_*`: model experiments
- `*_hf_job.sh`: Hugging Face Jobs container entry points

For a graph-managed source wave, use `ingestion_graph.py` with a unique
`--run-id` and `--refresh-derived`. This checkpointed mode acquires and extracts
the selected source wave, then rebuilds corpus-derived local views, package
previews, the file map, and the managed metrics block in `README.md`. If the run
stops, resume it with the same run ID and `--refresh-derived` flag. The command
does not publish to GitHub or upload packages to Hugging Face; those remain
explicit release actions after the generated checks pass.

`ingest_archive_language_studies.py` extracts the downloaded Internet Archive
DjVu OCR for the 1967 Juyal and 1976 Bhatta Garhwali-language studies into
page-level local research records. It verifies each source PDF against its
download manifest, flags within-intake and existing-project exact overlaps,
and preserves the uploader's unverified CC0 claim without marking the pages
training-eligible. Re-run it with:

```bash
python3 scripts/ingest_archive_language_studies.py
```

`ingest_archive_dabral_references.py` and
`ingest_archive_regional_historical_references.py` create page-aligned local
reference indexes from Archive scans, preserving source pages and rights
uncertainty while checking exact overlap. `ingest_archive_snow_balls.py` and
`ingest_archive_holy_himalaya.py` index their named Archive books with the
same local-only, source-linked treatment. These outputs are contextual
research material; the extraction scripts do not mark them training-eligible
or publish them.

`audit_archive_intake_quality.py` profiles Archive OCR-page identifiers,
non-empty exact-text duplicates, character scripts, and transparent
OCR-warning signals; it also probes local MP3/MP4 container metadata with
`ffprobe`. When present, it reads the consolidated source-linked review view;
otherwise it falls back to the original page indexes. Run it with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_intake_quality.py
```

`audit_archive_corpus_overlap.py` compares those page texts against every
record in the canonical `data/processed/model_ready/cleaned/text.jsonl` view.
It reports exact matches and high-similarity character 5-gram candidates,
without copying source text into its report or changing corpus rows:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_corpus_overlap.py
```

Both scripts write machine-readable reports under Git-ignored
`data/extracted/research/`. A zero candidate count applies only to the stated
normalization, threshold, and compared text view; it does not prove there are
no semantic, source-family, segment, or audio/transcript overlaps. The current
interpretation and measured results are in the
[`Internet Archive quality audit`](../research/internet-archive-intake-quality-2026-10-04.md).

`build_archive_source_disposition.py` records every locally captured Archive
item's metadata claims and creates non-destructive local page/media review
indexes. It scans already-downloaded DjVu XML sidecars for text items missing
from the original page indexes, assigns source/page IDs and text hashes, links
exact corpus matches to existing provenance, and labels follow-up groups
without asserting page language or rights clearance. Every page candidate also
carries script composition, text length, and transparent OCR-warning signals;
language identification is explicitly marked as not performed. Its tracked
outputs are a metadata-only JSON register and Markdown report; page text and
media indexes remain Git-ignored. To rebuild all derived outputs after source indexes change,
run the two audits first, the disposition builder, then rerun the audits and
builder once so the consolidated candidate view and its cross-corpus references
are synchronized:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_intake_quality.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_corpus_overlap.py
PYTHONPATH=scripts .venv/bin/python scripts/build_archive_source_disposition.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_intake_quality.py
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_corpus_overlap.py
PYTHONPATH=scripts .venv/bin/python scripts/build_archive_source_disposition.py
```

The per-item decisions and limits are in the
[`Internet Archive source disposition`](../research/internet-archive-source-disposition-2026-10-04.md).

`audit_archive_media_first_pass.py` re-hashes each downloaded Archive media
candidate and reconciles its path, byte size, duration, and stream metadata
against the existing `ffprobe` report. It reports technical formats, exact
duplicate hashes, captured rights, source-transcript status, and separately
matched local machine drafts. It does not
identify language, transcribe, change rights, or publish media. Rebuild the
ignored local report with this command. It also checks each captured Archive
file listing and local item folder for transcript/caption sidecars without
reading their contents:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_archive_media_first_pass.py
```

The verified 4 October results and interpretation are in the
[`media first-pass report`](../research/internet-archive-media-first-pass-2026-10-04.md).

`prepare_hf_additive_upload.py` validates the rights-filtered public package,
its declared hashes, file inventory, and absence of source/audio payloads. It
stages a release under a versioned Hub path without deletion operations. The
script does not upload; publication is a separate authenticated step after the
remote destination prefix is checked.

Unit tests live in `tests/` and mirror the Python command name. Run all tests
with:

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

The current working-tree suite passes **760 tests**. The
frozen v0.2.0 release run passed 607/607 pytest and 605/605 unittest tests.
The project's CI uses the documented `.venv/bin/python -m unittest` command and
installs dependencies from `requirements-pipeline.txt`. Current benchmark
refreshes use saved ASR outputs and dependency-free local translation/retrieval
diagnostics; fresh NLLB, dense retrieval, and SraVaani inference remain blocked
by uncached model weights. The optional local ASR environment is pinned in
`requirements-asr.txt`; no paid Hugging Face job was started for the Archive
media pilot. See the dated reports linked from the project README.

`analyze_saved_asr_validation.py` re-scores saved SraVaani and Whisper outputs
using only the frozen 269-row ASR validation manifest. It filters by audio hash,
verifies the saved reference against the manifest, and writes a shared
`run_manifest.json` without scoring held-out rows or running inference. The
manifested output is ignored at
`data/processed/evaluation/asr/validation_comparison_manifested_2026-09-27/`.
The 2026-09-27 scores reproduce the prior validation report exactly. See
[`research/asr-validation-run-manifest-2026-09-27.md`](../research/asr-validation-run-manifest-2026-09-27.md).

`audit_saved_asr_heldout_lineage.py` reconciles the saved base, decoder-sweep,
61-trial, expanded-human, and 102-step SraVaani predictions to the fixed
112-row test manifest. It verifies audio hashes, cleaned references, and
aggregate WER/CER counters, then computes paired speaker-cluster bootstrap
intervals. This is a post-hoc audit of a previously scored test set; it does
not select or promote a model. Its local outputs stay ignored under
`data/processed/evaluation/asr/heldout_lineage_audit_2026-09-28/`.
See
[`research/asr-heldout-lineage-audit-2026-09-28.md`](../research/asr-heldout-lineage-audit-2026-09-28.md).

`audit_vaani_official_split_lineage.py` reconciles local prepared ASR views to
VAANI's official 4,778/666/450 transcript splits. It reports aggregate counts
only and can optionally write a local-only manifest for the 338 official-test
rows outside the project's previously used 112-row subset. The 4 October
report records the exposure of each training view and a one-time Whisper-tiny
diagnostic on those 338 rows; it is open-test evidence, not a blind or
speaker-independent score. Reproduce the audit with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_vaani_official_split_lineage.py \
  --remainder-manifest data/extracted/research/vaani-official-test-remainder.jsonl
```

The generated JSON/manifest are ignored under `data/`. The scoring runner
accepts an explicit `--run-id` for non-speaker-safe views and records the local
weight-file SHA-256; do not label an evaluation speaker-safe unless the exact
data and speaker checks support that claim. See
[`research/vaani-official-split-lineage-2026-10-04.md`](../research/vaani-official-split-lineage-2026-10-04.md).

`manifest_saved_generation_validation.py` reconciles the three saved mT0
generation systems against their shared frozen validation IDs and writes one
hash-linked run manifest per seed. It checks task/reference matches and the
selected-ID hash; it performs no model inference or test scoring. The original
sampling parameters and adapter checkpoint hashes were not present in the
synced output. Manifests are ignored under
`data/processed/evaluation/generation/mt0_32768_validation_manifested_2026-09-27/`.
See [`research/mt0-validation-run-manifest-2026-09-27.md`](../research/mt0-validation-run-manifest-2026-09-27.md).

`analyze_generation_output_diagnostics.py` verifies those three validation
manifests and summarizes per-task output length, normalized answer-mode
concentration, repeated character/token runs, selected Unicode anomalies, and
script-family counts. It reads saved validation predictions only, writes
aggregate diagnostics without generated text, and rejects hash/ID/task/reference
drift. Run it with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_generation_output_diagnostics.py
```

The [dated report](../research/generation-output-diagnostics-2026-09-28.md)
records a strong repeated-answer concentration in Garhwali-to-English lexicon
outputs. This is a candidate mode-collapse signal, not a correctness judgment;
the script does not run inference or score held-out rows.

`run_translation_baseline.py` and `run_nllb_translation_baseline.py` write
`predictions.jsonl`, `report.json`, and a hash-linked `run_manifest.json` for
completed runs. The manifest records the requested split, input and selected-row
hashes, selected IDs, config hash, code commit/dirty state, runtime/device,
timestamps, and output hashes. NLLB checks the input and local checkpoint before
importing its model runtime; both translation runners require `--split test`
and `--allow-historical-test` before scoring the historical test split. The NLLB
inference path itself remains unverified until its pinned local checkpoint and
runtime are available.

`audit_benchmark_overlap_candidates.py` scans recommended text splits, the
internal text candidate, and external benchmark primary text. It writes a
local-only JSON/Markdown candidate report under
`data/processed/evaluation/garhwali_bench/`; it records hashes, row IDs,
similarity settings, and an unreviewed state without removing source rows.

`audit_benchmark_nested_overlap.py` scans configured nested task fields for
exact cross-split and recommended-training matches. It writes only IDs, field
paths, splits, counts, and normalized-text hashes; it never copies nested text
or removes rows. `audit_xorqa_source_page_families.py` groups exact normalized
XORQA page titles across original splits and records hashes/IDs without copying
source text. `build_benchmark_usage_labels.py` verifies exact source contexts,
page titles, top-level Garhwali questions, and nested English oracle questions
against source rows and current input hashes. Its local-only overlay labels
138 affected records for open diagnostics; every row remains retained.
Repeated answer spans stay candidate evidence and are not automatically
classified as leakage. Findings are tracked in the
[`research/benchmark-overlap-adjudication-2026-09-26.md`](../research/benchmark-overlap-adjudication-2026-09-26.md).
The page-level results are in
[`research/benchmark-source-page-families-2026-09-28.md`](../research/benchmark-source-page-families-2026-09-28.md).

`validate_benchmark_v02.py` validates the current benchmark manifest, three
external task datasets, internal text/ASR views, and recommended text splits.
It checks source hashes, record counts and IDs, NFC text hashes, task references,
rights/provenance declarations, splits, and local ASR file hashes. Its report is
a local draft-contract audit; it does not freeze v0.2 or clear rights.

`build_benchmark_v02.py` adapts the same eight views into a deterministic,
ignored local draft at `data/processed/evaluation/garhwali_bench/v0.2-draft/`.
It retains each legacy row, separates available source/scoring text, pins
normalizer IDs, validates the XORQA usage-overlay hashes, and verifies output
hashes/counts. `benchmark_metrics.py` provides versioned QA exact-match/token-F1
and summary ROUGE-L scoring with explicit denominator policies. Overall metric
and task contracts remain drafts; no model scores or rights clearance are
produced. The package contains local ASR identifiers and must not be uploaded
as-is. See
[`benchmark-v02-export-2026-09-26.md`](../research/benchmark-v02-export-2026-09-26.md).

`audit_benchmark_v02_rights.py` summarizes upstream license declarations,
item-level rights evidence, and the upload/clearance flags from the draft. It
checks its total against the package manifest. It does not make legal
determinations or change any release flag. The current inventory and its
interpretation are in
[`garhwali-bench-v0.2-rights-inventory-2026-09-29.md`](../research/garhwali-bench-v0.2-rights-inventory-2026-09-29.md).

`score_benchmark_predictions.py` scores existing ASR, Garhwali-to-English
FLORES, CrossSum, or XORQA predictions on dev by default and writes predictions, a
metric report, and the shared hash-linked run manifest. It maps references to
`source_example.target`, `source_example.summary`, and
`source_example.translated_answers[*].text`; requires exact row-ID coverage;
and requires `--allow-historical-test` for test scoring. It preserves rows with
missing target-language references while excluding them from the metric
denominator. ASR reports pooled and per-record WER/CER; its run manifest hashes
the metric implementation. Translation BLEU/chrF remain explicitly identified as the
project's custom metrics, not SacreBLEU. Re-scoring saved translation-memory
dev predictions reproduced 997/997 IDs and the original baseline metrics.

`run_retrieval_baseline.py` writes the same manifest for the BM25 dev-only
retrieval run, with a fixed candidate-corpus hash and all 500 selected query
IDs. `analyze_translation_uncertainty.py` computes paired record-bootstrap
intervals for saved translation predictions, records the seed/replicate count,
and writes pairwise exact-match outcomes and a hash-linked manifest. It does not
cluster by source family; report intervals as descriptive development evidence.

`analyze_retrieval_cluster_uncertainty.py` resamples whole XORQA Wikipedia
source-page families for the saved BM25 dev predictions. Before reporting
intervals, it requires exact dev-ID coverage, hashes matching the parent
retrieval report, valid page-title lineage, and point metrics matching the
saved report. It writes hash-linked JSON/Markdown locally; it neither reads
test predictions nor changes model or benchmark data. Run it with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_retrieval_cluster_uncertainty.py
```

The intervals are conditional on the fixed 1,059-document retrieval corpus,
which contains documents from all source splits; they do not establish
generalization to unseen pages.

`analyze_retrieval_misses.py` verifies saved dev prediction coverage and the
candidate-corpus hash, then separates zero-score queries from gold passages
ranked below the top-10 cutoff. It confirms that all 500 XORQA dev gold
passages are present in the fixed corpus. Outputs contain row IDs and hashes,
not copied source text, and remain under ignored `data/processed/`. Run it
with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/analyze_retrieval_misses.py
```

The [dated report](../research/retrieval-miss-analysis-2026-09-28.md) records
the miss counts and all-split-corpus limitation. This is post-hoc dev analysis;
it does not run inference, score test, or establish semantic support.

After collection and model experiments are frozen, rebuild and validate every
local release layer with `bash scripts/finalize_local_release.sh`.

The separate speech release is built with `scripts/build_hf_speech_release.py`.
When the pinned Meta Omnilingual shards are present in
`data/downloads/meta_omni_gbm/data/gbm_Deva/`, add that source with
`python -m pip install -r requirements-hf-release.txt` followed by
`PYTHONPATH=scripts python scripts/build_hf_meta_omni_speech.py`.
The builder verifies local text/audio hashes and duplicate overlap before
writing the second config. The generated package is gitignored; syncing it to
Hugging Face requires a write-scoped repository credential. Re-running the
metadata update is idempotent: it keeps one Meta config/card section and does
not duplicate attribution or manifests.

### Build local Meta Omnilingual ASR manifests

With the pinned Meta Garhwali Parquet shards, transcript manifest, `pyarrow`,
and FFmpeg already available locally, build an ASR-ready view without network
access:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/prepare_meta_omnilingual_asr.py \
  --source-manifest data/huggingface/garhwali-language-lab-speech-2026-09-23/meta_omnilingual-manifest.jsonl \
  --text-manifest corpus/meta_omni.jsonl \
  --parquet-root data/downloads/meta_omni_gbm/data/gbm_Deva \
  --output-dir data/processed/model_ready/splits/meta_omnilingual_asr \
  --ffmpeg /opt/homebrew/bin/ffmpeg
```

The builder checks every Parquet shard and source row against both local
manifests, writes 16 kHz mono PCM WAVs for eligible rows, and records every
source row (including safety exclusions) in `source_audit.jsonl`. The 2,927-row
source currently yields 2,294 safe train, 271 safe validation, and 292 safe
test rows; Meta test remains unresolved and must not be scored. The generated
audio and manifests are ignored by Git. A pre-existing output directory is
never overwritten.

To run the available Garhwali-adapted Whisper checkpoint on development
validation, use a unique output path and keep `--input` on the safe validation
manifest. Predictions carry record/audio identity and grouped error slices.
SraVaani comparison requires its model weights and compatible NeMo runtime to
be present locally; this pipeline does not download them or invoke paid jobs.

For the bounded local Meta adaptation experiment, first create a Whisper-sized
view. This keeps all long clips and long references in the original source
manifests while excluding them from this model-specific run with a hashed
row-level ledger:

```bash
.venv/bin/python scripts/prepare_whisper_compatible_manifests.py \
  --train-manifest data/processed/model_ready/splits/meta_omnilingual_asr/train.jsonl \
  --validation-manifest data/processed/model_ready/splits/meta_omnilingual_asr/validation.jsonl \
  --model models/whisper-tiny-garhwali-v0.2 \
  --output-dir data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible
```

Train from the filtered train view and evaluate only on its paired validation
view with `scripts/train_whisper_garhwali.py --train-manifest ...
--eval-manifest ... --eval-split validation --seed 17`. Compare candidate and
baseline predictions on the exact same IDs, audio hashes, and references with
`scripts/compare_asr_predictions.py`. The paired output includes aggregate,
speaker, duration, and reference-length slices. See the dated adaptation
report for the full command, pinned input/model hashes, results, and limits.
This result is a development diagnostic; it does not authorize scoring Meta
test or promoting the checkpoint as independently accurate.
