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

This establishes the corpus scaling floor. The next controlled-modeling substep
is pretrained-model transfer and continued masked-language adaptation with the
same validation-first, frozen-test-last discipline.

## Reproduce

```bash
python3 scripts/run_text_scaling_experiment.py
```

The full run matrix is generated under `data/processed/evaluation/` and remains
outside Git. The tracked release manifest records the selected configuration and
result.
