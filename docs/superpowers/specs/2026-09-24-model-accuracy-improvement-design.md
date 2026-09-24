# Garhwali model accuracy improvement design

**Date:** 2026-09-24
**Status:** Design for review; no training or model changes authorized by this document alone.

## Intent and constraints

Improve measurable Garhwali quality across the existing speech recognition,
text representation, generation/translation, and retrieval systems, in a
controlled sequence. Prefer local, reproducible experiments. Do not launch paid
Hugging Face Jobs, buy compute, publish model artifacts, delete corpus rows, or
automatically replace source transcripts. Native-speaker review and dialect
annotation remain deferred at the owner's direction; therefore all resulting
language-quality claims must be labeled as automated-reference results, not
native-validated accuracy.

The project should not treat a metric improvement on one task as proof that a
single general Garhwali model is accurate. Maintain separate task-specific
baselines, data manifests, promotion decisions, and limitations.

## Evidence informing the sequence

- On the existing 112-record VAANI comparison, SraVaani 1.0 leads at 42.761%
  WER / 17.606% CER. The 61-trial selected decoder lowers validation WER to
  42.711% but scores 43.528% WER on the previously frozen test; the expanded
  human-transcript adaptation scores 43.289% test WER. Keep the original model
  as baseline; do not promote either adaptation.
- Two Whisper machine-transcript curriculum pilots worsened fixed validation.
  Do not scale that pseudo-label recipe.
- The public Meta Omnilingual Garhwali subset has 2,927 audio/transcript pairs
  (2,329 train, 298 validation, 300 test), no exact audio or transcript overlap
  with VAANI, and five exact-audio duplicate groups with conflicting text. Its
  existing split-safety metadata must be honored. It may provide a more
  independent evaluation of VAANI-trained systems, subject to checking each
  checkpoint's training lineage.
- IndicBERTv2 continuation improved mean validation masked-token accuracy from
  24.299% to 28.287%, but this is not yet downstream evidence of better language
  understanding.
- The 32,768-step mT0 continuation has two completed seeds; the third seed and
  combined generation diagnostics were stopped when HF balance was insufficient.
  Earlier mT0 generation reached 2.308% exact match, while adapted chrF2 remained
  below the zero-shot base.
- Existing IndicGenBench retrieval results are low: IndicBERTv2 reaches 10.39%
  Recall@10. Current Garhwali-to-English translation results are exploratory and
  include only a 32-row NLLB pilot using a Hindi source-token proxy.
- The existing VAANI 112-row test and other fixed benchmarks have already been
  inspected for previous decisions. Audit exact evaluated hashes before calling
  any evaluation blind or untouched.

## Approaches considered

1. **Task-by-task controlled improvement (selected).** Establish reliable
   baselines, then optimize ASR, text understanding, generation/translation,
   and retrieval separately. This keeps failures diagnosable and makes each
   result comparable to its own baseline.
2. **One joint Garhwali model.** Mix all task data into a single model immediately.
   This would entangle incompatible labels and task objectives before their
   baselines and data leakage are fully characterized.
3. **More data or pseudo-labels first.** Expand training with all available
   machine transcripts. Prior controlled ASR pilots regressed, and agreement
   scores are not correctness probabilities, so this is not the first move.

## Ordered work design

### Phase 1 — Accuracy and split audit

1. Inventory model weights, model revisions, training data hashes, split
   manifests, checkpoints, predictions, and all test hashes already examined.
2. Verify speaker, audio-hash, exact-text, and known semantic-duplicate isolation
   for each task. Record unknown upstream model pretraining overlap as unknown.
3. Produce one baseline registry with reproducible commands and metrics for
   current ASR, IndicBERT, mT0, translation, and retrieval models.
4. Identify valid final evaluation sets. Prefer the fixed Meta Omnilingual test
   for testing models that have not trained on it; exclude duplicate-unsafe rows
   using the existing flags. Do not label it blind until checkpoint lineage and
   prior evaluations are checked. If no genuinely independent test remains,
   report that limitation instead of manufacturing a clean-test claim.

**Gate:** no further tuning begins until every candidate run has a known
training manifest and an identified validation set. Existing tests stay closed
to tuning.

### Phase 2 — ASR, the primary accuracy track

1. Re-score the original SraVaani checkpoint and current Whisper baseline on the
   eligible Meta test rows without changing decoding, then save hash-verified
   predictions and WER/CER by source split and relevant audio strata.
