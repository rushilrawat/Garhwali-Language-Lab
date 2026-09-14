# Confidence-aware ASR training curriculum

Date: 2026-09-14  
Run: `garhwali-asr-confidence-curriculum-v0.1`

## Outcome

The project now has a deterministic ASR curriculum that combines the strict
human-reference training split with every unique SraVaani machine-labelled
recording. It retains all machine audio in the experimental training view while
keeping the human validation and test sets isolated.

| Split | Records | Labels | Use |
| --- | ---: | --- | --- |
| Train | 106,155 | 1,621 human + 104,534 machine | staged, confidence weighted |
| Validation | 269 | human only | model selection |
| Test | 112 | human only | final comparison |

The train manifest covers 129.564 hours: 2.870 human-reference hours and 126.693
machine-labelled hours. The 104,542 machine source rows reduce to 104,534 unique
audio hashes because eight source rows repeat an existing recording. No unique
audio was removed, and no audio hash overlaps the human train, validation, or
test manifests.

## Curriculum

1. Stage 0: 1,621 human-reference rows.
2. Stage 1: add 103,346 standard SraVaani rows.
3. Stage 2: add 30 medium-confidence recovery rows.
4. Stage 3: add 35 low-confidence recovery rows.
5. Stage 4: add 1,123 very-low-confidence recovery rows.

All machine rows receive a positive `sample_weight`. Standard SraVaani rows use
the expanded 381-reference character-accuracy calibration score of 0.814594.
Recovery rows use their conservative cross-model confidence score. These scores
rank evidence; they are not calibrated probabilities that a transcript is
correct.

The weights are normalized so the entire 104,534-row machine collection has the
same effective loss mass as the 1,621 human training references. This prevents
the much larger pseudo-labelled set from overwhelming human labels while still
using every recording. The resulting mass is 1,621.000 for human references and
1,620.999999 for machine labels after per-row rounding.

One 1.923-second recovery row had an empty preferred SraVaani hypothesis. The
builder uses its non-empty Whisper alternative, marks the choice as
`nonempty_candidate_fallback`, keeps the very-low confidence tier and associated
quality flags, and assigns only 0.001708 effective weight. The final manifests
contain zero empty targets.

## Reproducibility and checks

```bash
.venv/bin/python scripts/build_asr_training_curriculum.py
```

The command writes the ignored local artifacts under
`data/processed/model_ready/asr_curriculum/`:

- `train.jsonl`, `validation.jsonl`, and `test.jsonl`
- `stage_plan.json`
- `report.json` with input/output hashes and count checks

The builder fails on conflicting duplicate machine transcripts, conflicting
recovery evidence, human split overlap, machine-to-human overlap, non-positive
machine weight mass, or an audio record with no non-empty transcript candidate.
Generated data remains outside Git; the builder, tests, report integration, and
this methodology note are tracked.

## Trainer integration

The Whisper trainer now selects curriculum stages, applies `sample_weight` to
each single-record loss, verifies immediate-predecessor checkpoints between
stages, and provides a dependency-free full-manifest dry run. Implementation and
validation results are documented in
[`asr-weighted-trainer-2026-09-14.md`](asr-weighted-trainer-2026-09-14.md).
