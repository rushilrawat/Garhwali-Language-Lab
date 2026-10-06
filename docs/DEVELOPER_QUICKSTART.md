# Developer quick start

The dataset IDs are `rushilrawat/garhwali-corpus` (text and reference tables)
and `rushilrawat/garhwali-speech` (audio and speech metadata). Both repositories
are public. The Hub cards link to the latest published revisions and preserve release history.
This guide is bundled with `garhwali-language-lab-v0.2.7`; its
configuration counts match that package manifest. Use the Hub cards for current publication
status and immutable revisions. The packages preserve a common rights/quality
envelope, schema, and loading guidance. These examples stream the published
configs. Pass a commit SHA as `revision=` when
you need an immutable Hub snapshot.

## Training readiness and honest counts

The corpus repository is currently better for source discovery, vocabulary
exploration, and research than for general language-model training. The Hub
displays 961,533 rows, but 778,157 (80.9%) are provenance/reference-table rows;
all config totals overlap. The main `text` config has 18,598 rows and 291,914
whitespace-separated words, but **zero rows are currently marked
recommended_for_training**. The 1,737 `text_expansion` and 475
`text_resources` rows are also all marked not recommended for general text
training. The 14,988-row PahariLI config is experimental language-identification
material with unresolved sentence origins and unreviewed labels.

The speech repo contains substantial audio (113,363 rows, about 154.65 hours),
but only 2,002 strict speaker-disjoint reference rows are in the linked ASR
view, and those transcripts are unreviewed. The 104,500 non-empty SraVaani
outputs are machine drafts, not ground truth. See the [current metrics and
utility audit](../research/huggingface-current-metrics-and-utility-2026-10-06.md)
before selecting a config for training or evaluation.

## Try three vocabulary rows

Install the small dependencies:

```bash
python -m pip install "datasets>=5,<6" pandas duckdb
```

Optionally keep Hugging Face downloads in a project-local cache (the project
ignores `.cache/`):

```bash
export HF_HOME=.cache/huggingface
```

