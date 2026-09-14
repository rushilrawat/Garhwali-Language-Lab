# SraVaani confidence-aware manifest integration

Confidence v0.2 is integrated into the complete SraVaani experimental draft
layer without replacing a source hypothesis or excluding a recording.

| Full local manifest | Records |
| --- | ---: |
| Original source rows | 104,542 |
| Unique audio hashes | 104,534 |
| Inherited duplicate-audio source rows | 8 |
| Confidence-scored recovery alternatives attached | 1,188 |
| Untargeted SraVaani drafts preserved | 103,354 |
| Removed or quarantined | 0 |
| Promoted to supervised training | 0 |

Each targeted row retains the original SraVaani hypothesis as
`machine_transcript`. A nested `recovery_confidence` object carries the local
Whisper alternative, structural flags, cross-model agreement, calibration
evidence, confidence band, and review priority. The score is explicitly marked
as a review signal rather than a correctness probability.

The transcript-only Hugging Face package now reads this enriched source. Its
SraVaani configuration contains 104,534 content-deduplicated rows, including all
1,188 confidence-scored records. It records the eight duplicate source paths as
source-record counts, contains no raw filenames or local paths, and packages no
audio. Public upload remains deferred.

## Reproduction

```bash
.venv/bin/python scripts/integrate_sravaani_confidence.py
.venv/bin/python scripts/build_huggingface_dataset.py \
  --output data/huggingface/garhwali-language-lab --profile public
.venv/bin/python scripts/build_release_manifest.py
```

Generated local artifacts remain ignored by Git:

- `data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware.jsonl`
- `data/processed/model_ready/transcripts/machine_drafts_sravaani_confidence_aware_report.json`
- `data/huggingface/garhwali-language-lab/`
