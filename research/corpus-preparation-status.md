# Corpus preparation status

Generated 2026-09-10 from the checked-in preparation scripts. Raw and downloaded material remains under gitignore.

## Text

- 30,088 source records from 35 files; 27,987 unique normalized texts / 7,391,666 characters.
- 2,101 duplicate rows retained in 2,003 provenance groups.
- PahariLI's 15,000 records explicitly labeled `gbm` are available in the user-approved candidate view `data/processed/text/paharili_garhwali.jsonl`; the original quarantine snapshot remains unchanged for provenance.
- The final web-learning pass archived 189 phrase or example rows from three eUttaranchal lessons, LanguagesHome, and Omniglot. Exact deduplication contributed 139 new unique texts; all 189 retain source URLs and no-open-license flags in the experimental quarantine layer.
- All 27,987 canonical normalized texts, including quarantine and restricted provenance, are available in the opt-in `data/processed/text/all_garhwali.jsonl` view.
- Conservative cleanup retained all 27,987 texts, removed invisible formatting characters from 821 records, and routed 7,237 records to `data/processed/review/text_cleanup_review.jsonl` without rewriting spelling or dialect forms.
- Sentence-like re-extraction exposes 91,536 occurrences / 86,215 exact-unique segments while retaining every parent and provenance chain. The 332 segments shared by parents in different document splits are explicitly reported; its segment-hash split is provisional until document-aware splitting.
- Deterministic document partitions: train 25,169; validation 1,425; test 1,393.
- Quality signals: 62 low quality; 27,925 review band.

## VAANI Garhwali

- 110,436 WAV rows, 135.509 hours; 5,894 supervised and 104,542 untranscribed.
- Supervised official partitions: train 4,778; validation 666; test 450.
- 13 transcript rows are quarantined (8 Bengali-script rows, with overlapping review flags).
- 110,436/110,436 WAVs are readable, mono, 16 kHz, 16-bit PCM. Three exceed the clipping review threshold.
- The full signal pass now measures RMS, peak, zero share, and DC offset for every WAV. Median RMS is -16.375 dBFS; 856 files are below -40 dBFS, 552 are above -10 dBFS, and 2,718 have absolute DC offset above 0.02.
- A non-destructive normalization manifest covers all 110,436 WAVs. It flags 4,112 files for signal review and 10,967 gain recommendations whose projected peak would exceed -1 dBFS; no source audio was rewritten.
- No supervised speaker appears across partitions.
- Model-ready audio manifests retain all 5,894 supervised and 104,542 untranscribed rows, with quality flags attached rather than excluded.
- Transcript preparation derives 5,894 non-empty ASR targets and divides all 104,542 untranscribed rows into 105 reproducible batches; 13 supervised rows remain in the transcript review queue.
- A second reversible cleanup pass retains all 27,987 text and 5,894 supervised audio-transcript rows. It cleans annotation/markup artifacts and flags 925 text plus 920 audio-transcript rows for truncation, URLs, or script review.
- Whisper-small zero-shot evaluation on 20 validation rows scored 134.3% WER and 94.8% CER, so it is rejected for pseudo-labeling. Fine-tuning exports retain all 4,778/666/450 train/validation/test rows.

## Language quality

- All 27,987 cleaned texts have source-backed language, Unicode-script, genre, explicit-dialect, and geographic-evidence fields.
- Separate views contain 25,343 likely Garhwali candidates, 1,468 declared mixed-language records, 859 unresolved script/language records, and 317 non-Garhwali cultural-context records. The tagged all-data view retains all four groups.
- Language-identity confidence is high for 9,525 texts, medium for 15,818, and low for 2,644. The medium group is dominated by 14,999 PahariLI texts whose Garhwali label is useful but whose component lineage remains missing.
- Every text has a genre; 1,917 exact-duplicate groups carry multiple source genres. Resource views expose 1,124 lexicon candidates, 446 unique English–Garhwali pairs, and 1,187 grammar-source candidates.
- Only 29 text records carry explicit dialect labels. District names are never converted into dialect labels; 10,873 conversational, lexical, or folk records are prioritized for dialect review.
- All 110,436 VAANI recordings carry district, gender, speaker-status, and language-evidence tags. Nine supervised transcripts need language/script review. The untranscribed 104,542 remain medium-confidence source-labelled Garhwali audio until transcription verifies their content.
- VAANI has 363 distinct non-placeholder speaker IDs across 21,023 rows; 89,413 rows use an unidentified speaker placeholder. Geographic coverage is limited to Uttarkashi (74,552) and Tehri Garhwal (35,884).

## Review queues

`data/processed/review/` contains bounded samples: 13 transcript, 3 clipping, 4,112 normalization, 62 low-quality text, and 100 review-band text records.

The current prepared release is indexed by `data/processed/release/manifest.json`; its referenced canonical, experimental, segmented, audio, transcript, and evaluation views exist and their line counts were verified.

## Reproduction

```sh
python3 scripts/prepare_text_corpus.py
python3 scripts/build_all_data_view.py
python3 scripts/clean_text_corpus.py
python3 scripts/deep_cleanup.py
python3 scripts/segment_text_corpus.py
python3 scripts/prepare_vaani_supervised.py
python3 scripts/audit_audio_quality.py --untranscribed data/processed/vaani/untranscribed.jsonl
python3 scripts/prepare_audio_normalization.py
python3 scripts/tag_language_quality.py
python3 scripts/build_review_queues.py
python3 scripts/build_release_manifest.py
```

The complete pipeline suite has 64 passing tests in the project `.venv`, including the LangGraph checkpoint/retry tests and final-audit extractors.
