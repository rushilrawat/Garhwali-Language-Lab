# SraVaani refined 61-trial result

Updated: 2026-09-16
Job: [`6aaa1726f76d6a098a70f768`](https://huggingface.co/jobs/rushilrawat/6aaa1726f76d6a098a70f768)
Decision: retain base SraVaani; do not promote the refined checkpoint

## Result

All 61 validation-first trials completed with no failures. The selected recipe
was decoder/joint-only adaptation at learning rate `5e-5`, two epochs, seed 17,
and 102 optimizer steps. It improved the 269-record validation set from
43.454% to 42.711% WER and from 18.948% to 18.660% CER.

The selected checkpoint was then evaluated once on the frozen 112-record test.
It scored 43.528% WER and 17.494% CER. Base SraVaani scores 42.761% WER and
17.606% CER on the same test. The refinement therefore worsened the primary
test metric by 0.767 percentage points while improving CER by 0.112 percentage
points. The base checkpoint remains the preferred ASR model.

| Model | Validation WER | Validation CER | Frozen test WER | Frozen test CER |
| --- | ---: | ---: | ---: | ---: |
| Base SraVaani | 43.454% | 18.948% | 42.761% | 17.606% |
| Validation-selected refined checkpoint | 42.711% | 18.660% | 43.528% | 17.494% |

Selection used validation WER only. The frozen test did not select or tune a
configuration. The retained experimental checkpoint SHA-256 is
`f1a29db9c7a70566e456fe657051f558c7d77d1731585e6f80ab9b889e414a4e`.

## Runtime and credit estimate

The job ran for 10,072 seconds on `l4x1`, or 2h47m52s. At $0.80/hour its
estimated charge is $2.2382. Across the five completed L4 jobs, the known runtime
is 12,639 seconds and the estimated charge is $2.8087. A short canceled job has
no duration in the Jobs API, so the remaining amount from the authorized $5 is
conservatively treated as approximately $2.06 to $2.19.

## Next experiment

The next run uses all 5,513 human-transcribed training clips that do not share
an audio hash with the fixed 269-record validation or 112-record test sets. It
also excludes every known benchmark speaker. Training covers 8.112 hours; 3,886
rows lack complete speaker identity, so the run is explicitly experimental.
The fixed benchmark remains unchanged.

Synced artifacts are under
`data/processed/evaluation/asr/sravaani_refined_61/cloud_output/`.
