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

The adaptation adds 16 word errors, worsening WER by 0.7670 percentage points
(1.79% relative), while removing 11 character errors and improving CER by
0.1542 percentage points (0.88% relative). Because WER was the declared primary
selection metric, this checkpoint is retained as an experimental artifact and
is not promoted over the original SraVaani model.

At record level, word errors improve on 25 clips, worsen on 32, and remain equal
on 55. Character errors improve on 35, worsen on 41, and remain equal on 36.
Neither model produces an empty hypothesis, and neither produces a fully exact
transcript on this difficult test. This confirms a small redistribution of
errors rather than a reliable overall gain.

## Reproducibility

- Frozen manifest SHA-256: `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`
- Frozen audio archive SHA-256: `8eb4d109e9fb70e6f04d6b699f5190e3ba3d668a61411e78cdbb8f37e8901d10`
- Evaluation output: `data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/`
- Predictions: 112 rows with reference, hypothesis, and per-record error counts
- Decoder runtime: 6.228 seconds on one NVIDIA L4 after model restoration

The test result is closed. Any later adaptation must use validation or a newly
created native-reviewed development split rather than tuning against these 112
records.
