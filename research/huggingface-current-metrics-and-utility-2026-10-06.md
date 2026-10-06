# Hugging Face dataset size, content, and training utility — 2026-10-06

## Executive result

The public corpus is a useful source/provenance catalogue and research resource,
but it is **not currently a ready-to-train general Garhwali text corpus**. Its
Hub headline of 961,533 rows sums overlapping config views and reference tables;
it does not mean 961,533 language examples. In the published `text`,
`text_expansion`, and `text_resources` configs, **zero rows are currently marked
recommended for general text training**. The separate speech repository has
substantial audio, but most audio has no provider transcript, and its machine
drafts are not reference transcripts.

This report replaces storage totals or viewer row counts as proxies for model-
ready data. It does not remove, rewrite, or change the rights status of records.

## Live Hugging Face repositories

The Hub pages were checked on 6 October 2026:

| Repository | Hub total file size | Hub displayed rows | What the counts mean |
| --- | ---: | ---: | --- |
| [garhwali-corpus](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) | 7.56 GB | 961,533 | 183,376 overlapping content-config view rows plus 778,157 reference-table view rows |
| [garhwali-speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech) | 36.5 GB | 113,363 | 110,436 VAANI and 2,927 Meta Omnilingual speech rows |

The corpus reference tables are 355,846 `record_index` rows, 9,571
`source_catalog` rows, and 412,740 `record_sources` joins. Together they are
778,157 view rows, or **80.9%** of the Hub's 961,533-row display. They are
valuable for provenance and discovery, but they are not text or training
examples. The remaining 183,376 rows are also overlapping views and include
catalog, bibliography, vocabulary, transcripts, instructions, and experimental
text—not 183,376 unique passages.

Hub total-file-size values describe each repository, including retained
versioned paths. They should not be compared directly with local source-file
sizes or presented as unique language-content volume.

## Actual text and transcript content

Counts below come from the v0.2.7 prepared export at corpus commit
[`1f7b2ce`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/1f7b2ceed1b743412b75d6288757e1d2cadac9c4),
using the row fields and CSV manifest in the local prepared package.

| Config or item | Rows | Text measure | Quality/use status |
| --- | ---: | ---: | --- |
| `text` | 18,598 | 291,914 whitespace-separated words; 1,373,045 characters | All 18,598 are `automated_quality_assessed_unreviewed`; all have `recommended_for_training=false` |
| `text_expansion` | 1,737 | 156,464 words; 754,117 characters | All 1,737 have `recommended_for_training=false`; 454 are in `source_overlap` |
| `text_resources` | 475 | 43,518 words; 196,400 characters | All 475 have `recommended_for_training=false`; quality and reuse terms vary |
| Three text-oriented config views, summed | 20,810 | 491,896 words; 2,323,562 characters | View sum only; the configs can overlap; 0 rows currently recommended |
| `paharili_gbm` | 14,988 | 236,566 words; 1,091,695 characters | Experimental language-identification view; item origins and Garhwali labels remain unresolved/unreviewed; not general LM training data |
| `asr` | 2,002 | 36,228 transcript words; 163,317 characters | Strict speaker-disjoint provider/human-reference view; all are `not_reviewed`, not native-adjudicated |
| `sravaani_drafts` | 104,534 | 104,500 non-empty drafts; 34 empty | Machine hypotheses only; all are marked noisy experimental and not training eligible |

The config rows overlap with the catalog and with each other. Word totals are
whitespace counts, not linguistic tokenization. Do not sum the rows above and
call the result unique training text.

The parent text catalog has 36,105 records. Its `catalog.text` field is blank
for 23,448 rows, but a cross-config scan found 15,004 of those values elsewhere
in the public repository. The remaining **8,444 distinct full texts**, totaling
2,936,664 words and 16,388,267 characters, are held locally with
`rights_pending` / `not_cleared` status and are not present as full text in the
public repository. All have a source locator, but some locators identify only a
collection or dataset. A locator is not rights clearance.

## Speech: substantial audio, limited adjudicated transcripts

The public speech repo contains 113,363 rows, 113,350 unique audio hashes,
154.65 hours, and about 16.91 GiB of embedded source audio. That represents
audio availability, **not 113,363 supervised audio/transcript pairs**.

