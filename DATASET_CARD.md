# Dataset card: Garhwali Language Lab

## Summary

Garhwali Language Lab is a provenance-preserving collection and preparation
pipeline for Garhwali (`gbm`). It joins speech, transcripts, vocabulary, idioms,
folklore, folk songs, educational material, historical linguistics, community
writing, and cultural context without erasing source rights or uncertain language
labels.

The current release is `garhwali-language-lab-v0.1.0-candidate.1`. It is an
internal candidate pending two-pass native review, final source-rights decisions,
and a held-out evaluation freeze.

## Current scale

| Resource | Current candidate |
| --- | ---: |
| Exact-unique parent texts | 27,987 |
| Sentence segments | 86,215 |
| Strict identified-speaker speech rows | 2,002 / 3.562395 hours |
| Normalized training-candidate WAVs | 1,736 |
| Peak-safe flagged review WAVs | 266 |
| Segmented folktale audio | 1,204 clips / 8.928764 hours |
| Identified speakers in strict speech splits | 248 |
| Untranscribed VAANI rows retained | 104,542 |
| Lexicon/pronunciation candidates | 1,124 |
| Pronunciations with source phonetic segments | 293 |
| Normalized TTS candidate pairs | 1,736 |
| Current Whisper-tiny baseline | 0.743 WER / 0.404 CER |
| Review-only machine transcript pilot | 100 rows / 0 training-eligible |

Text segments use connected-document splitting: 80,926 train, 2,488 validation,
and 2,801 test. Strict speech uses 1,621 train, 269 validation, and 112 test rows.
No exact text hash or identified speaker crosses these partitions.

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

The candidate supports corpus research, native review, language identification,
tokenizer experiments, ASR/TTS preparation, lexicon building, and evaluation-set
design. Public or production use must select only records allowed by
[`LICENSE_POLICY.md`](LICENSE_POLICY.md) and must retain attribution.

## Sources and licenses

Each record keeps source URL or repository, source identifier, retrieval metadata,
checksum, attribution, license evidence, rights status, and transformation flags.
The corpus contains CC BY, CC BY-SA, CC BY-NC-SA, public-domain, restricted,
rights-pending, and unresolved components. There is therefore no single license
covering the complete local corpus.

VAANI is recorded as CC BY 4.0 in its source metadata. Modern books, podcast
episodes, community pages, social posts, and dataset components whose repository
license does not clear underlying content remain restricted or quarantined.

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
- Romanized spelling, OCR, Hindi/Garhwali overlap, and mixed-language records need
  native review.
- Historical sources can contain colonial framing, dated terminology, OCR damage,
  and mixed Kumauni/Garhwali/English material.
- Candidate evaluation manifests are stable review targets, not accepted ground
  truth.
- The current fine-tuned ASR baseline improves substantially over zero-shot
  Whisper but remains too inaccurate to promote machine drafts as transcripts.

## Reproduction

Run the preparation commands in [`README.md`](README.md). Machine-generated data
stays under `data/processed/`; the tracked release summary is
[`release/candidate-manifest.json`](release/candidate-manifest.json). The full
test suite, release-index validator, leakage checks, and source-freshness workflow
run in GitHub Actions.
