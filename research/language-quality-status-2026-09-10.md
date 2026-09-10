# Garhwali language-quality status

**Generated:** 2026-09-10  
**Grain:** one exact-unique cleaned text record, or one VAANI utterance/audio file.  
**Intended use:** preserve the complete experimental corpus while giving model preparation explicit language, script, genre, dialect, geography, and speaker boundaries.

## Outcome

The language-quality stage is operational for all **27,987 text records** and **110,436 VAANI audio records**. The master tagged views retain every record. Four text views now separate likely Garhwali candidates, source-declared mixed language, explicit non-Garhwali cultural context, and unresolved records.

| Text language bucket | Records | Share |
| --- | ---: | ---: |
| Likely Garhwali candidate | 25,343 | 90.55% |
| Mixed-language source | 1,468 | 5.25% |
| Script/language review | 859 | 3.07% |
| Non-Garhwali cultural context | 317 | 1.13% |

The buckets control selection; they do not delete records. Romanized Garhwali remains in the likely-Garhwali view with a mandatory spelling-review flag.

## Checks and findings

### Language and script

| Finding | Evidence | Risk | Severity |
| --- | --- | --- | --- |
| Medium-confidence source concentration | 15,818 medium-confidence texts, including 14,999 PahariLI records with missing component lineage | A model may overlearn one noisy or translated source | High |
| Known mixed-language material | 1,468 records declare or flag Garhwali/Hindi/English mixture | Language-model and tokenizer statistics can be biased | High |
| Mixed or unsupported script | 773 Devanagari–Latin, 104 other mixed, 3 Bengali, and 3 unsupported-script records | OCR, markup, transliteration, and wrong-language rows can enter training | Medium |
| Romanized spelling variation | 640 Romanized Garhwali candidates | Orthographic inconsistency can fragment tokens | Medium |
| Explicit English cultural context | 317 records, primarily historical Garhwal reference prose | Useful research context can be mistaken for Garhwali training text | Medium |

Language-identity confidence is **high for 9,525**, **medium for 15,818**, and **low for 2,644** texts. Confidence describes the language label only; it does not replace license, OCR, or factual-quality fields.

The automatic rules use explicit source labels, source quality flags, and Unicode scripts. They deliberately do not classify shared Devanagari vocabulary as Hindi or Garhwali. That distinction needs a validated Garhwali language-identification model or native review.

### Genre and linguistic resources

Every record now has a genre label. Explicit source metadata is used when available, with four narrow fallbacks for older folklore, idiom, social-media, and cultural-reference extractions. There are no unclassified records; 1,917 records have `multi_genre` because identical text occurs in differently described sources.

Generated resource views contain:

- **1,124 lexicon candidates**, retaining English/Hindi/other glosses and semantic domains when present;
- **446 exact-unique English–Garhwali pairs** from phrasebooks, translations, and localization data;
- **1,187 grammar-source candidates** from educational and historical linguistic material.

These are candidates rather than native-reviewed dictionaries or grammatical annotations.

### Dialect and geography

Only **29 text records** contain explicit dialect labels. Another **27,958** are unlabeled. The review queue prioritizes **10,873** speech, folk, phrase, sentence, idiom, social, and lexical records where dialect annotation would be most useful.

District is retained as a geographic hint and never treated as a dialect. This prevents labels such as “Tehri Garhwal” from being silently converted into “Tehriyali.”

### Audio and speakers

| Audio property | Records |
| --- | ---: |
| Supervised transcripts | 5,894 |
| High-confidence Garhwali transcript candidates | 5,885 |
| Transcript language/script review | 9 |
| Source-labelled, untranscribed Garhwali audio | 104,542 |
| Rows with identified speaker ID | 21,023 |
| Rows with unidentified speaker placeholder | 89,413 |
| Unique identified speaker IDs | 363 |

VAANI geography is Uttarkashi **74,552 (67.51%)** and Tehri Garhwal **35,884 (32.49%)**. Gender metadata is Male **67,322 (60.96%)** and Female **43,114 (39.04%)**. These distributions are material coverage limits for ASR or TTS evaluation.

## Review queues

| Queue | Records | Purpose |
| --- | ---: | --- |
| `language_identity_review.jsonl` | 3,284 | Declared mixture, script conflict, explicit non-Garhwali source, or unsupported script |
| `language_confidence_review.jsonl` | 18,462 | Every medium- or low-confidence language label |
| `dialect_review.jsonl` | 10,873 | High-value records lacking explicit dialect |
| `audio_language_review.jsonl` | 9 | Supervised VAANI transcript language/script anomalies |
| `genre_review.jsonl` | 0 | No unresolved genre after fallbacks |

## Reproduction

```sh
.venv/bin/python scripts/prepare_text_corpus.py
.venv/bin/python scripts/prepare_vaani_supervised.py
.venv/bin/python scripts/build_audio_training_manifests.py
.venv/bin/python scripts/prepare_transcripts.py
.venv/bin/python scripts/deep_cleanup.py
.venv/bin/python scripts/tag_language_quality.py
.venv/bin/python scripts/build_release_manifest.py
```

The next quality gain requires native-speaker decisions: confirm the 18,462 non-high-confidence text labels, add dialects to the prioritized 10,873 records, and transcribe enough of the 104,542 unlabelled recordings to validate language identity and broaden supervised coverage.
