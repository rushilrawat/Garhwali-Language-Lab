# Model-assisted text cleanup and ablation

## Outcome

The pass represents all **27,987** parent texts and excludes none. Each generated
record keeps the immutable original, the current cleaned value, the mechanical
proposal, candidate spelling pairs, source and language metadata, and an explicit
`proposal_only` status. No canonical text, language label, dialect label, or
source record was overwritten.

## Proposal pass

- **4,096** priority records scored with pinned
  `ai4bharat/IndicBERTv2-MLM-only` revision
  `8598f13fe52443bc3fc054fcd665944560145b5c`.
- **81,116** deterministic masked tokens scored on CPU.
- **410** records at or above the 90th-percentile loss threshold retained as
  model/source disagreements.
- **108** records have conservative mechanical suggestions.
- **35,864** low-confidence spelling pairs occur across **10,200** records.
- **2,327** mixed or unresolved records have Hindi/Garhwali ambiguity priority.
- **10,660** records lack explicit dialect evidence in a dialect-relevant genre.
- **2,328** records retain OCR-source priority.
- **16,687** records have at least one proposal or priority signal.

Spelling candidates come only from medium/high-confidence Garhwali texts in the
training partition. A candidate must be one edit away, substantially more frequent,
and is still treated as a suggestion. IndicBERTv2 loss is an anomaly-ranking signal;
it does not prove that a text is Hindi, Garhwali, or a particular dialect.

## Fixed-split ablation

| Variant | Changed records | Character perplexity | Test token OOV | Train singleton types | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| Current text | 0 | 16.88499549 | 0.06995491 | 56,158 | Baseline |
| Mechanical only | 108 | 16.88726214 | 0.06995491 | 56,158 | Not promoted |
| Mechanical + bulk spelling | 10,244 | 16.76707705 | 0.06016912 | 48,320 | Not promoted |

The evaluation uses the existing document split: **25,169** training parents and
**1,393** test parents. The mechanical variant slightly worsens perplexity. Bulk
spelling improves surface statistics, but inspection shows substitutions can map
valid forms to unrelated frequent neighbors. Surface improvement is insufficient
evidence for semantic, spelling, or dialect correctness.

## Reproduce

```bash
PYTHONPATH=.cache/asr-runtime python3 scripts/propose_text_cleanup.py --model-records 4096 --device cpu
python3 scripts/run_text_cleanup_ablation.py
```

Generated manifests remain under `data/processed/` and are ignored by Git. The
tracked release summary records the counts and decisions.
