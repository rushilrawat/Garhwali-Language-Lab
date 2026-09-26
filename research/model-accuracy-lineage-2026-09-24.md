# Model accuracy split and evaluation lineage audit

This deterministic audit inventories frozen input manifests and saved prediction files. It does not modify corpus rows or model artifacts.

Model training lineage and upstream pretraining overlap are recorded as unknown unless an artifact records them. Any matched validation, development, or test rows have prior evaluation evidence; test rows must not be described as blind.

## Frozen manifests

| Family | Split | Rows | Manifest SHA-256 | Missing audio hashes | Missing text hashes |
|---|---:|---:|---|---:|---:|
| asr | train | 1621 | `87ea08229a3a445460043127a2296112a131e914ea0d507c4a35ee0f5ee33ec8` | 0 | 0 |
| asr | validation | 269 | `65b0acefa0deb166e95bd8aa29fe37ee5b693e06b11afdc76dca8b5a91dfac66` | 0 | 0 |
| asr | test | 112 | `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52` | 0 | 0 |
| asr_expanded_human | train | 5513 | `bb61c8505b36b976c4cd8d62045ff937deef3267f65224ba6111c19e1b8d57a3` | 0 | 0 |
| asr_expanded_human | validation | 269 | `65b0acefa0deb166e95bd8aa29fe37ee5b693e06b11afdc76dca8b5a91dfac66` | 0 | 0 |
| asr_expanded_human | test | 112 | `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52` | 0 | 0 |
| asr_experimental | train | 4778 | `3812dd8d83b4488a604a463456a666e94251b02698c12c42b823fbc5aebd5f84` | 0 | 0 |
| asr_experimental | validation | 666 | `d7f4e7605b9e1a48d4e4facc1df02eb21fd15497a67a37067b9a324b4956596f` | 0 | 0 |
| asr_experimental | test | 450 | `75a01ddf165fb6646b140bb6cc50aff4f0e981569c85ffcbcf5ac9062da1bfcd` | 0 | 0 |
| benchmark_crosssum | dev=100, test=500, train=99 | 699 | `fcb10709e25c9a7a174df3e97501dc59c061601687fa253f214dedeb44856e4b` | 699 | 0 |
| benchmark_flores | dev=997, test=1012 | 2009 | `7c96d63be5f43e6a65fc229238c6d295d983fe46be032e9f8418d32150225097` | 2009 | 0 |
| benchmark_xorqa | dev=500, test=539, train=100 | 1139 | `e69be06befb0227395ba0feb58220388134279d4f95659ba8442e0b8e3d13ed6` | 1139 | 0 |
| instructions_v0.2 | train | 2650 | `fe79e202f5d0f95969e0406cb91509e2cd4b276899662a5118668cdedd6d2b9e` | 2650 | 0 |
| instructions_v0.2 | validation | 320 | `71c86477f8acc56d11b9bf1f9da421cbb244bc241a0910b30bb3cdee87ca856b` | 320 | 0 |
| instructions_v0.2 | test | 260 | `990ee4860f2467198aebbcbe219fbb6e3bdb9d4fa8dadf902e65b64ff96ff9f5` | 260 | 0 |
| meta_omnilingual | test=300, train=2329, validation=298 | 2927 | `67f158a742bc3e9947bf9308c6e0a1e5c8ee448f1a2605a109bcbce6d8dc99e9` | 0 | 0 |
| text_recommended | train | 7490 | `2de3f3f95f24d41df9a4ce142496b7e9e97ac402ff4cca4c00edb6bed41d6ec8` | 7490 | 0 |
| text_recommended | validation | 377 | `a031c770c267dbd22c18f723aa88c780740edf8a00eeb1d55a5fe07623a4fdf3` | 377 | 0 |
| text_recommended | test | 398 | `34a6ceb690335e9c67d08751f889871ad196b5587f90ee0aee9604f3ec8e089c` | 398 | 0 |
| tts | train | 1621 | `87ea08229a3a445460043127a2296112a131e914ea0d507c4a35ee0f5ee33ec8` | 0 | 0 |
| tts | validation | 269 | `65b0acefa0deb166e95bd8aa29fe37ee5b693e06b11afdc76dca8b5a91dfac66` | 0 | 0 |
| tts | test | 112 | `2cc0defa1745deb4247e04e1a8cd478576cd1893842047baf81652102951bc52` | 0 | 0 |
| tts_language_resources | train | 1422 | `15cabcb6db4f3cbf0954369d12cd41268ec0ccfd7762c67e95ef93495110ea05` | 0 | 0 |
| tts_language_resources | validation | 225 | `78bbd824ed3582f60a4b19599fcc6acbe766c9b97502a6f36b42eac86affdadb` | 0 | 0 |
| tts_language_resources | test | 89 | `d3e91664f712b0ebcac5e15eba57586c9667f8e94e85bf9120cc608a6f858614` | 0 | 0 |

