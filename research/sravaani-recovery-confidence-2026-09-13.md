# SraVaani recovery confidence calibration

The 1,188 SraVaani recovery recordings have no audio-hash overlap with any of
the 5,894 human-transcribed VAANI records. Row-level WER, CER, or correctness
cannot therefore be measured for this set. Confidence calibration now uses 381
speaker-disjoint validation and test recordings with human references. None
overlaps the 1,621 recordings used to train local Whisper v0.2. The resulting
**review-priority signal** is not a probability of transcript correctness.

## Human-reference evidence

Both models were compared on the same 381 audio hashes and identical normalized
references: 269 validation and 112 test recordings from 50 speakers.

| Result on the 381 human references | Records |
| --- | ---: |
| SraVaani has lower row-level CER | 369 |
| Local Whisper v0.2 has lower row-level CER | 8 |
| Equal row-level CER | 4 |

| Cross-model agreement | Records | SraVaani CER | Whisper CER |
| --- | ---: | ---: | ---: |
| Strong (`>= 0.75`) | 68 | 0.1114 | 0.2223 |
| Moderate (`>= 0.50`) | 225 | 0.1795 | 0.4119 |
| Weak (`>= 0.25`) | 79 | 0.2353 | 0.6275 |
| Minimal (`< 0.25`) | 9 | 0.2893 | 0.8330 |

Agreement is negatively correlated with error: Pearson correlation is -0.499
for SraVaani CER and -0.921 for Whisper CER. The monotonic CER increase from
strong to minimal agreement supports agreement as a useful review-ordering signal.
It does not override the stronger SraVaani result.

## Recovery-set confidence

| Result | Records |
| --- | ---: |
| Medium review confidence | 30 |
| Low review confidence | 35 |
| Very-low review confidence | 1,123 |
| Minimal cross-model agreement | 1,074 |
| Outside a represented calibration agreement band | 0 |
| Selected candidate still has a structural flag | 99 |
| Same-record human references | 0 |
| Automatic promotions | 0 |

The earlier 112-record calibration contained no minimal-agreement example, so
1,074 recovery rows were outside its observed support. The expanded set includes
nine such human-referenced cases. All recovery rows now map to a represented
agreement band, while minimal-agreement rows remain very-low confidence because
that benchmark band has 0.289 SraVaani CER and 0.833 Whisper CER. Confidence is
capped at medium because no same-record human reference exists.

### Change from confidence v0.1

The expanded calibration changes all 1,188 numeric scores and reduces the mean
score from 0.169 to 0.114. Median absolute score change is 0.065. This decrease
is intentional: the earlier calibration used the all-record Whisper CER as a
fallback for 1,074 unsupported minimal-agreement rows, while the expanded human
evidence measures 0.833 CER for that band. The categorical totals remain 30
medium, 35 low, and 1,123 very-low records.

The score combines the selected model's CER in the matching benchmark agreement
bin, cross-model character agreement, a structural-flag penalty, and an
out-of-support penalty. Each output records the formula inputs and states
`confidence_is_accuracy_probability: false`.

All 1,188 records remain active experimental data. Originals and both model
hypotheses are preserved, no record is quarantined, and none becomes eligible
for supervised training.

## Reproduction

```bash
mkdir -p data/processed/evaluation/asr/confidence_calibration
cat data/processed/model_ready/splits/asr/validation.jsonl \
    data/processed/model_ready/splits/asr/test.jsonl \
  > data/processed/evaluation/asr/confidence_calibration/manifest.jsonl
.cache/asr-runtime/bin/python scripts/run_sravaani_comparison.py \
  --input data/processed/evaluation/asr/confidence_calibration/manifest.jsonl \
  --output data/processed/evaluation/asr/confidence_calibration/sravaani \
  --device cpu
.cache/asr-runtime/bin/python scripts/run_whisper_comparison.py \
  --model models/whisper-tiny-garhwali-v0.2 \
  --model-id whisper-tiny-garhwali-v0.2 --revision local-v0.2 \
  --input data/processed/evaluation/asr/confidence_calibration/manifest.jsonl \
  --output data/processed/evaluation/asr/confidence_calibration/whisper_v0.2 \
  --device cpu
.venv/bin/python scripts/calibrate_sravaani_recovery_confidence.py
```

Generated artifacts remain ignored by Git:

- `data/processed/model_ready/transcripts/sravaani_recovery_confidence.jsonl`
- `data/processed/model_ready/transcripts/sravaani_recovery_confidence_report.json`

The report stores SHA-256 hashes for the recovery input, the 5,894-row human
transcript manifest, the Whisper training manifest, and both 381-row prediction
files. It also verifies zero overlap between confidence calibration and Whisper
training audio.
