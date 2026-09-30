# Garhwali web goldmine intake — 2026-09-30

## Result

The tenth ingestion wave scanned **6,844 public Blogger feed entries** from
[Uttarakhand e-Magazine](https://e-magazineofuttarakhand.blogspot.com/) and
retrieved two source-labelled short-story pages at Uttarakhand Khabar Saar:
[Jani Mayedi Tani Jayedi](https://uttarakhandkhabarsaar.in/jani-mayedi-tani-jayedi-a-garhwali-short-story/)
and [Khuded Bhajed](https://uttarakhandkhabarsaar.in/khuded-bhajed-a-garhwali-short-story/).
The deterministic title/URL filter selected 1,816 Blogger pages and the two
story pages. Exact text comparison skipped **46 duplicate rows** (35 duplicate
text groups), leaving **1,772 exact-new page records / 6,758,808 source
characters**: 1,770 e-Magazine pages and two short-story pages.

These are useful discovery and language-data candidates, not 1,772 verified
Garhwali utterances. A page title, regional keyword, or source label is not
proof that the full page is in Garhwali. The current automatic language pass
places the records in low-confidence or unverified categories:

| Automated bucket | Records | Interpretation |
| --- | ---: | --- |
| Mixed-script review | 1,147 | Mixed Devanagari/Latin surface; language identity unresolved |
| Romanized Garhwali candidate | 543 | Romanized candidate; no native confirmation |
| Garhwali scope unverified | 82 | The page/title points to Garhwali, but text identity is unconfirmed |
| **Total** | **1,772** | Candidate records only; no native review performed |

## Corpus integration and figures

The new rows are retained in `experimental/garhwali_web_goldmines.jsonl`, which
is Git-ignored, and flow through the ordinary canonicalization pipeline. The
local text pipeline now reports **33,562 source rows from 47 files**, **31,198
exact-unique parent texts**, **16,084,744 characters**, and **150,814
exact-unique text segments** (162,169 segment occurrences). It reports zero
cross-split exact-segment leakage. Relative to the frozen v0.2.0 snapshot,
this local working tree has 1,772 more unique parent texts, 6,758,808 more
source characters, and 35,029 more exact-unique segments.

The source rows remain active in the experimental all-data view and the local
all-data package preview. The current quality tiers do not put them in the
recommended rights-cleared training view. No full text from this wave was
added to the public Hugging Face content profile; the remote v0.2.0 dataset is
unchanged. The local public-profile catalog preserves source/provenance
references while redacting the text. The local all-data package preview is
labelled `v0.2.1-dev`; it is not an uploaded release.

The rebuilt local `v0.2.1-dev` previews contain **297,000 all-data rows**
across overlapping views and **151,812 public-profile package rows**, of which
125,475 carry public-profile content. The complete reference index contains
297,000 metadata-only row references, 4,144 source entries, and 324,338
record/source links. All 1,772 new candidate texts are redacted in the public
profile and preserved in the all-data preview. Across the complete text
inventory, automated tiering reports 3,616 strict candidates, 21,189
experimental-review rows, 1,750 high-quality rights-pending rows, and 4,643
non-strict context rows; strict-candidate status is an automated filter, not a
native-speaker quality certification.

## Rights, quality, and use

The Blogger and story pages do not provide a verified open dataset license for
the collected full text. All 1,772 records therefore carry
`rights_status=rights_unassessed`, `training_eligible=false`,
`experimental_training_eligible=true`, and an experimental corpus layer.
They may be used in local exploratory work under the project's all-data
policy, but the rights status is not resolved by web accessibility. Do not
describe them as rights-cleared or publish their full text as an open dataset.

The intake preserves the page URL, title, author/attribution where exposed,
retrieval timestamp, page snapshot hash, text hash, extraction version, and
quality flags. It does not rewrite source spelling. Exact duplicate strings
were not added as new canonical text, while their distinct provenance remains
available where already captured.

## Repeatable commands

```bash
.venv/bin/python scripts/ingestion_graph.py run \
  --wave tenth --run-id garhwali-web-YYYY-MM-DD
.venv/bin/python scripts/refresh_corpus_after_ingestion.py
```

The graph performs source acquisition, extraction, exact deduplication, and
verification. The refresh command rebuilds the derived text, language,
segment, split, benchmark, instruction, quality, and local package views,
then regenerates the current metrics block in `README.md`. It stops on the
first failing stage and never uploads to Hugging Face. Raw snapshots, extracted
candidate text, generated manifests, and metrics remain under Git-ignored
data paths.

The source-specific implementation is `scripts/ingest_web_goldmines.py`; the
wave is registered in `scripts/collect_online.py` and
`scripts/ingestion_graph.py`. Its bounded-fetch, robots, deduplication, and
completeness checks are covered by `tests/test_ingest_web_goldmines.py` and
`tests/test_ingestion_graph.py`. The full post-ingestion working-tree suites
passed **635/635 pytest** and **633/633 unittest** tests.
