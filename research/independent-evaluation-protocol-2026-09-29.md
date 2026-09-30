# Independent Garhwali Evaluation Set Protocol

- **Prepared:** 2026-09-29; status refreshed 2026-09-30
- **Status:** protocol ready; no new examples collected. The owner approved active work toward final-accuracy evidence in all five task areas.
- **Current eligibility:** 0/5 model-task areas support an independent final-accuracy claim. Approval sets the work priority; it does not waive the evidence gates below.

## Why the current scores are not independent

The fixed public test sets have saved predictions or known reuse, while external
checkpoint pretraining exposure is often undocumented. An exact-match scan can
find copied strings or audio hashes, but cannot establish that a pretrained
checkpoint never saw a translation, paraphrase, source page, or recording. The
current VAANI test is historical for the project's ASR runs and SraVaani's
upstream exposure to VAANI is not traceable to example IDs. Keep those numbers
as historical diagnostics; do not rescore them to choose a new model.

## Five-task readiness matrix — 2026-09-30

| Area | Current evidence | Next valid work | What a final claim still needs |
| --- | --- | --- | --- |
| Language modeling | The 402-row text candidate is historical/open. Exact audit finds 15 shared text hashes between recommended training and instruction test and 29 with instruction validation. This is an exposure risk if those texts were used for model training, not proof that a checkpoint consumed every row. | Freeze model, tokenizer, scoring code, and corpus snapshot; verify training sources against the overlaps; then evaluate on newly authored, source-grouped Garhwali text. | Rights-cleared held-out text created after the model freeze, stable text references, and an exposure record. |
| Translation | Existing public parallel-task rows and saved scores are reused/open; NLLB is not runnable with current local weights/runtime. | Freeze translation system and metric contract; prepare new Hindi/English inputs paired with independently authored Garhwali references. | Fresh, source-traceable parallel items created after freeze, model/version hash, and suitable reference evidence. |
| Retrieval | XORQA has a known exact train/dev text repeat and its evaluation uses a fixed public candidate corpus; prior test questions were scored. | Freeze retriever and a new candidate index; collect new questions and passages, grouping all questions from a passage/work together. | New rights-cleared passages and questions with verified answer evidence, an index hash, and no training or tuning exposure. |
| Generation | Shared scorer is implemented. Three saved mT0 runs match 130/320 current validation rows; 190 lack predictions. Recommended training text shares 15 exact hashes with instruction test and 29 with validation; checkpoint use of those source rows is not established. References are unreviewed. | Preserve the diagnostic; verify model training sources against cross-view overlaps; freeze a model and prompt, then create a fresh instruction/passage set with accepted references and score it once. | New post-freeze prompts/source texts, suitable references, checkpoint and prompt hashes, and a one-time frozen evaluation. |
| ASR | VAANI outputs have already been scored; SraVaani's upstream VAANI example overlap is unknown. Meta Omnilingual has four exact train/test audio and four train/test transcript-text overlap groups, and 27 train/validation text groups. The expanded-human train view also overlaps the experimental test view in 338 exact audio-hash groups and 575 transcript-text groups. New compatible local inference assets are absent. | Preserve and flag overlap findings; do not use the experimental split as held out; inventory model assets and decode settings; for independent evidence, record consented post-freeze speech and transcript references from new speakers. | Audio-use consent, new speaker-disjoint recordings, blind transcripts/adjudication, hashes, and a model freeze before collection. |

This table treats the owner's approval as authorization to pursue all five
tracks. It does not convert current historical/development measurements into
independent final accuracy. The project can continue local tooling and
provenance work now; claims requiring fresh Garhwali references or recordings
cannot be completed credibly by synthesizing the evaluation answers from the
same models being measured.

