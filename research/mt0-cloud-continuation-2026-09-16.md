# mT0 Garhwali instruction continuation

Updated: 2026-09-16
Job: [`6aaab2465527934177eea964`](https://huggingface.co/jobs/rushilrawat/6aaab2465527934177eea964)
Status: `COMPLETED`

Three rank-4 LoRA seeds trained for 2,048 steps on the current split-safe
instruction corpus. Selection used 130 validation records. The 256-record fixed
test split was not opened or used for training, selection, or evaluation.

| System | Validation cross-entropy |
| --- | ---: |
| Unadapted mT0-small | 5.780505 |
| Seed 17 | 4.631072 |
| Seed 29, selected | **4.625628** |
| Seed 43 | 4.628153 |
| Three-seed mean | **4.628285** |

All three seeds improved on the current validation set. Each seed saw the whole
2,046-record training selection once; the current source files contain 2,178
training records in total. The machine-readable report records all hashes and
confirms zero test use.

The job ran for 531.741 wall-clock seconds and the experiment used 383.908
seconds. At $0.80 per L4 hour, the wall-clock estimate is **$0.1182**. Artifacts
are synced under
`data/processed/evaluation/controlled_modeling/mt0_instruction_cloud_v0_3/cloud_output/`.

Because this run did not generate validation answers, the next continuation
adds validation-only exact-match and chrF2 measurement while retaining the
closed test.
