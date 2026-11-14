<!--
Hugging Face dataset card template, filled in by build_huggingface_dataset.py.

Each "card:" marker starts a section that runs to the next marker. Leading and
trailing blank lines of a section are ignored. Placeholders use Python format
syntax: {name} inserts a value, {name:,} adds thousands separators.
Do not use literal curly braces in the prose.
-->
<!-- card:main -->
---
language:
{language_header}
license: other
task_categories:
- automatic-speech-recognition
- text-classification
- text-generation
- translation
configs:
{configs_yaml}
{dataset_info_yaml}---

# Garhwali Language Lab

Release: **{release_id}**

{access_notice}
{source_expansion}

## Project history

This release is the result of a staged corpus build, with older releases kept
available under their own versioned paths:

1. **v0.1.x — establish the corpus workflow.** The project began by collecting
   Garhwali text and language references with source attribution, then added a
   reproducible preparation and release pipeline.
2. **v0.2.0 — expand Garhwali-only sources.** A deduplicated source wave added
   671 exact-unique texts, including historical Garhwali specimens and stories.
   Historical OCR and translated stories remain visibly marked as unreviewed.
3. **v0.2.1 — continue the corpus and make it easier to use (30 September–1 October 2026).**
   The follow-up added 164 exact-new strings after deduplication, brought more
   values into the rights-filtered profile under their recorded bases, and
   exposed factual/bibliographic metadata for all 216 structured records. The
   release also adds a consistent rights-and-quality envelope, exact-count
   quick start, schema guide, searchable lexicon example, and linked speech
   dataset. Earlier release files remain available.
{candidate_history}

The figures below describe the current v{release_version} package, not a cumulative sum of
overlapping views. Row-level terms and quality labels remain authoritative.

## Developer quick start

Install the small tabular-data stack with `pip install datasets pandas duckdb`,
then stream three vocabulary entries:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "rushilrawat/garhwali-corpus", "lexicon", split="train", streaming=True
)
for row in lexicon.take(3):
    print(row["form"], row.get("glosses"), row["rights_status"], row["quality_status"])
