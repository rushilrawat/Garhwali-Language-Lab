# Garhwali ASR baseline

The zero-shot baseline used `openai/whisper-small` with the Hindi transcription prompt on 20 deterministic VAANI validation records.

- WER: 1.3433 (134.3%)
- CER: 0.9485 (94.8%)
- Decision: rejected for bulk pseudo-labeling

The model often transliterates Garhwali into Latin script or repeats hallucinated tokens. Its output must not replace source transcripts or label the untranscribed corpus.

This historical 20-row validation pilot has now been superseded by the strict
112-row speaker-safe comparison. On that shared test set, zero-shot
Whisper-small scores 0.9717 WER / 0.5782 CER and the selected fine-tuned
Whisper-tiny checkpoint scores 0.7430 / 0.4044. See
[`speech-baseline-comparison-2026-09-11.md`](speech-baseline-comparison-2026-09-11.md).

The pilot predictions and exact references are stored under `data/processed/evaluation/asr/`. Model files and runtime dependencies remain in the ignored project cache.