- VAANI contributes 110,436 recordings and 5,894 provider-transcribed rows.
- The linked corpus `asr` config is the stricter 2,002-row speaker-disjoint
  subset (1,621 train / 269 validation / 112 test); its transcripts remain
  unreviewed.
- Meta Omnilingual contributes 2,927 recordings and 19.14 hours. Its upstream
  references are not native-speaker adjudications; split-safety fields must be
  applied for evaluation.
- SraVaani produced 104,542 source rows that deduplicate to 104,534 audio
  hashes. Of those, 104,500 carry a non-empty machine draft and 34 are empty.
  These drafts must not be counted as human transcripts or gold labels.

The Hub page's 36.5 GB is the repository's total file-size display; 16.91 GiB
is the embedded source-audio size reported in the package manifest. They are
different measures.

## Where the local 77 GB / 120 GB figures went

A fresh local inventory found 230,707 files below `data/` on 6 October 2026.
The folder's path-by-path logical file sizes total **171,249,207,713 bytes
(171.25 GB / 159.49 GiB)**. Because release snapshots use hard links, unique
file-inode sizes total **128,503,289,760 bytes (128.50 GB / 119.68 GiB)**.
`du -sk data` reports about **119.93 GiB allocated**. These are storage
measures, not unique Garhwali text or training-data counts. The earlier 77 GB
headline is not the current complete `data/` total; it used a different or
partial accounting scope and cannot be reconciled as a unique-data figure.

| Local path | Logical bytes | Main contents |
| --- | ---: | --- |
| `data/huggingface/` | 87,100,082,741 | Versioned/staging Hub packages; 58.93 GB across unique file inodes, with repeated hard-linked paths across snapshots |
| `data/processed/` | 41,807,390,124 | Derived views and model/evaluation artifacts, including large checkpoints; not all are corpus text |
| `data/vaani/` | 32,118,891,449 | VAANI source, extracted audio, and reference images |
| `data/downloads/` | 9,351,063,686 | Acquired sources and media, including Internet Archive video and Meta data |
| `data/kaggle/` | 767,391,421 | Ignored local export packages; not published to Kaggle |
| `data/extracted/` | 104,222,678 | Extracted text and source-specific derived files |

Across all `data/`, 42,745,917,953 bytes are repeated hard-linked paths rather
than additional file inodes. This confirms repeated snapshot paths, not all
content-level duplicates: separate files with identical bytes require a hash
comparison. No data was deleted in this inventory.

## What users can realistically do today

- **Discover sources and provenance:** use `catalog`, `record_index`,
  `source_catalog`, and `record_sources`; filter by the per-row rights and
  quality fields.
- **Explore vocabulary:** use `lexicon` as source-spelling and gloss candidates;
  entries are not native-validated.
- **Experiment with language identification:** use `paharili_gbm` only with its
  unresolved sentence origins and upstream-label limitations clearly retained.
- **Prototype ASR and speech analysis:** use the speech configs and distinguish
  provider references from SraVaani machine drafts; do not claim validated
  accuracy from the current labels.
- **Train a general Garhwali text model:** the current release has no
  project-recommended text rows under its conservative eligibility flags.
  Users could independently inspect records and source terms, but the project
  should not market the corpus as ready-to-train LM data.

The corpus is therefore best described today as a **source-linked Garhwali
research/resource collection with a substantial speech archive**, not a
large, clean, generally reusable training corpus. Improve the useful-content
counts through source-specific rights resolution, duplicate/quality gates,
transcript review, and a separate purpose-labeled training subset. Keep viewer
row totals, repository bytes, text words, audio hours, and training-eligible
examples as separate metrics in every future report.

## Method and reproducibility

- Live repository sizes, displayed rows, and current configs were read from the
  two public Hugging Face pages on 6 October 2026.
- Text row, word, character, training-flag, and draft counts were recomputed
  from `data/kaggle/garhwali-language-corpus-v0.2.7/*.csv` and its
  `manifest.json`, which identify the upstream v0.2.7 commit above. The Kaggle
  package is a local measurement/export, not a Kaggle publication.
- Local file sizes were counted with `stat` over `data/`; repeated hard links
  were grouped by `(device, inode)`. Allocated blocks were read with `du -sk`.
- This closeout changes documentation only. It does not alter data payloads,
  row rights, model weights, splits, or benchmark results.
