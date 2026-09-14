# SraVaani transcript recovery routing

All 104,542 SraVaani source drafts remain active experimental records. The
recovery layer identifies 1,188 drafts that need a targeted second decoding pass
or comparison before they can be treated as reliable text. It does not delete,
quarantine, or silently replace any transcript.

| Recovery action | Records |
| --- | ---: |
| Decode with a Devanagari-constrained model | 1,049 |
| Retry frequent identical hypotheses | 121 |
| Retry empty hypotheses | 34 |
| Compare reversible repetition compaction | 17 |
| Resegment and decode duration anomalies | 2 |

Actions can overlap because one draft may have several failure signals. The 17
repetition candidates only reduce consecutive runs beyond two tokens; the
original SraVaani output is retained beside every candidate. No candidate is
automatically promoted to a human transcript or strict supervised target.

The compact recovery queue is generated at
`data/processed/model_ready/transcripts/sravaani_recovery_queue.jsonl`. Run:

```bash
python3 scripts/route_sravaani_recovery.py
```

## Targeted model-assisted re-decoding

The full queue was re-decoded with the local `whisper-tiny-garhwali-v0.2`
checkpoint using Hindi/Devanagari generation constraints. The output contains
exactly 1,188 unique audio hashes: no queued hash is missing and no unexpected
hash was added.

| Result | Records |
| --- | ---: |
| Alternative has a lower weighted structural-risk score | 1,154 |
| Preserved original has the lower or equal structural-risk score | 34 |
| Alternative has no automated structural flag | 1,089 |
| Alternative contains a decoding replacement character | 32 |
| Alternative repeats an identical corpus-level hypothesis at least 10 times | 19 |
| Alternative contains a repeated-token loop | 49 |
| Alternative is implausibly long for its audio duration | 15 |
| Alternative contains mixed scripts | 2 |
| Empty alternatives | 0 |
| Automatic transcript promotions | 0 |

Structural comparison uses only observable failure signals: script mismatch,
empty output, repeated tokens or hypotheses, duration mismatch, and decoding
replacement characters. These signals do **not** establish linguistic accuracy.
The local Whisper checkpoint scored 0.743 WER / 0.404 CER on the frozen
112-record human benchmark, while the full SraVaani model scored 0.428 WER /
0.176 CER there. The new hypotheses are therefore alternatives for focused
review and experimentation, not replacements for SraVaani or human references.

The post-pass also measures hypothesis frequency across the entire recovery
queue. This catches superficially valid Devanagari outputs such as the same
one-word hypothesis repeated across many recordings. Every result retains its
original transcript, all records remain active experimentally, and supervised
training eligibility remains false.

The local outputs are:

- `data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2.jsonl`
- `data/processed/model_ready/transcripts/sravaani_recovery_whisper_v0.2_report.json`

They remain ignored by Git because they include derived transcripts and local
audio references. Reproduce or resume the decoding pass with:

```bash
python3 scripts/redecode_sravaani_recovery.py
```

Recompute the corpus-level checks without loading the model with:

```bash
python3 scripts/redecode_sravaani_recovery.py --summarize-only
```
