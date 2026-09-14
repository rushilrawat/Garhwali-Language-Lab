# Intensive quality audit

## Outcome

The first intensive quality pass adds evidence-based tiers to all **27,987 text
records**, **5,894 human-transcribed speech records**, and **104,542 SraVaani
machine drafts**. It changes no text or transcript value. Every tier includes
explicit reasons, so later corrections remain reversible and auditable.

## Findings

| Dataset | Strict/high-quality | Experimental/review | Context | Main risk |
| --- | ---: | ---: | ---: | --- |
| Human-transcribed speech | 5,881 strict candidates | 13 review | 0 | Existing transcript/training flags |
| SraVaani machine drafts | 103,354 experimental | 1,188 review | 0 | Script, repetition, empty output, or weak cross-model agreement |
| Text | 4,790 high-quality local-only | 20,553 review | 2,644 non-strict context | Public-training rights and language confidence do not yet overlap |

No text currently satisfies every strict-public rule. This is a real release
constraint, not a processing failure: only **188** text records report any
training-eligible source, and all 188 still have medium language confidence;
184 also carry cleanup-review signals. Conversely, 4,790 clean, high-confidence
Garhwali candidates fail only the rights-cleared-source requirement and remain
useful for local research.

## Quality policy

- Preserve original, cleaned, and proposed values independently.
- Never infer Hindi versus Garhwali from shared Devanagari vocabulary alone.
- Never convert district names into dialect labels.
- Never promote a machine transcript to human-reference status.
- Keep mixed-language and cultural-context data active in named, non-strict views.
- Require strong language evidence, clean structure, compatible rights, and no
  active review flags for the strict public tier.

## Next correction order

1. Review the 188 rights-eligible text records first; they are the shortest path
   to a defensible public text seed.
2. Resolve the 13 supervised-speech review records before freezing GarhwaliBench.
3. Review the 1,188 risky machine drafts using audio and model disagreement;
   never guess corrections from text alone.
4. Audit the 4,790 high-quality local-only texts source by source for explicit
   redistribution and model-training permission.
5. Sample the 15,160 clean medium-confidence Garhwali candidates by source and
   promote a source only after native language validation.
6. Rebuild tiers, evaluation data, and Hugging Face exports after each accepted
   correction batch.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest scripts/test_build_quality_tiers.py
.venv/bin/python scripts/build_quality_tiers.py
```

Generated tiered manifests and the machine-readable report are under
`data/processed/model_ready/quality_v2/` and remain Git-ignored with the other
generated datasets.
