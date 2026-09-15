# SraVaani structural-outlier audio evidence

The final 35 structurally flagged recovery proposals now have deterministic
audio-conditioned re-decoding, waveform activity measurements, and empirical
score calibration. They cover 97.307 seconds of audio. Every stronger-checkpoint
re-decode exactly matches its stored Whisper `v0.2` hypothesis.

## Review result

| Category | Records | Required action |
| --- | ---: | --- |
| Common short output with exact three-model text consensus | 11 | Listening spot check |
| Decoder repetition loop | 17 | Listening and manual transcription |
| Replacement-character decoding corruption | 3 | Listening and manual transcription |
| Empty output | 1 | New manual transcription |
| Other unresolved output | 3 | Listening review |
| **Total** | **35** | **Human listening remains required** |

No record was automatically corrected, promoted to a human reference, or
recommended for machine-label training. Original values and every candidate
remain preserved.

## What the audio evidence establishes

Each row now contains overall RMS level, an energy-activity share, leading and
trailing inactive duration, zero and clipped-sample shares, exact re-decode
status, and the two Whisper checkpoints' raw score percentiles against a shared
112-record human-reference calibration set. Energy activity is not treated as
speech or language ground truth.

The raw score-to-CER Pearson correlations are only -0.163638 for Whisper `v0.1`
and -0.231576 for Whisper `v0.2`. High raw scores occur on some obvious decoder
loops. The scores therefore rank review work but do not measure correctness.

## Reproduce

```bash
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/transcribe_vaani_drafts.py \
  --input data/processed/model_ready/transcripts/sravaani_recovery_audio_review_queue.jsonl \
  --output data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_audio_scored.jsonl \
  --model models/whisper-tiny-garhwali-v0.2 --max-records 0 --device cpu \
  --local-files-only
PYTHONPATH=scripts .venv/bin/python scripts/build_sravaani_audio_grounded_review.py
```

The machine-readable result and report are under
`data/processed/model_ready/transcripts/`; the same safe evidence is embedded in
the local Hugging Face `sravaani_drafts` configuration. Local paths and raw
speaker identifiers are not exported.
