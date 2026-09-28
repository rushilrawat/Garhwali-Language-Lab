# ASR validation comparison with a shared run manifest — 2026-09-27

This step adds reproducibility metadata to an existing paired ASR validation
analysis. It rescored saved predictions; it did not run either model or access
the held-out test split.

| Model | WER | CER | Word errors / words | Character errors / characters |
| --- | ---: | ---: | ---: | ---: |
| SraVaani 1.0 | 43.3936% | 18.9252% | 2,161 / 4,980 | 3,282 / 17,342 |
| Garhwali Whisper v0.2 | 78.0522% | 46.2980% | 3,887 / 4,980 | 8,029 / 17,342 |

Both models are scored against the same **269 frozen validation audio hashes**.
Their saved 269-row summaries exactly reproduce
[`asr-validation-error-analysis-2026-09-24.json`](asr-validation-error-analysis-2026-09-24.json),
including its row-set SHA-256
`442871fc0c3a312e96e761e5d46a7ddaff041c0a641676c020e6053e3808f2a0`.

The local-only output is ignored under
`data/processed/evaluation/asr/validation_comparison_manifested_2026-09-27/`.
Its run-manifest SHA-256 is
`b9db7af8d906c78254b91b1e75d9f209393d6fade4465bf63061c1037dd305a3`;
the output hashes recorded inside that manifest are:

- `predictions.jsonl`: `e2609b183427bc5c1f9300ec68d8de7db7b3a3f7558a07057a1478026f8c1e7c`
- `report.json`: `68921292fe8d982d3b23805fc07ff280bd1be2755fa44d1df9a624643d178b43`

The manifest pins the validation manifest, both saved prediction files, the
scoring code, metric normalizer, model IDs/revisions where available, selected
audio-hash IDs, and output hashes. The source prediction files each contain
381 rows, but the scorer loads and scores only rows matching the 269 validation
hashes; held-out rows are not JSON-decoded or scored. A focused test checks
that selected IDs and output hashes reconcile with the manifest.

These are **development/validation measurements**, not independent final
accuracy. SraVaani's VAANI training exposure is not auditable at example level,
the saved references have not been independently adjudicated, and the
validation set has prior use. No checkpoint is promoted by this reanalysis.
