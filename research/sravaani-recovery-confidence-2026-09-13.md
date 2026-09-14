# SraVaani recovery confidence calibration

The 1,188 SraVaani recovery recordings have no audio-hash overlap with any of
the 5,894 human-transcribed VAANI records. Row-level WER, CER, or correctness
cannot therefore be measured for this set. This phase uses the separate frozen
112-record human-reference benchmark to calibrate a **review-priority signal**;
it does not treat that signal as a probability of transcript correctness.

## Human-reference evidence

Both models were compared on the same 112 audio hashes and identical normalized
references.

| Result on the 112 human references | Records |
| --- | ---: |
| SraVaani has lower row-level CER | 108 |
| Local Whisper v0.2 has lower row-level CER | 3 |
| Equal row-level CER | 1 |

| Cross-model agreement | Records | SraVaani CER | Whisper CER |
| --- | ---: | ---: | ---: |
| Strong (`>= 0.75`) | 22 | 0.1255 | 0.2516 |
| Moderate (`>= 0.50`) | 77 | 0.1712 | 0.3973 |
| Weak (`>= 0.25`) | 13 | 0.2685 | 0.6483 |
| Minimal (`< 0.25`) | 0 | — | — |

Agreement is negatively correlated with error: Pearson correlation is -0.453
for SraVaani CER and -0.882 for Whisper CER. The monotonic CER increase from
strong to weak agreement supports agreement as a useful review-ordering signal.
It does not override the stronger SraVaani result.

## Recovery-set confidence

| Result | Records |
| --- | ---: |
| Medium review confidence | 30 |
| Low review confidence | 35 |
| Very-low review confidence | 1,123 |
| Minimal cross-model agreement | 1,074 |
| Selected candidate still has a structural flag | 99 |
| Same-record human references | 0 |
| Automatic promotions | 0 |

The 1,074 minimal-agreement rows fall outside the agreement range represented in
the human benchmark. They receive an explicit out-of-support penalty and a
very-low band. Confidence is capped at medium for every recovery row because no
same-record human reference exists.

The score combines the selected model's CER in the matching benchmark agreement
bin, cross-model character agreement, a structural-flag penalty, and an
out-of-support penalty. Each output records the formula inputs and states
`confidence_is_accuracy_probability: false`.

All 1,188 records remain active experimental data. Originals and both model
hypotheses are preserved, no record is quarantined, and none becomes eligible
for supervised training.

## Reproduction

```bash
.venv/bin/python scripts/calibrate_sravaani_recovery_confidence.py
```

Generated artifacts remain ignored by Git:

- `data/processed/model_ready/transcripts/sravaani_recovery_confidence.jsonl`
- `data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json`

The report stores SHA-256 hashes for the recovery input, the 5,894-row human
transcript manifest, and both 112-row benchmark prediction files.
