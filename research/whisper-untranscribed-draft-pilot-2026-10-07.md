# Whisper drafts for untranscribed VAANI audio — 2026-10-07

## Pilot

Generated a separate alternate-hypothesis file for the 100 highest-priority
rows from `data/processed/model_ready/transcripts/untranscribed_queue.jsonl`,
using `models/whisper-tiny-garhwali-cpu-v0.1` on CPU. All 100 unique audio
records are from `ARTPARK-IISc/Vaani` and carry `CC-BY-4.0` metadata. The clips
total about 1.8 minutes.

- Drafts: `data/processed/model_ready/transcripts/machine_drafts_whisper_cpu_v0.1.jsonl`
- Run metadata and hashes: `data/processed/model_ready/transcripts/machine_drafts_whisper_cpu_v0.1_pilot_report.json`
- Empty drafts: 0; Devanagari outputs: 100.
- Every row remains `training_eligible=false` and
  `review_status=machine_draft_noisy_experimental`.
- Weight SHA-256: `2b815ed2a1a201309aeca2fa38f218318a480d9e7c4e121a99c26f1ae86f7d29`.

## Interpretation

These audio records do not have human transcripts. The project already has
SraVaani machine drafts for all 104,542 source rows, and an older Whisper v0.2
draft for these same 100 rows. The new model is a third hypothesis, not a new
gold transcript.

On this 100-row pilot, mean WER/CER disagreement with the SraVaani draft was
0.7243 / 0.3983; disagreement with the older Whisper v0.2 draft was
0.5888 / 0.2918. These are agreement statistics only, not accuracy measures.
The separate held-out evaluation of this checkpoint found WER 0.7480 on 338
previously-unscored VAANI records. Together, these results support keeping the
new drafts in a review queue, not promoting them automatically into training
splits.

## Resume

The resumable command below processes the rest of the source queue into the
same separate output file. It may take many hours on CPU; review the pilot
before running it on the full queue.

```bash
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/transcribe_vaani_drafts.py \
  --model models/whisper-tiny-garhwali-cpu-v0.1 \
  --input data/processed/model_ready/transcripts/untranscribed_queue.jsonl \
  --output data/processed/model_ready/transcripts/machine_drafts_whisper_cpu_v0.1.jsonl \
  --max-records 0 --device cpu --local-files-only
```
