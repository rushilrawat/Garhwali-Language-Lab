# Kaggle ASR run attempt — 2026-10-07

## Current Kaggle state — 2026-10-07

This records the initial v0.1 input/run attempt. Kaggle's private ASR dataset
has since been updated to version 2 with 2,718 existing VAANI reference clips
(2,202 train / 373 validation / 143 test), preserving all 2,002 previous
examples and adding 716 already-existing references. The notebook is saved at
version 3 with v2 input, but remains unrun; no Kaggle training result exists.
See the [v0.2 sync report](kaggle-asr-v0.2-sync-2026-10-07.md) and [current
platform metrics](../project-status/current-platform-metrics-2026-10-08.md).

The private Kaggle input dataset is [Garhwali ASR reference clips v0.1](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1). It contains 2,002 **existing** VAANI reference-labeled clips and the manifest used for the reproducibility notebook. These are not new corpus examples.

The [Garhwali ASR baseline notebook](https://www.kaggle.com/code/rushilrawat1/garhwali-asr-baseline-reference-labels) was imported and Quick Saved as version 1. Its first cell ran successfully on Kaggle's free CPU session and confirmed:

```text
train: 1,621; validation: 269; test: 112; device: CPU
```

The model-training cell was started, then stopped because Kaggle's notebook settings showed **Internet off** with a disabled toggle and a **Get phone verified** link. GPU was also disabled. Without internet, the notebook cannot fetch `openai/whisper-tiny`. No Kaggle training checkpoint or Kaggle WER/CER result was produced. Do not claim a Kaggle run completed.

The already-completed, no-cost local CPU run is documented in [whisper-cpu-finetune-2026-10-07.md](whisper-cpu-finetune-2026-10-07.md). It trained for one epoch on 4,778 strict ASR rows and improved WER/CER on a 338-row previously-unscored diagnostic subset from 0.8325/0.4847 to 0.7480/0.4349. It used an earlier Garhwali Whisper Tiny checkpoint as its starting point. See that report for evaluation exposure limits.

After the account owner completes Kaggle's phone verification, enable internet in notebook Session options and run all cells, or run training and scoring cells in order. Kaggle's free GPU may then become available, but CPU is sufficient if GPU remains unavailable.
