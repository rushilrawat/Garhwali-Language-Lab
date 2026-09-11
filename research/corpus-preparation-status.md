# Corpus preparation status

Generated 2026-09-10 from the checked-in preparation scripts. Raw and downloaded material remains under gitignore.

## Text

- 30,088 source records from 35 files; 27,987 unique normalized texts / 7,391,666 characters.
- 2,101 duplicate rows retained in 2,003 provenance groups.
- PahariLI's 15,000 records explicitly labeled `gbm` are active in the complete experimental corpus and in `data/processed/text/paharili_garhwali.jsonl`; source provenance remains unchanged.
- The final web-learning pass archived 189 phrase or example rows from three eUttaranchal lessons, LanguagesHome, and Omniglot. Exact deduplication contributed 139 new unique texts; all 189 are active for local experiments and retain source URLs and no-open-license flags.
- All 27,987 canonical normalized texts, including experimental and restricted provenance, are active in `data/processed/text/all_garhwali.jsonl`.
- Conservative cleanup retained all 27,987 texts, removed invisible formatting characters from 821 records, and routed 7,237 records to `data/processed/review/text_cleanup_review.jsonl` without rewriting spelling or dialect forms.
- Sentence-like re-extraction exposes 91,536 occurrences / 86,215 exact-unique segments while retaining every parent and provenance chain. Connected-component assignment resolves all 332 prior cross-document conflicts; zero exact segment now crosses train, validation and test.
- Deterministic document-aware partitions: train 25,293; validation 1,364; test 1,330. Only 136 documents moved from their original hash split to keep connected documents together.
- Quality signals: 62 low quality; 27,925 review band.

## VAANI Garhwali

- 110,436 WAV rows, 135.509 hours; 5,894 supervised and 104,542 untranscribed.
- Supervised official partitions: train 4,778; validation 666; test 450.
- Thirteen transcript rows retain review flags (including eight Bengali-script rows) but remain present in the complete experimental supervised view.
- 110,436/110,436 WAVs are readable, mono, 16 kHz, 16-bit PCM. Three exceed the clipping review threshold.
- The full signal pass now measures RMS, peak, zero share, and DC offset for every WAV. Median RMS is -16.375 dBFS; 856 files are below -40 dBFS, 552 are above -10 dBFS, and 2,718 have absolute DC offset above 0.02.
- A non-destructive normalization manifest covers all 110,436 WAVs. It flags 4,112 files for signal review and 10,967 gain recommendations whose projected peak would exceed -1 dBFS; no source audio was rewritten.
- The strict ASR/TTS selection has 1,736 unflagged recordings rendered as derived, gain-adjusted, DC-corrected WAVs. Another 266 strict files have peak-safe copies whose projected-clipping, unusual-level, or high-DC flags remain attached; all 2,002 are active experimentally. All original VAANI audio remains unchanged.
- No supervised speaker appears across partitions.
- Model-ready audio manifests retain all 5,894 supervised and 104,542 untranscribed rows, with quality flags attached rather than excluded.
- Transcript preparation derives 5,894 non-empty ASR targets and divides all 104,542 untranscribed rows into 105 reproducible batches; 13 supervised rows remain in the transcript review queue.
- A second reversible cleanup pass retains all 27,987 text and 5,894 supervised audio-transcript rows. It cleans annotation/markup artifacts and flags 925 text plus 920 audio-transcript rows for truncation, URLs, or script review.
- Whisper-small zero-shot evaluation on 20 validation rows scored 134.3% WER and 94.8% CER. A speaker-safe Whisper-tiny fine-tune improved the 112-row strict speaker-disjoint candidate result to 74.3% WER and 40.4% CER after the initial pass plus two lower-learning-rate passes. Because this candidate set informed iteration, it is not the future frozen native benchmark, and the model remains unsafe for automatic pseudo-label promotion.
- A resumable 100-record draft-transcription pilot completed with file-level provenance and uncalibrated token confidence. Median confidence is 0.174; every draft is marked `machine_draft_noisy_experimental` and remains active only in the noisy experimental view.

## Long-form folklore audio

- All 66 locally archived Garhwali Folktales podcast episodes were segmented with silence-aware, 29.5-second target boundaries into 1,204 mono 16 kHz PCM WAV clips covering 8.928764 hours.
- Each clip retains episode GUID, title, source URL and hash, time bounds, derived hash, and rights status. All clips are active for local experiments; creator copyright keeps them outside public redistribution.

## Language quality

