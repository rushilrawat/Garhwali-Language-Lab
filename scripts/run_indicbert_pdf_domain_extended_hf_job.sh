#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  'peft==0.17.1' \
  sentencepiece

hf download ai4bharat/IndicBERTv2-MLM-only \
  --revision 8598f13fe52443bc3fc054fcd665944560145b5c \
  --include '*.json' '*.model' '*.bin' '*.safetensors' \
  --local-dir /tmp/indicbertv2

python /workspace/scripts/run_indicbert_lora_adaptation.py \
  --train /data/train.jsonl \
  --validation /data/validation.jsonl \
  --output /output/report.json \
  --checkpoint-dir /output/checkpoints \
  --model-path /tmp/indicbertv2 \
  --device cuda \
  --steps 32768 \
  --training-records 25983 \
  --evaluation-records 615 \
  --learning-rate 0.00005 \
  --seeds 17,29,43