```

Counts are rows in the current views, not unique examples. Configurations can
overlap, and reference-index rows are not model-training examples. See the
[developer quick start](DEVELOPER_QUICKSTART.md), [schema guide](DATASET_SCHEMA.md),
and [lexicon search script](search_garhwali_lexicon.py) for practical examples.

## Configurations and current row counts

| Configuration | Rows | Use |
| --- | ---: | --- |
{config_table}

{resource_summary}

{draft_summary} {audio_summary}

This dataset card describes data scope, not model accuracy. Native-speaker
review and dialect annotation are deferred; transcripts and machine drafts retain
their review status. The project pipeline uses Python 3.12 and LangGraph for
resumable ingestion; quality checks and model metrics use task-specific scripts.
LangChain is not part of the current pipeline. See the [project README](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/README.md)
and [benchmark research status](https://github.com/rushilrawat/Garhwali-Language-Lab/blob/main/research/benchmark-research-status-2026-09-25.md)
for the latest measured results and limitations.

{catalog_summary}

{text_source_overlap_summary}

{text_expansion_summary}

{text_resources_summary}

{paharili_summary}

The `asr` configuration contains human transcripts from VAANI. The
`sravaani_drafts` configuration contains machine-generated hypotheses from
`ARTPARK-IISc/SraVaani-1.0` revision
`f5dd5358325a5208775b91dad98918e079ea2b27`; these are noisy experimental data,
not human ground truth. Targeted rows also retain their local Whisper alternative,
cross-model agreement, and bounded review-confidence evidence. Draft export
status: **{draft_status}**.

All **{draft_third_checkpoint_records:,}** targeted recordings retain
the third-checkpoint hypothesis. For the **{draft_three_checkpoint_review_records:,}**
Garhwali review records, the package also carries a structurally ranked machine
proposal and its evidence limits. These proposals are pending audio review and
are never represented as automatic corrections or human references.
The remaining **{draft_audio_grounded_review_records:,}** structural
outliers also include deterministic re-decoding, waveform activity, and
human-reference calibration evidence. They still require listening review.

The draft layer also preserves **{draft_source_label_conflicts:,}
source-label conflict recordings**. These remain available for auditing but are
explicitly ineligible for Garhwali training.

To keep Dataset Viewer schemas stable across shards, the SraVaani draft
configuration stores nested evidence objects and draft quality-flag arrays as
compact JSON strings. Parse those columns with a JSON parser; their values are
preserved without flattening or omission.

This package uses multiple upstream licenses. Inspect each row's provenance
before redistribution or model release. Full documentation, limitations, and the
release audit are in the [source repository](https://github.com/rushilrawat/Garhwali-Language-Lab).{speech_companion}

<!-- card:history-0.2.2 -->
4. **v0.2.2 — improve traceability and report usable counts.** The package
   resolves existing social-record IDs to their item URLs, separates source
   references from content rows, reports rights and reuse labels by config, and
   adds a deduplicated `text_expansion` view from already-collected catalog
   values. Earlier files remain available.

<!-- card:history-0.2.3 -->
5. **v0.2.3 — surface additional existing Garhwali resources.** Adds a
   deduplicated, rights-filtered `text_resources` view for catalog text not
   already present in other text-bearing configurations. The view preserves
   row-level rights and quality signals, excludes held-out evaluation source
   records, and is explicitly not an evaluation set or uniformly training-ready.

<!-- card:history-0.2.4 -->
4. **v0.2.2 — improve traceability and report usable counts.** The package
   resolves existing social-record IDs to their item URLs, separates source
   references from content rows, reports rights and reuse labels by config, and
   adds a deduplicated `text_expansion` view from already-collected catalog
   values. Earlier files remain available.
5. **v0.2.3 — surface additional existing Garhwali resources.** Adds a
   deduplicated, rights-filtered `text_resources` view for catalog text not
   already present in other text-bearing configurations. The view preserves
   row-level rights and quality signals, excludes held-out evaluation source
   records, and is explicitly not an evaluation set or uniformly training-ready.
6. **v0.2.4 — improve source attribution and revision traceability.** Recovers
   creator attribution for 36 existing Tatoeba sentences and adds immutable
   page-revision/history links for 319 existing Wikimedia and Wiktionary
   records. No new text is added; source text, release eligibility, and review
   status are not promoted by this metadata update.

<!-- card:history-0.2.5 -->
4. **v0.2.2 — improve traceability and report usable counts.** Resolves existing
   social-record IDs to item URLs, separates source references from content,
   and adds a deduplicated `text_expansion` view from collected catalog values.
5. **v0.2.3 — surface existing Garhwali resources.** Adds a deduplicated,
   rights-filtered `text_resources` view with row-level source and quality data.
6. **v0.2.4 — improve source attribution and revision traceability.** Recovers
   creator attribution for 36 Tatoeba sentences and immutable history links for
   319 Wikimedia/Wiktionary records. It adds no source text.
7. **v0.2.5 — prevent upstream evaluation-source overlap in default train.**
   Keeps all records but routes text linked to upstream Meta/VAANI development
   or test sources into an explicit `source_overlap` split. The split audit and
   evidence IDs are included with the release.

<!-- card:all-data-resources -->
Versioned Garhwali (`gbm`) text, speech, lexicon,
instructions, geography, historical terms, literature, music, and university-
research resources built by the Garhwali Language Lab. Available source, rights,
and review metadata vary by configuration.

<!-- card:all-data-catalog -->
The `catalog` configuration contains all
**{catalog_records:,} exact-unique collected text records with their full
text values. No catalog text values are redacted. Source, license, rights status,
quality tier, language evidence, and review state remain attached to every row so
research use and any later redistribution decision can be audited.

<!-- card:all-data-access -->
> **Access warning:** this all-data profile contains
restricted and rights-pending source content. Keep it local or access-controlled;
do not publish it as an open dataset until every included component is cleared.
It retains all structured records with row-level source, quality, and rights
metadata attached.

<!-- card:public-speech-companion -->
## Linked speech dataset

The companion [Garhwali Speech dataset](https://huggingface.co/datasets/rushilrawat/garhwali-speech) contains VAANI audio with provider transcripts and separately labeled SraVaani drafts.

<!-- card:public-resources -->
This public profile contains Garhwali
text, human transcripts, lexicon and instructions, plus experimental SraVaani
drafts. The geography, history, literature, song, and university-research
configurations contain factual and bibliographic metadata, with expressive
notes, lyrics, summaries, and source passages omitted.

<!-- card:public-catalog -->
The `catalog` configuration publicly accounts for all
**{catalog_records:,} exact-unique collected text records**. Rows whose
source terms do not permit redistribution retain their stable content hash,
source URL, rights status, quality tier, language evidence, and review reasons;
their full text is not included in public content. The current catalog exposes **{catalog_noncommercial_records:,}** CC BY-NC-SA 4.0 records,
**{catalog_sharealike_records:,}** total share-alike records, and
**{catalog_source_policy_records:,}** entries under source-specific reproduction policies (5 PIB instrument facts and 193 Mountain Voices glossary headwords), plus **{catalog_factual_word_records:,}** exact one-token facts published without definitions, source record positions, or list arrangement. The fact-only projection includes individually selected tokens and lexical tokens that appear in at least two distinct thematic source collections; it is not a copy of any source list. The Panos guideline permits attributed reproduction by press, educational/research institutions, and nonprofits; commercial scope and machine-learning training are not expressly addressed, so these headwords are excluded from model-training views. Per-row terms apply; the package asserts no blanket content license.

<!-- card:public-access -->
All **{metadata_only_records:,} structured geography, history, literature, song, and research records** appear in factual/bibliographic form; no records are dropped from these metadata configurations. Prose notes, lyrics, translations, abstracts, and source passages are omitted unless separately licensed. For retained catalog entries, the full text not included in this public profile remains in the local all-data package; entries whose source text was not acquired remain represented by their available source metadata. Each text-catalog record carries its specific rights state: CC BY-SA rows require attribution and share-alike; CC BY-NC-SA rows are noncommercial and share-alike; the five PIB instrument terms cite the PIB reproduction policy; and the 193 Mountain Voices glossary headwords carry Panos's attributed-reproduction guideline for press, educational/research institutions, and nonprofits. That guideline does not expressly address commercial scope or model training, so those values are excluded from model-training views. The **{catalog_factual_word_records:,}** isolated one-token facts are listed without definitions, source record positions, or list ordering. Lexical facts from unlicensed thematic sources are included only when independently present in at least two distinct source collections; all such facts remain catalog-only, outside training views, and retain language-review flags. See the [source-by-source rights-resolution log](research/text-rights-resolution-2026-09-30.md). Native-speaker review and dialect annotation are deferred; benchmark and model scores are automated research results, not native-validated claims.

<!-- card:text-expansion -->
## Fast-tracked text expansion

The `text_expansion` config adds **{expansion_records:,}** Garhwali candidate texts from the existing catalog. Each passed automated strict-tier and recorded rights-basis checks, is absent from the existing text splits after NFKC/alphanumeric normalization, and has no source-record ID matching existing text validation/test or frozen benchmark validation/test rows. **{expansion_source_overlap_records:,}** values with upstream Meta or VAANI development/test source matches remain published in the `source_overlap` split, outside default `train`. The values remain machine-screened, not native-reviewed. **{expansion_recommended:,}** currently meet the project's conservative training-recommendation rule; **{expansion_not_recommended:,}** do not pass the current source-eligibility or quality gates. This is not training approval; source-page-family isolation is not assessed, so it is not an independent evaluation set. Values also appear in the `catalog` inventory by design; do not add config row counts when reporting unique texts.

<!-- card:text-resources -->
## Supplementary text resources

The `text_resources` config adds **{resource_records:,}** additional normalized-unique Garhwali records ({resource_words:,} whitespace-delimited words; {resource_characters:,} characters) already present in the source catalog. These pass the recorded redistribution-basis and Garhwali-language filters and are absent from the existing text-bearing views after normalized deduplication. Their quality tiers vary; **{resource_recommended:,}** are currently recommended for training and none are recommended for evaluation. The config is intended for lookup and research. Check each row's `redistribution_status`, license, quality flags, and source terms before reuse. CC BY-NC-SA rows are limited to noncommercial use and require share-alike; this subset is not uniformly training-ready or a native-reviewed text set.

<!-- card:paharili -->
## PahariLI Garhwali text addition

The new `paharili_gbm` config adds **{paharili_new_records:,} normalized-unique Garhwali-labeled sentence records** from the [PahariLI corpus](https://github.com/rachanagusain/PahariLI). It starts from {paharili_source_records:,} upstream GBM-labeled rows, which reduce to {paharili_unique_texts:,} distinct normalized texts after collapsing {paharili_collapsed_records:,} repeated source rows. All source record IDs and surface variants are retained: {paharili_new_source_ids:,} source IDs appear in this config, and {paharili_existing_source_ids:,} remain on the exact-matching row already in `text_expansion`. That existing text is not duplicated here.

The config keeps the upstream language-identification splits: {paharili_train:,} train, {paharili_test:,} test, and {paharili_source_overlap:,} text groups that occur in both upstream splits. The last group stays in `source_overlap` to avoid train/test leakage. This test split is the upstream PahariLI classification split; it is not an independent evaluation set for the project's language model or other tasks.

The PahariLI repository includes an Apache-2.0 license file, but its README does not identify the sentence-level source of each item. Each row therefore keeps the repository-level license declaration, raw-file URL and SHA-256, source index, attribution, and the existing `source_lineage_missing`, `component_rights_review_required`, and possible scripture/blog flags. The release makes no claim that Apache-2.0 independently clears underlying source text. Rows are unreviewed and not recommended for general language-model training; the upstream `train` partition remains usable for experimental language-identification work. The upstream license text is included at `licenses/PahariLI-Apache-2.0.txt`.

<!-- card:source-overlap -->
## Upstream source-split overlap

The text package preserves every row. The `text/source_overlap` split contains **{text_source_overlap_records:,}** rows previously assigned to `text/train` that carry a Meta dev/test record ID, an official VAANI test-remainder source record, or a transcript match to held-out Meta/VAANI source material. The `text_expansion/source_overlap` split contains **{expansion_source_overlap_records:,}** similar catalog additions. These rows remain downloadable and retain their source metadata, but are kept outside the default train split. This is a conservative source-lineage warning, not a claim that all matched audio recordings are identical. See the [split-overlap audit]({overlap_audit_url}).

<!-- card:additions-0.2.1 -->
## Garhwali source additions included in v0.2.1

- **Jambu Garhwali reflex lexicon:** {jambu_source_records:,} source rows and
  {jambu_unique_forms:,} distinct forms. This source was already in the
  preceding local corpus snapshot; the v0.2.1 refresh revalidates its pinned local
  snapshot and adds **{jambu_new_forms:,}**
  new forms (the current snapshot already contains {jambu_already_in_corpus:,}).
  Its earlier intake comparison found {jambu_cross_source_overlap:,}
  forms shared with other sources and {jambu_new_vs_other_sources:,}
  forms absent from those sources. It is an attributed CC BY 4.0 lexical source,
  not conversational text, and remains unreviewed by native speakers.
- **Garhwali Language Library 1.0.0:** {library_source_records:,} pinned static
  word, phrase, proverb, and riddle entries; {library_unique_strings:,}
  distinct strings, {library_cross_source_overlap:,} exact overlaps with
  the existing corpus, and {library_new_vs_current_corpus:,} exact-new
  strings. Types: {library_type_counts}. The static files are attributed under MIT;
  generated inflection forms are excluded and are not counted as corpus examples.

Both additions retain their upstream spellings, provenance, license and review
state. Exact matches keep source attribution without counting again as new text.
The public profile includes a row only when its rights filter passes. Neither
source entry has received native-speaker review or been promoted into
recommended training splits.

<!-- card:additions-0.2.0 -->
## Garhwali-only additions in v0.2.0

This release adds **671 exact-unique source texts** after normalization and
cross-corpus deduplication (696 source rows; 673 unique values within this
intake, including two exact matches already held in earlier layers):

- 632 Garhwali entries from the dialect-comparison table in the
  [Linguistic Survey of India, Vol. IX, Part IV](https://archive.org/details/LSIV0-V11),
  representing 609 exact-unique forms explicitly tagged Standard, Rathi, or
  Tehri. 496 table rows have OCR confidence below 60/100; all OCR remains
  machine-produced and unreviewed.
- Nine Devanagari Garhwali language specimens from the same historical volume.
  These are source-grounded OCR excerpts, not modern conversational speech.
- Five sayings explicitly identified as Garhwali in Upreti's 1894
  [*Proverbs & Folklore of Kumaun and Garhwal*](https://archive.org/details/cu31924089930774).
- Fifty Garhwali Open Bible Stories from the pinned
  [Door43 OBS-TLF source](https://git.door43.org/OBS-TLF/gbm_obs), revision
  `f08afc73e1770129fbcd3089181f2faf2abbf54d`, licensed CC BY-SA 4.0.

The historical excerpts use a recorded Public Domain Mark basis; each story
retains the upstream attribution and CC BY-SA terms. The corpus rows preserve
page, source revision or checksum, rights, script/language evidence, and quality
status. The OCR and translated stories have not received native-speaker review.
For the public profile, only rows passing the project's rights filter carry
full text; the all-data package retains every collected value locally.
