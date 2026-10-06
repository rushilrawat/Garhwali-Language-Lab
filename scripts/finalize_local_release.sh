#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
export PYTHONPATH="scripts${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
RELEASE_VERSION="${GARHWALI_RELEASE_VERSION:-0.2.8}"
RELEASE_DIR="release/v${RELEASE_VERSION#v}"
RELEASE_INDEX="release/v${RELEASE_VERSION#v}-manifest.json"

if [[ ! -f "$RELEASE_INDEX" ]]; then
  cp release/v0.1.1-manifest.json "$RELEASE_INDEX"
  "$PYTHON_BIN" - "$RELEASE_INDEX" "$RELEASE_VERSION" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
version = sys.argv[2].removeprefix('v')
index = json.loads(path.read_text(encoding='utf-8'))
index['release_id'] = f'garhwali-language-lab-v{version}'
index['status'] = 'preparing_v' + version
path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
PY
fi

"$PYTHON_BIN" scripts/ingest_obs_tlf.py
"$PYTHON_BIN" scripts/ingest_upreti_1894_garhwali.py
"$PYTHON_BIN" scripts/ingest_lsi_garhwali_table.py
"$PYTHON_BIN" scripts/ingest_lsi_garhwali_specimens.py
"$PYTHON_BIN" scripts/audit_garhwali_expansion.py

"$PYTHON_BIN" scripts/integrate_whisper_turbo_evidence.py
"$PYTHON_BIN" scripts/integrate_sravaani_confidence.py
"$PYTHON_BIN" scripts/build_asr_training_curriculum.py
"$PYTHON_BIN" scripts/integrate_reocr_evidence.py
"$PYTHON_BIN" scripts/promote_paharili_garhwali.py
"$PYTHON_BIN" scripts/prepare_text_corpus.py
"$PYTHON_BIN" scripts/build_all_data_view.py
"$PYTHON_BIN" scripts/clean_text_corpus.py
"$PYTHON_BIN" scripts/deep_cleanup.py
"$PYTHON_BIN" scripts/segment_text_corpus.py
"$PYTHON_BIN" scripts/tag_language_quality.py
"$PYTHON_BIN" scripts/build_dataset_splits.py
"$PYTHON_BIN" scripts/build_quality_tiers.py
"$PYTHON_BIN" scripts/build_recommended_text_view.py
"$PYTHON_BIN" scripts/build_language_resources.py
"$PYTHON_BIN" scripts/build_garhwali_benchmark.py
"$PYTHON_BIN" scripts/build_instruction_dataset.py
"$PYTHON_BIN" scripts/build_instruction_accuracy_split.py
"$PYTHON_BIN" scripts/build_huggingface_dataset.py \
  --profile public \
  --output data/huggingface/garhwali-language-lab
"$PYTHON_BIN" scripts/build_huggingface_dataset.py \
  --profile all-data \
  --output data/huggingface/garhwali-language-lab-all-data
"$PYTHON_BIN" scripts/build_hf_reference_index.py
"$PYTHON_BIN" scripts/build_release_manifest.py
"$PYTHON_BIN" scripts/sync_release_index.py
audit_failed=0
if ! "$PYTHON_BIN" scripts/audit_final_release.py; then
  audit_failed=1
fi
"$PYTHON_BIN" scripts/sync_release_index.py
"$PYTHON_BIN" scripts/validate_release_index.py
"$PYTHON_BIN" scripts/validate_hf_package_cloud.py \
  --package data/huggingface/garhwali-language-lab-all-data \
  --output "$RELEASE_DIR/huggingface-all-data-preflight.json"
"$PYTHON_BIN" scripts/validate_hf_package_cloud.py \
  --package data/huggingface/garhwali-language-lab \
  --output "$RELEASE_DIR/huggingface-public-preflight.json"
"$PYTHON_BIN" scripts/build_hf_upload_plan.py \
  --package data/huggingface/garhwali-language-lab-all-data \
  --output "$RELEASE_DIR/huggingface-all-data-upload.json" \
  --visibility private
"$PYTHON_BIN" scripts/build_hf_upload_plan.py \
  --package data/huggingface/garhwali-language-lab \
  --output "$RELEASE_DIR/huggingface-public-upload.json" \
  --visibility public
env -u GARHWALI_RELEASE_VERSION "$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'
"$PYTHON_BIN" scripts/build_release_bundle.py
"$PYTHON_BIN" scripts/build_release_bundle.py --check
if [[ "$audit_failed" -ne 0 ]]; then
  echo "Final audit failed; release status is blocked." >&2
  exit 1
fi
