#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'nemo_toolkit[asr,cu12]' \
  pytorch-lightning \
  omegaconf

python /workspace/scripts/evaluate_sravaani_finetune.py \
  --checkpoint /output/sravaani-garhwali-decoder-pilot-v0.1.nemo \
  --data /data \
  --output /output/held_out_evaluation \
  --batch-size 4
