---
language:
- gbm
license: other
task_categories:
- automatic-speech-recognition
- text-generation
- translation
configs:
- config_name: text
  data_files:
  - split: train
    path: data/text/train-*.jsonl
  - split: validation
    path: data/text/validation-*.jsonl
  - split: test
    path: data/text/test-*.jsonl
- config_name: asr
  data_files:
  - split: train
    path: data/asr/train-*.jsonl
  - split: validation
    path: data/asr/validation-*.jsonl
  - split: test
    path: data/asr/test-*.jsonl
- config_name: sravaani_drafts
  data_files:
  - split: train
    path: data/sravaani_drafts/train-*.jsonl
- config_name: lexicon
  data_files:
  - split: train
    path: data/lexicon/train-*.jsonl
- config_name: instructions
  data_files:
  - split: train
    path: data/instructions/train-*.jsonl
  - split: validation
    path: data/instructions/validation-*.jsonl
  - split: test
    path: data/instructions/test-*.jsonl
- config_name: catalog
  data_files:
  - split: train
    path: data/catalog/train-*.jsonl
---

# Garhwali Language Lab

Release: **garhwali-language-lab-v0.1.0**

Versioned Garhwali (`gbm`) text, speech, lexicon, and instruction resources built
by the Garhwali Language Lab. Every row retains source and license evidence.

This rights-filtered package contains **145,359 records** across six
configurations, including transcripts for **104,534
unique SraVaani recordings**. This transcript-only package does not include audio files or source filenames.

The `catalog` configuration publicly accounts for all
**27,987 exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
only the protected text value is redacted. Nothing is silently omitted.

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Targeted rows also retain their local Whisper alternative,
cross-model agreement, and bounded review-confidence evidence. Draft export
status: **complete**.

All **1,188** targeted recordings retain
the third-checkpoint hypothesis. For the **1,090**
Garhwali review records, the package also carries a structurally ranked machine
proposal and its evidence limits. These proposals are pending audio review and
are never represented as automatic corrections or human references.
The remaining **35** structural
outliers also include deterministic re-decoding, waveform activity, and
human-reference calibration evidence. They still require listening review.

The draft layer also preserves **98
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).
