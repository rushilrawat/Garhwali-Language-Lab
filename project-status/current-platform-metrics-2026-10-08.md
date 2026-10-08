# Current platform metrics — 8 October 2026

This is the current cross-platform status checked against the live dataset
pages on 8 October 2026. Dataset Viewer and Kaggle totals count configurations,
files, or index views; they are not all unique language examples. Historical
release and experiment reports below this date retain the measurements they
recorded at the time.

## Hugging Face: corpus

The live [Garhwali Corpus](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
page reports **963,484 rows** and **7.57 GB** across **20 configurations** and
31 config/split views. The breakdown is **778,157 source/reference-table rows**
and **185,327 overlapping content-view rows**. These totals describe the
published views, not distinct passages or training examples.

The public text-training surface has 1,841 automatically screened,
sentence-length Meta Omnilingual candidates (47,566 whitespace-separated
words) and 110 short context rows. The selected text values already occur in
the earlier `text` / `text_expansion` views. They make existing material easier
to select; they add no source recordings or unique transcript text. Neither
view has native-speaker review. The corpus `asr` config remains a separate
2,002-row provider-reference view.

## Hugging Face: speech

The live [Garhwali Speech](https://huggingface.co/datasets/rushilrawat/garhwali-speech)
page reports **118,375 rows** and **36.5 GB**. The displayed row total is the
sum of **113,363 source/audio rows**, a **2,718-row text-only VAANI
`asr_reference` index**, and a **2,294-row text-only Meta
`asr_meta_extra_train` index**. The two indexes point to audio already in the
source configs; adding the view counts does not create new audio.

The audio configs contain **113,350 unique audio hashes** and about **154.65
hours**. VAANI has 110,436 audio rows, of which 5,894 have provider
transcripts. The current speaker-disjoint `asr_reference` view has **2,202
train / 373 validation / 143 test rows**. These provider references are
unadjudicated. A separate 2,294-row Meta view is train-only and must not be
used as an independent evaluation set. The earlier corpus `asr` view still
has 2,002 rows; the speech view makes 716 already-present VAANI references
newly eligible through recovered speaker identity joins.

SraVaani's 104,534 unique audio-hash rows include 104,500 non-empty machine
drafts and 34 empty drafts. Drafts are hypotheses, not reference transcripts.
The speech audio payload remains at its v0.2.1 base release; the v0.2 views
add text-only indexes and documentation. The live Hugging Face language tag
is `gbm` (Garhwali).

## Kaggle

The public [Garhwali Screened Text Candidates](https://www.kaggle.com/datasets/rushilrawat1/garhwali-screened-text-candidates)
dataset is at **version 1**. Its preview shows 1,841 training texts (47,566
words) and 110 short context rows. It mirrors existing Meta-derived Hugging
Face views and adds no unique examples. Rows are automated candidates without
native-speaker review.

The private [Garhwali ASR reference clips](https://www.kaggle.com/datasets/rushilrawat1/garhwali-asr-reference-clips-v0-1)
dataset is at **version 2** with **2,718** existing VAANI audio/reference
pairs: 2,202 train, 373 validation, and 143 test. All 2,002 rows from version
1 remain, with 716 additional existing references newly indexed. No audio or
transcript was created. Its manifest preview works. The baseline notebook was
saved as Kaggle version 3 with the v2 input selected; it has not been run.

## GitHub language identifier

The repository README identifies the project as Garhwali (`gbm`). The GitHub
About description now reads “Garhwali (gbm) language corpus, speech, and
research resources with provenance, rights, and training-ready views,” and the
repository has the `gbm` topic. GitHub's Languages bar still classifies
programming languages; the About description and topic provide the language
identifier for this natural-language project.

## Developer tools and release checks

The [GitHub developer update](https://github.com/rushilrawat/Garhwali-Language-Lab/commit/a62c9945521f70a957658d1094ffafe0afbdef46)
published a Python 3.12 setup, a CPU-first masked-language-model example, a
Kaggle ASR notebook, dataset contracts, and a readiness guide. The
[8 October CI run](https://github.com/rushilrawat/Garhwali-Language-Lab/actions/runs/37802743148)
passed **832 tests** and the frozen v0.1.1 bundle-integrity check. The full
source-freshness comparison still finds newer ignored local artifacts; it is
not a new bundle release. Neither new training example has been rerun from a
clean public account environment, and no independently validated model is
claimed.

## Sources and metric limits

- Hugging Face corpus Dataset Viewer and card: the linked corpus page above.
- Hugging Face speech Dataset Viewer and card: the linked speech page above.
- Kaggle dataset cards and previews: the linked text and ASR pages above.
- Project release checks and immutable upload records: [Hugging Face speech-view report](../research/huggingface-speech-training-views-2026-10-07.md), [Kaggle ASR sync report](../research/kaggle-asr-v0.2-sync-2026-10-07.md), and [ASR nine-step progress report](asr-nine-step-progress-2026-10-07.md).

No new model training or benchmark run is reported here. Row totals are
platform view counts. Word totals use whitespace separation. Automated
screening and split checks do not certify Garhwali spelling, dialect, meaning,
or transcript accuracy.
