# Developer quick start

The dataset IDs are `rushilrawat/garhwali-corpus` (text and reference tables)
and `rushilrawat/garhwali-speech` (audio and speech metadata). Both repositories
are public. The latest corpus release is v0.2.3 at commit
[`76dac8d`](https://huggingface.co/datasets/rushilrawat/garhwali-corpus/commit/76dac8de70d37595c7af9a3c642c81ece615ec5d); the speech dataset is at commit
[`9da266e`](https://huggingface.co/datasets/rushilrawat/garhwali-speech/commit/9da266e23bfc198f70784a6e81edbf32f946102f).
The corpus release adds a deduplicated `text_resources` view of 246 existing
rights-cleared Garhwali records; it does not add newly collected sources.
Counts below describe the v0.2.3 corpus and current speech package. Pass a
commit SHA as `revision=` when you need an immutable Hub snapshot.

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

Load the vocabulary config from the local v0.2.3 package without loading any
other corpus subset:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "json",
    data_files="data/huggingface/garhwali-language-lab-v0.2.3-staging/data/lexicon/train-*.jsonl",
    split="train",
)
for row in lexicon.select(range(3)):
    print(row["form"], row.get("glosses", {}))
    print("rights:", row.get("rights_status", "use the source-specific provenance"))
    print("quality:", row.get("quality_status", "review status not supplied"))
```

The `lexicon` config has **1,493 rows**. Entries retain source spelling;
pronunciation and dialect labels can be absent, and native-speaker review is
deferred. The equivalent load from the public Hub is:

```python
from datasets import load_dataset

lexicon = load_dataset("rushilrawat/garhwali-corpus", "lexicon", split="train")
print(lexicon.select(range(3)))
```

Try the searchable CLI against the local v0.2.3 package files with:

```bash
python examples/search_garhwali_lexicon.py "water" --data-file \
  'data/huggingface/garhwali-language-lab-v0.2.3-staging/data/lexicon/train-*.jsonl'
```

To stream the current corpus config directly, omit `--data-file`. If you
downloaded the versioned package, pass its local `data/lexicon/train-*.jsonl`
path instead.

For example, a record is `गाड़` (“river”, Hindi `नदी`); its row-level
metadata marks source terms, attribution conditions, and unreviewed linguistic
status separately. The demo prints these fields with each match.

## Configurations and exact release counts

Counts below were reconciled against the v0.2.3 release. A config may contain train,
validation, and test splits; numbers are summed across those splits. Views can
overlap, so do not add the table to calculate unique training examples.

| Config | Rows | Intended use |
| --- | ---: | --- |
| `text` | 18,949 | Rights-filtered text examples; train 17,289, validation 895, test 765 |
| `text_expansion` | 1,647 | Strict-tier additions already in the catalog; train-only, machine-screened |
| `text_resources` | 246 | Additional catalog text for lookup/research; mixed quality, not for training or evaluation |
| `lexicon` | 1,493 | Word forms, gloss candidates, and pronunciation metadata |
| `asr` | 2,002 | Strict speaker-disjoint subset of 5,894 VAANI provider transcripts; 1,621 train, 269 validation, 112 test; not native-adjudicated |
| `sravaani_drafts` | 104,534 | Unique audio hashes: 104,500 non-empty machine drafts and 34 empty outputs; experimental, not ground truth |
| `instructions` | 3,228 | Instruction/response examples; train 2,686, validation 356, test 186 |
| `catalog` | 32,072 | Exact-unique text inventory; 12,606 values exposed, 19,466 text values redacted |
| `geography` | 50 | Place facts and citations, without source prose |
| `historical_terms` | 36 | Historical names and terms |
| `literary_people` | 26 | Writer and contributor metadata |
| `literary_works` | 66 | Work-level bibliography; not the works themselves |
| `popular_songs` | 30 | Song metadata; no lyrics |
| `university_research` | 8 | Research bibliography |
| `record_index` | 302,641 | Content-free archive references; not training examples |
| `source_catalog` | 5,019 | Deduplicated sources and their known terms |
| `record_sources` | 355,403 | Join rows connecting records to sources |

The release reports **827,450 total view rows**: 164,387 content/config rows
plus 663,063 reference rows. This is not 827,450 unique examples. The corpus
also has different reuse terms by source; it does not have one blanket license.
The 19,466 text values without compatible public redistribution terms are
redacted in the public content table. Speech is a linked dataset, with separate
source, split-safety, transcript, and audio terms.

## Pandas and DuckDB

The vocabulary config is small enough to load into memory:

```python
from datasets import load_dataset

lexicon = load_dataset(
    "json",
    data_files="data/huggingface/garhwali-language-lab/data/lexicon/train-*.jsonl",
    split="train",
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

The configs contain **110,436 VAANI rows** (train 109,320, validation 666,
test 450) and **2,927 Meta rows** (train 2,329, validation 298, test 300).
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
