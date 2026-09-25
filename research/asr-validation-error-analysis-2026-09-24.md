# Saved ASR validation comparison

This is a validation-only reanalysis of existing prediction files. The test rows in those combined files were not parsed or scored.

- Status: `development_only`
- Rows: 269
- Exact row-set SHA-256: `442871fc0c3a312e96e761e5d46a7ddaff041c0a641676c020e6053e3808f2a0`
- Normalization: scripts/asr_metrics.py: NFC, casefold, punctuation/symbol to space, whitespace collapse

| Model | WER | CER | Word errors | Character errors |
|---|---:|---:|---:|---:|
| sravaani | 0.4339 | 0.1893 | 2161 | 3282 |
| whisper_v0.2 | 0.7805 | 0.4630 | 3887 | 8029 |

## Paired record comparison

| Model | Rows with lower WER | Rows with lower CER |
|---|---:|---:|
| sravaani | 249 | 261 |
| whisper_v0.2 | 8 | 5 |

## Limits

Automated-reference comparison only; this validation split has prior evaluation history and does not establish native-speaker correctness or blind generalization.

Prediction and manifest SHA-256 values are in the JSON report.
