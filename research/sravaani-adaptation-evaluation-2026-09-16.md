# SraVaani Garhwali adaptation evaluation

Updated: 2026-09-16  
Training job: [`6aa9e33af76d6a098a70ec01`](https://huggingface.co/jobs/rushilrawat/6aa9e33af76d6a098a70ec01)  
Evaluation job: [`6aa9ff28f76d6a098a70f025`](https://huggingface.co/jobs/rushilrawat/6aa9ff28f76d6a098a70f025)

## Outcome

The two-epoch, 102-step decoder/joint adaptation completed successfully on 1,621
human-reference Garhwali recordings. The encoder remained frozen and no machine
transcripts were used. The resulting 1,796,198,400-byte checkpoint has SHA-256
`986800b39d402c0075e4e170480282db3971f247663f3fcb92274d77490383ea`.

The checkpoint was evaluated once on the frozen 112-record, 19-speaker test
split. That split was not used for training, checkpoint selection, or parameter
tuning.

| Model | Word errors / words | WER | Character errors / characters | CER |
| --- | ---: | ---: | ---: | ---: |
| Original SraVaani 1.0 | 892 / 2,086 | 42.7613% | 1,256 / 7,134 | 17.6058% |
| Garhwali decoder/joint adaptation | 908 / 2,086 | 43.5283% | 1,245 / 7,134 | 17.4516% |

The aggregate counts differ by 16 word errors and 11 character errors. A
post-run audit found that the adaptation report's test-manifest SHA-256
(`d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`) differs
from the base-model report's hash
(`2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`). Both
reports have 112 rows and matching denominators, but row identity has not been
reconciled. Therefore the displayed differences are historical aggregate
arithmetic, not verified paired WER/CER deltas; this checkpoint remains
experimental and is not promoted.

The original report recorded 25/32/55 rows with lower/higher/equal word errors
and 35/41/36 with lower/higher/equal character errors. Those paired row counts
are retained as historical but are not independently verified against the two
different manifest hashes in this audit. No test payload was reopened here.

## Reproducibility

- Frozen manifest SHA-256: `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`
- Post-run audit: base-model test manifest SHA-256 is `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`; the hashes differ, and equal record counts do not establish row identity.
- Frozen audio archive SHA-256: `8eb4d109e9fb70e6f04d6b699f5190e3ba3d668a61411e78cdbb8f37e8901d10`
- Evaluation output: `data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/`
- Predictions: 112 rows with reference, hypothesis, and per-record error counts
- Decoder runtime: 6.228 seconds on one NVIDIA L4 after model restoration

The test result is closed. Any later adaptation must use validation or a newly
created native-reviewed development split rather than tuning against these 112
records.