See Hugging Face's [`load_dataset` guide](https://huggingface.co/docs/datasets/loading),
[dataset cards](https://huggingface.co/docs/hub/main/datasets-cards), and
[supported dataset formats](https://huggingface.co/docs/hub/en/datasets-adding)
for the underlying interfaces.

Load the vocabulary config directly from Hugging Face without downloading the
other corpus subsets:

```python
from datasets import load_dataset

lexicon = load_dataset("rushilrawat/garhwali-corpus", "lexicon", split="train")
for row in lexicon.select(range(3)):
    print(row["form"], row.get("glosses", {}))
    print("rights:", row.get("rights_status", "inspect source provenance"))
    print("quality:", row.get("quality_status", "not supplied"))
```

The current `lexicon` row count is on the dataset card. Entries retain source
spelling; pronunciation and dialect labels can be absent, and native-speaker
review is deferred.

## Try Garhwali text-classification examples

The `paharili_gbm` config provides the Garhwali-labeled portion of PahariLI's
text language-identification corpus:

```python
from datasets import load_dataset

sentences = load_dataset(
    "rushilrawat/garhwali-corpus", "paharili_gbm",
    split="train", streaming=True,
)
for row in sentences.take(3):
    print(row["text"], row["source_record_ids"], row["rights_status"])
```

PahariLI's repository declares Apache-2.0, but its README does not identify the
source of each sentence. Rows preserve that caveat, upstream file hashes, and
source-lineage flags. The config is unreviewed, is not a general language-model
training recommendation, and its upstream test split is not an independent
evaluation set for other tasks. Check `rights_status`, `reuse_scope`, and
`record_quality_flags` before reuse.

Search the public lexicon directly from the project checkout; by default, the
tool streams the Hub config:

```bash
python examples/search_garhwali_lexicon.py "water" --limit 10
```

To pin the search to a specific Hub commit, pass `--revision COMMIT_SHA`.

For example, a record is `गाड़` (“river”, Hindi `नदी`); its row-level
metadata marks source terms, attribution conditions, and unreviewed linguistic
status separately. The demo prints these fields with each match.

## Load the fast-tracked text view

The `text_expansion` config contains **1,737** rows: 1,283 in `train` and 454
in `source_overlap`. They are candidates already present in the catalog, not
new source ingestion or an independent evaluation set. Currently zero rows meet
the conservative training-recommendation rule because source-level eligibility
or quality evidence remains unresolved. Rows retain their rights and quality
fields; review each row before downstream reuse.

```python
from datasets import load_dataset

extra_text = load_dataset(
    "rushilrawat/garhwali-corpus", "text_expansion", split="train", streaming=True
)
for row in extra_text.take(3):
    print(row["text"], row["rights_status"], row["quality_status"])
```

## Load supplementary text resources

The `text_resources` config exposes **475** rows already present in the source
catalog: 285 in `train` and 190 in `source_overlap`. This is a lookup and
research view with varied quality; it is not an evaluation set or uniformly
training-ready. Check record-level rights and quality fields before reuse.

```python
from datasets import load_dataset

resources = load_dataset(
    "rushilrawat/garhwali-corpus", "text_resources", split="train", streaming=True
)
for row in resources.take(3):
    print(row["text"], row["redistribution_status"], row["quality_status"])
```

## Configurations and exact release counts

Counts below are synchronized from the release manifest. Config views can
overlap; adding their row counts does not give the number of unique examples.

| Config | Rows | Intended use |
| --- | ---: | --- |
| `text` | 18,598 | Main Garhwali text splits, with source, rights, and quality metadata |
| `paharili_gbm` | 14,988 | PahariLI-derived Garhwali text-language-identification examples |
| `text_expansion` | 1,737 | Additional deduplicated text view; inspect row-level status |
| `text_resources` | 475 | Supplementary research text; inspect row-level status |
| `lexicon` | 1,493 | Word forms, gloss candidates, and pronunciation metadata |
| `asr` | 2,002 | Provider transcripts, not native-adjudicated |
| `sravaani_drafts` | 104,534 | Machine transcript drafts; not ground truth |
| `instructions` | 3,228 | Instruction and response examples |
| `catalog` | 36,105 | Unique text inventory with included text and source-linked metadata rows |
| `geography` | 50 | Place facts and citations |
| `historical_terms` | 36 | Historical names and terms |
| `literary_people` | 26 | Writer and contributor metadata |
| `literary_works` | 66 | Work-level bibliography |
| `popular_songs` | 30 | Song-level metadata |
| `university_research` | 8 | Research bibliography |
| `record_index` | 355,846 | Archive references; not training examples |
| `source_catalog` | 9,571 | Deduplicated sources and their known terms |
| `record_sources` | 412,740 | Record-to-source join rows |

The `garhwali-language-lab-v0.2.7` package manifest reports **961,533 total view rows**: 183,376 content/config rows plus 778,157 reference rows. This is not a unique-example count.

## Follow a catalog record to its source

The catalog exposes `id`, `text_publicly_available`, and a `sources` list. The
separate `source_catalog` config supplies deduplicated source URLs. Use the
`source_id` in the catalog row to resolve its source; a link is a locator, not a
reuse license.

```python
from datasets import load_dataset

catalog = load_dataset(
    "rushilrawat/garhwali-corpus", "catalog", split="train", streaming=True
)
source_rows = load_dataset(
    "rushilrawat/garhwali-corpus", "source_catalog", split="train"
)
source_by_id = {row["source_id"]: row for row in source_rows}

metadata_only = next(row for row in catalog if not row["text_publicly_available"])
for source in metadata_only.get("sources", []):
    reference = source_by_id.get(source.get("source_id"))
    source_url = source.get("source_url") or (reference or {}).get("source_url")
    source_title = (
        source.get("source_title")
        or (reference or {}).get("source_title")
        or source.get("source_id")
    )
    if source_url:
        print(metadata_only["id"], source_title, source_url)
```

The 2026-10-06 cross-config audit found 15,004 values from these catalog rows
already present elsewhere in the public JSONL tables and 8,444 full-text values
not present in any public config. Those 8,444 remain in the local all-data
package with rights pending. Of those rows, 7,675 have an inline source URL and
769 use the `source_catalog` lookup. A URL may identify a dataset or collection
rather than the exact work/page; verify the edition and rights evidence before
reuse. See the [text-availability audit](../research/huggingface-corpus-gap-resolution-2026-10-06.md).

Reuse terms vary by source; the package has no blanket content license. Use
each row's rights and quality fields rather than treating config or split
membership as approval for a particular use.

## Pandas and DuckDB

The vocabulary config is small enough to load into memory:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "rushilrawat/garhwali-corpus", "lexicon", split="train"
)
frame = lexicon.select_columns(
    ["form", "glosses", "rights_status", "reuse_scope", "quality_status"]
).to_pandas()
print(frame.head())
```

For SQL, materialize one config as Parquet and query it with DuckDB:

```python
import duckdb

lexicon.to_parquet("garhwali_lexicon.parquet")
print(duckdb.sql("""
    SELECT form, glosses, rights_status, quality_status
    FROM read_parquet('garhwali_lexicon.parquet')
    LIMIT 10
""").df())
```

## Speech access

Audio is published separately so consumers can choose text-only or speech
downloads. Start with metadata and a single row; decoding may require a local
FFmpeg/TorchCodec setup. See the [Hugging Face audio-loading guide](https://huggingface.co/docs/datasets/audio_load):

```python
from datasets import Audio, load_dataset

speech = load_dataset(
    "rushilrawat/garhwali-speech", "garhwali_speech",
    split="train", streaming=True,
)
speech = speech.cast_column("audio", Audio(decode=False))
print(next(iter(speech)))
```

Use the `meta_omnilingual` config for the separate Meta subset. Check
`split_safe_for_training` or `split_safe_for_evaluation` before using a row in
training or evaluation. `transcript_review_status` distinguishes provider
references from untranscribed audio; machine drafts are separate and are not
human labels.

## Next small tools

The first reusable tool is the searchable lexicon example in `examples/`.
Next, publish reproducible text and ASR baselines with their frozen split and
exposure limits. A hosted API can follow after each endpoint has an explicit
reuse scope, versioned input schema, and tested baseline. No paid service is
required for the examples in this guide.
