# Native-reference review readiness

**Updated:** 2026-09-29

## Outcome

The workflow packages the priority text-accuracy and transcript-review queues.
Generated JSONL packets preserve source payloads. Transcript reviewers now get a
blind first-pass file, so they can listen and transcribe before seeing provider
references or model hypotheses. A context-rich second-pass file is produced for
error adjudication.

| Review artifact | Records | Evidence included |
| --- | ---: | --- |
| Text accuracy | 176 | Source form, English alignment, source ID, priority, reasons, allowed decisions |
| Transcript blind first pass | 113 | Audio path and duration only, blank transcript and reviewer fields; no reference or model output |
| Transcript context pass | 113 | Audio path, current reference, and two local model hypotheses for the five ambiguous supervised references |

The 176 text records consist of **172 Translatewiki** interface translations and
**four PanLex** forms. All Translatewiki records retain their OPUS English
alignments. The PanLex mirror does not supply meaning links for its four remaining
Romanized forms, so they cannot be responsibly promoted from spelling alone.

## Generated views

- `data/processed/native_review/packets/text_accuracy.jsonl`
- `data/processed/native_review/packets/transcript.jsonl`
- `data/processed/native_review/templates/text_accuracy.csv`
- `data/processed/native_review/templates/transcript_blind.csv`
- `data/processed/native_review/templates/transcript.csv`

The full packet builder also records 10,876 dialect, 4,218 language-identity,
1,114 lexicon, 1,545 OCR, and 2,539 evaluation-text rows, plus the 112-row
evaluation-ASR packet. Those broader packets do not yet have reviewer-ready flat
forms and are not represented as reviewed. The current three flat forms are the
bounded priority queue, not a claim that every candidate in the corpus has been
checked.

These generated files remain outside Git with the other row-level datasets. Their
counts and construction code are versioned in the release evidence.

## Decision flow

Each reviewer fills a separate copy of the CSV template, including `reviewer_id`,
`round`, and one of the listed decisions. Completed copies can be imported with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/native_review_workflow.py \
  --import-decisions reviewer-one-text-accuracy.csv reviewer-two-text-accuracy.csv \
  reviewer-one-transcript.csv reviewer-two-transcript.csv
```

For transcripts, collect and freeze both `transcript_blind.csv` passes first.
Only then use `transcript.csv` to compare the blind transcriptions with the
provider reference and model hypotheses, and record each reviewer's final
decision once in that context-form copy. Import only the context-form final
decisions: importing both files would create duplicate reviewer decisions.
Two reviewers must have distinct IDs; disagreements remain open for adjudication.

The importer ignores blank rows, rejects decisions without reviewer identity,
prevents duplicate decisions by the same reviewer, and converts dialect lists
back to structured values. Matching decisions from two distinct reviewers are
materialized alongside the immutable source payload. Reviewer notes remain
attached but do not create a false disagreement when the structured decisions
match. Actual decision disagreements remain open. Rebuilding templates leaves
separately named reviewer CSV copies intact. Importing a later batch appends to
the existing decision ledger; an already imported reviewer/record pair is
rejected before the ledger is changed.

## Evidence boundary

The official Translatewiki API returned HTTP 403 to the project client during
this pass. This was an access refusal, not a rate-limit or account-usage pause.
The pinned OPUS snapshot and its English alignments remain available and fully
represented in the packets.

The 2026-09-29 run produced **zero imported decisions, zero adjudications, and
zero completed reviewer templates**. The 176 priority texts and 113 transcript
records therefore remain unreviewed. Two independent Garhwali reviewers must
complete the templates before any of these records can support a native-validated
claim. Automated counts and model agreement remain triage signals only; they are
not substitutes for native judgment.

This stage incurred **$0** in API, GPU, or Hugging Face billing charges.