The 2026-09-30 row-level lineage audit refreshed 11 manifest families and 41
saved prediction files. It keeps the text, XORQA, generation, and VAANI test
results historical or unresolved and permits only development use for the
corresponding dev/validation splits. Its cross-view exact matches identify
shared content and possible training exposure; they do not prove a given model
consumed every matching item. The complete local-only audit is at
`data/processed/evaluation/garhwali_bench/model_accuracy_lineage_2026-09-30`
and is excluded from Git because its row-level JSON includes speaker IDs.

## Collection and freeze sequence

1. **Freeze models first.** Save model/revision and weight hashes, tokenizer,
   adapter, decoder or prompt configuration, code commit, and selected dev
   results. Do not tune again after test access.
2. **Author new material afterward.** Garhwali speakers create new prompts,
   passages, translations, and recordings that are not copied from this
   repository, public benchmarks, or model outputs. Record author/source and
   creation dates.
3. **Collect consent and rights.** Each contributor approves the specific
   recording/text use, attribution, release conditions, and whether their voice
   may be redistributed. Keep speaker names/contact data out of model manifests.
4. **Review references independently.** Two Garhwali reviewers work separately;
   transcript first pass is blind to the provider transcript and model output.
   Disagreements remain unresolved until documented adjudication.
5. **Check source and speaker families.** Keep all passages from one work and
   all recordings from one speaker in a single split. Run exact and near-match
   checks against all existing project data and candidate model predictions.
6. **Seal and score once.** Publish the test-manifest hash and metric contract
   before scoring. A custodian who did not tune the model runs the frozen
   candidate once. After the score is frozen, the examples can be published if
   rights permit; that published set then becomes an open historical test for
   later model versions.

## First-wave task sizes

These are practical initial targets for a useful diagnostic study, not a claim
of statistical power. Report speaker/source-clustered intervals and per-slice
counts; expand if intervals are too wide.

| Task | New material target | Required reference evidence |
| --- | --- | --- |
| ASR | At least 200 utterances from 6 or more speakers, including prompted and spontaneous speech; record duration, district self-report, device, and environment | Two independent blind transcripts per clip, adjudicated reference, consent for audio and text release |
| Translation | 200 new Hindi/English inputs across everyday, civic, geographic, and cultural domains | Two independent Garhwali translations per item; preserve both variants |
| QA/retrieval | 100 questions grounded in at least 25 newly authored Garhwali source passages | Two reviewers verify answer, evidence passage, and answerability; split by source passage/work |
| Summarization/generation | 40 new source passages with one or more task prompts each | Two native reference responses or explicit rubric-based human ratings; keep source families together |
| Language modeling | At least 200 new paragraphs, with a target of 30,000 Garhwali characters | Two reviewers confirm language scope and transcription; score only after tokenizer/model freeze |

One source collection may support several tasks, but its source family must stay
in one split across all of them. Do not treat several prompts from one passage
or several clips from one speaker as independent observations.

## Exposure record

Each model card/run must say `known`, `partial`, or `unknown` for training-data
exposure and link the evidence. Record exact-text, normalized-text, source-page,
audio-hash, and known-parallel-source overlap results. A negative scan is
evidence only about the scanned forms; if upstream exposure is unknown, label
the result **new-set evaluation with unknown pretraining exposure**, not
contamination-free or fully independent.

## Required files and retention

Keep a versioned row manifest containing a stable ID, task, split, source/work
family, creation date, author/reviewer pseudonyms, language/script evidence,
reference values and hashes, rights/consent state, model-exposure state, and
exclusion reason. Keep contact information and raw consent forms separately
with restricted access. Do not publish a row until its specific consent and
rights allow it. A sealed test is an evaluation-control stage, not deletion or
loss: retain its catalog entry, row count, steward, and manifest hash, then
publish the content when the one-time score is locked and rights allow.

## Current next action

The protocol is ready, but the project has no newly authored/recorded set or
reviewer decisions. This cannot be completed by running an LLM over existing
corpus data: that would not create new independent references or native
validation. The next external dependency is at least six consenting speakers
for ASR and two independent Garhwali reviewers for each task's references.
