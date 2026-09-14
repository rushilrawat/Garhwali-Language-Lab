# Corpus preparation status

Updated 2026-09-12 from the checked-in preparation scripts. Raw and downloaded material remains under gitignore.

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
- A fair five-checkpoint comparison uses the same 112 speaker-safe test rows and normalization. Zero-shot Whisper-tiny scores 147.939% WER / 136.810% CER; zero-shot Whisper-small scores 97.172% / 57.822%; the two local tiny fine-tunes reach 79.051% / 42.907% and 74.305% / 40.440%. Provider-approved SraVaani 1.0 is strongest at 42.761% WER / 17.606% CER, a 42.45% relative WER reduction from the best local Whisper checkpoint.
- The resumable SraVaani path completed all 104,542 untranscribed source rows, covering 104,534 unique audio hashes with zero missing or unexpected hashes. Eight duplicate hashes are inherited from distinct VAANI source filenames and produce identical drafts. Thirty-four drafts are empty; every source row remains active experimental data with model revision and machine-draft status.

## Model-assisted text cleanup

- All 27,987 parent texts now have immutable original/current fields in a reversible cleanup-proposal manifest; zero records are excluded.
- Pinned IndicBERTv2 scored 4,096 OCR-, language-, spelling-, and dialect-priority records over 81,116 deterministic masked tokens. The 90th-percentile loss threshold identifies 410 model/source disagreements for inspection without changing source labels.
- Train-only corpus frequencies produced 35,864 low-confidence one-edit spelling pairs across 10,200 records. These remain suggestions because frequent neighbors can be semantically wrong or valid competing dialect forms.
- The fixed document-split ablation compared 25,169 train and 1,393 test parent texts. Mechanical cleanup changed 108 records and moved character-bigram perplexity from 16.88499549 to 16.88726214, so it was not promoted.
- Bulk spelling substitution changed 10,244 records, lowered perplexity to 16.76707705, and lowered test token OOV from 0.06995491 to 0.06016912. It was still not promoted because the aggregate metric cannot establish semantic or dialect correctness.

## Controlled modeling

- The first data-scaling control evaluates character bigrams and trigrams at 1%, 5%, 10%, 25%, 50%, and 100% of the 80,926-row training split with seeds 17, 29, and 43: 36 validation runs in total.
- Model selection uses only the 2,488-row validation split. Full-data trigrams win with 11.712997 mean validation perplexity; the frozen 2,492-row test candidate is untouched until this selection is fixed.
- The selected full-data trigram reaches 11.893886 frozen-test perplexity, 27.76% below the earlier 16.464093 bigram floor. Seed variance is zero at full data because each seed contains the identical complete training set.
- Exact train/validation and train/test text overlap are both zero. The scaling curve continues to improve from 50% to 100%, supporting continued collection and controlled transfer experiments.
- A three-seed IndicBERTv2 transfer pilot freezes the 277.5M-parameter encoder and trains only 842,128 MLM-head parameters for 64 train-only steps per seed. All three seeds improve the same 128-record validation subset.
- Mean masked-token validation cross-entropy falls from 6.678164 to 6.578552 (standard deviation 0.014935), while accuracy moves from 21.747212% to 21.933086%. The result advances to encoder adaptation; the frozen test candidate remains unused.
- Rank-4 LoRA on all IndicBERTv2 attention query/value projections trains 147,456 parameters for 256 steps per seed. Validation loss falls to a 6.062648 mean across all three seeds, 0.615516 below the unadapted checkpoint.
- With configuration fixed, a checksum-addressed 256-record frozen-test subset and 1,037 common masked tokens compare the base, head-only, and encoder-LoRA families. Base loss is 6.659330, head-only mean loss is 6.537236, and LoRA mean loss is 6.014093 with 0.008828 standard deviation. Exact train/test overlap is zero and this test result is closed to further tuning.
- A longer 1,024-step IndicBERTv2 LoRA continuation draws an 8,192-record pool per seed from the full training partition. All three seeds improve validation loss; the 5.624498 mean is 7.23% below the earlier 256-step LoRA mean. The closed transfer test remains untouched.
- Existing parallel and lexicon evidence yields 2,518 active instruction records: 2,304 train, 130 validation, and 84 test. Parent-document and exact instruction-pair crossing are both zero, and provenance and rights fields remain attached.
- Three 64-step mT5-small LoRA seeds all improve validation loss from 28.201385 to a 27.569880 mean. The validation-selected seed 29 scores 29.059347 test cross-entropy versus the base model's 30.416287, but generation remains at 0% exact match and 0.0 chrF2 after sentinel-token removal, so this adapter is not promoted.
- A new v0.2 instruction test was frozen from 258 parent records unseen by the earlier pilot; the old 84-record test was not reused. Zero-shot mT0-small scores 5.614353 validation cross-entropy, and three 256-step LoRA seeds reach a 4.961989 mean and 5.019603 mean on the new test. All seeds improve teacher-forced loss; exact match remains 0%, so native-reference scoring and a longer curriculum remain open.

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

