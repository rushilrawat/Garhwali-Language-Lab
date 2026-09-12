# Controlled Garhwali text-scaling experiment

## Design

The first controlled-modeling experiment compares add-one-smoothed character
bigrams and trigrams at **1%, 5%, 10%, 25%, 50%, and 100%** of the existing
80,926-row training split. Seeds **17, 29, and 43** create deterministic nested
samples within each seed, producing **36 validation runs**.

Configuration selection uses only the 2,488 validation records. The frozen
2,492-record text candidate is evaluated only after order and data fraction are
fixed. Exact train/validation and train/test text overlap are both zero.

## Scaling curve

| Model | Train fraction | Mean records | Validation perplexity | Seed standard deviation |
| --- | ---: | ---: | ---: | ---: |
| Bigram | 1% | 810 | 19.856703 | 0.156510 |
| Bigram | 5% | 4,047 | 17.516364 | 0.030989 |
| Bigram | 10% | 8,093 | 17.118708 | 0.022201 |
| Bigram | 25% | 20,232 | 16.814189 | 0.014621 |
| Bigram | 50% | 40,463 | 16.684671 | 0.001241 |
| Bigram | 100% | 80,926 | 16.597915 | 0.000000 |
| Trigram | 1% | 810 | 31.182276 | 0.443696 |
| Trigram | 5% | 4,047 | 18.375017 | 0.075639 |
| Trigram | 10% | 8,093 | 15.891575 | 0.256666 |
| Trigram | 25% | 20,232 | 13.572712 | 0.008333 |
| Trigram | 50% | 40,463 | 12.475784 | 0.012893 |
| Trigram | 100% | 80,926 | **11.712997** | 0.000000 |

The trigram is data-starved below 10%, then overtakes the bigram as context
coverage grows. Performance still improves materially from 50% to 100%, so the
available text has not reached a visible plateau for this control family.

## Frozen test result

The validation-selected full-data trigram reaches **11.893886** perplexity on the
frozen test candidate. This is **27.76% lower** than the earlier 16.464093
character-bigram floor. All three seeds are identical at 100% because every run
contains the same complete training set; this zero variance is expected for a
deterministic count model.

This establishes the corpus scaling floor.

## IndicBERTv2 transfer control

The next pilot uses pinned `ai4bharat/IndicBERTv2-MLM-only` revision
`8598f13fe52443bc3fc054fcd665944560145b5c`. The 277.5M-parameter encoder is
frozen; only the 842,128 parameters in the MLM prediction transform and output
bias are trained for 64 steps under seeds 17, 29, and 43. Each seed draws from
the training split and scores the same 128-record validation subset with 538
deterministic masked tokens.

| Run | Validation cross-entropy | Masked-token accuracy |
| --- | ---: | ---: |
| Unadapted checkpoint | 6.678164 | 21.747212% |
| Seed 17 | 6.590277 | 22.118959% |
| Seed 29 | 6.557475 | 21.747212% |
| Seed 43 | 6.587905 | 21.933086% |
| Adapted mean | **6.578552** | **21.933086%** |

All three seeds improve validation cross-entropy. The mean improvement is
0.099612 with a 0.014935 standard deviation. This justifies moving to encoder
LoRA or full continued pretraining. It is a validation-only transfer result; the
frozen test candidate has not been evaluated or used for selection.

## Encoder LoRA continuation

The encoder experiment inserts rank-4 LoRA weights into all attention query and
value projections, leaving the MLM head and base parameters frozen. This trains
147,456 of 278,292,880 parameters. A 32-step screen improved every seed; the
validation-selected 256-step configuration was then run under all three seeds.

| Run | Validation cross-entropy | Masked-token accuracy |
| --- | ---: | ---: |
| Unadapted checkpoint | 6.678164 | 21.747212% |
| Seed 17 | 6.069991 | 21.747212% |
| Seed 29 | 6.054579 | 21.747212% |
| Seed 43 | 6.063375 | 21.561338% |
| LoRA mean | **6.062648** | **21.685254%** |

The mean validation loss improves by 0.615516 with a 0.006313 standard deviation.

## Frozen transfer comparison

After fixing the LoRA configuration, one deterministic 256-record subset of the
frozen test candidate was opened. Its SHA-256 is
`943cd7bf66ac462fb0e6db9e10783ceca727ee131aefceb0da62774ae6c060e3`; every model
scores the same 1,037 masked tokens.

| Family | Test cross-entropy | Standard deviation | Masked-token accuracy |
| --- | ---: | ---: | ---: |
| Unadapted IndicBERTv2 | 6.659330 | 0.000000 | 20.443587% |
| 64-step head-only adaptation | 6.537236 | 0.022426 | 20.475731% |
| 256-step encoder LoRA | **6.014093** | **0.008828** | **21.279331%** |

All three LoRA seeds beat both the base and head-only controls. The LoRA mean
reduces frozen-test cross-entropy by 0.645237 and raises masked-token accuracy by
0.835744 percentage points. Exact train/test overlap is zero. This result is
closed: the test subset will not be used to retune the same model family.

## Reproduce

```bash
python3 scripts/run_text_scaling_experiment.py
PYTHONPATH=.cache/asr-runtime python3 scripts/run_indicbert_adaptation.py --device cpu
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_indicbert_lora_adaptation.py --device cpu --steps 256 --training-records 2048
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/evaluate_indicbert_transfer.py --device cpu --test-records 256
```

The full run matrix is generated under `data/processed/evaluation/` and remains
outside Git. The tracked release manifest records the selected configuration and
result.
