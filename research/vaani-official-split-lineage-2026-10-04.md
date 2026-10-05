# VAANI official-split lineage and ASR diagnostic — 2026-10-04

## Result

The local prepared transcript manifest contains all **5,894** VAANI Garhwali
transcription-part rows and reconciles to the official **4,778 train / 666
validation / 450 test** split. The 5,894 audio hashes are unique across the
manifest, with no hash crossing an official split. The project's fixed strict
ASR manifests map exactly into the corresponding official splits: **1,621
train / 269 validation / 112 test** (2,002 records total).

The remaining **338 official test utterances** (0.454958 hours) were scored
once with the existing local Whisper-tiny v0.2 checkpoint. This is an **open
official-split diagnostic**, not an independent or speaker-generalization
result:

| Measure | Result |
| --- | ---: |
| Records / unique audio hashes | 338 / 338 |
| Corpus WER | **83.249%** (3,449 / 4,143 reference words) |
| Corpus CER | **48.468%** (7,356 / 15,177 reference characters) |
| Audio checked | 338/338 present, non-empty reference, mono 16 kHz 16-bit PCM |
| Speaker metadata | 5/338 rows identify a speaker; 333 are unidentified |

The checkpoint was trained on the 1,621-row strict human-reference train view.
The remainder has zero exact audio-hash overlap with that training view and
zero known speaker overlap among its five identified rows. Missing speaker
identity on 333 rows prevents a speaker-independent claim. The checkpoint was
already evaluated on the related fixed 112-row subset, and VAANI's official
test is public and used in other research, so this result is neither blind nor
independent. The 338-row references are prepared provider transcripts, not
native-speaker adjudications.

## Training exposure found

| Local view | Rows | Official VAANI train overlap | Validation overlap | Test overlap |
| --- | ---: | ---: | ---: | ---: |
| Strict ASR training | 1,621 | 1,621 | 0 | 0 |
| Expanded human-transcript training | 5,513 | 4,778 | 397 | 338 |
| Whisper curriculum candidate | 106,057 | 1,621 | 0 | 0 |

The expanded SraVaani training view excluded the project's fixed 269-row
validation and 112-row test manifests, but it included **397 other official
validation rows and 338 other official test rows**. Its checkpoint must not be
scored on the full official VAANI validation or test split. Its previously
reported fixed-112 test result remains a separate historical result because
those exact audio hashes were excluded from its training view.

The Whisper curriculum has no exact audio-hash overlap with official validation
or test, but its speaker IDs appear on 110 identified rows of the full official
test (mostly the fixed 112-row subset). The local Whisper-tiny v0.2 checkpoint
did not use that curriculum: its checkpoint report records human-reference
training on the strict 1,621-row view. Keep those two lineage statements
separate.

## Reproduction and artifacts

Run the aggregate-only lineage audit and optionally emit the local-only 338-row
manifest:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_vaani_official_split_lineage.py \
  --remainder-manifest data/extracted/research/vaani-official-test-remainder.jsonl
```

The scoring command was:

```bash
.venv/bin/python scripts/run_whisper_comparison.py \
  --model models/whisper-tiny-garhwali-v0.2 \
  --model-id whisper-tiny-garhwali-v0.2 \
  --revision local-v0.2 \
  --input data/extracted/research/vaani-official-test-remainder.jsonl \
  --output data/processed/evaluation/asr/whisper_tiny_official_test_remainder_2026-10-04 \
  --device cpu \
  --run-id whisper-tiny-v0.2-vaani-official-test-remainder-2026-10-04
```

The scoring report records the model weight SHA-256
`598546b068c3aa509ef5036ee4ff12502fbb3c0dc507096a56d1a2a3143d6225`, the
evaluation-manifest SHA-256
`e127a1c82989baf64bfa0dbf354a775d3feb67ef186fbce33f5cda2c45a83d26`, and
238.842 seconds of local CPU inference. An independent post-run audit matched
all 338 unique audio hashes and references, recomputed every per-row WER/CER
count, and reproduced the corpus totals exactly. Row-level audio, references,
and predictions remain in Git-ignored `data/`; this report contains aggregate
results and manifest fingerprints only.

The lineage command writes its aggregate JSON to
`data/extracted/research/vaani-official-split-lineage.json`. It emits no audio
hashes, row IDs, speaker IDs, or transcript text. The generated remainder
manifest and model predictions are local-only and must not be added to Git or a
public benchmark package without a separate source-rights review.

## Research context and next decision

The 2026 paper [*Seeds Before Objectives: Rethinking Evaluation for Low-Resource
Garhwali ASR*](https://arxiv.org/abs/2608.10670) reports w2v-BERT 2.0 with
standard CTC at 47.0% mean WER over five seeds on the same official VAANI
splits; its [code and per-seed results](https://github.com/soodashima91/Garhwali-ASR)
are public. That work provides useful multi-seed methodology, but it does not
turn our open VAANI scores into independent results, and its larger CTC model,
training view, and five-seed aggregate are not a like-for-like comparison with
our single Whisper-tiny remainder score.

Do not train on or select a model with the 338-row remainder. The next useful
ASR research step is a train/dev-only, multi-seed comparison using the strict
speaker-aware training pool, with a frozen recipe and a seed-level uncertainty
report. A truly independent language-accuracy claim still requires a source
and speaker history that can be audited, plus human reference review when
available.
