#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir 'huggingface_hub[cli]' 'transformers==4.56.2' sentencepiece
hf download ai4bharat/IndicBERTv2-MLM-only \
  --revision 8598f13fe52443bc3fc054fcd665944560145b5c \
  --include '*.json' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/indicbertv2

python /workspace/scripts/propose_text_cleanup.py \
  --input /data/text.jsonl \
  --output-dir /output \
  --model-records 28755 \
  --device cuda \
  --model-path /tmp/indicbertv2
