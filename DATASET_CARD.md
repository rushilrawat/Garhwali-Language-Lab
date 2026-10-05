# Dataset card: Garhwali Language Lab

## Summary

Garhwali Language Lab is a provenance-preserving collection and preparation
pipeline for Garhwali (`gbm`). It joins speech, transcripts, vocabulary, idioms,
folklore, folk songs, educational material, historical linguistics, community
writing, and cultural context without erasing source rights or uncertain language
labels.

The current public corpus release is **v0.2.5**. Its additive 51-file payload
is at [Hub commit `46407fc`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/46407fcb623d7f51d3f401f5842f73209dbffc4c).
The root and versioned cards are now at
[`dc3308d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dc3308d4eb1d0eb619ab78071d0b34c2cbe8ac09).
That card-only update includes the corrected versioned paths first published
at [`dbb1c99`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/dbb1c99503e11db454392a6c232254a37c9189d7) and explicit merged feature schemas for `text_expansion` and `sravaani_drafts`.
All 18 LFS and 33 Git-blob files match the planned local hashes; earlier
release paths remain. The new public `source_overlap` splits retain 1,308 core
and 363 text-expansion rows linked to upstream held-out source material,
outside default `train`. The release changes no text values and removes no
rows. The preceding
v0.2.2 release is at [commit `b9d0538`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b9d0538b5b4dda3be73e5ae33b279b371ef75c3f),
with its card correction at
[commit `b18933b`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/b18933bb2e98f091add0b1889e70587448d9891f).
The v0.2.1 corpus payload was published at
[commit `7cae908`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/7cae908fee51acd2e1e47955acaa9ee035c9bfbc), with its developer quick-start corrected at
[commit `0a76bc6`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/0a76bc6a1f403b2ba460ef0ece464050c178c189).
The speech companion is live as v0.2.1 at
[Hugging Face commit `9da266e`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/9da266e23bfc198f70784a6e81edbf32f946102f).
The corrected corpus card/manifests are at [commit `a2d8716`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/a2d8716d0dfdc49e5bce440b22312be4b94f9b98); the corrected speech card is at [commit `1a9cf07`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/1a9cf07176bc5a2dc4598dc3e0fa7321b8f982e5), with a split/transcript-count clarification at [commit `2808ad7`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/2808ad7d4c59becbd842f76ed38af1ee06274ba8). The latter states that VAANI split counts refer to all 110,436 audio rows, separately from the 5,894 provider-transcribed rows and strict 2,002-row ASR view. It changes no audio or Parquet payloads. The linked schema, quick-start, license policy, and rights log were aligned to v0.2.1 at corpus commit [`796b5c4`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/796b5c45e6395c1d2559fbbc12cb2f795d0138fc).
Both updates were additive; earlier release files remain available. V0.2.1 adds
a common rights-and-quality schema, chronological dataset cards, a developer
quick start, and a searchable lexicon example.
V0.2.2 added the separate `text_expansion/train` configuration with 1,647
existing catalog texts exposed as a strict-tier, train-only view. This is a
new access path, not newly ingested source material; its values remain in the
catalog by design, and the row-level rights and quality labels still apply.
Its content tables expose 12,606 of 32,072 exact-unique catalog values under
source-specific terms or narrow fact-only treatment. The other 19,466 catalog
records remain listed with source and rights metadata but without the full text
in public content, pending a compatible reuse basis. All 216 structured records
are discoverable through factual/bibliographic projections; their expressive
payloads are not included. The complete all-data package retains every value
locally, but is not uploaded. The v0.2.5 package has **827,450 overlapping-view
rows**: 164,387 content/config rows and 663,063 reference/join rows across 14
content configs and 22 config-split views. Core text splits are 15,981 train,
1,308 source-overlap, 895 validation, and 765 test; all 18,949 values remain.
The 246-row `text_resources` and
1,647-row `text_expansion` views expose existing catalog material; they are
not new source acquisition. None of the public `text`, `text_expansion`, or
`text_resources` rows is currently recommended for training. The source-level
eligibility audit reports zero stored/recomputed gate mismatches and changes no
eligibility labels. Local schema validation loads all 13 JSONL shards across
the two affected configs (1,647 expansion rows and 104,534 draft rows). The
latest Viewer check reports every capability enabled, all 25 splits available, and all 25 Parquet outputs ready with no pending or failed jobs. The row API returns samples from `text_expansion/train` and `sravaani_drafts/train` (1,284 and 104,534 rows). Dataset-wide Viewer validity is confirmed.
The public
reference index covers 302,641 record-index rows, 5,019 source records, and
355,403 source links without copying
text or media that is not included in the public content views. The linked
[`Garhwali Speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
dataset is public separately. Native-speaker review and dialect annotation are
deferred; benchmark and model scores remain automated research results, not
native- or dialect-validated claims. See [`finalreport.md`](finalreport.md)
and [`LICENSE_POLICY.md`](LICENSE_POLICY.md) for decisions and conditions.
The frozen v0.2.0 corpus snapshot remains available in the earlier release
history. V0.2.1 keeps the original Hub storage prefix for stable links; that
folder name records the first upload path, not the project's release number.

## Developer access

Use the [developer quick start](docs/DEVELOPER_QUICKSTART.md) for exact config
counts, a copy-paste `datasets.load_dataset` sample, pandas and DuckDB recipes,
and the searchable vocabulary CLI. The
[schema guide](docs/DATASET_SCHEMA.md) defines common record-level rights and
quality fields alongside each config's payload fields. The v0.2.5 corpus keeps
the common envelope and source-specific evidence fields. The local Internet
Archive intake is separate research material and is not in this Hub release;
see its [intake report](research/internet-archive-intake-2026-10-03.md) and
[quality audit](research/internet-archive-intake-quality-2026-10-04.md).

## Current scale

| Resource | Current release |
| --- | ---: |
| Exact-unique parent texts | 32,072 |
| Exact-unique sentence segments | 151,690 |
| Local all-data text package | 302,641 overlapping-view rows, including all 32,072 full catalog text values; not uploaded |
| Rights-filtered corpus profile | public v0.2.5: 164,387 content/config rows across 14 configs / 22 config-split views, plus 663,063 reference/join rows |
| Total corpus package views | 827,450 overlapping-view rows; not unique examples |
| `text_resources/train` | 246 existing catalog records for lookup/research |
| Local Archive intake (not in Hub package) | 119 payloads / 6.01 GB; 3,369 OCR pages / 3,368 exact-unique texts; 39 media files. Zero exact or ≥0.85 5-gram near-match candidates against 32,072 cleaned parent texts |
| Speech release (public v0.2.1) | 113,363 rows / 267 Parquet shards / 154.645 hours |
| V0.2.1 speech file-tree size | 18.24 GB new release files; earlier files remain available |
| Catalog text in public content | 12,606 values; 19,466 catalog entries expose identifiers and source/rights metadata without full text |
| Structured knowledge | 216 fact/bibliographic projections; expressive payloads omitted |
| Metadata index in v0.2.5 | 302,641 records / 5,019 sources / 355,403 links |
| All supervised speech rows | 5,894 / 8.803724 hours |
| Strict identified-speaker comparison rows | 2,002 / 3.562395 hours |
| Normalized training-candidate WAVs | 1,736 |
| Peak-safe flagged review WAVs | 266 |
| Segmented folktale audio | 1,204 clips / 8.928764 hours |
| Identified speakers in strict speech splits | 248 |
| Untranscribed VAANI rows retained | 104,542 |
| Lexicon/pronunciation candidates | 1,114 |
| Pronunciations with source phonetic segments | 293 |
| Normalized TTS candidate pairs | 1,736 |
| Current SraVaani baseline | 0.428 WER / 0.176 CER |
| Zero-shot Whisper-tiny, same 112 rows | 1.479 WER / 1.368 CER |
| Zero-shot Whisper-small, same 112 rows | 0.972 WER / 0.578 CER |
| SraVaani experimental drafts | 104,542 source rows / 104,534 unique audio hashes: 104,500 non-empty, 34 empty |
| SraVaani draft quality | 103,354 standard / 1,188 flagged |
| Independent Whisper agreement evidence | 65,000 rows / 157 exact agreements |
| Incoming PDF OCR consensus | 659 pages checked / 69 same-engine layout variants |
| GarhwaliBench external task records | 3,847 |
| GarhwaliBench held-out text / ASR | 398 / 112 |
| Character bigram baseline | 17.000058 perplexity / 0 observed character OOV |
| Best multilingual tokenizer | IndicBERTv2 / 1.531569 tokens per word |
| IndicBERTv2 masked-token pilot | 17.786561% accuracy / 506 masks |
| Translation benchmark | 997 development / 1,012 test pairs |
| NLLB Hindi-token proxy pilot | 0.219719 BLEU / 0.574134 chrF2 on 32 rows |
| XORQA retrieval index | 1,059 passages / 1,039 dev/test questions |
| IndicBERTv2 retrieval | 10.389610% Recall@10 on 539 test questions |
| Reversible text-cleanup proposals | 27,987 records / 16,687 with signals |
| IndicBERTv2 cleanup ranking | 4,096 records / 410 high-loss disagreements |
| Controlled text-scaling runs | 36 validation runs / 3 seeds / 6 scales |
| Selected character trigram | 11.893886 frozen-test perplexity |
| IndicBERTv2 head adaptation | 6.678164 → 6.578552 validation cross-entropy |
| IndicBERTv2 encoder LoRA | 6.659330 → 6.014093 frozen-test cross-entropy |
| Longer IndicBERTv2 LoRA | 6.678164 → 5.624498 mean validation cross-entropy |
| Instruction examples | 3,230 total / 2,650 train / 320 validation / 260 test |
| mT5 instruction LoRA | 28.201385 → 27.569880 mean validation cross-entropy |
| mT0-small accuracy LoRA | 5.614353 → 4.961989 mean validation cross-entropy |

The v0.2.1 all-data text view uses connected-document splitting: 144,731
train, 3,520 validation, and 3,439 test records. The public text view contains
17,289 train, 895 validation, and 765 test records. Strict speech uses 1,621
train, 269 validation, and 112 test rows. No normalized text component, exact
text hash, or identified speaker crosses these partitions. GarhwaliBench also
reports zero exact train/evaluation text overlap and zero ASR speaker overlap.

The tokenizer and model results below were run on earlier checksum-addressed
snapshots, including a 2,492-record historical test set. They remain reproducible
research results, but they are not scores on the current 398-record
GarhwaliBench candidate and must not be presented as current release-benchmark
results.

The instruction split inherits document-level parent partitions and has zero
parent, exact instruction-pair, or normalized-prompt crossing. All 3,230 records are active in the
all-data package for experiments. The first mT5 run remains a negative baseline;
the later mT0-small
run improves teacher-forced accuracy on a new 258-record test but still requires
native-reference evaluation before application use.

## Data represented

- VAANI prompted and descriptive Garhwali speech from Uttarkashi and Tehri
  Garhwal, with source speaker, district, gender, and transcript metadata;
- local vocabulary for animals, birds, plants, food, tools, occupations,
  instruments, kinship, agriculture, land, and ritual life;
- idioms, proverbs, folktales, folk-song books, ballads, theatre and cultural
  scholarship;
- historical grammars, word lists, surveys, gazetteers, and public-domain context;
- learning phrases, software localization, community examples, and Romanized or
  mixed-language material retained for review.

Historical English cultural prose and mixed-language sources are not labelled as
Garhwali training text merely because they concern Garhwal.

## Intended uses

The release supports corpus research, language correction, language identification,
tokenizer experiments, ASR/TTS preparation, lexicon building, and evaluation-set
design. Public or production use must select only records allowed by
[`LICENSE_POLICY.md`](LICENSE_POLICY.md) and must retain attribution.

## Sources and licenses

Each record keeps source URL or repository, source identifier, retrieval metadata,
checksum, attribution, license evidence, rights status, and transformation flags.
The corpus contains CC BY, CC BY-SA, CC BY-NC-SA, public-domain, restricted,
rights-pending, and unresolved components. There is therefore no single license
covering the complete all-data package.

The repository code is licensed under MIT in [`LICENSE`](LICENSE). That license
does not apply to the dataset, upstream source material, or all-data package.

VAANI is recorded as CC BY 4.0 in its source metadata. Modern books, podcast
episodes, community pages, social posts, and dataset components whose repository
license does not clear underlying content remain active all-data research inputs
with their rights flags attached.

## Personal and speaker data

Raw VAANI metadata can contain quasi-identifiers. Public exports must omit private
metadata and use only the minimum speaker identifier needed to enforce disjoint
splits. TTS use requires a separate voice-consent decision. The project does not
publish raw caches, reference images, or private reviewer identities.

## Known limitations

- VAANI geography currently covers only Uttarkashi and Tehri Garhwal.
- Most VAANI audio is untranscribed, and 89,413 full-corpus rows use an
  unidentified-speaker placeholder.
- Only 29 text records carry an explicit dialect label.
- Romanized spelling, OCR, Hindi/Garhwali overlap, and mixed-language records carry
  uncertainty flags and may receive later native corrections.
- Historical sources can contain colonial framing, dated terminology, OCR damage,
  and mixed Kumauni/Garhwali/English material.
- Candidate evaluation manifests are automatically screened experimental targets,
  not claimed native ground truth.
- The translation pilot uses NLLB's Hindi language token because NLLB has no
  Garhwali token. Its 32-record result is an engineering baseline, not a final
  Garhwali translation evaluation.
- XORQA supplies no English oracle question for its 539 test rows. The English
  lexical comparator therefore covers dev only, and retrieval scoring credits
  only each row's associated deduplicated passage.
- SraVaani 1.0 is the strongest tested ASR baseline at 42.761% WER / 17.606%
  CER on the 112-row speaker-safe comparison. It remains too inaccurate to turn
  machine drafts into trusted labels without review. The 104,542 source rows
  deduplicate to 104,534 unique audio hashes; 104,500 have non-empty drafts and
  34 are empty. All remain clearly marked as noisy experimental records.
- SraVaani 1.0 lists Garhwali support and a 53.5 WER on its own Vaani evaluation,
  while this project uses a provider-approved pinned snapshot. The published
  result uses a different split and scoring setup and is not directly comparable.
- The 35,864 corpus-neighbor spelling pairs are suggestions, not corrections.
  Bulk substitution lowers character perplexity and token OOV but can erase real
  dialect and spelling forms, so no spelling proposal is promoted automatically.

## Reproduction

Run the preparation commands in [`README.md`](README.md). Machine-generated data
stays under `data/processed/`; the tracked release summary is
[`release/v0.1.1-manifest.json`](release/v0.1.1-manifest.json). The full
test suite, release-index validator, leakage checks, and source-freshness workflow
run in GitHub Actions.

The Hugging Face export builder creates separate text, ASR, SraVaani-draft,
lexicon, and instruction configurations. Its public profile excludes components
whose underlying redistribution evidence is absent or still needs review, while
the complete experimental profile remains available locally.
