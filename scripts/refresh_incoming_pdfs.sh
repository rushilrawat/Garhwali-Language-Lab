#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
DEFAULT_PDF_PYTHON="/Users/rushilrawat/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
PDF_PYTHON_BIN="${PDF_PYTHON_BIN:-$DEFAULT_PDF_PYTHON}"
if [[ ! -x "$PDF_PYTHON_BIN" ]]; then
  PDF_PYTHON_BIN="$PYTHON_BIN"
fi

PYTHONPATH=scripts "$PDF_PYTHON_BIN" scripts/ingest_incoming_pdfs.py
PYTHONPATH=scripts "$PYTHON_BIN" scripts/integrate_reocr_evidence.py
"$PYTHON_BIN" scripts/prepare_text_corpus.py
"$PYTHON_BIN" scripts/build_all_data_view.py
"$PYTHON_BIN" scripts/clean_text_corpus.py
"$PYTHON_BIN" scripts/deep_cleanup.py
"$PYTHON_BIN" scripts/segment_text_corpus.py
"$PYTHON_BIN" scripts/tag_language_quality.py
"$PYTHON_BIN" scripts/build_dataset_splits.py
"$PYTHON_BIN" scripts/build_quality_tiers.py
PYTHONPATH=scripts "$PYTHON_BIN" scripts/build_huggingface_dataset.py --profile all-data

PYTHONPATH=scripts "$PYTHON_BIN" -m unittest \
  tests/test_ingest_incoming_pdfs.py \
  tests/test_prepare_text_corpus.py
