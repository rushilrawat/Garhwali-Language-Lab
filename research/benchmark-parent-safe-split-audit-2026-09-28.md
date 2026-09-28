# Parent-safe split and source-family audit — 2026-09-28

## Finding

The historical text split manifests contain **114,064 segments from 28,754
parent documents**. Rechecking each parent's `text_sha256` across the actual
train, validation, and test files found **50 parent documents spanning splits**
and affecting **1,523 segment rows**: 33 parent documents crossed train/test,
and 17 crossed train/validation. Exact segment hashes did not cross splits.
The previous exact-segment check therefore passed while source-document
siblings could still be separated.

The cause was the order of operations in the split builder. Normalized or
supported-semantic links could move one segment into another split without
moving every segment extracted from that same source document.

## Fix and candidate evidence

The builder now joins all segments sharing a parent document before applying
normalized-text and supported-semantic links, then rejects any result where a
parent document still appears in more than one split. Its report also records
SHA-256 hashes of the source text, audio, and semantic-edge files.

A separate, ignored candidate was rebuilt at
`data/processed/model_ready/splits_parent_safe_v0.2_2026-09-28/` under release
ID `garhwali-parent-safe-splits-v0.2-2026-09-28`. It retains all **114,064**
text rows and reports zero cross-split exact segment, normalized text,
supported semantic edge, parent-document, and identified-speaker groups.
It has 28,754 parent documents, 90,921 parent-document union links, 1,884
normalized links, 1,623 supported-semantic links, and 26,368 connected
components; 1,624 segment assignments were moved to keep connected groups
together.

The filtered recommended-text view retains all **8,265** records. Its old
counts were train 7,490 / validation 377 / test 398; the candidate has train
7,496 / validation 377 / test 392. Six recommended records move from test to
train, and no recommended record is added or removed. All historical manifests,
published files, and old scores remain unchanged.

| Candidate artifact | Records | SHA-256 |
| --- | ---: | --- |
| `text/train.jsonl` | 108,419 | `6ce3879f87bee8d7242c1c9e5d1c0e241fd922296c6aa8b090c5b9d0cd0c3661` |
| `text/validation.jsonl` | 2,721 | `d254428ae398c8465f0bd428cd3cb2e1751716d8d000d976c219988df8dbbb93` |
| `text/test.jsonl` | 2,924 | `877617c6bcb6ad5ddab69c27ddbc0ef1d7a658a03e1e5b433b8cc393cc44e256` |
| `text_recommended/train.jsonl` | 7,496 | `fc7b2357361b0ec0ce902e18a3b0bae87af01e8382508d3065b0b2c1ff168ee9` |
| `text_recommended/validation.jsonl` | 377 | `f2e5d78cf0456516b1f2eed0c68db402d4f11701c14dc8e46187a6e521aac8ea` |
| `text_recommended/test.jsonl` | 392 | `9d9205fe03d912e1d3383beaecfb0ab47843db0398eef8ad8e01aafa27c54698` |
| `report.json` | — | `d32d3170f1727d3c24ff5d0f5d905f4c0ba2bd1bcc5372cf6a87b8424d8da567` |

The report's input hashes are text segments
`b8cbe09eda0c1e6ebe08bfd8e5a591a5d77cea4114765e55ef2394e15860a139`, audio
`1c3bd0a1887a3e11d34288418def8439f9b64b1a9e4f31463604f2866a8ff694`, and
semantic edges
`f11891fdbe353c89a82b28de43a46eec52deefbf26a593e6bd17a3104cafc344`.

The benchmark builder was then run against these corrected manifests under
release ID `garhwali-bench-parent-safe-candidate-2026-09-28`. It produced a
separate local candidate with 3,847 external records, 392 internal text rows,
and 112 ASR rows. Its 392 internal rows match the candidate recommended test
view exactly by segment ID and text; exact training-text overlap and identified
speaker overlap are both zero. The known XORQA train/dev source-text repeat
remains flagged.

| Candidate benchmark artifact | SHA-256 |
| --- | --- |
| `garhwali_bench/manifest.json` | `f5bbed4250983a3af36d43c6e34647ff4ab0674136ad52a1d671114d1ac6c2bb` |
| `garhwali_bench/internal_text.jsonl` | `8ef6e278ff52c4fb9bfda863a2f4f7cd04e927cb81c4ac824176a5fc67cbf843` |

The builder's deterministic character-bigram output is perplexity **14.123460**
on those 392 rows, trained on the 7,496-row corrected recommended view. The
rows were already used by earlier benchmark work, so this number is a
historical/open-test diagnostic only; it was not used for model selection and
does not estimate independent accuracy. No neural inference was run.

## External benchmark source-family checks

- **CrossSum:** all 699 records have a source and target URL; exact canonical
  URL grouping found 699 distinct URLs in each field and no URL repeated across
  source splits (99 train, 100 dev, 500 test). Canonicalization lowercases the
  URL scheme and host and drops fragments. This does not detect redirects,
  aliases, mirrored articles, or semantically related pages.
- **FLORES:** 2,009 rows (997 dev, 1,012 test) expose one dataset-level
  `source_id`, with no row-level source or target URLs. The available fields
  cannot support a meaningful finer-grained page/source-family split audit.
- **XORQA:** the existing exact-title audit remains the stronger source-family
  result: 54 page families / 134 rows cross original splits; 32 families have
  different exact context passages. The retained-row overlay marks 138 records
  for open diagnostics. See the [XORQA source-page review](benchmark-source-page-families-2026-09-28.md).

## Reproduction and remaining limits

The parent-safe candidate is generated by `scripts/build_dataset_splits.py`
followed by `scripts/build_recommended_text_view.py`, using release ID
`garhwali-parent-safe-splits-v0.2-2026-09-28`. Its benchmark candidate is
generated by `scripts/build_garhwali_benchmark.py` with the release ID above.
Regression tests cover parent grouping before semantic reassignment, source
input hash recording, and versioned benchmark IDs. All candidate outputs are
Git-ignored and have not been promoted to the public release. The deterministic
text score is historical/open-test diagnostic evidence, not a model-selection
result or an independent-accuracy claim.

This closes one reproducible split-builder defect; it does not close all of
Phase 2. Semantic/paraphrase and translation-equivalence analysis remain open.
FLORES lacks source-family metadata at the row level. Existing model results
and test-exposure decisions remain historical; the new candidate split is not a
blind test for checkpoints trained or evaluated on earlier project snapshots.
