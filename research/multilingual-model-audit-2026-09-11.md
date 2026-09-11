# Multilingual model audit

Generated on 2026-09-11 from 2,492 frozen GarhwaliBench text records. Model
repositories and revisions are pinned, tokenizer files are checksummed, and all
downloads remain in the project’s ignored Hugging Face cache.

## Tokenizer comparison

| Candidate | Family | Tokens/word | Characters/token | Unknown-token rate |
| --- | --- | ---: | ---: | ---: |
| `ai4bharat/IndicBERTv2-MLM-only` | Indic encoder | **1.531569** | 3.112073 | 0 |
| `google/muril-base-cased` | Indic encoder | 1.618804 | 2.944368 | 0.00016117 |
| `FacebookAI/xlm-roberta-base` | Multilingual encoder | 1.858901 | 2.564070 | 0 |
| `google/mt5-small` | Multilingual encoder-decoder | 2.307433 | 2.065652 | 0 |
| `hikinegi/UK-Garhwali-Language` | Garhwali OpenLLaMA adapter tokenizer | 5.326503 | 0.894837 | 0 |

IndicBERTv2 gives the lowest Garhwali fragmentation. Its tokenizer uses 29% fewer
tokens than mT5-small and 71% fewer than the Garhwali OpenLLaMA adapter tokenizer
on the same text. No candidate exceeds its declared context window. The audit
uses Transformers’ corrected pre-tokenization regex and native SentencePiece
loading.

## First full-model baseline

The pinned 1.1 GB IndicBERTv2 masked-language checkpoint was evaluated on 128
deterministically selected held-out records. Fifteen percent masking is selected
from each segment hash; each record contributes at least one non-special token.

| Metric | Result |
| --- | ---: |
| Held-out records | 128 |
| Masked tokens | 506 |
| Masked-token accuracy | **0.17786561** |
| Masked-token cross-entropy | **6.977486** |
| Masked-token perplexity | **1072.219001** |
| Truncated records | 0 |

This is a pre-adaptation diagnostic. Its masked-token perplexity is not directly
comparable to the character-bigram perplexity because the prediction units and
objectives differ. The result establishes a reproducible IndicBERTv2 baseline
for continued-pretraining and cleanup ablations.

## Garhwali-specific candidates discovered

- `hikinegi/UK-Garhwali-Language` is a LoRA adapter over
  `openlm-research/open_llama_3b_v2`. Its card names an unknown dataset and gives
  no evaluation result; its tokenizer fragmentation makes the 3B base a low
  priority.
- `Gaurav17/garhwali-nllb-v12` is a 4.7 MB LoRA adapter over
  `facebook/nllb-200-distilled-600M`. Its generated model card gives no training
  data, language-token mapping, metrics, or license, so it remains an
  experimental translation candidate.
- Multiple Garhwali and multidialect Whisper/Wav2Vec2-BERT repositories are now
  catalogued for the later ASR comparison. Their evaluation must use the frozen
  112-row speaker-safe split because repository download counts are not evidence
  of quality.

## Decision

Use IndicBERTv2 as the first encoder and continued-pretraining control. Keep
MuRIL as the second Indic control, XLM-R as the broad multilingual control, and
mT5-small for later generative tasks. Do not download the 3B OpenLLaMA base until
the smaller, better-tokenizing controls have been evaluated. Treat the Garhwali
NLLB adapter as unverified until its language mapping and held-out translation
quality are reproduced.

## Reproduction

```bash
.venv/bin/python -m pip install --target .cache/asr-runtime -r requirements-model-audit.txt
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/audit_multilingual_tokenizers.py
PYTHONPATH=.cache/asr-runtime .venv/bin/python scripts/run_masked_lm_baseline.py
```
