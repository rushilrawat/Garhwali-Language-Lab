#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir 'huggingface_hub[cli]' 'transformers==4.56.2' sentencepiece
hf download ai4bharat/IndicBERTv2-MLM-only \
  --revision 8598f13fe52443bc3fc054fcd665944560145b5c \
  --include '*.json' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/indicbertv2
python /workspace/scripts/validate_ocr_corrections.py \
  --input /data/priority.jsonl --output /output \
  --model-path /tmp/indicbertv2 --device cuda
