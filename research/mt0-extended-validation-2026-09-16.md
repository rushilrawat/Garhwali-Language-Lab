# Extended mT0 validation-only continuation

Updated: 2026-09-16
Job: [`6aaab5b35527934177eeaa05`](https://huggingface.co/jobs/rushilrawat/6aaab5b35527934177eeaa05)
Status: `COMPLETED`

Three rank-4 LoRA seeds trained for 8,192 steps at learning rate `1e-4` on the
current 2,178-record instruction training split. Selection and generation
metrics use 130 validation records. The fixed 256-record test split remained
unopened.

| System | Validation CE | Exact match | chrF2 |
| --- | ---: | ---: | ---: |
| Base mT0-small | 5.780505 | 0.0000% | **0.088327** |
| Seed 17, CE-selected | **4.476975** | 1.5385% | 0.061862 |
| Seed 29 | 4.505441 | 1.5385% | **0.068875** |
| Seed 43 | 4.501707 | **2.3077%** | 0.060827 |
| Adapted mean | **4.494708** | — | — |

The longer run improves the best validation CE from 4.625628 at 2,048 steps to
4.476975 and produces the first nonzero exact matches. chrF2 remains below the
zero-shot base, so the adapter is a validated learning result but is not yet a
general generation release.

The job used 2,034.335 wall-clock seconds, approximately **$0.4521** at
$0.80/hour. Artifacts are synced under
`data/processed/evaluation/controlled_modeling/mt0_instruction_extended_v0_4/cloud_output/`.
