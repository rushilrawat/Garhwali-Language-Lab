# Model-backed text noise audit

Job: [`6aab0af85527934177eebcb0`](https://huggingface.co/jobs/rushilrawat/6aab0af85527934177eebcb0)
Status: `COMPLETED`

Pinned IndicBERTv2 scored all **28,755** canonical text records over **232,158**
deterministic masked tokens. The audit identifies 2,876 high-loss model/source
disagreements, 2,987 OCR-source priorities, 2,982 Hindi/Garhwali ambiguity
priorities, and 47,165 low-confidence spelling candidate pairs across 10,856
records. All 28,755 records remain active; nothing was automatically corrected,
relabelled, or excluded.

The run used 398.410 wall-clock seconds, approximately **$0.0885** at
$0.80/hour. Complete proposals remain private under
`data/processed/evaluation/data_quality/text_noise_audit_v0_2/cloud_output/`.
