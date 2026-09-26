# Corpus preparation status

Updated 2026-09-24. This is a chronological preparation log: model-result paragraphs retain the exact dataset snapshot used by each experiment and are not automatically current-release metrics. The current counts, release blockers, and authoritative review status are in [`finalreport.md`](../finalreport.md). Raw and downloaded material remains under gitignore.

## Hugging Face publication

- [`Garhwali Speech`](https://huggingface.co/datasets/rushilrawat/garhwali-speech) is public with separate VAANI and Meta Omnilingual configs: 110,436 VAANI rows / 135.510 hours and 2,927 Meta rows / 19.136 hours. The combined release is 113,363 rows / 154.646 hours. Commit `914eb221b6f58f88d85a8d5dd826acac827ee1c4` adds 50 Meta Parquet shards; all remote sizes and SHA-256 hashes match the local manifests.
- [`Garhwali Corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus) is owner-private. The public-profile export contains redacted catalog values and excludes 216 structured records without compatible redistribution evidence; it does not meet the project's no-redactions release requirement.
- The complete local all-data corpus remains unchanged. No paid Hugging Face compute job or storage purchase was used for these uploads.
- The speech release omits raw filenames, reference images, speaker IDs, stay-duration, and fine-grained location fields. It retains source CC BY 4.0 attribution and split metadata; transcripts remain unreviewed references or model hypotheses. The first post-upload Dataset Viewer check returned a temporary HTTP 500 while indexing; a later retry succeeded for splits, validity, Parquet listing, and a Meta validation preview. Both configs expose train/validation/test splits, and the validity endpoint reports preview, viewer, search, filter, and statistics enabled.
- The candidate-source overlap audit and exact duplicate decisions are in [`huggingface-release-overlap-audit-2026-09-24.md`](huggingface-release-overlap-audit-2026-09-24.md). Card-only Hub commit `b64f0c4b914296c979947cf551ec976a0342d8af` now tells users to filter split-safety fields: all 2,927 rows remain published, while 2,857 pass both leakage-safety flags.

## Text

- 31,094 source records from 42 files; 28,755 unique normalized texts / 9,145,955 characters.
- 2,123 duplicate rows retained in 2,022 provenance groups.
- PahariLI's 15,000 records explicitly labeled `gbm` are active in the complete experimental corpus and in `data/processed/text/paharili_garhwali.jsonl`; source provenance remains unchanged.
- The final web-learning pass archived 189 phrase or example rows from three eUttaranchal lessons, LanguagesHome, and Omniglot. Exact deduplication contributed 139 new unique texts; all 189 are active for local experiments and retain source URLs and no-open-license flags.
- All 28,755 canonical normalized texts, including experimental and restricted provenance, are active in `data/processed/text/all_garhwali.jsonl`.
- Conservative cleanup retained all 28,755 texts without rewriting spelling or dialect forms.
- Sentence-like re-extraction exposes 119,679 occurrences / 114,064 exact-unique segments while retaining every parent and provenance chain. Connected-component assignment leaves zero exact segment crossing train, validation and test.
- Deterministic document-aware parent partitions: train 25,862; validation 1,452; test 1,441. Connected-component assignment keeps related documents together.
- Quality signals: 71 low quality; 28,684 review band.
- Seven incoming PDFs were hash-checked. Six unique books yielded 769 active page records and 1,774,697 characters; the seventh exactly matches the already ingested 370-record *Gadwali LokGeet* scan. The new pages contribute 27,926 Hugging Face text segment identities with full book, page, hash, OCR, rights, and quality provenance. Seven neighboring JSON records now preserve verified title-page and catalog bibliography, including roles, editions, publication dates and places, publishers, identifiers, extent, subjects, source links, duplicate relationships, and rights evidence.
- Structured Wiktionary extraction now yields 77 Garhwali lemmas, alternative forms, and examples in place of 56 flattened raw page blobs. Conservative wikitext rendering removes page scaffolding while preserving source prose.
- Source-aware treatment preserves 392 scholarly Garhwali transcriptions in their published notation. The public accuracy queue fell from 628 to 176; none of these source-grounded resolutions is described as native review.
- The full four-layout OCR sweep covered all 659 incoming machine-OCR pages. It retained 69 same-engine layout-consensus variants beside the original OCR, source hash, confidence, and layout evidence. These are machine proposals rather than validated corrections. Rebuilding after the variants reduced derived segment identities by 18 through deduplication without deleting any parent source record.

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
- A second reversible cleanup pass retains all 28,755 text and 5,894 supervised audio-transcript rows. It cleans annotation/markup artifacts and flags 928 text plus 920 audio-transcript rows for truncation, URLs, or script review.
- Whisper-small zero-shot evaluation on 20 validation rows scored 134.3% WER and 94.8% CER. A speaker-safe Whisper-tiny fine-tune improved the 112-row strict speaker-disjoint candidate result to 74.3% WER and 40.4% CER after the initial pass plus two lower-learning-rate passes. Because this candidate set informed iteration, it is not the future frozen native benchmark, and the model remains unsafe for automatic pseudo-label promotion.
- A resumable 100-record draft-transcription pilot completed with file-level provenance and uncalibrated token confidence. Median confidence is 0.174; every draft is marked `machine_draft_noisy_experimental` and remains active only in the noisy experimental view.
- A fair five-checkpoint comparison uses the same 112 speaker-safe test rows and normalization. Zero-shot Whisper-tiny scores 147.939% WER / 136.810% CER; zero-shot Whisper-small scores 97.172% / 57.822%; the two local tiny fine-tunes reach 79.051% / 42.907% and 74.305% / 40.440%. Provider-approved SraVaani 1.0 is strongest at 42.761% WER / 17.606% CER, a 42.45% relative WER reduction from the best local Whisper checkpoint.
- The human-reference SraVaani decoder/joint adaptation completed 102 steps on 1,621 training clips and was evaluated once on the same frozen 112-record test. It scores 43.528% WER / 17.452% CER: 16 more word errors but 11 fewer character errors than base SraVaani. Because primary WER worsened, the adapted checkpoint remains experimental and base SraVaani stays preferred.
- A refined validation-first sweep completed all 61 decoder/joint trials without failure. Its selected `5e-5`, two-epoch, seed-17 checkpoint improves validation WER from 43.454% to 42.711%, but frozen-test WER worsens from base SraVaani's 42.761% to 43.528%; it is not promoted. The next experimental package contains 5,513 human-transcribed training clips / 8.112 hours with zero fixed validation/test hash overlap and zero identified-speaker overlap; 3,886 training rows retain incomplete speaker identity.
- Expanded human-reference SraVaani training completed 346 steps on all 5,513 eligible clips. Validation WER improves to 42.209%, but frozen-test WER is 43.289% versus base SraVaani's 42.761%; the experimental checkpoint is retained and the base model remains preferred.
- The resumable SraVaani path completed all 104,542 untranscribed source rows, covering 104,534 unique audio hashes with zero missing or unexpected hashes. Eight duplicate hashes are inherited from distinct VAANI source filenames and produce identical drafts. Thirty-four drafts are empty. All rows remain preserved; 98 source-label-conflict drafts are active for source analysis but excluded from Garhwali training.
- Independent Whisper-large-v3-turbo evidence covers 65,000 unique SraVaani drafts, including 157 exact transcript agreements. This evidence is attached without replacing any SraVaani transcript. A later 15,000-row batch job (`6aac7f02b1dc2b62dc58fb5c`) is marked `CANCELED`; its last log reports 13,840/15,000 processed, but the local batch directory has no predictions or report, so those rows are not included in the integrated evidence. Hugging Face reported no cancellation reason, and the log contains no rate-limit error; the cause is unconfirmed. There are currently no running or scheduled Hugging Face jobs.
- A second local Whisper checkpoint now supplies a third hypothesis and uncalibrated acoustic score for every one of the 1,188 recovery recordings. The resulting 1,090-record Garhwali review layer has 325 clean related-checkpoint consensus proposals, 730 clean low-consensus proposals, and 35 structurally unresolved proposals. It preserves every source value and makes no human-reference or training promotion.
- The 35 structural outliers now carry waveform activity, deterministic Whisper `v0.2` re-decoding, and score percentiles calibrated on 112 human-referenced clips. All re-decodes match exactly. The score-to-CER correlations are only -0.164 for `v0.1` and -0.232 for `v0.2`, so these rows remain pending listening review and outside recommended machine-label training.

## Model-assisted text cleanup

The rebuilt complete package contains 257,807 rows and the rights-filtered public profile contains 146,684 rows. The public package excludes 216 structured records with unassessed or incompatible rights; the all-data package retains them. Both package validations pass with zero strict cross-split identity overlap, zero normalized instruction-prompt overlap, 81 distinct provenance sources in all-data, traceable source locators on every structured record, and no deleted or mutated source records. Native-speaker review and dialect annotation are deferred; this release is labeled an automated candidate.

- The original model-assisted cleanup run covered 27,987 parent texts before the source-grounded re-extraction. Its immutable proposal artifact remains a historical model snapshot; the current canonical corpus contains 28,755 texts.
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
- The L4 continuation extends this to 4,096 steps per seed over the complete 106,804-record training pool. All three seeds improve the 128-record validation subset; mean cross-entropy is 5.089108 versus 6.395484 for the current unadapted baseline, and mean masked-token accuracy is 28.2866% versus 24.2991%. The fixed test remains unopened.
- Existing parallel and lexicon evidence yields 2,518 active instruction records: 2,304 train, 130 validation, and 84 test. Parent-document and exact instruction-pair crossing are both zero, and provenance and rights fields remain attached.
- Three 64-step mT5-small LoRA seeds all improve validation loss from 28.201385 to a 27.569880 mean. The validation-selected seed 29 scores 29.059347 test cross-entropy versus the base model's 30.416287, but generation remains at 0% exact match and 0.0 chrF2 after sentinel-token removal, so this adapter is not promoted.
- A new v0.2 instruction test was frozen from 258 parent records unseen by the earlier pilot; the old 84-record test was not reused. Zero-shot mT0-small scores 5.614353 validation cross-entropy, and three 256-step LoRA seeds reach a 4.961989 mean and 5.019603 mean on the new test. All seeds improve teacher-forced loss; exact match remains 0%, so native-reference scoring and a longer curriculum remain open.
- The final 16,384-step mT0 continuation lowers best validation cross-entropy from 4.476975 at 8,192 steps to 4.315077. Seed 43 reaches 2.3077% exact match and 0.073709 chrF2, but adapted chrF2 remains below the zero-shot base; the fixed test remains unopened.
- **Superseded partial-run note:** all three 32,768-step mT0 seeds later completed. The seed-43 validation loss is 4.188287; cross-seed and per-task generation analysis completed, and the validation-selected seed-43 checkpoint was evaluated once on the separate 86-row test. It reached 4.358291 test cross-entropy and 2.33% exact match, while chrF2 (0.062177) remained below the base model (0.085840). The test was not used for selection.
- Cross-encoder refinement of all 29,903 semantic candidates identified 267 high-confidence and 1,357 supported near-duplicate pairs, 14,257 likely false positives, and 14,022 review-required pairs. The original split report had 92 supported cross-split pairs. **Superseded:** the rebuilt split manifest uses 1,623 supported semantic edges, reassigns 120 records, and reports zero supported-semantic cross-split overlap; source texts remain unchanged.

## Long-form folklore audio

- All 66 locally archived Garhwali Folktales podcast episodes were segmented with silence-aware, 29.5-second target boundaries into 1,204 mono 16 kHz PCM WAV clips covering 8.928764 hours.
- Each clip retains episode GUID, title, source URL and hash, time bounds, derived hash, and rights status. All clips are active for local experiments; creator copyright keeps them outside public redistribution.

## Popular music discovery

- The tracked catalog [`garhwali-popular-song-catalog.json`](garhwali-popular-song-catalog.json)
  contains 30 Garhwali song metadata records, with 16 added in the second pass;
  21 records include Narendra Singh Negi and the set also covers Jeet Singh Negi,
  Chander Singh Rahi, Gajender Rana, Preetam Bhartwan, Meena Rana, and traditional
  performers.
- Five records point to lyric pages and three point to meaning or translation
  discussions. Six linked YouTube recordings were checked for public timed text;
  none exposed a caption track on 2026-09-15. No audio, full modern lyrics, or
  third-party translation bodies were copied.
- The generated metadata view is reproducible with
  `PYTHONPATH=scripts .venv/bin/python scripts/ingest_popular_songs.py`; its
  ignored JSONL/report are source-review inputs for a future permissioned
  transcription pass.

## Literary works and geography

- Poetry and theatre are already present through the UOU CGL/MAHL study units,
  Govind Chatak's *Gadwali Lokgeet* pages, and bibliographic records for Tara Dutt
  Gairola, Chander Singh Rahi, and Jeet Singh Negi. The named poems, plays, and
  radio-geet-natika works are inventoried in
  [`garhwali-poetry-plays-inventory-2026-09-15.md`](garhwali-poetry-plays-inventory-2026-09-15.md);
  complete modern editions remain rights-sensitive.
- [`garhwali-literary-works-catalog.json`](garhwali-literary-works-catalog.json)
  includes every named work in the user-supplied Itihaas history plus the later
  writers list: 66 records spanning early manuscripts, religious translations, survey texts,
  poetry, drama, prose, satire, periodicals, and digital language resources.
  Three named oral genres are retained separately. The only two unresolved
  mentions are an untitled Pineflix short film and an untitled government
  dictionary; both are explicit in the coverage audit rather than silently
  dropped. Run `PYTHONPATH=scripts .venv/bin/python
  scripts/ingest_literary_works.py` to reproduce the ignored JSONL and report.
- [`garhwali-literary-people-catalog.json`](garhwali-literary-people-catalog.json)
  preserves 26 named writers, historians, translators, poets, and playwrights.
  Three uncertain names and the Harish/Gireesh Juyal `Khigtaat` attribution
  conflict remain explicit.
- [`garhwali-university-research-catalog.json`](garhwali-university-research-catalog.json)
  contains eight deduplicated records from seven institutions. The Hugging Face
  packages expose this catalog together with geography, history, works, people,
  and songs as six first-class configurations totaling 216 records.
- The geography catalog
  [`garhwali-geography-catalog.json`](garhwali-geography-catalog.json) adds 50
  place and feature records across all seven Garhwal districts: 36 settlements
  and 14 rivers, peaks, parks, protected areas, reservoirs, and pilgrimage sites.
  Each record keeps Hindi naming, place type, district relationship, Wikipedia
  and OpenStreetMap pointers, and a clear separation between geography and
  dialect labels. Coordinates are left unset until an authoritative gazetteer
  export is added.

## Historical terms

- [`garhwali-historical-terms.json`](garhwali-historical-terms.json) contains 36
  unique terms across 25 categories: historical region names, kingdoms and
  capitals, dynasties and rulers, administrative and labour institutions,
  political events and movements, military history, and living ritual/media
  traditions.
- The materialized view is generated with
  `PYTHONPATH=scripts python3 scripts/ingest_historical_terms.py` and writes
  `data/extracted/historical_terms/records.jsonl` plus `report.json`.
- Every row retains Hindi form, period, variants, context, and source references.
  Context is an original research summary; no source passage is copied into this
  metadata layer, and historical references are never treated as dialect labels.

## Language quality

- All 28,755 cleaned texts have source-backed language, Unicode-script, genre, explicit-dialect, and geographic-evidence fields.
- Separate views contain 25,341 likely Garhwali candidates, 2,237 mixed-language records, 860 unresolved script/language records, and 317 non-Garhwali cultural-context records. The tagged all-data view retains all four groups.
- Current language-resource report: confidence is high for 9,975 texts, medium for 15,366, and low for 3,414. The medium group is dominated by 14,999 PahariLI texts whose Garhwali label is useful but whose component lineage remains missing.
- Every text has a genre. Resource views expose 1,114 lexicon candidates, 455 parallel examples, and 1,187 grammar-source candidates.
- Current train-only language resources include a 331-symbol Unicode character tokenizer, 262,231 observed word types, 1,114 pronunciation candidates (293 with source phonetic evidence), and 1,736 normalized TTS candidate pairs.
- Only 29 text records carry explicit dialect labels. District names are never converted into dialect labels; 10,872 conversational, lexical, or folk records are prioritized for dialect review.
- All 110,436 VAANI recordings carry district, gender, speaker-status, and language-evidence tags. Nine supervised transcripts need language/script review. The untranscribed 104,542 remain medium-confidence source-labelled Garhwali audio until transcription verifies their content.
- VAANI has 363 distinct non-placeholder speaker IDs across 21,023 rows; 89,413 rows use an unidentified speaker placeholder. Geographic coverage is limited to Uttarkashi (74,552) and Tehri Garhwal (35,884).

## SraVaani quality sweep

- Completed Hugging Face Job [`6aaa1726f76d6a098a70f768`](https://huggingface.co/jobs/rushilrawat/6aaa1726f76d6a098a70f768) ran all 61 validation-first trials. The selected adaptation improved validation WER but worsened held-out WER, so base SraVaani remains preferred. Paid Hugging Face processing is no longer active. See [`sravaani-refined-61-result-2026-09-16.md`](sravaani-refined-61-result-2026-09-16.md).

## Review queues

`data/processed/review/` contains bounded samples: 13 source transcript, 3 clipping, 4,112 normalization, 62 low-quality text, and 100 review-band text records. The two-pass native-review workflow packages 176 current source/text accuracy cases and 113 transcript packets; broader older packets include 10,873 dialect-priority and 2,492 earlier evaluation-text items. These are review queues, not adjudicated examples. It has received zero human decisions so far. The current strict benchmark contains 398 automatically screened text items and 112 ASR items.

Adjudication requires matching decisions from two distinct reviewers. Accepted and corrected decisions are materialized beside their immutable source payloads; originals are never overwritten.

The current prepared release is indexed by `data/processed/release/manifest.json`; its referenced canonical, experimental, segmented, audio, transcript, and evaluation views exist and their line counts were verified.

A bounded stage-1 ASR curriculum pilot trained on 32 human references and 2,048
standard SraVaani machine labels for 2,080 updates. On the same 269 human-only
validation records as stage 0, WER increased from 0.780522 to 0.784137 and CER
increased from 0.462980 to 0.463038. The configuration is rejected, no machine
labels are promoted, and curriculum stage 2 remains locked.

The follow-up weighted-batch trainer distributed the same 2,080 records into 32
normalized updates, each containing one human reference and 64 machine labels.
WER increased further to 0.788153 and CER to 0.463672, adding 38 word and 12
character errors relative to stage 0. The machine-label curriculum recipe is
closed without running its full stage; all source and draft records remain active.

All 2,002 strict human-reference recordings are also packaged for official
SraVaani NeMo adaptation: 1,621 train, 269 validation, and 112 held-out test
records in deterministic tar/manifest pairs totaling 412,037,120 archive bytes.
All audio hashes and 16 kHz mono 16-bit PCM properties pass, every row retains
CC BY 4.0 evidence, and cross-split audio/speaker leakage is zero. The decoder-only
102-step plan and official 1,796,208,640-byte NeMo checkpoint were verified. The
`l4x1` Hugging Face Job completed training, persisted a 1,796,198,400-byte
adapted checkpoint, and completed the closed held-out evaluation. The resulting
43.528% WER / 17.452% CER does not displace base SraVaani because its primary
WER is worse.

The current GarhwaliBench v0.1 candidate indexes 3,847 external task records,
398 strict automated text rows, and 112 speaker-safe ASR rows. The benchmark
builder now trains its character-bigram floor on the 7,490-row recommended
Garhwali view (manifest SHA-256
`2de3f3f95f24d41df9a4ce142496b7e9e97ac402ff4cca4c00edb6bed41d6ec8`): test
perplexity is 14.122106 with zero observed character OOV and zero exact
train/evaluation overlap. The prior 17.000058 score used the broad 106,915-row
training view and is retained only as a same-scorer comparison. The external
audit also flags one exact XORQA primary-text group across source train/dev (two
rows); neither row is in test, and neither is removed. There is no approved
independent final accuracy score. Native review and dialect annotation are
deferred, so GarhwaliBench remains an automated candidate rather than a gold
benchmark. See
[`benchmark-research-status-2026-09-25.md`](benchmark-research-status-2026-09-25.md)
for the counted status and remaining steps.

The earlier multilingual audit compares five pinned tokenizers on a historical,
checksum-addressed 2,492-text test snapshot. IndicBERTv2 has the lowest fertility
at 1.531569 tokens per whitespace word. Its first 128-record masked-language
pilot scores 17.786561% masked-token accuracy and 6.977486 cross-entropy over 506
deterministic masks, with zero truncation. These values have not been recomputed
on the current 398-record benchmark candidate.

The Garhwali-to-English translation audit covers 997 IndicGenBench FLORES development pairs and all 1,012 test pairs. The deterministic translation-memory floor scores 0.008208 smoothed BLEU / 0.215886 chrF2. On the same fixed 32-record pilot, pinned NLLB-200 distilled with an explicit Hindi source-token proxy scores 0.219719 / 0.574134, while the community Garhwali LoRA adapter scores 0.095460 / 0.460474. The base model is retained as the current pilot because the adapter underperforms and publishes no Garhwali language-token mapping.

The XORQA retrieval audit deduplicates 1,139 source rows into 1,059 passages and evaluates 500 dev plus 539 test questions. On the full test split, word BM25 reaches 1.669759% Recall@10, character BM25 reaches 2.411874%, and zero-shot mean-pooled IndicBERTv2 reaches 10.389610% with 2.226345% Recall@1. English oracle BM25 reaches 85.2% Recall@10 on the 500 dev rows where the upstream benchmark supplies oracle questions; all 539 test oracle questions are empty and are explicitly excluded from that comparator.

## Dataset splits

- The complete all-data text partitions contain 106,915 train, 3,063 validation,
  and 4,086 test segments; the public text partitions contain 8,037 train, 401
  validation, and 422 test segments. Neither normalized text components nor
  exact segment hashes cross partitions.
- Strict ASR and TTS candidate partitions retain 2,002 clean transcript/audio rows from 248 identified speakers: 1,621 train, 269 validation, and 112 test. No identified speaker crosses a partition.
- The broader 5,894-row supervised ASR export remains available. The strict view excludes 3,886 placeholder-speaker rows and six transcript/language-review rows rather than deleting them.
- Candidate evaluation manifests contain 398 strict automated test text segments
  and 112 strict test audio rows. They are checksum-addressed and active for
  experimental evaluation; native review and dialect annotation remain pending.
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

The current full-suite run passes **466 tests**. Structured records have standardized provenance and quality
metadata, including URLs or capture fingerprints for every source reference.
A web review added source-specific rights findings to the 186 formerly
unassessed records, but did not establish a compatible public-rights basis for
the complete mixed-source records. The 146,684-row public profile therefore
omits all 216 structured records; all remain in the 257,807-row all-data
package. Public and all-data preflights pass for the rebuilt packages.
Native-speaker review and dialect annotation are deferred; the benchmark is an
automated candidate. See
[`finalreport.md`](../finalreport.md) and
[`DEEP_DIVE_FINAL_AUDIT.md`](../DEEP_DIVE_FINAL_AUDIT.md) for the release
decision and [`structured-rights-web-review-2026-09-23.md`](structured-rights-web-review-2026-09-23.md) for source findings.
