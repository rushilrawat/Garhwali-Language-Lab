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

The 2026-09-26 full-suite result is 519 passing tests. Current benchmark refreshes
use saved ASR outputs and dependency-free local translation/retrieval diagnostics;
fresh NLLB, dense retrieval, and SraVaani inference are blocked by uncached model
weights and missing runtime packages. No paid Hugging Face job was started for
those refreshes. See the dated reports linked from the project README.

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

`build_benchmark_usage_labels.py` verifies exact XORQA question and source
context overlaps against the current benchmark hash. It writes a local-only
row-level usage overlay under the same ignored directory; all rows are retained,
and flagged rows are limited to open diagnostics rather than independent
source-generalization claims. The reviewed findings are tracked in
[`research/benchmark-overlap-adjudication-2026-09-26.md`](../research/benchmark-overlap-adjudication-2026-09-26.md).

`validate_benchmark_v02.py` validates the current benchmark manifest, three
external task datasets, internal text/ASR views, and recommended text splits.
It checks source hashes, record counts and IDs, NFC text hashes, task references,
rights/provenance declarations, splits, and local ASR file hashes. Its report is
a local draft-contract audit; it does not freeze v0.2 or clear rights.

`build_benchmark_v02.py` adapts the same eight views into a deterministic,
ignored local draft at `data/processed/evaluation/garhwali_bench/v0.2-draft/`.
It retains each legacy row, separates available source/scoring text, pins
normalizer IDs, validates the XORQA usage-overlay hashes, and verifies output
hashes/counts. The metric signatures are still drafts; no model scores or
rights clearance are produced. The package contains local ASR identifiers and
must not be uploaded as-is. See
[`benchmark-v02-export-2026-09-26.md`](../research/benchmark-v02-export-2026-09-26.md).

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
