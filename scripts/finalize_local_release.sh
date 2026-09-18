#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
export PYTHONPATH="scripts${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1

"$PYTHON_BIN" scripts/integrate_whisper_turbo_evidence.py
"$PYTHON_BIN" scripts/integrate_reocr_evidence.py
"$PYTHON_BIN" scripts/prepare_text_corpus.py
"$PYTHON_BIN" scripts/build_all_data_view.py
"$PYTHON_BIN" scripts/clean_text_corpus.py
"$PYTHON_BIN" scripts/deep_cleanup.py
"$PYTHON_BIN" scripts/segment_text_corpus.py
"$PYTHON_BIN" scripts/tag_language_quality.py
"$PYTHON_BIN" scripts/build_dataset_splits.py
"$PYTHON_BIN" scripts/build_language_resources.py
"$PYTHON_BIN" scripts/build_garhwali_benchmark.py
"$PYTHON_BIN" scripts/build_instruction_dataset.py
"$PYTHON_BIN" scripts/build_instruction_accuracy_split.py
"$PYTHON_BIN" scripts/build_quality_tiers.py
"$PYTHON_BIN" scripts/build_huggingface_dataset.py \
  --profile public \
  --output data/huggingface/garhwali-language-lab
"$PYTHON_BIN" scripts/build_huggingface_dataset.py \
  --profile all-data \
  --output data/huggingface/garhwali-language-lab-all-data
"$PYTHON_BIN" scripts/build_release_manifest.py
"$PYTHON_BIN" scripts/sync_release_index.py
"$PYTHON_BIN" scripts/audit_final_release.py
"$PYTHON_BIN" scripts/validate_hf_package_cloud.py \
  --package data/huggingface/garhwali-language-lab-all-data \
  --output data/processed/evaluation/data_quality/hf_package_local_validation
"$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'
