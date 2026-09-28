# Post-hoc ASR held-out lineage audit — 2026-09-28

## Finding

The SraVaani base, six-configuration decoder sweep, 61-trial fine-tune,
expanded-human-transcript fine-tune, and original 102-step adaptation all use
the same fixed 112-row ASR test set. Each saved prediction file matches all
112 audio SHA-256 IDs and all 112 `asr_target_clean` references in the current
manifest. Summed per-row error counters reproduce each run's saved aggregate
WER and CER.

This closes the earlier uncertainty about whether the fine-tune aggregates
used identical examples. It does not make the scores independent or
native-validated: the test was already scored, SraVaani's upstream VAANI
example exposure remains unknown, and a speaker cannot certify transcript
correctness through arithmetic checks.

## Paired historical comparison

Saved per-row predictions were compared to the base on the same audio/reference
pairs. The intervals below resample all utterances belonging to a speaker as
one cluster (19 identified speakers, 10,000 replicates, seed 1729). Deltas are
candidate minus base in percentage points; positive means more errors. These
post-hoc test diagnostics were not used for model selection or promotion.

| Candidate | WER delta (95% speaker-cluster interval) | CER delta (95% speaker-cluster interval) |
| --- | ---: | ---: |
| Six-configuration decoder sweep, selected configuration | +0.000 [−0.583, +0.656] | −0.196 [−0.391, +0.000] |
| 61-trial decoder/joint fine-tune | +0.767 [−0.107, +1.591] | −0.112 [−0.683, +0.384] |
| Expanded-human-transcript fine-tune | +0.527 [−0.710, +1.518] | −0.210 [−0.949, +0.366] |
| Original 102-step human-reference adaptation | +0.767 [−0.307, +1.683] | −0.154 [−0.936, +0.398] |

Every WER interval includes zero. The small CER point reductions are also
uncertain; every CER interval includes zero or touches it. This audit supplies
no reliable evidence that a fine-tune improves held-out accuracy.

## Integrity details

- Fixed manifest: 112 rows, 112 unique audio hashes, SHA-256
  `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`.
- The base report directly records that manifest SHA-256. Its 112-row
  `predictions.jsonl` is now included in the paired audit.
- The other four prediction outputs each have the same ordered audio-ID digest
  `9240b0028d5f0f59414917b98cf010d8af44b6f4b7d3204b804c7abb07c14642` and
  reference/audio pair digest
  `2b157a1a230bfac72e189fab5bb9d620c29e9af7641ee606b92b89da585ce44e`.
- The original 102-step report declares manifest-byte hash
  `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`, which
  differs from the current manifest bytes. Its saved predictions nevertheless
  match all audio IDs and cleaned references; the difference in historical
  serialization is unexplained.
- No audio payload was downloaded; no inference, retraining, or test-based
  selection ran. The machine-readable post-hoc report is generated under the
  ignored directory `data/processed/evaluation/asr/heldout_lineage_audit_2026-09-28/`.

## Reproduction

Run `PYTHONPATH=scripts .venv/bin/python
scripts/audit_saved_asr_heldout_lineage.py`. The script verifies output IDs,
cleaned references, aggregate counters, manifest/report/output hashes, and
speaker-clustered paired intervals. Unit coverage is in
`tests/test_audit_saved_asr_heldout_lineage.py`.
