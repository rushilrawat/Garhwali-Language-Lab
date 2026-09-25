# Dataset card: Garhwali Language Lab

## Summary

Garhwali Language Lab is a provenance-preserving collection and preparation
pipeline for Garhwali (`gbm`). It joins speech, transcripts, vocabulary, idioms,
folklore, folk songs, educational material, historical linguistics, community
writing, and cultural context without erasing source rights or uncertain language
labels.

The current package snapshot uses release ID
`garhwali-language-lab-v0.1.1`; annotated tag v0.1.1 resolves to the reviewed
commit and the historical v0.1.0 tag remains unchanged. The public profile includes records
with an explicit compatible rights basis and excludes 216 structured reference
records whose rights remain unassessed or incompatible. Those records remain
intact in the all-data package. Native-speaker review and dialect annotation are
deferred; benchmark and model scores are automated research results, not native-
or dialect-validated claims. See [`finalreport.md`](finalreport.md) for the
release decision and audit scope. Current Hugging Face publication is split
between [`Garhwali Speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech),
which is public, and [`Garhwali Corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus),
which is owner-private because the current text profile contains redacted
catalog entries and excludes 216 structured records without compatible public
rights evidence. The text repository will remain private until the release can
meet the project's no-redactions requirement without misrepresenting reuse
rights.

## Current scale

| Resource | Current release |
| --- | ---: |
| Exact-unique parent texts | 28,755 |
| Sentence segments | 114,064 |
| All-data package | 257,807 rows / 0 redacted texts |
| Rights-filtered public profile | 146,684 rows / 12 configurations |
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
| SraVaani experimental drafts | 104,542 source rows / 104,534 unique audio |
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

The complete all-data text view uses connected-document splitting: 106,915
train, 3,063 validation, and 4,086 test records. The public text view contains
8,043 train, 401 validation, and 422 test records. Strict speech uses 1,621
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
  machine drafts into trusted labels without review. All 104,542 untranscribed
  source rows have revision-pinned SraVaani drafts, covering 104,534 unique audio
  hashes; all remain active as noisy experimental records.
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
