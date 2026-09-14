# ASR curriculum stage-0 selection

Date: 2026-09-14  
Run: `garhwali-whisper-curriculum-stage-0-selection-v0.1`

## Decision

`models/whisper-tiny-garhwali-v0.2` is registered as the stage-0 checkpoint.
It is the stronger of the two existing Whisper-tiny checkpoints trained only on
the strict human-reference set. Stage 1 can load it directly, without retraining
the same data or storing another 151 MB copy of its weights.

The registration verifies that curriculum stage 0 and the original strict
training split contain the same 1,621 unique audio hashes and the same target for
every hash. Both checkpoints therefore satisfy the stage-0 data definition.

## Human-only validation comparison

| Checkpoint | Validation records | WER | CER |
| --- | ---: | ---: | ---: |
| Whisper-tiny `v0.1` | 269 | 0.875100 | 0.495964 |
| Whisper-tiny `v0.2` | 269 | **0.780522** | **0.462980** |
| SraVaani 1.0 comparator | 269 | **0.433936** | **0.189252** |

Relative to `v0.1`, `v0.2` reduces validation WER by 10.81% and CER by 6.65%.
SraVaani remains substantially stronger: its WER is 44.40% lower and CER is
59.12% lower than the selected local checkpoint on these same records.

The `v0.1` validation inference ran locally on Apple Metal in 86.054 seconds.
The `v0.2` and SraVaani results were recomputed by filtering their existing
381-record, training-disjoint calibration predictions to the exact 269
validation hashes. All three summaries contain 4,980 reference words and 17,342
reference characters.

The older 112-record test split informed earlier Whisper iteration, as already
documented in the corpus status report. It is not presented as a pristine final
benchmark for these checkpoints. Curriculum stages now default to validation so
the test split is not repeatedly used for further stage decisions.

## Reproducibility

```bash
.venv/bin/python scripts/register_asr_stage0.py
```

The command:

1. verifies strict/stage-0 hash and transcript equivalence;
2. recomputes same-validation metrics for both human-only checkpoints and the
   SraVaani comparator;
3. selects the human-only checkpoint with the lowest validation CER;
4. writes the ignored selection report under
   `data/processed/evaluation/asr/curriculum_stage_0/`; and
5. writes `curriculum_stage_report.json` beside the selected checkpoint so the
   trainer can verify it as a completed immediate predecessor.

The original checkpoint report and weights remain unchanged. No model weights
are copied.

## Stage-1 readiness

A full dependency-free resume dry run passed with the selected checkpoint:

- 104,967 training records;
- 128.694202 training hours;
- 3,239.404158 effective loss mass;
- 269 human-only validation records;
- zero missing audio, empty targets, or duplicate training hashes.

The next compute phase is a bounded stage-1 machine-label pilot. It should prove
that weighted optimization and checkpoint output work end to end before the full
103,346-record SraVaani tier is scheduled.
