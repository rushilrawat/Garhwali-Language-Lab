#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  soundfile

hf download openai/whisper-small \
  --revision 973afd24965f72e36ca33b3055d56a652f456b4d \
  --include '*.json' '*.txt' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/whisper-small

PYTHONPATH=/workspace/scripts python /workspace/scripts/transcribe_whisper_agreement.py \
  --data /data \
  --output /output \
  --model /tmp/whisper-small \
  --batch-size 16
