# X-high final Garhwali data audit

**Date:** 2026-09-10  
**Scope:** Repeat the earlier low-effort collection and preprocessing decisions at high depth, recover useful material that was present but under-exposed, and record what still cannot add trustworthy unique Garhwali data.

## Result

This pass produced two material gains. It recovered **189 attributed phrase/example rows** from overlooked public learning pages, of which **139 are new exact-unique texts**, and it converted page-sized cleaned records into **91,536 sentence-like occurrences / 86,215 exact-unique segments**. The canonical all-data text view now contains **27,987 unique texts and 7,391,666 characters**.

The pass also replaced header-only audio checking with signal-level measurements across all **110,436 VAANI WAVs / 135.509 hours**. Every file remains readable, mono, 16 kHz, and 16-bit PCM. A reversible normalization plan now covers every file; the original audio was not changed.

## Newly recovered web text

| Source | Rows | Notes |
| --- | ---: | --- |
| eUttaranchal lesson 1 | 23 | English–Garhwali examples |
| eUttaranchal lesson 2 | 34 | English–Garhwali examples |
| eUttaranchal lesson 3 | 38 | English–Garhwali examples |
| LanguagesHome | 90 | Phrase pairs |
| Omniglot | 4 | Devanagari sample text |
| **Total** | **189** | **185 Romanized, 4 Devanagari** |

The extractor archives each raw HTML response by SHA-256 and stores the source URL, paired English where present, script, rights status, and quality flags. One repeated web row and 49 rows already present in other sources account for 50 duplicate occurrences; 139 texts are new to the canonical view. The sources do not state an open text license, so these rows remain traceable in the user-approved experimental quarantine layer.[^1][^2][^3]

## Text re-extraction

Earlier preparation treated many OCR books and long web documents as one record per page. The new segmenter exposes sentence-like units while retaining the parent text hash, original provisional document split, full provenance, and occurrence count.

| Measure | Count |
| --- | ---: |
| Parent cleaned records | 27,987 |
| Segment occurrences | 91,536 |
| Exact-unique segments | 86,215 |
| Duplicate segment occurrences | 5,321 |
| Segments containing Devanagari | 58,959 |
| Romanized/other-script segments | 27,256 |
| Very short review flags | 2,338 |
| Longer than 1,000 characters | 31 |

Exact segment hashes receive provisional deterministic splits, so an identical segment cannot occur in two segment splits. The report also records **332 segments** whose parent documents had different prior splits. These splits are suitable for exploration; final model evaluation still needs document-aware connected-component splitting to keep related passages together.

## Full audio signal audit

The added measurements are RMS level, peak level, zero-sample share, clipped-sample share, and normalized DC offset. They reveal quality variation that format checks could not see.

| Signal measure | Result |
| --- | ---: |
| RMS dBFS, median | -16.374791 |
| RMS dBFS, 1st–99th percentile | -39.109681 to -10.541420 |
| Very quiet, RMS below -40 dBFS | 856 |
| Very loud, RMS above -10 dBFS | 552 |
| Absolute DC offset above 0.02 | 2,718 |
| At least 1% clipped samples | 3 |
| Normalization review records | 4,112 |
| Recommendations projected above -1 dBFS | 10,967 |

The normalization manifest recommends gain toward -20 dBFS, capped to ±12 dB, and flags projected clipping rather than rewriting a waveform. This gives the later audio-cleanup stage a complete, reproducible work queue without throwing away difficult speech.

## Sources rechecked without double-counting

The current Hugging Face language filter exposes 24 datasets tagged for `gbm`; repository inspection showed that most are mirrors or derivatives already represented locally.[^4] In particular:

- `mlexplorer008/hin_dialect_classification` mirrors the HinDialect material already represented by 128 Garhwali rows, so it was not counted again.[^5]
- `grushaaaaa/indic-dialect-asr` is already represented by 7,823 quarantined Garhwali transcript rows with component lineage retained.[^6]
- Chaashini remains gated and currently advertises only one 2.2-second Garhwali clip, so gaining access would add negligible volume.[^7]
- `aoiandroid/mms-multilingual-audio-5to30min` offers one approximately 28.3-minute Garhwali YouTube-derived recording without a transcript. It remains a discovery lead because it needs source-level rights and duplication review.[^8]

## Reproduction

```sh
/opt/anaconda3/bin/python scripts/ingest_web_learning.py
python3 scripts/prepare_text_corpus.py
python3 scripts/build_all_data_view.py
python3 scripts/clean_text_corpus.py
python3 scripts/deep_cleanup.py
python3 scripts/segment_text_corpus.py
python3 scripts/prepare_audio_normalization.py
python3 scripts/build_review_queues.py
python3 scripts/build_release_manifest.py
```

The Anaconda interpreter is used only for HTTPS retrieval because it has a working local certificate bundle. The extractor never disables TLS verification.

The project-local `.venv` now contains the pinned LangGraph dependencies. All **64 pipeline tests** pass, including orchestration checkpoints/retries, web extraction, text segmentation, signal auditing, normalization, and the experimental-use safety invariant.

## Remaining limits

This is the practical end of high-yield unattended collection from the sources currently reachable. The largest remaining improvement is the **104,542 untranscribed VAANI utterances**, which requires transcription or a Garhwali-adapted ASR model. Native-speaker review remains necessary for Romanized spelling, dialect labels, OCR repairs, the 13 VAANI transcript flags, and mixed-language records. Books, podcasts, songs, private/community archives, and blocked sites may still contain material, but each needs a supplied copy, permission, or human transcription before it becomes reliable training data.

[^1]: [eUttaranchal, Learn Garhwali](https://www.euttaranchal.com/culture/learn-garhwali.php)
[^2]: [LanguagesHome, English to Garhwali](https://www.languageshome.com/English-Garhwali.htm)
[^3]: [Omniglot, Garhwali writing and sample text](https://omniglot.com/writing/garhwali.htm)
[^4]: [Hugging Face datasets tagged Garhwali (`gbm`)](https://huggingface.co/datasets?language=language%3Agbm)
[^5]: [mlexplorer008, Hin dialect classification](https://huggingface.co/datasets/mlexplorer008/hin_dialect_classification)
[^6]: [Indic Dialect ASR](https://huggingface.co/datasets/grushaaaaa/indic-dialect-asr)
[^7]: [Chaashini](https://huggingface.co/datasets/kapturecx/Chaashini)
[^8]: [MMS multilingual long-form audio](https://huggingface.co/datasets/aoiandroid/mms-multilingual-audio-5to30min)
