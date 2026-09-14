# SraVaani Garhwali adaptation readiness

Date: 2026-09-14  
Package: `garhwali-sravaani-nemo-finetune-package-v0.1`  
Training plan: `garhwali-sravaani-decoder-only-adaptation-pilot-v0.1`

## Current status

The human-reference data package and guarded training launcher are complete.
Actual fine-tuning is blocked by two external requirements: the trainable
`SraVaani-nemo-checkpoint.nemo` and a CUDA-capable NVIDIA GPU. The current Mac
has Apple Metal rather than CUDA.

The authenticated Hugging Face repository is useful for inference but cannot
serve as this training checkpoint. At pinned revision
`f5dd5358325a5208775b91dad98918e079ea2b27`, it publishes a 908,846,278-byte
FP16 TorchScript graph and inference wrapper. It does not publish a `.nemo` or
raw Lightning checkpoint. The official fine-tuning repository separately links
the approximately 1.7 GB NeMo checkpoint and recommends about 16 GB GPU memory.

## Verified data package

The package follows the official NeMo tarred-audio contract. Archive members use
their source audio SHA-256 as the filename, and each paired JSONL row contains
only `audio_filepath`, `text`, and measured `duration`.

| Split | Records | Hours | Speakers | Archive bytes |
| --- | ---: | ---: | ---: | ---: |
| Train | 1,621 | 2.870402 | 198 | 332,001,280 |
| Validation | 269 | 0.471186 | 31 | 54,507,520 |
| Held-out test | 112 | 0.220797 | 19 | 25,528,320 |
| **Total** | **2,002** | **3.562384** | **248** | **412,037,120** |

Verification proves:

- 2,002 of 2,002 source audio SHA-256 values match;
- every clip is readable 16 kHz mono 16-bit PCM WAV;
- all targets are non-empty;
- all 2,002 records retain CC BY 4.0 license evidence;
- exact audio overlap across splits is zero;
- identified-speaker overlap across splits is zero;
- tar member order matches manifest order; and
- a complete rebuild produces identical tar and manifest hashes.

The source WAVs remain unchanged. The generated 394 MiB package is ignored by
Git and can be deleted after transfer because the tracked builder recreates it
byte-for-byte.

## Training design

The first adaptation run follows the conservative path in the official training
repository at revision `11026fa0f97386ae05270872d899800151b2a8ef`:

| Setting | Value |
| --- | --- |
| Trainable scope | Decoder and joint network; encoder frozen |
| Training labels | 1,621 human references only |
| Epochs | 2 |
| Micro-batch | 4 |
| Gradient accumulation | 8 |
| Effective batch | 32 |
| Optimizer steps | 102 |
| Optimizer | AdamW, learning rate `1e-4`, weight decay `1e-3` |
| Scheduler | Cosine annealing, 10 warmup steps, minimum `1e-6` |
| Selection | Lowest validation WER on 269 records |
| Final test | 112 records, evaluated once after selection |

Machine transcripts are excluded. This directly tests whether the strongest
available multilingual checkpoint benefits from the project's reliable Garhwali
references without repeating the failed Whisper pseudo-label recipe.

## Reproduction

```bash
# Rebuild and verify the ignored 394 MiB NeMo package
PYTHONPATH=scripts .venv/bin/python scripts/prepare_sravaani_finetune.py

# Inspect the plan and external dependencies without importing NeMo
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/train_sravaani_garhwali.py

# On the CUDA host, after placing the checkpoint at the default path
python scripts/train_sravaani_garhwali.py --execute
```

Default checkpoint path:

```text
.cache/sravaani-finetune/SraVaani-nemo-checkpoint.nemo
```

The execution path validates that the checkpoint is a readable tar archive and
that CUDA is available before importing NeMo or starting training. The generated
plan is included in the local release manifest.

## Exact remaining access

Hugging Face model access is already confirmed. The remaining model access is to
the NeMo checkpoint linked by the official training repository. Training then
needs either a user-provided CUDA host or explicit authorization to launch a
paid cloud GPU job. No additional Garhwali data or manual labeling is required
for this pilot.
