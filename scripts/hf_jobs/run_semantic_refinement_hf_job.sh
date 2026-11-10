#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'sentence-transformers==5.1.1' \
  'transformers==4.56.2'

python /workspace/scripts/refine_semantic_duplicates.py \
  --input /data/candidates.jsonl \
  --output /output \
  --batch-size 128
