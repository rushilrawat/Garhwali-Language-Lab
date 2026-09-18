#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'sentence-transformers==5.1.1' \
  'faiss-cpu==1.12.0' \
  'huggingface_hub[cli]'

python /workspace/scripts/audit_semantic_duplicates.py \
  --input /data \
  --output /output \
  --threshold 0.92 \
  --neighbors 12 \
  --limit 200000 \
  --batch-size 128
