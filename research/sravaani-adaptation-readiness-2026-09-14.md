# SraVaani Garhwali adaptation readiness

Updated: 2026-09-15
Package: `garhwali-sravaani-nemo-finetune-package-v0.1`  
Training plan: `garhwali-sravaani-decoder-only-adaptation-pilot-v0.1`

## Current status

The human-reference package and guarded training launcher are complete. The
official ARTPARK fine-tuning guide now provides a direct download for the
1,796,208,640-byte `SraVaani-nemo-checkpoint.nemo`; an HTTP preflight returned
the expected file and size on 2026-09-15. The launcher can download it directly
on the training host and validates its exact size and tar structure before NeMo
loads. No 1.8 GB checkpoint was stored on this Mac.

Local execution still cannot run because this Mac has Apple Metal rather than
CUDA. Hugging Face authentication is confirmed, but a Jobs preflight returned
HTTP 402 because the account has no positive compute-credit balance. The
preflight stopped before creating a job, so it incurred no charge. The bounded
plan uses one `t4-small` GPU at $0.40/hour with an eight-hour hard timeout, for a
maximum compute charge of $3.20. Hugging Face Jobs requires a positive credit
balance; a Pro subscription is not required for this launch.

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

# On a CUDA host: download, validate, train, and write outputs to explicit paths
python scripts/train_sravaani_garhwali.py \
  --package-report /data/report.json \
  --data /data \
  --checkpoint /workspace/SraVaani-nemo-checkpoint.nemo \
  --download-checkpoint \
  --output /output/sravaani-garhwali-decoder-pilot-v0.1.nemo \
  --experiments /output/experiments \
  --plan-output /output/plan.json \
  --execute

# From the repository root after Hugging Face credit is available
mkdir -p data/processed/evaluation/asr/sravaani_finetune/cloud_output
HF_HOME=.cache/huggingface hf jobs run \
  --name garhwali-sravaani-adaptation-v0-1 \
  --flavor t4-small \
  --timeout 8h \
  -v ./scripts:/workspace/scripts \
  -v ./data/processed/model_ready/sravaani_finetune:/data \
  -v ./data/processed/evaluation/asr/sravaani_finetune/cloud_output:/output:rw \
  pytorch/pytorch:2.8.0-cuda12.9-cudnn9-runtime \
  bash /workspace/scripts/run_sravaani_hf_job.sh
```

Default checkpoint path:

```text
.cache/sravaani-finetune/SraVaani-nemo-checkpoint.nemo
```

The execution path validates the official byte count and tar structure, then
checks CUDA before importing NeMo or starting training. The generated plan is
included in the local release manifest.

## Exact remaining action

Add at least $5 of Hugging Face compute credit, then rerun the bounded Jobs
launch. The pilot itself is fully prepared and needs no additional Garhwali data
or manual labeling. After training, the selected checkpoint must be evaluated
once on the existing 112-record held-out test split before any promotion.

The local-directory mounts are uploaded to Hugging Face's private transient
`jobs-artifacts` storage for the run. The CLI prints the exact sync command for
retrieving the writable output directory. The complete corpus release remains a
separate later upload task.
