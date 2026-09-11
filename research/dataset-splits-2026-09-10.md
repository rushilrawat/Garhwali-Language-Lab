# Garhwali dataset split status

Generated 2026-09-10. The split layer preserves all broad experimental views
while producing narrower candidates whose leakage claims can be verified.

## Text

The 86,215 exact-unique sentence segments are grouped by connected parent
documents. If two documents share a segment, directly or through another
document, the entire connected component receives one split. This resolved all
332 conflicts in the earlier hash-only assignment and moved 136 of 27,987
documents.

| Split | Documents | Segments |
| --- | ---: | ---: |
| Train | 25,293 | 80,926 |
| Validation | 1,364 | 2,488 |
| Test | 1,330 | 2,801 |

The segment ratio differs from the document ratio because long documents and
connected duplicate groups contribute different numbers of segments. No exact
segment hash crosses a split.

## Strict speech candidates

VAANI's full 5,894-row supervised view remains available. The strict split keeps
only rows with an identified speaker, a readable audio file, a clean Garhwali
language label, a non-empty cleaned transcript, and no transcript or training
quality flag.

| Split | Rows | Hours |
| --- | ---: | ---: |
| Train | 1,621 | 2.870413 |
| Validation | 269 | 0.471185 |
| Test | 112 | 0.220797 |
| **Total** | **2,002** | **3.562395** |

The strict ASR and TTS candidate manifests cover 248 identified speakers, with
zero speaker identities crossing splits. They exclude 3,886 placeholder-speaker
rows and six language/transcript-review rows. Exclusion from the strict view does
not remove a row from the broader supervised corpus.

The ASR and TTS manifests are currently identical candidate selections. TTS use
still requires speaker suitability, consent-scope, transcript, and audio review;
the label does not claim that every retained speaker is ready for voice modeling.

## Evaluation candidates

The frozen candidate manifests contain 2,492 unflagged text-test segments and 112
strict ASR test rows. Every row is marked `pending_native_review`. They provide a
stable review target but are not yet the final benchmark, because freezing a
language evaluation without Garhwali-speaker acceptance would turn automated
judgment into ground truth.

## Reproduction

```sh
.venv/bin/python scripts/segment_text_corpus.py
.venv/bin/python scripts/build_dataset_splits.py
.venv/bin/python scripts/build_release_manifest.py
```

Generated files live under `data/processed/model_ready/splits/`. Its `report.json`
records row counts, exclusion counts, leakage checks, and a SHA-256 digest for
every text, ASR, TTS, and evaluation artifact.