## Split overlap findings

### asr_expanded_human

- `asr_target_sha256`: 1 cross-split duplicate groups
- `speaker_id`: 3860 rows have no usable speaker ID

### asr_experimental

- `asr_target_sha256`: 1 cross-split duplicate groups
- `speaker_id`: 3860 rows have no usable speaker ID

### benchmark_xorqa

- `text_sha256`: 1 cross-split duplicate groups

### meta_omnilingual

- `audio_sha256`: 4 cross-split duplicate groups
- `text_sha256`: 31 cross-split duplicate groups
- Same-audio conflicting transcript hashes: text_sha256=5

## Training-to-evaluation overlap between views

| Training view | Evaluation view | Audio hashes | Exact text hashes | Speakers |
|---|---|---:|---:|---:|
| asr_expanded_human | asr/test | 0 | 1 | 0 |
| asr_expanded_human | asr_expanded_human/test | 0 | 1 | 0 |
| asr_expanded_human | asr_experimental/test | 338 | 575 | 1 |
| asr_expanded_human | asr_experimental/validation | 397 | 683 | 0 |
| asr_expanded_human | tts/test | 0 | 1 | 0 |
| asr_experimental | asr/test | 0 | 1 | 0 |
| asr_experimental | asr_expanded_human/test | 0 | 1 | 0 |
| asr_experimental | asr_experimental/test | 0 | 1 | 0 |
| asr_experimental | tts/test | 0 | 1 | 0 |
| benchmark_xorqa | benchmark_xorqa/dev | 0 | 1 | 0 |
| meta_omnilingual | meta_omnilingual/test | 4 | 4 | 0 |
| meta_omnilingual | meta_omnilingual/validation | 0 | 27 | 0 |
| meta_omnilingual | text_recommended/test | 0 | 33 | 0 |
| meta_omnilingual | text_recommended/validation | 0 | 36 | 0 |
| text_recommended | instructions_v0.2/test | 0 | 15 | 0 |
| text_recommended | instructions_v0.2/validation | 0 | 29 | 0 |
| text_recommended | meta_omnilingual/test | 0 | 75 | 0 |
| text_recommended | meta_omnilingual/validation | 0 | 85 | 0 |
Exact row references and hashes are in the local-only JSON ledger, which contains VAANI speaker identifiers and is excluded from Git and public packages.

## Evaluation use decisions

No current split is approved as an independent held-out confirmation. A row-set fingerprint identifies each exact subset; its manifest SHA-256 and any previously scored row IDs/hashes are in the local-only JSON ledger, which contains VAANI speaker identifiers and is excluded from Git and public packages.

| Evaluation | Status | Selected rows | Previously scored | Permitted use |
|---|---|---:|---:|---|
| crosssum_test | unresolved | 500 / 500 | 0 | historical_or_unresolved_only; no blind-test claim |

- **crosssum_test:** No local prediction match was found, but upstream model pretraining overlap has not been established; do not call it blind.
| flores_test | development_only | 1012 / 1012 | 1012 | historical_or_unresolved_only; no blind-test claim |

- **flores_test:** All 1,012 rows have saved translation predictions; this set is already examined.
| instructions_test | development_only | 260 / 260 | 134 | historical_or_unresolved_only; no blind-test claim |

- **instructions_test:** 134 of 260 current rows match saved test predictions. Another 126 lack a match, which is not proof they were unseen; an older mT0 test sidecar has a different split membership.
| meta_omnilingual_test | unresolved | 292 / 300 | 0 | historical_or_unresolved_only; no blind-test claim |

- **meta_omnilingual_test:** Do not use as a final held-out claim until upstream checkpoint pretraining/fine-tuning overlap is resolved. The internal safety flags only address duplicates within this Meta manifest.
| meta_omnilingual_validation | development_only | 271 / 298 | 0 | development_selection_and_error_analysis_only |

- **meta_omnilingual_validation:** Use the internally safe rows for development selection/error analysis only. Upstream checkpoint exposure is unknown, so results cannot establish independent generalization.
| text_recommended_test | unresolved | 398 / 398 | 0 | historical_or_unresolved_only; no blind-test claim |

