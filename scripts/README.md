# Script layout

`scripts/` contains executable pipeline and research commands. Run Python
commands from the repository root so their paths and generated manifests stay
stable.

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
