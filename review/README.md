# Native-review workflow

## Current status (checked 2026-10-07)

The review system is ready, but **0 records have been adjudicated**. The
current packet inventory has 176 text-accuracy packets and 113 transcript
packets, with five ambiguous supervised transcripts carrying additional model
evidence. The project owner has deferred native-language and dialect review;
therefore the corpus and benchmark remain automated candidates, not
native-validated data. Packet generation and counts are local and do not
change the published dataset.
These queues do not block local experiments, and no model output is promoted to
ground truth without review. Current aggregate status is in
[`project-status/corpus-preparation-status.md`](../project-status/corpus-preparation-status.md).

Run `python3 scripts/native_review_workflow.py` to rebuild review packets under
`data/processed/native_review/packets/`. Each packet has a stable target ID, the
full source payload, and a review type covering language identity, dialect,
lexicon, OCR, transcripts, or evaluation data.

Reviewers copy the shape in `decision-template.json` into the Git-ignored file
`data/review_decisions/native_reviews.jsonl`. Use a project-assigned pseudonymous
reviewer ID rather than a name or contact detail. A target becomes adjudicated
only when two distinct reviewers submit identical decisions. Disagreements remain
explicit and require a third adjudication decision.

Allowed `review_type` values are `language_identity`, `dialect`, `lexicon`,
`ocr`, `transcript`, `evaluation_text`, and `evaluation_asr`. A decision is
`accept`, `reject`, or `correct`. Fill only the fields relevant to that review.
Never overwrite the source text, transcript, audio, or provenance record.

Outputs under `data/processed/native_review/results/` separate two-pass
agreements, pending second reviews, and disagreements. The current packet counts
are recorded in `data/processed/native_review/packets/report.json`. Adjudicated
records are then joined back to their immutable source payloads under
`data/processed/native_review/reviewed/`; corrections appear as `effective_text`
and never overwrite the original text or transcript.

Review-only VAANI drafts created by `scripts/transcribe_vaani_drafts.py` enter the
same `transcript` packet. Their token confidence is explicitly uncalibrated and
cannot make a draft training-eligible without matching independent reviews.
