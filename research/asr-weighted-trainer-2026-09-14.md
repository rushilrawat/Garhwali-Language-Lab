# Weighted curriculum trainer and dry-run audit

Date: 2026-09-14  
Dry-run ID: `garhwali-whisper-curriculum-dry-run-v0.1`

## Implemented behavior

The existing Whisper trainer can now consume the confidence-aware curriculum
without changing its model architecture or human-only evaluation procedure.

- `--curriculum-stage 0` through `4` selects rows whose `introduced_stage` is no
  greater than the requested stage.
- Every single-record training loss is multiplied by that record's positive
  `sample_weight`. Human references retain weight 1.0.
- Reports keep both mean raw loss and mean weighted loss, plus the effective
  training mass, curriculum stage, and evaluation split.
- The legacy strict-supervised command still reads `asr_target_clean` and assigns
  implicit weight 1.0.
- Stage-specific defaults write to separate model directories, protecting the
  existing `whisper-tiny-garhwali-v0.1` checkpoint.

The later `--weighted-batches` mode fixes the optimizer-level weakness found by
the first stage-1 pilot. It distributes machine rows deterministically across
human anchors, accumulates every record's gradient after normalizing by total
batch weight, and takes one optimizer step per mixed batch. The original
one-record behavior remains the default so the first pilot stays reproducible;
weighted runs use a separate `-weighted-batches` output directory.

For stages 1 through 4, a real training run must provide `--resume-from`. The
trainer accepts only a completed immediate predecessor and verifies its report,
model weights, model configuration, processor configuration, and tokenizer
before loading it. This supports deliberate stage-to-stage continuation and
prevents a later stage from silently starting from the wrong checkpoint.

## Full dry-run result

```bash
.venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 4 \
  --dry-run
```

| Check | Result |
| --- | ---: |
| Training records | 106,057 |
| Validation records | 269 |
| Training audio | 129.310351 hours |
| Effective loss mass | 3,241.999996 |
| Empty training targets | 0 |
| Empty evaluation targets | 0 |
| Duplicate training audio hashes | 0 |
| Missing local audio files | 0 |
| Validation status | passed |

The default curriculum evaluation is the 269-row human-only validation split,
which keeps the 112-row final test set out of stage decisions. An explicit
`--eval-split test` dry run also confirms that all 112 final-test records and
audio paths are complete.

The effective mass is 1,621.0 from human references plus 1,620.999996 from the
104,436 eligible machine-labelled recordings after per-row rounding. The 98
source-label-conflict drafts remain preserved outside Garhwali loss. Stage 0 was also run
independently and selected exactly 1,621 human-reference rows, 2.870413 hours,
and 1,621.0 effective weight.

The dry-run path completes before Torch and Transformers are imported. It reads
the real manifests and checks the real local audio paths, so the validation can
run cheaply even when the separate ASR runtime is not installed.

The generated report is stored at
`data/processed/model_ready/asr_curriculum/trainer_dry_run_report.json` and is
included in the local release manifest. Generated data and model outputs remain
Git-ignored.

## Training commands

Stage 0 starts from the pinned base model:

```bash
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 0 \
  --device mps
```

After stage 0 completes, stage 1 must load its output explicitly:

```bash
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/train_whisper_garhwali.py \
  --curriculum-stage 1 \
  --resume-from models/whisper-tiny-garhwali-curriculum-stage-0 \
  --device mps
```

The same immediate-predecessor rule applies through stage 4. Each completed
stage evaluates on the 269 human-reference validation recordings and writes a
`training_complete` report for the next stage. The final 112-record test is run
only after stage selection by passing `--eval-split test` explicitly.

## Stage-0 continuation

The two existing local checkpoints were trained only on the exact stage-0 human
data, so the stronger `whisper-tiny-garhwali-v0.2` checkpoint was selected by
human-only validation CER rather than duplicating its training or weights. The
equivalence proof, 269-record comparison, and stage-1 readiness check are in
[`asr-curriculum-stage0-2026-09-14.md`](asr-curriculum-stage0-2026-09-14.md).

The 32-batch controlled ablation is documented in
[`asr-weighted-batch-ablation-2026-09-14.md`](asr-weighted-batch-ablation-2026-09-14.md).
It verifies that the optimizer now receives normalized mixed gradients, but the
result still worsens validation WER and CER, so the full stage is not promoted.
