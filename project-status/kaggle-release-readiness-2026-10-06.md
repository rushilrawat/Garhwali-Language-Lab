# Kaggle release preparation audit — 2026-10-06

## Live platform follow-up — 2026-10-07

This audit records the original 6 October packaging state. Since then, the
focused screened-text package was published publicly at Kaggle version 1
(1,841 training candidates and 110 context rows), and the ASR package was
updated privately to version 2 (2,718 existing VAANI references). The
baseline notebook is saved at version 3 with v2 input and remains unrun. The
latest counts and status are in the [cross-platform metrics audit](current-platform-metrics-2026-10-08.md)
and [ASR v0.2 sync report](../research/kaggle-asr-v0.2-sync-2026-10-07.md).

The initial packaging report below remains a snapshot; its statements that
these packages were unpublished describe the state on 6 October.

## Quality-first text package follow-up — 2026-10-06 snapshot

A separate, focused package is built locally for direct Kaggle use:
1,841 sentence-length training rows plus 110 nonblank short utterances in a
separate context CSV. It carries CC BY 4.0 attribution, row-level provenance,
quality labels, a documented duplicate exclusion, and matching source/output
hashes. The matching configs are already live in the Hugging Face corpus at
[v0.2.8 commit `48f9107`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/48f9107d0285b3b3ec3c893303efb8a997cfc49b).
The corrected live card is at [commit `cf60b2175`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/cf60b217d9d3de045d81fb41d82514e29db2bf33).
The focused package is **not published on Kaggle yet**;
see the [quality-screened text release report](../research/quality-screened-text-release-report-2026-10-06.md)
and [publication roadmap](../research/huggingface-kaggle-quality-release-roadmap-2026-10-06.md).

## Status — original 6 October snapshot (historical)

The reproducible Kaggle packages are built locally and kept under the
Git-ignored `data/kaggle/` directory. The broad corpus and speech-metadata
packages remain unpublished. The focused screened-text package is also not
published yet. The user approved enabling the ChatGPT extension's local-file
access permission, but a browser security restriction prevents automated
extension-setting changes; the user must toggle it manually. No Kaggle upload
has occurred.

## Packages prepared

| Package | Source snapshot | Kaggle license field | Data included |
| --- | --- | --- | --- |
| `Garhwali Language Corpus v0.2.7` | Public Hugging Face corpus v0.2.7, commit `1f7b2ceed1b743412b75d6288757e1d2cadac9c4` | `other`, with source-specific terms explained in the card and row fields | 17 configs, 26 config/split views, 946,545 overlapping view rows, plus a content-free 14,988-row PahariLI ID/hash index |
| `Garhwali Speech Metadata v0.2.1` | Public Hugging Face speech release v0.2.1 | `CC-BY-4.0` | 113,363 transcript/metadata rows across VAANI and Meta Omnilingual; no audio bytes |

The corpus CSVs use one file per configuration. Nested values are serialized as
JSON strings; `dataset_config` and `dataset_split` retain the originating view.
The combined package has 961,533 CSV rows if the separate PahariLI index is
counted, but these are overlapping dataset views and references, not unique
training examples. The text package is 618,336,483 bytes; the speech metadata
CSV is 149,054,706 bytes.

The count does not mean the package supplies a 961,533-row training corpus. The
17 included configs have 946,545 overlapping rows; 778,157 are source/reference
rows. The 14,988 PahariLI source-index rows contain IDs and hashes, not sentence
text. The `text`, `text_expansion`, and `text_resources` configs sum to 20,810
overlapping view rows / 491,896 whitespace-separated words / 2,323,562
characters; the main `text` config alone has 18,598 rows / 291,914 words.
None of the 20,810 rows is currently recommended for general text training.
The full breakdown and local storage numbers are in the [current
Hugging Face metrics audit](huggingface-current-metrics-and-utility-2026-10-06.md).

## Scope and reuse

Each text row retains source-level provenance, attribution, license labels,
rights status, reuse scope, and quality status where present. Kaggle requires
one dataset-level license entry; its supported `other` value is used for the
corpus because the component records have different terms. The card says
explicitly that this is not a blanket license. Users must follow the terms on
each record. See the [Kaggle dataset metadata contract](https://github.com/Kaggle/kaggle-cli/blob/main/docs/datasets_metadata.md)
and [Kaggle dataset documentation](https://www.kaggle.com/docs/datasets).

The existing 8,444 local-only full texts remain absent from this derived public
package while item-level redistribution evidence is unresolved. Their public
catalog entries keep content blank, with source IDs and locators. No source
text was removed from the local all-data package. The 14,988 PahariLI sentence
bodies are omitted because the upstream Apache declaration does not establish
rights for the underlying sentences; `paharili_source_index.csv` retains only
IDs, hashes, split/source identifiers, and the reason for omission. This does
not alter the existing Hugging Face v0.2.7 dataset.

The speech CSV excludes the nested `audio` column before reading Parquet row
batches, so no audio bytes are copied. It records `audio_included=false` and a
link to the public Hugging Face speech dataset on every row. Provider
transcripts and SraVaani machine drafts remain separately labeled; machine
drafts are not ground truth. The GarhwaliBench evaluation release is not
included; it remains a local draft with public rights and independent-evidence
gates unresolved.

## Verification

- Rebuilt all 17 corpus config CSVs from the exact v0.2.7 staging package and
  reconciled every output row count with its input manifest.
- Verified SHA-256 for all 18 corpus CSVs (17 configs plus the PahariLI index)
  and for the speech CSV.
- Re-read the speech CSV: 113,363 rows, zero audio columns, and no embedded
  audio bytes. The source contains 110,436 VAANI and 2,927 Meta Omnilingual
  rows; the release reports 113,350 unique audio hashes.
- Compared all 14,988 PahariLI normalized sentence values against every
  string-valued CSV field in the corpus export, using NFKC, case-folding, and
  collapsed whitespace. There were zero exact matches. This check does not
  establish absence of paraphrases, translation overlap, or other near
  duplicates.
- Added two exporter regression tests: nested corpus fields and the omission
  index are preserved; speech audio is excluded while transcript metadata is
  retained.
- Full repository test suite: **820/820 passed** with the documented command
  `PYTHONPATH=scripts .venv/bin/python -m unittest discover -s tests -p 'test_*.py'`.

The build is reproducible with:

```bash
.venv/bin/python scripts/build_kaggle_release.py
```

The local output folders are:

- `data/kaggle/garhwali-language-corpus-v0.2.7/`
- `data/kaggle/garhwali-speech-metadata-v0.2.1/`

## Work that remains outside this Kaggle packaging fix

Kaggle mirrors make the eligible public resource easier to discover; they do
not resolve the 8,444 full-text rights queue, validate Garhwali language
quality, review the 104,500 non-empty SraVaani drafts, or clear the benchmark.
Native review remains deferred. The source intake stop point remains in effect:
this pass added no new source records.
