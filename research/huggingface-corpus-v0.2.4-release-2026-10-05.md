# Hugging Face corpus release v0.2.4 — 2026-10-05

## Release result

The public [`rushilrawat/garhwali-corpus`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus)
repo now points to latest card correction commit
[`574aa66`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/574aa667a2486948444d28ff533c668ada3178e2).
The 48-path v0.2.4 package (47 files under `releases/v0.2.4/` plus the root
dataset card) was first published at
[`76b93dc`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76b93dc0f35aca444ba06dfcab186fb7ca5106d1).
The documentation-only follow-up at
[`32844de`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/32844de7cdd7d3632a11331cb1adc05b67a8be0c)
corrected the root card, versioned card, and developer quick-start. The later
card-only correction at `574aa66` made the text-expansion training status
unambiguous and clarified the local all-data statement; it changed the two
card copies only. Neither follow-up changed data shards or record values. The
current v0.2.4 package plus root card totals **815,702,453** logical bytes; the
complete repository contains 297 files totaling **4,889,314,595** logical
bytes across retained releases. All prior release paths remain; no delete
operation was included.

The content/config view still contains 164,387 rows across 14 configurations
and 20 config/split views. The three source-reference tables add 663,063 rows;
the package therefore contains 827,450 overlapping view rows, not that many
unique language records. The catalog has 32,072 records. Its public content
projection includes 12,606 values under their recorded terms or narrow
fact-only basis; 19,466 full text values remain outside public text content
while their source records and rights state remain in the catalog. The
separate speech repo is unchanged.

## What changed

This is a provenance and eligibility correction, not a new-text release.
Relative to the local v0.2.3 package, every content-record identity and text
value is unchanged: zero content IDs were added or removed, and zero text
values changed. The package adds source-specific attribution and immutable
revision/history links for 355 existing records: 36 Tatoeba sentences and 319
Wikimedia/Wiktionary records. The Tatoeba contributor attribution was
recovered as `sabretou`; the API reports all 36 sentences as orphaned. Their
unreviewed status and training ineligibility remain explicit. The metadata
overlay is content-free and has SHA-256
`3bbacd69ef5a5ba86af5bc89600d579574e6e14315ab18e8b0a14f33a1063484`.

The text-training recommendation now respects explicit source eligibility
and excludes any row whose declared split is not `train`. In the current
public `text`, `text_expansion`, and `text_resources` views, zero rows pass the
recommendation rule. This label is a conservative project rule; it does not
assert that the source text is linguistically poor, nor does it replace the
source-specific license fields.

## Validation and access check

- Full unittest discovery: **774/774 passed**.
- Independent public and local all-data package preflights: passed with zero
  errors; both report zero deleted or mutated records.
- Old/new comparison of every content identity and text field: identical.
- Remote upload-plan reconciliation: all 47 versioned v0.2.4 files and the
  root card are present; the package data hashes match the original upload,
  and prior v0.2.3 paths remain. The latest correction changes only the two
  card copies; the developer quick-start is at `32844de`.
- `datasets.load_dataset(..., streaming=True)` successfully opened the live
  `text` and `lexicon` train configs and read one row from each. No complete
  split was downloaded for this check.
- After the `32844de` update, Dataset Viewer `/is-valid`, `/splits`, `/parquet`,
  and `/rows` returned HTTP 200. Immediately after the later card-only `574aa66`
  update, all four returned a transient HTTP 500 busy response; the new card
  is in the repo tree, and Viewer re-indexing must be checked again. This
  service-side rendering issue does not affect the retained data files.
- A source-level eligibility audit recomputed all 20,842 rows across `text`,
  `text_expansion`, and `text_resources`: zero recommendation mismatches and
  zero currently recommended training rows. It identifies explicit source
  flags, quality flags, and missing public-rights bases by source. A
  diagnostic-only simulation (not a rights decision) finds 2,956 core train
  and 606 expansion rows would pass other current gates if explicit source
  training flags were resolved; no flags were changed. See the
  [eligibility audit](huggingface-training-eligibility-audit-2026-10-05.md).

The successful Hub upload and direct streaming check verify file availability;
they do not imply that every row is correct Garhwali, training-eligible,
commercially reusable, independently evaluative, or native-speaker reviewed.
No new source texts were ingested, and no model accuracy claim changed.

## Next roadmap action

Continue Phase 2 of the [Hugging Face dataset quality roadmap](huggingface-dataset-quality-roadmap.md):
review the ranked source families against primary source terms and their
component lineage, then record redistribution, research, training, commercial,
attribution, and unresolved-quality decisions separately. Do not turn the
diagnostic counts into eligibility decisions. Dataset Viewer and Parquet
checks are currently healthy.
