# Whisper Tiny CPU fine-tune — 2026-10-07

## Run

- Status: completed locally on CPU; no paid compute was used.
- Initialized from `models/whisper-tiny-garhwali-v0.2`.
- One epoch over 4,778 strict ASR training rows (7.17 hours), 4,778 optimizer steps, seed 17, learning rate `1e-5`.
- Used `data/processed/model_ready/splits/asr_experimental/train.jsonl` and its 666-row validation split. Dry-run checks found no missing audio, duplicate audio, normalized transcript overlap, speaker overlap, or unsafe rows.
- Wall time was about 30 minutes, including validation, on the current CPU-only environment.
- Mean training loss: `0.5872`.

## Same-split validation comparison

Both checkpoints were decoded against the same 666 validation rows, using the same language prompt and greedy decoding settings.

| Checkpoint | WER | CER |
| --- | ---: | ---: |
| Before fine-tuning (`whisper-tiny-garhwali-v0.2`) | 0.7830 | 0.4540 |
| After one CPU epoch | 0.7197 | 0.4090 |
| Change | -0.0632 | -0.0450 |

WER improved by 6.32 percentage points and CER by 4.50 percentage points on validation. This is a development-set result, not an independent final benchmark.

## Held-out comparison

After the validation comparison, both checkpoints were evaluated once on the same 449 rows from the 450-row held-out test split. The one previously exposed row was excluded.

| Checkpoint | WER | CER |
| --- | ---: | ---: |
| Before fine-tuning (`whisper-tiny-garhwali-v0.2`) | 0.8026 | 0.4593 |
| After one CPU epoch | 0.7245 | 0.4245 |
| Change | -0.0781 | -0.0348 |

### Prior-checkpoint evaluation exposure

A lineage check after this run found that the starting checkpoint (`whisper-tiny-garhwali-v0.2`) had already been scored on all 112 records in the older `asr/test` split. Those 112 records are also contained in the current 450-row experimental test split. The timing-probe row excluded above is one of those 112; the 449-row predictions therefore include 111 rows whose audio had already been scored for the starting checkpoint.

For a less exposed comparison, I recomputed aggregate WER/CER on the 338 rows in the current 449-row predictions that do not appear in the older checkpoint's saved evaluation predictions:

| Checkpoint | WER | CER |
| --- | ---: | ---: |
| Before fine-tuning (`whisper-tiny-garhwali-v0.2`) | 0.8325 | 0.4847 |
| After fine-tuning | 0.7480 | 0.4349 |

Use this 338-row previously-unscored subset as the primary diagnostic comparison. It improved by 8.45 WER points and 4.98 CER points. It is still a development result on the same VAANI source family, not an independent final benchmark. The broader 449-row comparison is retained above for lineage completeness, but includes 111 rows already scored during development of the starting checkpoint; on those 449 rows, the difference was 7.81 WER points and 3.48 CER points.

The 449-row evaluation manifest has SHA-256 `02dcc08d412b590c7cfc1c64dc761ae49181b605424613f6074e1b65e94bb58f`.

## Artifacts

- Fine-tuned model and training/validation report: `models/whisper-tiny-garhwali-cpu-v0.1/`
- Fine-tuned validation predictions: `models/whisper-tiny-garhwali-cpu-v0.1/evaluation_predictions.jsonl`
- Previous-checkpoint baseline report and predictions on validation: `data/processed/evaluation/asr/whisper_tiny_v02_same_validation_cpu_2026-10-07/`
- Baseline and fine-tuned held-out reports/predictions (449 rows): `data/processed/evaluation/asr/whisper_cpu_final_test_2026-10-07/`
- Primary previously-unscored subset: recomputed from the saved 449-row prediction files after excluding audio hashes in `models/whisper-tiny-garhwali-v0.2/evaluation_predictions.jsonl`.
- Training manifest SHA-256: `3812dd8d83b4488a604a463456a666e94251b02698c12c42b823fbc5aebd5f84`
- Validation manifest SHA-256: `d7f4e7605b9e1a48d4e4facc1df02eb21fd15497a67a37067b9a324b4956596f`
- Trained weight SHA-256: `2b815ed2a1a201309aeca2fa38f218318a480d9e7c4e121a99c26f1ae86f7d29`

## Held-out test note

The full fine-tune and the same-split baseline comparison used validation only. A separate two-clip CPU timing probe earlier inherited the trainer's default test evaluation and scored one item. That item was not used for training or model selection; it was excluded from the 449-row held-out comparison:

`audio_sha256 = 0061e1574d9370e8bbfa65f8db1cd5c798191830b785005c91a7a4ef4d0d867f`

This item is in the current 450-row experimental test split. The remaining 449 rows were used once for the current checkpoint comparison; 111 of them had also been scored earlier for the starting checkpoint, as described above.
