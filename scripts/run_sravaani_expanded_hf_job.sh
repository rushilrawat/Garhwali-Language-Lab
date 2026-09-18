#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'nemo_toolkit[asr,cu12]' \
  pytorch-lightning \
  omegaconf

python /workspace/scripts/sweep_sravaani_garhwali.py \
  --data /data \
  --checkpoint /tmp/SraVaani-nemo-checkpoint.nemo \
  --output /output \
  --plan-mode expanded_human \
  --max-runtime-seconds 4500
