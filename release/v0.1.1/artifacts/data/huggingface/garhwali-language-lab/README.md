---
language:
- gbm
license: other
task_categories:
- automatic-speech-recognition
- text-generation
- translation
configs:
- config_name: asr
  data_files:
  - split: test
    path: data/asr/test-00000.jsonl
  - split: train
    path: data/asr/train-00000.jsonl
  - split: validation
    path: data/asr/validation-00000.jsonl
- config_name: catalog
  data_files:
  - split: train
    path: data/catalog/train-00000.jsonl
  - split: train
    path: data/catalog/train-00001.jsonl
  - split: train
    path: data/catalog/train-00002.jsonl
- config_name: instructions
  data_files:
  - split: test
    path: data/instructions/test-00000.jsonl
  - split: train
    path: data/instructions/train-00000.jsonl
  - split: validation
    path: data/instructions/validation-00000.jsonl
- config_name: lexicon
  data_files:
  - split: train
    path: data/lexicon/train-00000.jsonl
- config_name: sravaani_drafts
  data_files:
  - split: train
    path: data/sravaani_drafts/train-00000.jsonl
  - split: train
    path: data/sravaani_drafts/train-00001.jsonl
  - split: train
    path: data/sravaani_drafts/train-00002.jsonl
  - split: train
    path: data/sravaani_drafts/train-00003.jsonl
  - split: train
    path: data/sravaani_drafts/train-00004.jsonl
  - split: train
    path: data/sravaani_drafts/train-00005.jsonl
  - split: train
    path: data/sravaani_drafts/train-00006.jsonl
  - split: train
    path: data/sravaani_drafts/train-00007.jsonl
  - split: train
    path: data/sravaani_drafts/train-00008.jsonl
  - split: train
    path: data/sravaani_drafts/train-00009.jsonl
  - split: train
    path: data/sravaani_drafts/train-00010.jsonl
- config_name: text
  data_files:
  - split: test
    path: data/text/test-00000.jsonl
  - split: train
    path: data/text/train-00000.jsonl
  - split: validation
    path: data/text/validation-00000.jsonl
---

# Garhwali Language Lab

Release: **garhwali-language-lab-v0.1.1**

This public profile omits **216 structured-knowledge records**
whose provenance does not include an explicit compatible public-rights basis.
They remain intact in the complete all-data package. No source license is
inferred from a URL. The text catalog records each collected text identity and
redacts values without compatible redistribution evidence. Native-speaker
review and dialect annotation are deferred; benchmark and model scores are
automated research results, not native-validated claims.

Versioned Garhwali (`gbm`) text, speech, lexicon, instruction, geographic,
historical, literary, music, and university-research resources built by the
Garhwali Language Lab. Available source and review metadata vary by configuration.

This public-profile package contains **146,684 records** across 6 configurations, including transcripts for **104,534
unique SraVaani recordings**. This transcript-only package does not include audio files or source filenames.

The `catalog` configuration publicly accounts for all
**28,755 exact-unique collected text records**. Rows whose
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
