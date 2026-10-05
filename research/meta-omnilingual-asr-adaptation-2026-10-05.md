# Meta Omnilingual ASR adaptation — 2026-10-05

**Status: development-only. No independent or native-validated accuracy claim.**
This experiment continued the local Garhwali-adapted Whisper-tiny v0.2
checkpoint on Meta Omnilingual training audio and evaluated only on the
speaker-disjoint compatible validation view. The Meta test split was not read
for model selection or scored.

## Safe, model-compatible data

The source audit contains 2,927 Meta rows. Its safe split manifests contain
2,294 training rows, 271 validation rows, and 292 unresolved test rows. The
full training and validation manifests have zero exact audio-hash,
normalized-transcript, or known-speaker intersections; their cross-corpus
duplicate and conflict flags are also clear.

Whisper-tiny accepts at most 30 seconds of audio and 448 target tokens. The
reproducible filter in [`scripts/prepare_whisper_compatible_manifests.py`](../scripts/prepare_whisper_compatible_manifests.py)
therefore produced a task-specific view:

| Split | Safe source rows | Whisper-compatible rows | Removed from this experiment |
| --- | ---: | ---: | ---: |
| Train | 2,294 | 1,793 (10.920 hours) | 501 |
| Validation | 271 | 241 (1.212 hours) | 30 |

The 531 excluded rows remain unchanged in the original manifests and source
audit. The compatibility ledger records their IDs, hashes, duration/token
counts, and reasons. Across the two splits, 409 rows exceed the 30-second
window and 311 exceed 448 target tokens; some have both reasons. No source row
was deleted or rewritten. This limited Whisper view does not make those
long-form records unusable for other models or segmentation workflows.

The input manifest hashes are `d22b7909af079e925099b55c5a45da7fca9e00508465d9c140d7848aa9ec2e86`
(train) and `fd0727ed348a5e71585dea1b89afcf47271dfb2c8a2c918d6275a99adbda8b8b`
(validation). The derived compatible manifests hash to
`3609591379d06e8846234578d792b7f0c369f2299c7ab8691fcfe07e0be87a15`
(train) and `4af37da8f070e123283444f2e3f37c103a548cc2c8daff55ef33ea567de40a12`
(validation). The local exclusion ledger SHA-256 is
`1f36fcedcad3bbb8035de04e4ae874f52836b8d03dfeb7f54473e5df9293245d`.

## Training and validation result

The starting checkpoint was `models/whisper-tiny-garhwali-v0.2`, weight
SHA-256 `598546b068c3aa509ef5036ee4ff12502fbb3c0dc507096a56d1a2a3143d6225`.
The one-epoch continuation used all 1,793 compatible training records, learning
rate `1e-5`, one record per optimizer step, CPU execution, and seed 17. Its
weights hash to
`08687a1e54f61f400bdc747fcc66044d8ed6623c6f5acc3125d6c9137ca4d19c`.
Mean training loss was 1.133329. It was evaluated with greedy decoding on the
same 241 rows used to compare the original checkpoint.

| Checkpoint | WER | Word errors / words | CER | Character errors / characters |
| --- | ---: | ---: | ---: | ---: |
| Whisper-tiny v0.2, before adaptation | 93.444% | 10,191 / 10,906 | 70.522% | 31,625 / 44,844 |
| After one Meta train epoch | **89.318%** | **9,741 / 10,906** | **68.502%** | **30,719 / 44,844** |
| Difference | **−4.126 pp** | 450 fewer word errors | **−2.020 pp** | 906 fewer character errors |

On individual records, WER decreased on 154, increased on 33, and stayed equal
on 54. CER decreased on 165, increased on 73, and stayed equal on 3. The
change improved both aggregate metrics on each of the two validation speakers:

| Validation speaker | Rows | Baseline WER / CER | Adapted WER / CER |
| --- | ---: | ---: | ---: |
| `spk11` | 119 | 96.520% / 77.063% | 94.798% / 76.211% |
| `spk17` | 122 | 90.159% / 63.487% | 83.466% / 60.210% |

The development comparison is exactly matched by record ID, audio hash, and
reference. The comparison output is reproducible with
[`scripts/compare_asr_predictions.py`](../scripts/compare_asr_predictions.py);
its local JSON output also records the input-file hashes. The baseline
predictions are a subset of the earlier 271-row greedy run. The candidate
prediction file SHA-256 is
`2e7154923be78ca5af5bf1b94cd90bbcd52149329b5cc89aad208436fd515dfe`.

## Seed check and claim limits

The recipe was run under seed 17 and seed 29. Both runs produced the same
checkpoint hash (`08687a1e54f61f400bdc747fcc66044d8ed6623c6f5acc3125d6c9137ca4d19c`),
the same validation metrics, and the same prediction-file hash shown above.
The pinned Whisper configuration has zero dropout, attention dropout,
activation dropout, and layer drop, and the data order is fixed by audio hash.
The training traces are identical. Seed 43 was not run because it would repeat
the same deterministic experiment rather than add a new independent seed
estimate.

This is promising validation evidence that Meta in-domain adaptation improves
the current checkpoint on the compatible short-clip view. It is not a fresh
independent accuracy estimate: the validation slice selected the adaptation,
references are upstream and unadjudicated, the base Whisper model's broad
pretraining exposure is not fully known, and only two validation speakers are
available. Native review remains deferred. The 292 safe Meta test rows remain
unscored because checkpoint/source exposure is unresolved. No model is
promoted for release, no test was used, no files were downloaded, and no paid
job was launched.

## Reproduction

Build the model-compatible view from already prepared local manifests and the
pinned local tokenizer/config:

```bash
.venv/bin/python scripts/prepare_whisper_compatible_manifests.py \
  --train-manifest data/processed/model_ready/splits/meta_omnilingual_asr/train.jsonl \
  --validation-manifest data/processed/model_ready/splits/meta_omnilingual_asr/validation.jsonl \
  --model models/whisper-tiny-garhwali-v0.2 \
  --output-dir data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible
```

The training and validation manifests, checkpoints, exclusion ledger, and
per-record predictions are Git-ignored generated files. Reproduce the distinct
seed-17 run locally with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/train_whisper_garhwali.py \
  --model models/whisper-tiny-garhwali-v0.2 \
  --output models/whisper-tiny-garhwali-meta-multiseed-17 \
  --train-manifest data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible/train.jsonl \
  --eval-manifest data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible/validation.jsonl \
  --eval-split validation --epochs 1 --device cpu --local-files-only \
  --seed 17 --save-every 0
```

Then compare the original greedy predictions with the candidate on the exact
compatible validation rows:

```bash
.venv/bin/python scripts/compare_asr_predictions.py \
  --manifest data/processed/model_ready/splits/meta_omnilingual_asr/whisper_tiny_compatible/validation.jsonl \
  --baseline data/processed/evaluation/asr/meta_omnilingual_baselines/whisper_tiny_garhwali_v0.2/predictions.jsonl \
  --candidate models/whisper-tiny-garhwali-meta-multiseed-17/evaluation_predictions.jsonl \
  --output data/processed/evaluation/asr/meta_omnilingual_dev/whisper_tiny_meta_adaptation_comparison.json
```
