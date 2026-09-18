#!/usr/bin/env bash
set -euo pipefail

python -m pip install --no-cache-dir \
  'huggingface_hub[cli]' \
  'transformers==4.56.2' \
  'peft==0.17.1' \
  sentencepiece

hf download ai4bharat/IndicBERTv2-MLM-only \
  --revision 8598f13fe52443bc3fc054fcd665944560145b5c \
  --local-dir /tmp/indicbertv2

python /workspace/scripts/run_indicbert_lora_adaptation.py \
  --train /data/train.jsonl \
  --validation /data/validation.jsonl \
  --output /output/report.json \
  --checkpoint-dir /output/checkpoints \
  --model-path /tmp/indicbertv2 \
  --device cuda \
  --steps 4096 \
  --training-records 106804 \
  --evaluation-records 128 \
  --seeds 17,29,43
