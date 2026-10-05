# Model lineage refresh — 2026-10-05

**Outcome:** closed an audit-coverage gap for the 5 October Meta Whisper
adaptation. The run remains development-only; this audit does not create a
fresh independent accuracy result.

## Scope

The lineage auditor previously included the full Meta Omnilingual source
manifest but omitted the exact Whisper-compatible train/validation manifests
used for this adaptation. It also did not scan the adaptation's saved
predictions under the ignored `models/` directory. The auditor now includes
those two derived manifests and scans only matching Meta Whisper run
prediction files. Its default row-level JSON output now goes under the
Git-ignored `data/processed/` tree.

The refreshed local machine-readable ledger is
`data/processed/evaluation/garhwali_bench/model-accuracy-lineage-2026-10-05.json`.
It contains row identifiers and speaker metadata and must stay local. The
tracked report contains aggregate counts only.

## Verified run inputs

The safe Meta source manifests contain 2,294 training and 271 validation rows.
The Whisper-tiny limits retained 1,793 training and 241 validation rows;
the other 501 and 30 rows remain in the source manifests and the exclusion
ledger. The exact derived-manifest hashes are:

| Input | Rows | SHA-256 |
| --- | ---: | --- |
| Whisper-compatible training manifest | 1,793 | `3609591379d06e8846234578d792b7f0c369f2299c7ab8691fcfe07e0be87a15` |
| Whisper-compatible validation manifest | 241 | `4af37da8f070e123283444f2e3f37c103a548cc2c8daff55ef33ea567de40a12` |
| Saved adaptation predictions | 241 | `2e7154923be78ca5af5bf1b94cd90bbcd52149329b5cc89aad208436fd515dfe` |

The lineage auditor verifies the sidecar's declared training and evaluation
manifest paths, hashes, and row counts against the local files. Both hash and
count checks pass (1,793 training examples and 241 evaluation examples). The
sidecar also records the starting and resulting checkpoint hashes. Saved
prediction rows match all 241 compatible validation rows; the lineage decision
therefore records the set as `development_only` and previously scored, not as
untouched test evidence.

## Exposure findings

- The compatible training and validation views have **zero exact audio-hash,
  transcript-hash, and known-speaker overlap across splits**. The older strict
  1,621-row VAANI training view also has zero exact audio/text/speaker overlap
  with this compatible validation view.
- The compatible training transcript text shares **31 exact-hash groups with
  31 rows in each** of the current recommended text validation and test views.
  These are direct text-exposure matches relevant if this adapted checkpoint
  is later used in text-task evaluation. They do not establish semantic
  leakage, and they do not show that Meta validation audio overlaps training.
  Keep all records; do not treat the matched text rows as independent evidence
  for this checkpoint.
- The filtered compatible train/validation manifests have no cross-split
  exact-text groups. The wider source manifest contains flagged cross-split
  repetitions, which is why counts from the full source dump cannot be
  substituted for the specific model-ready inputs.
- The compatible view contains 23 repeated exact transcript-hash groups
  within its split data. They were retained; the audit does not merge or
  delete source records.
- The 292 safe Meta test rows remain unscored. Upstream checkpoint exposure,
  semantic/paraphrase overlap, and reference correctness are unresolved.

## Effect on claims and next work

The 241-row score and the comparison to Whisper-tiny v0.1 remain
development-only. Across the five task areas—language modeling, translation,
retrieval, generation, and ASR—independent-final evidence eligibility remains
**0/5**. Native review and dialect annotation remain deferred.

No training, inference, test scoring, network access, source-data edits, or
Hugging Face/GitHub data upload occurred in this audit. The next valid path to
independent accuracy is a frozen checkpoint followed by a newly collected,
rights-cleared and independently referenced evaluation set; the project
cannot manufacture that independence by rescoring existing public data.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_model_accuracy_lineage.py \
  --output-prefix data/processed/evaluation/garhwali_bench/model-accuracy-lineage-2026-10-05
```

The auditor's 5 October implementation is covered by
`tests/test_audit_model_accuracy_lineage.py`. At this report's run, the full
repository unittest suite passed **762/762**; a later v0.2.4 release follow-up
added regression coverage and the current suite passes **774/774**. The release index validator passes for the frozen
v0.1.1 snapshot.