- **text_recommended_test:** No local prediction match was found, but base-checkpoint pretraining exposure is unknown. Cross-view exact-text overlaps also require the workstream to use this family in isolation.
| vaani_asr_test | development_only | 112 / 112 | 112 | historical_or_unresolved_only; no blind-test claim |

- **vaani_asr_test:** No further tuning or blind-test claim. All 112 rows have saved predictions, and SraVaani's exact VAANI exposure is unspecified upstream.
| vaani_asr_validation | development_only | 269 / 269 | 269 | development_selection_and_error_analysis_only |

- **vaani_asr_validation:** Selection and error analysis only. All 269 rows already have saved predictions; this is not fresh confirmation.
| xorqa_dev | development_only | 500 / 500 | 500 | development_selection_and_error_analysis_only |

- **xorqa_dev:** All 500 rows have saved retrieval predictions; use only as historical development evidence.
| xorqa_test | development_only | 539 / 539 | 539 | historical_or_unresolved_only; no blind-test claim |

- **xorqa_test:** All 539 rows have saved retrieval predictions; this set is already examined.

### Upstream evidence: sravaani_1_0

The model card reports 31,255 hours of VAANI pretraining and about 31,270 hours of labelled fine-tuning from VAANI plus open-source speech datasets; its dataset links include Vaani and Vaani-transcription-part. The paper describes 24 public datasets for labelled fine-tuning. Neither source provides Garhwali row IDs or confirms exclusion of this project's fixed splits.

Exact VAANI test exposure is unknown; absence of a named Meta Omnilingual source does not prove it was excluded from every upstream dataset.

