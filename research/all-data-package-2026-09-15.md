# Complete all-data package

> **Historical snapshot (2026-09-15).** Current authoritative counts are in [`release/v0.1.0-manifest.json`](../release/v0.1.0-manifest.json) and the 2026-09-19 report.

The Garhwali Language Lab now builds a first-class `all-data` Hugging Face
profile. It keeps every collected text value available for quality improvement,
research, and model preparation. No text is placed in a hidden or quarantine
tier.

## Verified contents

| Layer | Rows |
| --- | ---: |
| Full prepared text segments | 114,082 |
| Exact-unique source-text catalog | 28,755 |
| Catalog texts redacted | 0 |
| Human VAANI ASR split | 5,894 |
| SraVaani machine-draft audio identities | 104,534 |
| Lexicon | 1,114 |
| Instructions | 2,568 |
| Total exported rows | 256,947 |

The eight repeated SraVaani source rows are represented once per identical audio
hash and retain `source_audio_records`, so the package does not train twice on an
identical recording while still accounting for every source row.

Every source text retains provenance, language and quality evidence, its original
rights status, and a stable hash. Rights metadata is descriptive; it does not
delete, redact, quarantine, or lower the training visibility of a row inside the
all-data package. A separate `public` profile remains available for redistribution
decisions.

## Reproduce

```bash
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py \
  --profile all-data
```

The generated package is `data/huggingface/garhwali-language-lab-all-data/`.
Its `manifest.json` must report `all_collected_text_values_included: true` and
`catalog_redacted_text_records: 0`.
