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

python /workspace/scripts/run_mt5_instruction_tuning.py \
  --data-dir /data \
  --output-dir /output \
  --checkpoint-dir /output/checkpoints \
  --model-path /tmp/mt0-small \
  --model-id bigscience/mt0-small \
  --revision 8116a34237e19160ec003147e758f065876d95f0 \
  --run-id garhwali-mt0-instruction-lora-32768-seed43-v0.6 \
  --device cuda \
  --steps 32768 \
  --training-records 2178 \
  --validation-records 130 \
  --learning-rate 0.0001 \
  --seeds 43 \
  --skip-test \
  --evaluate-validation-generation