Sources: [https://huggingface.co/ARTPARK-IISc/SraVaani-1.0](https://huggingface.co/ARTPARK-IISc/SraVaani-1.0), [https://arxiv.org/abs/2608.08235](https://arxiv.org/abs/2608.08235)

## Meta split-safety flags

| Split | Safety flag | True | False | Missing/invalid |
|---|---|---:|---:|---:|
| test | `split_safe_for_evaluation` | 292 | 8 | 0 |
| test | `split_safe_for_training` | 292 | 8 | 0 |
| train | `split_safe_for_evaluation` | 2294 | 35 | 0 |
| train | `split_safe_for_training` | 2294 | 35 | 0 |
| validation | `split_safe_for_evaluation` | 271 | 27 | 0 |
| validation | `split_safe_for_training` | 271 | 27 | 0 |

| Duplicate flag | Computed rows | Declared true rows | Mismatches |
|---|---:|---:|---:|
| `cross_split_audio_overlap` | 8 | 8 | 0 |
| `cross_split_text_overlap` | 62 | 62 | 0 |
| `transcript_conflict_for_audio` | 10 | 10 | 0 |

## Previously saved prediction outputs

| File | Rows | SHA-256 | Matched split rows | Matched validation/dev rows | Matched test rows | Ambiguous rows | Unmatched rows |
|---|---:|---|---|---:|---:|---:|---:|
| `data/processed/evaluation/asr/baseline_predictions.jsonl` | 20 | `7cbe14c0276610515113d89e4cffefeadb23e0112075f14a85c6fb1dc1341391` | asr:validation=7; asr_expanded_human:train=13, validation=7; asr_experimental:validation=20; tts:validation=7; tts_language_resources:validation=7 | 48 | 0 | 0 | 0 |
| `data/processed/evaluation/asr/confidence_calibration/sravaani/predictions.jsonl` | 381 | `78b9509b5682474f391fb388a1a5ed1d25b5c48f527824eb9cf4cb879219f73a` | asr:test=112, validation=269; asr_expanded_human:test=112, validation=269; asr_experimental:test=112, validation=269; tts:test=112, validation=269; tts_language_resources:test=89, validation=225 | 1301 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/confidence_calibration/whisper_v0.2/predictions.jsonl` | 381 | `4f068f4c2d5949a9be285c84fb956f0467e9ebe6ab5347eb1c58e41fe735a723` | asr:test=112, validation=269; asr_expanded_human:test=112, validation=269; asr_experimental:test=112, validation=269; tts:test=112, validation=269; tts_language_resources:test=89, validation=225 | 1301 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/curriculum_stage_0_validation/predictions.jsonl` | 269 | `6b92dc55f6abc55298fdaf37017f5d2c1d33d81f93b587a8aab39735b0fc6d3e` | asr:validation=269; asr_expanded_human:validation=269; asr_experimental:validation=269; tts:validation=269; tts_language_resources:validation=225 | 1301 | 0 | 0 | 0 |
| `data/processed/evaluation/asr/low_confidence_whisper_agreement/cloud_output/predictions.jsonl` | 500 | `e2fc7bebbb238be0fe4edcea08279f460ff02f75fad0cd1a9c555827ef6d5560` | unmatched | 0 | 0 | 0 | 500 |
| `data/processed/evaluation/asr/low_confidence_whisper_turbo_agreement/cloud_output/predictions.jsonl` | 5000 | `fd04818b5f627f5cc7d98a6e1f859836adc5b05294bfe940e153df6578e2709a` | unmatched | 0 | 0 | 0 | 5000 |
| `data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_005000/cloud_output/predictions.jsonl` | 15000 | `9f178871fcc822fc8ebe0c3276c9194df56657fe53bbfe80c07a2b3a9e2d4487` | unmatched | 0 | 0 | 0 | 15000 |
| `data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_020000/cloud_output/predictions.jsonl` | 15000 | `53b2819b344bed560333523c8ba49feceb59b0ae2a9d3bb438bd95028660ff8d` | unmatched | 0 | 0 | 0 | 15000 |
| `data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_035000/cloud_output/predictions.jsonl` | 15000 | `ac1055080ef32bddaad5ab25ca5e589f7e02da9d33762defce2c914a31e77d4c` | unmatched | 0 | 0 | 0 | 15000 |
| `data/processed/evaluation/asr/low_confidence_whisper_turbo_offset_050000/cloud_output/predictions.jsonl` | 15000 | `a7f759c1d675596d2258f2b6369137ea7b25f9eb0b979b548bb5fd82afa40fab` | unmatched | 0 | 0 | 0 | 15000 |
| `data/processed/evaluation/asr/sravaani_1_0/predictions.jsonl` | 112 | `d8f6e1299dd91a167293a9c4609a967c5f7ad9632885bd23dfb166698fdc14be` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_decoding_sweep/cloud_output/selected-test-predictions.json` | 112 | `04f2af74461b18b5972575c3217a92a65f4634e70611c2161878076f9510882c` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/best-validation-predictions.json` | 269 | `bc5f169d52cd4b91687baa686ae5de4ac8f9a33b20bb5bbc0cc6a0a5e32887a7` | asr:validation=269; asr_expanded_human:validation=269; asr_experimental:validation=269; tts:validation=269; tts_language_resources:validation=225 | 1301 | 0 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_expanded_human/cloud_output/held-out-test-predictions.json` | 112 | `0348118a3749aaceeca5b6881664fba72bddfa62cb7bd2afa29e9d9ae5002b23` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_finetune/cloud_output/held_out_evaluation/predictions.jsonl` | 112 | `b9edfc8ab3982cc088285b76b65e6ccc122e6a7b2b471706d3b418679cfb1868` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_refined_61/cloud_output/best-validation-predictions.json` | 269 | `096c892a8943d66948ddd97178fc45d2bbc57de50a3819b5fe3478eeae3aa938` | asr:validation=269; asr_expanded_human:validation=269; asr_experimental:validation=269; tts:validation=269; tts_language_resources:validation=225 | 1301 | 0 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_refined_61/cloud_output/held-out-test-predictions.json` | 112 | `f07852166d2f5462b1956d680dcb27a005af5b8ed4b2e49c023fc44857799ace` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/best-validation-predictions.json` | 269 | `3f95538c9bc63def0ebacbbb77e6c9b500203bb60b33989235bff66a41880085` | asr:validation=269; asr_expanded_human:validation=269; asr_experimental:validation=269; tts:validation=269; tts_language_resources:validation=225 | 1301 | 0 | 0 | 0 |
| `data/processed/evaluation/asr/sravaani_six_config_sweep/cloud_output/held-out-test-predictions.json` | 112 | `b2ae21718e230b74c8dfcd1ae9c7d0d6182ac7f96406c4aa6c2fab95738d28f6` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/whisper_small_zero_shot/predictions.jsonl` | 112 | `66a7a58f95fb5f45b652d8202c992d09be678c844d6e6f8c9ebd8dcb1ec3dfc3` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/asr/whisper_tiny_zero_shot/predictions.jsonl` | 112 | `f3edcd1be166c7e563b4a6dd0fd6fa2de6ef38c45772e6587e23715f6dc0c446` | asr:test=112; asr_expanded_human:test=112; asr_experimental:test=112; tts:test=112; tts_language_resources:test=89 | 0 | 537 | 0 | 0 |
| `data/processed/evaluation/controlled_modeling/instruction_base_audit/mt0-small-predictions.jsonl` | 130 | `e5d37348719cc1cd4aeccd57c5fe3249263717527bf284664a47f44dc634ef65` | instructions_v0.2:validation=130 | 130 | 0 | 0 | 0 |
| `data/processed/evaluation/controlled_modeling/mt0_instruction_32768_generation_analysis_v0_6/cloud_output/validation_predictions.jsonl` | 390 | `ddfe215bf5d8607216aad2a8c4b2866a6ff01818ed8715aab80edd14ffc0652f` | instructions_v0.2:validation=130 | 130 | 0 | 0 | 0 |
| `data/processed/evaluation/controlled_modeling/mt0_instruction_32768_seed43_v0_6/cloud_output/validation_predictions.jsonl` | 260 | `49f90c85c388fa61364cd42965e7b785b2f06bcfa3b33a2167f4fe59fed651b8` | instructions_v0.2:validation=130 | 130 | 0 | 0 | 0 |
| `data/processed/evaluation/controlled_modeling/mt0_instruction_32768_selected_test_v0_6/cloud_output/test_predictions.jsonl` | 172 | `a61d90aff5270f47b97316d297dbafe7e10937a37b11b4d7d129864eaf6e9b10` | unmatched | 0 | 0 | 0 | 172 |
| `data/processed/evaluation/controlled_modeling/mt0_instruction_v0.2/test_predictions.jsonl` | 1032 | `ec771ac72e1971d6c34ed10ecfda059ea58d39865b5ab5d7e71ad3b5f430c3db` | instructions_v0.2:test=134, train=114, validation=10 | 10 | 134 | 0 | 0 |
| `data/processed/evaluation/controlled_modeling/mt5_instruction/test_predictions.jsonl` | 336 | `1bc275a14fcaa298211b4eb7283240c11000b4326b3db2a5b44e4e2923081eea` | unmatched | 0 | 0 | 0 | 336 |
| `data/processed/evaluation/retrieval/indicbertv2/predictions.jsonl` | 539 | `974e2168901bde326d9e1d58bd10152b383bbb0d32c6e63a46ec163fe11ee054` | benchmark_xorqa:test=539 | 0 | 539 | 0 | 0 |
| `data/processed/evaluation/retrieval/predictions.jsonl` | 1039 | `c1b4f6b6d91cb872d3f34ba9d39b72e9e625d8b3d4d22cb5cd8bef8055a3b02c` | benchmark_xorqa:dev=500, test=539 | 500 | 539 | 0 | 0 |
| `data/processed/evaluation/translation/nllb_garhwali_adapter_hindi_proxy/predictions.jsonl` | 32 | `74f81962cd5c791f5a719c71b4e6e4ab2ddb9afc35f910a959260f7828a2721e` | benchmark_flores:test=32 | 0 | 32 | 0 | 0 |
| `data/processed/evaluation/translation/nllb_hindi_proxy/predictions.jsonl` | 32 | `75d0f73c5b4300fbb8e5a210951734f2e6e8b3faa4f7900e686e4d28e72fbd33` | benchmark_flores:test=32 | 0 | 32 | 0 | 0 |
| `data/processed/evaluation/translation/predictions.jsonl` | 1012 | `759c28e6ec78f8ad5c70a6f500c9c773dcc2ab2e16860f5c940b62532c1bc73f` | benchmark_flores:test=1012 | 0 | 1012 | 0 | 0 |

## Exact previously scored rows

- **asr:** test=112, validation=269. Exact row IDs and hashes are in the local-only JSON ledger.
- **asr_expanded_human:** test=112, validation=269. Exact row IDs and hashes are in the local-only JSON ledger.
- **asr_experimental:** test=112, validation=282. Exact row IDs and hashes are in the local-only JSON ledger.
- **benchmark_flores:** test=1012. Exact row IDs and hashes are in the local-only JSON ledger.
- **benchmark_xorqa:** dev=500, test=539. Exact row IDs and hashes are in the local-only JSON ledger.
- **instructions_v0.2:** test=134, validation=144. Exact row IDs and hashes are in the local-only JSON ledger.
- **tts:** test=112, validation=269. Exact row IDs and hashes are in the local-only JSON ledger.
- **tts_language_resources:** test=89, validation=225. Exact row IDs and hashes are in the local-only JSON ledger.

## Provenance limits

Prediction files and manifests include local SHA-256 digests. Content-hash matches that identify multiple manifest rows are marked ambiguous and do not assign a split. Unmatched rows may come from corpus candidates or inputs outside the configured fixed splits; they are not automatically leakage. Model training data lineage and upstream pretraining overlap remain unknown unless recorded in a saved artifact. Exact matches establish that a row was evaluated before; an absent match is not proof that a test row was never viewed or used elsewhere.
