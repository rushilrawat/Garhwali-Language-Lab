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
