# Expanded human-transcript SraVaani experiment

Updated: 2026-09-16
Job: [`6aaaa754f76d6a098a70f2f`](https://huggingface.co/jobs/rushilrawat/6aaaa754f76d6a098a70f2f)
Final status: completed; checkpoint retained as experimental, no model promoted

## Data boundary

The source pool contains all 5,894 human-transcribed Garhwali VAANI rows. The
training builder removes all 381 audio hashes in the fixed benchmark: 269
validation and 112 test. It also removes any identifiable benchmark speaker;
there were no additional matches after hash exclusion.

The resulting training set contains 5,513 unique clips, 8.112 hours, and 199
identified speakers. Speaker identity is incomplete for 3,886 rows, so this is
an experimental training run rather than a speaker-disjoint release model.
Audio-hash overlap and known-speaker overlap with the fixed benchmark are zero.

## Training decision

The run uses the recipe selected by the completed 61-trial validation sweep:
decoder/joint-only adaptation, learning rate `5e-5`, two epochs, effective batch
size 32, and seed 17. Selection remains on the unchanged 269-record validation
set. The 112-record test is evaluated once only if validation WER improves over
the base model.

The L4 job has a 90-minute hard timeout, limiting its maximum compute charge to
$1.20 at $0.80/hour. It does not overlap another paid job. Artifacts persist in
the private bucket:

```text
hf://buckets/rushilrawat/jobs-artifacts/cloud_output-dc73f3d4
```

After completion, sync with:

```bash
hf buckets sync \
  hf://buckets/rushilrawat/jobs-artifacts/cloud_output-dc73f3d4 \
  data/processed/evaluation/asr/sravaani_expanded_human/cloud_output
```

The reproducible builders and launcher are
`scripts/prepare_sravaani_expanded_finetune.py` and
`scripts/run_sravaani_expanded_hf_job.sh`.

## Result

The job completed 346 optimizer steps. Validation improved from 43.454% to
42.209% WER and from 18.948% to 18.302% CER. The saved 112-record test
aggregate is 43.289% WER / 17.396% CER; the fine-tune report does not record a
test-manifest hash, so the comparison to base SraVaani's 42.761% / 17.606% is
not verifiably paired. The checkpoint remains experimental and is not promoted.

The job used 693 seconds of billed L4 runtime, an estimated $0.154 at $0.80/hour.
