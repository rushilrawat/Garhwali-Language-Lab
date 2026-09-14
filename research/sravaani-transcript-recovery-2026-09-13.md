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

The next model-assisted pass should operate only on this queue, compare every
new hypothesis against the preserved original, and evaluate any decoding change
on the frozen 112-row human-transcribed benchmark before bulk replacement.
