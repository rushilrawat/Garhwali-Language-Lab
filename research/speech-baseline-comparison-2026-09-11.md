# Garhwali speech baseline comparison

Generated on 2026-09-11 on the strict speaker-safe ASR test manifest. All local
scores use the same **112 recordings**, **2,086 reference words**, **7,134
reference characters**, punctuation-insensitive Unicode normalization, and
micro-averaged WER/CER. Lower is better.

## Comparable local results

| Model | Training state | WER | CER |
| --- | --- | ---: | ---: |
| `openai/whisper-tiny` | Zero-shot; Hindi language prompt | 1.479386 | 1.368096 |
| `openai/whisper-small` | Zero-shot; Hindi language prompt | 0.971716 | 0.578217 |
| `whisper-tiny-garhwali-v0.1` | 1,621 Garhwali steps | 0.790508 | 0.429072 |
| `whisper-tiny-garhwali-v0.2` | 3,242 total Garhwali steps | **0.743049** | **0.404401** |

The zero-shot tiny model frequently emits long hallucinated sequences, which is
why its WER and CER exceed 1.0. Whisper-small reduces that failure substantially.
The selected v0.2 checkpoint improves WER by 23.53% relative to zero-shot small
and by 49.77% relative to zero-shot tiny. It still makes roughly three word edits
per four reference words and remains unsuitable for automatic transcript
promotion.

Both saved fine-tuned prediction files were rechecked against the current test
manifest: all 112 audio hashes match, no audio hash is duplicated, every
reference matches, and recomputation with `scripts/asr_metrics.py` reproduces the
stored WER/CER exactly.

## SraVaani status

[SraVaani 1.0](https://vaani.iisc.ac.in/models/sravaani) is the strongest
currently relevant external candidate: its official page lists Garhwali among
65 supported languages, an MIT release, and gated Hugging Face access. Its
[model card](https://huggingface.co/ARTPARK-IISc/SraVaani-1.0) reports **53.5
WER** for Garhwali on its own Vaani evaluation.

The authenticated project account can access the VAANI datasets but, as of
2026-09-11, the SraVaani model repository returns `Access denied. This repository
requires approval.` No weights were downloaded. The published 53.5 result is
context only because its split, decoding, and scoring differ from this 112-row
speaker-safe evaluation. Community mirrors are not used to bypass the gate.

The 2026 VarDial study previously catalogued in this repository reports other
Garhwali systems on another split, including wav2vec2-BERT at 0.493 WER / 0.193
CER. Those numbers also remain external references rather than direct comparisons.

## Reproduction

```bash
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --model .cache/huggingface/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d --model-id openai/whisper-small --revision 973afd24965f72e36ca33b3055d56a652f456b4d --output data/processed/evaluation/asr/whisper_small_zero_shot --device cpu
```

Raw audio, model weights, and generated predictions remain ignored by Git. The
tracked candidate manifest records aggregate results and the exact test-manifest
checksum.
