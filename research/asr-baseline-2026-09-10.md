# Garhwali ASR baseline

The zero-shot baseline used `openai/whisper-small` with the Hindi transcription prompt on 20 deterministic VAANI validation records.

- WER: 1.3433 (134.3%)
- CER: 0.9485 (94.8%)
- Decision: rejected for bulk pseudo-labeling

The model often transliterates Garhwali into Latin script or repeats hallucinated tokens. Its output must not replace source transcripts or label the untranscribed corpus. Fine-tuning on the complete 8.8-hour supervised VAANI partition is the next model experiment.

The pilot predictions and exact references are stored under `data/processed/evaluation/asr/`. Model files and runtime dependencies remain in the ignored project cache.
