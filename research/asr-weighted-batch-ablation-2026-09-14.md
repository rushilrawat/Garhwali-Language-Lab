# ASR normalized weighted-batch ablation

Date: 2026-09-14  
Run: `garhwali-whisper-stage-1-weighted-batch-pilot-h32-m2048-v0.1`

## Decision

The normalized weighted-batch stage-1 pilot is rejected. The trainer redesign
correctly combines human and machine gradients before each optimizer update, but
the fixed validation result is worse than both stage 0 and the original stage-1
pilot. The human-only Whisper-tiny `v0.2` checkpoint remains selected, stage 2
stays locked, and this machine-label curriculum recipe will not run at full scale.

All source audio and machine transcripts remain active in the complete
experimental corpus. No record was deleted, quarantined, or silently promoted.

## Trainer redesign

The first pilot applied a scalar weight to one record immediately before each
AdamW update. An adaptive optimizer can largely absorb that scale, so 2,048
machine updates could still dominate 32 human updates despite equal nominal loss
mass.

The new explicit `--weighted-batches` mode:

1. sorts human and machine rows by immutable audio hash;
2. creates one batch for each human anchor;
3. distributes machine rows round-robin across those batches;
4. normalizes record weights by total weight inside each batch;
5. accumulates the normalized gradients; and
6. takes one optimizer step after the complete mixed batch.

For this exact pilot, each of 32 batches contains one human record and 64 machine
records. Human mass is 1.0 per batch and machine mass is 1.002244, producing an
approximately equal gradient objective. The run processes the same 2,080 records
and 2.536038 hours as the original pilot, while taking 32 optimizer steps instead
of 2,080. The original path remains available for exact reproduction, and the
weighted output is written to a separate ignored model directory.

## Fixed-validation result

Every result below uses the same 269 human-reference validation rows, 4,980
reference words, and 17,342 reference characters.

| Model | Word errors | WER | Character errors | CER |
| --- | ---: | ---: | ---: | ---: |
| Stage-0 Whisper-tiny `v0.2` | 3,887 | **0.780522** | 8,029 | **0.462980** |
| Original one-record pilot | 3,905 | 0.784137 | 8,030 | 0.463038 |
| Normalized weighted-batch pilot | 3,925 | 0.788153 | 8,041 | 0.463672 |

Relative to stage 0, the weighted pilot adds 38 word errors and 12 character
errors. WER increases by 0.007631, or 0.9776% relative, and CER increases by
0.000692, or 0.1495% relative. It also adds 20 word and 11 character errors over
the first pilot.

Paired scoring shows lower row-level CER for 131 records, higher CER for 97, and
41 ties. WER improves on 89, worsens on 93, and ties on 87. The larger regression
magnitudes outweigh the number of CER improvements, which is why promotion uses
aggregate error counts rather than a majority-of-records rule.

## Reproducibility

```bash
.venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 1 \
  --resume-from models/whisper-tiny-garhwali-v0.2 \
  --pilot-human 32 \
  --pilot-machine 2048 \
  --weighted-batches \
  --dry-run \
  --dry-run-report data/processed/evaluation/asr/curriculum_stage_1_weighted_batch_pilot/dry_run_report.json

PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 1 \
  --resume-from models/whisper-tiny-garhwali-v0.2 \
  --pilot-human 32 \
  --pilot-machine 2048 \
  --weighted-batches \
  --epochs 1 \
  --learning-rate 5e-6 \
  --save-every 8 \
  --device mps

PYTHONPATH=scripts .venv/bin/python scripts/register_asr_stage1_weighted_batch_pilot.py
```

The registration command verifies all saved predictions against the frozen
validation references, recomputes aggregate and paired metrics, checks the exact
32-by-65 training shape, and records hashes for the model, predictions, report,
and validation manifest. The compact report is included in the generated local
release manifest. The 148 MB model output and all generated data remain ignored
by Git.

## Accuracy direction

Two controlled variants now fail the same promotion gate. More compute on this
Whisper-tiny text-pseudo-label recipe lacks positive validation evidence. The
next speech-accuracy experiment should start from the substantially stronger
SraVaani checkpoint and adapt it only with human references, or wait for new
human transcripts. That keeps the strongest available speech model as the
starting point and avoids another round of self-distillation into a weaker model.