A bounded stage-1 ASR curriculum pilot trained on 32 human references and 2,048
standard SraVaani machine labels for 2,080 updates. On the same 269 human-only
validation records as stage 0, WER increased from 0.780522 to 0.784137 and CER
increased from 0.462980 to 0.463038. The configuration is rejected, no machine
labels are promoted, and curriculum stage 2 remains locked.

GarhwaliBench v0.1 indexes 3,847 external task records, 2,492 held-out text segments, and 112 speaker-safe ASR rows. Exact train/evaluation text overlap and ASR speaker overlap are zero. Its deterministic character-bigram floor is 16.464093 perplexity with a 0.00000498 character OOV rate.

The multilingual audit compares five pinned tokenizers on all 2,492 held-out texts. IndicBERTv2 has the lowest fertility at 1.531569 tokens per whitespace word. Its first 128-record masked-language pilot scores 17.786561% masked-token accuracy and 6.977486 cross-entropy over 506 deterministic masks, with zero truncation.

The Garhwali-to-English translation audit covers 997 IndicGenBench FLORES development pairs and all 1,012 test pairs. The deterministic translation-memory floor scores 0.008208 smoothed BLEU / 0.215886 chrF2. On the same fixed 32-record pilot, pinned NLLB-200 distilled with an explicit Hindi source-token proxy scores 0.219719 / 0.574134, while the community Garhwali LoRA adapter scores 0.095460 / 0.460474. The base model is retained as the current pilot because the adapter underperforms and publishes no Garhwali language-token mapping.

The XORQA retrieval audit deduplicates 1,139 source rows into 1,059 passages and evaluates 500 dev plus 539 test questions. On the full test split, word BM25 reaches 1.669759% Recall@10, character BM25 reaches 2.411874%, and zero-shot mean-pooled IndicBERTv2 reaches 10.389610% with 2.226345% Recall@1. English oracle BM25 reaches 85.2% Recall@10 on the 500 dev rows where the upstream benchmark supplies oracle questions; all 539 test oracle questions are empty and are explicitly excluded from that comparator.

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
PYTHONPATH=.cache/asr-runtime python3 scripts/audit_multilingual_tokenizers.py
PYTHONPATH=.cache/asr-runtime python3 scripts/run_masked_lm_baseline.py
python3 scripts/run_translation_baseline.py
PYTHONPATH=.cache/asr-runtime python3 scripts/run_nllb_translation_baseline.py --max-records 32 --max-new-tokens 64 --device cpu
python3 scripts/run_retrieval_baseline.py
PYTHONPATH=.cache/asr-runtime python3 scripts/run_indicbert_retrieval_baseline.py --max-records 0 --device cpu
PYTHONPATH=.cache/asr-runtime python3 scripts/run_whisper_comparison.py --device cpu
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_sravaani_comparison.py --device cpu --batch-size 4
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/transcribe_sravaani_drafts.py --device cpu --batch-size 4 --max-records 100
python3 scripts/build_instruction_dataset.py
python3 scripts/build_instruction_accuracy_split.py
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_indicbert_lora_adaptation.py --device cpu --steps 1024 --training-records 8192 --output data/processed/evaluation/controlled_modeling/indicbert_lora_long.json --checkpoint-dir models/controlled_modeling/indicbert_lora_v0.2
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_mt5_instruction_tuning.py --device cpu --steps 64 --training-records 2304
PYTHONPATH=.cache/asr-runtime:scripts python3 scripts/run_mt5_instruction_tuning.py --device cpu --data-dir data/processed/model_ready/instructions_v0.2 --output-dir data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2 --checkpoint-dir models/controlled_modeling/mt0_instruction_v0.2 --steps 256 --training-records 2046 --model-path .cache/huggingface/hub/models--bigscience--mt0-small/snapshots/8116a34237e19160ec003147e758f065876d95f0 --model-id bigscience/mt0-small --revision 8116a34237e19160ec003147e758f065876d95f0 --run-id garhwali-mt0-instruction-lora-v0.2
python3 scripts/build_review_queues.py
python3 scripts/native_review_workflow.py
python3 scripts/segment_long_audio.py
python3 scripts/build_release_manifest.py
```

The complete pipeline suite has 231 passing tests in the project `.venv`, including LangGraph checkpoint/retry behavior, final-audit extractors, language-quality tagging, reversible cleanup proposals and ablation, controlled multi-seed text scaling, IndicBERTv2 head/encoder adaptation, instruction construction and mT5 tuning utilities, frozen transfer comparison, document-aware split invariants, benchmark contamination checks, tokenizer, masked-language, translation, retrieval, speech comparison, confidence-aware curriculum selection, bounded pilot registration, training and review audio rendering, long-form segmentation, native-review materialization, ASR draft resumption, source freshness, and release validation.
