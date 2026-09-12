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
| `ARTPARK-IISc/SraVaani-1.0` | Provider-approved multilingual Indic ASR | **0.427613** | **0.176058** |

The zero-shot tiny model frequently emits long hallucinated sequences, which is
why its WER and CER exceed 1.0. Whisper-small reduces that failure substantially.
The selected v0.2 checkpoint improves WER by 23.53% relative to zero-shot small
and by 49.77% relative to zero-shot tiny. It still makes roughly three word edits
per four reference words and remains unsuitable for automatic transcript
promotion.

SraVaani reduces WER by 42.45% and CER by 56.46% relative to the best local
Whisper checkpoint. Its 42.76% WER is a major improvement but still does not
justify automatic promotion of unreviewed transcripts.

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

Provider access was verified on 2026-09-12. The complete 867 MiB inference
package was downloaded to the ignored project Hugging Face cache, inspected, and
run from pinned revision `f5dd5358325a5208775b91dad98918e079ea2b27`. The
TorchScript model artifact SHA-256 is
`789a21b6df8b0bb2ea2cc1c120edbfd4b898d3a26e6c6673cca45d14b64a47f2`.
The published 53.5 result remains context because its split, decoding, and scoring
differ from this 112-row speaker-safe evaluation.

The 2026 VarDial study previously catalogued in this repository reports other
Garhwali systems on another split, including wav2vec2-BERT at 0.493 WER / 0.193
CER. Those numbers also remain external references rather than direct comparisons.

## Untranscribed-audio pilot

The resumable SraVaani path processed the first 100 priority records from the
104,542-row untranscribed queue. All audio hashes are unique, 99 drafts are
non-empty, and mean Devanagari share among alphabetic output is 91%. The same 100
audio hashes have earlier Whisper drafts, with zero exact transcript agreement.
There are no references for these rows, so agreement is not an accuracy score.
All SraVaani drafts retain source metadata and remain active only as explicitly
noisy experimental records.

## Reproduction

```bash
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --model .cache/huggingface/hub/models--openai--whisper-small/snapshots/973afd24965f72e36ca33b3055d56a652f456b4d --model-id openai/whisper-small --revision 973afd24965f72e36ca33b3055d56a652f456b4d --output data/processed/evaluation/asr/whisper_small_zero_shot --device cpu
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/run_sravaani_comparison.py --device cpu --batch-size 4
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/transcribe_sravaani_drafts.py --device cpu --batch-size 4 --max-records 100
```

Raw audio, model weights, and generated predictions remain ignored by Git. The
tracked candidate manifest records aggregate results and the exact test-manifest
checksum.
