# Semantic duplicate refinement

> The 92 cross-split pairs below describe the pre-rebuild split. The current
> connected split uses supported semantic edges, reassigns 120 records, and
> reports zero supported-semantic cross-split leakage; see the generated split
> report and [`finalreport.md`](../finalreport.md).

Updated: 2026-09-16
Job: [`6aab31eaf76d6a098a712001`](https://huggingface.co/jobs/rushilrawat/6aab31eaf76d6a098a712001)
Status: `COMPLETED`

The refinement re-scored all **29,903** embedding candidates with the pinned
multilingual `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` model and an explicit
character-level similarity signal.

| Decision | Pairs |
| --- | ---: |
| High-confidence near duplicate | 267 |
| Supported candidate | 1,357 |
| Review required | 14,022 |
| Likely false positive | 14,257 |

The supported groups contain **92 cross-split pairs**. These are now a focused
leakage-review queue. No source record was deleted, rewritten, or automatically
excluded. The evidence remains reversible and preserves source provenance.

The job ran for 152.725 wall-clock seconds, approximately **$0.0339** at
$0.80/hour. Artifacts are under
`data/processed/evaluation/data_quality/semantic_duplicates_refined_v0_2/cloud_output/`.
