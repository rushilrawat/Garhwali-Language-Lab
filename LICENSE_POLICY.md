# Corpus redistribution and model-use policy

This policy separates the complete all-data research package from the public
redistribution profile. The project keeps every acquired record active in the
all-data package, including records with restricted or rights-pending source
terms. Retention does not change the source's
copyright, license, consent scope, or attribution requirements.

The repository code is licensed under MIT by `LICENSE`. That code license does
not license corpus content, source scans, recordings, or generated data.

## Public dataset releases

A record may enter a public dataset only when its source-level provenance shows
one of the following:

1. an explicit license compatible with the release's stated purpose;
2. authoritative public-domain evidence for the relevant edition and jurisdiction;
3. written permission covering redistribution and the intended model use; or
4. contributor consent collected by this project with the same scope.

The public release must preserve source URL, attribution, license identifier and
URL, source checksum, transformation history, language-review status, and any
required share-alike or noncommercial condition. Records with conflicting source
terms take the most restrictive applicable treatment until the conflict is
resolved.

Copyright does not depend on a visible copyright notice. Public accessibility,
indexing, or the absence of an explicit “private” label is not a reuse license.
Short individual facts, names, titles, and words can be represented as facts
when independently verified, while a source's original wording, definitions,
selection, or arrangement may remain protected. A public corpus may not infer
permission from silence; it must record a license, written permission, or
work-specific public-domain basis before redistributing expressive source text.

Some catalog entries may be shared under an upstream CC BY-NC-SA 4.0 grant.
Those rows must carry the exact license and attribution, stay separate from
unrestricted training exports, and be treated as noncommercial/share-alike. A
source-specific reproduction policy is recorded as that policy, not converted
into a Creative Commons license; if commercial use is not expressly addressed,
the row must say so.

Factual and bibliographic projections may include identifiers, names, titles,
dates, categories, and citations while omitting source prose, lyrics, translations,
abstracts, and extended descriptions. This metadata-only treatment is not a
license for the underlying work and does not clear its full text for reuse.

## Complete all-data research package

Historical rights-pending material, public social posts, modern books, podcasts,
and source components without a verified license remain full-value research
inputs. They are included in the complete all-data dataset with their original
source and rights fields. The public redistribution profile filters these rows
unless their source terms are verified. Raw VAANI audio, reference images,
caches, PDFs, and generated datasets remain Git-ignored because GitHub is the
code repository; the dataset package is built separately for Hugging Face.

## Models

Every released model must name the exact dataset release and its use restrictions.
A model trained on restricted, noncommercial, or rights-pending components may
not be represented as unrestricted. TTS additionally requires documented speaker
and voice-modeling consent; a speech-corpus license alone is not treated as
permission to imitate an identifiable voice.

## Review and removal

Native review cannot override copyright or consent, and a license decision cannot
override language-quality review. Both gates must pass independently. A source
owner, contributor, or speaker can submit a removal request using the source or
audio identifier; derived records and future releases must carry the resulting
exclusion while preserving a private audit entry.

The **published v2.1.0 public package** includes all 216 structured knowledge
records as factual or bibliographic metadata and omits their unresolved prose,
lyrics, translations, abstracts, and source passages. It also exposes
source-specific CC BY-NC-SA 4.0 entries, five PIB-policy instrument facts,
193 Mountain Voices headwords under Panos's attributed-reproduction guideline,
and 16 fact-only individual words without definitions, source positions, or
list order. Five of these are corroborated across two thematic lexicons; other
unlicensed list headwords remain local because a one-word rule does not clear
a compilation's selection. This fact-only treatment does not grant a license
to those compilations. Panos's
eligible audiences and attribution rule remain on each row; its terms do not
expressly grant commercial or model-training rights. These condition-bearing
and fact-only values do not enter unrestricted training views. The public
release exposes 12,606 / 32,072 catalog texts; the local all-data package
retains every value, including the 19,466 pending full texts.
The additive v2.1.0 Hugging Face release is at commit
[`53c1ce9`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/53c1ce9baa07e6fb05722e5a1ed750f33096124b). The source-by-source decision log is in
[`research/text-rights-resolution-2026-09-30.md`](research/text-rights-resolution-2026-09-30.md). The latest docs-only Hub amendment is at [`f2def9e`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/f2def9e717390008ebf7aac05decebf1c264fa98); no corpus payload was changed by that amendment.
