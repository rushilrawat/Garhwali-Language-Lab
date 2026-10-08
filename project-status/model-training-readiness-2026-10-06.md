# Garhwali model-training readiness — 2026-10-06

> Dated snapshot. For the current public CPU training example, dataset
> contracts, and release checks, use the [developer readiness guide](../docs/DEVELOPER_READINESS.md)
> and [8 October platform audit](current-platform-metrics-2026-10-08.md).

## Decision

The local text profile now loads as a normal Hugging Face `datasets` JSON dataset
and its default train/development splits contain only records covered by the
project's exact Meta Omnilingual CC BY 4.0 decision. The larger text candidates
remain outside those splits until their source and quality flags are resolved.

No new Hub upload or cloud training job was made in this pass. The eligible Meta
texts are already in `rushilrawat/garhwali-corpus`, the speech companion is
already public, and the connected Hugging Face credential currently has no
repository-write scope. The account reports no Pro plan, which the configured
Hugging Face Jobs training workflow requires. A new job without a way to push
its model artifacts would lose the result when the job ends.

## Text profile built locally

Rebuild with:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/build_model_training_candidate.py
```

The generated `data/training/garhwali-text-training-v0.2/` package has:

| File | Rows | Purpose |
| --- | ---: | --- |
| `train.jsonl` | 1,657 | Plain-text continued-pretraining candidates |
| `validation.jsonl` | 184 | Deterministic 10% record-level development slice |
| `context.jsonl` | 110 | Short Meta utterances; excluded from default training |
| `review_queue.jsonl` | 2,077 | OBS/LSI candidates with source training and release flags false |
| `pdf_rights_queue.csv` | 7 supplied PDFs / 6 unique | Rights and prior-ingestion inventory |

Train and validation together contain 47,566 words, all from the Meta
Omnilingual CC BY 4.0 subset. The original source eligibility flag is retained
separately from the project decision. The validation slice comes from the
upstream train split and shares 9 of its 10 speakers with training; use it only
as a development loss monitor, not as an independent benchmark. A `datasets` load
confirmed 1,657 train and 184 validation rows, eligible flags on both splits,
and no model-eligible rows in the review queue.

The 1,793 Open Bible Stories rows and 284 1916 LSI rows in the review queue are
not optimizer data or evaluation data. Their recorded training/public-release
flags remain false; the story translation review and LSI OCR/native review are
also unresolved. The package is not instruction/chat data. It is suitable only
for a small continued-pretraining experiment, not training a language model
from scratch.

## Existing audio training path

The Hub speech dataset is already uploaded. The local strict transcript profile
has 4,778 train, 666 validation, and 450 test rows (about 7.17, 0.96, and 0.68
hours). The larger confidence-weighted curriculum has 106,057 train rows and
129.31 audio hours: 1,621 human/provider references plus 104,436 machine-labeled
rows, with 269 human-only validation rows and 112 held-out test rows. The
machine labels are weighted experimental targets, not gold transcripts.

The Whisper training code and curriculum are already in the repository. Stage 0
uses the human reference data. A weighted stage-1 ablation worsened validation
WER/CER, so the full pseudo-labeled curriculum should not be promoted just by
adding volume; it needs a better training recipe and a human-only validation
win first.

## PDFs

Seven supplied files represent six unique PDFs and 769 active page records.
The PDFs already fed a completed IndicBERT domain-adaptation job: 25,983 train
segments, 615 validation segments, and 1,328 test segments. The held-out test
was not used for training or selection. Selected-seed validation accuracy rose
from 25.20% to 35.84%, with validation loss moving from 6.19 to 4.52. This was
PDF-domain masked-language-model adaptation, not a Garhwali text-generation
model.

The source rights queue identifies copyrighted, unresolved, or
limited-reproduction material. Keep these texts out of another public release
or model publication until each edition's reuse and training scope is resolved.

## Hugging Face source check

The Hub dataset-search connector was disabled by server configuration during
this pass, so I used Hub search and repository cards as a fallback.

- `hikinegi/Garhwali-Dataset` has 53 Romanized prompt/response pairs and is
  already stored locally in the experimental layer. Its card does not declare
  a license or authorship, and at least one answer identifies Kumaon; it is not
  cleared for training.
- `abar-uwc/vaani-uttarakhand_tehrigarhwal-cleaned` shows 6.87K mixed-language
  audio/text rows. A displayed image ID and transcript match the locally
  collected official Vaani source after removing its `[breathing]` annotation.
  The repo card does not show a reuse license;
  exact row/audio deduplication and rights evidence are needed before treating
  any extra rows as new.
- `aoiandroid/mms-multilingual-audio-5to30min` includes about 28.3 minutes of
  Garhwali YouTube-derived audio without transcripts. It is a known source lead,
  not supervised training data; resolve underlying audio rights and duplication
  before using it.
- Google's IndicGenBench CrossSum card explicitly says not to use benchmark rows
  for LLM pretraining. Keep it evaluation-only.

The 53-row Hikinegi set and CrossSum are already cataloged locally. The Vaani
collection is already present locally and in the public speech dataset; the
third-party cleaned mirror does not yet establish any net-new usable rows.

## Next training steps

1. Use the local text profile only for a small continued-pretraining trial; keep
   its validation slice as a development monitor and do not claim benchmark
   performance.
2. For a stronger model-development result, continue the existing Whisper path
   with a revised stage-1 recipe and human-only validation. The text profile and
   audio curriculum are separate tasks and should stay separate.
3. Increase reusable text only after native review and source-by-source rights
   resolution. The broader local archive still has 8,444 full texts marked
   rights-pending (about 2.94 million whitespace-separated words).
4. Before a new Hugging Face run, reconnect with repository-write permission and
   an eligible Jobs plan so the model can be saved to the Hub.
