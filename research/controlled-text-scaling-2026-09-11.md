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

## Reproduce

```bash
python3 scripts/run_text_scaling_experiment.py
PYTHONPATH=.cache/asr-runtime python3 scripts/run_indicbert_adaptation.py --device cpu
```

The full run matrix is generated under `data/processed/evaluation/` and remains
outside Git. The tracked release manifest records the selected configuration and
result.
