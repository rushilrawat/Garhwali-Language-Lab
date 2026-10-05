# Upstream development/test text overlap audit — 2026-10-05

## Finding

The v0.2.4 text export used project-level `train` splits, but some rows carry
source records from upstream Meta development/test splits. The train-only
`grushaaaaa/indic-dialect-asr` aggregation also contains transcripts that can be
matched to held-out Meta or VAANI material. Leaving these records under the
default `train` name makes the source split history easy to miss.

The v0.2.5 build routes the affected content into an explicit `source_overlap`
split. It does not remove or redact text. Rows retain their IDs, text,
provenance, rights fields, and original split field; the generated rows record
`source_split_overlap_status` and the matching source IDs. Every moved row is
marked `recommended_for_training: false`.

## Evidence and method

The audit joins the local VAANI and Meta transcript manifests to the
7,823 Garhwali rows extracted from `grushaaaaa/indic-dialect-asr`. It also
checks the exact Meta source record IDs already attached to public text rows.
The content-free crosswalk and input hashes are in
[`huggingface-upstream-split-overlap-2026-10-05.json`](huggingface-upstream-split-overlap-2026-10-05.json).

| Source snapshot | Local rows | Split counts |
| --- | ---: | --- |
| `facebook/omnilingual-asr-corpus`, Garhwali manifest | 2,927 | train 2,329; dev 298; test 300 |
| VAANI canonical supervised manifest | 5,894 | train 5,891; validation 1; test 2 |
| `grushaaaaa/indic-dialect-asr`, Garhwali extract | 7,823 | 1,930 Meta-declared; 3,999 VAANI Tehri; 1,894 VAANI Uttarkashi; the aggregator exposes these in `train` |

Matching uses NFKC normalization, case-folding, and removal of non-alphanumeric
characters, the same conservative key used by the release deduplicator. This
can produce candidate matches across punctuation variants. A text match does
not prove that two audio recordings are identical.

Of the 7,823 aggregator rows, 35 have text matching an upstream held-out split:

| Upstream component | Match | Rows | Evidence strength |
| --- | --- | ---: | --- |
| Meta | dev and train | 28 | Repeated text; aggregator audio/source-record identity is ambiguous |
| Meta | test and train | 4 | Repeated text; aggregator audio/source-record identity is ambiguous |
| VAANI | test | 2 | One matching manifest row per transcript |
| VAANI | validation | 1 | One matching manifest row |

The other 1,898 Meta matches map to train-only text in the local Meta manifest;
5,890 VAANI matches map to train-only rows. Seventeen aggregator rows do not
map to the local source manifests. They remain experimental and are not
promoted by this audit.

Separately, 598 exact Meta source record IDs in the local manifest belong to dev
or test. Matching those IDs in package provenance avoids relying on text
similarity when the record identity is already present.

## v0.2.4 package impact and v0.2.5 routing

The public v0.2.4 text package contained these train rows linked to upstream
held-out material:

| Config | Direct upstream held-out record IDs | Aggregator text matches | Unique rows moved |
| --- | ---: | ---: | ---: |
| `text` | 1,304 | 81 | **1,308** |
| `text_expansion` | 363 | 20 | **363** |
| `text_resources` | 0 | 0 | **0** |

Some rows appear in both evidence columns; the unique-row column is the union.
The v0.2.5 package therefore has:

- `text/train`: 15,981 rows, plus 1,308 in `text/source_overlap`; validation
  remains 895 and test remains 765. Total text rows stay at 18,949.
- `text_expansion/train`: 1,284 rows, plus 363 in
  `text_expansion/source_overlap`. Total expansion rows stay at 1,647.
- `text_resources/train`: all 246 rows; none matched the audited source
  development/test IDs.

No values were added, rewritten, or dropped in this step. The training
recommendation remains zero across the public text configs; source-split
routing does not itself clear the existing rights and quality gates. The new
split is public and directly loadable; it is not a quarantine or a hidden
dataset layer.

## Reproduction

```bash
PYTHONPATH=scripts .venv/bin/python scripts/audit_upstream_split_overlap.py
GARHWALI_RELEASE_VERSION=0.2.5 PYTHONPATH=scripts .venv/bin/python \
  scripts/build_huggingface_dataset.py \
  --output data/huggingface/garhwali-language-lab-v0.2.5-staging \
  --profile public
```

The audit verifies that the community extract and ingested records have the
same row order and original text before assigning a split-evidence crosswalk.
VAANI is represented by the two revisions listed in the JSON audit; the
Indic-dialect aggregate is pinned to `ca33c7c2e8ee72e9edc414cb37d1bf0903a3f9ae`.
The local Meta manifest has no recorded upstream commit, so this report binds
the result to its local SHA-256 instead of implying a pinned remote revision.
