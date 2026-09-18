#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  'peft==0.17.1' \
  sentencepiece

hf download bigscience/mt0-small \
  --revision 8116a34237e19160ec003147e758f065876d95f0 \
  --include '*.json' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/mt0-small

PYTHONPATH=/workspace/scripts python /workspace/scripts/evaluate_mt0_generation_checkpoints.py \
  --data /data \
  --model /tmp/mt0-small \
  --old-checkpoints /checkpoints-old \
  --new-checkpoints /checkpoints-new \
  --output /output
