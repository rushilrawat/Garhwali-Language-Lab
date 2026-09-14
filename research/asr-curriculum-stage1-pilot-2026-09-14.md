# ASR curriculum stage-1 machine-label pilot

Date: 2026-09-14  
Run: `garhwali-whisper-curriculum-stage-1-pilot-h32-m2048-v0.1`

## Decision

The bounded stage-1 configuration is rejected. It completed training and fixed
validation successfully, but it did not improve either required accuracy metric.
The human-only Whisper-tiny `v0.2` checkpoint remains selected, a full stage-1
run is not justified, and stage 2 remains locked.

No source row or machine transcript was removed or quarantined. All machine
labels remain available in the complete experimental curriculum.

## Pilot design

The deterministic, audio-hash-sorted sample contained 32 human-reference rows
and 2,048 standard SraVaani machine-label rows. The machine weights sum to
32.071795, close to the 32.0 human weight mass. The run therefore exposed the
trainer to 2,080 records, 2.536038 audio hours, and 64.071795 total nominal loss
mass.

Training resumed from the registered stage-0 checkpoint and used one epoch,
2,080 optimizer updates, a `5e-6` learning rate, and Apple Metal. Mean raw loss
was 0.661673 and mean weighted loss was 0.018370. The generated checkpoint is
148 MB and remains ignored by Git with the other model artifacts.

## Fixed-validation result

Both models were evaluated on the same 269 human-reference validation records,
4,980 reference words, and 17,342 reference characters. The registration command
recomputed the pilot scores from every saved prediction and verified each
reference against the frozen validation manifest.

| Model | Word errors | WER | Character errors | CER |
| --- | ---: | ---: | ---: | ---: |
| Stage-0 Whisper-tiny `v0.2` | 3,887 | **0.780522** | 8,029 | **0.462980** |
| Stage-1 pilot | 3,905 | 0.784137 | 8,030 | 0.463038 |

The pilot added 18 word errors and one character error. WER increased by
0.003614, or 0.4631% relative, and CER increased by 0.000058, or 0.0125%
relative. Promotion requires both WER and CER to be lower than stage 0, so the
result fails the rule.

This outcome also shows a limitation in the current one-record-per-update
training design. Scaling a single record's loss before an AdamW update does not
guarantee that its influence falls in direct proportion to the nominal weight.
A later machine-label experiment should first combine human and machine examples
inside accumulated batches, normalize weighted batch loss, and prove the update
mixture on a bounded ablation. Repeating the full stage with the present update
scheme would spend substantially more compute without positive validation
evidence.

## Reproducibility

```bash
.venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 1 \
  --resume-from models/whisper-tiny-garhwali-v0.2 \
  --pilot-human 32 \
  --pilot-machine 2048 \
  --dry-run \
  --dry-run-report data/processed/evaluation/asr/curriculum_stage_1_pilot/dry_run_report.json

PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 1 \
  --resume-from models/whisper-tiny-garhwali-v0.2 \
  --pilot-human 32 \
  --pilot-machine 2048 \
  --epochs 1 \
  --learning-rate 5e-6 \
  --save-every 500 \
  --device mps

PYTHONPATH=scripts .venv/bin/python scripts/register_asr_stage1_pilot.py
```

The pilot selector refuses incomplete human/machine limits and marks every
bounded run `training_complete: false`, so it cannot unlock the next curriculum
stage. The compact ignored report records hashes for the model, training report,
predictions, and frozen validation manifest. Validation generation now uses one
explicit length control to avoid ambiguous Transformers settings in later runs.
