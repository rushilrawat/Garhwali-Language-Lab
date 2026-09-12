# Controlled Garhwali modeling: continuation and instruction tuning

## Scope

This cycle completes the planned longer encoder-continuation and first
instruction-tuning experiments. Both use fixed train/validation/test boundaries,
three seeds (17, 29, and 43), pinned base revisions, ignored local checkpoints,
and immutable source records. Every collected instruction record remains active
for local experiments; none is placed in quarantine.

## Longer IndicBERTv2 continuation

The continuation keeps the IndicBERTv2 MLM head and original weights frozen and
trains 147,456 rank-4 LoRA parameters on attention query/value projections. Each
seed draws an 8,192-record pool from the full 80,926-record training partition
and takes 1,024 train-only update steps. Selection still uses the same 128-record,
538-mask validation subset. The previously opened frozen transfer test is not
reused.

| Run | Validation cross-entropy | Masked-token accuracy |
| --- | ---: | ---: |
| Unadapted checkpoint | 6.678164 | 21.747212% |
| Seed 17 | 5.610578 | 23.048327% |
| Seed 29 | **5.607038** | **23.791822%** |
| Seed 43 | 5.655880 | **23.791822%** |
| 1,024-step mean | **5.624498** | **23.543990%** |

The mean loss is 0.438150 lower than the earlier 256-step LoRA mean, a 7.23%
relative reduction. All three seeds beat the unadapted and shorter-run validation
results. This validates longer Garhwali continued pretraining while preserving
the closed transfer-test result.

## Instruction dataset

The split-safe instruction builder converts existing parallel and lexicon
evidence into 2,518 bidirectional examples. Parent documents retain their
existing split, and provenance, rights, semantic-domain, and active-use metadata
stay attached.

| Split | Records |
| --- | ---: |
| Train | 2,304 |
| Validation | 130 |
| Test | 84 |
| Total | **2,518** |

The six tasks contain 892 sentence-translation instructions, 1,106
English/Garhwali lexicon instructions, and 520 Hindi/Garhwali lexicon
instructions. Checks find zero parent crossing, zero exact instruction-pair
crossing, zero missing parent splits, and zero benchmark records used for
training.

## mT5 instruction tuning

Pinned `google/mt5-small` revision
`73fb5dbe4756edadc8fbe8c769b0a109493acf7a` supplies the 300,176,768-parameter
base. Each run trains 172,032 rank-4 LoRA parameters on encoder and decoder
attention `q`/`v` projections for 64 steps. The 2,304 training records form the
active pool; deterministic task balancing exposes 64 unique records per seed in
this first compute-bounded pilot.

| Run | Validation cross-entropy | Test cross-entropy | Test exact match | Test chrF2 |
| --- | ---: | ---: | ---: | ---: |
| Base mT5 | 28.201385 | 30.416287 | 0% | 0.000000 |
| Seed 17 | 28.007602 | 30.502042 | 0% | 0.000000 |
| Seed 29 (validation-selected) | **27.194060** | **29.059347** | 0% | 0.000000 |
| Seed 43 | 27.507977 | 29.014620 | 0% | 0.000000 |
| Adapted mean | **27.569880** | **29.525337** | 0% | 0.000000 |

All seeds improve validation loss. Two of three improve test loss, and the
validation-selected seed 29 improves test loss by 1.356940. Generation does not
improve: every system emits only the mT5 sentinel `<extra_id_0>` for every test
prompt. The evaluator removes that control token before scoring, leaving empty
answers. The adapter is therefore retained as a reproducible negative/early
baseline and is not promoted for generation.

The fixed 84-record test split was opened only after every seed was trained and
the validation-selected seed was fixed. It is closed for further tuning of this
configuration.

## Reproduce

```bash
python3 scripts/build_instruction_dataset.py
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_indicbert_lora_adaptation.py --device cpu --steps 1024 --training-records 8192 --output data/processed/evaluation/controlled_modeling/indicbert_lora_long.json --checkpoint-dir models/controlled_modeling/indicbert_lora_v0.2
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_mt5_instruction_tuning.py --device cpu --steps 64 --training-records 2304
```

Generated datasets, model weights, adapters, and predictions stay ignored. The
tracked code, dataset card, release summary, and this report contain the
configuration and results needed to audit the experiment.
