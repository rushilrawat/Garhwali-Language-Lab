# Native-reference review readiness

## Outcome

The two-pass native workflow now packages the complete remaining text-accuracy
queue and the full transcript-review queue. Generated JSONL packets preserve the
nested source payload, while flat CSV copies make the same decisions practical
for independent reviewers.

| Review artifact | Records | Evidence included |
| --- | ---: | --- |
| Text accuracy | 176 | Source form, English alignment, source ID, priority, reasons, allowed decisions |
| Transcript | 113 | Audio path and transcript context for all rows; two local model hypotheses for the five ambiguous supervised references |

The 176 text records consist of **172 Translatewiki** interface translations and
**four PanLex** forms. All Translatewiki records retain their OPUS English
alignments. The PanLex mirror does not supply meaning links for its four remaining
Romanized forms, so they cannot be responsibly promoted from spelling alone.

## Generated views

- `data/processed/native_review/packets/text_accuracy.jsonl`
- `data/processed/native_review/packets/transcript.jsonl`
- `data/processed/native_review/templates/text_accuracy.csv`
- `data/processed/native_review/templates/transcript.csv`

These generated files remain outside Git with the other row-level datasets. Their
counts and construction code are versioned in the release evidence.

## Decision flow

Each reviewer fills a separate copy of the CSV template, including `reviewer_id`,
`round`, and one of the listed decisions. Completed copies can be imported with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/native_review_workflow.py \
  --import-decisions reviewer-one.csv reviewer-two.csv
```

The importer ignores blank rows, rejects decisions without reviewer identity,
prevents duplicate decisions by the same reviewer, and converts dialect lists
back to structured values. Matching decisions from two distinct reviewers are
materialized alongside the immutable source payload. Reviewer notes remain
attached but do not create a false disagreement when the structured decisions
match. Actual decision disagreements remain open.

## Evidence boundary

The official Translatewiki API returned HTTP 403 to the project client during
this pass. This was an access refusal, not a rate-limit or account-usage pause.
The pinned OPUS snapshot and its English alignments remain available and fully
represented in the packets.

No native decisions were fabricated. The pipeline work is complete, but promotion
of these 176 texts and correction of the five ambiguous human transcripts still
requires listening or language judgment from two independent Garhwali reviewers.
All records remain active experimentally while that evidence is pending.

This stage incurred **$0** in API, GPU, or Hugging Face billing charges.
