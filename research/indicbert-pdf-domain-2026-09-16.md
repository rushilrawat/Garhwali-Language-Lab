# IndicBERTv2 incoming-PDF domain continuation

Updated: 2026-09-16
Job: [`6aaabf3e5527934177eeac89`](https://huggingface.co/jobs/rushilrawat/6aaabf3e5527934177eeac89)
Status: `COMPLETED`

The experiment trains only on 25,983 segments from the six unique incoming
books and selects on all 615 incoming-book validation segments. The 1,328
incoming-book test segments were neither uploaded nor opened.

| System | Validation CE | Masked-token accuracy |
| --- | ---: | ---: |
| Base IndicBERTv2 | 6.190638 | 25.1979% |
| Seed 17 | 4.668432 | **34.2128%** |
| Seed 29, selected | **4.655975** | **34.2128%** |
| Seed 43 | 4.670884 | 33.3333% |
| Three-seed mean | **4.665097** | **33.9197%** |

All seeds improve both metrics. The mean loss falls by 1.525541 and mean
accuracy rises by 8.7218 percentage points over the pinned base checkpoint.
This validates book-domain continued pretraining while preserving test
isolation.

The job used 683.859 wall-clock seconds, approximately **$0.1520** at
$0.80/hour. Artifacts are synced under
`data/processed/evaluation/controlled_modeling/indicbert_pdf_domain_v0_1/cloud_output/`.
