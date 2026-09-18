# IndicBERTv2 Garhwali cloud continuation

Updated: 2026-09-16
Job: [`6aaaad62f76d6a098a71100f`](https://huggingface.co/jobs/rushilrawat/6aaaad62f76d6a098a71100f)
Status: `COMPLETED`

## Audited input

The current split-safe text corpus contains 106,804 training, 3,114 validation,
and 4,164 untouched test segments. Exact segment-hash overlap is zero across all
three splits. The six unique incoming PDFs contribute 27,926 segment identities:
25,983 train, 615 validation, and 1,328 test. Test segments are excluded from
training and selection.

The exact manifest hashes and coverage counts are recorded in
`data/processed/evaluation/controlled_modeling/indicbert_cloud_input.json`.

## Experiment

The pinned `ai4bharat/IndicBERTv2-MLM-only` revision
`8598f13fe52443bc3fc054fcd665944560145b5c` receives rank-4 LoRA adapters on
attention query/value projections. Three seeds (17, 29, 43) each run 4,096
train-only steps against the complete 106,804-record training pool. Selection
uses the existing deterministic 128-record validation subset; the test split is
not opened.

## Result

| System | Validation cross-entropy | Masked-token accuracy |
| --- | ---: | ---: |
| Unadapted checkpoint | 6.395484 | 24.2991% |
| Seed 17, 4,096 steps | 5.089711 | 27.4766% |
| Seed 29, 4,096 steps | **5.087592** | 28.2243% |
| Seed 43, 4,096 steps | 5.090020 | **29.1589%** |
| Three-seed mean | **5.089108** | **28.2866%** |

All three seeds improved validation loss. The mean is 0.535390 lower than the
earlier 1,024-step continuation mean of 5.624498. Seed 29 is selected by the
predeclared validation-loss rule. The frozen test split remained unopened.

The job used 316 billed L4 seconds, approximately **$0.0702** at $0.80/hour;
the experiment itself used 287.383 seconds. Together with the expanded-human
SraVaani run, the two new jobs used about $0.2242 of the confirmed $4 balance.
Output persists in:

```text
hf://buckets/rushilrawat/jobs-artifacts/cloud_output-0009f020
```

The tracked launcher is `scripts/run_indicbert_hf_job.sh`; the input auditor is
`scripts/audit_indicbert_cloud_input.py`. Adapters and the machine-readable
report are synced locally under
`data/processed/evaluation/controlled_modeling/indicbert_cloud_v0_3/cloud_output/`.
