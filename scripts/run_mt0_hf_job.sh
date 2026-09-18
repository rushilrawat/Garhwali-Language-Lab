#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  'peft==0.17.1' \
  sentencepiece

hf download bigscience/mt0-small \
  --revision 8116a34237e19160ec003147e758f065876d95f0 \
  --local-dir /tmp/mt0-small

python /workspace/scripts/run_mt5_instruction_tuning.py \
  --data-dir /data \
  --output-dir /output \
  --checkpoint-dir /output/checkpoints \
  --model-path /tmp/mt0-small \
  --model-id bigscience/mt0-small \
  --revision 8116a34237e19160ec003147e758f065876d95f0 \
  --run-id garhwali-mt0-instruction-lora-cloud-v0.3 \
  --device cuda \
  --steps 2048 \
  --training-records 2046 \
  --validation-records 130 \
  --seeds 17,29,43 \
  --skip-test
