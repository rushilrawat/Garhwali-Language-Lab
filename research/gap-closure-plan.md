# Garhwali data gap-closure plan

Updated 2026-09-09. This plan separates access work, rights work, digitization,
community collection and quality review. A source enters the training pool only
after its provenance, rights, language identity and quality checks pass.

## Priority 1: validate and prepare the licensed VAANI data

Project VAANI now states that its dataset is CC BY 4.0 and hosted on Hugging
Face. The access form/contact-sharing gate is an account action rather than an
unclear-license problem.

1. The project owner signs in to Hugging Face and accepts access for
   `ARTPARK-IISc/Vaani` and `ARTPARK-IISc/Vaani-transcription-part`.
2. Store the Hugging Face credential in the local credential manager or
   `HF_TOKEN`; never commit it.
3. Download the Garhwali metadata and transcription subset first. Reconcile
   the official 5,894 rows against the 5,893-row community mirror by stable
   file or utterance ID.
4. Preserve official train/validation/test splits. Keep all evaluation rows
   out of training.
5. Download audio only after the manifest is validated. Verify checksums,
   duration, district, speaker identifiers and consent fields.
6. Add a VAANI-specific attribution file and keep the original row IDs.

This is the highest-yield next action: up to 136.80 hours of Garhwali audio and
8.80 transcribed hours are already known from the saved Garhwali configuration.

## Priority 2: obtain a licensed HimLingo export

HimLingo explicitly prohibits scraping or copying without permission. Its
contributors retain ownership while granting HimLingo a platform license, so
permission from the platform alone may not be sufficient to relicense every
contribution.

Ask HimLingo for:

- a structured Garhwali-only export;
- word, gloss, example, dialect, contributor and moderation fields;
- an explicit CC BY 4.0 or CC0 dataset license;
- confirmation that contributor terms permit that sublicense;
- separate consent and license fields for pronunciation audio;
- a stable version identifier and attribution instructions.

If existing contributor terms cannot support an open export, collaborate on a
new opt-in release: contributors explicitly approve their entries and audio
under the chosen dataset license.

## Priority 3: enumerate digital-library holdings

### Kumauni Archives

Use the Garhwali language filter and enumerate item metadata first. For every
result record title, author, year, language, genre, stable URL, file access,
rights statement and checksum. Download text or scans only when the item is
public domain, openly licensed or permissioned. Treat the archive's take-down
policy as an access policy, not automatically as a reuse license.

### Lucknow Digital Library

Open the item page for each Garhwali result and distinguish a catalogue record
from an accessible scan. Establish author death date, publication date, edition
and scan rights. Older scholarship about Garhwali can provide research context
without necessarily containing Garhwali training text.

### Historical *Garhwali* periodical

The located catalogue reports microfilm holdings from 1916–1926 with gaps.
Request:

- reel and issue inventory;
- digitization or reading-room access;
- scan reproduction conditions;
- publication and editor metadata;
- permission to redistribute OCR and corrected transcriptions.

After access, segment by issue, page, article and language. Record author names
because public-domain status may differ by contribution.

## Priority 4: process local PDFs

Place each PDF in `incoming/pdfs/` with the metadata sidecar described in that
folder's README. The pipeline should then:

1. hash and identify the edition;
2. check for an existing duplicate scan;
3. render and OCR page by page;
4. preserve original OCR and corrected text separately;
5. classify Garhwali, Hindi, Kumaoni and English passages;
6. attach page, work, author and rights provenance;
7. send uncertain lines to native review.

Best first PDFs are dictionaries, grammars, primers, early periodicals and
folk collections with clear rights. A scan being downloadable is not itself a
reuse license.

## Priority 5: build missing data with speakers

Web collection alone will not fix dialect or conversational gaps. Run a
consented community collection covering districts, age groups, genders and
speaking contexts.

Collect three linked products:

- thematic lexicon: word, Hindi/English gloss, dialect, example sentence and
  pronunciation;
- prompted speech: balanced prompts for daily life, agriculture, ecology,
  kinship, health, directions, numbers and local culture;
- natural speech: stories, conversations and procedural explanations with
  speaker and third-party privacy review.

Each contribution needs a participant ID, district/dialect, recording date,
consent version, allowed uses, withdrawal process and chosen license. Do not
collect names, phone numbers or unrelated personal details in the public data.

## Native-review workflow

Reviewers should see one item at a time and record:

- accept, correct, reject or uncertain;
- corrected Garhwali spelling;
- meaning and natural example;
- district/dialect and alternative forms;
- whether the form is Garhwali, shared regional Hindi or another language;
- reviewer ID and timestamp.

Require two independent reviews for dictionary entries and evaluation data.
Resolve disagreements with a third reviewer instead of collapsing dialect
variants. Freeze a held-out evaluation set before using reviewed text for
training.

## Practical milestones

1. **Access milestone achieved (2026-09-09):** official VAANI manifests acquired and reconciled; see `research/vaani-audit-2026-09-09.md`.
2. **Lexicon milestone:** 5,000 native-reviewed concepts/forms with dialect and
   example fields.
3. **Text milestone:** 50,000 clean, rights-cleared Garhwali sentences spanning
   conversational, informational and literary genres.
4. **Speech milestone:** at least 25–50 transcribed hours balanced across major
   districts and speaker groups, plus a separate immutable test set.
5. **Release milestone:** dataset card, consent statement, source manifest,
   license matrix, deduplication report and documented exclusions.

## Decisions requiring the project owner

- Accept the VAANI/Hugging Face access conditions using the owner's account.
- Choose the intended public dataset license and whether commercial model use
  is allowed.
- Send partnership and archive requests in the owner's name.
- Recruit native speakers and approve compensation and consent language.
