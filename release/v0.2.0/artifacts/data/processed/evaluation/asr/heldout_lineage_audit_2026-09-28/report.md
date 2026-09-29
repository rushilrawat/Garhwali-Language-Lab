# Post-hoc ASR held-out lineage audit (2026-09-28)

This audit verifies saved output identity, aggregate arithmetic, and retrospective paired uncertainty. It ran no inference and did not select a model.

Fixed manifest: `112` rows; SHA-256 `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52`.

| Run | Audio IDs | Clean references | WER | CER | Original manifest hash matches current bytes |
| --- | ---: | ---: | ---: | ---: | --- |
| SraVaani 1.0 base | 112 | 112 | 42.7613% | 17.6058% | yes |
| Six-configuration decoder sweep, selected configuration | 112 | 112 | 42.7613% | 17.4096% | not recorded |
| 61-trial decoder/joint fine-tune | 112 | 112 | 43.5283% | 17.4937% | not recorded |
| Expanded-human-transcript fine-tune | 112 | 112 | 43.2886% | 17.3956% | not recorded |
| Original 102-step human-reference adaptation | 112 | 112 | 43.5283% | 17.4516% | no; post-hoc rows match |

All five runs identify the same fixed 112-row evaluation set. Every saved prediction file matches all 112 audio hashes and all 112 cleaned references; the row counters reproduce each aggregate WER/CER report. The base report directly records the fixed manifest hash and row count.

| Candidate vs base | WER delta, percentage points (95% speaker-cluster interval) | CER delta, percentage points (95% speaker-cluster interval) | Speaker clusters |
| --- | ---: | ---: | ---: |
| Six-configuration decoder sweep, selected configuration | +0.000 [-0.583, +0.656] | -0.196 [-0.391, +0.000] | 19 |
| 61-trial decoder/joint fine-tune | +0.767 [-0.107, +1.591] | -0.112 [-0.683, +0.384] | 19 |
| Expanded-human-transcript fine-tune | +0.527 [-0.710, +1.518] | -0.210 [-0.949, +0.366] | 19 |
| Original 102-step human-reference adaptation | +0.767 [-0.307, +1.683] | -0.154 [-0.936, +0.398] | 19 |

Positive deltas mean higher error than the base. These paired intervals are retrospective descriptions of a previously scored public test; they were not used to select or promote a model. They do not establish independent generalization, upstream SraVaani exposure is unresolved, and references have not been native-adjudicated.

The 102-step run’s recorded manifest byte hash differs from the current manifest hash, but its saved predictions reconcile by all audio-hash IDs and cleaned references. This verifies example identity; it does not explain the historical serialization difference.

No fresh inference or model selection occurred.

Machine-readable report: `report.json` (written beside this Markdown file).
