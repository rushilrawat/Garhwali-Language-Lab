# SraVaani Garhwali budget sweep

Updated: 2026-09-16  
Job: [`6aaa08ed5527934177ee7c78`](https://huggingface.co/jobs/rushilrawat/6aaa08ed5527934177ee7c78)  
Final status: canceled before the refined replacement run

## Budget

This launch was replaced by the refined 61-trial decoder sweep in Job
[`6aaa1726f76d6a098a70f768`](https://huggingface.co/jobs/rushilrawat/6aaa1726f76d6a098a70f768).
The replacement completed all trials in 10,072 seconds at an estimated $2.2382.
The full result and promotion decision are documented in
[`sravaani-refined-61-result-2026-09-16.md`](sravaani-refined-61-result-2026-09-16.md).

## Experiment

The job uses the verified 2,002-record SraVaani package: 1,621 human-reference
training clips, 269 validation clips, and 112 held-out test clips. It compares
decoder/joint adaptation with cautious full-model adaptation over smaller
learning rates, multiple epoch budgets, and confirmation seeds. Sixty-one trials
are ordered so both adaptation scopes are tested early. A rolling runtime guard
stops new trials with at least 15 minutes reserved for final evaluation and
artifact persistence.

Every trial is selected on validation WER. The held-out test is evaluated once
for the selected checkpoint only when it improves on the original model's
validation WER. The test split never selects a trial. Progress, failures, the
best checkpoint, validation predictions, and any held-out result are written to
the mounted private Jobs bucket throughout the run.

## Persistence

The input package and scripts were uploaded to private transient Hugging Face
Jobs storage. The writable result bucket is:

```text
hf://buckets/rushilrawat/jobs-artifacts/cloud_sweep_v0_2-28c7bf17
```

After completion, sync it with:

```bash
HF_HOME=.cache/huggingface hf buckets sync \
  hf://buckets/rushilrawat/jobs-artifacts/cloud_sweep_v0_2-28c7bf17 \
  data/processed/evaluation/asr/sravaani_finetune/cloud_sweep_v0_2
```

The tracked launchers are `scripts/sweep_sravaani_garhwali.py` and
`scripts/run_sravaani_hf_sweep.sh`.
