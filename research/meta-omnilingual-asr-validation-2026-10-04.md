# Meta Omnilingual ASR validation — 2026-10-04

**Status: development-only. No independent accuracy claim.** This report covers
one local ASR-ready conversion of the pinned Garhwali portion of Meta's
Omnilingual ASR corpus and a validation-only run of the local
Garhwali-adapted Whisper-tiny v0.2 checkpoint.

## Source reconciliation and eligible views

The builder at [`scripts/prepare_meta_omnilingual_asr.py`](../scripts/prepare_meta_omnilingual_asr.py)
reconciled all **2,927** Meta rows against the pinned release manifest, the
project transcript manifest, and seven local Parquet shard hashes. The
upstream split contains 2,329 train, 298 dev, and 300 test rows. The safe
model-ready views contain **2,294 train**, **271 validation**, and **292
test** rows. The remaining 70 rows stay in the full local
`source_audit.jsonl` with their exclusion reasons; no source row was deleted.

Eligible audio was converted to mono 16 kHz signed 16-bit PCM WAV. The build
wrote 2,857 audio files (2,160,569,086 bytes); source FLAC bytes total
2,546,971,905. Raw audio and derived files remain Git-ignored. The local
source is pinned to revision `8648ba8946377697b427ae952076e49fc0e5e44d`,
marked CC-BY-4.0 by its source manifest. Input manifest digests:

| Input | SHA-256 |
| --- | --- |
| Meta speech manifest | `67f158a742bc3e9947bf9308c6e0a1e5c8ee448f1a2605a109bcbce6d8dc99e9` |
| Project transcript manifest | `33392328a76a0bec5b6190606c9ff328c6a5cac93998772c6e724782e399e10f` |
| Safe validation manifest used below | `fd0727ed348a5e71585dea1b89afcf47271dfb2c8a2c918d6275a99adbda8b8b` |

The 292 internally safe test rows remain **unresolved** for model evaluation
because upstream checkpoint exposure is unknown. They were not scored.

## Greedy development result

The local `whisper-tiny-garhwali-v0.2` checkpoint was run with the existing
Hindi language prompt, deterministic greedy decoding, and 128-token maximum
on all 271 internally safe validation rows. The output identity, ordered
audio hashes, references, and per-row WER/CER counters were independently
reconciled and rescored.

| Measure | Result |
| --- | ---: |
| Records | 271 / 271 |
| WER | **93.900%** (12,608 / 13,427 words) |
| CER | **72.918%** (40,371 / 55,365 characters) |
| CPU inference time | 330.3 seconds |
| Model-weight SHA-256 | `598546b068c3aa509ef5036ee4ff12502fbb3c0dc507096a56d1a2a3143d6225` |
| Prediction-file SHA-256, after provenance join | `366cf5f63eea6a5166dbd1aed203311f6382a94c8f26369f6a014f27a86df121` |
| Input manifest SHA-256 | `fd0727ed348a5e71585dea1b89afcf47271dfb2c8a2c918d6275a99adbda8b8b` |

These error rates show that this checkpoint performs poorly on the Meta
prompted-speech validation set. WER can exceed 100% for a slice when insertions
outnumber reference words. Error slices are descriptive: 194 clips longer
than 15 seconds have 94.63% WER / 76.01% CER; 75 clips of 8–15 seconds have
90.20% / 58.06%; and the 3–8-second slice has only two clips. There are two
speaker IDs in this validation view (133 and 138 rows), too few speakers for a
generalization claim. Reference-length slices have 249 long references
(26+ words) and 22 references of 11–25 words. This source has no district or
per-record acoustic-quality annotations, so those slices are unavailable.

The result is development evidence only. The checkpoint is adapted on VAANI;
its broader pretraining exposure is not fully characterized, the Meta
references are upstream and unadjudicated, and native-speaker review is
deferred. It is not an independent Garhwali accuracy estimate.

## Bounded decoder comparison

Beam size 5 was run on the **same 271 rows**, checkpoint, prompt, and token
limit as the greedy configuration. Both prediction files were matched by all
271 record IDs, audio hashes, and references; row metrics were independently
recomputed. Results:

| Decode | WER | CER | Word errors | Character errors | CPU time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Greedy (`num_beams=1`) | 93.9004% | **72.9179%** | 12,608 | **40,371** | 330.3 s |
| Beam 5 | **93.4460%** | 72.9504% | **12,547** | 40,389 | 1,094.0 s |

Beam 5 reduces WER by 0.4543 percentage points (61 fewer word errors) while
CER rises by 0.0325 points (18 additional character errors). Under the
predeclared no-CER-regression guardrail, greedy remains selected; no model or
benchmark result is promoted. The paired change is mixed across rows (beam 5
has lower word-error counts on 89 rows, higher on 64, and equal on 118).
Complete aggregate and row-coverage evidence is in the ignored
`greedy_vs_beam5_comparison.json` beside the local evaluation artifacts.

After inference, both prediction manifests were joined to the reconciled
source audit using `record_id` plus `audio_sha256`. The additional source-file
hash, license, duplicate, conflict, and split-safety fields do not change
audio or transcript inputs; this post-inference enrichment is recorded in
each local JSON report.

The planned cross-model comparison is incomplete: the original Whisper-tiny
weights are not cached locally, and the cached SraVaani repository is missing
its model weights, preprocessor, and tokenizer; NeMo is also not installed.
No downloads or paid jobs were used. No Meta test rows were scored.

## Reproduction

Prepare local audio/manifests with the command in
[`scripts/README.md`](../scripts/README.md). Reproduce the greedy run with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/run_whisper_comparison.py \
  --model models/whisper-tiny-garhwali-v0.2 \
  --model-id whisper-tiny-garhwali-v0.2 --revision local-v0.2 \
  --input data/processed/model_ready/splits/meta_omnilingual_asr/validation.jsonl \
  --output data/processed/evaluation/asr/meta_omnilingual_baselines/whisper_tiny_garhwali_v0.2 \
  --max-records 0 --max-new-tokens 128 --language-prompt hi --num-beams 1 \
  --device cpu --run-id whisper-tiny-garhwali-v0.2-meta-validation-2026-10-04
```

The model-ready manifests, predictions, derived audio, and JSON reports remain
local and ignored by Git. This work used no hosted job or paid compute.
