#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  soundfile

hf download openai/whisper-large-v3-turbo \
  --revision 41f01f3fe87f28c78e2fbf8b568835947dd65ed9 \
  --include '*.json' '*.txt' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/whisper-large-v3-turbo

PYTHONPATH=/workspace/scripts python /workspace/scripts/transcribe_whisper_agreement.py \
  --data /data \
  --output /output \
  --model /tmp/whisper-large-v3-turbo \
  --model-id openai/whisper-large-v3-turbo \
  --revision 41f01f3fe87f28c78e2fbf8b568835947dd65ed9 \
  --batch-size 16
