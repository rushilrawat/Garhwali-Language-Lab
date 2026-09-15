# SraVaani risky-draft three-checkpoint review

The 1,090 Garhwali recovery recordings now have a complete comparison across
`ARTPARK-IISc/SraVaani-1.0`, `whisper-tiny-garhwali-v0.1`, and
`whisper-tiny-garhwali-v0.2`. The 98 source-label conflicts remain represented
in their separate registry and are not mixed into this Garhwali review queue.

## Result

| Evidence state | Records |
| --- | ---: |
| Clean proposal with at least 75% agreement between the related Whisper checkpoints | 325 |
| Clean proposal with lower Whisper-checkpoint agreement | 730 |
| Best proposal still has a structural flag | 35 |
| **Total** | **1,090** |

The structurally ranked proposal comes from Whisper `v0.2` for 1,039 records,
Whisper `v0.1` for 33, and SraVaani for 18. This is a review proposal rather
than a corrected transcript. All originals and all three candidates remain
available, all rows remain pending audio review, and none is marked as a human
reference or recommended machine-training label.

## Calibration boundary

The three models overlap on 112 held-out human-referenced recordings. SraVaani
has the lowest row CER, including ties, on 108; Whisper `v0.2` on 3; and Whisper
`v0.1` on 2. Their mean row CER values are 0.183524, 0.390708, and 0.413177,
respectively. None of those 112 SraVaani hypotheses exhibits the failure pattern
that created this queue. The two Whisper checkpoints are also related models.
These facts rule out automatic accuracy promotion from checkpoint agreement.

## Reproduce

```bash
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/transcribe_vaani_drafts.py \
  --input data/processed/model_ready/transcripts/sravaani_recovery_queue.jsonl \
  --output data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.1.jsonl \
  --model models/whisper-tiny-garhwali-v0.1 --max-records 0 --device cpu \
  --local-files-only
PYTHONPATH=scripts .venv/bin/python scripts/build_sravaani_recovery_adjudication.py
```

The machine-readable outputs are
`data/processed/model_ready/transcripts/sravaani_recovery_adjudication.jsonl`,
its adjacent report, and the priority-sorted
`data/processed/review/sravaani_recovery_adjudication.jsonl` queue. The Hugging
Face draft configuration exposes the safe comparison fields without local paths
or raw speaker identifiers.
