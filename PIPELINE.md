# Garhwali ingestion pipeline

The deterministic collectors remain responsible for source snapshots, hashes,
extraction, licensing fields, and corpus records. LangGraph coordinates those
steps and checkpoints progress in `data/cache/ingestion-graph.sqlite`.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-pipeline.txt
.venv/bin/python -m pip install --target .cache/asr-runtime -r requirements-model-audit.txt
```

## Run and resume

Each ingestion batch needs a stable run ID.

```bash
.venv/bin/python scripts/ingestion_graph.py run --wave sixth --run-id uou-more-2026-09-08
.venv/bin/python scripts/ingestion_graph.py run --wave seventh --run-id scholarly-open-2026-09-09
.venv/bin/python scripts/ingestion_graph.py run --wave eighth --run-id cultural-open-2026-09-09
.venv/bin/python scripts/ingestion_graph.py run --wave ninth --run-id thematic-vocabulary-2026-09-09
.venv/bin/python scripts/ingestion_graph.py status --run-id uou-more-2026-09-08
.venv/bin/python scripts/ingestion_graph.py resume --run-id uou-more-2026-09-08
```

The graph executes acquisition, extraction, exact deduplication, and full
verification in order. Acquisition retries HTTP 429 and transient 5xx, timeout,
and connection-reset failures with exponential backoff. Confirmed schema errors,
403 responses, and 404 responses remain logged for review instead of looping.

Snapshot and extraction functions are idempotent. A resumed run verifies and
reuses completed downloads rather than appending duplicate records.

## Current graph-managed waves

- `fourth`: current CLDF numeral sources and Garhwali Open Bible Stories.
- `fifth`: Kellogg and Walton public-domain historical material.
- `sixth`: selected Garhwali units from additional UOU modules.
- `seventh`: rights-audited scholarly references; no paper prose is promoted to
  the Garhwali corpus.
- `eighth`: public-domain Garhwal cultural history and folklore passages,
  Wikisource references, and open Wikimedia cultural-media metadata.
- `ninth`: themed Garhwali vocabulary from rendered dictionary pages, animal
  and bird lists, occupations, and a Government of India instrument list.

Add a new wave by defining `<name>_wave_acquire` and `<name>_wave_extract` in
`scripts/collect_online.py`, then registering the pair in `wave_actions()`.

## Verification

```bash
.venv/bin/python -m unittest discover -s scripts -p 'test_*.py'
.venv/bin/python scripts/dedup_report.py
.venv/bin/python scripts/verify_ingestion.py
.venv/bin/python scripts/tag_language_quality.py
.venv/bin/python scripts/build_dataset_splits.py
.venv/bin/python scripts/build_garhwali_benchmark.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/audit_multilingual_tokenizers.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_masked_lm_baseline.py
.venv/bin/python scripts/run_translation_baseline.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_nllb_translation_baseline.py --max-records 32 --max-new-tokens 64 --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_nllb_translation_baseline.py --adapter .cache/model-adapters/garhwali-nllb-v12 --output data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy --max-records 32 --max-new-tokens 64 --device cpu
.venv/bin/python scripts/run_retrieval_baseline.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_indicbert_retrieval_baseline.py --max-records 0 --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_whisper_comparison.py --device cpu
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/propose_text_cleanup.py --model-records 4096 --device cpu
.venv/bin/python scripts/run_text_cleanup_ablation.py
.venv/bin/python scripts/run_text_scaling_experiment.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_indicbert_adaptation.py --device cpu
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/run_indicbert_lora_adaptation.py --device cpu --steps 256 --training-records 2048
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/evaluate_indicbert_transfer.py --device cpu --test-records 256
.venv/bin/python scripts/build_instruction_dataset.py
.venv/bin/python scripts/build_instruction_accuracy_split.py
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/run_indicbert_lora_adaptation.py --device cpu --steps 1024 --training-records 8192 --output data/processed/evaluation/controlled_modeling/indicbert_lora_long.json --checkpoint-dir models/controlled_modeling/indicbert_lora_v0.2
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/run_mt5_instruction_tuning.py --device cpu --steps 64 --training-records 2304
PYTHONPATH=.cache/asr-runtime:scripts .venv/bin/python scripts/run_mt5_instruction_tuning.py --device cpu --data-dir data/processed/model_ready/instructions_v0.2 --output-dir data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2 --checkpoint-dir models/controlled_modeling/mt0_instruction_v0.2 --steps 256 --training-records 2046 --model-path .cache/huggingface/hub/models--bigscience--mt0-small/snapshots/8116a34237e19160ec003147e758f065876d95f0 --model-id bigscience/mt0-small --revision 8116a34237e19160ec003147e758f065876d95f0 --run-id garhwali-mt0-instruction-lora-v0.2
PYTHONPATH=scripts .venv/bin/python scripts/analyze_sravaani_drafts.py
PYTHONPATH=scripts .venv/bin/python scripts/build_huggingface_dataset.py --output data/huggingface/garhwali-language-lab --include-audio
```

The benchmark builder indexes the frozen external, text, and ASR evaluation
assets, validates their schemas and checksums, rejects internal text or speaker
leakage, reports external contamination separately, and runs the deterministic
character-bigram floor used by later model audits.

The tokenizer audit loads only pinned local snapshots and measures fragmentation,
unknown tokens, and context overflow on the frozen text evaluation set. The
masked-language runner uses deterministic hash-selected masks so repeated model
comparisons score the same held-out positions.

The translation floor evaluates source copying and development-set translation
memory on every IndicGenBench FLORES test row. The NLLB pilot uses a pinned local
snapshot and the same deterministic 32-record subset for both comparisons.
Because NLLB has no Garhwali language token, both runs explicitly use `hin_Deva`
as an experimental source-token proxy and `eng_Latn` as the target token. The
community adapter's own language-token mapping is undocumented, so its result is
retained for comparison rather than treated as a validated Garhwali score.

The retrieval audit deduplicates XORQA contexts into a fixed passage index and
scores dev/test questions without training on benchmark queries. Word and
character BM25 provide dependency-free cross-script floors. Pinned IndicBERTv2
uses zero-shot, mean-pooled embeddings for a full 539-query test comparison.
English oracle BM25 is reported only on the 500 dev rows where the upstream
benchmark supplies a non-empty oracle question.

The Whisper comparison runner evaluates pinned local checkpoints on the strict
112-row speaker-safe ASR test manifest with one normalization and micro-averaged
WER/CER implementation. Use explicit `--model`, `--model-id`, `--revision`, and
`--output` arguments for Whisper-small or a fine-tuned checkpoint. The separate
`run_sravaani_comparison.py` runner evaluates the provider-approved SraVaani 1.0
snapshot on those same 112 rows. Its local score is 42.761% WER / 17.606% CER;
the official 53.5 WER remains a separate result from a different evaluation.
`transcribe_sravaani_drafts.py` applies the same pinned snapshot resumably to the
untranscribed queue. Its outputs stay active in the experimental view with model
revision and machine-draft status attached. The completed run covers all 104,542
source rows / 104,534 unique audio hashes; eight inherited duplicate-audio rows
retain both source paths and collapse to one row in the Hugging Face export.

The cleanup proposer keeps the original, current, and proposed text together for
all parent records. It builds spelling candidates from train-only corpus counts,
uses a pinned IndicBERTv2 masked-language score to rank 4,096 priority records,
and never changes language or dialect labels automatically. The ablation compares
the unchanged, mechanical-only, and bulk spelling variants on the fixed document
split before any proposal can enter a versioned cleaned view.

The scaling runner compares character bigram and trigram controls at six nested
training fractions under three deterministic seeds. It selects order and scale
using validation cross-entropy, then evaluates only that configuration on the
frozen test candidate. Exact train/validation and train/test overlap must remain
zero in the resulting integrity report.

The first transfer pilot freezes the IndicBERTv2 encoder and adapts only its MLM
prediction transform and output bias for 64 train-only steps under three seeds.
It evaluates a fixed 128-record validation subset, saves small ignored head
checkpoints, and does not touch the frozen test candidate. Its only promotion
decision is whether the stronger encoder-adaptation experiment is justified.

The encoder pilot adds rank-4 LoRA parameters to every attention query and value
projection, trains three 256-step seeds, and selects the run length on validation.
The transfer evaluator then opens one checksum-addressed 256-record frozen-test
subset exactly once to compare the unadapted model, head-only adaptation, and all
three LoRA seeds. Its result is final for this experiment and cannot be used to
retune the same test comparison.

The longer continuation draws an 8,192-record pool per seed from the whole text
training partition and takes 1,024 updates without reopening the closed transfer
test. The instruction builder then derives 2,518 translation and lexicon prompts
from existing evidence while inheriting each parent document's split. The mT5
runner trains three rank-4 LoRA seeds, selects on 130 validation records, and
opens the separate 84-record instruction test only after selection. Generated
answers and teacher-forced loss are both retained so a lower loss cannot hide an
unusable generation result.

The accuracy continuation freezes a second 258-record instruction test from
previously unused training parents, audits mT0-small on validation, and then
trains three 256-step LoRA seeds. It keeps the earlier 84-record test closed and
reports teacher-forced loss alongside chrF2 and exact match.

The Hugging Face builder writes JSONL shards for five Dataset Viewer
configurations, generates the dataset card and manifest, filters the public
profile using component-level license evidence, and hard-links content-addressed
audio. Its final mode rejects an incomplete SraVaani draft set; partial output is
available only through the explicit preview flag.