2. Use validation only to analyze error classes and try bounded decoding or
   normalization changes. Keep the previously viewed VAANI test out of selection.
3. Test one data-adaptation hypothesis only if local hardware and the existing
   code can run it without paid compute: add Meta train pairs to a controlled
   SraVaani/Whisper adaptation while reserving Meta validation and test. Keep
   machine-generated transcripts out of supervised training.
4. Compare each candidate on the same paired examples. Promote only if it lowers
   WER and CER on validation and the selected candidate also improves the
   untouched test without a material source/speaker regression. Otherwise retain
   the prior checkpoint.
5. Keep confidence as an abstention/review signal. Do not auto-correct source
   transcripts or describe calibrated scores as correctness probabilities.

**Fallback:** if local SraVaani fine-tuning is unsupported or too resource-heavy,
finish the free inference/error-analysis work and adapt only the model that can
be trained reproducibly on available local hardware. Do not submit a paid job.

### Phase 3 — Text representation quality

1. Compare the current IndicBERTv2 base and continuation checkpoints on the
   same frozen text evaluation sets, using source-aware splits.
2. Add downstream tests that measure Garhwali-relevant behavior: Garhwali versus
   Hindi discrimination, lexicon/example matching, and retrieval ranking. The
   MLM validation loss remains a diagnostic, not the promotion metric.
3. Use the checksum-frozen recommended Garhwali training view by default; report
   broader/mixed-language experiments separately.
4. Run one final held-out comparison after checkpoint selection. If an existing
   test has informed prior tuning, record it as development evidence and create
   an independent test only from records with defensible lineage.

### Phase 4 — Generation and translation

1. Audit the saved mT0 seeds and partial 32,768-step artifacts before resuming
   anything. Resume the missing seed locally only if its exact checkpoint,
   data, runtime, and hardware are available; otherwise mark that branch
   incomplete instead of recreating it from memory.
2. Select checkpoints on validation-generation outputs, not teacher-forced loss
   alone. Measure exact match, chrF2, empty/malformed output, source copying,
   repetition, and unsupported additions by task.
3. For translation, retain NLLB's Hindi source-token setup as a proxy baseline.
   Tune only on training/development pairs and report its missing Garhwali token
   explicitly. Compare with mT0 on the same eligible pairs.
4. Evaluate the selected system once on a test subset whose rows were not used
   for prior tuning. Do not promote if generation quality remains below the
   zero-shot base or produces unacceptable malformed/hallucinated output.

### Phase 5 — Retrieval

1. Reproduce the BM25 and IndicBERTv2 baselines from the frozen XORQA records.
2. Train a task-specific retriever only on training pairs; select model and
   hyperparameters on development data.
3. Compare Recall@1/5/10 and MRR on the unchanged test. Include exact-match and
   duplicate-passage handling, and report query-language limitations.
4. Promote only a reproducible improvement against both current baselines.

### Phase 6 — TTS readiness and final model report

1. Do not train a TTS model yet. First audit the 1,736 derived candidate pairs,
   voice coverage, transcript/audio alignment, and source split isolation.
2. Define a future TTS evaluation protocol before training. Automated ASR or MOS
   proxy scores can triage outputs but cannot establish naturalness without
   listening evaluation; no native-review claim will be made.
3. Generate a final report with per-task model, source revision, input hashes,
   exact splits, inference/training settings, paired metrics, confidence
   intervals, error slices, promotion decision, compute/runtime, and known
   limitations. Keep non-promoted checkpoints and all source data intact.

## Success criteria

- Every reported score can be recomputed from saved predictions and frozen
  manifests; each comparison uses identical examples and metric normalization.
- No train/evaluation leakage by known speaker, audio hash, exact text, or
  supported semantic duplicate edge; unknown pretraining exposure is disclosed.
- An update is promoted only after validation selection and a separate
  held-out confirmation. WER/CER and generation/retrieval metrics are not
  collapsed into a single vague accuracy claim.
- No paid Hugging Face job or new credit spend; no source rows or transcripts
  are deleted, redacted further, or automatically rewritten as part of model
  training.
- Native-language validity remains explicitly unverified while human review is
  deferred.

## Execution boundary

The work proceeds in the phase order above. Phase 1 is the first executable
task; later phases depend on its leakage and held-out-set findings. The design
does not authorize publishing datasets, uploading checkpoints, spending money,
or changing source text. Those actions are outside this model-accuracy study.
