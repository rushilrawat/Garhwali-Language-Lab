#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'nemo_toolkit[asr,cu12]' \
  pytorch-lightning \
  omegaconf

python /workspace/scripts/train_sravaani_garhwali.py \
  --package-report /data/report.json \
  --data /data \
  --checkpoint /tmp/SraVaani-nemo-checkpoint.nemo \
  --download-checkpoint \
  --output /output/sravaani-garhwali-decoder-pilot-v0.1.nemo \
  --experiments /output/experiments \
  --plan-output /output/plan.json \
  --execute
