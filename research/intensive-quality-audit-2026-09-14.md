# Intensive quality audit

## Outcome

The intensive quality gate covers all **27,987 exact-unique text records**,
**5,894 human-transcribed speech records**, and **104,542 SraVaani machine
drafts**. It changes no linguistic value. Every tier includes explicit reasons,
so later corrections remain reversible and auditable.

## Findings

| Dataset | Strict/high-quality | Experimental/review | Context | Main risk |
| --- | ---: | ---: | ---: | --- |
| Human-transcribed speech | 5,881 strict candidates | 13 review | 0 | Existing transcript/training flags |
| SraVaani machine drafts | 103,354 experimental | 1,188 review | 0 | Script, repetition, empty output, or weak cross-model agreement |
| Text | 1,188 strict public + 3,653 high-quality local-only | 20,502 review | 2,644 non-strict context | Language confidence, cleanup evidence, and source rights |

The strict public text seed contains 1,188 records. Another 3,653 clean,
high-confidence Garhwali candidates fail only the rights-cleared-source rule and
remain useful for local research. The public Garhwali candidate pool contains
1,818 records in total; 630 do not yet meet the strict quality gate.

## Public-text refinement

The first value-focused pass inspected all 1,818 public Garhwali candidates.
It identified 495 records with concrete review signals and 1,323 without an
additional surface issue:

| Signal | Records | Treatment |
| --- | ---: | --- |
| Romanized text requiring native spelling review | 441 | Preserve spelling; request native review |
| Very short non-lexical fragment | 39 | Verify context before training use |
| Accidental-looking double/repeated punctuation | 14 | Review as possible extraction noise; valid ellipses are exempt |
| Short slash-separated variants | 3 | Review boundaries; long sentences containing slashes are exempt |

Short lexicon forms and digits in numeral lexicons are explicitly exempt from
fragment warnings. Seven release values had unambiguous orphan wiki markup removed,
while their originals remain preserved. The pass resolved 24 HTML-markup, 96 stale
mixed-script, 50 valid short-lexicon, and one stale URL flag. These evidence-backed
resolutions promoted 51 records into the strict tier. No spelling, transliteration,
language, or dialect value was guessed automatically.

## Quality policy

- Preserve original, cleaned, and proposed values independently.
- Never infer Hindi versus Garhwali from shared Devanagari vocabulary alone.
- Never convert district names into dialect labels.
- Never promote a machine transcript to human-reference status.
- Keep mixed-language and cultural-context data active in named, non-strict views.
- Require strong language evidence, clean structure, compatible rights, and no
  active review flags for the strict public tier.

## Next correction order

1. Resolve the 630 non-strict public Garhwali candidates: 616 require source/native
   language validation and 14 high-confidence records retain content anomalies.
2. Resolve the 13 supervised-speech review records before freezing GarhwaliBench.
3. Review the 1,188 risky machine drafts using audio and model disagreement;
   never guess corrections from text alone.
4. Audit the 3,653 high-quality local-only texts source by source for explicit
   redistribution and model-training permission.
5. Sample clean medium-confidence sources for native language validation and
   promote a source only when the evidence supports it.
6. Rebuild tiers, evaluation data, and Hugging Face exports after each accepted
   correction batch.

## Public transparency

The Hugging Face package includes a complete `catalog` configuration for all
27,987 exact-unique text records. Rights-pending records expose their stable hash,
source URL, rights status, language evidence, quality tier, and review reasons.
Only the protected text value is redacted. This makes the full collection visible
and countable without falsely relicensing third-party content. The catalog also
exposes the public-text refinement signals without publishing private source text.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest scripts/test_build_quality_tiers.py
.venv/bin/python scripts/build_quality_tiers.py
PYTHONPATH=scripts .venv/bin/python -m unittest scripts/test_refine_priority_text.py
.venv/bin/python scripts/refine_priority_text.py
```

Generated manifests and reports are under `data/processed/model_ready/quality_v2/`
and `data/processed/model_ready/text_quality_v2/`. They remain Git-ignored with
the other generated datasets.
