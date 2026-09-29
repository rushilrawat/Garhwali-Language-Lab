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

The locally generated public profile contains only records with an explicit
compatible rights basis. It excludes 216 structured knowledge records until
source-specific reuse evidence is recorded. The complete all-data profile keeps
those values and their original source terms together and must remain private or
access-controlled. The public profile's exclusion passes its automated rights
gate; it does not clear the omitted records for redistribution. The current
release review is in [`finalreport.md`](finalreport.md).
