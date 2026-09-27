# ASR baseline consolidation — 2026-09-26

**Status:** Completed from saved outputs; no new inference or test scoring.

**Scope:** SraVaani base decoding, decoder sweep, training sweeps, and their saved validation/test aggregates.
**Metric:** Micro WER/CER using `scripts/asr_metrics.py` (NFC, case-fold, punctuation/symbols to spaces, whitespace collapse; CER removes spaces).

This consolidates the existing ASR experiment results requested by Phase 5 of the [benchmark and model research roadmap](benchmark-model-roadmap.md). Validation predictions were re-scored from their saved reference/hypothesis text with the local metric implementation. Held-out-test values below are copied only from pre-existing aggregate reports; test prediction/reference rows were not opened, recomputed, or selected from.

## Results

Every listed validation prediction artifact contains the same 269 ordered `audio_filepath` values and the same ordered references. Their ordered audio-path digest is `aaac4de4d0f2d62992023a6e8c4326220c0e139ca37ba8e00c6bd17ea33f2d08`; the ordered-reference digest is `22f755f009928e85daa74314870e43449b9e9426e1d91e3063c673bded53d382`. Validation denominators reconcile at 4,980 reference words and 17,342 reference characters, and local re-scoring matched every stored per-row error count in all five files.

| Candidate | Validation WER (errors / words) | Validation CER (errors / chars) | Historical test WER (errors / words) | Historical test CER (errors / chars) | Selection / status |
| --- | ---: | ---: | ---: | ---: | --- |
| SraVaani base, RNNT greedy-batch | 43.454% (2,164 / 4,980) | 18.948% (3,286 / 17,342) | — | — | Decoder-sweep validation baseline; separate base test report does not specify decoder |
| SraVaani base model report | — | — | 42.761% (892 / 2,086) | 17.606% (1,256 / 7,134) | Revision `f5dd535`; 112-row test manifest SHA is recorded |
| SraVaani base, RNNT beam-8 | 43.253% (2,154 / 4,980) | 18.919% (3,281 / 17,342) | 42.761% (892 / 2,086) | 17.410% (1,242 / 7,134) | Selected among six decoder configs on validation; not a fine-tune |
| Original 102-step human-reference adaptation | — | — | 43.528% (908 / 2,086) | 17.452% (1,245 / 7,134) | Its report's test-manifest SHA differs from the base report; exact row identity is unverified |
| Six-config decoder/joint fine-tune | 43.012% (2,142 / 4,980) | 18.712% (3,245 / 17,342) | 43.528% (908 / 2,086) | 17.704% (1,263 / 7,134) | 6/6 trials completed; best validation trial |
| Refined 61-trial decoder/joint fine-tune | 42.711% (2,127 / 4,980) | 18.660% (3,236 / 17,342) | 43.528% (908 / 2,086) | 17.494% (1,248 / 7,134) | 61/61 trials completed; best validation trial |
| Expanded-human-transcript decoder/joint fine-tune | 42.209% (2,102 / 4,980) | 18.302% (3,174 / 17,342) | 43.289% (903 / 2,086) | 17.396% (1,241 / 7,134) | 1/1 trial completed; experimental, speaker metadata incomplete |

The validation row-wise error counts compared with RNNT greedy-batch were lower/equal/higher on 55/167/47 utterances for beam-8; 79/127/63 for the six-config fine-tune; 88/116/65 for the 61-trial fine-tune; and 90/123/56 for expanded-human fine-tuning. These are descriptive paired counts on a repeatedly used development set, not independent confidence estimates.

## Interpretation and limits

- The saved test aggregates show beam-8 with the same WER as the base report and lower CER, while fine-tune aggregates have numerically higher WER. However, only the base model report includes a test-manifest SHA-256; the decoder-sweep and fine-tune reports omit one. Exact test-row identity and paired deltas therefore cannot be verified from the saved metadata. Treat every test value as historical and do not use those comparisons to promote a model.
- The apparent validation gains are selection-biased: each fine-tune's checkpoint was selected from validation, and 61-trial selection tried many candidates. The fixed 112-row VAANI test has already been scored and is historical only.
- The base model report pins test manifest SHA-256 `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`. The original 102-step adaptation report records `d9202d6c8e659aef86a1170409a726f42a65b4ae87825c3cd82a0530d55483a1`, a different digest. The decoder sweep's selected-test aggregate and the later training-sweep `held_out_test` aggregates contain no test-manifest hash. Matching row/word/character counts do not prove identical examples; see BMR-012.
- SraVaani's upstream training exposure includes VAANI, but row-level overlap is not available. The existing test therefore cannot establish independent generalization. References are not native-adjudicated; native review and dialect annotation are deferred at the owner's direction.
- A legacy validation comparator in `research/asr-validation-error-analysis-2026-09-24.json` reports 2,161 word errors and 3,282 character errors on 269 rows (the same denominator and manifest digest). The current sweep's greedy output reports 2,164 and 3,286. The legacy comparator records the normalizer and prediction input hash but not enough decoder/checkpoint/run provenance to explain the different aggregate errors. It remains a separate historical comparator; do not silently choose one result as the unique SraVaani baseline. Tracked as BMR-009 in the [issues and improvement plan](issues%26improvement%20plan.md).

## Artifact provenance

| Artifact | Run/checkpoint evidence |
| --- | --- |
| Base SraVaani report | `ARTPARK-IISc/SraVaani-1.0`, revision `f5dd5358325a5208775b91dad98918e079ea2b27`; report artifact SHA-256 `789a21b6df8b0bb2ea2cc1c120edbfd4b898d3a26e6c6673cca45d14b64a47f2` |
| Decoder sweep | Run `garhwali-sravaani-decoding-sweep-v0.1`; selected `rnnt-beam-8`; recorded checkpoint SHA-256 `cb206f88afbe179d10229a8002e92c74789eed77557ef38a33533e26b69067af`; `selection_used_test_split=false` |
| Six-config fine-tune | Best checkpoint SHA-256 `ef36e6f747d1a0a70d8a2bab1955fd7f6f1828623838fdbce97741cfae41cd68`; 51 optimizer steps |
| Refined 61-trial fine-tune | Best checkpoint SHA-256 `f1a29db9c7a70566e456fe657051f558c7d77d1731585e6f80ab9b889e414a4e`; 102 optimizer steps |
| Expanded-human fine-tune | Best checkpoint SHA-256 `684f18cadabdd27263d14b7c66e884e863a061e7a30898557bcc949cd10680f3`; 346 optimizer steps; training set 5,513 human-transcript clips, 8.112 hours |

The sweep reports record validation-only selection (`selection_used_test_split=false`). Fine-tune test aggregates are retained solely as historical report values; their exact row sets are not fully fingerprinted in those reports. Machine-readable inputs live under `data/processed/evaluation/asr/`, which remains ignored by Git.

## What is stopping the next ASR work

The saved sweep reports show 6/6, 61/61, and 1/1 trials completed; no ASR run represented by these artifacts stopped due to an account usage limit. Fresh local inference is a separate issue: the SraVaani model cache contains metadata but no base weights, the local runtime lacks NeMo, and PyArrow/audio-decoding packages needed by the available Parquet/audio path are absent. The trained `.nemo` checkpoints and the Garhwali Whisper-tiny checkpoint are present locally, but no new inference was attempted. The exact preflight and remaining gates are recorded in [the renamed issue plan](issues%26improvement%20plan.md).

No Hugging Face job was launched, polled, or billed for this consolidation.
