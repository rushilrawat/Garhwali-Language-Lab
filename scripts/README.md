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

Unit tests live in `tests/` and mirror the Python command name. Run all tests
with:

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'
```

The v0.2.0 full pytest run passed 607/607; the documented unittest runner
passed 605/605. Plain system
pytest does not see the `.venv` packages, so it cannot import the pinned
`langgraph` dependency. Use `PYTHONPATH=.venv/lib/python3.12/site-packages:scripts pytest -q`
or the documented `.venv/bin/python -m unittest` command. CI installs the
dependency from `requirements-pipeline.txt`. Current benchmark refreshes use saved ASR outputs
and dependency-free local translation/retrieval diagnostics; fresh NLLB, dense
retrieval, and SraVaani inference are blocked by uncached model weights and
missing runtime packages. No paid Hugging Face job was started for those
refreshes. See the dated reports linked from the project README.

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

`score_benchmark_predictions.py` scores existing Garhwali-to-English FLORES,
CrossSum, or XORQA predictions on dev by default and writes predictions, a
metric report, and the shared hash-linked run manifest. It maps references to
`source_example.target`, `source_example.summary`, and
`source_example.translated_answers[*].text`; requires exact row-ID coverage;
and requires `--allow-historical-test` for test scoring. It preserves rows with
missing target-language references while excluding them from the metric
denominator. Translation BLEU/chrF remain explicitly identified as the
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
