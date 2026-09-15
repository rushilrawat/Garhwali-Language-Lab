# Intensive quality audit

## Outcome

The intensive quality gate covers all **27,986 exact-unique text records**,
**5,894 human-transcribed speech records**, and **104,542 SraVaani machine
drafts**. Original linguistic values remain immutable; release values contain only
bounded mechanical normalization. Every tier includes explicit reasons, so later
corrections remain reversible and auditable.

## Findings

| Dataset | Strict/high-quality | Experimental/review | Context | Main risk |
| --- | ---: | ---: | ---: | --- |
| Human-transcribed speech | 5,881 strict candidates | 13 review | 0 | Existing transcript/training flags |
| SraVaani machine drafts | 103,354 experimental | 1,090 three-checkpoint review records | 98 source-label conflicts | 325 clean related-checkpoint consensus proposals, 730 clean low-consensus proposals, and 35 machine-audio-reviewed outliers pending listening |
| Text | 3,559 strict public + 1,748 high-quality rights-pending | 20,034 review | 2,645 non-strict context | Language confidence, cleanup evidence, and source rights |

The strict public text seed now contains 3,559 records. Another 1,748 clean,
high-confidence Garhwali candidates fail only the rights-cleared-source rule and
remain represented in the public catalog with protected text values redacted. The
public Garhwali candidate pool contains 3,735 records in total; 176 require native
or source-level validation before entering the strict tier.

## Public-text refinement

The value-focused pass inspected all 3,735 public Garhwali candidates. After the
source-grounded extraction corrections, it identifies 14 records with concrete
surface signals and 3,721 without an additional surface issue:

| Signal | Records | Treatment |
| --- | ---: | --- |
| Romanized text requiring native spelling review | 4 | Preserve spelling; request native review |
| Very short non-lexical fragment | 8 | Verify context before training use |
| Short slash-separated variants | 2 | Review boundaries; long sentences containing slashes are exempt |

Short lexicon forms and digits in numeral lexicons are explicitly exempt from
fragment warnings. Seven release values had unambiguous orphan wiki markup removed,
and 29 prompted-speech values had exact double-period pause markers normalized to
the Unicode ellipsis; all originals remain preserved. The pass resolved 26 HTML
markup, 98 stale mixed-script, 402 Romanized `no_devanagari`, 51 valid short-lexicon,
and one stale URL flag. Structured Wiktionary/Wikimedia extraction and explicit
scholarly transcription evidence then removed obsolete review reasons, while the
source-rights audit raised the strict total through exact matches to separately
licensed sources. No spelling, transliteration, language, or dialect value was
guessed automatically.

## Evidence dimensions and review order

The 176 unresolved public candidates now have separate evidence for language
identity, orthography, semantic alignment, source reliability, and surface form.
The queue is deterministic and contains each stable text identity once:

| Priority | Records | Reason |
| --- | ---: | --- |
| Surface or source scaffolding | 9 | Short fragments, variant boundaries, or remaining flags |
| Source accuracy | 163 | Native accuracy or community review is explicitly unresolved |
| Romanized orthography | 4 | Source form is valid data but spelling has not been natively reviewed |

These labels describe available evidence and the next review action. They are not
accuracy probabilities. Multiple-source occurrence is recorded as corroboration
evidence but never treated as proof that a value is correct.

## Supervised-speech triage

All 13 non-strict human-transcribed rows were inspected. Eight contain Bengali
script and are consistently marked as source-label conflicts in the original,
training, and transcript review fields. They remain preserved but excluded from
Garhwali supervised training. The other five contain Devanagari Garhwali
candidates with incomplete wording, unbalanced annotation characters, or unclear
phonetic spelling. Both local human-trained Garhwali Whisper checkpoints were run
on all five clips. The models disagreed with each other and with the full reference
in every case, so their hypotheses are retained as evidence and never substituted
for human text. Two release proposals remove a single unmatched opening parenthesis;
the immutable references remain unchanged. All five still require listening review.
No supervised row was silently removed or promoted.

## Cross-layer source conflict

All eight Bengali-script human transcripts and 98 Bengali-script machine drafts
map to the same stable VAANI source speaker key, `Uttarkashi:98459`. Every human
transcript and every machine draft observed for that key uses Bengali script, and
the source metadata lists Bengali among the speaker's known languages. The 106
records are preserved with a source-label-conflict status. The 98 machine drafts
remain in the public dataset for auditing but are excluded from Garhwali training
loss. This is a source-scope decision, not a claim that script alone proves the
audio language.

## Quality policy

- Preserve original, cleaned, and proposed values independently.
- Never infer Hindi versus Garhwali from shared Devanagari vocabulary alone.
- Never convert district names into dialect labels.
- Never promote a machine transcript to human-reference status.
- Keep mixed-language and cultural-context data active in named, non-strict views.
- Require strong language evidence, clean structure, compatible rights, and no
  active review flags for the strict public tier.

## Next correction order

1. Validate the ranked 176-record public queue by source and native review.
2. Listen-review the five ambiguous supervised transcripts; retain the eight
   Bengali-script source-label conflicts as excluded evidence.
3. Listening-review the 35 machine-audio-reviewed outliers: 11 common short-form
   spot checks, 17 decoder loops, three decoding corruptions, one empty output,
   and three other unresolved records. Never treat model agreement as a human
   reference.
4. Continue permission work for the 1,748 high-quality texts that remain
   rights-pending after the completed source-level audit.
5. Sample clean medium-confidence sources for native language validation and
   promote a source only when the evidence supports it.
6. Rebuild tiers, evaluation data, and Hugging Face exports after each accepted
   correction batch.

## Public transparency

The Hugging Face package includes a complete `catalog` configuration for all
27,986 exact-unique text records. Of these, 4,195 have a public rights basis and
23,791 remain rights-pending. Pending records expose their stable hash,
source URL, rights status, language evidence, quality tier, and review reasons.
Only the protected text value is redacted. This makes the full collection visible
and countable without falsely relicensing third-party content. The catalog also
exposes the public-text refinement signals without publishing private source text.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python -m unittest scripts/test_refine_priority_text.py
PYTHONPATH=scripts .venv/bin/python scripts/refine_priority_text.py
PYTHONPATH=scripts .venv/bin/python -m unittest scripts/test_build_quality_tiers.py
PYTHONPATH=scripts .venv/bin/python scripts/build_quality_tiers.py
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/redecode_supervised_review.py
.venv/bin/python scripts/build_huggingface_dataset.py
.venv/bin/python scripts/audit_final_release.py
```

Generated manifests and reports are under `data/processed/model_ready/quality_v2/`
and `data/processed/model_ready/text_quality_v2/`. They remain Git-ignored with
the other generated datasets.