- All 27,987 cleaned texts have source-backed language, Unicode-script, genre, explicit-dialect, and geographic-evidence fields.
- Separate views contain 25,343 likely Garhwali candidates, 1,468 declared mixed-language records, 859 unresolved script/language records, and 317 non-Garhwali cultural-context records. The tagged all-data view retains all four groups.
- Language-identity confidence is high for 9,525 texts, medium for 15,818, and low for 2,644. The medium group is dominated by 14,999 PahariLI texts whose Garhwali label is useful but whose component lineage remains missing.
- Every text has a genre; 1,917 exact-duplicate groups carry multiple source genres. Resource views expose 1,124 lexicon candidates, 446 unique English–Garhwali pairs, and 1,187 grammar-source candidates.
- Train-only language resources include a 332-symbol Unicode character tokenizer, 203,706 observed word types, 1,124 pronunciation candidates (293 with source phonetic evidence), and 1,736 normalized TTS candidate pairs.
- Only 29 text records carry explicit dialect labels. District names are never converted into dialect labels; 10,873 conversational, lexical, or folk records are prioritized for dialect review.
- All 110,436 VAANI recordings carry district, gender, speaker-status, and language-evidence tags. Nine supervised transcripts need language/script review. The untranscribed 104,542 remain medium-confidence source-labelled Garhwali audio until transcription verifies their content.
- VAANI has 363 distinct non-placeholder speaker IDs across 21,023 rows; 89,413 rows use an unidentified speaker placeholder. Geographic coverage is limited to Uttarkashi (74,552) and Tehri Garhwal (35,884).

## Review queues

`data/processed/review/` contains bounded samples: 13 source transcript, 3 clipping, 4,112 normalization, 62 low-quality text, and 100 review-band text records. The unified two-pass native-review workflow additionally exposes 10,873 dialect, 2,492 evaluation-text, 112 evaluation-ASR, 3,284 language-identity, 1,124 lexicon, 892 OCR, and 113 transcript packets. It has received zero human decisions so far.

Adjudication requires matching decisions from two distinct reviewers. Accepted and corrected decisions are materialized beside their immutable source payloads; originals are never overwritten.

The current prepared release is indexed by `data/processed/release/manifest.json`; its referenced canonical, experimental, segmented, audio, transcript, and evaluation views exist and their line counts were verified.

GarhwaliBench v0.1 indexes 3,847 external task records, 2,492 held-out text segments, and 112 speaker-safe ASR rows. Exact train/evaluation text overlap and ASR speaker overlap are zero. Its deterministic character-bigram floor is 16.464093 perplexity with a 0.00000498 character OOV rate.

## Dataset splits

- Document-aware text partitions contain 80,926 train, 2,488 validation, and 2,801 test segments. Exact segment hashes do not cross partitions.
- Strict ASR and TTS candidate partitions retain 2,002 clean transcript/audio rows from 248 identified speakers: 1,621 train, 269 validation, and 112 test. No identified speaker crosses a partition.
- The broader 5,894-row supervised ASR export remains available. The strict view excludes 3,886 placeholder-speaker rows and six transcript/language-review rows rather than deleting them.
- Candidate evaluation manifests contain 2,492 unflagged test text segments and 112 strict test audio rows. They are checksum-addressed, automatically screened, and active for experimental evaluation; later native corrections remain optional versioned improvements.
- Reproduce these outputs with `python3 scripts/build_dataset_splits.py`. The release manifest records every split artifact, row count, and SHA-256 digest.

## Reproduction

The scheduled freshness audit currently covers 43 catalogued public URLs: 41
responded successfully, translatewiki rejected the automated audit with HTTP 403,
and the Central Hindi Directorate PDF timed out while remaining catalogued. These
access outcomes do not change the stored source evidence.

```sh
python3 scripts/prepare_text_corpus.py
python3 scripts/build_all_data_view.py
python3 scripts/clean_text_corpus.py
python3 scripts/deep_cleanup.py
python3 scripts/segment_text_corpus.py
python3 scripts/prepare_vaani_supervised.py
python3 scripts/audit_audio_quality.py --untranscribed data/processed/vaani/untranscribed.jsonl
python3 scripts/prepare_audio_normalization.py
python3 scripts/render_normalized_audio.py --render-flagged-review
python3 scripts/tag_language_quality.py
python3 scripts/build_dataset_splits.py
python3 scripts/build_language_resources.py
python3 scripts/build_garhwali_benchmark.py
python3 scripts/build_review_queues.py
python3 scripts/native_review_workflow.py
python3 scripts/segment_long_audio.py
python3 scripts/build_release_manifest.py
```

The complete pipeline suite has 119 passing tests in the project `.venv`, including LangGraph checkpoint/retry behavior, final-audit extractors, language-quality tagging, document-aware split invariants, benchmark contamination checks, training and review audio rendering, long-form segmentation, native-review materialization, ASR draft resumption, source freshness, and release validation.
