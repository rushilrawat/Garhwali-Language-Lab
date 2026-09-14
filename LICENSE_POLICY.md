# Corpus redistribution and model-use policy

This policy separates local research retention from public redistribution. The
project keeps every acquired record in its active experimental layer, including
restricted and rights-pending material. Retention does not change the source's
copyright, license, consent scope, or attribution requirements.

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

## Local research layers

`restricted/`, `experimental/`, historical rights-pending material, public social
posts, modern books, podcasts, and source components without a verified license
remain local research inputs. They may be analyzed in the complete experimental
view but are excluded from public dataset payloads and public model-training
claims. Raw VAANI audio, reference images, caches, PDFs, and generated datasets
remain Git-ignored.

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

The public `v0.1.0` release contains only the rights-filtered Hugging Face export.
Evaluation rows and pronunciation/TTS resources retain optional native-review
metadata. This release does not grant redistribution rights for the complete
local corpus.
